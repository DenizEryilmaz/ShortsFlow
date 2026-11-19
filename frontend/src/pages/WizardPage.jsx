import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft, ArrowRight, Check, Clapperboard, Film, Loader2, Play, Plus,
  Sparkles, Trash2, Users, Volume2,
} from 'lucide-react';
import { apiJson, getApiUrl } from '../api';
import {
  API, ASPECT_RATIOS, BGM_PRESETS, CAPTION_STYLES, defaultSettings, formatEta,
  INGREDIENT_TYPES, LANGUAGES, requestJson,
} from '../constants';
import { useStudio } from '../context/StudioContext';
import { QualityPicker } from '../components/ui/Primitives';

const WIZARD_STEPS = [
  { num: 1, label: 'Fikir' },
  { num: 2, label: 'Stil' },
  { num: 3, label: 'Kadro' },
  { num: 4, label: 'Format & Kalite' },
  { num: 5, label: 'Özet' },
];

const TONES = ['Sıcak & Masalsı', 'Eğitici & Merak Uyandıran', 'Komik & Dinamik', 'Gizemli & Gerilimli', 'Sinematik & Epik'];

export default function WizardPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { styles, models, saveDoc, refreshLibrary, addToast } = useStudio();

  const [step, setStep] = useState(1);
  const [mode, setMode] = useState(() => (searchParams.get('type') === 'single' ? 'single' : 'series')); // 'series' | 'single'
  const [title, setTitle] = useState('');
  const [idea, setIdea] = useState('');
  const [tone, setTone] = useState(TONES[0]);
  const [episodeCount, setEpisodeCount] = useState(5);
  const [duration, setDuration] = useState(35);
  const [styleId, setStyleId] = useState('clay_stopmotion');
  const [previewLang, setPreviewLang] = useState('tr');
  const [language, setLanguage] = useState('tr');
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [imageModel, setImageModel] = useState('flux2-klein-4b');
  const [videoModel, setVideoModel] = useState('freevideo-h3');
  const [voiceId, setVoiceId] = useState('');
  const [bgmPreset, setBgmPreset] = useState('warm_story');
  const [captionStyle, setCaptionStyle] = useState('shorts');

  const [logline, setLogline] = useState('');
  const [continuityNote, setContinuityNote] = useState('');
  const [cast, setCast] = useState([]);
  const [generateRefs, setGenerateRefs] = useState(true);
  const [proposing, setProposing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [estimate, setEstimate] = useState(null);
  const [previewVoice, setPreviewVoice] = useState('');

  const readyVoices = useMemo(() => models.filter(m => m.kind === 'voice' && m.ready), [models]);

  useEffect(() => {
    const match = readyVoices.find(v => v.language === language) || readyVoices[0];
    if (match && !voiceId) setVoiceId(match.id);
  }, [readyVoices, language, voiceId]);

  useEffect(() => {
    const eps = mode === 'series' ? episodeCount : 1;
    const scenesPerEp = Math.max(4, Math.round(duration / 6));
    apiJson(`${API}/estimate?episodes=${eps}&scenes=${scenesPerEp}&image=${encodeURIComponent(imageModel)}&video=${encodeURIComponent(videoModel)}`)
      .then(setEstimate)
      .catch(() => {});
  }, [mode, episodeCount, duration, imageModel, videoModel]);

  const selectedStyle = styles.find(s => s.id === styleId) || styles[0];

  const handleProposeCast = async () => {
    if (idea.trim().length < 5) {
      addToast('Önce en az bir cümlelik hikâye fikri yazın.', 'err');
      return;
    }
    setProposing(true);
    try {
      const res = await apiJson(`${API}/wizard/propose-cast`, requestJson('POST', {
        idea,
        style: styleId,
        language,
        tone,
      }));
      if (!title.trim() && res.title) setTitle(res.title);
      if (res.logline) setLogline(res.logline);
      if (res.continuity_note) setContinuityNote(res.continuity_note);
      const langVoicePool = readyVoices.filter(v => v.language === language);
      const pool = langVoicePool.length ? langVoicePool : readyVoices;
      const mapped = (res.ingredients || []).map((item, i) => ({
        id: crypto.randomUUID(),
        name: item.name,
        ingredient_type: item.ingredient_type || 'character',
        description: item.description,
        voice: item.ingredient_type === 'character' && pool.length ? pool[i % pool.length].id : '',
      }));
      setCast(mapped);
      addToast(`${mapped.length} bileşen önerildi. İstediğiniz gibi düzenleyebilirsiniz.`, 'ok');
    } catch (err) {
      addToast(err.detail || err.message || 'Kadro önerisi alınamadı.', 'err');
    } finally {
      setProposing(false);
    }
  };

  const addManualCast = () => {
    setCast(prev => [
      ...prev,
      { id: crypto.randomUUID(), name: '', ingredient_type: 'character', description: '', voice: voiceId },
    ]);
  };

  const updateCastItem = (id, patch) => {
    setCast(prev => prev.map(item => (item.id === id ? { ...item, ...patch } : item)));
  };

  const removeCastItem = id => {
    setCast(prev => prev.filter(item => item.id !== id));
  };

  const handleFinish = async () => {
    const cleanTitle = title.trim() || idea.trim().slice(0, 48) || 'Yeni Proje';
    setCreating(true);
    try {
      const spec = ASPECT_RATIOS[aspectRatio] || ASPECT_RATIOS['9:16'];
      const baseSettings = {
        ...defaultSettings(models, language),
        image: imageModel,
        video: videoModel,
        voice: voiceId || defaultSettings(models, language).voice,
        language,
        aspect_ratio: aspectRatio,
        width: spec.width,
        height: spec.height,
        bgm_preset: bgmPreset,
        caption_style: captionStyle,
      };

      let seriesId = '';
      if (mode === 'series') {
        const seriesDoc = await saveDoc('series', {
          name: cleanTitle,
          logline: logline.trim() || idea.trim(),
          continuity_note: continuityNote.trim(),
          style: styleId,
          episode_count: episodeCount,
          episode_duration: duration,
          character_ids: [],
          defaults: baseSettings,
        });
        seriesId = seriesDoc.id;
      }

      // Create characters / locations / props
      const createdCharIds = [];
      for (const item of cast.filter(c => c.name.trim())) {
        const savedChar = await saveDoc('character', {
          name: item.name.trim(),
          ingredient_type: item.ingredient_type || 'character',
          description: item.description.trim() || item.name.trim(),
          voice: item.voice || '',
          style: styleId,
          series_ids: seriesId ? [seriesId] : [],
          references: [],
        });
        createdCharIds.push(savedChar.id);
        if (generateRefs && item.description.trim()) {
          apiJson(`${API}/characters/${savedChar.id}/generate`, requestJson('POST', { settings: baseSettings })).catch(() => {});
        }
      }

      if (seriesId && createdCharIds.length) {
        const refreshed = await refreshLibrary();
        const sRow = refreshed.series.find(s => s.id === seriesId);
        if (sRow) {
          await saveDoc('series', { ...sRow.data, character_ids: createdCharIds }, sRow);
        }
      }

      if (mode === 'series') {
        const ep1 = await apiJson(`${API}/series/${seriesId}/episodes`, requestJson('POST', {
          name: `${cleanTitle} · Bölüm 01`,
          brief: idea.trim(),
          duration,
        }));
        await refreshLibrary();
        addToast(`"${cleanTitle}" dizisi ve 1. bölüm oluşturuldu!`, 'ok');
        navigate(`/series/${seriesId}/episodes/${ep1.id}`);
      } else {
        const proj = await saveDoc('project', {
          name: cleanTitle,
          brief: idea.trim(),
          style: styleId,
          duration,
          production_mode: 'staged',
          character_ids: createdCharIds,
          settings: baseSettings,
        });
        await refreshLibrary();
        addToast(`"${cleanTitle}" projesi hazır!`, 'ok');
        navigate(`/episodes/${proj.id}`);
      }
    } catch (err) {
      addToast(err.detail || err.message || 'Oluşturma başarısız oldu.', 'err');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="st-page">
      <div className="st-page-head">
        <div>
          <h1>Yeni Yapım Oluştur</h1>
          <p className="st-muted">5 adımda fikrinizi stile, kadroya ve hazır bir dizi/bölüme dönüştürün.</p>
        </div>
        <button type="button" className="st-btn" onClick={() => navigate(-1)}>
          <ArrowLeft size={15} />Geri
        </button>
      </div>

      <div className="st-stepper">
        {WIZARD_STEPS.map(s => (
          <button
            key={s.num}
            type="button"
            className={step === s.num ? 'st-step active' : step > s.num ? 'st-step done' : 'st-step'}
            onClick={() => setStep(s.num)}
          >
            <span className="st-step-num">{step > s.num ? <Check size={13} /> : s.num}</span>
            <span>{s.label}</span>
          </button>
        ))}
      </div>

      <div className="st-card">
        {/* STEP 1: FİKİR */}
        {step === 1 && (
          <div className="st-stack">
            <h2 style={{ margin: 0 }}>1. Nasıl bir yapım oluşturmak istersiniz?</h2>
            <div className="st-mode-grid">
              <button
                type="button"
                className={mode === 'series' ? 'st-mode-card active' : 'st-mode-card'}
                onClick={() => setMode('series')}
              >
                <Clapperboard size={22} />
                <strong>Mini Dizi (Çok Bölümlü)</strong>
                <small>Ortak kadro, ortak görsel stil ve Dizi Kitabı ile birden fazla bölüm üretin.</small>
              </button>
              <button
                type="button"
                className={mode === 'single' ? 'st-mode-card active' : 'st-mode-card'}
                onClick={() => setMode('single')}
              >
                <Film size={22} />
                <strong>Tek Bağımsız Video</strong>
                <small>Tek seferlik Shorts, Reels veya YouTube kısa filmi oluşturun.</small>
              </button>
            </div>

            <div className="st-form-grid two">
              <label className="st-field">
                <span>Yapım başlığı (opsiyonel — AI da önerebilir)</span>
                <input
                  placeholder="Örn: Saatli Fırın / Gece Yarısı Bilim"
                  value={title}
                  onChange={e => setTitle(e.target.value)}
                />
              </label>
              <label className="st-field">
                <span>Anlatım dili</span>
                <select
                  value={language}
                  onChange={e => {
                    const lang = e.target.value;
                    setLanguage(lang);
                    const match = readyVoices.find(v => v.language === lang);
                    if (match) setVoiceId(match.id);
                  }}
                >
                  {Object.entries(LANGUAGES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                </select>
              </label>
            </div>

            <label className="st-field">
              <span>Hikâye fikriniz nedir?</span>
              <textarea
                rows={4}
                placeholder="Örn: Gece yarısı canlanan kil hamuru karakterlerinin gizli bir fırında yaşadıkları sıcak ve komik maceralar…"
                value={idea}
                onChange={e => setIdea(e.target.value)}
              />
            </label>

            <div className="st-field">
              <span>Ton / Atmosfer</span>
              <div className="st-chips">
                {TONES.map(t => (
                  <button
                    key={t}
                    type="button"
                    className={tone === t ? 'st-btn st-btn-sm st-btn-primary' : 'st-btn st-btn-sm'}
                    onClick={() => setTone(t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            <div className="st-form-grid two">
              {mode === 'series' && (
                <label className="st-field">
                  <span>Hedef bölüm sayısı</span>
                  <input
                    type="number"
                    min={2}
                    max={24}
                    value={episodeCount}
                    onChange={e => setEpisodeCount(Math.max(2, Number(e.target.value) || 5))}
                  />
                </label>
              )}
              <label className="st-field">
                <span>Bölüm süresi (sn)</span>
                <input
                  type="number"
                  min={10}
                  max={120}
                  value={duration}
                  onChange={e => setDuration(Math.max(10, Number(e.target.value) || 35))}
                />
              </label>
            </div>
          </div>
        )}

        {/* STEP 2: STİL */}
        {step === 2 && (
          <div className="st-stack">
            <div className="st-row-between">
              <div>
                <h2 style={{ margin: 0 }}>2. Görsel Stilinizi Seçin</h2>
                <p className="st-muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
                  Her stilin gerçek 20 saniyelik yerel model demosunu anında izleyebilirsiniz.
                </p>
              </div>
              <div className="st-segmented">
                <button type="button" className={previewLang === 'tr' ? 'active' : ''} onClick={() => setPreviewLang('tr')}>TR</button>
                <button type="button" className={previewLang === 'en' ? 'active' : ''} onClick={() => setPreviewLang('en')}>EN</button>
              </div>
            </div>

            <div className="st-wizard-style-layout">
              <div className="st-style-picker-grid">
                {styles.map(st => (
                  <button
                    key={st.id}
                    type="button"
                    className={styleId === st.id ? 'st-style-mini active' : 'st-style-mini'}
                    onClick={() => setStyleId(st.id)}
                  >
                    <img src={getApiUrl(st.sample_url)} alt={st.name} />
                    <div>
                      <strong>{st.name}</strong>
                      <small>{st.subtitle}</small>
                    </div>
                  </button>
                ))}
              </div>

              {selectedStyle && (
                <div className="st-style-preview-box">
                  <div className="st-row-between" style={{ marginBottom: 8 }}>
                    <strong>{selectedStyle.name}</strong>
                    <span className="st-badge st-badge-accent">20 sn canlı önizleme</span>
                  </div>
                  <video
                    key={`${selectedStyle.id}-${previewLang}`}
                    controls
                    playsInline
                    preload="metadata"
                    src={getApiUrl(`${API}/styles/${selectedStyle.id}/example-video?language=${previewLang}`)}
                  />
                  <p className="st-muted" style={{ fontSize: 12, margin: '8px 0 0' }}>
                    {selectedStyle.summary}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* STEP 3: KADRO */}
        {step === 3 && (
          <div className="st-stack">
            <div className="st-row-between">
              <div>
                <h2 style={{ margin: 0 }}>3. Karakterler &amp; Ana Mekanlar</h2>
                <p className="st-muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
                  Tutarlı yüzler ve mekanlar için AI’dan kadro önerisi isteyebilir veya elle ekleyebilirsiniz.
                </p>
              </div>
              <div className="st-actions" style={{ margin: 0 }}>
                <button type="button" className="st-btn st-btn-primary" disabled={proposing} onClick={handleProposeCast}>
                  {proposing ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                  {cast.length ? 'Yeniden Öner' : 'AI ile Kadro Öner'}
                </button>
                <button type="button" className="st-btn" onClick={addManualCast}>
                  <Plus size={14} />Elle Ekle
                </button>
              </div>
            </div>

            {cast.length === 0 ? (
              <div className="st-empty-inline">
                <Users size={24} />
                <p>Henüz kadro eklenmedi. &ldquo;AI ile Kadro Öner&rdquo; ile fikrinizden otomatik karakter ve mekan tasarımı çıkarabilir veya doğrudan sonraki adıma geçebilirsiniz.</p>
              </div>
            ) : (
              <div className="st-stack">
                {cast.map(item => (
                  <div key={item.id} className="st-cast-editor-row">
                    <div className="st-form-grid three">
                      <label className="st-field">
                        <span>Ad</span>
                        <input value={item.name} onChange={e => updateCastItem(item.id, { name: e.target.value })} placeholder="Örn: Barnaby" />
                      </label>
                      <label className="st-field">
                        <span>Tür</span>
                        <select value={item.ingredient_type} onChange={e => updateCastItem(item.id, { ingredient_type: e.target.value })}>
                          {Object.entries(INGREDIENT_TYPES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                        </select>
                      </label>
                      <label className="st-field">
                        <span>Karakter sesi</span>
                        <div className="st-row-gap">
                          <select value={item.voice || ''} onChange={e => updateCastItem(item.id, { voice: e.target.value })}>
                            <option value="">Varsayılan ses</option>
                            {readyVoices.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                          </select>
                          {item.voice && (
                            <button
                              type="button"
                              className="st-icon-btn"
                              onClick={() => setPreviewVoice(previewVoice === item.voice ? '' : item.voice)}
                              title="Sesi dinle"
                            >
                              <Volume2 size={14} />
                            </button>
                          )}
                          <button type="button" className="st-icon-btn" onClick={() => removeCastItem(item.id)} title="Kaldır">
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </label>
                    </div>
                    <label className="st-field">
                      <span>Görsel görünüm tarifi (Referans görsel üretimi için)</span>
                      <textarea rows={2} value={item.description} onChange={e => updateCastItem(item.id, { description: e.target.value })} />
                    </label>
                    {previewVoice && previewVoice === item.voice && (
                      <audio controls autoPlay src={getApiUrl(`${API}/voices/${item.voice}/preview`)} style={{ width: '100%', height: 32 }} />
                    )}
                  </div>
                ))}
                <label className="st-checkbox">
                  <input type="checkbox" checked={generateRefs} onChange={e => setGenerateRefs(e.target.checked)} />
                  <span>Yapım oluşturulduğunda bu bileşenlerin referans görsellerini arka planda otomatik üret</span>
                </label>
              </div>
            )}
          </div>
        )}

        {/* STEP 4: FORMAT & KALİTE */}
        {step === 4 && (
          <div className="st-stack">
            <h2 style={{ margin: 0 }}>4. Format, Kalite &amp; Ses Ayarları</h2>
            <div>
              <span className="st-field-label">Üretim kalite profili</span>
              <QualityPicker
                image={imageModel}
                video={videoModel}
                onChange={(img, vid) => { setImageModel(img); setVideoModel(vid); }}
              />
            </div>

            <div className="st-form-grid three">
              <label className="st-field">
                <span>Ekran oranı</span>
                <select value={aspectRatio} onChange={e => setAspectRatio(e.target.value)}>
                  {Object.entries(ASPECT_RATIOS).map(([id, spec]) => <option key={id} value={id}>{spec.label}</option>)}
                </select>
              </label>
              <label className="st-field">
                <span>Varsayılan anlatıcı sesi</span>
                <select value={voiceId} onChange={e => setVoiceId(e.target.value)}>
                  {readyVoices.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                </select>
              </label>
              <label className="st-field">
                <span>Arka plan müziği</span>
                <select value={bgmPreset} onChange={e => setBgmPreset(e.target.value)}>
                  {BGM_PRESETS.filter(b => b.id !== 'custom').map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              </label>
            </div>

            <label className="st-field" style={{ maxWidth: 320 }}>
              <span>Altyazı stili</span>
              <select value={captionStyle} onChange={e => setCaptionStyle(e.target.value)}>
                {Object.entries(CAPTION_STYLES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </label>
          </div>
        )}

        {/* STEP 5: ÖZET & TAHMİN */}
        {step === 5 && (
          <div className="st-stack">
            <h2 style={{ margin: 0 }}>5. Yapım Özeti &amp; Süre Tahmini</h2>
            <div className="st-summary-grid">
              <div className="st-summary-card">
                <span>Başlık &amp; Tür</span>
                <strong>{title.trim() || idea.trim().slice(0, 40) || 'Yeni Yapım'}</strong>
                <small>{mode === 'series' ? `${episodeCount} bölümlük dizi · ${duration} sn/bölüm` : `Tek video · ${duration} sn`}</small>
              </div>
              <div className="st-summary-card">
                <span>Görsel Stil &amp; Format</span>
                <strong>{selectedStyle?.name || styleId}</strong>
                <small>{ASPECT_RATIOS[aspectRatio]?.label} · {LANGUAGES[language]}</small>
              </div>
              <div className="st-summary-card">
                <span>Kadro</span>
                <strong>{cast.filter(c => c.name.trim()).length} bileşen</strong>
                <small>{cast.filter(c => c.name.trim()).map(c => c.name).join(', ') || 'Kadrosuz'}</small>
              </div>
              <div className="st-summary-card">
                <span>Tahmini Üretim Süresi</span>
                <strong>{estimate ? formatEta(estimate.per_episode_seconds) : 'Hesaplanıyor…'} / bölüm</strong>
                <small>
                  {estimate ? `Toplam ~${formatEta(estimate.total_seconds)} · ~${estimate.estimated_mb} MB disk` : ''}
                </small>
              </div>
            </div>
            <p className="st-muted" style={{ fontSize: 13 }}>
              Oluştur butonuna bastığınızda {mode === 'series' ? 'Dizi Kitabı, kadro bileşenleri ve 1. bölüm' : 'proje ve kadro'} kaydedilip çalışma alanına yönlendirileceksiniz.
            </p>
          </div>
        )}

        {/* Wizard Footer */}
        <div className="st-wizard-footer">
          <button type="button" className="st-btn" disabled={step === 1} onClick={() => setStep(s => Math.max(1, s - 1))}>
            <ArrowLeft size={15} />Önceki Adım
          </button>
          {step < 5 ? (
            <button type="button" className="st-btn st-btn-primary" onClick={() => setStep(s => Math.min(5, s + 1))}>
              Sonraki Adım<ArrowRight size={15} />
            </button>
          ) : (
            <button type="button" className="st-btn st-btn-primary st-btn-lg" disabled={creating} onClick={handleFinish}>
              {creating ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
              {mode === 'series' ? 'Diziyi Oluştur ve 1. Bölümü Aç' : 'Projeyi Oluştur ve Başla'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
