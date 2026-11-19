import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowUpToLine, Bell, ChevronDown, ChevronUp, Loader2, Play, RotateCcw, Trash2, X,
} from 'lucide-react';
import { formatDate, formatEta, humanizeError, JOB_LABELS, STATUS_LABELS, STATUS_TONE } from '../constants';
import { useStudio } from '../context/StudioContext';

export default function QueueDrawer() {
  const navigate = useNavigate();
  const {
    jobs, queueOpen, setQueueOpen, cancelJob, retryJob, prioritizeJob, deleteJob, startService, addToast,
  } = useStudio();
  const [filter, setFilter] = useState('active');
  const [notifGranted, setNotifGranted] = useState(
    () => typeof Notification !== 'undefined' && Notification.permission === 'granted',
  );

  const running = useMemo(() => jobs.filter(j => j.status === 'running'), [jobs]);
  const queued = useMemo(() => [...jobs.filter(j => j.status === 'queued')].reverse(), [jobs]);
  const recent = useMemo(() => jobs.filter(j => ['completed', 'failed'].includes(j.status)).slice(0, 25), [jobs]);

  const totalEtaSec = useMemo(
    () => [...running, ...queued].reduce((sum, j) => sum + (Number(j.estimate_seconds) || 0), 0),
    [running, queued],
  );

  const requestNotifications = async () => {
    if (typeof Notification === 'undefined') {
      addToast('Bu tarayıcı bildirimleri desteklemiyor.', 'err');
      return;
    }
    const perm = await Notification.requestPermission();
    setNotifGranted(perm === 'granted');
    addToast(perm === 'granted' ? 'Üretim bitince tarayıcı bildirimi alacaksınız.' : 'Bildirim izni verilmedi.', perm === 'granted' ? 'ok' : 'info');
  };

  const activeCount = running.length + queued.length;
  const currentJob = running[0];
  const pctMatch = currentJob?.latest_event?.match(/%(\d{1,3})/);
  const pct = pctMatch ? Number(pctMatch[1]) : null;

  return (
    <aside className={queueOpen ? 'st-queue open' : 'st-queue'} aria-label="Üretim kuyruğu">
      <button type="button" className="st-queue-bar" onClick={() => setQueueOpen(!queueOpen)}>
        <div className="st-queue-bar-left">
          {running.length > 0 ? (
            <Loader2 size={15} className="animate-spin st-accent-text" />
          ) : (
            <span className={activeCount > 0 ? 'st-dot warn' : 'st-dot ok'} />
          )}
          <strong>
            {running.length > 0
              ? `${currentJob.label || JOB_LABELS[currentJob.kind] || 'Üretiliyor'}`
              : queued.length > 0
                ? `${queued.length} iş kuyrukta`
                : 'Üretim kuyruğu hazır'}
          </strong>
          {pct !== null && <span className="st-badge st-badge-accent">%{pct}</span>}
          {activeCount > 0 && <span className="st-muted" style={{ fontSize: 12 }}>· {formatEta(totalEtaSec)}</span>}
        </div>
        <div className="st-queue-bar-right">
          {activeCount > 0 && <span className="st-badge">{activeCount} aktif</span>}
          {queueOpen ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
        </div>
      </button>

      {queueOpen && (
        <div className="st-queue-body">
          <div className="st-queue-toolbar">
            <div className="st-pills">
              <button type="button" className={filter === 'active' ? 'active' : ''} onClick={() => setFilter('active')}>
                Aktif ({activeCount})
              </button>
              <button type="button" className={filter === 'done' ? 'active' : ''} onClick={() => setFilter('done')}>
                Tamamlanan ({recent.filter(j => j.status === 'completed').length})
              </button>
              <button type="button" className={filter === 'failed' ? 'active' : ''} onClick={() => setFilter('failed')}>
                Hatalar ({recent.filter(j => j.status === 'failed').length})
              </button>
            </div>
            {!notifGranted && (
              <button type="button" className="st-btn st-btn-sm" onClick={requestNotifications}>
                <Bell size={13} />Bitince bildir
              </button>
            )}
          </div>

          <div className="st-queue-list">
            {filter === 'active' && (
              <>
                {running.map(item => (
                  <div key={item.id} className="st-queue-item running">
                    <div className="st-row-between">
                      <div>
                        <strong>{item.label || JOB_LABELS[item.kind]}</strong>
                        <small>{JOB_LABELS[item.kind]} · {formatEta(item.estimate_seconds)}</small>
                      </div>
                      <button type="button" className="st-btn st-btn-sm st-btn-danger" onClick={() => cancelJob(item.id)}>
                        <X size={13} />İptal
                      </button>
                    </div>
                    <p className="st-queue-event">{item.latest_event || 'Üretiliyor…'}</p>
                  </div>
                ))}
                {queued.map((item, idx) => (
                  <div key={item.id} className="st-queue-item">
                    <div className="st-row-between">
                      <div>
                        <strong>#{idx + 1} · {item.label || JOB_LABELS[item.kind]}</strong>
                        <small>{JOB_LABELS[item.kind]} · {formatEta(item.estimate_seconds)}</small>
                      </div>
                      <div className="st-actions" style={{ margin: 0, gap: 4 }}>
                        {idx > 0 && (
                          <button type="button" className="st-icon-btn" title="Öne al" onClick={() => prioritizeJob(item.id)}>
                            <ArrowUpToLine size={14} />
                          </button>
                        )}
                        <button type="button" className="st-icon-btn danger" title="İptal et" onClick={() => cancelJob(item.id)}>
                          <X size={14} />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
                {activeCount === 0 && (
                  <p className="st-muted" style={{ textAlign: 'center', padding: '18px 0', fontSize: 13 }}>
                    Şu an çalışan veya bekleyen bir üretim yok.
                  </p>
                )}
              </>
            )}

            {filter !== 'active' && (
              <>
                {recent
                  .filter(j => (filter === 'done' ? j.status === 'completed' : j.status === 'failed'))
                  .map(item => {
                    const errInfo = item.status === 'failed' ? humanizeError(item.error) : null;
                    return (
                      <div key={item.id} className="st-queue-item">
                        <div className="st-row-between">
                          <div>
                            <strong>{item.label || JOB_LABELS[item.kind]}</strong>
                            <small>{JOB_LABELS[item.kind]} · {formatDate(item.updated)}</small>
                          </div>
                          <span className={`st-badge st-badge-${STATUS_TONE[item.status]}`}>{STATUS_LABELS[item.status]}</span>
                        </div>
                        {errInfo && (
                          <div className="st-error-inline">
                            <strong>{errInfo.title}</strong>
                            <p>{errInfo.hint}</p>
                          </div>
                        )}
                        <div className="st-actions" style={{ margin: '8px 0 0', gap: 6 }}>
                          {item.result?.video && (
                            <button type="button" className="st-btn st-btn-sm st-btn-primary" onClick={() => { setQueueOpen(false); navigate(`/library?job=${item.id}`); }}>
                              <Play size={12} />İzle
                            </button>
                          )}
                          {item.project_id && (
                            <button type="button" className="st-btn st-btn-sm" onClick={() => { setQueueOpen(false); navigate(`/episodes/${item.project_id}`); }}>
                              Bölümü aç
                            </button>
                          )}
                          {errInfo?.action === 'start_comfyui' && (
                            <button type="button" className="st-btn st-btn-sm st-btn-primary" onClick={() => startService('comfyui')}>
                              ComfyUI Başlat
                            </button>
                          )}
                          {errInfo?.action === 'start_ollama' && (
                            <button type="button" className="st-btn st-btn-sm st-btn-primary" onClick={() => startService('ollama')}>
                              Ollama Başlat
                            </button>
                          )}
                          {item.status === 'failed' && (
                            <button type="button" className="st-btn st-btn-sm" onClick={() => retryJob(item.id)}>
                              <RotateCcw size={12} />Yeniden dene
                            </button>
                          )}
                          <button type="button" className="st-icon-btn danger" title="Sil" onClick={() => deleteJob(item.id)}>
                            <Trash2 size={13} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                {recent.filter(j => (filter === 'done' ? j.status === 'completed' : j.status === 'failed')).length === 0 && (
                  <p className="st-muted" style={{ textAlign: 'center', padding: '18px 0', fontSize: 13 }}>
                    Bu kategoride kayıt yok.
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </aside>
  );
}
