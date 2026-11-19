"""Live service health, hardware telemetry (GPU/VRAM/RAM/Disk), cache management, and service startup."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import httpx

from . import llm
from .models import COMFY, COMFY_URL, FREEVIDEO, ROOT


def _dir_size_bytes(path: Path) -> int:
    if not path.is_dir():
        return 0
    total = 0
    for item in path.rglob('*'):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                pass
    return total


def _probe_http(url: str, timeout: float = 1.5) -> tuple[bool, str]:
    try:
        resp = httpx.get(url, timeout=timeout)
        if resp.status_code < 400:
            return True, 'Çalışıyor'
        return False, f'HTTP {resp.status_code}'
    except Exception:
        return False, 'Bağlanılamadı'


def _gpu_info() -> dict:
    try:
        out = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu', '--format=csv,noheader,nounits'],
            timeout=3,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        line = out.splitlines()[0]
        parts = [p.strip() for p in line.split(',')]
        return {
            'available': True,
            'name': parts[0],
            'vram_total_mb': int(float(parts[1])),
            'vram_used_mb': int(float(parts[2])),
            'vram_free_mb': int(float(parts[3])),
            'utilization_pct': int(float(parts[4])) if len(parts) > 4 else 0,
        }
    except Exception:
        return {'available': False, 'name': 'NVIDIA GPU algılanmadı', 'vram_total_mb': 0, 'vram_used_mb': 0, 'vram_free_mb': 0, 'utilization_pct': 0}


def _ram_info() -> dict:
    try:
        if os.name == 'nt':
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('ullAvailExtendedVirtual', ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_mb = int(stat.ullTotalPhys / (1024 * 1024))
            free_mb = int(stat.ullAvailPhys / (1024 * 1024))
            return {'total_mb': total_mb, 'used_mb': max(0, total_mb - free_mb), 'free_mb': free_mb}
    except Exception:
        pass
    return {'total_mb': 0, 'used_mb': 0, 'free_mb': 0}


def _worker_alive(data_root: Path) -> bool:
    lock_path = data_root / 'worker.lock'
    if not lock_path.is_file():
        return False
    try:
        with lock_path.open('a+b') as fh:
            if os.name == 'nt':
                import msvcrt
                try:
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
                    return False
                except OSError:
                    return True
            else:
                import fcntl
                try:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
                    return False
                except OSError:
                    return True
    except OSError:
        return False


def get_system_status(data_root: Path) -> dict:
    comfy_ok, comfy_msg = _probe_http(f'{COMFY_URL}/system_stats')
    ollama_ok, ollama_msg = _probe_http(f'{llm.base_url()}/models')
    ffmpeg_ok = shutil.which('ffmpeg') is not None
    worker_ok = _worker_alive(data_root)
    disk = shutil.disk_usage(data_root)
    cache_bytes = _dir_size_bytes(data_root / 'cache')
    jobs_bytes = _dir_size_bytes(data_root / 'jobs')
    assets_bytes = _dir_size_bytes(data_root / 'assets')

    return {
        'services': [
            {
                'id': 'comfyui',
                'name': 'ComfyUI (Görsel & LTX-Video)',
                'ready': comfy_ok,
                'detail': comfy_msg if not comfy_ok else f'Hazır · {COMFY_URL}',
                'can_start': not comfy_ok and (COMFY / 'main.py').is_file(),
            },
            {
                'id': 'ollama',
                'name': 'Ollama (Senaryo & Çeviri LLM)',
                'ready': ollama_ok,
                'detail': ollama_msg if not ollama_ok else f'Hazır · {llm.model_name()}',
                'can_start': not ollama_ok,
            },
            {
                'id': 'worker',
                'name': 'Üretim İşçisi (GPU Kuyruğu)',
                'ready': worker_ok,
                'detail': 'Aktif ve kuyruğu dinliyor' if worker_ok else 'Beklemede (iş gelince otomatik başlar)',
                'can_start': not worker_ok,
            },
            {
                'id': 'ffmpeg',
                'name': 'FFmpeg (Kurgu, Ses & Altyazı)',
                'ready': ffmpeg_ok,
                'detail': 'Kurulu ve hazır' if ffmpeg_ok else 'PATH üzerinde bulunamadı',
                'can_start': False,
            },
        ],
        'hardware': {
            'gpu': _gpu_info(),
            'ram': _ram_info(),
            'disk': {
                'total_gb': round(disk.total / 1e9, 1),
                'free_gb': round(disk.free / 1e9, 1),
                'used_gb': round(disk.used / 1e9, 1),
            },
        },
        'storage': {
            'cache_mb': round(cache_bytes / (1024 * 1024), 1),
            'jobs_mb': round(jobs_bytes / (1024 * 1024), 1),
            'assets_mb': round(assets_bytes / (1024 * 1024), 1),
            'freevideo_ready': (FREEVIDEO / 'machine.json').is_file(),
        },
    }


def clear_cache(data_root: Path) -> float:
    cache_dir = (data_root / 'cache').resolve()
    if not cache_dir.is_relative_to(data_root.resolve()) or not cache_dir.is_dir():
        return 0.0
    before = _dir_size_bytes(cache_dir)
    for child in list(cache_dir.iterdir()):
        try:
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
            else:
                child.unlink(missing_ok=True)
        except OSError:
            pass
    after = _dir_size_bytes(cache_dir)
    return round(max(0, before - after) / (1024 * 1024), 1)


def start_service(service_id: str, data_root: Path) -> str:
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) | getattr(subprocess, 'DETACHED_PROCESS', 0)
    if service_id == 'comfyui':
        py = COMFY / '.venv' / 'Scripts' / 'python.exe'
        if not py.is_file():
            py = Path(sys.executable)
        if not (COMFY / 'main.py').is_file():
            raise ValueError('ComfyUI dizini bulunamadı.')
        log = (data_root / 'comfyui-start.log').open('a', encoding='utf-8')
        subprocess.Popen(
            [
                str(py), 'main.py', '--listen', '127.0.0.1', '--port', '8188',
                '--disable-dynamic-vram', '--lowvram', '--disable-pinned-memory',
                '--disable-all-custom-nodes',
            ],
            cwd=COMFY,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
        return 'ComfyUI başlatılıyor (15-20 sn içinde hazır olur).'
    if service_id == 'ollama':
        exe = shutil.which('ollama') or str(Path(os.getenv('LOCALAPPDATA', '')) / 'Programs' / 'Ollama' / 'ollama.exe')
        if not Path(exe).is_file():
            raise ValueError('Ollama kurulumu bulunamadı.')
        log = (data_root / 'ollama-start.log').open('a', encoding='utf-8')
        subprocess.Popen([exe, 'serve'], stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        return 'Ollama başlatılıyor.'
    if service_id == 'worker':
        from .worker import start as start_worker
        start_worker(data_root)
        return 'Üretim işçisi başlatıldı.'
    raise ValueError(f'Bilinmeyen servis: {service_id}')
