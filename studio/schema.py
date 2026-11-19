"""Pydantic validation schemas for studio projects, scripts, characters and templates."""
from typing import Literal

from pydantic import BaseModel, Field

STYLE_IDS = Literal[
    'animation_2d',
    'paint_storybook',
    'science_2d',
    'paper_cut',
    'anime_cel',
    'clay_stopmotion',
    'noir_comic',
    'pixel_retro',
]


LANGUAGE_IDS = Literal['tr', 'en', 'de', 'fr', 'es', 'it', 'ru', 'pt']
ASPECT_RATIOS = Literal['9:16', '16:9', '1:1']
TRANSITIONS = Literal['cut', 'crossfade', 'fade']
CAPTION_STYLES = Literal['shorts', 'classic', 'minimal', 'none']
INGREDIENT_TYPES = Literal['character', 'location', 'prop']


class Settings(BaseModel):
    script: str = 'qwen3-vl:8b-instruct'
    image: Literal['flux2-klein-4b', 'qwen-image-21'] = 'flux2-klein-4b'
    video: Literal['wan22-ti2v-5b', 'ltxv-distilled', 'freevideo-h3', 'still-motion'] = 'wan22-ti2v-5b'
    voice: str = 'tr_TR-dfki-medium'
    renderer: Literal['hyperframes', 'ffmpeg'] = 'hyperframes'
    language: LANGUAGE_IDS = 'tr'
    aspect_ratio: ASPECT_RATIOS = '9:16'
    transition: TRANSITIONS = 'cut'
    caption_style: CAPTION_STYLES = 'shorts'
    sync_captions: bool = True
    auto_translate_prompts: bool = True
    bgm_preset: str = ''
    bgm_asset: str = ''
    bgm_volume: float = Field(default=0.18, ge=0.0, le=1.0)
    bgm_ducking: bool = True
    seed: int = Field(default=743, ge=0, le=2**32 - 1)
    width: int = Field(default=448, ge=256, le=768, multiple_of=32)
    height: int = Field(default=768, ge=256, le=1024, multiple_of=32)
    ram_reserve_gib: float = Field(default=1, ge=.25, le=4)


class Scene(BaseModel):
    id: str
    title: str = ''
    duration: float = Field(default=5, ge=2, le=20)
    narration: str = Field(default='', max_length=2500)
    caption: str = Field(default='', max_length=160)
    visual_prompt: str = Field(default='', max_length=12000)
    motion_prompt: str = Field(default='', max_length=12000)
    end_prompt: str = Field(default='', max_length=12000)
    negative_prompt: str = Field(default='', max_length=4000)
    shot_size: str = ''
    camera_move: str = ''
    character_ids: list[str] = Field(default_factory=list, max_length=3)
    speaker_id: str = ''
    first_asset: str = ''
    last_asset: str = ''
    audio_asset: str = ''
    clip_asset: str = ''
    spoken_duration: float | None = None
    approved: bool = False
    seed: int | None = Field(default=None, ge=0, le=2**32 - 1)
    takes: dict[str, list[str]] = Field(default_factory=dict)
    narration_hash: str = ''
    visual_hash: str = ''


class EpisodeSummary(BaseModel):
    episode: int = Field(default=1, ge=1)
    title: str = ''
    duration: float = Field(default=15, ge=4, le=180)
    summary: str = ''


class Script(BaseModel):
    title: str
    logline: str = ''
    continuity_note: str = ''
    recommended_duration: float | None = None
    episode_plan: list[EpisodeSummary] = Field(default_factory=list, max_length=12)
    scenes: list[Scene] = Field(min_length=1, max_length=20)


class GeneratedScene(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    duration: float = Field(ge=2, le=20)
    narration: str = Field(min_length=1, max_length=2500)
    caption: str = Field(min_length=1, max_length=160)
    shot_size: Literal['establishing', 'wide', 'medium', 'closeup', 'extreme_closeup'] = 'medium'
    camera_move: Literal['static', 'push', 'pull', 'pan_left', 'pan_right', 'tilt_up', 'tilt_down', 'tracking'] = 'static'
    visual_prompt: str = Field(min_length=10, max_length=4000, description='Required English description of the FIRST FRAME.')
    end_prompt: str = Field(min_length=10, max_length=4000, description='Required English description of the LAST FRAME of the same shot.')
    motion_prompt: str = Field(min_length=10, max_length=4000, description='Required English camera and subject motion prompt.')
    negative_prompt: str = ''
    character_ids: list[str] = Field(default_factory=list, max_length=3)
    speaker_id: str = ''


class GeneratedScript(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    logline: str = Field(min_length=1, max_length=1000)
    continuity_note: str = ''
    recommended_duration: float = Field(ge=4, le=180)
    episode_plan: list[EpisodeSummary] = Field(default_factory=list, max_length=12)
    scenes: list[GeneratedScene] = Field(min_length=1, max_length=20)


class Project(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    brief: str = Field(default='', max_length=16000)
    style: STYLE_IDS = 'animation_2d'
    duration: int = Field(default=10, ge=4, le=180)
    series: str = ''
    series_id: str = ''
    episode: int = Field(default=1, ge=1)
    episode_count: int = Field(default=1, ge=1, le=24)
    scene_count: int = Field(default=0, ge=0, le=20)
    production_mode: Literal['staged', 'full'] = 'staged'
    character_ids: list[str] = Field(default_factory=list, max_length=12)
    settings: Settings = Field(default_factory=Settings)
    script: Script | None = None
    prompt_template: str = Field(default='', max_length=24000)


class Series(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    logline: str = Field(default='', max_length=2000)
    tone: str = Field(default='', max_length=300)
    audience: str = Field(default='', max_length=300)
    style: STYLE_IDS = 'animation_2d'
    continuity_note: str = Field(default='', max_length=4000)
    cover_asset: str = ''
    character_ids: list[str] = Field(default_factory=list, max_length=20)
    episode_duration: int = Field(default=30, ge=4, le=180)
    episode_count: int = Field(default=1, ge=1, le=24)
    defaults: Settings = Field(default_factory=Settings)


class Character(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    ingredient_type: INGREDIENT_TYPES = 'character'
    description: str = Field(default='', max_length=12000)
    negative_prompt: str = Field(default='', max_length=4000)
    style: STYLE_IDS = 'animation_2d'
    voice: str = ''
    series_ids: list[str] = Field(default_factory=list, max_length=20)
    references: list[str] = Field(default_factory=list, max_length=8)
    seed: int = Field(default=743, ge=0, le=2**32 - 1)


class CharacterPrompt(BaseModel):
    visual_prompt: str = Field(min_length=1, max_length=2000)
    negative_prompt: str = Field(default='', max_length=1000)


class TranslatedScenePrompts(BaseModel):
    visual_prompt: str = Field(default='', max_length=6000)
    end_prompt: str = Field(default='', max_length=6000)
    motion_prompt: str = Field(default='', max_length=6000)
    negative_prompt: str = Field(default='', max_length=3000)


class ProposedIngredient(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    ingredient_type: INGREDIENT_TYPES = 'character'
    description: str = Field(min_length=10, max_length=2000)
    voice_hint: str = Field(default='', max_length=120)


class WizardCastProposal(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    logline: str = Field(min_length=10, max_length=1000)
    continuity_note: str = Field(default='', max_length=2000)
    ingredients: list[ProposedIngredient] = Field(default_factory=list, max_length=6)


class PublishMetadata(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    hook: str = Field(default='', max_length=300)
    description: str = Field(min_length=10, max_length=3000)
    hashtags: list[str] = Field(default_factory=list, max_length=15)


class Template(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    prompt: str = Field(min_length=1, max_length=24000)
    category: Literal['script', 'image', 'motion', 'character'] = 'script'


SCHEMAS = {'series': Series, 'project': Project, 'character': Character, 'template': Template}
