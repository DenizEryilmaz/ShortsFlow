import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft, BookOpen, Clapperboard, Film, Loader2, Play, Plus, Sparkles, Users, Volume2,
} from 'lucide-react';
import { apiJson, getApiUrl } from '../api';
import {
  API, ASPECT_RATIOS, BGM_PRESETS, CAPTION_STYLES, INGREDIENT_TYPES, jobFileUrl, LANGUAGES, mediaUrl, requestJson, TRANSITIONS,
} from '../constants';
import { useStudio } from '../context/StudioContext';
import { EmptyState, QualityPicker } from '../components/ui/Primitives';

export default function SeriesHubPage() {
  const { seriesId } = useParams();
  const navigate = useNavigate();
  const {
    library, styles, models, latestVideoByProject, activeJobByProject,
    saveDoc, produceJob, refreshLibrary, addToast,
  } = useStudio();

  const [tab, setTab] = useState('episodes');
  const [busy, setBusy] = useState(false);
  const [marathonIdx, setMarathonIdx] = useState(null);
  const [previewVoice, setPreviewVoice] = useState('');
  const [bible, setBible] = useState(null);
  const [saveState, setSaveState] = useState('');

  const seriesRow = library.series.find(s => s.id === seriesId);

  useEffect(() => {
    if (seriesRow) setBible(seriesRow.data);
  }, [seriesRow?.id, seriesRow?.revision]);

  const episodes = useMemo(
    () => library.project
      .filter(p => p.data.series_id === seriesId)
      .sort((a, b) => (a.data.episode || 0) - (b.data.episode || 0)),
    [library.project, seriesId],
  );

  const cast = useMemo(
    () => library.character.filter(c => (c.data.series_ids || []).includes(seriesId) || (seriesRow?.data?.character_ids || []).includes(c.id)),
    [library.character, seriesId, seriesRow],
  );

  const completedEpisodes = useMemo(
    () => episodes.filter(ep => Boolean(latestVideoByProject[ep.id])).map(ep => ({ ep, job: latestVideoByProject[ep.id] })),
    [episodes, latestVideoByProject],
  );

  if (!seriesRow || !bible) {
    return (
      <div className="st-page">
        <EmptyState
          icon={<Clapperboard size={28} />}
          title="Dizi bulunamadı"
          action={<button type="button" className="st-btn" onClick={() => navigate('/series')}>Dizilere dön</button>}
        />
      </div>
    );
  }

  const updateBible = async patch => {
    const next = { ...bible, ...patch };
    setBible(next);
    setSaveState('Kaydediliyor…');
    try {
      await saveDoc('series', next, seriesRow);
      setSaveState('Kaydedildi');
    } catch (err) {
      setSaveState('');
      addToast(err.detail || err.message || 'Kaydedilemedi.', 'err');
    }
  };

  const addEpisode = async () => {
    setBusy(true);
    try {
      const created = await apiJson(`${API}/series/${seriesId}/episodes`, requestJson('POST', {}));
      await refreshLibrary();
      addToast(`${created.data.name} eklendi (dizi ayarları miras alındı).`, 'ok');
      navigate(`/series/${seriesId}/episodes/${created.id}`);
    } catch (err) {
      addToast(err.detail || err.message || 'Bölüm eklenemedi.', 'err');
    } finally {
      setBusy(false);
    }
  };

  const renderAllRemaining = async () => {
    setBusy(true);
    try {
      const res = await apiJson(`${API}/series/${seriesId}/render-all`, { method: 'POST' });
      await refreshLibrary();
      addToast(res.count > 0 ? `${res.count} bölüm üretim kuyruğuna eklendi.` : 'Üretilecek eksik bölüm yok.', res.count > 0 ? 'ok' : 'info');
    } catch (err) {
      addToast(err.detail || err.message || 'Toplu üretim başlatılamadı.', 'err');
    } finally {
      setBusy(false);
    }
  };

  const toggleCastMember = async charRow => {
    const inSeries = (charRow.data.series_ids || []).includes(seriesId);
    const nextSeriesIds = inSeries
      ? (charRow.data.series_ids || []).filter(id => id !== seriesId)
      : [...(charRow.data.series_ids || []), seriesId];
    const nextBibleCids = inSeries
      ? (bible.character_ids || []).filter(id => id !== charRow.id)
      : Array.from(new Set([...(bible.character_ids || []), charRow.id]));
    await saveDoc('character', { ...charRow.data, series_ids: nextSeriesIds }, charRow);
    await updateBible({ character_ids: nextBibleCids });
  };

  const styleMeta = styles.find(s => s.id === bible.style);
  const doneCount = completedEpisodes.length;
  const pct = episodes.length ? Math.round((doneCount / episodes.length) * 100) : 0;

  return (
    <div className="st-page">
      <div className="st-breadcrumb">
        <button type="button" className="st-btn st-btn-sm" onClick={() => navigate('/series')}>
          <ArrowLeft size={14} />Diziler
        </button>
        {saveState && <span className="st-muted" style={{ fontSize: 12 }}>{saveState}</span>}
      </div>

      <section className="st-hero">
        <div className="st-hero-cover">
          {bible.cover_asset ? (
            <img src={mediaUrl(bible.cover_asset)} alt={bible.name} />
          ) : styleMeta?.sample_url ? (
            <img src={getApiUrl(styleMeta.sample_url)} alt={bible.name} />
          ) : (
            <Clapperboard size={40} />
          )}
        </div>
        <div className="st-hero-info">
          <div className="st-chips">
            <span className="st-badge st-badge-accent">{styleMeta?.name || bible.style}</span>
            <span className="st-badge">{LANGUAGES[bible.defaults?.language || 'tr']}</span>
            <span className="st-badge">{bible.defaults?.aspect_ratio || '9:16'}</span>
            <span className="st-badge st-badge-ok">{doneCount}/{episodes.length} bölüm hazır (%{pct})</span>
          </div>
          <h1>{bible.name}</h1>
          <p>{bible.logline || 'Bu dizi için henüz özet yazılmadı.'}</p>
          <div className="st-mini-bar" style={{ maxWidth: 360 }}>
            <div style={{ width: `${pct}%` }} />
          </div>
          <div className="st-actions" style={{ margin: '14px 0 0' }}>
            <button type="button" className="st-btn st-btn-primary" disabled={busy} onClick={addEpisode}>
              <Plus size={15} />Yeni Bölüm Ekle
            </button>
            {doneCount < episodes.length && (
              <button type="button" className="st-btn" disabled={busy} onClick={renderAllRemaining}>
                <Sparkles size={15} />Kalan Tüm Bölümleri Üret ({episodes.length - doneCount})
              </button>
            )}
            {completedEpisodes.length > 0 && (
              <button type="button" className="st-btn" onClick={() => setMarathonIdx(0)}>
                <Play size={15} />Maraton İzle ({completedEpisodes.length})
              </button>
            )}
          </div>
        </div>
      </section>

      {marathonIdx !== null && completedEpisodes[marathonIdx] && (
        <section className="st-card st-marathon">
          <div className="st-row-between" style={{ marginBottom: 12 }}>
            <div>
              <span className="st-kicker">MARATON OYNATICI · {marathonIdx + 1}/{completedEpisodes.length}</span>
              <h3 style={{ margin: '2px 0 0' }}>{completedEpisodes[marathonIdx].ep.data.name}</h3>
            </div>
            <button type="button" className="st-btn st-btn-sm" onClick={() => setMarathonIdx(null)}>Kapat</button>
          </div>
          <div className="st-marathon-grid">
            <video
              key={completedEpisodes[marathonIdx].job.id}
              controls
              autoPlay
              playsInline
              src={jobFileUrl(completedEpisodes[marathonIdx].job.id, 'final.mp4')}
              onEnded={() => {
                if (marathonIdx + 1 < completedEpisodes.length) setMarathonIdx(marathonIdx + 1);
              }}
            />
            <div className="st-marathon-list">
              {completedEpisodes.map((entry, idx) => (
                <button
                  key={entry.ep.id}
                  type="button"
                  className={idx === marathonIdx ? 'st-list-row active' : 'st-list-row'}
                  onClick={() => setMarathonIdx(idx)}
                >
                  <strong>{entry.ep.data.episode}. {entry.ep.data.name}</strong>
                  <small>{Number(entry.job.result?.duration || entry.ep.data.duration).toFixed(0)} sn</small>
                </button>
              ))}
            </div>
          </div>
        </section>
      )}

      <div className="st-subtabs">
        <button type="button" className={tab === 'episodes' ? 'active' : ''} onClick={() => setTab('episodes')}>
          <Film size={15} />Bölümler ({episodes.length})
        </button>
        <button type="button" className={tab === 'cast' ? 'active' : ''} onClick={() => setTab('cast')}>
          <Users size={15} />Kadro ({cast.length})
        </button>
        <button type="button" className={tab === 'bible' ? 'active' : ''} onClick={() => setTab('bible')}>
          <BookOpen size={15} />Dizi Kitabı
        </button>
      </div>

      {tab === 'episodes' && (
        <div className="st-grid-cards">
          {episodes.map(ep => {
            const thumb = ep.data.script?.scenes?.find(s => s.first_asset)?.first_asset;
            const videoJob = latestVideoByProject[ep.id];
            const activeJob = activeJobByProject[ep.id];
            const scenesCount = ep.data.script?.scenes?.length || 0;
            return (
              <article key={ep.id} className="st-media-card" onClick={() => navigate(`/series/${seriesId}/episodes/${ep.id}`)}>
                <div className="st-media-thumb">
                  {thumb ? <img src={mediaUrl(thumb)} alt={ep.data.name} /> : <Film size={28} />}
                  <span className="st-thumb-badge">Bölüm {ep.data.episode} · {ep.data.duration} sn</span>
                  {activeJob && <span className="st-thumb-live">{activeJob.status === 'running' ? 'Üretiliyor' : 'Sırada'}</span>}
                  {videoJob && <span className="st-play-overlay"><Play size={20} /></span>}
                </div>
                <div className="st-media-body">
                  <h3>{ep.data.name}</h3>
                  <p>{ep.data.script?.logline || ep.data.brief || `${scenesCount} sahne`}</p>
                  <div className="st-row-between" style={{ marginTop: 'auto', paddingTop: 6 }}>
                    <span className={videoJob ? 'st-badge st-badge-ok' : activeJob ? 'st-badge st-badge-accent' : 'st-badge'}>
                      {videoJob ? 'Hazır' : activeJob ? (activeJob.status === 'running' ? 'Üretiliyor' : 'Kuyrukta') : scenesCount ? 'Senaryo hazır' : 'Taslak'}
                    </span>
                    <div className="st-actions" style={{ margin: 0, gap: 6 }}>
                      {videoJob ? (
                        <button
                          type="button"
                          className="st-btn st-btn-sm st-btn-primary"
                          onClick={e => { e.stopPropagation(); navigate(`/series/${seriesId}/episodes/${ep.id}?step=deliver`); }}
                        >
                          <Play size={12} />İzle
                        </button>
                      ) : !activeJob && (
                        <button
                          type="button"
                          className="st-btn st-btn-sm"
                          onClick={e => { e.stopPropagation(); produceJob(ep.id, scenesCount ? 'render' : 'full'); }}
                        >
                          {busy ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}Üret
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}

      {tab === 'cast' && (
        <section className="st-section">
          <div className="st-section-head">
            <div>
              <h2>Dizi Kadrosu (Karakterler · Mekanlar · Objeler)</h2>
              <p className="st-muted" style={{ fontSize: 13, margin: '4px 0 0' }}>Bu diziye bağlı bileşenler yeni açılan tüm bölümlere otomatik eklenir.</p>
            </div>
            <button type="button" className="st-btn st-btn-primary" onClick={() => navigate(`/assets?tab=ingredients&series=${seriesId}`)}>
              <Plus size={15} />Yeni Bileşen Ekle
            </button>
          </div>
          <div className="st-grid-cards">
            {cast.map(c => {
              const epCount = episodes.filter(ep => (ep.data.character_ids || []).includes(c.id)).length;
              return (
                <article key={c.id} className="st-media-card" onClick={() => navigate(`/assets?tab=ingredients&id=${c.id}`)}>
                  <div className="st-media-thumb">
                    {c.data.references?.[0] ? <img src={mediaUrl(c.data.references[0])} alt={c.data.name} /> : <Users size={28} />}
                    <span className="st-thumb-badge">{INGREDIENT_TYPES[c.data.ingredient_type || 'character']}</span>
                  </div>
                  <div className="st-media-body">
                    <h3>{c.data.name}</h3>
                    <p>{c.data.description}</p>
                    <div className="st-row-between" style={{ marginTop: 'auto', paddingTop: 6 }}>
                      <small>{epCount} bölümde yer alıyor</small>
                      {c.data.voice && (
                        <button
                          type="button"
                          className="st-btn st-btn-sm"
                          onClick={e => { e.stopPropagation(); setPreviewVoice(previewVoice === c.data.voice ? '' : c.data.voice); }}
                        >
                          <Volume2 size={13} />Ses
                        </button>
                      )}
                    </div>
                    {previewVoice === c.data.voice && c.data.voice && (
                      <audio controls autoPlay src={getApiUrl(`${API}/voices/${c.data.voice}/preview`)} onClick={e => e.stopPropagation()} style={{ width: '100%', height: 32, marginTop: 6 }} />
                    )}
                  </div>
                </article>
              );
            })}
          </div>

          {library.character.length > cast.length && (
            <div className="st-card" style={{ marginTop: 18 }}>
              <h3 style={{ margin: '0 0 10px', fontSize: 15 }}>Diğer kütüphane bileşenlerini bu diziye bağla</h3>
              <div className="st-chips">
                {library.character.filter(c => !cast.some(x => x.id === c.id)).map(c => (
                  <button key={c.id} type="button" className="st-btn st-btn-sm" onClick={() => toggleCastMember(c)}>
                    <Plus size={12} />{c.data.name} ({INGREDIENT_TYPES[c.data.ingredient_type || 'character']})
                  </button>
                ))}
              </div>
            </div>
          )}
        </section>
      )}

      {tab === 'bible' && (
        <section className="st-card">
          <h2 style={{ margin: '0 0 14px' }}>Dizi Kitabı &amp; Ortak Varsayılanlar</h2>
          <div className="st-form-grid two">
            <label className="st-field">
              <span>Dizi adı</span>
              <input value={bible.name} onChange={e => updateBible({ name: e.target.value })} />
            </label>
            <label className="st-field">
              <span>Görsel stil</span>
              <select value={bible.style} onChange={e => updateBible({ style: e.target.value })}>
                {styles.map(st => <option key={st.id} value={st.id}>{st.name}</option>)}
              </select>
            </label>
          </div>
          <label className="st-field">
            <span>Dizi özeti (Logline)</span>
            <textarea rows={2} value={bible.logline} onChange={e => updateBible({ logline: e.target.value })} />
          </label>
          <label className="st-field">
            <span>Devamlılık kuralları</span>
            <textarea rows={3} value={bible.continuity_note} onChange={e => updateBible({ continuity_note: e.target.value })} />
          </label>
          <div style={{ margin: '14px 0' }}>
            <span className="st-field-label">Varsayılan kalite profili</span>
            <QualityPicker
              image={bible.defaults?.image}
              video={bible.defaults?.video}
              onChange={(image, video) => updateBible({ defaults: { ...bible.defaults, image, video } })}
            />
          </div>
          <div className="st-form-grid three">
            <label className="st-field">
              <span>Format</span>
              <select
                value={bible.defaults?.aspect_ratio || '9:16'}
                onChange={e => {
                  const ratio = e.target.value;
                  const spec = ASPECT_RATIOS[ratio];
                  updateBible({ defaults: { ...bible.defaults, aspect_ratio: ratio, width: spec.width, height: spec.height } });
                }}
              >
                {Object.entries(ASPECT_RATIOS).map(([id, spec]) => <option key={id} value={id}>{spec.label}</option>)}
              </select>
            </label>
            <label className="st-field">
              <span>Dil</span>
              <select value={bible.defaults?.language || 'tr'} onChange={e => updateBible({ defaults: { ...bible.defaults, language: e.target.value } })}>
                {Object.entries(LANGUAGES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </label>
            <label className="st-field">
              <span>Anlatıcı sesi</span>
              <select value={bible.defaults?.voice || ''} onChange={e => updateBible({ defaults: { ...bible.defaults, voice: e.target.value } })}>
                {models.filter(m => m.kind === 'voice').map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
              </select>
            </label>
          </div>
          <div className="st-form-grid three">
            <label className="st-field">
              <span>Sahne geçişi</span>
              <select value={bible.defaults?.transition || 'crossfade'} onChange={e => updateBible({ defaults: { ...bible.defaults, transition: e.target.value } })}>
                {Object.entries(TRANSITIONS).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </label>
            <label className="st-field">
              <span>Altyazı stili</span>
              <select value={bible.defaults?.caption_style || 'shorts'} onChange={e => updateBible({ defaults: { ...bible.defaults, caption_style: e.target.value } })}>
                {Object.entries(CAPTION_STYLES).map(([id, label]) => <option key={id} value={id}>{label}</option>)}
              </select>
            </label>
            <label className="st-field">
              <span>Arka plan müziği</span>
              <select value={bible.defaults?.bgm_preset || ''} onChange={e => updateBible({ defaults: { ...bible.defaults, bgm_preset: e.target.value } })}>
                {BGM_PRESETS.filter(b => b.id !== 'custom').map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
              </select>
            </label>
          </div>
        </section>
      )}
    </div>
  );
}
