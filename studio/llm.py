"""Structured JSON client for OpenAI-compatible local LLM servers (Ollama, LM Studio, vLLM)."""
from __future__ import annotations

import json
import os
import time
from typing import Callable, Optional, Tuple, Type

import httpx
from pydantic import BaseModel

DEFAULT_BASE_URL = "http://127.0.0.1:11434/v1"
DEFAULT_MODEL = "qwen3-vl:8b-instruct"
DEFAULT_TIMEOUT = 600.0


def base_url() -> str:
    return (os.environ.get("LLM_BASE_URL") or DEFAULT_BASE_URL).strip().rstrip("/")


def model_name() -> str:
    return (os.environ.get("LLM_MODEL") or "").strip() or DEFAULT_MODEL


def _timeout() -> float:
    try:
        return float(os.environ.get("LLM_TIMEOUT") or DEFAULT_TIMEOUT)
    except ValueError:
        return DEFAULT_TIMEOUT


def _headers() -> dict:
    key = (os.environ.get("LLM_API_KEY") or "ollama").strip()
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _generation_options() -> dict:
    out = {}
    try:
        out["max_tokens"] = max(64, int(os.environ.get("LLM_MAX_TOKENS", "2048")))
    except ValueError:
        out["max_tokens"] = 2048
    if (os.environ.get("LLM_PROVIDER") or "ollama").strip().lower() == "ollama":
        out["think"] = os.environ.get("LLM_THINK", "0").strip().lower() in ("1", "true", "yes")
    return out


def _client(**kwargs) -> httpx.Client:
    return httpx.Client(timeout=_timeout(), **kwargs)


def _strip_code_fences(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _extract_json_candidate(text: str) -> str:
    cleaned = _strip_code_fences(text)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start:end + 1]
    return cleaned


def _escape_invalid_unicode_escapes(text: str) -> str:
    chars = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text) and text[i + 1] == "u":
            hex_digits = text[i + 2:i + 6]
            if len(hex_digits) < 4 or any(ch not in "0123456789abcdefABCDEF" for ch in hex_digits):
                chars.append("\\\\u")
                i += 2
                continue
        chars.append(text[i])
        i += 1
    return "".join(chars)


def parse_json_response_text(text: str) -> dict:
    """Extract and parse a JSON object from an LLM completion."""
    if not text:
        raise ValueError("Dil modeli boş yanıt döndürdü.")
    candidate = _extract_json_candidate(text).replace("\x00", "").strip()
    if not candidate:
        raise ValueError("Dil modeli yanıtında JSON nesnesi bulunamadı.")
    attempts = [candidate]
    sanitized = _escape_invalid_unicode_escapes(candidate)
    if sanitized != candidate:
        attempts.append(sanitized)
    last_error: Optional[Exception] = None
    for item in attempts:
        try:
            return json.loads(item)
        except json.JSONDecodeError as exc:
            last_error = exc
    raise ValueError(f"JSON yanıtı ayrıştırılamadı: {last_error}")


def _response_formats(schema: Type[BaseModel]):
    name = getattr(schema, "__name__", "response").lower()
    yield {
        "type": "json_schema",
        "json_schema": {"name": name, "schema": schema.model_json_schema()},
    }
    yield {"type": "json_object"}
    yield None


def _is_format_rejection(resp: httpx.Response) -> bool:
    if resp.status_code not in (400, 422):
        return False
    body = resp.text.lower()
    return (
        "response_format" in body
        or "json_schema" in body
        or "json_object" in body
        or "format" in body
    )


def _extract_choice_text(data: dict) -> str:
    choices = data.get("choices") or []
    text = ""
    if choices:
        msg = choices[0].get("message") or {}
        text = msg.get("content") or ""
        if isinstance(text, list):
            text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
    return text


def generate_json(
    prompt: str,
    schema: Type[BaseModel],
    model: Optional[str] = None,
    on_progress: Optional[Callable[[str], None]] = None,
) -> Tuple[dict, dict]:
    """Request a structured JSON completion and validate against ``schema``."""
    url = f"{base_url()}/chat/completions"
    model = model or model_name()
    messages = [
        {"role": "system", "content": "You answer with a single JSON object and nothing else."},
        {"role": "user", "content": prompt},
    ]
    last_rejection: Optional[str] = None
    stream_requested = on_progress is not None
    text = ""
    usage: dict = {}
    try:
        with _client() as client:
            for fmt in _response_formats(schema):
                body = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.2,
                    "stream": stream_requested,
                    **_generation_options(),
                }
                if fmt is not None:
                    body["response_format"] = fmt
                if not stream_requested:
                    resp = client.post(url, json=body, headers=_headers())
                    if fmt is not None and _is_format_rejection(resp):
                        last_rejection = resp.text[:200]
                        continue
                    if resp.status_code >= 400:
                        raise RuntimeError(f"LLM sunucusu hatası ({resp.status_code}) {url}: {resp.text[:300]}")
                    data = resp.json()
                    text = _extract_choice_text(data)
                    usage = data.get("usage") or {}
                    break

                with client.stream("POST", url, json=body, headers=_headers()) as resp:
                    if fmt is not None and resp.status_code in (400, 422):
                        resp.read()
                        if _is_format_rejection(resp):
                            last_rejection = resp.text[:200]
                            continue
                    if resp.status_code >= 400:
                        resp.read()
                        raise RuntimeError(f"LLM sunucusu hatası ({resp.status_code}) {url}: {resp.text[:300]}")
                    ctype = (resp.headers.get("content-type") or "").lower()
                    if "text/event-stream" not in ctype:
                        resp.read()
                        data = resp.json()
                        text = _extract_choice_text(data)
                        usage = data.get("usage") or {}
                        break
                    chunks: list[str] = []
                    total_chars = 0
                    last_emit = time.monotonic()
                    for raw_line in resp.iter_lines():
                        line = raw_line.strip()
                        if not line.startswith("data:"):
                            continue
                        payload = line[5:].strip()
                        if not payload or payload == "[DONE]":
                            continue
                        try:
                            event = json.loads(payload)
                        except json.JSONDecodeError:
                            continue
                        if event.get("usage"):
                            usage = event["usage"]
                        choices = event.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta") or {}
                        part = delta.get("content") or ""
                        if part:
                            chunks.append(part)
                            total_chars += len(part)
                            now = time.monotonic()
                            if now - last_emit >= 2.0:
                                on_progress(f"Model yazıyor · {total_chars} karakter…")
                                last_emit = now
                    text = "".join(chunks)
                    if total_chars:
                        on_progress(f"Model yanıtı alındı · {total_chars} karakter doğrulama yapılıyor.")
                    break
            else:
                raise RuntimeError(f"LLM sunucusu tüm response_format seçeneklerini reddetti: {last_rejection}")
    except httpx.ConnectError as exc:
        raise RuntimeError(
            f"Yerel dil modeli sunucusuna bağlanılamadı ({base_url()}). Ollama servisinin çalıştığından emin olun."
        ) from exc

    parsed = parse_json_response_text(text)
    validated = schema.model_validate(parsed).model_dump()
    meta = {
        "input_tokens": int(usage.get("prompt_tokens") or 0),
        "output_tokens": int(usage.get("completion_tokens") or 0),
        "model": model,
        "local": True,
    }
    return validated, meta
