"""Scene production using immutable job inputs, staged review and reusable completed stages."""
import hashlib
import html
import json
import re
import shutil
import subprocess
import uuid
from pathlib import Path

from . import llm, media, providers
from .json_utils import write_json_atomic
from .models import WORKSPACE, voice_path
from .schema import CharacterPrompt, GeneratedScene, GeneratedScript, Script, TranslatedScenePrompts
from .store import Conflict

DEFAULT_CHARACTER_NEGATIVE = 'multiple characters, cropped, cut off, text, watermark, signature, blurry'

SHOT_SIZE_PROMPTS = {
    'establishing': 'Wide establishing shot',
    'wide': 'Wide shot',
    'medium': 'Medium shot',
    'closeup': 'Close-up shot',
    'extreme_closeup': 'Extreme close-up shot',
}

CAMERA_MOVE_PROMPTS = {
    'static': 'Fixed locked-off camera, no camera movement',
    'push': 'Slow smooth camera push-in',
    'pull': 'Slow smooth camera pull-back',
    'pan_left': 'Smooth camera pan to the left',
    'pan_right': 'Smooth camera pan to the right',
    'tilt_up': 'Slow camera tilt upward',
    'tilt_down': 'Slow camera tilt downward',
    'tracking': 'Smooth tracking shot following the subject',
}

STYLES = media.STYLE_PRESETS
DEFAULT_PROMPT = '''You direct a narrated animated short.
Topic: {topic}
Style: {style}
Spoken & text language: {language_name} ({language}).
Write title, logline, continuity_note, episode_plan titles/summaries, scene title, narration, and caption in {language_name}.
Write visual_prompt, end_prompt, and motion_prompt in descriptive English (NEVER leave them empty).
Target total duration: {duration} seconds. Use about {words} spoken words total.
Series: {series}. Current episode: {episode}. Total planned episodes: {episode_count}.
Scene count instruction: {scene_count_instruction}
Available characters and their IDs: {characters}
Use only available character IDs, and only in scenes that need them.
Describe characters interacting with the actual environment in visual_prompt and end_prompt.
Each scene has 2 to 20 seconds. Scene durations must add up cleanly to the target duration.
For every scene fill ALL fields:
- title, duration, narration, caption (at most 8 words)
- shot_size (establishing, wide, medium, closeup, extreme_closeup)
- camera_move (static, push, pull, pan_left, pan_right, tilt_up, tilt_down, tracking)
- visual_prompt: vivid English description of the FIRST FRAME composition
- end_prompt: vivid English description of the LAST FRAME of the SAME shot after the action happens
- motion_prompt: vivid English camera and subject movement connecting first frame to last frame
- negative_prompt, character_ids, speaker_id
Include one simple visible action per shot, consistent anatomy and a concrete consequence.
CRITICAL: Every scene MUST have a unique title and advance the story with a NEW visual beat and setting — NEVER repeat a previous scene's title, narration, or visual idea.
For history/science avoid unsupported exact claims.
If total planned episodes > 1, include episode_plan as a list of {episode, title, duration, summary}.
Return JSON matching the schema.
'''


LANGUAGE_NAMES = {
    'tr': 'Turkish (Türkçe)',
    'en': 'English',
    'de': 'German (Deutsch)',
    'fr': 'French (Français)',
    'es': 'Spanish (Español)',
    'it': 'Italian (Italiano)',
    'ru': 'Russian (Русский)',
    'pt': 'Portuguese (Português)',
}


def resolve_prompt(project, characters):
    scene_count = int(project.get('scene_count') or 0)
    episode_count = int(project.get('episode_count') or 1)
    language = project['settings']['language']
    language_name = LANGUAGE_NAMES.get(language, 'English')
    scene_count_instruction = (
        f'Write exactly {scene_count} scenes.'
        if scene_count > 0
        else 'Choose the best number of scenes (between 2 and 8) for pacing.'
    )
    values = dict(
        topic=project['brief'],
        style=STYLES[project['style']],
        language=language,
        language_name=language_name,
        duration=str(project['duration']),
        words=str(round(project['duration'] * 1.8)),
        series=project['series'],
        episode=str(project['episode']),
        episode_count=str(episode_count),
        scene_count=str(scene_count),
        scene_count_instruction=scene_count_instruction,
        characters=json.dumps([{**row['data'], 'id': row['id']} for row in characters], ensure_ascii=False),
    )
    values.update(
        konu=values['topic'],
        stil=values['style'],
        süre=values['duration'],
        karakter=values['characters'],
        dil=values['language'],
    )
    text = project['prompt_template'] or DEFAULT_PROMPT
    return re.sub(r'\{([^{}]+)\}', lambda match: values.get(match[1], match[0]), text)


def artifact(root, asset, ext='png'):
    if ext not in ('png', 'wav', 'mp4'):
        raise ValueError('Desteklenmeyen dosya türü.')
    path = (root / 'assets' / f'{asset}.{ext}').resolve()
    if not path.is_relative_to(root / 'assets') or not path.is_file():
        raise ValueError('Referans dosyası bulunamadı.')
    return path


def resolve_asset(store, owner, asset_id):
    row = store.get(owner, asset_id)
    if not row or row['kind'] != 'asset':
        raise ValueError('Varlık kaydı bulunamadı.')
    ext = row['data'].get('ext', 'png')
    return artifact(store.root, asset_id, ext)


def save_generated_asset(store, owner, source_path, name, ext='png'):
    asset_id = str(uuid.uuid4())
    destination = store.root / 'assets' / f'{asset_id}.{ext}'
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, destination)
    store.save(
        owner,
        'asset',
        {'name': name, 'ext': ext, 'generated': True, 'sha256': digest(destination)},
        asset_id,
    )
    return asset_id


def _text_sig(value: str) -> str:
    return hashlib.sha256((value or '').strip().encode('utf-8')).hexdigest()[:12]


def patch_project_scene(store, owner, project_id, scene_id, updates):
    if not project_id or not scene_id:
        return
    for _ in range(3):
        current = store.get(owner, project_id)
        if not current or current['kind'] != 'project':
            return
        data = current['data']
        script = data.get('script')
        if not script or not script.get('scenes'):
            return
        updated_scenes = []
        matched = False
        for scene in script['scenes']:
            if scene['id'] == scene_id:
                merged = {**scene, **updates}
                takes = {k: list(v) for k, v in (scene.get('takes') or {}).items()}
                for field, take_key in (
                    ('first_asset', 'first'),
                    ('last_asset', 'last'),
                    ('clip_asset', 'clip'),
                    ('audio_asset', 'audio'),
                ):
                    new_id = updates.get(field)
                    if new_id:
                        bucket = takes.get(take_key, [])
                        prev_id = scene.get(field)
                        if prev_id and prev_id not in bucket:
                            bucket.append(prev_id)
                        if new_id not in bucket:
                            bucket.append(new_id)
                        takes[take_key] = bucket[-6:]
                merged['takes'] = takes
                if updates.get('audio_asset'):
                    merged['narration_hash'] = _text_sig(merged.get('narration', ''))
                if updates.get('first_asset') or updates.get('clip_asset'):
                    merged['visual_hash'] = _text_sig(
                        f"{merged.get('visual_prompt', '')}|{merged.get('end_prompt', '')}|{merged.get('motion_prompt', '')}"
                    )
                updated_scenes.append(merged)
                matched = True
            else:
                updated_scenes.append(scene)
        if not matched:
            return
        next_data = {**data, 'script': {**script, 'scenes': updated_scenes}}
        try:
            store.save(owner, 'project', next_data, current['id'], current['revision'])
            return
        except Conflict:
            continue


def save_project_script(store, owner, project_id, script):
    if not project_id:
        return
    for _ in range(3):
        current = store.get(owner, project_id)
        if not current or current['kind'] != 'project':
            return
        next_data = {**current['data'], 'script': script}
        try:
            store.save(owner, 'project', next_data, current['id'], current['revision'])
            return
        except Conflict:
            continue


def validate_media(path):
    try:
        return path.is_file() and path.stat().st_size > 100 and providers.movie_duration(path) > 0
    except (ValueError, OSError, subprocess.CalledProcessError):
        return False


def cached_stage(store, job, target, inputs, generate, validate=None):
    """Reuse only artifacts generated from the same complete stage inputs."""
    key = hashlib.sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    owner_key = hashlib.sha256(job['owner'].encode()).hexdigest()[:20]
    cached = store.root / 'cache' / owner_key / f'{key}{target.suffix}'
    if target.is_file() and (validate is None or validate(target)):
        return False
    if cached.is_file() and (validate is None or validate(cached)):
        shutil.copyfile(cached, target)
        store.event(job['id'], f'Korunan aşama kullanıldı · {target.name}')
        return False
    generate()
    if not target.is_file() or (validate is not None and not validate(target)):
        raise RuntimeError(f'Üretim aşaması doğrulanamadı · {target.name}')
    cached.parent.mkdir(parents=True, exist_ok=True)
    temporary = cached.with_suffix('.tmp')
    shutil.copyfile(target, temporary)
    temporary.replace(cached)
    return True


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_character_prompt(data, model_id=None, log=None):
    """Build a subject-first English ingredient prompt (character, location, or prop)."""
    ingredient_type = data.get('ingredient_type') or 'character'
    description = (data.get('description') or '').strip()
    user_negative = (data.get('negative_prompt') or '').strip()
    translated_visual = description
    translated_negative = ''
    if description and model_id:
        if log:
            log('Bileşen tarifi görsel prompta hazırlanıyor.')
        kind_hint = {
            'character': (
                'a 2D character sheet image generator. Preserve EVERY physical attribute faithfully '
                '(e.g. if bald/kel, state "completely bald man with a smooth hairless head, no hair at all"; '
                'keep hair color, beard, age, build, clothing, accessories). Do NOT invent conflicting hair or extra people.'
            ),
            'location': (
                'an environment/location concept art reference sheet. Preserve every architectural detail, '
                'lighting, colors, time of day, and atmosphere faithfully. Do NOT add random people unless requested.'
            ),
            'prop': (
                'a single hero object/prop design sheet on a clean neutral background. Preserve material, '
                'shape, color, and proportions faithfully. Do NOT add people or cluttered backgrounds.'
            ),
        }.get(ingredient_type, 'a 2D reference sheet image generator.')
        translation_prompt = (
            f'Convert this description into a concise, literal English visual prompt for {kind_hint} '
            'Also provide negative_prompt terms to prevent contradicting traits. '
            'Return JSON with visual_prompt and negative_prompt.\n'
            f'Description: {description}'
        )
        try:
            parsed, _ = llm.generate_json(translation_prompt, CharacterPrompt, model=model_id)
            translated_visual = parsed['visual_prompt'].strip() or description
            translated_negative = parsed.get('negative_prompt', '').strip()
        except Exception:
            translated_visual = description
        finally:
            providers.release_script_model(model_id)
    style_text = STYLES[data['style']]
    if ingredient_type == 'location':
        prompt = (
            f'{style_text}. Environment location reference sheet, wide establishing architectural view, '
            f'consistent lighting and spatial layout. {translated_visual}. Crisp composition, no text.'
        )
        default_neg = 'text, watermark, signature, blurry, collage, split screen'
    elif ingredient_type == 'prop':
        prompt = (
            f'{style_text}. Single hero object and prop reference sheet, centered on a plain solid white background, '
            f'clear silhouette and material details. {translated_visual}. No people, no text.'
        )
        default_neg = 'people, hands, cropped, cut off, text, watermark, signature, blurry'
    else:
        prompt = (
            f'{style_text}. Single character model sheet, full-body portrait from head to toe, '
            f'standing in a neutral pose on a plain solid white background. '
            f'{translated_visual}. Clean silhouette, consistent proportions.'
        )
        default_neg = DEFAULT_CHARACTER_NEGATIVE
    negative_parts = [part for part in (user_negative, translated_negative, default_neg) if part]
    negative = ', '.join(dict.fromkeys(p.strip() for chunk in negative_parts for p in chunk.split(',') if p.strip()))
    return prompt, negative


def _generate_script(snapshot, output, log):
    log('Senaryo ve sahne planı oluşturuluyor.')
    prompt = snapshot['resolved_prompt']
    (output / 'script.prompt.txt').write_text(prompt, encoding='utf-8')
    model_id = snapshot['project']['settings']['script']
    try:
        raw, _ = llm.generate_json(prompt, GeneratedScript, model=model_id, on_progress=log)
    finally:
        providers.release_script_model(model_id)
    generated = GeneratedScript.model_validate(raw).model_dump()
    selected = set(snapshot['project']['character_ids'])
    scenes = []
    for index, scene in enumerate(generated['scenes'], 1):
        scenes.append({
            **scene,
            'id': f'scene-{index:02d}',
            'character_ids': [value for value in scene['character_ids'] if value in selected],
            'speaker_id': scene['speaker_id'] if scene['speaker_id'] in selected else '',
            'first_asset': '',
            'last_asset': '',
            'audio_asset': '',
            'clip_asset': '',
            'spoken_duration': None,
            'approved': False,
            'seed': None,
        })
    generated['scenes'] = scenes
    return Script.model_validate(generated).model_dump()


_NON_ENGLISH_CHARS = re.compile(r'[çğıöşüÇĞİÖŞÜäöüßéèêëàâîïôùûñáíóúА-Яа-яЁё]')
_TURKISH_HINT_WORDS = {
    'bir', 've', 'ile', 'icin', 'kamera', 'yavasca', 'dogru', 'sahne', 'adam', 'kadin',
    'gunes', 'isik', 'renk', 'arka', 'plan', 'uzerinde', 'icinde', 'hareket', 'eder',
    'olur', 'gibi', 'daha', 'cok', 'kirmizi', 'mavi', 'sari', 'yesil', 'siyah', 'beyaz',
    'karanlik', 'parlak', 'kovan', 'arilar', 'tekne', 'deniz', 'fener', 'orman', 'ev',
}
_PROMPT_TRANSLATION_CACHE: dict[str, dict[str, str]] = {}


def _needs_english_translation(text: str) -> bool:
    """Return True if ``text`` appears to be Turkish or another non-English language."""
    cleaned = (text or '').strip()
    if not cleaned:
        return False
    if _NON_ENGLISH_CHARS.search(cleaned):
        return True
    tokens = {w.lower() for w in re.findall(r'[A-Za-z]+', cleaned)}
    return len(tokens & _TURKISH_HINT_WORDS) >= 2


def translate_scene_prompts(scene: dict, model_id: str | None, log=None) -> dict:
    """Translate any non-English visual/end/motion/negative fields to vivid English for image/video models."""
    fields = ('visual_prompt', 'end_prompt', 'motion_prompt', 'negative_prompt')
    to_translate = {k: (scene.get(k) or '').strip() for k in fields if _needs_english_translation(scene.get(k) or '')}
    if not to_translate or not model_id:
        return scene
    cache_key = hashlib.sha256(json.dumps([model_id, to_translate], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    cached = _PROMPT_TRANSLATION_CACHE.get(cache_key)
    if cached is not None:
        return {**scene, **{k: cached[k] for k in to_translate if cached.get(k)}}
    if log:
        log('Türkçe görsel/hareket promptları üretim için İngilizceye çevriliyor…')
    translation_prompt = (
        'Translate the following image/video generation prompts into concise, vivid, literal English '
        'optimized for diffusion image and video models (FLUX, Qwen Image, LTX-Video, FreeVideo). '
        'Preserve EVERY visual detail, subject, action, color, lighting, and camera movement faithfully. '
        'Only fill the fields provided below; leave omitted fields empty. '
        'Return JSON matching the schema.\n'
        + json.dumps(to_translate, ensure_ascii=False, indent=2)
    )
    try:
        parsed, _ = llm.generate_json(translation_prompt, TranslatedScenePrompts, model=model_id)
        translated = {k: (parsed.get(k) or '').strip() for k in to_translate}
        _PROMPT_TRANSLATION_CACHE[cache_key] = translated
        return {**scene, **{k: v for k, v in translated.items() if v}}
    except Exception:
        return scene
    finally:
        providers.release_script_model(model_id)


def _scene_prompts(store, project, scene, characters, log=None):
    settings = project.get('settings') or {}
    if settings.get('auto_translate_prompts', True):
        scene = translate_scene_prompts(scene, settings.get('script'), log=log)
    references = []
    descriptions = []
    kinds = set()
    kind_labels = {'character': 'Character', 'location': 'Location', 'prop': 'Object/Prop'}
    for identifier in scene['character_ids']:
        item = characters[identifier]['data']
        itype = item.get('ingredient_type') or 'character'
        kinds.add(itype)
        desc = item['description']
        if settings.get('auto_translate_prompts', True) and _needs_english_translation(desc):
            translated_item = translate_scene_prompts({'visual_prompt': desc}, settings.get('script'))
            desc = translated_item.get('visual_prompt') or desc
        descriptions.append(f"{kind_labels.get(itype, 'Character')} {item['name']}: {desc}")
        if item['references']:
            references.append(artifact(store.root, item['references'][0]))
    shot_prefix = SHOT_SIZE_PROMPTS.get(scene.get('shot_size', ''), '')
    camera_prefix = CAMERA_MOVE_PROMPTS.get(scene.get('camera_move', ''), '')
    prompt_parts = [STYLES[project['style']]]
    if shot_prefix:
        prompt_parts.append(shot_prefix)
    if scene['visual_prompt']:
        prompt_parts.append(scene['visual_prompt'])
    prompt = '. '.join(part.rstrip('.') for part in prompt_parts if part).strip() + '.'
    if descriptions:
        prompt += ' ' + ' '.join(descriptions)
    if references:
        if kinds == {'character'}:
            prompt += ' Preserve the identity, clothing and facial features of the supplied character references in this scene.'
        else:
            prompt += ' Preserve the exact visual design, colors and identity of all supplied character, location and object references in this scene.'
    motion_base = scene['motion_prompt'] or prompt
    motion_prompt = f'{camera_prefix}. {motion_base}' if camera_prefix else motion_base
    return prompt, motion_prompt, references, scene


def _scene_seed(settings, scene, index):
    return int(scene['seed']) if scene.get('seed') is not None else int(settings['seed']) + index


def _mux_clip_audio(raw_video, output_video, audio_path=None, log_path=None):
    """Strip model-generated audio from a scene clip and optionally mux the real Piper narration."""
    raw_video = Path(raw_video)
    output_video = Path(output_video)
    same_path = raw_video.resolve() == output_video.resolve()
    target = output_video.with_name(f'{output_video.stem}.mux{output_video.suffix}') if same_path else output_video
    if audio_path and Path(audio_path).is_file():
        cmd = [
            'ffmpeg', '-y', '-i', raw_video, '-i', audio_path,
            '-map', '0:v:0', '-map', '1:a:0',
            '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000',
            '-af', 'adelay=50,apad', '-shortest', '-movflags', '+faststart',
            target,
        ]
    else:
        cmd = [
            'ffmpeg', '-y', '-i', raw_video,
            '-map', '0:v:0', '-c:v', 'copy', '-an', '-movflags', '+faststart',
            target,
        ]
    providers.run(cmd, log_path=log_path)
    if same_path:
        target.replace(output_video)


def _produce_scene_audio(store, job, project, scene, characters, voices, stem, assets, snapshot, log, *, force=False):
    settings = project['settings']
    speaker = characters.get(scene['speaker_id'], {}).get('data', {})
    voice_id = speaker.get('voice') or settings['voice']
    audio = assets / f'{stem}.wav'
    existing_id = scene.get('audio_asset') or ''
    if existing_id and not force:
        try:
            shutil.copyfile(resolve_asset(store, job['owner'], existing_id), audio)
            spoken = providers.movie_duration(audio)
            return audio, spoken, voice_id, existing_id
        except (ValueError, OSError, subprocess.CalledProcessError):
            pass
    if voice_id not in voices:
        voices[voice_id] = media.load_voice(voice_path(voice_id))
    voice = voices[voice_id]
    if force:
        media.synthesize(voice, scene['narration'], audio)
        if not validate_media(audio):
            raise RuntimeError(f'Seslendirme doğrulanamadı · {audio.name}')
        generated = True
    else:
        generated = cached_stage(
            store,
            job,
            audio,
            [
                voice_id,
                scene['narration'],
                next((model for model in snapshot.get('models', []) if model['id'] == voice_id), None),
            ],
            lambda: media.synthesize(voice, scene['narration'], audio),
            validate_media,
        )
    spoken = providers.movie_duration(audio)
    if spoken > scene['duration'] - 0.1:
        raise ValueError(
            f"Sahne ({scene['title'] or stem}) seslendirmesi {spoken:.1f} sn, sahne {scene['duration']:.1f} sn. Metni kısaltın veya süreyi uzatın."
        )
    if generated or not existing_id:
        asset_id = save_generated_asset(
            store, job['owner'], audio, f"{scene['title'] or stem} · ses", ext='wav'
        )
        updates = {
            'audio_asset': asset_id,
            'spoken_duration': round(spoken, 2),
        }
        # If a clip already exists for this scene, re-mux it with the new narration so preview stays in sync
        clip_id = scene.get('clip_asset') or ''
        if clip_id:
            try:
                clip_src = resolve_asset(store, job['owner'], clip_id)
                remuxed = assets / f'{stem}-remux.mp4'
                _mux_clip_audio(clip_src, remuxed, audio)
                new_clip_id = save_generated_asset(
                    store, job['owner'], remuxed, f"{scene['title'] or stem} · klip", ext='mp4'
                )
                updates['clip_asset'] = new_clip_id
            except Exception:
                pass
        patch_project_scene(store, job['owner'], job.get('project_id'), scene['id'], updates)
        existing_id = asset_id
    return audio, spoken, voice_id, existing_id


def _produce_scene_first(store, job, project, scene, index, prompt, references, stem, assets, snapshot, log, *, force=False):
    settings = project['settings']
    first = assets / f'{stem}-first.png'
    existing_id = scene.get('first_asset') or ''
    if existing_id and not force:
        try:
            shutil.copyfile(artifact(store.root, existing_id), first)
            return first, existing_id
        except (ValueError, OSError):
            pass
    seed = _scene_seed(settings, scene, index)
    image_inputs = [
        prompt,
        scene['negative_prompt'],
        settings['image'],
        seed,
        settings['width'],
        settings['height'],
        [digest(path) for path in references],
        '' if force else existing_id,
        snapshot.get('models'),
    ]

    def generate_first():
        log(f'Sahne {index} · ilk kare üretiliyor')
        providers.generate_image(
            prompt,
            scene['negative_prompt'],
            first,
            {**settings, 'seed': seed},
            references,
            on_progress=lambda msg: log(f'Sahne {index} · İlk kare · {msg}'),
            cancel_check=lambda: store.is_cancelled(job['id']),
        )

    if force:
        generate_first()
        if not first.is_file():
            raise RuntimeError(f'İlk kare üretilemedi · {first.name}')
    else:
        cached_stage(store, job, first, image_inputs, generate_first)

    if force or not existing_id:
        asset_id = save_generated_asset(
            store, job['owner'], first, f"{scene['title'] or stem} · ilk kare", ext='png'
        )
        patch_project_scene(store, job['owner'], job.get('project_id'), scene['id'], {'first_asset': asset_id})
        existing_id = asset_id
    return first, existing_id


def _produce_scene_last(store, job, project, scene, index, first, stem, assets, snapshot, log, *, force=False):
    settings = project['settings']
    last = assets / f'{stem}-last.png'
    existing_id = scene.get('last_asset') or ''
    if existing_id and not force:
        try:
            shutil.copyfile(artifact(store.root, existing_id), last)
            return last, existing_id
        except (ValueError, OSError):
            pass
    if not scene.get('end_prompt', '').strip():
        return None, ''
    seed = _scene_seed(settings, scene, index)

    def generate_last():
        log(f'Sahne {index} · son kare üretiliyor')
        providers.generate_image(
            f"{STYLES[project['style']]}. Same scene, camera and characters. {scene['end_prompt']}",
            scene['negative_prompt'],
            last,
            {**settings, 'seed': seed},
            [first],
            on_progress=lambda msg: log(f'Sahne {index} · Son kare · {msg}'),
            cancel_check=lambda: store.is_cancelled(job['id']),
        )

    if force:
        generate_last()
        if not last.is_file():
            raise RuntimeError(f'Son kare üretilemedi · {last.name}')
    else:
        cached_stage(
            store,
            job,
            last,
            [
                project['style'],
                settings['image'],
                seed,
                settings['width'],
                settings['height'],
                digest(first),
                scene['end_prompt'],
                '' if force else existing_id,
                snapshot.get('models'),
            ],
            generate_last,
        )

    if force or not existing_id:
        asset_id = save_generated_asset(
            store, job['owner'], last, f"{scene['title'] or stem} · son kare", ext='png'
        )
        patch_project_scene(store, job['owner'], job.get('project_id'), scene['id'], {'last_asset': asset_id})
        existing_id = asset_id
    return last, existing_id


def _produce_scene_clip(
    store, job, project, scene, index, first, last, motion_prompt, references, stem, assets, output, snapshot, log,
    *, force=False, unload_before=True,
):
    settings = project['settings']
    duration = scene['duration']
    video = assets / f'{stem}.mp4'
    existing_id = scene.get('clip_asset') or ''
    if existing_id and not force:
        try:
            shutil.copyfile(resolve_asset(store, job['owner'], existing_id), video)
            if validate_media(video):
                return video, existing_id
        except (ValueError, OSError):
            pass
    seed = _scene_seed(settings, scene, index)

    def _attach_narration(raw_video):
        audio_src = None
        if scene.get('audio_asset'):
            try:
                audio_src = resolve_asset(store, job['owner'], scene['audio_asset'])
            except ValueError:
                audio_src = None
        _mux_clip_audio(raw_video, video, audio_src, log_path=output / 'render.log')
        raw_video.unlink(missing_ok=True)

    def generate_video():
        log(f'Sahne {index} · hareket klibi üretiliyor')
        if settings['video'] == 'ltxv-distilled':
            raw_video = assets / f'{stem}-raw.mp4'
            providers.ltxv_video(
                motion_prompt,
                first,
                last,
                duration,
                raw_video,
                {**settings, 'seed': seed},
                on_progress=lambda msg: log(f'Sahne {index} · LTX-Video · {msg}'),
                cancel_check=lambda: store.is_cancelled(job['id']),
                unload_before=unload_before,
            )
            _attach_narration(raw_video)
        elif settings['video'] == 'freevideo-h3':
            raw_video = assets / f'{stem}-raw.mp4'
            providers.freevideo(
                motion_prompt,
                first,
                last,
                references,
                duration,
                raw_video,
                {**settings, 'seed': seed},
                on_progress=lambda msg: log(f'Sahne {index} · {msg}'),
                cancel_check=lambda: store.is_cancelled(job['id']),
                unload_before=unload_before,
            )
            # Strip FreeVideo's model-generated audio track (which can speak the motion prompt)
            # and attach the scene's real Piper narration if available.
            _attach_narration(raw_video)
        else:
            frames = round(duration * 24)
            w, h = settings['width'], settings['height']
            providers.run(
                [
                    'ffmpeg', '-y', '-loop', '1', '-i', first, '-t', str(duration),
                    '-vf', f"scale={w * 2}:{h * 2},zoompan=z='1+.045*on/{frames}':d=1:s={w}x{h}:fps=24,format=yuv420p",
                    '-c:v', 'libx264', '-preset', 'fast', video,
                ],
                log_path=output / 'render.log',
                cancel_check=lambda: store.is_cancelled(job['id']),
            )
            if scene.get('audio_asset'):
                try:
                    audio_src = resolve_asset(store, job['owner'], scene['audio_asset'])
                    _mux_clip_audio(video, video, audio_src, log_path=output / 'render.log')
                except ValueError:
                    pass

    if force:
        generate_video()
        if not validate_media(video):
            raise RuntimeError(f'Sahne klibi doğrulanamadı · {video.name}')
    else:
        cached_stage(
            store,
            job,
            video,
            [
                settings['video'],
                seed,
                settings['width'],
                settings['height'],
                motion_prompt,
                duration,
                digest(first),
                digest(last) if last else None,
                snapshot.get('models'),
            ],
            generate_video,
            validate_media,
        )

    if force or not existing_id:
        asset_id = save_generated_asset(
            store, job['owner'], video, f"{scene['title'] or stem} · klip", ext='mp4'
        )
        patch_project_scene(store, job['owner'], job.get('project_id'), scene['id'], {'clip_asset': asset_id})
        existing_id = asset_id
    return video, existing_id


def execute(store, job):
    snapshot = job['snapshot']
    output = store.root / 'jobs' / job['id']
    output.mkdir(parents=True, exist_ok=True)
    log = lambda text: store.event(job['id'], text)
    write_json_atomic(str(output / 'snapshot.json'), snapshot, ensure_ascii=False, indent=2)

    if job['kind'] == 'script':
        script = _generate_script(snapshot, output, log)
        save_project_script(store, job['owner'], job.get('project_id'), script)
        return {'script': script}

    if job['kind'] == 'character':
        data = snapshot['character']['data']
        settings = snapshot['settings']
        prompt, negative = build_character_prompt(data, settings.get('script'), log)
        (output / 'character.prompt.txt').write_text(prompt, encoding='utf-8')
        write_json_atomic(
            str(output / 'character.prompts.json'),
            {'description': data['description'], 'prompt': prompt, 'negative': negative},
            ensure_ascii=False,
            indent=2,
        )
        log('Karakter referansı üretiliyor.')
        asset_id = snapshot['asset_id']
        destination = store.root / 'assets' / f'{asset_id}.png'
        destination.parent.mkdir(exist_ok=True)
        references = [artifact(store.root, key) for key in data['references'][:3]]
        providers.generate_image(
            prompt,
            negative,
            destination,
            settings,
            references,
            on_progress=lambda msg: log(f'Karakter · {msg}'),
            cancel_check=lambda: store.is_cancelled(job['id']),
        )
        current = store.get(job['owner'], snapshot['character']['id'])
        if current and current['revision'] == snapshot['character']['revision']:
            updated = {**current['data'], 'references': [asset_id, *current['data']['references']][:8]}
            store.save(job['owner'], 'character', updated, current['id'], current['revision'])
        return {'asset_id': asset_id, 'character_id': snapshot['character']['id']}

    if job['kind'] == 'style_sample':
        style_id = snapshot['style_id']
        entry = next((item for item in media.STYLE_CATALOG if item['id'] == style_id), None)
        if entry is None:
            raise ValueError('Stil bulunamadı.')
        prompt = f"{entry['prompt']}. {entry['sample_subject']}. No text, no watermark."
        (output / 'style.prompt.txt').write_text(prompt, encoding='utf-8')
        sample_dir = store.root / 'style_samples'
        sample_dir.mkdir(exist_ok=True)
        destination = sample_dir / f'{style_id}.png'
        log(f"{entry['name']} stili için canlı örnek görsel üretiliyor.")
        providers.generate_image(
            prompt,
            'text, watermark, blurry, low quality',
            destination,
            snapshot['settings'],
            on_progress=lambda msg: log(f"{entry['name']} · {msg}"),
            cancel_check=lambda: store.is_cancelled(job['id']),
        )
        try:
            from .style_examples import build_style_demo_video
            log(f"{entry['name']} · 20 sn Türkçe ve İngilizce örnek videolar güncelleniyor…")
            build_style_demo_video(store.root, style_id, 'tr', force=True)
            build_style_demo_video(store.root, style_id, 'en', force=True)
        except Exception:
            pass
        return {'style_id': style_id, 'sample_url': f'/api/studio/styles/{style_id}/sample'}

    if job['kind'] == 'style_demo':
        from .style_examples import render_style_demo_scenes
        style_id = snapshot['style_id']
        render_style_demo_scenes(
            store.root,
            style_id,
            video_mode=snapshot.get('video_mode', 'still'),
            on_progress=log,
            cancel_check=lambda: store.is_cancelled(job['id']),
        )
        return {'style_id': style_id, 'video_tr': f'/api/studio/styles/{style_id}/example-video?language=tr'}

    if job['kind'] == 'scene_rewrite':
        return _rewrite_scene(store, job, output, log)

    if job['kind'] in ('scene_audio', 'scene_first', 'scene_last', 'scene_clip', 'scene_all'):
        return execute_scene_stage(store, job, output, log)

    if job['kind'] == 'full':
        if snapshot.get('regenerate_script') or not snapshot['project'].get('script'):
            script = _generate_script(snapshot, output, log)
            snapshot['project']['script'] = script
            save_project_script(store, job['owner'], job.get('project_id'), script)
        result = render(store, job, output, log)
        result['script'] = snapshot['project']['script']
        return result

    return render(store, job, output, log)


def _rewrite_scene(store, job, output, log):
    snapshot = job['snapshot']
    project = snapshot['project']
    script = Script.model_validate(project['script']).model_dump()
    scene_id = snapshot['scene_id']
    matched = [(idx, row) for idx, row in enumerate(script['scenes'], 1) if row['id'] == scene_id]
    if not matched:
        raise ValueError('Hedef sahne bulunamadı.')
    index, target_scene = matched[0]
    language = project['settings']['language']
    language_name = LANGUAGE_NAMES.get(language, 'English')
    other_scenes = [
        f"Scene {idx}: {row['title']} — {row['narration']}"
        for idx, row in enumerate(script['scenes'], 1)
        if row['id'] != scene_id
    ]
    prompt = (
        f"Rewrite ONLY Scene {index} of a {project['duration']}s narrated short.\n"
        f"Topic: {project['brief']}\n"
        f"Style: {STYLES[project['style']]}\n"
        f"Target duration for this scene: {target_scene['duration']} seconds.\n"
        f"Write title, narration, and caption in {language_name}.\n"
        f"Write visual_prompt (FIRST FRAME), end_prompt (LAST FRAME), and motion_prompt in vivid English.\n"
        f"CRITICAL: Must be completely distinct from all other scenes (unique title, new visual event, no repetition):\n"
        + '\n'.join(other_scenes)
        + f"\nPrevious draft of Scene {index} to improve: {target_scene['title']} — {target_scene['narration']}\n"
        f"Available character IDs: {project['character_ids']}\n"
        "Return JSON matching the scene schema."
    )
    (output / f'scene-{index:02}.rewrite.prompt.txt').write_text(prompt, encoding='utf-8')
    log(f'Sahne {index} LLM ile yeniden yazılıyor…')
    model_id = project['settings']['script']
    try:
        raw, _ = llm.generate_json(prompt, GeneratedScene, model=model_id, on_progress=log)
    finally:
        providers.release_script_model(model_id)
    rewritten = GeneratedScene.model_validate(raw).model_dump()
    selected = set(project['character_ids'])
    updates = {
        **rewritten,
        'character_ids': [cid for cid in rewritten['character_ids'] if cid in selected],
        'speaker_id': rewritten['speaker_id'] if rewritten['speaker_id'] in selected else '',
        'first_asset': '',
        'last_asset': '',
        'audio_asset': '',
        'clip_asset': '',
        'spoken_duration': None,
        'approved': False,
    }
    patch_project_scene(store, job['owner'], job.get('project_id'), scene_id, updates)
    return {'scene_id': scene_id, **updates}


def execute_scene_stage(store, job, output, log):
    snapshot = job['snapshot']
    project = snapshot['project']
    script = Script.model_validate(project['script']).model_dump()
    scene_id = snapshot['scene_id']
    matched = [(idx, row) for idx, row in enumerate(script['scenes'], 1) if row['id'] == scene_id]
    if not matched:
        raise ValueError('Hedef sahne bulunamadı.')
    index, scene = matched[0]
    stem = f'scene-{index:02}'
    assets = output / 'assets'
    assets.mkdir(exist_ok=True)
    characters = {row['id']: row for row in snapshot['characters']}
    voices = {}
    prompt, motion_prompt, references, scene = _scene_prompts(store, project, scene, characters, log=log)
    write_json_atomic(
        str(output / f'{stem}.prompts.json'),
        dict(
            image=prompt,
            negative=scene['negative_prompt'],
            motion=motion_prompt,
            last=scene['end_prompt'],
            narration=scene['narration'],
        ),
        ensure_ascii=False,
        indent=2,
    )
    result = {'scene_id': scene_id}

    if job['kind'] in ('scene_audio', 'scene_all'):
        log(f"Adım 1/4 · Sahne {index} seslendirme" if job['kind'] == 'scene_all' else f"Sahne {index} · seslendirme üretiliyor")
        _, spoken, _, audio_id = _produce_scene_audio(
            store, job, project, scene, characters, voices, stem, assets, snapshot, log,
            force=(job['kind'] == 'scene_audio'),
        )
        scene['audio_asset'] = audio_id
        result['audio_asset'] = audio_id
        result['spoken_duration'] = round(spoken, 2)

    if job['kind'] in ('scene_first', 'scene_all'):
        if job['kind'] == 'scene_all':
            log(f"Adım 2/4 · Sahne {index} ilk kare")
        _, first_id = _produce_scene_first(
            store, job, project, scene, index, prompt, references, stem, assets, snapshot, log,
            force=(job['kind'] == 'scene_first'),
        )
        scene['first_asset'] = first_id
        result['first_asset'] = first_id

    if job['kind'] == 'scene_last':
        first, first_id = _produce_scene_first(
            store, job, project, scene, index, prompt, references, stem, assets, snapshot, log
        )
        result['first_asset'] = first_id
        _, last_id = _produce_scene_last(
            store, job, project, scene, index, first, stem, assets, snapshot, log, force=True
        )
        result['last_asset'] = last_id

    if job['kind'] == 'scene_all' and scene.get('end_prompt', '').strip():
        log(f"Adım 3/4 · Sahne {index} son kare")
        first = artifact(store.root, scene['first_asset'])
        _, last_id = _produce_scene_last(
            store, job, project, scene, index, first, stem, assets, snapshot, log, force=True
        )
        scene['last_asset'] = last_id
        result['last_asset'] = last_id

    if job['kind'] in ('scene_clip', 'scene_all'):
        if job['kind'] == 'scene_all':
            log(f"Adım 4/4 · Sahne {index} klip")
        first, first_id = _produce_scene_first(
            store, job, project, scene, index, prompt, references, stem, assets, snapshot, log
        )
        result['first_asset'] = first_id
        last, last_id = _produce_scene_last(
            store, job, project, scene, index, first, stem, assets, snapshot, log
        )
        if last_id:
            result['last_asset'] = last_id
        _, clip_id = _produce_scene_clip(
            store, job, project, scene, index, first, last, motion_prompt, references,
            stem, assets, output, snapshot, log, force=(job['kind'] == 'scene_clip'),
        )
        result['clip_asset'] = clip_id

    return result


def render(store, job, output, log):
    snapshot = job['snapshot']
    project = snapshot['project']
    settings = project['settings']
    script = Script.model_validate(project['script']).model_dump()
    scene_ids = [row['id'] for row in script['scenes']]
    if len(set(scene_ids)) != len(scene_ids):
        raise ValueError('Her sahnenin kimliği benzersiz olmalı.')
    assets = output / 'assets'
    assets.mkdir(exist_ok=True)
    characters = {row['id']: row for row in snapshot['characters']}
    voices = {}
    scenes = script['scenes']
    total = len(scenes)

    # Phase 1: Produce all scene audio & prepare/translate all prompts first (LLM loads/unloads once)
    prepared = []
    for index, scene in enumerate(scenes, 1):
        stem = f'scene-{index:02}'
        log(f"Faz 1/3 · Ses & prompt · Sahne {index}/{total} · {scene['title']}")
        _, spoken, voice_id, audio_id = _produce_scene_audio(
            store, job, project, scene, characters, voices, stem, assets, snapshot, log
        )
        scene['audio_asset'] = audio_id
        prompt, motion_prompt, references, scene = _scene_prompts(store, project, scene, characters, log=log)
        write_json_atomic(
            str(output / f'{stem}.prompts.json'),
            dict(
                image=prompt,
                negative=scene['negative_prompt'],
                motion=motion_prompt,
                last=scene['end_prompt'],
                voice=voice_id,
                narration=scene['narration'],
            ),
            ensure_ascii=False,
            indent=2,
        )
        prepared.append({
            'index': index,
            'stem': stem,
            'scene': scene,
            'spoken': spoken,
            'prompt': prompt,
            'motion_prompt': motion_prompt,
            'references': references,
            'first': None,
            'last': None,
        })

    # Phase 2: Generate all First & Last keyframes back-to-back while the image model stays hot in VRAM
    for item in prepared:
        index, stem, scene = item['index'], item['stem'], item['scene']
        log(f"Faz 2/3 · Kareler · Sahne {index}/{total} · {scene['title']}")
        first, _ = _produce_scene_first(
            store, job, project, scene, index, item['prompt'], item['references'], stem, assets, snapshot, log
        )
        item['first'] = first
        last, _ = _produce_scene_last(
            store, job, project, scene, index, first, stem, assets, snapshot, log
        )
        item['last'] = last

    # Phase 3: Generate all video clips back-to-back (evict image model once before first clip, then stay hot)
    timings = []
    evicted_image_model = False
    for item in prepared:
        index, stem, scene = item['index'], item['stem'], item['scene']
        log(f"Faz 3/3 · Video klip · Sahne {index}/{total} · {scene['title']}")
        should_unload = not evicted_image_model
        video, _ = _produce_scene_clip(
            store, job, project, scene, index, item['first'], item['last'], item['motion_prompt'],
            item['references'], stem, assets, output, snapshot, log, unload_before=should_unload,
        )
        if should_unload:
            evicted_image_model = True
        timings.append(
            dict(
                stem=stem,
                duration=scene['duration'],
                spoken=item['spoken'],
                narration=scene['narration'],
                caption=scene['caption'],
                source_duration=providers.movie_duration(video),
            )
        )
        write_json_atomic(str(output / 'stages.json'), timings, ensure_ascii=False, indent=2)
    log('Kurgu ve altyazı hazırlanıyor.')
    srt_path = _write_srt(output, timings, sync_captions=bool(settings.get('sync_captions', True)))
    if settings['renderer'] == 'hyperframes':
        final = hyperframes(output, timings, project['name'], settings)
    else:
        final = ffmpeg(output, timings, settings)

    bgm_path = _resolve_bgm_path(store, job['owner'], settings)
    bgm_volume = float(settings.get('bgm_volume', 0.18))
    if bgm_path and bgm_volume > 0:
        log('Arka plan müziği ve ses dengeleme (auto-ducking) uygulanıyor.')
        _mix_bgm(final, bgm_path, bgm_volume, bool(settings.get('bgm_ducking', True)), output / 'render.log')

    media.verify_narration(final)
    duration = providers.movie_duration(final)
    expected = sum(row['duration'] for row in timings)
    if settings['renderer'] == 'ffmpeg' and settings.get('transition') == 'crossfade' and len(timings) > 1:
        expected -= 0.35 * (len(timings) - 1)
    if abs(duration - expected) > .35:
        raise RuntimeError('Çıktı süresi sahne planıyla uyuşmuyor.')
    return {
        'video': f'jobs/{job["id"]}/final.mp4',
        'srt': f'jobs/{job["id"]}/{srt_path.name}' if srt_path else None,
        'duration': duration,
        'project_file': f'jobs/{job["id"]}/index.html' if settings['renderer'] == 'hyperframes' else None,
        'scenes': timings,
    }


def _write_srt(output, scenes, sync_captions=True):
    subtitles, clock, cue_idx = [], 0.0, 1
    for row in scenes:
        if sync_captions and row.get('narration'):
            spoken = float(row.get('spoken') or row['duration'])
            for c_start, c_end, text in media.timed_caption_cues(row['narration'], clock + 0.05, spoken):
                subtitles.append(f"{cue_idx}\n{media.srt_time(c_start)} --> {media.srt_time(c_end)}\n{text}")
                cue_idx += 1
        elif row.get('caption'):
            subtitles.append(
                f"{cue_idx}\n{media.srt_time(clock)} --> {media.srt_time(clock + row['duration'])}\n{row['caption']}"
            )
            cue_idx += 1
        clock += row['duration']
    srt_path = output / 'captions.srt'
    srt_path.write_text('\n\n'.join(subtitles), encoding='utf-8')
    return srt_path


def _resolve_bgm_path(store, owner, settings):
    preset = (settings.get('bgm_preset') or '').strip()
    if not preset:
        return None
    if preset == 'custom':
        asset_id = (settings.get('bgm_asset') or '').strip()
        if not asset_id:
            return None
        return resolve_asset(store, owner, asset_id)
    return media.ensure_bgm_file(preset, store.root / 'bgm')


def _mix_bgm(final_video, bgm_path, volume, ducking, log_path):
    """Overlay looped background music onto final.mp4 with optional voice auto-ducking."""
    final_video = Path(final_video)
    mixed = final_video.with_name('final.bgm.mp4')
    vol = max(0.01, min(1.0, float(volume)))
    if ducking:
        filter_complex = (
            f"[0:a]asplit=2[voice][sc];"
            f"[1:a]volume={vol:.3f}[bgm];"
            f"[bgm][sc]sidechaincompress=threshold=0.02:ratio=6:attack=40:release=350[ducked];"
            f"[voice][ducked]amix=inputs=2:duration=first:dropout_transition=2,alimiter=limit=0.95[outa]"
        )
    else:
        filter_complex = (
            f"[1:a]volume={vol:.3f}[bgm];"
            f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2,alimiter=limit=0.95[outa]"
        )
    providers.run(
        [
            'ffmpeg', '-y', '-i', final_video, '-stream_loop', '-1', '-i', bgm_path,
            '-filter_complex', filter_complex,
            '-map', '0:v:0', '-map', '[outa]',
            '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000', '-shortest', '-movflags', '+faststart',
            mixed,
        ],
        log_path=log_path,
    )
    mixed.replace(final_video)


def _delivery_size(settings):
    ratio = (settings or {}).get('aspect_ratio', '9:16')
    spec = media.ASPECT_RATIOS.get(ratio, media.ASPECT_RATIOS['9:16'])
    return spec['out_width'], spec['out_height']


def hyperframes(output, scenes, title, settings=None):
    settings = settings or {}
    language = settings.get('language', 'tr')
    caption_style = settings.get('caption_style', 'shorts')
    transition = settings.get('transition', 'cut')
    out_w, out_h = _delivery_size(settings)
    gsap = WORKSPACE / 'hyperframes-tool' / 'node_modules' / 'gsap' / 'dist' / 'gsap.min.js'
    shutil.copyfile(gsap, output / 'assets' / 'gsap.min.js')
    clips, clock = [], 0
    sync_captions = bool(settings.get('sync_captions', True))
    for index, row in enumerate(scenes):
        duration, stem = row['duration'], row['stem']
        caption_parts = []
        if caption_style != 'none':
            if sync_captions and row.get('narration'):
                spoken = float(row.get('spoken') or duration)
                for c_idx, (c_start, c_end, c_text) in enumerate(media.timed_caption_cues(row['narration'], clock + 0.05, spoken)):
                    caption_parts.append(
                        f'<p id="caption-{index}-{c_idx}" class="clip caption caption-{caption_style}" '
                        f'data-start="{c_start:.3f}" data-duration="{max(0.1, c_end - c_start):.3f}" data-track-index="2">'
                        f'{html.escape(c_text)}</p>'
                    )
            elif row.get('caption'):
                caption_parts.append(
                    f'<p id="caption-{index}" class="clip caption caption-{caption_style}" '
                    f'data-start="{clock}" data-duration="{duration}" data-track-index="2">'
                    f'{html.escape(row["caption"])}</p>'
                )
        caption_html = '\n        '.join(caption_parts)
        clips.append(
            f'''<video id="shot-{index}" class="clip picture" muted playsinline src="assets/{stem}.mp4" data-start="{clock}" data-duration="{duration}" data-track-index="0"></video>
        <audio id="voice-{index}" class="clip" src="assets/{stem}.wav" data-start="{clock + .05}" data-duration="{row['spoken']}" data-volume=".85" data-track-index="1"></audio>
        {caption_html}'''
        )
        clock += duration
    cap_width = int(out_w * 0.84)
    cap_left = int((out_w - cap_width) / 2)
    cap_bottom = int(out_h * 0.08)
    fade_script = ''
    if transition in ('fade', 'crossfade'):
        fade_script = (
            "const tl=window.__timelines.film;"
            "document.querySelectorAll('.picture').forEach(el=>{"
            "const s=Number(el.dataset.start),d=Number(el.dataset.duration);"
            "tl.fromTo(el,{opacity:0},{opacity:1,duration:0.25},s);"
            "tl.to(el,{opacity:0,duration:0.25},Math.max(s,s+d-0.25));"
            "});"
        )
    page = f'''<!doctype html><html lang="{html.escape(language)}"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
    <script src="assets/gsap.min.js"></script><style>
    html,body{{margin:0;background:#142328}} #film{{position:relative;width:{out_w}px;height:{out_h}px;overflow:hidden}}
    .picture{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
    .caption{{position:absolute;left:{cap_left}px;bottom:{cap_bottom}px;width:{cap_width}px;text-align:center;color:#fff4df;margin:0}}
    .caption-shorts{{font:800 {40 if out_w >= 1080 else 32}px/1.18 Arial,sans-serif;text-shadow:0 3px 12px #000,0 0 3px #000}}
    .caption-classic{{font:600 32px/1.22 Arial,sans-serif;background:rgba(10,12,16,.72);padding:12px 20px;border-radius:12px;box-sizing:border-box}}
    .caption-minimal{{font:500 28px/1.25 Arial,sans-serif;text-shadow:0 2px 8px rgba(0,0,0,.85)}}
    </style></head><body><main id="film" data-composition-id="film" data-start="0" data-duration="{clock}" data-width="{out_w}" data-height="{out_h}" data-fps="24">{''.join(clips)}</main>
    <script>window.__timelines={{film:gsap.timeline({{paused:true}})}};{fade_script}</script></body></html>'''
    (output / 'index.html').write_text(page, encoding='utf-8')
    final = output / 'final.mp4'
    providers.run(
        [
            'node', providers.hyperframes_cli(), 'render', '--quality', 'delivery',
            '--low-memory-mode', '--fps', '24', '-o', final,
        ],
        cwd=output,
        timeout=1800,
        log_path=output / 'render.log',
    )
    return final


def ffmpeg(output, scenes, settings=None):
    settings = settings or {}
    out_w, out_h = _delivery_size(settings)
    caption_style = settings.get('caption_style', 'shorts')
    transition = settings.get('transition', 'cut')
    parts, part_paths = [], []
    for index, row in enumerate(scenes, 1):
        stem = row['stem']
        part = output / f'part-{index:02}.mp4'
        vf = f'scale={out_w}:{out_h}:force_original_aspect_ratio=increase,crop={out_w}:{out_h},setsar=1,fps=24'
        if transition == 'fade':
            fade_out_start = max(0.0, float(row['duration']) - 0.25)
            vf += f',fade=t=in:st=0:d=0.25,fade=t=out:st={fade_out_start:.2f}:d=0.25'
        providers.run(
            [
                'ffmpeg', '-y', '-i', output / 'assets' / f'{stem}.mp4',
                '-i', output / 'assets' / f'{stem}.wav', '-t', str(row['duration']),
                '-map', '0:v', '-map', '1:a',
                '-vf', vf,
                '-af', 'adelay=50,apad', '-c:v', 'libx264', '-preset', 'fast', '-crf', '19',
                '-c:a', 'aac', '-ar', '48000', part,
            ],
            log_path=output / 'render.log',
        )
        parts.append(f"file '{part.name}'")
        part_paths.append((part, float(row['duration'])))
    (output / 'concat.txt').write_text('\n'.join(parts), encoding='utf-8')
    final = output / 'final.mp4'

    sub_styles = {
        'shorts': (
            "FontName=Segoe UI,Fontsize=12,Bold=1,Alignment=2,"
            "PrimaryColour=&H00FFFFFF,OutlineColour=&H00101216,"
            "BorderStyle=1,Outline=1.4,Shadow=0.6,MarginV=24,MarginL=22,MarginR=22"
        ),
        'classic': (
            "FontName=Segoe UI,Fontsize=11,Bold=0,Alignment=2,"
            "PrimaryColour=&H00FFFFFF,BackColour=&H99000000,"
            "BorderStyle=3,Outline=4,Shadow=0,MarginV=20,MarginL=22,MarginR=22"
        ),
        'minimal': (
            "FontName=Segoe UI,Fontsize=10,Bold=0,Alignment=2,"
            "PrimaryColour=&H00F8FAFC,OutlineColour=&H00000000,"
            "BorderStyle=1,Outline=1.0,Shadow=0.5,MarginV=18,MarginL=22,MarginR=22"
        ),
    }
    sub_filter = (
        f"subtitles=captions.srt:force_style='{sub_styles[caption_style]}'"
        if caption_style in sub_styles and (output / 'captions.srt').read_text(encoding='utf-8').strip()
        else None
    )

    if transition == 'crossfade' and len(part_paths) > 1:
        xfade_dur = 0.35
        inputs = []
        for path, _ in part_paths:
            inputs.extend(['-i', path.name])
        v_filters, a_filters = [], []
        prev_v = '[0:v]'
        prev_a = '[0:a]'
        offset = part_paths[0][1] - xfade_dur
        for idx in range(1, len(part_paths)):
            out_v = f'[v{idx}]'
            out_a = f'[a{idx}]'
            v_filters.append(f'{prev_v}[{idx}:v]xfade=transition=fade:duration={xfade_dur}:offset={max(0.0, offset):.3f}{out_v}')
            a_filters.append(f'{prev_a}[{idx}:a]acrossfade=d={xfade_dur}{out_a}')
            prev_v, prev_a = out_v, out_a
            offset += part_paths[idx][1] - xfade_dur
        if sub_filter:
            v_filters.append(f'{prev_v}{sub_filter}[vout]')
            v_map = '[vout]'
        else:
            v_map = prev_v
        a_filters.append(f'{prev_a}loudnorm=I=-16:TP=-1.5:LRA=7[aout]')
        providers.run(
            [
                'ffmpeg', '-y', *inputs,
                '-filter_complex', ';'.join(v_filters + a_filters),
                '-map', v_map, '-map', '[aout]',
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'fast', '-crf', '19',
                '-c:a', 'aac', '-movflags', '+faststart', final,
            ],
            cwd=output,
            log_path=output / 'render.log',
        )
    else:
        cmd = ['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', 'concat.txt']
        if sub_filter:
            cmd.extend(['-vf', sub_filter])
        cmd.extend([
            '-af', 'loudnorm=I=-16:TP=-1.5:LRA=7', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'fast',
            '-crf', '19', '-c:a', 'aac', '-movflags', '+faststart', final,
        ])
        providers.run(cmd, cwd=output, log_path=output / 'render.log')
    return final
