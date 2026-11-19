"""Local model adapters with persisted prompts and reproducible input graphs."""
import json
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

import httpx

from . import llm
from .json_utils import write_json_atomic
from .models import COMFY, COMFY_URL, FREEVIDEO, ROOT, WORKSPACE


class ResourceWait(RuntimeError):
    """A measured hardware budget can admit the same request later."""


class JobCancelled(RuntimeError):
    """Raised when the user cancels a running job."""


def _parse_freevideo_line(line: str) -> str | None:
    text = line.strip()
    if not text:
        return None
    if text.startswith('│ Estimate'):
        short = text.removeprefix('│ Estimate').strip().split('·')[0].strip()
        return f'FreeVideo tahmini süre: {short}'
    if text.startswith('{'):
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return None
        event = payload.get('event')
        if event == 'encoding_start':
            return 'FreeVideo metin ve kareleri kodluyor…'
        if event == 'video_start':
            steps = (payload.get('engine') or {}).get('steps')
            return f'FreeVideo video üretiyor ({steps} adım)…' if steps else 'FreeVideo video üretiyor…'
        if event in ('step', 'sampling_step') and payload.get('step') and payload.get('total_steps'):
            step, total = int(payload['step']), int(payload['total_steps'])
            pct = round((step / total) * 100)
            return f'FreeVideo adım {step}/{total} (%{pct})'
        if event in ('decode_start', 'decoding_start'):
            return 'FreeVideo kareleri çözüyor ve MP4 kaydediyor…'
    return None


def run(arguments, *, cwd=None, timeout=3600, log_path=None, on_progress=None, cancel_check=None):
    target_log = Path(log_path) if log_path else (ROOT / 'data' / 'subprocess.log')
    target_log.parent.mkdir(parents=True, exist_ok=True)
    log_offset = target_log.stat().st_size if target_log.is_file() else 0
    started = time.monotonic()
    last_report = started
    with target_log.open('a', encoding='utf-8') as stream:
        process = subprocess.Popen(
            [str(x) for x in arguments],
            cwd=cwd,
            stdout=stream,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
        try:
            while True:
                code = process.poll()
                if code is not None:
                    break
                if cancel_check and cancel_check():
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    raise JobCancelled('Kullanıcı tarafından iptal edildi.')
                if time.monotonic() - started > timeout:
                    process.terminate()
                    process.wait(timeout=15)
                    raise subprocess.TimeoutExpired(arguments, timeout)
                if on_progress and target_log.is_file():
                    try:
                        with target_log.open('r', encoding='utf-8', errors='replace') as reader:
                            reader.seek(log_offset)
                            chunk = reader.read()
                            log_offset = reader.tell()
                        for line in chunk.splitlines():
                            msg = _parse_freevideo_line(line)
                            if msg:
                                on_progress(msg)
                                last_report = time.monotonic()
                    except OSError:
                        pass
                    now = time.monotonic()
                    if now - last_report >= 15.0:
                        on_progress(f'İşlem sürüyor · {int(now - started)} sn…')
                        last_report = now
                time.sleep(2)
        except BaseException:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
            raise
    if code:
        detail = target_log.read_text(encoding='utf-8', errors='replace')[-1800:]
        if 'ResourceBudgetError' in detail:
            measurements = '\n'.join(
                line for line in detail.splitlines()
                if line.startswith(('RAM:', 'VRAM:', 'RAM shortfall:', 'VRAM shortfall:'))
            )
            raise ResourceWait(f'FreeVideo kullanılabilir bellek bekliyor.\n{measurements}')
        raise RuntimeError(f'{Path(str(arguments[0])).name} çıkış kodu {code}. {detail}')


def interrupt_comfy():
    try:
        with httpx.Client(timeout=5) as client:
            client.post(f'{COMFY_URL}/interrupt')
    except httpx.HTTPError:
        pass


def comfy(path, body=None):
    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(f'{COMFY_URL}/{path}', json=body) if body is not None else client.get(f'{COMFY_URL}/{path}')
            response.raise_for_status()
            return response.json() if response.content else {}
    except httpx.ConnectError as error:
        raise RuntimeError(
            f'ComfyUI sunucusuna bağlanılamadı ({COMFY_URL}). ComfyUI servisinin çalıştığından emin olun.'
        ) from error


def upload(path):
    try:
        with httpx.Client(timeout=30) as client, Path(path).open('rb') as stream:
            response = client.post(
                f'{COMFY_URL}/upload/image',
                files={'image': (f'{uuid.uuid4().hex}.png', stream, 'image/png')},
            )
            response.raise_for_status()
            data = response.json()
            return f"{data.get('subfolder', '')}/{data['name']}".lstrip('/')
    except httpx.ConnectError as error:
        raise RuntimeError(
            f'ComfyUI sunucusuna bağlanılamadı ({COMFY_URL}). ComfyUI servisinin çalıştığından emin olun.'
        ) from error


COMFY_NODE_LABELS = {
    'UNETLoader': 'Model yükleniyor',
    'CheckpointLoaderSimple': 'LTX-Video modeli yükleniyor',
    'CLIPLoader': 'Metin kodlayıcı yükleniyor (CUDA)',
    'CLIPTextEncode': 'Prompt kodlanıyor',
    'VAELoader': 'VAE yükleniyor',
    'LoadImage': 'Referans yükleniyor',
    'TextEncodeQwenImage21': 'Prompt ve referans kodlanıyor (CUDA)',
    'LTXVConditioning': 'LTX-Video hazırlanıyor',
    'LTXVImgToVideo': 'Başlangıç karesi bağlanıyor',
    'LTXVAddGuide': 'Son kare rehberi bağlanıyor',
    'EmptyLatentImage': 'Tuval hazırlanıyor',
    'EmptyFlux2LatentImage': 'Tuval hazırlanıyor (FLUX.2)',
    'ReferenceLatent': 'Referans görsel bağlanıyor',
    'VAEEncode': 'Referans kodlanıyor (VAE)',
    'Flux2Scheduler': 'FLUX.2 zamanlayıcı (4 adım)',
    'SamplerCustomAdvanced': 'Görsel örnekleniyor (CUDA)',
    'SamplerCustom': 'LTX-Video örnekleniyor (CUDA)',
    'VAEDecode': 'Kareler çözülüyor (VAE)',
    'CreateVideo': 'Video oluşturuluyor',
    'SaveImage': 'Görsel kaydediliyor',
    'SaveVideo': 'Video kaydediliyor',
}


def _wait_comfy(identifier, graph, client_id, ws, on_progress, cancel_check=None):
    started = time.monotonic()
    deadline = started + 3600
    last_report = started
    current_phase = 'ComfyUI kuyrukta'
    if ws is not None:
        try:
            while time.monotonic() < deadline:
                if cancel_check and cancel_check():
                    interrupt_comfy()
                    raise JobCancelled('Kullanıcı tarafından iptal edildi.')
                try:
                    raw = ws.recv(timeout=4)
                except TimeoutError:
                    response = comfy(f'history/{identifier}').get(identifier)
                    if response:
                        return response
                    now = time.monotonic()
                    if on_progress and now - last_report >= 6.0:
                        on_progress(f'{current_phase} · {int(now - started)} sn…')
                        last_report = now
                    continue
                if isinstance(raw, bytes):
                    continue
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                kind = event.get('type')
                data = event.get('data') or {}
                if data.get('prompt_id') not in (None, identifier):
                    continue
                if kind == 'executing':
                    node_id = data.get('node')
                    if node_id is None and data.get('prompt_id') == identifier:
                        break
                    if node_id in graph:
                        current_phase = COMFY_NODE_LABELS.get(graph[node_id]['class_type'], graph[node_id]['class_type'])
                        if on_progress:
                            on_progress(f'{current_phase}…')
                            last_report = time.monotonic()
                elif kind == 'progress' and data.get('max'):
                    value, max_val = int(data['value']), int(data['max'])
                    pct = round((value / max_val) * 100)
                    if on_progress:
                        on_progress(f'{current_phase} · adım {value}/{max_val} (%{pct})')
                        last_report = time.monotonic()
                elif kind == 'execution_error':
                    break
        except JobCancelled:
            raise
        except Exception:
            pass
    while time.monotonic() < deadline:
        if cancel_check and cancel_check():
            interrupt_comfy()
            raise JobCancelled('Kullanıcı tarafından iptal edildi.')
        response = comfy(f'history/{identifier}').get(identifier)
        if response:
            return response
        now = time.monotonic()
        if on_progress and now - last_report >= 6.0:
            on_progress(f'{current_phase} · {int(now - started)} sn…')
            last_report = now
        time.sleep(2)
    raise TimeoutError(f'ComfyUI işi zaman aşımına uğradı. İş kimliği {identifier}')


def _build_qwen_graph(prompt, negative, output, settings, uploaded_refs, clip_device='default'):
    graph = {}

    def add(kind, **inputs):
        node = str(len(graph) + 1)
        graph[node] = {'class_type': kind, 'inputs': inputs}
        return node

    model = add('UNETLoader', unet_name='qwen_image_2.1_turbo_int8_convrot.safetensors', weight_dtype='default')
    clip = add('CLIPLoader', clip_name='qwen3vl_8b_w4a8.safetensors', type='qwen_image', device=clip_device)
    vae = add('VAELoader', vae_name='qwen_image_2.1_vae_bf16.safetensors')
    inputs = dict(clip=[clip, 0], prompt=prompt, negative_prompt=negative, vae=[vae, 0], resolution=0)
    for index, uploaded_name in enumerate(uploaded_refs, 1):
        image = add('LoadImage', image=uploaded_name)
        inputs[f'images.image_{index}'] = [image, 0]
    encoded = add('TextEncodeQwenImage21', **inputs)
    latent = add('EmptyLatentImage', width=settings['width'], height=settings['height'], batch_size=1)
    sigmas = add('ManualSigmas', sigmas='1.0,0.978453,0.95418,0.926626,0.89508,0.845148,0.704534,0.414568,0')
    sampler = add('KSamplerSelect', sampler_name='euler')
    guider = add('CFGGuider', model=[model, 0], positive=[encoded, 0], negative=[encoded, 1], cfg=1)
    noise = add('RandomNoise', noise_seed=settings['seed'])
    sampled = add(
        'SamplerCustomAdvanced',
        noise=[noise, 0],
        guider=[guider, 0],
        sampler=[sampler, 0],
        sigmas=[sigmas, 0],
        latent_image=[latent, 0],
    )
    decoded = add('VAEDecode', samples=[sampled, 0], vae=[vae, 0])
    saved = add('SaveImage', images=[decoded, 0], filename_prefix=f'studio/{uuid.uuid4().hex}')
    return graph, saved


def _submit_comfy_graph(graph, on_progress=None, cancel_check=None):
    client_id = uuid.uuid4().hex
    ws = None
    if on_progress is not None:
        try:
            from websockets.sync.client import connect as ws_connect
            ws_url = COMFY_URL.replace('http://', 'ws://').replace('https://', 'wss://') + f'/ws?clientId={client_id}'
            ws = ws_connect(ws_url, open_timeout=3)
        except Exception:
            ws = None
    try:
        identifier = comfy('prompt', {'prompt': graph, 'client_id': client_id})['prompt_id']
        return _wait_comfy(identifier, graph, client_id, ws, on_progress, cancel_check)
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass


def qwen_image(prompt, negative, output, settings, references=(), on_progress=None, cancel_check=None):
    import os
    output = Path(output)
    uploaded_refs = []
    for index, reference in enumerate(references, 1):
        from PIL import Image, ImageOps
        normalized = output.with_name(f'{output.stem}-reference-{index}.png')
        with Image.open(reference) as original:
            canvas = Image.new('RGB', (settings['width'], settings['height']), 'white')
            fitted = ImageOps.contain(original.convert('RGB'), canvas.size)
            canvas.paste(fitted, ((canvas.width - fitted.width) // 2, (canvas.height - fitted.height) // 2))
            canvas.save(normalized)
        uploaded_refs.append(upload(normalized))

    preferred_device = os.getenv('STUDIO_CLIP_DEVICE', 'default').strip() or 'default'
    graph, saved = _build_qwen_graph(prompt, negative, output, settings, uploaded_refs, clip_device=preferred_device)
    write_json_atomic(str(output.with_suffix('.workflow.json')), graph, ensure_ascii=False, indent=2)
    response = _submit_comfy_graph(graph, on_progress, cancel_check)

    if response['status']['status_str'] != 'success' and preferred_device != 'cpu':
        status_blob = json.dumps(response['status'], ensure_ascii=False).lower()
        if any(token in status_blob for token in ('out of memory', 'cuda', 'oom', 'alloc', 'vram')):
            if on_progress:
                on_progress('VRAM yetersiz · metin kodlayıcı otomatik olarak CPU moduna alınıyor…')
            try:
                comfy('free', {'unload_models': True, 'free_memory': True})
            except Exception:
                pass
            graph, saved = _build_qwen_graph(prompt, negative, output, settings, uploaded_refs, clip_device='cpu')
            write_json_atomic(str(output.with_suffix('.workflow.json')), graph, ensure_ascii=False, indent=2)
            response = _submit_comfy_graph(graph, on_progress, cancel_check)

    if response['status']['status_str'] != 'success':
        raise RuntimeError(json.dumps(response['status'], ensure_ascii=False)[-1800:])
    row = response['outputs'][saved]['images'][0]
    source = (COMFY / 'output' / row.get('subfolder', '') / row['filename']).resolve()
    if not source.is_relative_to(COMFY / 'output'):
        raise ValueError('Geçersiz ComfyUI çıktı yolu.')
    shutil.copyfile(source, output)


def _build_flux2_klein_graph(prompt, negative, settings, uploaded_refs, clip_device='default'):
    graph = {}

    def add(kind, **inputs):
        node = str(len(graph) + 1)
        graph[node] = {'class_type': kind, 'inputs': inputs}
        return node

    w = max(256, (int(settings['width']) // 16) * 16)
    h = max(256, (int(settings['height']) // 16) * 16)
    model = add('UNETLoader', unet_name='flux-2-klein-4b-fp8.safetensors', weight_dtype='default')
    clip = add('CLIPLoader', clip_name='qwen_3_4b_fp4_flux2.safetensors', type='flux2', device=clip_device)
    vae = add('VAELoader', vae_name='flux2-vae.safetensors')
    pos = [add('CLIPTextEncode', clip=[clip, 0], text=prompt), 0]
    neg = [add('CLIPTextEncode', clip=[clip, 0], text=negative or ''), 0]
    for uploaded_name in uploaded_refs:
        img = add('LoadImage', image=uploaded_name)
        ref_lat = add('VAEEncode', pixels=[img, 0], vae=[vae, 0])
        pos = [add('ReferenceLatent', conditioning=pos, latent=[ref_lat, 0]), 0]
        neg = [add('ReferenceLatent', conditioning=neg, latent=[ref_lat, 0]), 0]
    latent = add('EmptyFlux2LatentImage', width=w, height=h, batch_size=1)
    sigmas = add('Flux2Scheduler', steps=4, width=w, height=h)
    sampler = add('KSamplerSelect', sampler_name='euler')
    guider = add('CFGGuider', model=[model, 0], positive=pos, negative=neg, cfg=1.0)
    noise = add('RandomNoise', noise_seed=int(settings['seed']))
    sampled = add(
        'SamplerCustomAdvanced',
        noise=[noise, 0],
        guider=[guider, 0],
        sampler=[sampler, 0],
        sigmas=[sigmas, 0],
        latent_image=[latent, 0],
    )
    decoded = add('VAEDecode', samples=[sampled, 0], vae=[vae, 0])
    saved = add('SaveImage', images=[decoded, 0], filename_prefix=f'studio/{uuid.uuid4().hex}')
    return graph, saved


def flux2_klein_image(prompt, negative, output, settings, references=(), on_progress=None, cancel_check=None):
    """Ultra-fast 4-step FLUX.2 [klein] 4B FP8 image generator with native ReferenceLatent support."""
    import os
    from PIL import Image, ImageOps

    output = Path(output)
    uploaded_refs = []
    for index, reference in enumerate(references, 1):
        normalized = output.with_name(f'{output.stem}-flux2-ref-{index}.png')
        with Image.open(reference) as original:
            canvas = Image.new('RGB', (settings['width'], settings['height']), 'white')
            fitted = ImageOps.contain(original.convert('RGB'), canvas.size)
            canvas.paste(fitted, ((canvas.width - fitted.width) // 2, (canvas.height - fitted.height) // 2))
            canvas.save(normalized)
        uploaded_refs.append(upload(normalized))

    preferred_device = os.getenv('STUDIO_CLIP_DEVICE', 'default').strip() or 'default'
    graph, saved = _build_flux2_klein_graph(prompt, negative, settings, uploaded_refs, clip_device=preferred_device)
    write_json_atomic(str(output.with_suffix('.flux2.workflow.json')), graph, ensure_ascii=False, indent=2)
    response = _submit_comfy_graph(graph, on_progress, cancel_check)

    if response['status']['status_str'] != 'success' and preferred_device != 'cpu':
        status_blob = json.dumps(response['status'], ensure_ascii=False).lower()
        if any(token in status_blob for token in ('out of memory', 'cuda', 'oom', 'alloc', 'vram')):
            if on_progress:
                on_progress('VRAM yetersiz · FLUX.2 metin kodlayıcı CPU moduna alınıyor…')
            try:
                comfy('free', {'unload_models': True, 'free_memory': True})
            except Exception:
                pass
            graph, saved = _build_flux2_klein_graph(prompt, negative, settings, uploaded_refs, clip_device='cpu')
            write_json_atomic(str(output.with_suffix('.flux2.workflow.json')), graph, ensure_ascii=False, indent=2)
            response = _submit_comfy_graph(graph, on_progress, cancel_check)

    if response['status']['status_str'] != 'success':
        raise RuntimeError(json.dumps(response['status'], ensure_ascii=False)[-1800:])
    row = response['outputs'][saved]['images'][0]
    source = (COMFY / 'output' / row.get('subfolder', '') / row['filename']).resolve()
    if not source.is_relative_to(COMFY / 'output'):
        raise ValueError('Geçersiz ComfyUI çıktı yolu.')
    shutil.copyfile(source, output)


def generate_image(prompt, negative, output, settings, references=(), on_progress=None, cancel_check=None):
    """Dispatch image generation to the selected local model (FLUX.2 Klein 4B or Qwen Image 2.1)."""
    if (settings or {}).get('image') == 'flux2-klein-4b':
        return flux2_klein_image(prompt, negative, output, settings, references, on_progress, cancel_check)
    return qwen_image(prompt, negative, output, settings, references, on_progress, cancel_check)


def _build_ltxv_graph(prompt, negative, settings, first_name, last_name, length, clip_device='default'):
    graph = {}

    def add(kind, **inputs):
        node = str(len(graph) + 1)
        graph[node] = {'class_type': kind, 'inputs': inputs}
        return node

    ckpt = add('CheckpointLoaderSimple', ckpt_name='ltxv-2b-0.9.8-distilled-fp8.safetensors')
    clip = add('CLIPLoader', clip_name='t5xxl_fp8_e4m3fn_scaled.safetensors', type='ltxv', device=clip_device)
    pos = add('CLIPTextEncode', clip=[clip, 0], text=prompt)
    neg = add('CLIPTextEncode', clip=[clip, 0], text=negative or 'low quality, worst quality, deformed, distorted, jittery, blurry, watermark, text')
    cond = add('LTXVConditioning', positive=[pos, 0], negative=[neg, 0], frame_rate=24.0)
    first_img = add('LoadImage', image=first_name)
    width = max(256, (int(settings['width']) // 32) * 32)
    height = max(256, (int(settings['height']) // 32) * 32)
    i2v = add(
        'LTXVImgToVideo',
        positive=[cond, 0],
        negative=[cond, 1],
        vae=[ckpt, 2],
        image=[first_img, 0],
        width=width,
        height=height,
        length=length,
        batch_size=1,
        strength=1.0,
    )
    guided_pos, guided_neg, guided_lat = [i2v, 0], [i2v, 1], [i2v, 2]
    if last_name:
        last_img = add('LoadImage', image=last_name)
        guide = add(
            'LTXVAddGuide',
            positive=guided_pos,
            negative=guided_neg,
            vae=[ckpt, 2],
            latent=guided_lat,
            image=[last_img, 0],
            frame_idx=-1,
            strength=0.9,
        )
        guided_pos, guided_neg, guided_lat = [guide, 0], [guide, 1], [guide, 2]
    sampler = add('KSamplerSelect', sampler_name='euler')
    sigmas = add('ManualSigmas', sigmas='1.0, 0.9937, 0.9875, 0.9812, 0.975, 0.9094, 0.725, 0.4219, 0.0')
    sampled = add(
        'SamplerCustom',
        model=[ckpt, 0],
        add_noise=True,
        noise_seed=int(settings['seed']),
        cfg=1.0,
        positive=guided_pos,
        negative=guided_neg,
        sampler=[sampler, 0],
        sigmas=[sigmas, 0],
        latent_image=guided_lat,
    )
    decoded = add('VAEDecode', samples=[sampled, 0], vae=[ckpt, 2])
    vid = add('CreateVideo', images=[decoded, 0], fps=24.0)
    saved = add('SaveVideo', video=[vid, 0], filename_prefix=f'studio/{uuid.uuid4().hex}', format='mp4', codec='h264')
    return graph, saved


def ltxv_video(prompt, first, last, duration, output, settings, on_progress=None, cancel_check=None, *, unload_before=True):
    """Fast 8-step local Image-to-Video using ComfyUI native LTX-Video 0.9.8 Distilled FP8."""
    import os
    from PIL import Image, ImageOps

    output = Path(output)
    w = max(256, (int(settings['width']) // 32) * 32)
    h = max(256, (int(settings['height']) // 32) * 32)

    def _upload_frame(src, tag):
        norm = output.with_name(f'{output.stem}-{tag}.png')
        with Image.open(src) as original:
            fitted = ImageOps.fit(original.convert('RGB'), (w, h))
            fitted.save(norm)
        return upload(norm)

    first_name = _upload_frame(first, 'ltx-first')
    last_name = _upload_frame(last, 'ltx-last') if last else None
    raw_frames = max(25, round(float(duration) * 24))
    # LTXV requires length = 8*n + 1
    length = ((raw_frames - 1 + 7) // 8) * 8 + 1

    # Free previously loaded image models (e.g. FLUX.2 / Qwen) to prevent RAM pressure on 16GB systems
    if unload_before:
        try:
            comfy('free', {'unload_models': True, 'free_memory': True})
        except Exception:
            pass

    preferred_device = os.getenv('STUDIO_CLIP_DEVICE', 'default').strip() or 'default'
    graph, saved = _build_ltxv_graph(prompt, '', settings, first_name, last_name, length, clip_device=preferred_device)
    write_json_atomic(str(output.with_suffix('.ltxv.workflow.json')), graph, ensure_ascii=False, indent=2)
    response = _submit_comfy_graph(graph, on_progress, cancel_check)

    if response['status']['status_str'] != 'success' and preferred_device != 'cpu':
        status_blob = json.dumps(response['status'], ensure_ascii=False).lower()
        if any(token in status_blob for token in ('out of memory', 'cuda', 'oom', 'alloc', 'vram')):
            if on_progress:
                on_progress('VRAM yetersiz · LTX-Video metin kodlayıcı CPU moduna alınıyor…')
            try:
                comfy('free', {'unload_models': True, 'free_memory': True})
            except Exception:
                pass
            graph, saved = _build_ltxv_graph(prompt, '', settings, first_name, last_name, length, clip_device='cpu')
            write_json_atomic(str(output.with_suffix('.ltxv.workflow.json')), graph, ensure_ascii=False, indent=2)
            response = _submit_comfy_graph(graph, on_progress, cancel_check)

    if response['status']['status_str'] != 'success':
        raise RuntimeError(json.dumps(response['status'], ensure_ascii=False)[-1800:])
    node_out = response['outputs'].get(saved) or {}
    items = node_out.get('videos') or node_out.get('images') or node_out.get('gifs') or []
    if not items:
        raise RuntimeError(f'LTX-Video çıktı dosyası bulunamadı: {json.dumps(node_out, ensure_ascii=False)}')
    row = items[0]
    source = (COMFY / 'output' / row.get('subfolder', '') / row['filename']).resolve()
    if not source.is_relative_to(COMFY / 'output') or not source.is_file():
        raise ValueError('Geçersiz ComfyUI video çıktı yolu.')
    shutil.copyfile(source, output)


def _build_wan22_ti2v_graph(prompt, negative, settings, first_name, length, clip_device='default'):
    graph = {}

    def add(kind, **inputs):
        node = str(len(graph) + 1)
        graph[node] = {'class_type': kind, 'inputs': inputs}
        return node

    w = max(256, (int(settings['width']) // 32) * 32)
    h = max(256, (int(settings['height']) // 32) * 32)
    unet = add('UNETLoader', unet_name='Wan2_2-TI2V-5B_fp8_e4m3fn_scaled_KJ.safetensors', weight_dtype='default')
    lora = add(
        'LoraLoaderModelOnly',
        model=[unet, 0],
        lora_name='Wan2_2_5B_FastWanFullAttn_lora_rank_128_bf16.safetensors',
        strength_model=1.0,
    )
    model = add('ModelSamplingSD3', model=[lora, 0], shift=8.0)
    clip = add('CLIPLoader', clip_name='umt5_xxl_fp8_e4m3fn_scaled.safetensors', type='wan', device=clip_device)
    vae = add('VAELoader', vae_name='wan2.2_vae.safetensors')
    pos = add('CLIPTextEncode', clip=[clip, 0], text=prompt)
    neg = add(
        'CLIPTextEncode',
        clip=[clip, 0],
        text=negative or 'blurry, distorted, deformed, low quality, worst quality, static, watermark, text',
    )
    first_img = add('LoadImage', image=first_name)
    latent = add(
        'Wan22ImageToVideoLatent',
        vae=[vae, 0],
        width=w,
        height=h,
        length=length,
        batch_size=1,
        start_image=[first_img, 0],
    )
    sampled = add(
        'KSampler',
        model=[model, 0],
        seed=int(settings['seed']),
        steps=6,
        cfg=1.0,
        sampler_name='uni_pc',
        scheduler='simple',
        positive=[pos, 0],
        negative=[neg, 0],
        latent_image=[latent, 0],
        denoise=1.0,
    )
    decoded = add('VAEDecode', samples=[sampled, 0], vae=[vae, 0])
    vid = add('CreateVideo', images=[decoded, 0], fps=24.0)
    saved = add('SaveVideo', video=[vid, 0], filename_prefix=f'studio/{uuid.uuid4().hex}', format='mp4', codec='h264')
    return graph, saved


def wan22_ti2v_video(prompt, first, duration, output, settings, on_progress=None, cancel_check=None, *, unload_before=True):
    """Fast 6-step Apache-2.0 Image-to-Video using ComfyUI native Wan 2.2 TI2V-5B FP8 + FastWan LoRA."""
    import os
    from PIL import Image, ImageOps

    output = Path(output)
    w = max(256, (int(settings['width']) // 32) * 32)
    h = max(256, (int(settings['height']) // 32) * 32)
    norm = output.with_name(f'{output.stem}-wan22-first.png')
    with Image.open(first) as original:
        fitted = ImageOps.fit(original.convert('RGB'), (w, h))
        fitted.save(norm)
    first_name = upload(norm)

    # Wan 2.2 TI2V-5B 24fps requires length = 4*n + 1
    raw_frames = max(25, round(float(duration) * 24))
    length = ((raw_frames - 1 + 3) // 4) * 4 + 1

    if unload_before:
        try:
            comfy('free', {'unload_models': True, 'free_memory': True})
        except Exception:
            pass

    preferred_device = os.getenv('STUDIO_CLIP_DEVICE', 'default').strip() or 'default'
    graph, saved = _build_wan22_ti2v_graph(prompt, '', settings, first_name, length, clip_device=preferred_device)
    write_json_atomic(str(output.with_suffix('.wan22.workflow.json')), graph, ensure_ascii=False, indent=2)
    response = _submit_comfy_graph(graph, on_progress, cancel_check)

    if response['status']['status_str'] != 'success' and preferred_device != 'cpu':
        status_blob = json.dumps(response['status'], ensure_ascii=False).lower()
        if any(token in status_blob for token in ('out of memory', 'cuda', 'oom', 'alloc', 'vram')):
            if on_progress:
                on_progress('VRAM yetersiz · Wan 2.2 metin kodlayıcı CPU moduna alınıyor…')
            try:
                comfy('free', {'unload_models': True, 'free_memory': True})
            except Exception:
                pass
            graph, saved = _build_wan22_ti2v_graph(prompt, '', settings, first_name, length, clip_device='cpu')
            write_json_atomic(str(output.with_suffix('.wan22.workflow.json')), graph, ensure_ascii=False, indent=2)
            response = _submit_comfy_graph(graph, on_progress, cancel_check)

    if response['status']['status_str'] != 'success':
        raise RuntimeError(json.dumps(response['status'], ensure_ascii=False)[-1800:])
    node_out = response['outputs'].get(saved) or {}
    items = node_out.get('videos') or node_out.get('images') or node_out.get('gifs') or []
    if not items:
        raise RuntimeError(f'Wan 2.2 video çıktı dosyası bulunamadı: {json.dumps(node_out, ensure_ascii=False)}')
    row = items[0]
    source = (COMFY / 'output' / row.get('subfolder', '') / row['filename']).resolve()
    if not source.is_relative_to(COMFY / 'output') or not source.is_file():
        raise ValueError('Geçersiz ComfyUI video çıktı yolu.')
    shutil.copyfile(source, output)


def freevideo(prompt, first, last, references, duration, output, settings, on_progress=None, cancel_check=None, *, unload_before=True):
    import os
    queue = comfy('queue')
    if queue.get('queue_running') or queue.get('queue_pending'):
        raise RuntimeError('ComfyUI başka bir üretim yapıyor. Bu sahnenin görselleri saklandı. İş bitince yeniden deneyin.')
    if unload_before:
        comfy('free', {'unload_models': True, 'free_memory': True})
    media = {'version': 1}
    if first:
        media['first'] = str(first.resolve())
    if last:
        media['last'] = str(last.resolve())
    if references and not first:
        media['references'] = [{'path': str(path.resolve()), 'kind': 'image'} for path in references]
    media_file = output.with_suffix('.media.json')
    prompt_file = output.with_suffix('.prompt.txt')
    shutil.rmtree(output.with_suffix('.artifacts'), ignore_errors=True)
    write_json_atomic(str(media_file), media, ensure_ascii=False, indent=2)
    prompt_file.write_text(prompt, encoding='utf-8')
    frames = max(39, round(duration * 24))
    cmd = [
        sys.executable, '-m', 'freevideo_engine.managed', '--root', FREEVIDEO, 'generate',
        '--prompt-file', prompt_file, '--media', media_file, '--out', output,
        '--width', settings['width'], '--height', settings['height'], '--frames', frames,
        '--seed', settings['seed'], '--no-two-pass', '--ram-reserve-gib', settings['ram_reserve_gib'],
    ]
    step_cache = os.getenv('STUDIO_FREEVIDEO_STEP_CACHE', 'easycache-av').strip().lower()
    if step_cache in ('easycache-av', 'fbcache'):
        cmd.extend(['--step-cache', step_cache])
    run(
        cmd,
        cwd=FREEVIDEO,
        timeout=7200,
        log_path=output.with_suffix('.log'),
        on_progress=on_progress,
        cancel_check=cancel_check,
    )


def release_script_model(identifier):
    if '11434' not in llm.base_url():
        return
    base = llm.base_url().removesuffix('/v1')
    try:
        httpx.post(f'{base}/api/generate', json={'model': identifier, 'keep_alive': 0}, timeout=30).raise_for_status()
    except httpx.HTTPError:
        pass


def movie_duration(path):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', str(path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout)


def hyperframes_cli():
    return WORKSPACE / 'hyperframes-tool' / 'node_modules' / 'hyperframes' / 'bin' / 'hyperframes.mjs'
