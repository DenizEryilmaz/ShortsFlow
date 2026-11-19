import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clapperboard, Film, Play, Plus, Search, Trash2 } from 'lucide-react';
import { formatDate, mediaUrl } from '../constants';
import { useStudio } from '../context/StudioContext';
import { EmptyState, SkeletonGrid } from '../components/ui/Primitives';

export default function SeriesListPage() {
  const navigate = useNavigate();
  const { library, styles, loading, latestVideoByProject, activeJobByProject, deleteDoc } = useStudio();
  const [query, setQuery] = useState('');

  const q = query.trim().toLowerCase();

  const filteredSeries = useMemo(
    () => library.series.filter(s => !q || s.data.name.toLowerCase().includes(q) || (s.data.logline || '').toLowerCase().includes(q)),
    [library.series, q],
  );

  const standaloneProjects = useMemo(
    () => library.project.filter(p => !p.data.series_id && (!q || p.data.name.toLowerCase().includes(q) || (p.data.brief || '').toLowerCase().includes(q))),
    [library.project, q],
  );

  const getSeriesCover = seriesRow => {
    if (seriesRow.data.cover_asset) return mediaUrl(seriesRow.data.cover_asset);
    const eps = library.project.filter(p => p.data.series_id === seriesRow.id);
    for (const ep of eps) {
      const first = ep.data.script?.scenes?.find(s => s.first_asset)?.first_asset;
      if (first) return mediaUrl(first);
    }
    const st = styles.find(s => s.id === seriesRow.data.style);
    return st?.sample_url || '';
  };

  return (
    <div className="st-page">
      <header className="st-page-head">
        <div>
          <span className="st-kicker">PRODÜKSİYONLAR</span>
          <h1>Diziler &amp; Projeler</h1>
        </div>
        <div className="st-actions" style={{ margin: 0 }}>
          <div className="st-search">
            <Search size={15} />
            <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Dizi veya bölüm ara…" />
          </div>
          <button type="button" className="st-btn st-btn-primary" onClick={() => navigate('/new')}>
            <Plus size={15} />Yeni Dizi / Video
          </button>
        </div>
      </header>

      {loading ? <SkeletonGrid count={4} /> : (
        <>
          <section className="st-section">
            <div className="st-section-head">
              <h2>Diziler ({filteredSeries.length})</h2>
            </div>
            {filteredSeries.length > 0 ? (
              <div className="st-grid-cards">
                {filteredSeries.map(s => {
                  const eps = library.project.filter(p => p.data.series_id === s.id);
                  const done = eps.filter(p => Boolean(latestVideoByProject[p.id])).length;
                  const running = eps.some(p => Boolean(activeJobByProject[p.id]));
                  const castCount = library.character.filter(c => (c.data.series_ids || []).includes(s.id) || (s.data.character_ids || []).includes(c.id)).length;
                  const styleMeta = styles.find(st => st.id === s.data.style);
                  const cover = getSeriesCover(s);
                  return (
                    <article key={s.id} className="st-media-card" onClick={() => navigate(`/series/${s.id}`)}>
                      <div className="st-media-thumb">
                        {cover ? <img src={cover} alt={s.data.name} /> : <Clapperboard size={30} />}
                        <span className="st-thumb-badge">{done}/{eps.length} bölüm hazır</span>
                        {running && <span className="st-thumb-live">Üretiliyor</span>}
                      </div>
                      <div className="st-media-body">
                        <div className="st-row-between">
                          <h3>{s.data.name}</h3>
                          <button
                            type="button"
                            className="st-icon-btn danger"
                            title="Dizi klasörünü sil (bölümler korunur)"
                            onClick={e => { e.stopPropagation(); deleteDoc(s.id, s.data.name); }}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                        <p>{s.data.logline || 'Dizi özeti eklenmemiş.'}</p>
                        <div className="st-chips">
                          {styleMeta && <span className="st-badge">{styleMeta.name}</span>}
                          <span className="st-badge">{castCount} kadro</span>
                        </div>
                        <div className="st-mini-bar">
                          <div style={{ width: `${eps.length ? Math.round((done / eps.length) * 100) : 0}%` }} />
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : (
              <EmptyState
                icon={<Clapperboard size={28} />}
                title="Henüz bir dizi yok"
                description="Çok bölümlü bir seri oluşturup ortak karakter, mekan ve stil kitabıyla tutarlı bölümler üretin."
                action={<button type="button" className="st-btn st-btn-primary" onClick={() => navigate('/new?type=series')}><Plus size={15} />İlk Dizini Oluştur</button>}
              />
            )}
          </section>

          <section className="st-section">
            <div className="st-section-head">
              <h2>Bağımsız Projeler ({standaloneProjects.length})</h2>
            </div>
            {standaloneProjects.length > 0 ? (
              <div className="st-grid-cards">
                {standaloneProjects.map(p => {
                  const first = p.data.script?.scenes?.find(s => s.first_asset)?.first_asset;
                  const videoJob = latestVideoByProject[p.id];
                  const activeJob = activeJobByProject[p.id];
                  const styleMeta = styles.find(st => st.id === p.data.style);
                  return (
                    <article key={p.id} className="st-media-card" onClick={() => navigate(`/episodes/${p.id}`)}>
                      <div className="st-media-thumb">
                        {first ? <img src={mediaUrl(first)} alt={p.data.name} /> : <Film size={28} />}
                        {videoJob && <span className="st-play-overlay"><Play size={20} /></span>}
                        {activeJob && <span className="st-thumb-live">Üretiliyor</span>}
                        <span className="st-thumb-badge">{p.data.duration} sn</span>
                      </div>
                      <div className="st-media-body">
                        <div className="st-row-between">
                          <h3>{p.data.name}</h3>
                          <button
                            type="button"
                            className="st-icon-btn danger"
                            title="Projeyi sil"
                            onClick={e => { e.stopPropagation(); deleteDoc(p.id, p.data.name); }}
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                        <small>{styleMeta?.name || p.data.style} · {p.data.script?.scenes?.length || 0} sahne · {formatDate(p.updated)}</small>
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : (
              <p className="st-muted" style={{ fontSize: 13 }}>Bağımsız tekil proje yok.</p>
            )}
          </section>
        </>
      )}
    </div>
  );
}
