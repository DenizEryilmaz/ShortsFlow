import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  AlertTriangle, ArrowDown, ArrowLeft, ArrowUp, Check, CheckCircle2, Clapperboard, Copy,
  Download, Film, Image as ImageIcon, Link2, Loader2, Mic, Music, Play, Plus, RefreshCw,
  Sliders, Sparkles, Trash2, Undo2, Upload, Users, Video, Volume2, Wand2,
} from 'lucide-react';
import { apiJson, getApiUrl } from '../api';
import {
  API, ASPECT_RATIOS, BGM_PRESETS, CAMERA_MOVES, CAPTION_STYLES, defaultSettings,
  emptyScene, formatEta, INGREDIENT_TYPES, LANGUAGES, mediaUrl, requestJson,
  SHOT_SIZES, textSig, TRANSITIONS,
} from '../constants';
import { useStudio } from '../context/StudioContext';
import DeliveryTheater from '../components/DeliveryTheater';
import { EmptyState, QualityPicker } from '../components/ui/Primitives';

const STEPS = [
  { id: 'plan', num: '1', label: 'Planla' },
  { id: 'produce', num: '2', label: 'Üret' },
  { id: 'deliver', num: '3', label: 'Teslim Et' },
];

export default function EpisodeWorkspacePage() {
  const { seriesId, episodeId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const {
    library, models, voices, styles, latestVideoByProject, activeJobByProject,
    saveDoc, deleteDoc, produceJob, uploadImage, uploadAudio, refreshCatalog, refreshLibrary,
    addToast, confirm,
  } = useStudio();

  const episodeRow = library.project.find(p => p.id === episodeId);
  const effectiveSeriesId = seriesId || episodeRow?.data?.series_id || '';
  const seriesRow = library.series.find(s => s.id === effectiveSeriesId);

  const stepParam = searchParams.get('step');
  const step = STEPS.some(s => s.id === stepParam) ? stepParam : 'plan';
  const setStep = next => {
    const p = new URLSearchParams(searchParams);
    p.set('step', next);
    setSearchParams(p, { replace: true });
  };

  const [draft, setDraft] = useState(null);
  const [dirty, setDirty] = useState(false);
  const [saveState, setSaveState] = useState('');
  const [undoStack, setUndoStack] = useState([]);
  const [activeSceneId, setActiveSceneId] = useState('');
  const [busyAction, setBusyAction] = useState('');
  const [installingVoice, setInstallingVoice] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [estimate, setEstimate] = useState(null);
  const [bgmPreview, setBgmPreview] = useState('');

  const lastLoadedIdRef = useRef('');
  const lastRevisionRef = useRef(0);
  const dirtyRef = useRef(false);
  const saveTimerRef = useRef(null);
  const latestRowRef = useRef(episodeRow);
  latestRowRef.current = episodeRow;

  // Sync draft from server on episode switch or external update (e.g. worker patched scene)
  useEffect(() => {
    if (!episodeRow) return;
    const isNewEpisode = lastLoadedIdRef.current !== episodeRow.id;
    const revChanged = lastRevisionRef.current !== episodeRow.revision;
    if (isNewEpisode || (revChanged && !dirtyRef.current)) {
      lastLoadedIdRef.current = episodeRow.id;
      lastRevisionRef.current = episodeRow.revision;
      setDraft(episodeRow.data);
      setDirty(false);
      dirtyRef.current = false;
      setSaveState(isNewEpisode ? '' : 'Güncellendi');
      if (isNewEpisode) {
        setUndoStack([]);
        const firstId = episodeRow.data.script?.scenes?.[0]?.id || '';
        setActiveSceneId(firstId);
      }
    }
  }, [episodeRow?.id, episodeRow?.revision, episodeRow]);

  // Keep activeSceneId valid
  const scenes = draft?.script?.scenes || [];
  useEffect(() => {
    if (scenes.length && !scenes.some(s => s.id === activeSceneId)) {
      setActiveSceneId(scenes[0].id);
    }
  }, [scenes, activeSceneId]);

  // Persist helper
  const persistNow = useCallback(async (nextData, silent = false) => {
    const row = latestRowRef.current;
    if (!row || !nextData) return null;
    if (saveTimerRef.current) {
      clearTimeout(saveTimerRef.current);
      saveTimerRef.current = null;
    }
    setSaveState('Kaydediliyor…');
    try {
      const saved = await saveDoc('project', nextData, row);
      lastRevisionRef.current = saved.revision;
      setDirty(false);
      dirtyRef.current = false;
      setSaveState('Kaydedildi');
      return saved;
    } catch (err) {
      setSaveState('Kaydedilemedi');
      if (!silent) addToast(err.detail || err.message || 'Değişiklikler kaydedilemedi.', 'err');
      return null;
    }
  }, [saveDoc, addToast]);

  // Apply edit + push undo + schedule debounced auto-save
  const applyDraft = useCallback((updater, pushUndo = true) => {
    setDraft(prev => {
      if (!prev) return prev;
      const next = typeof updater === 'function' ? updater(prev) : updater;
      if (pushUndo) {
        setUndoStack(stack => [...stack.slice(-24), prev]);
      }
      setDirty(true);
      dirtyRef.current = true;
      setSaveState('Kaydediliyor…');
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
      saveTimerRef.current = setTimeout(() => {
        persistNow(next, false);
      }, 900);
      return next;
    });
  }, [persistNow]);

  // Cleanup timer on unmount
  useEffect(() => () => {
    if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
  }, []);

  // Undo (Ctrl+Z) & J/K scene navigation
  const handleUndo = useCallback(() => {
    setUndoStack(stack => {
      if (!stack.length) return stack;
      const prev = stack[stack.length - 1];
      applyDraft(prev, false);
      addToast('Son değişiklik geri alındı.', 'info', { duration: 2000 });
      return stack.slice(0, -1);
    });
  }, [applyDraft, addToast]);

  useEffect(() => {
    const onKey = e => {
      const tag = (e.target?.tagName || '').toLowerCase();
      const inInput = ['input', 'textarea', 'select'].includes(tag);
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !e.shiftKey && !inInput) {
        if (undoStack.length) {
          e.preventDefault();
          handleUndo();
        }
      } else if (!inInput && step === 'produce' && scenes.length > 1) {
        const idx = scenes.findIndex(s => s.id === activeSceneId);
        if (e.key.toLowerCase() === 'j' && idx < scenes.length - 1) {
          setActiveSceneId(scenes[idx + 1].id);
        } else if (e.key.toLowerCase() === 'k' && idx > 0) {
          setActiveSceneId(scenes[idx - 1].id);
        }
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [undoStack.length, handleUndo, step, scenes, activeSceneId]);

  // Fetch ETA estimate when step === 'deliver' or model changes
  useEffect(() => {
    if (!draft) return;
    const sc = scenes.length || draft.scene_count || Math.max(3, Math.round((draft.duration || 30) / 6));
    const img = draft.settings?.image || 'flux2-klein-4b';
    const vid = draft.settings?.video || 'freevideo-h3';
    apiJson(`${API}/estimate?episodes=1&scenes=${sc}&image=${encodeURIComponent(img)}&video=${encodeURIComponent(vid)}`)
      .then(setEstimate)
      .catch(() => {});
  }, [draft?.settings?.image, draft?.settings?.video, draft?.duration, draft?.scene_count, scenes.length]);

  const seriesCastIds = useMemo(() => {
    if (!seriesRow) return [];
    const fromChars = library.character.filter(c => (c.data.series_ids || []).includes(seriesRow.id)).map(c => c.id);
    return Array.from(new Set([...(seriesRow.data.character_ids || []), ...fromChars]));
  }, [seriesRow, library.character]);

  const orderedIngredients = useMemo(() => {
    const inSeries = new Set(seriesCastIds);
    return [...library.character].sort((a, b) => Number(inSeries.has(b.id)) - Number(inSeries.has(a.id)));
  }, [library.character, seriesCastIds]);

  const voiceModels = useMemo(() => models.filter(m => m.kind === 'voice'), [models]);
  const langVoices = useMemo(
    () => voiceModels.filter(m => m.ready && m.language === (draft?.settings?.language || 'tr')),
    [voiceModels, draft?.settings?.language],
  );
  const suggestedInstallVoice = useMemo(
    () => voices.find(v => !v.installed && v.language === (draft?.settings?.language || 'tr')),
    [voices, draft?.settings?.language],
  );

  if (!episodeRow || !draft) {
    return (
      <div className="st-page">
        <EmptyState
          icon={<Film size={28} />}
          title="Bölüm bulunamadı"
          body="Bu bölüm silinmiş veya taşınmış olabilir."
          action={<button type="button" className="st-btn" onClick={() => navigate('/series')}>Dizilere dön</button>}
        />
      </div>
    );
  }

  const activeSceneIndex = scenes.findIndex(s => s.id === activeSceneId);
  const activeScene = activeSceneIndex >= 0 ? scenes[activeSceneIndex] : null;
  const latestVideoJob = latestVideoByProject[episodeId];
  const activeJob = activeJobByProject[episodeId];

  const updateSettings = patch => applyDraft(cur => ({
    ...cur,
    settings: { ...(cur.settings || defaultSettings(models)), ...patch },
  }));

  const updateScenes = fn => applyDraft(cur => {
    const currentScript = cur.script || { title: cur.name, logline: cur.brief, scenes: [] };
    const nextScenes = fn(currentScript.scenes || []);
    return { ...cur, script: { ...currentScript, scenes: nextScenes } };
  });

  const updateActiveScene = patch => {
    if (!activeScene) return;
    updateScenes(list => list.map(s => (s.id === activeScene.id ? { ...s, ...patch } : s)));
  };

  const addScene = () => {
    const fresh = emptyScene(6);
    fresh.title = `Sahne ${scenes.length + 1}`;
    updateScenes(list => [...list, fresh]);
    setActiveSceneId(fresh.id);
    setStep('produce');
  };

  const duplicateScene = sc => {
    const copy = {
      ...sc,
      id: crypto.randomUUID(),
      title: `${sc.title || 'Sahne'} (Kopya)`,
      first_asset: '',
      last_asset: '',
      audio_asset: '',
      clip_asset: '',
      takes: {},
    };
    updateScenes(list => {
      const idx = list.findIndex(x => x.id === sc.id);
      const next = [...list];
      next.splice(idx + 1, 0, copy);
      return next;
    });
    setActiveSceneId(copy.id);
  };

  const removeScene = async sc => {
    const ok = await confirm({
      title: 'Sahneyi sil',
      body: `"${sc.title || 'Bu sahne'}" bölümden kaldırılsın mı?`,
      confirmLabel: 'Sil',
      danger: true,
    });
    if (!ok) return;
    updateScenes(list => list.filter(x => x.id !== sc.id));
  };

  const moveScene = (idx, dir) => {
    const target = idx + dir;
    if (target < 0 || target >= scenes.length) return;
    updateScenes(list => {
      const next = [...list];
      const [item] = next.splice(idx, 1);
      next.splice(target, 0, item);
      return next;
    });
  };

  const toggleEpisodeIngredient = id => {
    applyDraft(cur => {
      const exists = (cur.character_ids || []).includes(id);
      const nextIds = exists ? cur.character_ids.filter(x => x !== id) : [...(cur.character_ids || []), id];
      let nextScript = cur.script;
      if (exists && nextScript?.scenes?.length) {
        nextScript = {
          ...nextScript,
          scenes: nextScript.scenes.map(sc => ({
            ...sc,
            character_ids: (sc.character_ids || []).filter(x => x !== id),
            speaker_id: sc.speaker_id === id ? '' : sc.speaker_id,
          })),
        };
      }
      return { ...cur, character_ids: nextIds, script: nextScript };
    });
  };

  const attachAllSeriesCast = () => {
    applyDraft(cur => ({
      ...cur,
      character_ids: Array.from(new Set([...(cur.character_ids || []), ...seriesCastIds])),
    }));
    addToast('Dizi kadrosu bölüme bağlandı.', 'ok');
  };

  const runProduction = async (kind, extra = {}) => {
    setBusyAction(kind);
    try {
      if (dirtyRef.current) {
        const saved = await persistNow(draft, false);
        if (!saved) return;
      }
      await produceJob(episodeId, kind, extra);
    } catch (err) {
      addToast(err.detail || err.message || 'Üretim başlatılamadı.', 'err');
    } finally {
      setBusyAction('');
    }
  };

  const handleInstallVoice = async voiceId => {
    setInstallingVoice(voiceId);
    try {
      await apiJson(`${API}/voices/${voiceId}/install`, { method: 'POST' });
      await refreshCatalog();
      updateSettings({ voice: voiceId });
      addToast('Ücretsiz ses indirildi ve seçildi.', 'ok');
    } catch (err) {
      addToast(err.detail || err.message || 'Ses indirilemedi.', 'err');
    } finally {
      setInstallingVoice('');
    }
  };

  const handleChainPreviousFrame = async () => {
    if (activeSceneIndex <= 0) return;
    const prev = scenes[activeSceneIndex - 1];
    if (prev.last_asset) {
      updateActiveScene({ first_asset: prev.last_asset });
      addToast('Önceki sahnenin son karesi başlangıç karesi olarak bağlandı.', 'ok');
      return;
    }
    if (prev.clip_asset) {
      setBusyAction('chain');
      try {
        const res = await apiJson(`${API}/assets/${prev.clip_asset}/last-frame`, { method: 'POST' });
        updateActiveScene({ first_asset: res.id });
        addToast('Önceki sahnenin klibinden son kare çıkarılıp bağlandı.', 'ok');
      } catch (err) {
        addToast(err.detail || err.message || 'Son kare çıkarılamadı.', 'err');
      } finally {
        setBusyAction('');
      }
    } else {
      addToast('Önceki sahnede son kare veya video klibi bulunmuyor.', 'info');
    }
  };

  const handleUploadSceneFrame = async (field, file) => {
    if (!file) return;
    setBusyAction(field);
    try {
      const id = await uploadImage(file);
      updateActiveScene({ [field]: id });
      addToast('Görsel yüklendi.', 'ok');
    } catch (err) {
      addToast(err.message || 'Görsel yüklenemedi.', 'err');
    } finally {
      setBusyAction('');
    }
  };

  const handleUploadBgm = async file => {
    if (!file) return;
    setBusyAction('bgm');
    try {
      const id = await uploadAudio(file);
      updateSettings({ bgm_preset: 'custom', bgm_asset: id });
      addToast('Özel arka plan müziği yüklendi.', 'ok');
    } catch (err) {
      addToast(err.message || 'Ses dosyası yüklenemedi.', 'err');
    } finally {
      setBusyAction('');
    }
  };

  const handleDeleteEpisode = async () => {
    const ok = await deleteDoc(episodeId, draft.name);
    if (ok) navigate(seriesRow ? `/series/${seriesRow.id}` : '/series');
  };

  const attachedCharacters = library.character.filter(c => (draft.character_ids || []).includes(c.id));
  const missingSeriesCast = seriesCastIds.filter(id => !(draft.character_ids || []).includes(id));

  // Stale detection for active scene
  const audioStale = Boolean(
    activeScene?.audio_asset && activeScene?.narration_hash && textSig(activeScene.narration) !== activeScene.narration_hash,
  );
  const visualStale = Boolean(
    activeScene?.first_asset && activeScene?.visual_hash && textSig(activeScene.visual_prompt) !== activeScene.visual_hash,
  );
  const durationOverrun = Boolean(
    activeScene?.spoken_duration && activeScene.spoken_duration > Number(activeScene.duration || 5) + 0.3,
  );

  const readyAudioCount = scenes.filter(s => s.audio_asset).length;
  const readyFirstCount = scenes.filter(s => s.first_asset).length;
  const readyClipCount = scenes.filter(s => s.clip_asset).length;

  return (
    <div className="st-page">
      <div className="st-workspace-top">
        <div className="st-breadcrumb">
          <button
            type="button"
            className="st-btn st-btn-sm"
            onClick={() => navigate(seriesRow ? `/series/${seriesRow.id}` : '/series')}
          >
            <ArrowLeft size={14} />{seriesRow ? seriesRow.data.name : 'Diziler'}
          </button>
          <span className="st-muted">/</span>
          <input
            className="st-title-input"
            value={draft.name}
            onChange={e => applyDraft(cur => ({ ...cur, name: e.target.value }))}
            aria-label="Bölüm başlığı"
          />
        </div>
        <div className="st-actions" style={{ margin: 0 }}>
          {saveState && <span className="st-save-pill">{dirty ? 'Kaydediliyor…' : saveState}</span>}
          <button
            type="button"
            className="st-btn st-btn-sm"
            disabled={!undoStack.length}
            title="Son değişikliği geri al (Ctrl+Z)"
            onClick={handleUndo}
          >
            <Undo2 size={14} />Geri al
          </button>
          <button type="button" className="st-btn st-btn-sm st-btn-danger" onClick={handleDeleteEpisode}>
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* 3-Step Workflow Bar */}
      <div className="st-stepper">
        {STEPS.map(item => (
          <button
            key={item.id}
            type="button"
            className={step === item.id ? 'st-step active' : 'st-step'}
            onClick={() => setStep(item.id)}
          >
            <span className="st-step-num">{item.num}</span>
            <span>{item.label}</span>
            {item.id === 'produce' && scenes.length > 0 && (
              <small className="st-step-meta">{readyClipCount}/{scenes.length} klip</small>
            )}
            {item.id === 'deliver' && latestVideoJob && (
              <CheckCircle2 size={14} style={{ color: 'var(--ok)' }} />
            )}
          </button>
        ))}
        {activeJob && (
          <div className="st-step-live">
            <Loader2 size={14} className="animate-spin" />
            <span>
              {activeJob.status === 'running' ? 'Üretiliyor' : 'Sırada'}
              {activeJob.latest_event?.match(/%(\d{1,3})/) ? ` · %${activeJob.latest_event.match(/%(\d{1,3})/)[1]}` : ''}
            </span>
          </div>
        )}
      </div>

      {/* STEP 1: PLANLA */}
      {step === 'plan' && (
        <div className="st-stack">
          <section className="st-card">
            <div className="st-row-between" style={{ marginBottom: 12 }}>
              <h2 style={{ margin: 0 }}>Hikâye &amp; Bölüm Ayarları</h2>
              <span className="st-badge">{styles.find(s => s.id === draft.style)?.name || draft.style}</span>
            </div>

            <label className="st-field">
              <span>Bölüm fikri / hikâye özeti</span>
              <textarea
                rows={3}
                placeholder="Bu bölümde neler oluyor? Karakterler arasındaki diyalog ve çatışmayı kısaca anlatın…"
                value={draft.brief}
                onChange={e => applyDraft(cur => ({ ...cur, brief: e.target.value }))}
              />
            </label>

            <div className="st-form-grid four">
              <label className="st-field">
                <span>Görsel stil</span>
                <select value={draft.style} onChange={e => applyDraft(cur => ({ ...cur, style: e.target.value }))}>
                  {styles.map(st => <option key={st.id} value={st.id}>{st.name}</option>)}
                </select>
              </label>
              <label className="st-field">
                <span>Hedef süre (sn)</span>
                <input
                  type="number"
                  min={8}
                  max={180}
                  value={draft.duration}
                  onChange={e => applyDraft(cur => ({ ...cur, duration: Math.max(8, Number(e.target.value) || 30) }))}
                />
              </label>
              <label className="st-field">
                <span>Sahne sayısı (0 = otomatik)</span>
                <input
                  type="number"
                  min={0}
                  max={20}
                  value={draft.scene_count || 0}
                  onChange={e => applyDraft(cur => ({ ...cur, scene_count: Math.max(0, Number(e.target.value) || 0) }))}
                />
              </label>
              <label className="st-field">
                <span>Format</span>
                <select
                  value={draft.settings?.aspect_ratio || '9:16'}
                  onChange={e => {
                    const ratio = e.target.value;
                    const spec = ASPECT_RATIOS[ratio];
                    updateSettings({ aspect_ratio: ratio, width: spec.width, height: spec.height });
                  }}
                >
                  {Object.entries(ASPECT_RATIOS).map(([id, spec]) => <option key={id} value={id}>{spec.label}</option>)}
                </select>
              </label>
            </div>

            <div className="st-form-grid two" style={{ marginTop: 10 }}>
              <label className="st-field">
                <span>Anlatım dili</span>
                <select
                  value={draft.settings?.language || 'tr'}
                  onChange={e => {
                    const lang = e.target.value;
                    const match = voiceModels.find(m => m.ready && m.language === lang);
                    updateSettings({ language: lang, ...(match ? { voice: match.id } : {}) });
                  }}
                >
                  {Object.entries(LANGUAGES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                </select>
              </label>
              <label className="st-field">
                <span>Varsayılan anlatıcı sesi</span>
                <select value={draft.settings?.voice || ''} onChange={e => updateSettings({ voice: e.target.value })}>
                  {voiceModels.map(m => (
                    <option key={m.id} value={m.id} disabled={!m.ready}>
                      {m.name}{m.ready ? '' : ' (Kurulu değil)'}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {langVoices.length === 0 && suggestedInstallVoice && (
              <div className="st-banner-warn">
                <AlertTriangle size={16} />
                <span>
                  Seçili dil ({LANGUAGES[draft.settings?.language]}) için kurulu ses yok. Ücretsiz <strong>{suggestedInstallVoice.name}</strong> sesini tek tıkla indirebilirsiniz.
                </span>
                <button
                  type="button"
                  className="st-btn st-btn-sm st-btn-primary"
                  disabled={Boolean(installingVoice)}
                  onClick={() => handleInstallVoice(suggestedInstallVoice.id)}
                >
                  {installingVoice === suggestedInstallVoice.id ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
                  Ücretsiz İndir
                </button>
              </div>
            )}

            <div style={{ marginTop: 14 }}>
              <span className="st-field-label">Üretim kalite profili</span>
              <QualityPicker
                image={draft.settings?.image}
                video={draft.settings?.video}
                onChange={(image, video) => updateSettings({ image, video })}
              />
            </div>
          </section>

          {/* Cast & Ingredients */}
          <section className="st-card">
            <div className="st-row-between" style={{ marginBottom: 10 }}>
              <div>
                <h2 style={{ margin: 0 }}>Bölüm Kadrosu &amp; Mekanlar</h2>
                <p className="st-muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
                  Seçilen bileşenlerin referans görselleri ve sesleri sahne üretimine otomatik aktarılır.
                </p>
              </div>
              <div className="st-actions" style={{ margin: 0 }}>
                {missingSeriesCast.length > 0 && (
                  <button type="button" className="st-btn st-btn-sm" onClick={attachAllSeriesCast}>
                    <Users size={14} />Dizi kadrosunu bağla ({missingSeriesCast.length})
                  </button>
                )}
                <button
                  type="button"
                  className="st-btn st-btn-sm"
                  onClick={() => navigate(`/assets?tab=ingredients${seriesRow ? `&series=${seriesRow.id}` : ''}`)}
                >
                  <Plus size={14} />Yeni Bileşen
                </button>
              </div>
            </div>

            {orderedIngredients.length === 0 ? (
              <p className="st-muted" style={{ fontSize: 13 }}>
                Henüz kayıtlı karakter veya mekan yok. Varlıklar sayfasından ekleyebilirsiniz.
              </p>
            ) : (
              <div className="st-cast-chips">
                {orderedIngredients.map(c => {
                  const selected = (draft.character_ids || []).includes(c.id);
                  return (
                    <button
                      key={c.id}
                      type="button"
                      className={selected ? 'st-cast-chip selected' : 'st-cast-chip'}
                      onClick={() => toggleEpisodeIngredient(c.id)}
                    >
                      {c.data.references?.[0] ? (
                        <img src={mediaUrl(c.data.references[0])} alt={c.data.name} />
                      ) : (
                        <span className="st-cast-fallback"><Users size={14} /></span>
                      )}
                      <div>
                        <strong>{c.data.name}</strong>
                        <small>{INGREDIENT_TYPES[c.data.ingredient_type || 'character']}</small>
                      </div>
                      {selected && <Check size={14} className="st-cast-check" />}
                    </button>
                  );
                })}
              </div>
            )}
          </section>

          {/* Script & Scene Plan */}
          <section className="st-card">
            <div className="st-row-between" style={{ marginBottom: 14 }}>
              <div>
                <h2 style={{ margin: 0 }}>Senaryo &amp; Sahne Planı ({scenes.length} sahne)</h2>
                <p className="st-muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
                  AI ile sıfırdan senaryo yazdırabilir veya sahneleri elle düzenleyebilirsiniz.
                </p>
              </div>
              <div className="st-actions" style={{ margin: 0 }}>
                <button
                  type="button"
                  className="st-btn st-btn-primary"
                  disabled={Boolean(busyAction)}
                  onClick={() => runProduction('script', { regenerate_script: true })}
                >
                  {busyAction === 'script' ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
                  {scenes.length ? 'Senaryoyu Yeniden Yaz' : 'Senaryo ve Sahne Planı Oluştur'}
                </button>
                <button
                  type="button"
                  className="st-btn"
                  disabled={Boolean(busyAction)}
                  onClick={() => runProduction('full')}
                >
                  <Clapperboard size={14} />Tek Tıkla Tam Bölüm Üret
                </button>
                <button type="button" className="st-btn" onClick={addScene}>
                  <Plus size={14} />Elle Sahne Ekle
                </button>
              </div>
            </div>

            {scenes.length === 0 ? (
              <EmptyState
                icon={<Wand2 size={26} />}
                title="Henüz sahne planı yok"
                body="Yukarıdaki 'Senaryo ve Sahne Planı Oluştur' butonuyla hikâyenizi saniyeler içinde sahnelere bölün."
              />
            ) : (
              <div className="st-scene-table">
                {scenes.map((sc, idx) => {
                  const speaker = library.character.find(c => c.id === sc.speaker_id);
                  return (
                    <div
                      key={sc.id}
                      className="st-scene-row"
                      onClick={() => { setActiveSceneId(sc.id); setStep('produce'); }}
                    >
                      <div className="st-scene-row-num">{idx + 1}</div>
                      <div className="st-scene-row-thumb">
                        {sc.first_asset ? <img src={mediaUrl(sc.first_asset)} alt={sc.title} /> : <ImageIcon size={16} />}
                      </div>
                      <div className="st-scene-row-main">
                        <strong>{sc.title || `Sahne ${idx + 1}`}</strong>
                        <p>{sc.narration || 'Seslendirme metni girilmedi…'}</p>
                      </div>
                      <div className="st-chips">
                        {speaker && <span className="st-badge st-badge-accent">{speaker.data.name}</span>}
                        <span className="st-badge">{sc.duration} sn</span>
                        <span className={sc.audio_asset ? 'st-badge st-badge-ok' : 'st-badge'}>Ses</span>
                        <span className={sc.first_asset ? 'st-badge st-badge-ok' : 'st-badge'}>Kare</span>
                        <span className={sc.clip_asset ? 'st-badge st-badge-ok' : 'st-badge'}>Klip</span>
                      </div>
                      <div className="st-actions" style={{ margin: 0, gap: 4 }} onClick={e => e.stopPropagation()}>
                        <button type="button" className="st-icon-btn" disabled={idx === 0} onClick={() => moveScene(idx, -1)} title="Yukarı taşı">
                          <ArrowUp size={13} />
                        </button>
                        <button type="button" className="st-icon-btn" disabled={idx === scenes.length - 1} onClick={() => moveScene(idx, 1)} title="Aşağı taşı">
                          <ArrowDown size={13} />
                        </button>
                        <button type="button" className="st-icon-btn" onClick={() => duplicateScene(sc)} title="Kopyala">
                          <Copy size={13} />
                        </button>
                        <button type="button" className="st-icon-btn" onClick={() => removeScene(sc)} title="Sil">
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </div>
                  );
                })}
                <div className="st-row-between" style={{ marginTop: 14 }}>
                  <span className="st-muted" style={{ fontSize: 13 }}>
                    Toplam {scenes.length} sahne · {scenes.reduce((acc, s) => acc + Number(s.duration || 0), 0)} sn · {readyAudioCount} ses, {readyFirstCount} kare, {readyClipCount} klip hazır
                  </span>
                  <button type="button" className="st-btn st-btn-primary" onClick={() => setStep('produce')}>
                    2. Aşamaya Geç: Sahneleri Üret →
                  </button>
                </div>
              </div>
            )}
          </section>
        </div>
      )}

      {/* STEP 2: ÜRET (Focused Master-Detail Storyboard) */}
      {step === 'produce' && (
        <div className="st-stack">
          {/* Horizontal Storyboard Strip */}
          <div className="st-storyboard">
            {scenes.map((sc, idx) => {
              const isSelected = sc.id === activeSceneId;
              const isStale = (sc.audio_asset && sc.narration_hash && textSig(sc.narration) !== sc.narration_hash)
                || (sc.first_asset && sc.visual_hash && textSig(sc.visual_prompt) !== sc.visual_hash);
              return (
                <button
                  key={sc.id}
                  type="button"
                  className={isSelected ? 'st-sb-card active' : 'st-sb-card'}
                  onClick={() => setActiveSceneId(sc.id)}
                >
                  <div className="st-sb-thumb">
                    {sc.first_asset ? <img src={mediaUrl(sc.first_asset)} alt={sc.title} /> : <Film size={20} />}
                    <span className="st-sb-num">{idx + 1}</span>
                    <span className="st-sb-dur">{sc.duration}s</span>
                    {isStale && <span className="st-sb-stale" title="Metin değişti — yeniden üret">!</span>}
                  </div>
                  <div className="st-sb-meta">
                    <strong>{sc.title || `Sahne ${idx + 1}`}</strong>
                    <div className="st-sb-dots">
                      <span className={sc.audio_asset ? 'ok' : ''} title="Ses">S</span>
                      <span className={sc.first_asset ? 'ok' : ''} title="İlk kare">K</span>
                      <span className={sc.clip_asset ? 'ok' : ''} title="Klip">V</span>
                    </div>
                  </div>
                </button>
              );
            })}
            <button type="button" className="st-sb-add" onClick={addScene}>
              <Plus size={18} />
              <span>Sahne Ekle</span>
            </button>
          </div>

          {!activeScene ? (
            <EmptyState
              icon={<Film size={28} />}
              title="Henüz sahne yok"
              body="Önce 1. aşamadan senaryo oluşturun veya elle sahne ekleyin."
              action={<button type="button" className="st-btn st-btn-primary" onClick={() => setStep('plan')}>Planlama aşamasına dön</button>}
            />
          ) : (
            <div className="st-scene-workspace">
              {/* Left: Visual & Audio Stages */}
              <div className="st-scene-media-col">
                <div className="st-card">
                  <div className="st-row-between" style={{ marginBottom: 10 }}>
                    <strong>Sahne {activeSceneIndex + 1} Çıktıları</strong>
                    <button
                      type="button"
                      className="st-btn st-btn-sm st-btn-primary"
                      disabled={Boolean(busyAction)}
                      onClick={() => runProduction('scene_all', { scene_id: activeScene.id })}
                    >
                      {busyAction === 'scene_all' ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                      Bu Sahneyi Komple Üret
                    </button>
                  </div>

                  {/* Stage: Audio */}
                  <div className="st-stage-box">
                    <div className="st-row-between">
                      <span className="st-stage-title"><Mic size={14} />Seslendirme</span>
                      <div className="st-actions" style={{ margin: 0, gap: 6 }}>
                        {audioStale && <span className="st-badge st-badge-warn">Metin değişti</span>}
                        <button
                          type="button"
                          className="st-btn st-btn-sm"
                          disabled={Boolean(busyAction)}
                          onClick={() => runProduction('scene_audio', { scene_id: activeScene.id })}
                        >
                          <RefreshCw size={12} />{activeScene.audio_asset ? 'Yeniden üret' : 'Ses üret'}
                        </button>
                      </div>
                    </div>
                    {activeScene.audio_asset ? (
                      <audio key={activeScene.audio_asset} controls src={mediaUrl(activeScene.audio_asset)} style={{ width: '100%', height: 34, marginTop: 8 }} />
                    ) : (
                      <p className="st-muted" style={{ fontSize: 12, margin: '8px 0 0' }}>Henüz seslendirme üretilmedi.</p>
                    )}
                    {activeScene.spoken_duration && (
                      <div className={durationOverrun ? 'st-stage-note warn' : 'st-stage-note'}>
                        Konuşma süresi: {Number(activeScene.spoken_duration).toFixed(1)} sn / Sahne: {activeScene.duration} sn
                        {durationOverrun && (
                          <button
                            type="button"
                            className="st-btn st-btn-sm"
                            style={{ marginLeft: 8 }}
                            onClick={() => updateActiveScene({ duration: Math.ceil(activeScene.spoken_duration + 0.6) })}
                          >
                            Süreyi {Math.ceil(activeScene.spoken_duration + 0.6)} sn yap
                          </button>
                        )}
                      </div>
                    )}
                    {activeScene.takes?.audio?.length > 1 && (
                      <div className="st-takes">
                        <span>Çekimler:</span>
                        {activeScene.takes.audio.map((aid, i) => (
                          <button
                            key={aid}
                            type="button"
                            className={activeScene.audio_asset === aid ? 'st-take-btn active' : 'st-take-btn'}
                            onClick={() => updateActiveScene({ audio_asset: aid })}
                          >
                            #{i + 1}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Stage: First Frame */}
                  <div className="st-stage-box">
                    <div className="st-row-between">
                      <span className="st-stage-title"><ImageIcon size={14} />Başlangıç Karesi</span>
                      <div className="st-actions" style={{ margin: 0, gap: 6 }}>
                        {visualStale && <span className="st-badge st-badge-warn">Tarif değişti</span>}
                        {activeSceneIndex > 0 && (
                          <button
                            type="button"
                            className="st-btn st-btn-sm"
                            title="Önceki sahnenin son karesini bağla"
                            onClick={handleChainPreviousFrame}
                          >
                            <Link2 size={12} />Öncekinden bağla
                          </button>
                        )}
                        <button
                          type="button"
                          className="st-btn st-btn-sm"
                          disabled={Boolean(busyAction)}
                          onClick={() => runProduction('scene_first', { scene_id: activeScene.id })}
                        >
                          <RefreshCw size={12} />{activeScene.first_asset ? 'Yeniden üret' : 'Kare üret'}
                        </button>
                      </div>
                    </div>
                    {activeScene.first_asset ? (
                      <div className="st-stage-preview">
                        <img src={mediaUrl(activeScene.first_asset)} alt="Başlangıç karesi" />
                      </div>
                    ) : (
                      <p className="st-muted" style={{ fontSize: 12, margin: '8px 0 0' }}>Henüz başlangıç karesi üretilmedi.</p>
                    )}
                    {activeScene.takes?.first?.length > 1 && (
                      <div className="st-takes-thumbs">
                        {activeScene.takes.first.map((aid, i) => (
                          <button
                            key={aid}
                            type="button"
                            className={activeScene.first_asset === aid ? 'st-take-thumb active' : 'st-take-thumb'}
                            onClick={() => updateActiveScene({ first_asset: aid })}
                            title={`Çekim #${i + 1}`}
                          >
                            <img src={mediaUrl(aid)} alt={`Çekim ${i + 1}`} />
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Stage: Clip */}
                  <div className="st-stage-box">
                    <div className="st-row-between">
                      <span className="st-stage-title"><Video size={14} />Hareket Klibi</span>
                      <button
                        type="button"
                        className="st-btn st-btn-sm"
                        disabled={Boolean(busyAction)}
                        onClick={() => runProduction('scene_clip', { scene_id: activeScene.id })}
                      >
                        <RefreshCw size={12} />{activeScene.clip_asset ? 'Yeniden üret' : 'Klip üret'}
                      </button>
                    </div>
                    {activeScene.clip_asset ? (
                      <div className="st-stage-preview">
                        <video key={activeScene.clip_asset} controls playsInline loop src={mediaUrl(activeScene.clip_asset)} />
                      </div>
                    ) : (
                      <p className="st-muted" style={{ fontSize: 12, margin: '8px 0 0' }}>Henüz video klibi üretilmedi.</p>
                    )}
                    {activeScene.takes?.clip?.length > 1 && (
                      <div className="st-takes">
                        <span>Klip çekimleri:</span>
                        {activeScene.takes.clip.map((aid, i) => (
                          <button
                            key={aid}
                            type="button"
                            className={activeScene.clip_asset === aid ? 'st-take-btn active' : 'st-take-btn'}
                            onClick={() => updateActiveScene({ clip_asset: aid })}
                          >
                            #{i + 1}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Optional Last Frame */}
                  {(activeScene.end_prompt || activeScene.last_asset) && (
                    <div className="st-stage-box">
                      <div className="st-row-between">
                        <span className="st-stage-title"><ImageIcon size={14} />Bitiş Karesi (Opsiyonel)</span>
                        <button
                          type="button"
                          className="st-btn st-btn-sm"
                          disabled={Boolean(busyAction) || !activeScene.end_prompt?.trim()}
                          onClick={() => runProduction('scene_last', { scene_id: activeScene.id })}
                        >
                          <RefreshCw size={12} />{activeScene.last_asset ? 'Yeniden üret' : 'Son kare üret'}
                        </button>
                      </div>
                      {activeScene.last_asset && (
                        <div className="st-stage-preview">
                          <img src={mediaUrl(activeScene.last_asset)} alt="Bitiş karesi" />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Right: Focused Scene Editor */}
              <div className="st-scene-edit-col">
                <div className="st-card">
                  <div className="st-row-between" style={{ marginBottom: 14 }}>
                    <div>
                      <span className="st-kicker">SAHNE {activeSceneIndex + 1} / {scenes.length} · J/K İLE GEÇİŞ</span>
                      <h2 style={{ margin: '2px 0 0' }}>{activeScene.title || `Sahne ${activeSceneIndex + 1}`}</h2>
                    </div>
                    <div className="st-actions" style={{ margin: 0, gap: 6 }}>
                      <button
                        type="button"
                        className="st-btn st-btn-sm"
                        disabled={Boolean(busyAction)}
                        onClick={() => runProduction('scene_rewrite', { scene_id: activeScene.id })}
                      >
                        <Wand2 size={13} />AI ile Yeniden Yaz
                      </button>
                      <button
                        type="button"
                        className="st-btn st-btn-sm"
                        disabled={activeSceneIndex <= 0}
                        onClick={() => setActiveSceneId(scenes[activeSceneIndex - 1].id)}
                      >
                        ← Önceki
                      </button>
                      <button
                        type="button"
                        className="st-btn st-btn-sm"
                        disabled={activeSceneIndex >= scenes.length - 1}
                        onClick={() => setActiveSceneId(scenes[activeSceneIndex + 1].id)}
                      >
                        Sonraki →
                      </button>
                    </div>
                  </div>

                  <div className="st-form-grid three">
                    <label className="st-field">
                      <span>Sahne başlığı</span>
                      <input value={activeScene.title || ''} onChange={e => updateActiveScene({ title: e.target.value })} />
                    </label>
                    <label className="st-field">
                      <span>Süre (sn)</span>
                      <input
                        type="number"
                        min={2}
                        max={20}
                        value={activeScene.duration || 5}
                        onChange={e => updateActiveScene({ duration: Math.max(2, Number(e.target.value) || 5) })}
                      />
                    </label>
                    <label className="st-field">
                      <span>Konuşan karakter</span>
                      <select
                        value={activeScene.speaker_id || ''}
                        onChange={e => updateActiveScene({ speaker_id: e.target.value })}
                      >
                        <option value="">Anlatıcı (Varsayılan)</option>
                        {attachedCharacters.map(c => (
                          <option key={c.id} value={c.id}>{c.data.name}</option>
                        ))}
                      </select>
                    </label>
                  </div>

                  <div className="st-form-grid two">
                    <label className="st-field">
                      <span>Çekim ölçeği</span>
                      <select value={activeScene.shot_size || ''} onChange={e => updateActiveScene({ shot_size: e.target.value })}>
                        {Object.entries(SHOT_SIZES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                      </select>
                    </label>
                    <label className="st-field">
                      <span>Kamera hareketi</span>
                      <select value={activeScene.camera_move || ''} onChange={e => updateActiveScene({ camera_move: e.target.value })}>
                        {Object.entries(CAMERA_MOVES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                      </select>
                    </label>
                  </div>

                  {attachedCharacters.length > 0 && (
                    <div className="st-field">
                      <span>Bu sahnede görünen bileşenler</span>
                      <div className="st-chips">
                        {attachedCharacters.map(c => {
                          const on = (activeScene.character_ids || []).includes(c.id);
                          return (
                            <button
                              key={c.id}
                              type="button"
                              className={on ? 'st-btn st-btn-sm st-btn-primary' : 'st-btn st-btn-sm'}
                              onClick={() => {
                                const next = on
                                  ? activeScene.character_ids.filter(id => id !== c.id)
                                  : [...(activeScene.character_ids || []), c.id];
                                updateActiveScene({ character_ids: next });
                              }}
                            >
                              {on && <Check size={12} />}{c.data.name}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  <label className="st-field">
                    <span>Seslendirme / Replik (Altyazı sesle birebir eşleşir)</span>
                    <textarea
                      rows={3}
                      value={activeScene.narration || ''}
                      onChange={e => updateActiveScene({ narration: e.target.value, caption: e.target.value })}
                    />
                  </label>

                  <label className="st-field">
                    <span>Görsel sahne tarifi</span>
                    <textarea
                      rows={3}
                      value={activeScene.visual_prompt || ''}
                      onChange={e => updateActiveScene({ visual_prompt: e.target.value })}
                    />
                  </label>

                  <div className="st-form-grid two">
                    <label className="st-field">
                      <span>Hareket tarifi</span>
                      <textarea
                        rows={2}
                        value={activeScene.motion_prompt || ''}
                        onChange={e => updateActiveScene({ motion_prompt: e.target.value })}
                      />
                    </label>
                    <label className="st-field">
                      <span>Bitiş karesi tarifi (opsiyonel)</span>
                      <textarea
                        rows={2}
                        placeholder="Sahne sonunda görüntünün nasıl bitmesini istersiniz?"
                        value={activeScene.end_prompt || ''}
                        onChange={e => updateActiveScene({ end_prompt: e.target.value })}
                      />
                    </label>
                  </div>

                  <div className="st-collapse">
                    <button type="button" className="st-btn st-btn-sm" onClick={() => setShowAdvanced(v => !v)}>
                      <Sliders size={13} />{showAdvanced ? 'Gelişmiş ayarları gizle' : 'Gelişmiş (Negatif tarif · Manuel görsel)'}
                    </button>
                    {showAdvanced && (
                      <div className="st-collapse-body">
                        <label className="st-field">
                          <span>İstenmeyen öğeler (Negatif tarif)</span>
                          <input
                            value={activeScene.negative_prompt || ''}
                            placeholder="blurry, text, watermark, distorted hands…"
                            onChange={e => updateActiveScene({ negative_prompt: e.target.value })}
                          />
                        </label>
                        <div className="st-actions" style={{ margin: '8px 0 0' }}>
                          <label className="st-btn st-btn-sm">
                            <Upload size={13} />İlk kare yükle
                            <input type="file" accept="image/*" hidden onChange={e => handleUploadSceneFrame('first_asset', e.target.files?.[0])} />
                          </label>
                          <label className="st-btn st-btn-sm">
                            <Upload size={13} />Son kare yükle
                            <input type="file" accept="image/*" hidden onChange={e => handleUploadSceneFrame('last_asset', e.target.files?.[0])} />
                          </label>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="st-row-between" style={{ marginTop: 18, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
                    <div className="st-actions" style={{ margin: 0 }}>
                      <button type="button" className="st-btn st-btn-sm" onClick={() => duplicateScene(activeScene)}>
                        <Copy size={13} />Kopyala
                      </button>
                      <button type="button" className="st-btn st-btn-sm st-btn-danger" onClick={() => removeScene(activeScene)}>
                        <Trash2 size={13} />Sil
                      </button>
                    </div>
                    <button type="button" className="st-btn st-btn-primary" onClick={() => setStep('deliver')}>
                      3. Aşamaya Geç: Kurgu ve Teslimat →
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* STEP 3: TESLİM ET */}
      {step === 'deliver' && (
        <div className="st-stack">
          {latestVideoJob && (
            <DeliveryTheater
              job={latestVideoJob}
              projectName={draft.name}
              aspectRatio={draft.settings?.aspect_ratio}
            />
          )}

          <section className="st-card">
            <div className="st-row-between" style={{ marginBottom: 14 }}>
              <div>
                <h2 style={{ margin: 0 }}>Kurgu, Altyazı &amp; Müzik Ayarları</h2>
                <p className="st-muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
                  Eksik sahne görselleri veya klipleri varsa final birleştirme sırasında otomatik tamamlanır.
                </p>
              </div>
              {estimate && (
                <span className="st-badge st-badge-accent">
                  Tahmini tam üretim: {formatEta(estimate.total_seconds)} · ~{estimate.estimated_mb} MB
                </span>
              )}
            </div>

            <div className="st-form-grid three">
              <label className="st-field">
                <span>Sahne geçişi</span>
                <select value={draft.settings?.transition || 'crossfade'} onChange={e => updateSettings({ transition: e.target.value })}>
                  {Object.entries(TRANSITIONS).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                </select>
              </label>
              <label className="st-field">
                <span>Altyazı stili</span>
                <select value={draft.settings?.caption_style || 'shorts'} onChange={e => updateSettings({ caption_style: e.target.value })}>
                  {Object.entries(CAPTION_STYLES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                </select>
              </label>
              <label className="st-field">
                <span>Arka plan müziği</span>
                <select value={draft.settings?.bgm_preset || ''} onChange={e => updateSettings({ bgm_preset: e.target.value })}>
                  {BGM_PRESETS.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                </select>
              </label>
            </div>

            {draft.settings?.bgm_preset && draft.settings.bgm_preset !== 'custom' && (
              <div className="st-actions" style={{ margin: '6px 0 12px' }}>
                <button
                  type="button"
                  className="st-btn st-btn-sm"
                  onClick={() => setBgmPreview(bgmPreview === draft.settings.bgm_preset ? '' : draft.settings.bgm_preset)}
                >
                  <Music size={13} />Müziği Dinle
                </button>
                {bgmPreview === draft.settings.bgm_preset && (
                  <audio controls autoPlay src={getApiUrl(`${API}/bgm/${draft.settings.bgm_preset}/preview`)} style={{ height: 32 }} />
                )}
              </div>
            )}

            {draft.settings?.bgm_preset === 'custom' && (
              <div className="st-actions" style={{ margin: '6px 0 12px' }}>
                <label className="st-btn st-btn-sm">
                  <Upload size={13} />MP3 / WAV Yükle
                  <input type="file" accept="audio/*" hidden onChange={e => handleUploadBgm(e.target.files?.[0])} />
                </label>
                {draft.settings?.bgm_asset && (
                  <audio controls src={mediaUrl(draft.settings.bgm_asset)} style={{ height: 32 }} />
                )}
              </div>
            )}

            <div className="st-toggles-row">
              <label className="st-checkbox">
                <input
                  type="checkbox"
                  checked={draft.settings?.sync_captions !== false}
                  onChange={e => updateSettings({ sync_captions: e.target.checked })}
                />
                <span>Altyazıyı sesle 1-1 eşleştir</span>
              </label>
              <label className="st-checkbox">
                <input
                  type="checkbox"
                  checked={draft.settings?.auto_translate_prompts !== false}
                  onChange={e => updateSettings({ auto_translate_prompts: e.target.checked })}
                />
                <span>Görsel/hareket tariflerini modele İngilizce ilet</span>
              </label>
              <label className="st-checkbox">
                <input
                  type="checkbox"
                  checked={draft.settings?.bgm_ducking !== false}
                  onChange={e => updateSettings({ bgm_ducking: e.target.checked })}
                />
                <span>Konuşurken arka plan müziğini otomatik kıs</span>
              </label>
            </div>

            {draft.settings?.bgm_preset && (
              <label className="st-field" style={{ maxWidth: 320, marginTop: 10 }}>
                <span>Müzik seviyesi (%{Math.round((draft.settings?.bgm_volume ?? 0.16) * 100)})</span>
                <input
                  type="range"
                  min={0.04}
                  max={0.5}
                  step={0.02}
                  value={draft.settings?.bgm_volume ?? 0.16}
                  onChange={e => updateSettings({ bgm_volume: Number(e.target.value) })}
                />
              </label>
            )}

            <div className="st-deliver-cta">
              <div>
                <strong>Final Bölümü Birleştir</strong>
                <p className="st-muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
                  {scenes.length} sahne · {readyAudioCount} ses · {readyFirstCount} kare · {readyClipCount} klip hazır.
                </p>
              </div>
              <button
                type="button"
                className="st-btn st-btn-primary st-btn-lg"
                disabled={Boolean(busyAction) || scenes.length === 0}
                onClick={() => runProduction('render')}
              >
                {busyAction === 'render' ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
                Final Videoyu Birleştir
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
