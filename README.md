# ShortsFlow

**Local-first AI animation & short-form series production studio.**  
Create multi-episode animated shorts, consistent cast & locations, voice-synced subtitles, and ready-to-publish videos on consumer hardware (**8 GB VRAM / 16 GB RAM**) — with zero cloud API fees.

> **Türkçe Özet:** ShortsFlow; yerel ekran kartınızda (8 GB VRAM / 16 GB RAM) çok bölümlü kısa animasyon dizileri, tutarlı karakter/mekan kadroları, sesle 1-1 eşleşen altyazılar ve yayına hazır YouTube Shorts / Reels / TikTok videoları üretmenizi sağlayan açık kaynaklı bir prodüksiyon stüdyosudur.

---

## Interface Preview

### Series Hub & Episode Management
![ShortsFlow Series Hub](./docs/screenshots/series-hub.png)

### 3-Stage Episode Workspace & Visual Storyboard
![ShortsFlow Episode Storyboard](./docs/screenshots/episode-storyboard.png)

### Video Library, Delivery Theater & Publish Pack
![ShortsFlow Delivery Theater](./docs/screenshots/delivery-theater.png)

---

## Key Features

- **Series → Episode → Scene Hierarchy:** Organize multi-episode shows with a shared **Series Bible** (visual style, aspect ratio, language, narrator voice, BGM, caption style) that automatically cascades to new episodes.
- **5-Step Creation Wizard:** Go from idea → live 20-second visual style previews → AI cast & location proposals → quality/format selection → live time & disk estimates.
- **3-Stage Episode Workspace (`Plan → Produce → Deliver`):**
  - Horizontal **Visual Storyboard Strip** + focused **Master–Detail Scene Editor** (debounced auto-save, `Ctrl+Z` undo, `J`/`K` scene navigation).
  - **Character & Location Consistency:** Reference sheets automatically conditioned across scenes, plus multi-character dialogue with per-character voices.
  - **Alternate Takes & Stale Detection:** Switch between prior takes (`first` / `last` / `clip` / `audio`) and get automatic warnings when script edits outdate generated assets.
  - **Automatic English Prompt Translation:** Write stories and prompts in Turkish (or any language); ShortsFlow translates visual/motion prompts to clean English before sending to diffusion models while keeping voiceover and subtitles in your chosen language.
- **1-to-1 Voice-Synced Subtitles & Auto-Ducking BGM:** Subtitles match exact spoken narration timings and sit cleanly in the lower safe zone, paired with royalty-free synthesized ambient music that ducks automatically during speech.
- **Persistent Production Queue & System Telemetry:** Live SSE updates, ETA estimates, job prioritization, humanized error diagnostics, 1-click local service launch, and live GPU VRAM / RAM / Disk monitoring.
- **Video Library & Publish Pack:** Unified gallery with sequential **Marathon Watch**, MP4 / SRT / ZIP export, and 1-click LLM-generated YouTube Shorts / TikTok / Reels titles, hooks, descriptions, and hashtags.

---

## Supported Quality Profiles (Bring Your Own Models)

ShortsFlow does **not** bundle any AI model weights. It orchestrates local open-source / open-weight engines installed on your machine:

| Profile | Image Engine | Video Engine | Typical Speed (RTX 5060 8 GB) |
|---|---|---|---|
| **Fast (Draft)** | FLUX.2 `[klein]` 4B FP8 (ComfyUI) | LTX-Video 0.9.8 Distilled FP8 (ComfyUI) | ~2–3 min / scene |
| **Balanced (Recommended)** | FLUX.2 `[klein]` 4B FP8 (ComfyUI) | MiniMax H3 INT8 (FreeVideo) | ~5 min / scene |
| **High (Cinematic)** | Qwen-Image-2.1 Turbo INT8 (ComfyUI) | MiniMax H3 INT8 (FreeVideo) | ~14 min / scene |
| **Still Motion** | Any image model | FFmpeg Ken Burns camera motion | ~30 sec / scene |

---

## Architecture

- **Backend:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, SQLite WAL job queue & document revision store, detached GPU worker process (`studio.worker`).
- **Frontend:** React 18, React Router, Vite, Lucide icons, Server-Sent Events (`/api/studio/events/stream`).
- **External Local Services (Out-of-Process):**
  - **Ollama** (or any OpenAI-compatible local LLM endpoint) for scriptwriting, prompt translation, cast proposals, and publish packs.
  - **ComfyUI** for image generation and LTX-Video.
  - **FreeVideo** *(optional)* for MiniMax H3 video generation.
  - **Piper CLI** *(optional external CLI)* for fast local multi-language TTS synthesis.
  - **FFmpeg** for crossfades, `yuv420p` H.264 encoding, subtitle burn-in, loudness normalization (`loudnorm`), and auto-ducking BGM mixing.

---

## Quick Start

### 1. Prerequisites
- Python 3.11+
- Node.js 18+
- `ffmpeg` and `ffprobe` on `PATH`
- [Ollama](https://ollama.com/) running locally (e.g., `ollama pull qwen3-vl:8b-instruct`)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) running on `http://127.0.0.1:8188`
- *(Optional)* External `piper` CLI installed separately for local TTS (`pip install piper-tts` in a dedicated environment or standalone Piper binary; set `STUDIO_PIPER_BIN` if not on `PATH`).

### 2. Backend Setup
```bash
git clone https://github.com/DenizEryilmaz/ShortsFlow.git
cd ShortsFlow

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

### 3. Frontend Build
```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Run ShortsFlow
```bash
python -m studio.app
```
Open **http://127.0.0.1:8010** in your browser.

### 5. Run Tests
```bash
pytest -v
```

---

## Third-Party Engine & Model Licenses

ShortsFlow itself is licensed under the **Apache License 2.0** (see [LICENSE](./LICENSE)).  
ShortsFlow does **not** redistribute any third-party engines, model weights, or voice checkpoints. When you download and use external engines or models on your own machine, **you are responsible for complying with their respective licenses**:

| Component | Integration Mode | License | Notes |
|---|---|---|---|
| **ShortsFlow** (this repo) | Core codebase | **Apache-2.0** | Permissive open source |
| **Ollama** | External HTTP API | MIT | Separate local server |
| **ComfyUI** | External HTTP API | GPL-3.0 | Separate local server |
| **FreeVideo** (engine code) | External CLI subprocess | Apache-2.0 | Separate local installation |
| **FFmpeg** | External CLI subprocess | LGPL / GPL | System binary |
| **Piper TTS** | External CLI subprocess | GPL-3.0-or-later | Invoked out-of-process via CLI (`STUDIO_PIPER_BIN`) |
| **Qwen3-VL-8B-Instruct** | Model weights (user-supplied) | **Apache-2.0** | Commercial & open-source friendly |
| **FLUX.2 `[klein]` 4B** | Model weights (user-supplied) | **Apache-2.0** | Commercial & open-source friendly *(larger 9B/dev variants are non-commercial)* |
| **LTX-Video 0.9.8** | Model weights (user-supplied) | LTX Open Weights / Community | Commercial free under revenue cap; check Lightricks terms |
| **MiniMax H3** | Model weights (user-supplied) | MiniMax H3 Community License | Revenue cap, attribution requirement, and regional restrictions (US/EU/UK/KR) — check MiniMax terms before commercial use |
| **Qwen-Image-2.1** | Model weights (user-supplied) | Qwen Research License | **Non-commercial** research/evaluation license for weights |
| **Piper Voices** (`rhasspy/piper-voices`) | Voice models (user-downloaded) | Per-voice `MODEL_CARD` | Licenses vary per voice dataset (CC0, CC-BY, research-only); inspect each voice's `MODEL_CARD` on Hugging Face |

---

## License

Copyright 2026 Deniz Eryilmaz.  
Licensed under the **Apache License, Version 2.0**. See [LICENSE](./LICENSE) for details.
