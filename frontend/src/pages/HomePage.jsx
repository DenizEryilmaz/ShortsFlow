import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle, ArrowRight, Clapperboard, Film, Loader2, Palette, Play, Plus, Sparkles,
} from 'lucide-react';
import { formatDate, formatEta, JOB_LABELS, mediaUrl } from '../constants';
import { useStudio } from '../context/StudioContext';
import { EmptyState, SkeletonGrid } from '../components/ui/Primitives';

export default function HomePage() {
  const navigate = useNavigate();
  const {
    library, jobs, styles, system, loading, latestVideoByProject, startService, setQueueOpen,
  } = useStudio();

  const offlineServices = (system?.services || []).filter(s => s.id !== 'worker' && !s.ready);
  const runningJob = jobs.find(j => j.status === 'running');
  const queuedCount = jobs.filter(j => j.status === 'queued').length;
  const recentVideos = useMemo(
    () => jobs.filter(j => j.status === 'completed' && j.result?.video).slice(0, 6),
    [jobs],
  );
  const recentProjects = useMemo(() => library.project.slice(0, 4), [library.project]);

  const seriesCover = seriesRow => {
    if (seriesRow.data.cover_asset) return mediaUrl(seriesRow.data.cover_asset);
    const eps = library.project.filter(p => p.data.series_id === seriesRow.id);
    for (const ep of eps) {
      const first = ep.data.script?.scenes?.find(s => s.first_asset)?.first_asset;
      if (first) return mediaUrl(first);
    }
    const style = styles.find(s => s.id === seriesRow.data.style);
    return style?.sample_url || '';
  };

  return (
    <div className="st-page">
      <header className="st-page-head">
        <div>
          <span className="st-kicker">ANA SAYFA</span>
          <h1>Stüdyo Özeti</h1>
        </div>
        <div className="st-actions" style={{ margin: 0 }}>
          <button type="button" className="st-btn" onClick={() => navigate('/assets?tab=styles')}>
            <Palette size={15} />Stil Örnekleri
          </button>
          <button type="button" className="st-btn st-btn-primary" onClick={() => navigate('/new')}>
            <Plus size={15} />Yeni Dizi / Video
          </button>
        </div>
      </header>

      {offlineServices.length > 0 && (
        <div className="st-alert-bar">
          <div className="st-row" style={{ gap: 10 }}>
            <AlertTriangle size={18} />
            <div>
              <strong>Bazı yerel motorlar kapalı:</strong>{' '}
              <span>{offlineServices.map(s => s.name).join(', ')}</span>
            </div>
          </div>
          <div className="st-actions" style={{ margin: 0 }}>
            {offlineServices.filter(s => s.can_start).map(s => (
              <button key={s.id} type="button" className="st-btn st-btn-sm st-btn-primary" onClick={() => startService(s.id)}>
                {s.id === 'comfyui' ? 'ComfyUI Başlat' : 'Ollama Başlat'}
              </button>
            ))}
            <button type="button" className="st-btn st-btn-sm" onClick={() => navigate('/system')}>Sistem</button>
          </div>
        </div>
      )}

      <section className="st-quick-grid">
        <button type="button" className="st-quick-card primary" onClick={() => navigate('/new?type=series')}>
          <span className="st-quick-icon"><Clapperboard size={22} /></span>
          <div>
            <strong>Yeni Dizi Başlat</strong>
            <small>5 adımlı sihirbazla çok bölümlü dizi, kadro ve senaryolar oluştur</small>
          </div>
          <ArrowRight size={16} />
        </button>
        <button type="button" className="st-quick-card" onClick={() => navigate('/new?type=single')}>
          <span className="st-quick-icon"><Film size={22} /></span>
          <div>
            <strong>Tek Video Üret</strong>
            <small>Hızlı Shorts, Reels veya YouTube anlatım videosu hazırla</small>
          </div>
          <ArrowRight size={16} />
        </button>
        <button type="button" className="st-quick-card" onClick={() => navigate('/assets?tab=styles')}>
          <span className="st-quick-icon"><Sparkles size={22} /></span>
          <div>
            <strong>Stil Örneğinden Başla</strong>
            <small>8 görsel stilin 20 sn TR/EN demolarını izle ve projeye al</small>
          </div>
          <ArrowRight size={16} />
        </button>
      </section>

      {runningJob && (
        <section className="st-card st-spotlight">
          <div className="st-row-between">
            <div className="st-row" style={{ gap: 10 }}>
              <Loader2 size={18} className="animate-spin st-accent-text" />
              <div>
                <span className="st-kicker">ŞU AN ÜRETİLİYOR</span>
                <h2 style={{ margin: '2px 0 0', fontSize: 17 }}>{runningJob.label || JOB_LABELS[runningJob.kind]}</h2>
              </div>
            </div>
            <div className="st-actions" style={{ margin: 0 }}>
              <span className="st-badge st-badge-accent">{formatEta(runningJob.estimate_seconds)}</span>
              {queuedCount > 0 && <span className="st-badge">+{queuedCount} kuyrukta</span>}
              <button type="button" className="st-btn st-btn-sm" onClick={() => setQueueOpen(true)}>Kuyruğu aç</button>
            </div>
          </div>
          <p className="st-muted" style={{ margin: '10px 0 0', fontSize: 13 }}>{runningJob.latest_event || 'Hazırlanıyor…'}</p>
        </section>
      )}

      {library.series.length > 0 && (
        <section className="st-section">
          <div className="st-section-head">
            <h2>Dizilerin</h2>
            <button type="button" className="st-btn st-btn-sm" onClick={() => navigate('/series')}>Tümünü gör</button>
          </div>
          <div className="st-grid-cards">
            {library.series.slice(0, 4).map(s => {
              const eps = library.project.filter(p => p.data.series_id === s.id);
              const done = eps.filter(p => Boolean(latestVideoByProject[p.id])).length;
              const cover = seriesCover(s);
              return (
                <article key={s.id} className="st-media-card" onClick={() => navigate(`/series/${s.id}`)}>
                  <div className="st-media-thumb">
                    {cover ? <img src={cover} alt={s.data.name} /> : <Film size={28} />}
                    <span className="st-thumb-badge">{done}/{eps.length} hazır</span>
                  </div>
                  <div className="st-media-body">
                    <h3>{s.data.name}</h3>
                    <p>{s.data.logline || `${eps.length} bölüm`}</p>
                    <div className="st-mini-bar">
                      <div style={{ width: `${eps.length ? Math.round((done / eps.length) * 100) : 0}%` }} />
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      )}

      <section className="st-section">
        <div className="st-section-head">
          <h2>Yeni Tamamlanan Videolar</h2>
          <button type="button" className="st-btn st-btn-sm" onClick={() => navigate('/library')}>Kütüphaneye git</button>
        </div>
        {loading ? <SkeletonGrid count={3} /> : recentVideos.length > 0 ? (
          <div className="st-grid-cards">
            {recentVideos.map(item => {
              const proj = library.project.find(p => p.id === item.project_id);
              const firstAsset = proj?.data?.script?.scenes?.find(s => s.first_asset)?.first_asset;
              return (
                <article key={item.id} className="st-media-card" onClick={() => navigate(`/library?job=${item.id}`)}>
                  <div className="st-media-thumb">
                    {firstAsset ? <img src={mediaUrl(firstAsset)} alt={item.label} /> : <Film size={28} />}
                    <span className="st-play-overlay"><Play size={22} /></span>
                    {item.result?.duration && <span className="st-thumb-badge">{Number(item.result.duration).toFixed(0)} sn</span>}
                  </div>
                  <div className="st-media-body">
                    <h3>{item.label || 'Video'}</h3>
                    <small>{formatDate(item.updated)} · {item.aspect_ratio || '9:16'}</small>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <EmptyState
            icon={<Film size={28} />}
            title="Henüz tamamlanmış video yok"
            description="Yeni bir dizi veya tek video başlatarak ilk filminizi üretin."
            action={<button type="button" className="st-btn st-btn-primary" onClick={() => navigate('/new')}><Plus size={15} />İlk Videonu Oluştur</button>}
          />
        )}
      </section>

      {recentProjects.length > 0 && (
        <section className="st-section">
          <div className="st-section-head">
            <h2>Kaldığın Yerden Devam Et</h2>
          </div>
          <div className="st-list-rows">
            {recentProjects.map(p => {
              const hasVideo = Boolean(latestVideoByProject[p.id]);
              return (
                <button
                  key={p.id}
                  type="button"
                  className="st-list-row"
                  onClick={() => navigate(p.data.series_id ? `/series/${p.data.series_id}/episodes/${p.id}` : `/episodes/${p.id}`)}
                >
                  <div>
                    <strong>{p.data.name}</strong>
                    <small>{p.data.series ? `${p.data.series} · ` : ''}{p.data.script?.scenes?.length || 0} sahne · {formatDate(p.updated)}</small>
                  </div>
                  <span className={hasVideo ? 'st-badge st-badge-ok' : 'st-badge'}>{hasVideo ? 'Video hazır' : 'Taslak'}</span>
                </button>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
