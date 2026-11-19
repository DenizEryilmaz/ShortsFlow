"""Installed providers and curated open-source voice registry."""
import json
import os
from pathlib import Path

import httpx

from . import llm

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
COMFY = Path(os.getenv('STUDIO_COMFY_ROOT', WORKSPACE / 'ComfyUI-local')).resolve()
FREEVIDEO = Path(os.getenv('STUDIO_FREEVIDEO_ROOT', WORKSPACE / 'FreeVideo-local')).resolve()
COMFY_URL = os.getenv('STUDIO_COMFY_URL', 'http://127.0.0.1:8188').rstrip('/')

VOICE_REGISTRY = [
    {
        'id': 'tr_TR-dfki-medium',
        'label': 'Türkçe · DFKI (Erkek, net anlatım)',
        'language': 'tr',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/tr/tr_TR/dfki/medium/tr_TR-dfki-medium.onnx',
    },
    {
        'id': 'tr_TR-fahrettin-medium',
        'label': 'Türkçe · Fahrettin (Erkek, doğal ton)',
        'language': 'tr',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/tr/tr_TR/fahrettin/medium/tr_TR-fahrettin-medium.onnx',
    },
    {
        'id': 'tr_TR-fettah-medium',
        'label': 'Türkçe · Fettah (Erkek, derin ton)',
        'language': 'tr',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/tr/tr_TR/fettah/medium/tr_TR-fettah-medium.onnx',
    },
    {
        'id': 'en_US-lessac-high',
        'label': 'English US · Lessac High (Kadın, stüdyo anlatıcı)',
        'language': 'en',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/high/en_US-lessac-high.onnx',
    },
    {
        'id': 'en_US-ryan-high',
        'label': 'English US · Ryan High (Erkek, enerjik doğal)',
        'language': 'en',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/high/en_US-ryan-high.onnx',
    },
    {
        'id': 'en_GB-cori-high',
        'label': 'English UK · Cori High (Kadın, sıcak İngiliz)',
        'language': 'en',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/cori/high/en_GB-cori-high.onnx',
    },
    {
        'id': 'en_GB-northern_english_male-medium',
        'label': 'English UK · Northern Male (Erkek, masalsı karakter)',
        'language': 'en',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx',
    },
    {
        'id': 'en_US-lessac-medium',
        'label': 'English US · Lessac (Kadın, belgesel)',
        'language': 'en',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx',
    },
    {
        'id': 'en_US-ryan-medium',
        'label': 'English US · Ryan (Erkek, net)',
        'language': 'en',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx',
    },
    {
        'id': 'en_US-amy-medium',
        'label': 'English US · Amy (Kadın, sıcak)',
        'language': 'en',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx',
    },
    {
        'id': 'en_US-joe-medium',
        'label': 'English US · Joe (Erkek, anlatıcı)',
        'language': 'en',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/joe/medium/en_US-joe-medium.onnx',
    },
    {
        'id': 'en_GB-alba-medium',
        'label': 'English UK · Alba (Kadın, İskoç aksanı)',
        'language': 'en',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alba/medium/en_GB-alba-medium.onnx',
    },
    {
        'id': 'de_DE-thorsten-medium',
        'label': 'Deutsch · Thorsten (Erkek, net anlatım)',
        'language': 'de',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx',
    },
    {
        'id': 'fr_FR-siwis-medium',
        'label': 'Français · Siwis (Kadın, doğal ton)',
        'language': 'fr',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx',
    },
    {
        'id': 'es_ES-davefx-medium',
        'label': 'Español · Davefx (Erkek, anlatıcı)',
        'language': 'es',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx',
    },
    {
        'id': 'it_IT-paola-medium',
        'label': 'Italiano · Paola (Kadın, doğal)',
        'language': 'it',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/it/it_IT/paola/medium/it_IT-paola-medium.onnx',
    },
    {
        'id': 'ru_RU-dmitri-medium',
        'label': 'Русский · Dmitri (Erkek, anlatıcı)',
        'language': 'ru',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/ru/ru_RU/dmitri/medium/ru_RU-dmitri-medium.onnx',
    },
    {
        'id': 'pt_BR-faber-medium',
        'label': 'Português BR · Faber (Erkek, net)',
        'language': 'pt',
        'url': 'https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx',
    },
]
VOICE_LABELS = {row['id']: row['label'] for row in VOICE_REGISTRY}


def voice_catalog():
    piper_dir = ROOT / 'models' / 'piper'
    installed = {
        path.stem: path
        for path in sorted(piper_dir.glob('*.onnx'))
        if Path(f'{path}.json').is_file()
    }
    rows = []
    seen = set()
    for entry in VOICE_REGISTRY:
        vid = entry['id']
        seen.add(vid)
        path = installed.get(vid)
        rows.append({
            'id': vid,
            'name': entry['label'],
            'language': entry['language'],
            'installed': path is not None,
            'bytes': path.stat().st_size if path else None,
        })
    for vid, path in installed.items():
        if vid not in seen:
            rows.append({
                'id': vid,
                'name': f'Piper · {vid}',
                'language': vid.split('_')[0],
                'installed': True,
                'bytes': path.stat().st_size,
            })
    return rows


def install_voice(voice_id):
    entry = next((row for row in VOICE_REGISTRY if row['id'] == voice_id), None)
    if entry is None:
        raise ValueError('Bilinmeyen ses modeli.')
    piper_dir = ROOT / 'models' / 'piper'
    piper_dir.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=120) as client:
        for suffix in ('', '.json'):
            target = piper_dir / f'{voice_id}.onnx{suffix}'
            temp = target.with_suffix(target.suffix + '.tmp')
            response = client.get(entry['url'] + suffix)
            response.raise_for_status()
            temp.write_bytes(response.content)
            temp.replace(target)
    return next(row for row in voice_catalog() if row['id'] == voice_id)


def catalog():
    items = []
    try:
        response = httpx.get(f'{llm.base_url()}/models', timeout=3)
        response.raise_for_status()
        for row in response.json()['data']:
            items.append(dict(id=row['id'], kind='script', name=row['id'], ready=True))
    except (httpx.HTTPError, KeyError, ValueError):
        items.append(dict(id=llm.model_name(), kind='script', name=llm.model_name(),
                          ready=False, reason='Yerel dil modeli sunucusuna ulaşılamadı.'))
    flux2_files = [
        'diffusion_models/flux-2-klein-4b-fp8.safetensors',
        'text_encoders/qwen_3_4b_fp4_flux2.safetensors',
        'vae/flux2-vae.safetensors',
    ]
    flux2_ready = all((COMFY / 'models' / name).is_file() for name in flux2_files)
    items.append(dict(
        id='flux2-klein-4b',
        kind='image',
        name='FLUX.2 [klein] 4B FP8 (Çok Hızlı)',
        ready=flux2_ready,
        capabilities=['text2img', 'references', '4-step-fast'],
        files=[dict(name=name, bytes=(COMFY / 'models' / name).stat().st_size,
                    modified_ns=(COMFY / 'models' / name).stat().st_mtime_ns)
               for name in flux2_files if (COMFY / 'models' / name).is_file()],
        reason='' if flux2_ready else 'FLUX.2 [klein] 4B model dosyaları eksik (indiriliyor olabilir).',
    ))
    qwen_files = ['diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors',
                  'text_encoders/qwen3vl_8b_w4a8.safetensors', 'vae/qwen_image_2.1_vae_bf16.safetensors']
    ready = all((COMFY / 'models' / name).is_file() for name in qwen_files)
    items.append(dict(id='qwen-image-21', kind='image', name='Qwen Image 2.1 Turbo INT8',
                      ready=ready, capabilities=['text2img', 'references'],
                      files=[dict(name=name, bytes=(COMFY / 'models' / name).stat().st_size,
                                  modified_ns=(COMFY / 'models' / name).stat().st_mtime_ns)
                             for name in qwen_files if (COMFY / 'models' / name).is_file()],
                      reason='' if ready else 'ComfyUI model dosyaları eksik.'))
    ltxv_files = [
        'checkpoints/ltxv-2b-0.9.8-distilled-fp8.safetensors',
        'text_encoders/t5xxl_fp8_e4m3fn_scaled.safetensors',
    ]
    ltxv_ready = all((COMFY / 'models' / name).is_file() for name in ltxv_files)
    items.append(dict(
        id='ltxv-distilled',
        kind='video',
        name='LTX-Video 0.9.8 Distilled FP8 (Hızlı)',
        ready=ltxv_ready,
        capabilities=['img2vid', 'first-last', '8-step-fast'],
        files=[dict(name=name, bytes=(COMFY / 'models' / name).stat().st_size,
                    modified_ns=(COMFY / 'models' / name).stat().st_mtime_ns)
               for name in ltxv_files if (COMFY / 'models' / name).is_file()],
        reason='' if ltxv_ready else 'LTX-Video checkpoint veya T5 text encoder eksik.',
    ))
    machine = FREEVIDEO / 'machine.json'
    configuration = json.loads(machine.read_text(encoding='utf-8')) if machine.is_file() else {}
    items.append(dict(id='freevideo-h3', kind='video', name='FreeVideo · MiniMax H3 INT8',
                      ready=bool(configuration.get('ready')),
                      version=configuration.get('engine_version'),
                      revision=configuration.get('model_revision'),
                      capabilities=['text2video', 'first_frame', 'last_frame', 'references'],
                      reason='' if machine.is_file() else 'FreeVideo kurulumu bulunamadı.'))
    items.append(dict(id='still-motion', kind='video', name='Görsel ve kamera hareketi', ready=True,
                      capabilities=['first_frame']))
    for path in sorted((ROOT / 'models' / 'piper').glob('*.onnx')):
        if Path(f'{path}.json').is_file():
            items.append(dict(id=path.stem, kind='voice', name=VOICE_LABELS.get(path.stem, f'Piper · {path.stem}'),
                              bytes=path.stat().st_size, modified_ns=path.stat().st_mtime_ns,
                              language=path.stem.split('_')[0], ready=True))
    items.append(dict(id='ffmpeg', kind='renderer', name='FFmpeg', ready=True))
    hyper = WORKSPACE / 'hyperframes-tool' / 'node_modules' / 'hyperframes' / 'bin' / 'hyperframes.mjs'
    items.append(dict(id='hyperframes', kind='renderer', name='HyperFrames', ready=hyper.is_file()))
    return items


def validate(settings, items=None, kinds=('script', 'image', 'video', 'voice', 'renderer')):
    items = items if items is not None else catalog()
    for kind in kinds:
        if not any(row['id'] == settings[kind] and row['kind'] == kind and row['ready'] for row in items):
            raise ValueError(f'Seçili {kind} modeli hazır değil: {settings[kind]}')
    if settings.get('language', 'tr') not in ('tr', 'en'):
        raise ValueError('Desteklenen diller Türkçe ve İngilizce.')


def voice_path(identifier):
    candidates = {path.stem: path for path in (ROOT / 'models' / 'piper').glob('*.onnx')}
    if identifier not in candidates or not Path(f'{candidates[identifier]}.json').is_file():
        raise ValueError('Ses modeli bulunamadı.')
    return candidates[identifier]
