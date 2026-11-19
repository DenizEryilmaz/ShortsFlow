"""Unit tests for standalone LLM JSON parsing, connection errors and media utilities."""
import httpx
import pytest

from studio import llm, providers
from studio.llm import parse_json_response_text
from studio.media import STYLE_PRESETS, srt_time
from studio.schema import Script


def test_parse_json_response_text_handles_code_fences_and_bad_unicode_escapes():
    raw = '```json\n{"title": "Test \\uX123", "scenes": []}\n```'
    parsed = parse_json_response_text(raw)
    assert parsed == {'title': 'Test \\uX123', 'scenes': []}


def test_parse_json_response_text_rejects_empty():
    with pytest.raises(ValueError):
        parse_json_response_text('')


def test_srt_time_and_style_presets():
    assert srt_time(0.0) == '00:00:00,000'
    assert srt_time(65.432) == '00:01:05,432'
    assert {'animation_2d', 'paint_storybook', 'science_2d', 'paper_cut'}.issubset(STYLE_PRESETS)


def test_connection_errors_name_target_service(monkeypatch):
    def fail_connect(*_args, **_kwargs):
        raise httpx.ConnectError('connection refused')

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        post = fail_connect
        get = fail_connect

    monkeypatch.setattr(httpx, 'Client', DummyClient)
    with pytest.raises(RuntimeError, match='ComfyUI sunucusuna bağlanılamadı'):
        providers.comfy('queue')
    with pytest.raises(RuntimeError, match='Yerel dil modeli sunucusuna bağlanılamadı'):
        llm.generate_json('prompt', Script)


def test_llm_generate_json_streams_progress_events(monkeypatch):
    class StreamResponse:
        status_code = 200
        headers = {'content-type': 'text/event-stream'}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def iter_lines(self):
            yield 'data: {"choices":[{"delta":{"content":"{\\"title\\": \\"Test\\", "}}]}'
            yield 'data: {"choices":[{"delta":{"content":"\\"scenes\\": [{\\"id\\": \\"1\\"}]}"}}],"usage":{"prompt_tokens":5,"completion_tokens":8}}'
            yield 'data: [DONE]'

    class StreamClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def stream(self, *args, **kwargs):
            return StreamResponse()

    monkeypatch.setattr(llm, '_client', lambda **kwargs: StreamClient())
    events = []
    parsed, meta = llm.generate_json('prompt', Script, on_progress=events.append)
    assert parsed['title'] == 'Test'
    assert meta['output_tokens'] == 8
    assert any('Model yanıtı alındı' in msg for msg in events)


def test_timed_caption_cues_syncs_exact_narration_to_spoken_duration():
    from studio import media

    text = "Fırtına büyüdükçe kıyıdaki eski fenerin ışığı titremeye başladı."
    cues = media.timed_caption_cues(text, 0.05, 3.6, max_words=5)
    assert len(cues) == 2
    assert cues[0][0] == 0.05
    assert abs(cues[-1][1] - 3.65) < 1e-6
    assert " ".join(c[2] for c in cues) == text
