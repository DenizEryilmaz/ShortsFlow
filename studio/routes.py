"""Standalone Studio API router."""
import asyncio
import copy
import hashlib
import io
import json
import shutil
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from PIL import Image
from pydantic import BaseModel, Field, ValidationError

from . import llm, media, providers, system_info
from .models import WORKSPACE, catalog, install_voice, validate, voice_catalog, voice_path
from .pipeline import DEFAULT_PROMPT, resolve_prompt, save_generated_asset
from .schema import (
    SCHEMAS,
    GeneratedSceneBlock,
    Project,
    PublishMetadata,
    Scene,
    Series,
    Settings,
    WizardCastProposal,
)
from .store import Conflict, Store
from .style_examples import STYLE_EXAMPLES, build_style_demo_video, get_style_example, style_demo_status
from .worker import start

ASSET_MIME_TYPES = {
    'png': 'image/png',
    'wav': 'audio/wav',
    'mp4': 'video/mp4',
}


class QueueReorderRequest(BaseModel):
    job_ids: list[str] = Field(default_factory=list)


class WizardCastRequest(BaseModel):
    idea: str = Field(min_length=3, max_length=4000)
    style: str = 'animation_2d'
    language: str = 'tr'
    tone: str = ''
    audience: str = ''


class SeriesEpisodeRequest(BaseModel):
    name: str = ''
    brief: str = ''
    duration: int | None = None
    scene_count: int | None = None


class ExpandBlockRequest(BaseModel):
    scene_group: str = Field(min_length=1, max_length=160)
    summary: str = Field(min_length=5, max_length=4000)
    duration: int = Field(default=20, ge=5, le=60)
    shot_count: int = Field(default=4, ge=1, le=12)
    hybrid: bool = True


class SaveRequest(BaseModel):
    data: dict
    revision: int | None = None


class ProductionRequest(BaseModel):
    kind: Literal[
        'script', 'render', 'full',
        'scene_audio', 'scene_first', 'scene_last', 'scene_clip', 'scene_all', 'scene_rewrite',
    ] = 'render'
    scene_id: str | None = None
    regenerate_script: bool = False


class CharacterProductionRequest(BaseModel):
    settings: Settings = Field(default_factory=Settings)


async def _default_owner(_: Request) -> str:
    return 'local'


def router(data_root, owner_id=None):
    api = APIRouter(prefix='/api/studio')
    store = Store(Path(data_root))
    resolve_owner = owner_id or _default_owner

    async def owner(request):
        return str(await resolve_owner(request) or 'local')

    def get(user, identifier, kind=None):
        row = store.get(user, identifier)
        if not row or (kind and row['kind'] != kind):
            raise HTTPException(404, 'Kayıt bulunamadı.')
        return row

    def asset(user, identifier):
        return get(user, identifier, 'asset')

    def validate_document(user, kind, value):
        try:
            result = SCHEMAS[kind].model_validate(value).model_dump()
        except (ValidationError, KeyError) as error:
            raise HTTPException(422, str(error)) from error
        if kind == 'character':
            for identifier in result['references']:
                asset(user, identifier)
        if kind == 'project':
            for identifier in result['character_ids']:
                get(user, identifier, 'character')
            scenes = result['script']['scenes'] if result['script'] else []
            if len({scene['id'] for scene in scenes}) != len(scenes):
                raise HTTPException(422, 'Sahne kimlikleri benzersiz olmalı.')
            for scene in scenes:
                if not set(scene['character_ids']).issubset(result['character_ids']):
                    raise HTTPException(422, 'Sahnenin karakteri önce projeye eklenmeli.')
                if scene['speaker_id'] and scene['speaker_id'] not in result['character_ids']:
                    raise HTTPException(422, 'Konuşmacı projeye eklenmeli.')
                for key in ('first_asset', 'last_asset', 'audio_asset', 'clip_asset'):
                    if scene[key]:
                        asset(user, scene[key])
        return result

    @api.get('/catalog')
    async def models(request: Request):
        await owner(request)
        return {
            'models': await asyncio.to_thread(catalog),
            'default_prompt': DEFAULT_PROMPT,
            'voices': voice_catalog(),
            'styles': [
                {
                    **item,
                    'has_live_sample': (store.root / 'style_samples' / f"{item['id']}.png").is_file(),
                    'demo_status': style_demo_status(store.root, item['id']),
                    'sample_url': (
                        f"/api/studio/styles/{item['id']}/sample"
                        if (store.root / 'style_samples' / f"{item['id']}.png").is_file()
                        else item['default_preview']
                    ),
                    'example': get_style_example(item['id'], 'tr'),
                    'examples': {
                        'tr': get_style_example(item['id'], 'tr'),
                        'en': get_style_example(item['id'], 'en'),
                    },
                }
                for item in media.STYLE_CATALOG
            ],
        }

    @api.get('/styles')
    async def styles_list(request: Request):
        await owner(request)
        return {
            'styles': [
                {
                    **item,
                    'has_live_sample': (store.root / 'style_samples' / f"{item['id']}.png").is_file(),
                    'demo_status': style_demo_status(store.root, item['id']),
                    'sample_url': (
                        f"/api/studio/styles/{item['id']}/sample"
                        if (store.root / 'style_samples' / f"{item['id']}.png").is_file()
                        else item['default_preview']
                    ),
                    'example': get_style_example(item['id'], 'tr'),
                    'examples': {
                        'tr': get_style_example(item['id'], 'tr'),
                        'en': get_style_example(item['id'], 'en'),
                    },
                }
                for item in media.STYLE_CATALOG
            ]
        }

    @api.post('/styles/{style_id}/demo-scenes')
    async def generate_style_demo_scenes(style_id: str, request: Request, mode: str = 'balanced'):
        user = await owner(request)
        entry = next((item for item in media.STYLE_CATALOG if item['id'] == style_id), None)
        if entry is None:
            raise HTTPException(404, 'Stil bulunamadı.')
        video_mode = mode if mode in ('still', 'ltxv', 'balanced', 'video') else 'balanced'
        job = store.submit(
            user,
            'style_demo',
            {'style_id': style_id, 'style_name': entry['name'], 'video_mode': video_mode},
        )
        start(store.root)
        return job

    @api.get('/styles/{style_id}/example-video')
    async def style_example_video(style_id: str, request: Request, language: str = 'tr'):
        await owner(request)
        if style_id not in media.STYLE_PRESETS:
            raise HTTPException(404, 'Stil bulunamadı.')
        lang = 'en' if language == 'en' else 'tr'
        try:
            path = await asyncio.to_thread(build_style_demo_video, store.root, style_id, lang)
        except ValueError as error:
            raise HTTPException(404, str(error)) from error
        except Exception as error:
            raise HTTPException(500, f'Örnek video hazırlanamadı: {error}') from error
        return FileResponse(path, media_type='video/mp4')

    @api.post('/styles/{style_id}/example-project')
    async def create_style_example_project(style_id: str, request: Request, language: str = 'tr'):
        user = await owner(request)
        lang = 'en' if language == 'en' else 'tr'
        example = get_style_example(style_id, lang)
        if example is None:
            raise HTTPException(404, 'Bu stil için örnek proje bulunamadı.')
        installed_models = catalog()
        default_voice = next(
            (m['id'] for m in installed_models if m['kind'] == 'voice' and m.get('ready') and m.get('language') == lang),
            next((m['id'] for m in installed_models if m['kind'] == 'voice' and m.get('ready')), 'tr_TR-dfki-medium'),
        )
        default_script = next(
            (m['id'] for m in installed_models if m['kind'] == 'script' and m.get('ready')),
            'qwen3-vl:8b-instruct',
        )
        default_video = next(
            (m['id'] for m in installed_models if m['kind'] == 'video' and m.get('ready')),
            'freevideo-h3',
        )
        default_renderer = next(
            (m['id'] for m in installed_models if m['id'] == 'hyperframes' and m.get('ready')),
            'ffmpeg',
        )
        default_image = next(
            (m['id'] for m in installed_models if m['kind'] == 'image' and m.get('ready')),
            'qwen-image-21',
        )
        settings = Settings(
            script=default_script,
            image=default_image,
            video=default_video,
            voice=default_voice,
            renderer=default_renderer,
            language=lang,
            bgm_preset=example.get('bgm_preset', ''),
            transition=example.get('transition', 'cut'),
            caption_style=example.get('caption_style', 'shorts'),
        ).model_dump()
        project_data = Project(
            name=example['name'],
            brief=example['brief'],
            style=style_id,
            duration=example['duration'],
            scene_count=example['scene_count'],
            production_mode='staged',
            settings=settings,
            script=example['script'],
        ).model_dump()
        return store.save(user, 'project', project_data)

    @api.get('/styles/{style_id}/sample')
    async def style_sample_file(style_id: str, request: Request):
        await owner(request)
        if style_id not in media.STYLE_PRESETS:
            raise HTTPException(404, 'Stil bulunamadı.')
        path = (store.root / 'style_samples' / f'{style_id}.png').resolve()
        if not path.is_relative_to(store.root / 'style_samples') or not path.is_file():
            raise HTTPException(404, 'Canlı stil örneği henüz üretilmedi.')
        return FileResponse(path, media_type='image/png')

    @api.post('/styles/{style_id}/sample')
    async def generate_style_sample(style_id: str, request: Request):
        user = await owner(request)
        entry = next((item for item in media.STYLE_CATALOG if item['id'] == style_id), None)
        if entry is None:
            raise HTTPException(404, 'Stil bulunamadı.')
        settings = Settings().model_dump()
        try:
            validate(settings, kinds=('image',))
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        job = store.submit(
            user,
            'style_sample',
            {'style_id': style_id, 'style_name': entry['name'], 'settings': settings},
        )
        start(store.root)
        return job

    @api.get('/voices/catalog')
    async def voices_list(request: Request):
        await owner(request)
        return {'voices': voice_catalog()}

    @api.post('/voices/{voice_id}/install')
    async def voice_install(voice_id: str, request: Request):
        await owner(request)
        try:
            row = await asyncio.to_thread(install_voice, voice_id)
        except ValueError as error:
            raise HTTPException(404, str(error)) from error
        except Exception as error:
            raise HTTPException(502, f'Ses indirilemedi: {error}') from error
        return {'voice': row}

    @api.get('/voices/{voice_id}/preview')
    async def voice_preview(voice_id: str, request: Request):
        await owner(request)
        try:
            path = voice_path(voice_id)
        except ValueError as error:
            raise HTTPException(404, str(error)) from error
        cache_dir = store.root / 'voice_previews'
        cache_dir.mkdir(exist_ok=True)
        safe_name = voice_id.replace(':', '_')
        wav_path = cache_dir / f'{safe_name}.wav'
        if not wav_path.is_file():
            samples = {
                'tr': 'Merhaba, ShortsFlow ses önizlemesi. Bu sesle hikâyenizi anlatabilirsiniz.',
                'en': 'Hello, this is a ShortsFlow voice preview for your animated short.',
                'de': 'Hallo, dies ist eine Sprachvorschau aus ShortsFlow für deinen Kurzfilm.',
                'fr': 'Bonjour, voici un aperçu vocal de ShortsFlow pour votre court métrage.',
                'es': 'Hola, esta es una vista previa de voz de ShortsFlow para tu historia.',
                'it': 'Ciao, questa è un anteprima vocale di ShortsFlow per la tua storia.',
                'ru': 'Привет, это предварительный просмотр голоса ShortsFlow для вашего видео.',
                'pt': 'Olá, esta é uma prévia de voz do ShortsFlow para a sua história.',
            }
            if str(path).startswith('kokoro:'):
                lang_prefix = str(path).split(':')[2].split('-')[0]
            else:
                lang_prefix = voice_id.split('_')[0]
            sample_text = samples.get(lang_prefix, samples['en'])
            def _synth():
                voice = media.load_voice(path)
                media.synthesize(voice, sample_text, wav_path)
            await asyncio.to_thread(_synth)
        return FileResponse(wav_path, media_type='audio/wav')

    @api.get('/bgm')
    async def bgm_list(request: Request):
        await owner(request)
        return {
            'tracks': [
                {'id': row['id'], 'name': row['name'], 'description': row['description']}
                for row in media.BGM_CATALOG
            ],
            'aspect_ratios': [
                {'id': key, **val}
                for key, val in media.ASPECT_RATIOS.items()
            ],
        }

    @api.get('/bgm/{bgm_id}/preview')
    async def bgm_preview(bgm_id: str, request: Request):
        await owner(request)
        try:
            path = await asyncio.to_thread(media.ensure_bgm_file, bgm_id, store.root / 'bgm')
        except ValueError as error:
            raise HTTPException(404, str(error)) from error
        return FileResponse(path, media_type='audio/wav')

    @api.get('/library')
    async def library(request: Request):
        user = await owner(request)
        store.migrate_series(user)
        return {kind: store.list(user, kind) for kind in ('series', 'project', 'character', 'template')}

    @api.post('/series/{series_id}/episodes')
    async def create_series_episode(series_id: str, body: SeriesEpisodeRequest, request: Request):
        user = await owner(request)
        series_row = get(user, series_id, 'series')
        sdata = series_row['data']
        existing_eps = [
            row for row in store.list(user, 'project')
            if row['data'].get('series_id') == series_id
        ]
        next_ep = max((int(r['data'].get('episode') or 0) for r in existing_eps), default=0) + 1
        ep_name = (body.name or '').strip() or f"{sdata['name']} · Bölüm {next_ep:02d}"
        ep_data = Project(
            name=ep_name,
            brief=(body.brief or '').strip(),
            style=sdata.get('style', 'animation_2d'),
            duration=int(body.duration or sdata.get('episode_duration') or 30),
            series=sdata['name'],
            series_id=series_id,
            episode=next_ep,
            episode_count=max(int(sdata.get('episode_count') or 1), next_ep),
            scene_count=int(body.scene_count) if body.scene_count is not None else 0,
            production_mode='staged',
            character_ids=list(sdata.get('character_ids') or []),
            settings=Settings.model_validate(sdata.get('defaults') or {}).model_dump(),
        ).model_dump()
        return store.save(user, 'project', ep_data)

    @api.post('/series/{series_id}/render-all')
    async def render_series_all(series_id: str, request: Request):
        user = await owner(request)
        get(user, series_id, 'series')
        episodes = sorted(
            [row for row in store.list(user, 'project') if row['data'].get('series_id') == series_id],
            key=lambda r: int(r['data'].get('episode') or 0),
        )
        all_jobs = store.jobs(user)
        done_project_ids = {
            j['project_id'] for j in all_jobs
            if j['status'] == 'completed' and j['kind'] in ('render', 'full') and (j.get('result') or {}).get('video')
        }
        active_project_ids = {
            j['project_id'] for j in all_jobs
            if j['status'] in ('queued', 'running') and j['kind'] in ('render', 'full')
        }
        queued = []
        models_list = catalog()
        for ep in episodes:
            pid = ep['id']
            if pid in done_project_ids or pid in active_project_ids:
                continue
            project = ep['data']
            has_script = bool(project.get('script') and project['script'].get('scenes'))
            kind = 'render' if has_script else 'full'
            try:
                validate(project['settings'], kinds=('image', 'video', 'voice', 'renderer') if has_script else ('script', 'image', 'video', 'voice', 'renderer'))
            except ValueError:
                continue
            characters = [get(user, cid, 'character') for cid in project['character_ids']]
            snapshot = {
                'project': project,
                'project_revision': ep['revision'],
                'characters': characters,
                'models': models_list,
                'resolved_prompt': resolve_prompt(project, characters),
                'regenerate_script': not has_script,
            }
            created_job = store.submit(user, kind, snapshot, pid)
            queued.append(created_job['id'])
        if queued:
            start(store.root)
        return {'queued': queued, 'count': len(queued)}

    @api.post('/queue/prioritize/{identifier}')
    async def prioritize_queue_item(identifier: str, request: Request):
        user = await owner(request)
        try:
            return store.prioritize_job(user, identifier)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except Conflict as error:
            raise HTTPException(409, str(error)) from error

    @api.post('/queue/reorder')
    async def reorder_queue_items(body: QueueReorderRequest, request: Request):
        user = await owner(request)
        store.reorder_queue(user, body.job_ids)
        return {'ok': True}

    @api.get('/estimate')
    async def estimate_production(
        request: Request,
        episodes: int = 1,
        scenes: int = 6,
        image: str = 'flux2-klein-4b',
        video: str = 'freevideo-h3',
        aspect_ratio: str = '9:16',
        hybrid: bool = False,
    ):
        await owner(request)
        ep_count = max(1, min(24, episodes))
        sc_count = max(1, min(600, scenes))
        is_480p = aspect_ratio == '16:9-480p'
        img_sec = (14 if is_480p else 24) if image == 'flux2-klein-4b' else 240
        if hybrid:
            # Typical TV drama mix: 65% dialogue (~8s), 25% fast action (~40s), 10% camera (~4s)
            avg_vid = 0.65 * 8 + 0.25 * (40 if is_480p else 75) + 0.10 * 4
            avg_frames = 0.75 * 1 + 0.25 * 2
            per_ep_sec = round(sc_count * (avg_frames * img_sec + avg_vid + 3) + 30)
            est_mb = round(ep_count * sc_count * (4 if is_480p else 9) + ep_count * 25)
        else:
            vid_sec = (40 if is_480p else 75) if video == 'ltxv-distilled' else (5 if video == 'still-motion' else 195)
            per_ep_sec = sc_count * (2 * img_sec + vid_sec + 4) + 25
            est_mb = round(ep_count * sc_count * (7 if is_480p else (14 if video != 'still-motion' else 3)) + ep_count * 18)
        total_sec = ep_count * per_ep_sec
        return {
            'per_episode_seconds': per_ep_sec,
            'total_seconds': total_sec,
            'estimated_mb': est_mb,
        }

    @api.post('/projects/{identifier}/expand-block')
    async def expand_scene_block(identifier: str, body: ExpandBlockRequest, request: Request):
        user = await owner(request)
        record = get(user, identifier, 'project')
        pdata = copy.deepcopy(record['data'])
        existing_script = pdata.get('script') or {
            'title': pdata['name'],
            'logline': pdata.get('brief', ''),
            'continuity_note': '',
            'recommended_duration': pdata.get('duration', 30),
            'episode_plan': [],
            'scenes': [],
        }
        existing_scenes = list(existing_script.get('scenes') or [])
        if len(existing_scenes) + body.shot_count > 600:
            raise HTTPException(422, 'Bir bölüm en fazla 600 plan içerebilir.')
        chars = [get(user, cid, 'character') for cid in pdata.get('character_ids') or []]
        char_summary = '\n'.join(
            f"- id={c['id']} | name={c['data']['name']} ({c['data'].get('ingredient_type', 'character')}): {c['data'].get('description', '')}"
            for c in chars
        ) or 'No pre-defined characters.'
        recent_context = '\n'.join(
            f"- {s.get('scene_group') or ''} / {s.get('title')}: {s.get('narration', '')[:120]}"
            for s in existing_scenes[-4:]
        ) or 'Opening block of the episode.'
        lang = (pdata.get('settings') or {}).get('language', 'tr')
        lang_name = 'Turkish (Türkçe)' if lang == 'tr' else 'English'
        style_desc = media.STYLE_PRESETS.get(pdata.get('style', 'realistic_35mm'), media.STYLE_PRESETS['realistic_35mm'])
        per_shot = max(3, min(15, round(body.duration / max(1, body.shot_count))))
        hybrid_rule = (
            "Assign each shot's `shot_mode` smartly for fast TV episode production: "
            "use `'camera'` for establishing/atmosphere shots, `'dialogue'` for close-up/medium speaking character shots, "
            "`'action'` for physical movement shots, and `'hero'` only for a climax moment."
            if body.hybrid
            else "Set `shot_mode` to `'auto'` for all shots."
        )
        prompt = (
            f"Break this single TV drama scene block into EXACTLY {body.shot_count} continuous shots (~{per_shot}s each, total ~{body.duration}s).\n"
            f"Episode: {pdata['name']}\n"
            f"Visual style: {style_desc}\n"
            f"Scene block title: {body.scene_group}\n"
            f"Scene beat summary: {body.summary}\n"
            f"Previous shots for continuity:\n{recent_context}\n"
            f"Cast & locations (ONLY use these exact character_ids/speaker_id values when applicable):\n{char_summary}\n"
            f"Write `scene_group`, shot `title`, `narration`, and `caption` in {lang_name}.\n"
            f"Write `visual_prompt`, `end_prompt`, and `motion_prompt` in vivid cinematic English.\n"
            f"Use classic film coverage (e.g. establishing -> character A close-up -> character B reverse-shot -> reaction/action).\n"
            f"{hybrid_rule}\n"
            "Return JSON matching the schema."
        )
        installed = catalog()
        model_id = (pdata.get('settings') or {}).get('script') or next(
            (m['id'] for m in installed if m['kind'] == 'script' and m.get('ready')),
            llm.model_name(),
        )
        def _run_llm():
            try:
                parsed, _ = llm.generate_json(prompt, GeneratedSceneBlock, model=model_id)
                return parsed
            finally:
                providers.release_script_model(model_id)
        try:
            block = await asyncio.to_thread(_run_llm)
        except Exception as error:
            raise HTTPException(502, f'Sahne bloğu genişletilemedi: {error}') from error

        valid_cids = set(pdata.get('character_ids') or [])
        added = []
        group_name = (block.get('scene_group') or body.scene_group).strip()
        for raw_shot in block.get('shots') or []:
            shot = Scene(
                id=str(uuid.uuid4()),
                title=raw_shot['title'],
                scene_group=group_name,
                shot_mode=raw_shot.get('shot_mode', 'auto'),
                duration=raw_shot['duration'],
                narration=raw_shot['narration'],
                caption=raw_shot['caption'],
                shot_size=raw_shot.get('shot_size', 'medium'),
                camera_move=raw_shot.get('camera_move', 'static'),
                visual_prompt=raw_shot['visual_prompt'],
                end_prompt=raw_shot.get('end_prompt', ''),
                motion_prompt=raw_shot.get('motion_prompt', ''),
                negative_prompt=raw_shot.get('negative_prompt', ''),
                character_ids=[cid for cid in (raw_shot.get('character_ids') or []) if cid in valid_cids],
                speaker_id=raw_shot['speaker_id'] if raw_shot.get('speaker_id') in valid_cids else '',
            ).model_dump()
            added.append(shot)
        existing_script['scenes'] = [*existing_scenes, *added]
        pdata['script'] = existing_script
        total_dur = int(round(sum(float(s.get('duration') or 5) for s in existing_script['scenes'])))
        pdata['duration'] = max(pdata.get('duration', 10), min(2700, total_dur))
        saved = store.save(user, 'project', pdata, identifier, record['revision'])
        return {'project': saved, 'added_shots': added}

    @api.get('/system/status')
    async def get_system(request: Request):
        await owner(request)
        return await asyncio.to_thread(system_info.get_system_status, store.root)

    @api.post('/system/cache/clear')
    async def clear_system_cache(request: Request):
        await owner(request)
        freed_mb = await asyncio.to_thread(system_info.clear_cache, store.root)
        return {'freed_mb': freed_mb}

    @api.post('/system/service/{service_id}/start')
    async def start_system_service(service_id: str, request: Request):
        await owner(request)
        try:
            message = await asyncio.to_thread(system_info.start_service, service_id, store.root)
        except ValueError as error:
            raise HTTPException(400, str(error)) from error
        except Exception as error:
            raise HTTPException(500, f'Servis başlatılamadı: {error}') from error
        return {'message': message}

    @api.post('/wizard/propose-cast')
    async def wizard_propose_cast(body: WizardCastRequest, request: Request):
        await owner(request)
        lang_name = 'Turkish (Türkçe)' if body.language == 'tr' else 'English'
        style_desc = media.STYLE_PRESETS.get(body.style, media.STYLE_PRESETS['animation_2d'])
        prompt = (
            f"Design a charming cast and key location/prop for an animated short series.\n"
            f"Idea: {body.idea}\n"
            f"Style: {style_desc}\n"
            f"Tone: {body.tone or 'warm, engaging, cinematic'}\n"
            f"Audience: {body.audience or 'general'}\n"
            f"Write title, logline, and continuity_note in {lang_name}.\n"
            f"Propose 2 to 3 distinct characters (ingredient_type='character') and 1 main location (ingredient_type='location').\n"
            f"Write every ingredient's visual description in vivid English suitable for image reference generation, "
            f"and include a short voice_hint (e.g. 'warm male', 'energetic female').\n"
            f"Return JSON matching the schema."
        )
        installed = catalog()
        model_id = next((m['id'] for m in installed if m['kind'] == 'script' and m.get('ready')), llm.model_name())
        def _run_llm():
            try:
                parsed, _ = llm.generate_json(prompt, WizardCastProposal, model=model_id)
                return parsed
            finally:
                providers.release_script_model(model_id)
        try:
            proposal = await asyncio.to_thread(_run_llm)
        except Exception as error:
            raise HTTPException(502, f'Kadro önerisi oluşturulamadı: {error}') from error
        return proposal

    @api.post('/jobs/{identifier}/publish-pack')
    async def generate_publish_pack(identifier: str, request: Request):
        user = await owner(request)
        record = store.job(user, identifier)
        if record is None:
            raise HTTPException(404, 'Üretim bulunamadı.')
        result = record.get('result') or {}
        if result.get('publish'):
            return result['publish']
        proj = (record.get('snapshot') or {}).get('project') or {}
        script = proj.get('script') or {}
        lang = (proj.get('settings') or {}).get('language', 'tr')
        lang_name = 'Turkish (Türkçe)' if lang == 'tr' else 'English'
        scenes_summary = '\n'.join(
            f"- {s.get('title', '')}: {s.get('narration', '')}"
            for s in (script.get('scenes') or [])
        )
        prompt = (
            f"Write a compelling YouTube Shorts / TikTok / Instagram Reels publishing pack in {lang_name}.\n"
            f"Video title: {proj.get('name', 'Short Film')}\n"
            f"Series: {proj.get('series', '')}\n"
            f"Logline: {script.get('logline') or proj.get('brief', '')}\n"
            f"Scenes:\n{scenes_summary}\n"
            f"Return JSON with title (catchy <= 90 chars), hook (1-line opening caption), "
            f"description (2-3 crisp sentences), and hashtags (6-10 relevant tags starting with #)."
        )
        installed = catalog()
        model_id = next((m['id'] for m in installed if m['kind'] == 'script' and m.get('ready')), llm.model_name())
        def _run_llm():
            try:
                parsed, _ = llm.generate_json(prompt, PublishMetadata, model=model_id)
                return parsed
            finally:
                providers.release_script_model(model_id)
        try:
            meta = await asyncio.to_thread(_run_llm)
        except Exception as error:
            raise HTTPException(502, f'Yayın paketi oluşturulamadı: {error}') from error
        updated_result = {**result, 'publish': meta}
        store.finish(identifier, record['status'], updated_result, record.get('error'))
        return meta

    @api.get('/events/stream')
    async def events_stream(request: Request):
        user = await owner(request)

        async def generator():
            last_sig = ''
            ticks = 0
            while ticks < 120:
                if await request.is_disconnected():
                    break
                jobs_list = store.jobs(user)
                active = [j for j in jobs_list if j['status'] in ('running', 'queued')]
                payload = {
                    'running_count': sum(1 for j in active if j['status'] == 'running'),
                    'queued_count': sum(1 for j in active if j['status'] == 'queued'),
                    'jobs': jobs_list[:50],
                }
                sig = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                if sig != last_sig:
                    last_sig = sig
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                else:
                    yield ": keepalive\n\n"
                ticks += 1
                await asyncio.sleep(2.0 if active else 5.0)

        return StreamingResponse(generator(), media_type='text/event-stream')

    @api.post('/import-examples')
    async def import_examples(request: Request):
        user = await owner(request)
        choices = [
            ('gravity-ten-second', 'yer-cekimi-yok-olsa-10s.mp4', 'Yer çekimi yok olsa? · 10 sn', 'science_2d', 10),
            ('gutenberg-paper-cut', 'gutenbergin-matbaasi-10s.mp4', 'Gutenberg’in matbaası · 10 sn', 'paper_cut', 10),
            ('gravity-science-qwen', 'yercekimi-bir-anda-yok-olsa.mp4', 'Yer çekimi yok olsa? · 60 sn', 'science_2d', 60),
        ]
        imported = []
        known = {row['data'].get('brief') for row in store.list(user, 'project')}
        for folder, filename, title, style, duration in choices:
            origin = WORKSPACE / 'outputs' / folder
            source = origin / filename
            marker = f'Önceki üretimden içe aktarıldı · {folder}'
            if marker in known or not source.is_file():
                continue
            data = Project(name=title, style=style, duration=duration, brief=marker).model_dump()
            project = store.save(user, 'project', data)
            prompts = {path.name: path.read_text(encoding='utf-8') for path in origin.glob('*.prompt.txt')}
            job = store.submit(user, 'import', {'project': data, 'source': folder, 'prompts': prompts}, project['id'])
            destination = store.root / 'jobs' / job['id']
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination / 'final.mp4')
            store.finish(job['id'], 'completed', {'video': f'jobs/{job["id"]}/final.mp4', 'duration': duration})
            store.event(job['id'], 'Önceki video ve mevcut prompt dosyaları içe aktarıldı.')
            imported.append(project['id'])
        return {'imported': imported}

    @api.post('/documents/{kind}')
    async def create(kind: str, body: SaveRequest, request: Request):
        user = await owner(request)
        data = validate_document(user, kind, body.data)
        return store.save(user, kind, data)

    @api.put('/documents/{identifier}')
    async def update(identifier: str, body: SaveRequest, request: Request):
        user = await owner(request)
        current = get(user, identifier)
        data = validate_document(user, current['kind'], body.data)
        try:
            return store.save(user, current['kind'], data, identifier, body.revision)
        except Conflict as error:
            raise HTTPException(409, str(error)) from error

    @api.get('/documents/{identifier}/revisions')
    async def revisions(identifier: str, request: Request):
        user = await owner(request)
        get(user, identifier)
        return {'revisions': store.history(user, identifier)}

    @api.delete('/documents/{identifier}')
    async def remove_document(identifier: str, request: Request):
        user = await owner(request)
        try:
            kind = store.delete(user, identifier)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        return {'deleted': identifier, 'kind': kind}

    @api.post('/assets')
    async def upload(request: Request, file: UploadFile = File(...)):
        user = await owner(request)
        raw = await file.read(20 * 1024 * 1024 + 1)
        if len(raw) > 20 * 1024 * 1024:
            raise HTTPException(413, 'Görsel 20 MB sınırını aşıyor.')
        try:
            image = Image.open(io.BytesIO(raw))
            if image.width * image.height > 16_000_000:
                raise ValueError('Görsel en fazla 16 megapiksel olabilir.')
            image.load()
            image = image.convert('RGB')
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            raise HTTPException(422, 'Geçerli bir PNG/JPEG görseli yükleyin.') from error
        identifier = str(uuid.uuid4())
        path = store.root / 'assets' / f'{identifier}.png'
        path.parent.mkdir(exist_ok=True)
        image.save(path)
        row = store.save(
            user,
            'asset',
            {'name': file.filename, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()},
            identifier,
        )
        return {'id': row['id']}

    @api.post('/assets/audio')
    async def upload_audio(request: Request, file: UploadFile = File(...)):
        user = await owner(request)
        raw = await file.read(30 * 1024 * 1024 + 1)
        if len(raw) > 30 * 1024 * 1024:
            raise HTTPException(413, 'Ses dosyası 30 MB sınırını aşıyor.')
        identifier = str(uuid.uuid4())
        assets_dir = store.root / 'assets'
        assets_dir.mkdir(exist_ok=True)
        suffix = Path(file.filename or 'audio.mp3').suffix.lower()
        if suffix not in ('.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac'):
            raise HTTPException(422, 'Desteklenen ses formatları: MP3, WAV, OGG, M4A, AAC, FLAC.')
        temp_in = assets_dir / f'{identifier}.upload{suffix}'
        out_wav = assets_dir / f'{identifier}.wav'
        temp_in.write_bytes(raw)
        try:
            await asyncio.to_thread(
                providers.run,
                ['ffmpeg', '-y', '-i', temp_in, '-ar', '48000', '-ac', '2', out_wav],
            )
            if not out_wav.is_file() or out_wav.stat().st_size < 100:
                raise RuntimeError('Ses dosyası dönüştürülemedi.')
        except Exception as error:
            out_wav.unlink(missing_ok=True)
            raise HTTPException(422, f'Geçerli bir ses dosyası yükleyin: {error}') from error
        finally:
            temp_in.unlink(missing_ok=True)
        row = store.save(
            user,
            'asset',
            {'name': file.filename or 'bgm.wav', 'ext': 'wav', 'sha256': hashlib.sha256(out_wav.read_bytes()).hexdigest()},
            identifier,
        )
        return {'id': row['id'], 'name': row['data']['name']}

    @api.get('/assets/{identifier}')
    async def media_asset(identifier: str, request: Request):
        row = asset(await owner(request), identifier)
        ext = row['data'].get('ext', 'png')
        if ext not in ASSET_MIME_TYPES:
            raise HTTPException(404, 'Dosya türü desteklenmiyor.')
        path = store.root / 'assets' / f'{identifier}.{ext}'
        if not path.is_file():
            raise HTTPException(404, 'Dosya bulunamadı.')
        return FileResponse(path, media_type=ASSET_MIME_TYPES[ext])

    @api.post('/assets/{identifier}/last-frame')
    async def extract_last_frame(identifier: str, request: Request):
        user = await owner(request)
        row = asset(user, identifier)
        ext = row['data'].get('ext', 'png')
        if ext != 'mp4':
            raise HTTPException(422, 'Son kare yalnızca video klibinden çıkarılabilir.')
        source = store.root / 'assets' / f'{identifier}.mp4'
        if not source.is_file():
            raise HTTPException(404, 'Video dosyası bulunamadı.')
        temp = store.root / 'assets' / f'.extract-{uuid.uuid4().hex}.png'
        temp.parent.mkdir(exist_ok=True)
        try:
            await asyncio.to_thread(
                providers.run,
                ['ffmpeg', '-y', '-sseof', '-0.1', '-i', source, '-update', '1', '-frames:v', '1', temp],
            )
            new_id = save_generated_asset(store, user, temp, f"{row['data'].get('name', 'klip')} · son kare", ext='png')
        finally:
            if temp.exists():
                temp.unlink()
        return {'id': new_id}

    @api.post('/projects/{identifier}/jobs')
    async def generate(identifier: str, body: ProductionRequest, request: Request):
        user = await owner(request)
        project = get(user, identifier, 'project')
        data = project['data']
        kind = body.kind
        required_models = {
            'script': ('script',),
            'full': ('script', 'image', 'video', 'voice', 'renderer') if (body.regenerate_script or not data['script']) else ('image', 'video', 'voice', 'renderer'),
            'render': ('image', 'video', 'voice', 'renderer'),
            'scene_audio': ('voice',),
            'scene_first': ('image',),
            'scene_last': ('image',),
            'scene_clip': ('image', 'video'),
            'scene_all': ('image', 'video', 'voice'),
            'scene_rewrite': ('script',),
        }[kind]
        try:
            validate(data['settings'], kinds=required_models)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        if kind == 'render':
            if not data['script']:
                raise HTTPException(422, 'Önce senaryoyu hazırlayın.')
            if any(not s['narration'].strip() for s in data['script']['scenes']):
                raise HTTPException(422, 'Her sahne için seslendirme metni girin.')
        if kind == 'full' and (body.regenerate_script or not data['script']) and not data['brief'].strip():
            raise HTTPException(422, 'Full üretim için konu ve hikâye metnini girin.')
        if kind.startswith('scene_'):
            if not data['script'] or not body.scene_id:
                raise HTTPException(422, 'Hedef sahne seçilmedi.')
            scene = next((s for s in data['script']['scenes'] if s['id'] == body.scene_id), None)
            if scene is None:
                raise HTTPException(404, 'Sahne bulunamadı.')
            if kind in ('scene_audio', 'scene_all') and not scene['narration'].strip():
                raise HTTPException(422, 'Seslendirme üretmek için metin girin.')
            if kind == 'scene_last' and not scene['end_prompt'].strip():
                raise HTTPException(422, 'Son kare üretmek için bitiş karesi tarifini girin.')
        existing = store.find_active_job(user, identifier, kind, body.scene_id)
        if existing is not None:
            return existing
        characters = [get(user, value, 'character') for value in data['character_ids']]
        snapshot_project = copy.deepcopy(data)
        if kind == 'script' or (kind == 'full' and body.regenerate_script):
            snapshot_project['script'] = None
        snapshot = {
            'project': snapshot_project,
            'project_revision': project['revision'],
            'characters': characters,
            'resolved_prompt': resolve_prompt(data, characters),
            'models': catalog(),
            'scene_id': body.scene_id,
            'regenerate_script': body.regenerate_script,
        }
        job = store.submit(user, kind, snapshot, identifier)
        start(store.root)
        return job

    @api.post('/characters/{identifier}/generate')
    async def character(identifier: str, body: CharacterProductionRequest, request: Request):
        user = await owner(request)
        record = get(user, identifier, 'character')
        if not record['data']['description'].strip():
            raise HTTPException(422, 'Karakterin görünüşünü tarif edin.')
        settings = body.settings.model_dump()
        try:
            validate(settings, kinds=('image',))
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        asset_id = str(uuid.uuid4())
        store.save(user, 'asset', {'name': record['data']['name'], 'generated': True}, asset_id)
        job = store.submit(user, 'character', {'character': record, 'settings': settings, 'asset_id': asset_id})
        start(store.root)
        return job

    @api.get('/jobs')
    async def history(request: Request):
        return {'jobs': store.jobs(await owner(request))}

    @api.get('/jobs/{identifier}')
    async def status(identifier: str, request: Request):
        user = await owner(request)
        record = store.job(user, identifier)
        if record is None:
            raise HTTPException(404, 'Üretim bulunamadı.')
        prompt_dir = store.root / 'jobs' / identifier
        record['prompts'] = {}
        for path in prompt_dir.glob('*.prompts.json'):
            record['prompts'][path.stem] = json.loads(path.read_text(encoding='utf-8'))
        if record['status'] == 'queued':
            record['running_job'] = store.running_job(user)
        return record

    @api.post('/jobs/{identifier}/retry')
    async def retry(identifier: str, request: Request):
        user = await owner(request)
        if store.job(user, identifier) is None:
            raise HTTPException(404, 'Üretim bulunamadı.')
        with store.connect() as db:
            changed = db.execute(
                "UPDATE jobs SET status='queued',error=NULL WHERE id=? AND owner=? AND status='failed'",
                (identifier, user),
            ).rowcount
        if not changed:
            raise HTTPException(409, 'Yalnızca başarısız üretim yeniden denenebilir.')
        start(store.root)
        return store.job(user, identifier)

    @api.post('/jobs/{identifier}/cancel')
    async def cancel(identifier: str, request: Request):
        user = await owner(request)
        try:
            updated = store.cancel_job(user, identifier)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except Conflict as error:
            raise HTTPException(409, str(error)) from error
        if updated['status'] == 'running':
            await asyncio.to_thread(providers.interrupt_comfy)
        return updated

    @api.delete('/jobs/{identifier}')
    async def remove_job(identifier: str, request: Request):
        user = await owner(request)
        try:
            store.delete_job(user, identifier)
        except LookupError as error:
            raise HTTPException(404, str(error)) from error
        except Conflict as error:
            raise HTTPException(409, str(error)) from error
        job_dir = (store.root / 'jobs' / identifier).resolve()
        if job_dir.is_relative_to(store.root / 'jobs') and job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)
        return {'deleted': identifier}

    @api.get('/jobs/{identifier}/export.zip')
    async def export_bundle(identifier: str, request: Request):
        import zipfile

        record = store.job(await owner(request), identifier)
        if record is None:
            raise HTTPException(404, 'Üretim bulunamadı.')
        base = (store.root / 'jobs' / identifier).resolve()
        if not base.is_dir():
            raise HTTPException(404, 'Üretim klasörü bulunamadı.')
        bundle = base / 'export.zip'
        with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            for name in ('final.mp4', 'captions.srt', 'stages.json'):
                candidate = base / name
                if candidate.is_file():
                    zf.write(candidate, arcname=name)
            assets_dir = base / 'assets'
            if assets_dir.is_dir():
                for item in sorted(assets_dir.iterdir()):
                    if item.is_file() and item.suffix in ('.mp4', '.wav', '.png'):
                        zf.write(item, arcname=f'scenes/{item.name}')
        return FileResponse(bundle, media_type='application/zip', filename=f'story-studio-{identifier[:8]}.zip')

    @api.get('/jobs/{identifier}/files/{filename:path}')
    async def file(identifier: str, filename: str, request: Request):
        if store.job(await owner(request), identifier) is None:
            raise HTTPException(404, 'Üretim bulunamadı.')
        base = (store.root / 'jobs' / identifier).resolve()
        path = (base / filename).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            raise HTTPException(404, 'Dosya bulunamadı.')
        return FileResponse(path)

    return api, store
