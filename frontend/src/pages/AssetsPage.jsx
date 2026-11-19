import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Check, Copy, Dices, Download, FileText, Layers, Loader2, Mic, Palette,
  Play, Plus, Save, Sparkles, Trash2, Upload, Users, Volume2,
} from 'lucide-react';
import { apiJson, getApiUrl } from '../api';
import {
  API, defaultSettings, INGREDIENT_TYPES, LANGUAGES, mediaUrl, requestJson,
} from '../constants';
import { useStudio } from '../context/StudioContext';
import { EmptyState } from '../components/ui/Primitives';

const ASSET_TABS = [
  { id: 'ingredients', label: 'Bileşenler (Karakter & Mekan)', icon: Users },
  { id: 'styles', label: 'Görsel Stiller', icon: Palette },
  { id: 'voices', label: 'Sesler', icon: Mic },
  { id: 'templates', label: 'Prompt Şablonları', icon: FileText },
];

const TEMPLATE_PURPOSES = {
  script: 'Senaryo',
  image: 'Görsel',
  motion: 'Hareket',
  character: 'Karakter',
};

const emptyIngredient = (seriesId = '', style = 'clay_stopmotion') => ({
  name: '',
  ingredient_type: 'character',
  description: '',
  style,
  voice: '',
  seed: Math.floor(100000 + Math.random() * 899999),
  series_ids: seriesId ? [seriesId] : [],
  references: [],
});

const emptyTemplate = () => ({
  name: '',
  purpose: 'script',
  body: '',
});

export default function AssetsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const {
    library, styles, models, voices, saveDoc, deleteDoc, uploadImage,
    refreshLibrary, refreshCatalog, addToast,
  } = useStudio();

  const tabParam = searchParams.get('tab');
  const tab = ASSET_TABS.some(t => t.id === tabParam) ? tabParam : 'ingredients';
  const setTab = next => {
    const p = new URLSearchParams(searchParams);
    p.set('tab', next);
    setSearchParams(p, { replace: true });
  };

  // Ingredients state
  const seriesQuery = searchParams.get('series') || '';
  const idQuery = searchParams.get('id') || '';
  const [ingSeriesFilter, setIngSeriesFilter] = useState(seriesQuery || 'all');
  const [ingTypeFilter, setIngTypeFilter] = useState('all');
  const [selectedIngId, setSelectedIngId] = useState(idQuery || '');
  const [ingDraft, setIngDraft] = useState(() => emptyIngredient(seriesQuery));
  const [busy, setBusy] = useState('');
  const [previewVoice, setPreviewVoice] = useState('');

  // Styles state
  const [styleLang, setStyleLang] = useState('tr');
  const [demoMode, setDemoMode] = useState('balanced');
  const [activeStyleVideo, setActiveStyleVideo] = useState('');

  // Voices state
  const [voiceLangFilter, setVoiceLangFilter] = useState('all');
  const [installingVoice, setInstallingVoice] = useState('');

  // Templates state
  const [selectedTplId, setSelectedTplId] = useState('');
  const [tplDraft, setTplDraft] = useState(emptyTemplate);

  // Sync selected ingredient from URL or list
  useEffect(() => {
    if (idQuery) {
      const found = library.character.find(c => c.id === idQuery);
      if (found) {
        setSelectedIngId(found.id);
        setIngDraft(found.data);
      }
    }
  }, [idQuery, library.character]);

  const filteredIngredients = useMemo(() => library.character.filter(c => {
    if (ingSeriesFilter !== 'all' && !(c.data.series_ids || []).includes(ingSeriesFilter)) return false;
    if (ingTypeFilter !== 'all' && (c.data.ingredient_type || 'character') !== ingTypeFilter) return false;
    return true;
  }), [library.character, ingSeriesFilter, ingTypeFilter]);

  const selectedIngRow = library.character.find(c => c.id === selectedIngId) || null;
  const readyVoices = useMemo(() => models.filter(m => m.kind === 'voice' && m.ready), [models]);

  const handleSelectIngredient = row => {
    setSelectedIngId(row.id);
    setIngDraft(row.data);
  };

  const handleNewIngredient = () => {
    setSelectedIngId('');
    setIngDraft(emptyIngredient(ingSeriesFilter !== 'all' ? ingSeriesFilter : ''));
  };

  const handleSaveIngredient = async () => {
    if (!ingDraft.name.trim()) {
      addToast('Bileşen adı girin.', 'err');
      return;
    }
    setBusy('save_ing');
    try {
      const saved = await saveDoc('character', ingDraft, selectedIngRow);
      setSelectedIngId(saved.id);
      setIngDraft(saved.data);
      addToast('Bileşen kaydedildi.', 'ok');
    } catch (err) {
      addToast(err.detail || err.message || 'Kaydedilemedi.', 'err');
    } finally {
      setBusy('');
    }
  };

  const handleGenerateRef = async () => {
    setBusy('gen_ref');
    try {
      const saved = await saveDoc('character', ingDraft, selectedIngRow);
      setSelectedIngId(saved.id);
      await apiJson(`${API}/characters/${saved.id}/generate`, requestJson('POST', {
        settings: defaultSettings(models, 'tr'),
      }));
      await refreshLibrary();
      addToast('Referans görsel üretimi kuyruğa alındı.', 'ok');
    } catch (err) {
      addToast(err.detail || err.message || 'Referans üretilemedi.', 'err');
    } finally {
      setBusy('');
    }
  };

  const handleUploadRef = async file => {
    if (!file) return;
    setBusy('upload_ref');
    try {
      const assetId = await uploadImage(file);
      setIngDraft(prev => ({ ...prev, references: [...(prev.references || []), assetId] }));
      addToast('Referans görsel eklendi. Kaydetmeyi unutmayın.', 'ok');
    } catch (err) {
      addToast(err.message || 'Görsel yüklenemedi.', 'err');
    } finally {
      setBusy('');
    }
  };

  const handleStyleDemo = async styleId => {
    setBusy(`demo_${styleId}`);
    try {
      await apiJson(`${API}/styles/${styleId}/demo-scenes?mode=${demoMode}`, { method: 'POST' });
      await refreshLibrary();
      addToast('20 sn stil demosu üretim kuyruğuna alındı.', 'ok');
    } catch (err) {
      addToast(err.detail || err.message || 'Demo başlatılamadı.', 'err');
    } finally {
      setBusy('');
    }
  };

  const handleCopyStyleProject = async styleId => {
    setBusy(`copy_${styleId}`);
    try {
      const created = await apiJson(`${API}/styles/${styleId}/example-project?language=${styleLang}`, { method: 'POST' });
      await refreshLibrary();
      addToast('Örnek proje oluşturuldu!', 'ok');
      navigate(`/episodes/${created.id}`);
    } catch (err) {
      addToast(err.detail || err.message || 'Örnek proje kopyalanamadı.', 'err');
    } finally {
      setBusy('');
    }
  };

  const handleInstallVoice = async id => {
    setInstallingVoice(id);
    try {
      await apiJson(`${API}/voices/${id}/install`, { method: 'POST' });
      await refreshCatalog();
      addToast('Ses indirildi ve kullanıma hazır.', 'ok');
    } catch (err) {
      addToast(err.detail || err.message || 'Ses indirilemedi.', 'err');
    } finally {
      setInstallingVoice('');
    }
  };

  const selectedTplRow = library.template.find(t => t.id === selectedTplId) || null;
  const handleSaveTemplate = async () => {
    if (!tplDraft.name.trim() || !tplDraft.body.trim()) {
      addToast('Şablon adı ve içeriği gerekli.', 'err');
      return;
    }
    setBusy('save_tpl');
    try {
      const saved = await saveDoc('template', tplDraft, selectedTplRow);
      setSelectedTplId(saved.id);
      setTplDraft(saved.data);
      addToast('Şablon kaydedildi.', 'ok');
    } catch (err) {
      addToast(err.detail || err.message || 'Şablon kaydedilemedi.', 'err');
    } finally {
      setBusy('');
    }
  };

  const filteredVoices = useMemo(
    () => voices.filter(v => voiceLangFilter === 'all' || v.language === voiceLangFilter),
    [voices, voiceLangFilter],
  );

  return (
    <div className="st-page">
      <div className="st-page-head">
        <div>
          <h1>Varlıklar &amp; Stüdyo Kütüphanesi</h1>
          <p className="st-muted">Karakterler, mekanlar, görsel stiller, sesler ve prompt şablonları.</p>
        </div>
      </div>

      <div className="st-subtabs">
        {ASSET_TABS.map(item => {
          const Icon = item.icon;
          return (
            <button key={item.id} type="button" className={tab === item.id ? 'active' : ''} onClick={() => setTab(item.id)}>
              <Icon size={15} />{item.label}
            </button>
          );
        })}
      </div>

      {/* TAB 1: BİLEŞENLER */}
      {tab === 'ingredients' && (
        <div className="st-split-view">
          <div className="st-split-list">
            <div className="st-row-between" style={{ marginBottom: 10 }}>
              <strong>Kayıtlı Bileşenler ({filteredIngredients.length})</strong>
              <button type="button" className="st-btn st-btn-sm st-btn-primary" onClick={handleNewIngredient}>
                <Plus size={13} />Yeni
              </button>
            </div>
            <div className="st-form-grid two" style={{ marginBottom: 10 }}>
              <select value={ingSeriesFilter} onChange={e => setIngSeriesFilter(e.target.value)}>
                <option value="all">Tüm diziler</option>
                {library.series.map(s => <option key={s.id} value={s.id}>{s.data.name}</option>)}
              </select>
              <select value={ingTypeFilter} onChange={e => setIngTypeFilter(e.target.value)}>
                <option value="all">Tüm türler</option>
                {Object.entries(INGREDIENT_TYPES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </div>
            <div className="st-stack-sm">
              {filteredIngredients.map(row => (
                <button
                  key={row.id}
                  type="button"
                  className={row.id === selectedIngId ? 'st-ing-item active' : 'st-ing-item'}
                  onClick={() => handleSelectIngredient(row)}
                >
                  {row.data.references?.[0] ? (
                    <img src={mediaUrl(row.data.references[0])} alt={row.data.name} />
                  ) : (
                    <span className="st-ing-ph"><Users size={16} /></span>
                  )}
                  <div>
                    <strong>{row.data.name}</strong>
                    <small>{INGREDIENT_TYPES[row.data.ingredient_type || 'character']}</small>
                  </div>
                </button>
              ))}
              {filteredIngredients.length === 0 && (
                <p className="st-muted" style={{ fontSize: 13 }}>Bu filtrede bileşen bulunamadı.</p>
              )}
            </div>
          </div>

          <div className="st-card">
            <div className="st-row-between" style={{ marginBottom: 14 }}>
              <h2 style={{ margin: 0 }}>{selectedIngRow ? `${selectedIngRow.data.name}` : 'Yeni Bileşen Oluştur'}</h2>
              <div className="st-actions" style={{ margin: 0 }}>
                <button type="button" className="st-btn st-btn-primary" disabled={Boolean(busy)} onClick={handleSaveIngredient}>
                  <Save size={14} />Kaydet
                </button>
                {selectedIngRow && (
                  <button
                    type="button"
                    className="st-btn st-btn-danger"
                    onClick={async () => {
                      const ok = await deleteDoc(selectedIngRow.id, selectedIngRow.data.name);
                      if (ok) handleNewIngredient();
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            </div>

            <div className="st-form-grid three">
              <label className="st-field">
                <span>Ad</span>
                <input value={ingDraft.name} onChange={e => setIngDraft(d => ({ ...d, name: e.target.value }))} placeholder="Örn: Barnaby" />
              </label>
              <label className="st-field">
                <span>Bileşen türü</span>
                <select value={ingDraft.ingredient_type || 'character'} onChange={e => setIngDraft(d => ({ ...d, ingredient_type: e.target.value }))}>
                  {Object.entries(INGREDIENT_TYPES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                </select>
              </label>
              <label className="st-field">
                <span>Görsel stil</span>
                <select value={ingDraft.style || 'clay_stopmotion'} onChange={e => setIngDraft(d => ({ ...d, style: e.target.value }))}>
                  {styles.map(st => <option key={st.id} value={st.id}>{st.name}</option>)}
                </select>
              </label>
            </div>

            <div className="st-form-grid two">
              <label className="st-field">
                <span>Karakter sesi</span>
                <div className="st-row-gap">
                  <select value={ingDraft.voice || ''} onChange={e => setIngDraft(d => ({ ...d, voice: e.target.value }))}>
                    <option value="">Varsayılan anlatıcı sesi</option>
                    {readyVoices.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                  </select>
                  {ingDraft.voice && (
                    <button
                      type="button"
                      className="st-icon-btn"
                      onClick={() => setPreviewVoice(previewVoice === ingDraft.voice ? '' : ingDraft.voice)}
                    >
                      <Volume2 size={14} />
                    </button>
                  )}
                </div>
              </label>
              <label className="st-field">
                <span>Tutarlılık tohumu</span>
                <div className="st-row-gap">
                  <input
                    type="number"
                    value={ingDraft.seed ?? 42}
                    onChange={e => setIngDraft(d => ({ ...d, seed: Number(e.target.value) || 0 }))}
                  />
                  <button
                    type="button"
                    className="st-icon-btn"
                    title="Rastgele sayı üret"
                    onClick={() => setIngDraft(d => ({ ...d, seed: Math.floor(100000 + Math.random() * 899999) }))}
                  >
                    <Dices size={14} />
                  </button>
                </div>
              </label>
            </div>

            {previewVoice && previewVoice === ingDraft.voice && (
              <audio controls autoPlay src={getApiUrl(`${API}/voices/${ingDraft.voice}/preview`)} style={{ width: '100%', height: 32, marginBottom: 10 }} />
            )}

            <label className="st-field">
              <span>Görsel görünüm tarifi (İngilizce veya Türkçe)</span>
              <textarea
                rows={3}
                value={ingDraft.description}
                onChange={e => setIngDraft(d => ({ ...d, description: e.target.value }))}
                placeholder="Kıyafet, saç, renk paleti, belirgin özellikler…"
              />
            </label>

            {library.series.length > 0 && (
              <div className="st-field">
                <span>Bağlı olduğu diziler</span>
                <div className="st-chips">
                  {library.series.map(s => {
                    const on = (ingDraft.series_ids || []).includes(s.id);
                    return (
                      <button
                        key={s.id}
                        type="button"
                        className={on ? 'st-btn st-btn-sm st-btn-primary' : 'st-btn st-btn-sm'}
                        onClick={() => setIngDraft(d => ({
                          ...d,
                          series_ids: on ? (d.series_ids || []).filter(x => x !== s.id) : [...(d.series_ids || []), s.id],
                        }))}
                      >
                        {on && <Check size={12} />}{s.data.name}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="st-field" style={{ marginTop: 12 }}>
              <div className="st-row-between" style={{ marginBottom: 8 }}>
                <span>Referans Görseller ({ingDraft.references?.length || 0})</span>
                <div className="st-actions" style={{ margin: 0 }}>
                  <button type="button" className="st-btn st-btn-sm st-btn-primary" disabled={Boolean(busy)} onClick={handleGenerateRef}>
                    {busy === 'gen_ref' ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                    AI Referans Üret
                  </button>
                  <label className="st-btn st-btn-sm">
                    <Upload size={13} />Görsel Yükle
                    <input type="file" accept="image/*" hidden onChange={e => handleUploadRef(e.target.files?.[0])} />
                  </label>
                </div>
              </div>
              {ingDraft.references?.length > 0 ? (
                <div className="st-ref-grid">
                  {ingDraft.references.map(refId => (
                    <div key={refId} className="st-ref-card">
                      <img src={mediaUrl(refId)} alt="Referans" />
                      <button
                        type="button"
                        className="st-ref-del"
                        onClick={() => setIngDraft(d => ({ ...d, references: d.references.filter(x => x !== refId) }))}
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="st-muted" style={{ fontSize: 12 }}>Henüz referans görsel yok. AI ile üretebilir veya dosya yükleyebilirsiniz.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: GÖRSEL STİLLER */}
      {tab === 'styles' && (
        <div className="st-stack">
          <div className="st-filter-bar">
            <div className="st-segmented">
              <button type="button" className={styleLang === 'tr' ? 'active' : ''} onClick={() => setStyleLang('tr')}>Türkçe Demo</button>
              <button type="button" className={styleLang === 'en' ? 'active' : ''} onClick={() => setStyleLang('en')}>English Demo</button>
            </div>
            <select value={demoMode} onChange={e => setDemoMode(e.target.value)} aria-label="Demo üretim modu">
              <option value="balanced">Demo Modu: Orta · Dengeli (FLUX.2 + FreeVideo)</option>
              <option value="ltxv">Demo Modu: Hızlı (FLUX.2 + LTX-Video)</option>
              <option value="video">Demo Modu: Yüksek (Qwen + FreeVideo)</option>
              <option value="still">Demo Modu: Görsel (Hareketsiz)</option>
            </select>
          </div>

          {activeStyleVideo && (
            <div className="st-card" style={{ marginBottom: 8 }}>
              <div className="st-row-between" style={{ marginBottom: 10 }}>
                <strong>{styles.find(s => s.id === activeStyleVideo)?.name} · 20 sn Canlı Demo ({styleLang.toUpperCase()})</strong>
                <button type="button" className="st-btn st-btn-sm" onClick={() => setActiveStyleVideo('')}>Kapat</button>
              </div>
              <video
                key={`${activeStyleVideo}-${styleLang}`}
                controls
                autoPlay
                playsInline
                style={{ width: '100%', maxHeight: 420, borderRadius: 12, background: '#000' }}
                src={getApiUrl(`${API}/styles/${activeStyleVideo}/example-video?language=${styleLang}`)}
              />
            </div>
          )}

          <div className="st-grid-cards">
            {styles.map(st => (
              <article key={st.id} className="st-media-card">
                <div className="st-media-thumb" onClick={() => setActiveStyleVideo(st.id)}>
                  <img src={getApiUrl(st.sample_url)} alt={st.name} />
                  <span className="st-thumb-badge">{st.subtitle}</span>
                  <span className="st-play-overlay"><Play size={22} /></span>
                </div>
                <div className="st-media-body">
                  <h3>{st.name}</h3>
                  <p>{st.summary}</p>
                  <div className="st-actions" style={{ margin: 'auto 0 0', paddingTop: 8 }}>
                    <button type="button" className="st-btn st-btn-sm st-btn-primary" onClick={() => setActiveStyleVideo(st.id)}>
                      <Play size={12} />20 sn İzle
                    </button>
                    <button type="button" className="st-btn st-btn-sm" disabled={Boolean(busy)} onClick={() => handleCopyStyleProject(st.id)}>
                      <Copy size={12} />Projeye Kopyala
                    </button>
                    <button type="button" className="st-btn st-btn-sm" disabled={Boolean(busy)} onClick={() => handleStyleDemo(st.id)}>
                      <Sparkles size={12} />Demo Üret
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      )}

      {/* TAB 3: SESLER */}
      {tab === 'voices' && (
        <div className="st-stack">
          <div className="st-filter-bar">
            <select value={voiceLangFilter} onChange={e => setVoiceLangFilter(e.target.value)}>
              <option value="all">Tüm diller ({voices.length})</option>
              {Object.entries(LANGUAGES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
            </select>
          </div>
          <div className="st-grid-cards">
            {filteredVoices.map(v => (
              <div key={v.id} className="st-card st-voice-card">
                <div className="st-row-between">
                  <strong>{v.name}</strong>
                  <span className={v.installed ? 'st-badge st-badge-ok' : 'st-badge'}>
                    {v.installed ? 'Kurulu' : 'Ücretsiz indirilebilir'}
                  </span>
                </div>
                <small className="st-muted">{LANGUAGES[v.language] || v.language} · {v.id}</small>
                <div className="st-actions" style={{ margin: '10px 0 0' }}>
                  {v.installed ? (
                    <button
                      type="button"
                      className="st-btn st-btn-sm"
                      onClick={() => setPreviewVoice(previewVoice === v.id ? '' : v.id)}
                    >
                      <Volume2 size={13} />Önizle
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="st-btn st-btn-sm st-btn-primary"
                      disabled={Boolean(installingVoice)}
                      onClick={() => handleInstallVoice(v.id)}
                    >
                      {installingVoice === v.id ? <Loader2 size={13} className="animate-spin" /> : <Download size={13} />}
                      Ücretsiz İndir
                    </button>
                  )}
                </div>
                {previewVoice === v.id && v.installed && (
                  <audio controls autoPlay src={getApiUrl(`${API}/voices/${v.id}/preview`)} style={{ width: '100%', height: 32, marginTop: 8 }} />
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 4: ŞABLONLAR */}
      {tab === 'templates' && (
        <div className="st-split-view">
          <div className="st-split-list">
            <div className="st-row-between" style={{ marginBottom: 10 }}>
              <strong>Prompt Şablonları ({library.template.length})</strong>
              <button type="button" className="st-btn st-btn-sm st-btn-primary" onClick={() => { setSelectedTplId(''); setTplDraft(emptyTemplate()); }}>
                <Plus size={13} />Yeni
              </button>
            </div>
            <div className="st-stack-sm">
              {library.template.map(row => (
                <button
                  key={row.id}
                  type="button"
                  className={row.id === selectedTplId ? 'st-list-row active' : 'st-list-row'}
                  onClick={() => { setSelectedTplId(row.id); setTplDraft(row.data); }}
                >
                  <strong>{row.data.name}</strong>
                  <small>{TEMPLATE_PURPOSES[row.data.purpose] || row.data.purpose}</small>
                </button>
              ))}
              {library.template.length === 0 && (
                <p className="st-muted" style={{ fontSize: 13 }}>Henüz özel şablon kaydedilmedi.</p>
              )}
            </div>
          </div>

          <div className="st-card">
            <div className="st-row-between" style={{ marginBottom: 14 }}>
              <h2 style={{ margin: 0 }}>{selectedTplRow ? selectedTplRow.data.name : 'Yeni Prompt Şablonu'}</h2>
              <div className="st-actions" style={{ margin: 0 }}>
                <button type="button" className="st-btn st-btn-primary" disabled={Boolean(busy)} onClick={handleSaveTemplate}>
                  <Save size={14} />Kaydet
                </button>
                {selectedTplRow && (
                  <button
                    type="button"
                    className="st-btn st-btn-danger"
                    onClick={async () => {
                      const ok = await deleteDoc(selectedTplRow.id, selectedTplRow.data.name);
                      if (ok) { setSelectedTplId(''); setTplDraft(emptyTemplate()); }
                    }}
                  >
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
            </div>
            <div className="st-form-grid two">
              <label className="st-field">
                <span>Şablon adı</span>
                <input value={tplDraft.name} onChange={e => setTplDraft(d => ({ ...d, name: e.target.value }))} />
              </label>
              <label className="st-field">
                <span>Kullanım alanı</span>
                <select value={tplDraft.purpose} onChange={e => setTplDraft(d => ({ ...d, purpose: e.target.value }))}>
                  {Object.entries(TEMPLATE_PURPOSES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
                </select>
              </label>
            </div>
            <label className="st-field">
              <span>Şablon metni</span>
              <textarea rows={8} value={tplDraft.body} onChange={e => setTplDraft(d => ({ ...d, body: e.target.value }))} />
            </label>
          </div>
        </div>
      )}
    </div>
  );
}
