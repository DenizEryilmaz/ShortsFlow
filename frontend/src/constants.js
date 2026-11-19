import { getApiUrl } from './api';

export const API = '/api/studio';
export const mediaUrl = id => getApiUrl(`${API}/assets/${id}`);
export const jobFileUrl = (id, path) => getApiUrl(`${API}/jobs/${id}/files/${path}`);
export const requestJson = (method, body) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

export const formatDate = value => (value ? new Date(value).toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '');

export const formatEta = seconds => {
  const s = Math.max(0, Math.round(Number(seconds) || 0));
  if (s < 60) return `~${s} sn`;
  const mins = Math.round(s / 60);
  if (mins < 60) return `~${mins} dk`;
  const hrs = Math.floor(mins / 60);
  const rem = mins % 60;
  return rem ? `~${hrs} sa ${rem} dk` : `~${hrs} sa`;
};

export const formatClock = seconds => {
  const s = Math.max(0, Math.floor(seconds || 0));
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
};

export const textSig = value => {
  const str = (value || '').trim();
  let h = 2166136261;
  for (let i = 0; i < str.length; i += 1) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16);
};

export const STATUS_LABELS = {
  queued: 'Sırada',
  running: 'Üretiliyor',
  completed: 'Hazır',
  failed: 'Hata',
};

export const STATUS_TONE = {
  queued: 'warn',
  running: 'accent',
  completed: 'ok',
  failed: 'err',
};

export const JOB_LABELS = {
  script: 'Senaryo yazımı',
  character: 'Bileşen referansı',
  render: 'Bölüm kurgusu',
  full: 'Tam bölüm üretimi',
  scene_audio: 'Sahne seslendirmesi',
  scene_first: 'İlk kare',
  scene_last: 'Son kare',
  scene_clip: 'Hareket klibi',
  scene_all: 'Sahne tam üretimi',
  scene_rewrite: 'Sahne yeniden yazımı',
  style_sample: 'Stil kapağı',
  style_demo: 'Stil 20 sn demosu',
  import: 'İçe aktarılan video',
};

export const INGREDIENT_TYPES = {
  character: 'Karakter',
  location: 'Mekan',
  prop: 'Obje',
};

export const SHOT_SIZES = {
  '': 'Otomatik',
  establishing: 'Geniş kurucu plan',
  wide: 'Geniş plan',
  medium: 'Orta plan',
  closeup: 'Yakın plan',
  extreme_closeup: 'Çok yakın plan',
};

export const CAMERA_MOVES = {
  '': 'Otomatik',
  static: 'Sabit kamera',
  push: 'Yavaş yaklaşma',
  pull: 'Yavaş uzaklaşma',
  pan_left: 'Sola kaydırma',
  pan_right: 'Sağa kaydırma',
  tilt_up: 'Yukarı eğim',
  tilt_down: 'Aşağı eğim',
  tracking: 'Takip çekimi',
};

export const LANGUAGES = {
  tr: 'Türkçe',
  en: 'English (İngilizce)',
  de: 'Deutsch (Almanca)',
  fr: 'Français (Fransızca)',
  es: 'Español (İspanyolca)',
  it: 'Italiano (İtalyanca)',
  ru: 'Русский (Rusça)',
  pt: 'Português (Portekizce)',
};

export const ASPECT_RATIOS = {
  '9:16': { label: '9:16 Dikey · Shorts / Reels', width: 448, height: 768, delivery: '1080×1920' },
  '16:9': { label: '16:9 Yatay · YouTube', width: 768, height: 448, delivery: '1920×1080' },
  '1:1': { label: '1:1 Kare · Sosyal Medya', width: 576, height: 576, delivery: '1080×1080' },
};

export const QUALITY_PROFILES = [
  { id: 'fast', title: 'Hızlı (Taslak)', desc: 'FLUX.2 4B + LTX-Video · ~1,5–2 dk/sahne', image: 'flux2-klein-4b', video: 'ltxv-distilled' },
  { id: 'balanced', title: 'Orta · Dengeli', desc: 'FLUX.2 4B + FreeVideo (Step-Cache) · ~3,5 dk/sahne', image: 'flux2-klein-4b', video: 'freevideo-h3', recommended: true },
  { id: 'high', title: 'Yüksek · Sinematik', desc: 'Qwen 2.1 + FreeVideo · ~12 dk/sahne', image: 'qwen-image-21', video: 'freevideo-h3' },
];

export const TRANSITIONS = {
  cut: 'Kesme',
  crossfade: 'Yumuşak geçiş',
  fade: 'Siyaha kararma',
};

export const CAPTION_STYLES = {
  shorts: 'Shorts (Büyük kalın)',
  classic: 'Klasik alt bant',
  minimal: 'Minimal sade',
  none: 'Altyazısız',
};

export const BGM_PRESETS = [
  { id: '', name: 'Müzik yok' },
  { id: 'calm_ambient', name: 'Sakin Ambiyans (Ücretsiz)' },
  { id: 'science_pulse', name: 'Bilim & Belgesel (Ücretsiz)' },
  { id: 'warm_story', name: 'Masal & Hikâye (Ücretsiz)' },
  { id: 'custom', name: 'Özel müzik yükle…' },
];

export const KIND_LABELS = {
  script: 'Senaryo (LLM)',
  image: 'Görsel',
  video: 'Video',
  voice: 'Seslendirme',
  renderer: 'Kurgu',
};

export const emptyScene = (duration = 5) => ({
  id: crypto.randomUUID(),
  title: '',
  duration,
  narration: '',
  caption: '',
  shot_size: '',
  camera_move: '',
  visual_prompt: '',
  motion_prompt: '',
  end_prompt: '',
  negative_prompt: '',
  character_ids: [],
  speaker_id: '',
  first_asset: '',
  last_asset: '',
  audio_asset: '',
  clip_asset: '',
  spoken_duration: null,
  approved: false,
  seed: null,
  takes: {},
  narration_hash: '',
  visual_hash: '',
});

export function defaultSettings(models = [], lang = 'tr') {
  const first = kind => models.find(m => m.kind === kind && m.ready)?.id;
  const langVoice = models.find(m => m.kind === 'voice' && m.ready && m.language === lang)?.id;
  return {
    script: first('script') || 'qwen3-vl:8b-instruct',
    image: models.find(m => m.id === 'flux2-klein-4b' && m.ready)?.id || first('image') || 'qwen-image-21',
    video: models.find(m => m.id === 'freevideo-h3' && m.ready)?.id
      || first('video')
      || 'ltxv-distilled',
    voice: langVoice || first('voice') || 'tr_TR-dfki-medium',
    renderer: 'ffmpeg',
    language: lang,
    aspect_ratio: '9:16',
    transition: 'crossfade',
    caption_style: 'shorts',
    sync_captions: true,
    auto_translate_prompts: true,
    bgm_preset: 'warm_story',
    bgm_asset: '',
    bgm_volume: 0.16,
    bgm_ducking: true,
    seed: 743,
    width: 448,
    height: 768,
    ram_reserve_gib: 1,
  };
}

export function humanizeError(raw) {
  if (!raw || raw === '__CANCEL_REQUESTED__') return null;
  const text = String(raw);
  const low = text.toLowerCase();
  if (low.includes('comfyui') && (low.includes('bağlanılamadı') || low.includes('connect'))) {
    return {
      title: 'Görsel motoru (ComfyUI) kapalı',
      hint: 'Sistem sayfasından ComfyUI servisini tek tıkla başlatıp işi yeniden deneyebilirsiniz.',
      action: 'start_comfyui',
    };
  }
  if (low.includes('ollama') || low.includes('11434')) {
    return {
      title: 'Dil modeli (Ollama) yanıt vermiyor',
      hint: 'Sistem sayfasından Ollama servisini başlatıp tekrar deneyin.',
      action: 'start_ollama',
    };
  }
  if (low.includes('out of memory') || low.includes('oom') || low.includes('vram')) {
    return {
      title: 'Ekran kartı belleği (VRAM) doldu',
      hint: 'Hızlı kalite profiline geçerek veya açık diğer GPU uygulamalarını kapatarak yeniden deneyin.',
      action: 'retry',
    };
  }
  if (low.includes('iptal edildi')) {
    return { title: 'Üretim kullanıcı tarafından durduruldu', hint: 'İstediğiniz zaman kaldığı yerden devam ettirebilirsiniz.', action: 'retry' };
  }
  if (low.includes('seslendirmesi') && low.includes('süreyi uzatın')) {
    return { title: 'Seslendirme sahne süresinden uzun', hint: text, action: null };
  }
  return {
    title: 'Üretim sırasında beklenmeyen bir hata oluştu',
    hint: text.length > 260 ? `${text.slice(0, 260)}…` : text,
    action: 'retry',
  };
}
