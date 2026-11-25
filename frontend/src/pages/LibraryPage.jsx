import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { ExternalLink, Film, Play, Search, Trash2 } from 'lucide-react';
import { formatDate, jobFileUrl } from '../constants';
import { useStudio } from '../context/StudioContext';
import DeliveryTheater from '../components/DeliveryTheater';
import { EmptyState, SkeletonGrid } from '../components/ui/Primitives';

export default function LibraryPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { jobs, library, loading, deleteJob } = useStudio();

  const [query, setQuery] = useState('');
  const [seriesFilter, setSeriesFilter] = useState('all');
  const [ratioFilter, setRatioFilter] = useState('all');
  const [marathonIdx, setMarathonIdx] = useState(null);

  const selectedJobId = searchParams.get('job') || '';
  const setSelectedJobId = id => {
    const p = new URLSearchParams(searchParams);
    if (id) p.set('job', id);
    else p.delete('job');
    setSearchParams(p, { replace: true });
  };

  const completedVideos = useMemo(
    () => jobs.filter(j => j.status === 'completed' && j.result?.video),
    [jobs],
  );

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return completedVideos.filter(j => {
      if (seriesFilter !== 'all') {
        if (seriesFilter === 'standalone' && j.series_id) return false;
        if (seriesFilter !== 'standalone' && j.series_id !== seriesFilter) return false;
      }
      if (ratioFilter !== 'all' && (j.aspect_ratio || '9:16') !== ratioFilter) return false;
      if (q) {
        const hay = `${j.label || ''} ${j.series_name || ''}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [completedVideos, seriesFilter, ratioFilter, query]);

  const activeJob = completedVideos.find(j => j.id === selectedJobId) || null;

  if (loading) {
    return (
      <div className="st-page">
        <div className="st-page-head"><h1>Video Kütüphanesi</h1></div>
        <SkeletonGrid count={6} />
      </div>
    );
  }

  return (
    <div className="st-page">
      <div className="st-page-head">
        <div>
          <h1>Video Kütüphanesi</h1>
          <p className="st-muted">Tamamlanmış tüm bölümleriniz, indirme paketleriniz ve sosyal medya yayın metinleriniz.</p>
        </div>
        {filtered.length > 0 && (
          <button type="button" className="st-btn st-btn-primary" onClick={() => { setSelectedJobId(''); setMarathonIdx(0); }}>
            <Play size={15} />Maraton İzle ({filtered.length})
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="st-filter-bar">
        <div className="st-search">
          <Search size={15} />
          <input placeholder="Video veya dizi ara…" value={query} onChange={e => setQuery(e.target.value)} />
        </div>
        <select value={seriesFilter} onChange={e => setSeriesFilter(e.target.value)} aria-label="Dizi filtresi">
          <option value="all">Tüm yapımlar ({completedVideos.length})</option>
          {library.series.map(s => (
            <option key={s.id} value={s.id}>{s.data.name}</option>
          ))}
          <option value="standalone">Bağımsız videolar</option>
        </select>
        <select value={ratioFilter} onChange={e => setRatioFilter(e.target.value)} aria-label="Format filtresi">
          <option value="all">Tüm formatlar</option>
          <option value="9:16">9:16 Dikey</option>
          <option value="16:9">16:9 Yatay (1080p)</option>
          <option value="16:9-480p">16:9 · 480p Dizi</option>
          <option value="1:1">1:1 Kare</option>
        </select>
      </div>

      {/* Marathon Player */}
      {marathonIdx !== null && filtered[marathonIdx] && (
        <section className="st-card st-marathon" style={{ marginBottom: 20 }}>
          <div className="st-row-between" style={{ marginBottom: 12 }}>
            <div>
              <span className="st-kicker">MARATON OYNATICI · {marathonIdx + 1}/{filtered.length}</span>
              <h3 style={{ margin: '2px 0 0' }}>{filtered[marathonIdx].label}</h3>
            </div>
            <button type="button" className="st-btn st-btn-sm" onClick={() => setMarathonIdx(null)}>Kapat</button>
          </div>
          <div className="st-marathon-grid">
            <video
              key={filtered[marathonIdx].id}
              controls
              autoPlay
              playsInline
              src={jobFileUrl(filtered[marathonIdx].id, 'final.mp4')}
              onEnded={() => {
                if (marathonIdx + 1 < filtered.length) setMarathonIdx(marathonIdx + 1);
              }}
            />
            <div className="st-marathon-list">
              {filtered.map((item, idx) => (
                <button
                  key={item.id}
                  type="button"
                  className={idx === marathonIdx ? 'st-list-row active' : 'st-list-row'}
                  onClick={() => setMarathonIdx(idx)}
                >
                  <strong>{item.label}</strong>
                  <small>{item.result?.duration ? `${Number(item.result.duration).toFixed(0)} sn` : ''}</small>
                </button>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Selected Delivery Theater */}
      {activeJob && (
        <div style={{ marginBottom: 22 }}>
          <DeliveryTheater
            job={activeJob}
            projectName={activeJob.label}
            aspectRatio={activeJob.aspect_ratio}
            onClose={() => setSelectedJobId('')}
          />
        </div>
      )}

      {filtered.length === 0 ? (
        <EmptyState
          icon={<Film size={32} />}
          title="Henüz hazır video yok"
          body="Bir bölümün final kurgusunu tamamladığınızda burada izleyebilir, indirebilir ve yayın paketini oluşturabilirsiniz."
          action={<button type="button" className="st-btn st-btn-primary" onClick={() => navigate('/series')}>Dizilere Git</button>}
        />
      ) : (
        <div className="st-grid-cards">
          {filtered.map(j => (
            <article
              key={j.id}
              className={j.id === selectedJobId ? 'st-media-card selected' : 'st-media-card'}
              onClick={() => { setMarathonIdx(null); setSelectedJobId(j.id); }}
            >
              <div className="st-media-thumb">
                <video muted playsInline preload="metadata" src={`${jobFileUrl(j.id, 'final.mp4')}#t=0.5`} />
                <span className="st-thumb-badge">
                  {j.result?.duration ? `${Number(j.result.duration).toFixed(0)} sn · ` : ''}{j.aspect_ratio || '9:16'}
                </span>
                <span className="st-play-overlay"><Play size={22} /></span>
              </div>
              <div className="st-media-body">
                <h3>{j.label || 'Tamamlanan Video'}</h3>
                <p>{[j.series_name, formatDate(j.updated || j.created_at)].filter(Boolean).join(' · ')}</p>
                <div className="st-row-between" style={{ marginTop: 'auto', paddingTop: 6 }}>
                  {j.project_id ? (
                    <button
                      type="button"
                      className="st-btn st-btn-sm"
                      onClick={e => { e.stopPropagation(); navigate(`/episodes/${j.project_id}`); }}
                    >
                      <ExternalLink size={12} />Bölümü aç
                    </button>
                  ) : <span />}
                  <button
                    type="button"
                    className="st-icon-btn"
                    title="Üretim kaydını sil"
                    onClick={e => { e.stopPropagation(); deleteJob(j.id); }}
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
