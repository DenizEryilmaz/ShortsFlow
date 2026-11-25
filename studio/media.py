"""Audio synthesis (Piper CLI), narration verification, subtitles and curated visual styles."""
import array
import math
import os
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

STYLE_CATALOG = [
    {
        "id": "animation_2d",
        "name": "2D Animasyon",
        "tagline": "El boyaması guaj dokulu, sıcak sinematik 2D animasyon",
        "description": "Temiz siluetler, sıcak ışık-gölge geçişleri ve hikâye anlatımına uygun el boyaması 2D animasyon görünümü.",
        "prompt": "stylized 2D animation, hand-painted gouache textures, clean expressive shapes, warm cinematic palette",
        "palette": ["#1c3238", "#d98845", "#f4d399", "#526b5c"],
        "default_preview": "/styles/animation_2d.png",
        "sample_subject": "A cozy sunlit hilltop workshop with glowing brass lanterns and floating golden dust motes",
    },
    {
        "id": "paint_storybook",
        "name": "Masal Kitabı",
        "tagline": "Suluboya ve fırça darbeleriyle illüstrasyon hissi",
        "description": "Görünür fırça izleri, yumuşak suluboya katmanları ve nostaljik çocuk/masal kitabı karesi.",
        "prompt": "storybook painting, visible brush strokes, gouache and watercolor, illustrated film still",
        "palette": ["#f5d5a7", "#e89f71", "#5e7260", "#7c5c6b"],
        "default_preview": "/styles/paint_storybook.svg",
        "sample_subject": "A small wooden cottage on a misty golden meadow at dusk with warm glowing windows",
    },
    {
        "id": "science_2d",
        "name": "Bilim Animasyonu",
        "tagline": "Net diyagramlar, sade kompozisyon ve açıklayıcı görseller",
        "description": "Eğitici bilim ve belgesel anlatımları için yüksek okunurluklu, temiz şekilli 2D sahneler.",
        "prompt": "educational 2D animation, hand-painted diagrams, clean shapes, playful but precise",
        "palette": ["#142c33", "#2b5b63", "#f08c3a", "#efe7d2"],
        "default_preview": "/styles/science_2d.png",
        "sample_subject": "A clean laboratory desk with a floating orange mechanical alarm clock and subtle beam of window light",
    },
    {
        "id": "paper_cut",
        "name": "Paper-Cut",
        "tagline": "Katmanlı el kesimi kâğıt ve gerçekçi gölgeler",
        "description": "Lifli renkli kâğıt katmanları, keskin kâğıt kenarları ve stop-motion derinlik gölgeleri.",
        "prompt": "layered cut-paper illustration, visibly fibrous colored paper, cut edges, cast shadows, stop motion animation",
        "palette": ["#d8c3a5", "#a44a3f", "#3a5a68", "#2d2620"],
        "default_preview": "/styles/paper_cut.jpg",
        "sample_subject": "An artisan wooden printing press workshop crafted from layered textured colored paper cutouts",
    },
    {
        "id": "anime_cel",
        "name": "Anime Cel",
        "tagline": "El çizimi anime karesi, net mürekkep hatları ve canlı gökyüzü",
        "description": "Klasik el çizimi anime sineması hissi; belirgin konturlar, yumuşak cel gölgeleme ve zengin arka planlar.",
        "prompt": "hand-drawn 2D anime film cel, crisp ink lineart, soft cel shading, lush painterly background, warm atmospheric lighting",
        "palette": ["#2e79c7", "#7ec4eb", "#5ca95e", "#ffffff"],
        "default_preview": "/styles/anime_cel.svg",
        "sample_subject": "A green hillside overlooking a sunlit summer sky filled with towering cumulus clouds and power lines",
    },
    {
        "id": "clay_stopmotion",
        "name": "Kil Stop-Motion",
        "tagline": "Minyatür set, parmak izi dokulu kil karakter ve stüdyo ışığı",
        "description": "El yapımı claymation stop-motion görünümü; yumuşak stüdyo ışığı ve sığ alan derinliği.",
        "prompt": "handcrafted claymation stop-motion frame, visible fingerprint clay texture, miniature diorama set, soft studio key light, shallow depth of field",
        "palette": ["#f2dcc2", "#e07a52", "#4e8f70", "#7d614d"],
        "default_preview": "/styles/clay_stopmotion.svg",
        "sample_subject": "A charming miniature handcrafted clay traveler standing on a tiny sculpted mossy hill",
    },
    {
        "id": "noir_comic",
        "name": "Çizgi Roman / Noir",
        "tagline": "Yüksek kontrastlı mürekkep gölgeleri ve grafik roman dokusu",
        "description": "Dramatik kenar ışıkları, yoğun siyah gölgeler, halftone baskı dokusu ve kehribar vurgular.",
        "prompt": "graphic novel ink illustration, bold black shadows, halftone print texture, dramatic rim lighting, limited amber and slate palette",
        "palette": ["#080a0e", "#1d222c", "#e59a42", "#f0b05d"],
        "default_preview": "/styles/noir_comic.svg",
        "sample_subject": "A lone trench-coated detective under a single amber streetlamp on a rain-slicked alley",
    },
    {
        "id": "pixel_retro",
        "name": "Retro Piksel",
        "tagline": "16-bit el yapımı piksel sanat ve nostaljik atmosfer",
        "description": "Keskin piksel ızgarası, atmosferik renk geçişleri ve bağımsız oyun sinematografisi.",
        "prompt": "crisp 16-bit pixel art scene, handcrafted sprite shading, atmospheric dithering, nostalgic indie game cinematography",
        "palette": ["#1b1c36", "#5e3d6b", "#c76b62", "#ffe699"],
        "default_preview": "/styles/pixel_retro.svg",
        "sample_subject": "A twilight pixel-art mountain cabin with a glowing warm window under a starry purple sky",
    },
    {
        "id": "realistic_35mm",
        "name": "Sinematik Fotogerçekçi (35mm)",
        "tagline": "Gerçek kamera, 35mm sinema lensi ve doğal film dokusu",
        "description": "Canlı aksiyon TV dizileri için ARRI Alexa sinematografisi, doğal cilt dokusu, sığ alan derinliği ve gerçekçi ışık.",
        "prompt": "photorealistic 35mm cinema film still, shot on ARRI Alexa, natural skin texture, subtle film grain, shallow depth of field, authentic live-action TV drama lighting",
        "palette": ["#141923", "#2d3c4e", "#c98b54", "#e7d8c3"],
        "default_preview": "/styles/realistic_35mm.svg",
        "sample_subject": "A rainy nocturnal city cafe seen through glass, warm tungsten table lamps reflecting on wet cobblestone street outside",
    },
    {
        "id": "documentary_4k",
        "name": "Belgesel · Doğal Kamera",
        "tagline": "Doğal gün ışığı, gerçekçi belgesel ve haber kamerası görünümü",
        "description": "Abartısız renkler, keskin optik odak, doğal dış/iç mekan ışığı ile gerçek hayat belgesel ve anlatım çekimleri.",
        "prompt": "authentic natural-light documentary film still, crisp 50mm lens, true-to-life colors, candid real-world cinematography, natural shadows",
        "palette": ["#1c262b", "#455a64", "#8d99ae", "#edf2f4"],
        "default_preview": "/styles/documentary_4k.svg",
        "sample_subject": "A bustling sunlit coastal harbor at golden morning hour, fishermen preparing wooden boats beside calm turquoise water",
    },
]

STYLE_PRESETS = {item["id"]: item["prompt"] for item in STYLE_CATALOG}

ASPECT_RATIOS = {
    "9:16": {"label": "9:16 Dikey (Shorts / Reels)", "width": 448, "height": 768, "out_width": 1080, "out_height": 1920},
    "16:9": {"label": "16:9 Yatay (YouTube 1080p)", "width": 768, "height": 448, "out_width": 1920, "out_height": 1080},
    "16:9-480p": {"label": "16:9 · 480p Hızlı Dizi (832×480)", "width": 832, "height": 480, "out_width": 854, "out_height": 480},
    "1:1": {"label": "1:1 Kare (Sosyal medya)", "width": 576, "height": 576, "out_width": 1080, "out_height": 1080},
}

BGM_CATALOG = [
    {
        "id": "calm_ambient",
        "name": "Sakin Ambiyans",
        "description": "Sıcak, yumuşak armonik pad · hikâye ve anlatım için sakin arka plan",
        "chords": [(261.63, 329.63, 392.00), (220.00, 261.63, 329.63), (174.61, 220.00, 261.63), (196.00, 246.94, 293.66)],
        "pulse_hz": 0.25,
    },
    {
        "id": "science_pulse",
        "name": "Bilim & Belgesel",
        "description": "Modern minimalist elektronik nabız · eğitici ve teknoloji içerikleri",
        "chords": [(293.66, 440.00, 523.25), (261.63, 392.00, 493.88), (220.00, 329.63, 440.00), (246.94, 369.99, 440.00)],
        "pulse_hz": 1.0,
    },
    {
        "id": "warm_story",
        "name": "Masal & Hikâye",
        "description": "Yumuşak arpejli sıcak tonlar · çocuk, masal ve duygusal anlatımlar",
        "chords": [(261.63, 329.63, 392.00, 493.88), (246.94, 293.66, 392.00, 493.88), (220.00, 261.63, 329.63, 392.00), (196.00, 246.94, 293.66, 392.00)],
        "pulse_hz": 0.5,
    },
]


def ensure_bgm_file(bgm_id: str, cache_dir: Path) -> Path:
    """Synthesize and cache a clean, seamless royalty-free stereo WAV loop for a built-in BGM preset."""
    import array

    entry = next((item for item in BGM_CATALOG if item["id"] == bgm_id), None)
    if entry is None:
        raise ValueError(f"Bilinmeyen arka plan müziği: {bgm_id}")
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    target = cache_dir / f"{bgm_id}.wav"
    if target.is_file() and target.stat().st_size > 1000:
        return target

    sr = 24000
    chords = entry["chords"]
    bar_sec = 4.0
    total_sec = bar_sec * len(chords)
    total_samples = int(sr * total_sec)
    pulse_hz = entry["pulse_hz"]
    samples = array.array("h")
    two_pi = 2.0 * math.pi

    for i in range(total_samples):
        t = i / sr
        bar_idx = int(t // bar_sec) % len(chords)
        bar_t = t % bar_sec
        chord = chords[bar_idx]
        # Smooth crossfade envelope per bar so chord changes never click
        env = min(1.0, bar_t / 0.35) * min(1.0, (bar_sec - bar_t) / 0.35)
        mod = 0.72 + 0.28 * math.sin(two_pi * pulse_hz * t)
        val_l = 0.0
        val_r = 0.0
        for idx, freq in enumerate(chord):
            base = math.sin(two_pi * freq * t)
            warm = 0.22 * math.sin(two_pi * (freq * 2.0) * t)
            sub = 0.28 * math.sin(two_pi * (freq * 0.5) * t) if idx == 0 else 0.0
            note = base + warm + sub
            pan = 0.38 + 0.24 * ((idx % 2) * 2 - 1)
            val_l += note * (1.0 - pan)
            val_r += note * pan
        scale = (0.28 / len(chord)) * (0.35 + 0.65 * env) * mod
        # Gentle loop boundary smoothing
        edge = min(1.0, t / 0.15, (total_sec - t) / 0.15)
        s_l = max(-32767, min(32767, int(val_l * scale * edge * 32767)))
        s_r = max(-32767, min(32767, int(val_r * scale * edge * 32767)))
        samples.append(s_l)
        samples.append(s_r)

    tmp = target.with_suffix(".tmp")
    with wave.open(str(tmp), "wb") as wav:
        wav.setparams((2, 2, sr, 0, "NONE", "not compressed"))
        wav.writeframes(samples.tobytes())
    tmp.replace(target)
    return target


def _piper_command() -> list[str]:
    """Resolve external Piper CLI command (kept out-of-process from Apache-2.0 app code)."""
    explicit = os.getenv("STUDIO_PIPER_BIN", "").strip()
    if explicit:
        return [explicit]
    found = shutil.which("piper")
    if found:
        return [found]
    return [sys.executable, "-m", "piper"]


def load_voice(path: str | Path) -> str | Path:
    """Validate and return a Piper ONNX voice path or a Kokoro-82M voice descriptor."""
    text_path = str(path)
    if text_path.startswith("kokoro:"):
        kokoro_dir = Path(__file__).resolve().parents[1] / "models" / "kokoro"
        if not (kokoro_dir / "kokoro-v1.0.onnx").is_file() or not (kokoro_dir / "voices-v1.0.bin").is_file():
            raise RuntimeError("Kokoro-82M model dosyaları eksik.")
        return text_path
    voice = Path(path)
    if not voice.is_file() or not Path(f"{voice}.json").is_file():
        raise RuntimeError(f"Piper ses modeli veya yapılandırması eksik: {voice}")
    return voice


def _synthesize_kokoro(descriptor: str, text: str, output_path: Path) -> None:
    """Run Kokoro-82M synthesis out-of-process on CPU (zero VRAM, clean license isolation)."""
    parts = descriptor.split(":")
    voice_name = parts[1] if len(parts) > 1 else "af_heart"
    lang_code = parts[2] if len(parts) > 2 else "en-us"
    kokoro_dir = Path(__file__).resolve().parents[1] / "models" / "kokoro"
    onnx_path = kokoro_dir / "kokoro-v1.0.onnx"
    voices_path = kokoro_dir / "voices-v1.0.bin"
    script = (
        "import array, sys, wave; "
        "from kokoro_onnx import Kokoro; "
        "k = Kokoro(sys.argv[1], sys.argv[2]); "
        "text = sys.stdin.read().strip(); "
        "samples, sr = k.create(text, voice=sys.argv[3], speed=1.0, lang=sys.argv[4]); "
        "pcm = array.array('h', (max(-32767, min(32767, int(x * 32767))) for x in samples)); "
        "w = wave.open(sys.argv[5], 'wb'); "
        "w.setparams((1, 2, sr, 0, 'NONE', 'not compressed')); "
        "w.writeframes(pcm.tobytes()); w.close()"
    )
    env = {**os.environ, "ONNX_PROVIDER": "CPUExecutionProvider"}
    result = subprocess.run(
        [sys.executable, "-c", script, str(onnx_path), str(voices_path), voice_name, lang_code, str(output_path)],
        input=text.encode("utf-8"),
        capture_output=True,
        env=env,
        timeout=120,
    )
    if result.returncode != 0 or not output_path.is_file():
        err = (result.stderr or b"").decode("utf-8", errors="replace")[-600:]
        raise RuntimeError(f"Kokoro-82M ses üretimi başarısız oldu: {err or f'çıkış kodu {result.returncode}'}")


def synthesize(voice: str | Path, text: str, output: Path) -> float:
    """Synthesize ``text`` to a WAV file via Kokoro-82M or Piper CLI and verify audible speech."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Seslendirme metni boş.")
    voice_ref = load_voice(voice)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(voice_ref, str) and voice_ref.startswith("kokoro:"):
        _synthesize_kokoro(voice_ref, cleaned, output_path)
    else:
        cmd = [*_piper_command(), "-m", str(voice_ref), "-f", str(output_path)]
        result = subprocess.run(
            cmd,
            input=cleaned.encode("utf-8"),
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0 or not output_path.is_file():
            err = (result.stderr or b"").decode("utf-8", errors="replace")[-600:]
            raise RuntimeError(f"Piper ses üretimi başarısız oldu: {err or f'çıkış kodu {result.returncode}'}")
    with wave.open(str(output_path), "rb") as wav:
        frames = wav.getnframes()
        sample_rate = wav.getframerate()
        raw = wav.readframes(frames)
    if frames == 0 or sample_rate <= 0:
        raise RuntimeError("Ses sentezleyici duyulabilir ses üretmedi.")
    samples = array.array("h")
    samples.frombytes(raw[: (len(raw) // 2) * 2])
    peak = max((abs(s) for s in samples), default=0) / 32768.0
    if peak < 0.01 or not math.isfinite(peak):
        raise RuntimeError("Ses sentezleyici duyulabilir ses üretmedi.")
    return frames / sample_rate


def verify_narration(path: Path) -> None:
    """Ensure the rendered MP4 has a non-silent audio track."""
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-map", "0:a:0", "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    if result.returncode:
        raise RuntimeError(f"ffmpeg: {result.stderr[-900:]}")
    peak = re.search(r"max_volume:\s+(-?\d+(?:\.\d+)?) dB", result.stderr)
    if peak is None or float(peak[1]) < -30:
        raise RuntimeError("MP4 ses kontrolünden geçemedi.")


def srt_time(seconds: float) -> str:
    """Format a timestamp in seconds as an SRT timecode."""
    ms = int(round(max(0.0, seconds) * 1000))
    hours, ms = divmod(ms, 3600000)
    minutes, ms = divmod(ms, 60000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def timed_caption_cues(text: str, start: float, duration: float, max_words: int = 6) -> list[tuple[float, float, str]]:
    """Split spoken narration into 1-to-1 voice-synced subtitle cues proportional to character length."""
    cleaned = " ".join((text or "").split())
    if not cleaned or duration <= 0:
        return []
    words = cleaned.split(" ")
    if len(words) <= max_words:
        return [(start, start + duration, cleaned)]

    # Prefer splitting at a natural punctuation boundary near the middle when 2 chunks suffice
    chunks: list[str] = []
    if len(words) <= max_words * 2:
        mid = len(words) // 2
        best_split = mid
        for offset in range(0, 3):
            for idx in (mid - offset, mid + offset):
                if 2 <= idx <= len(words) - 2 and words[idx - 1][-1] in ",;:.!?—":
                    best_split = idx
                    break
            else:
                continue
            break
        chunks = [" ".join(words[:best_split]), " ".join(words[best_split:])]
    else:
        for i in range(0, len(words), max_words):
            chunks.append(" ".join(words[i:i + max_words]))

    total_chars = sum(max(1, len(c)) for c in chunks)
    cues: list[tuple[float, float, str]] = []
    cursor = start
    for idx, chunk in enumerate(chunks):
        if idx == len(chunks) - 1:
            end = start + duration
        else:
            share = duration * (max(1, len(chunk)) / total_chars)
            end = cursor + share
        cues.append((cursor, end, chunk))
        cursor = end
    return cues
