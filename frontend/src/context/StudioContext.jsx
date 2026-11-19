import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { apiFetch, apiJson, getApiUrl } from '../api';
import { API, JOB_LABELS, requestJson } from '../constants';

const StudioContext = createContext(null);

export function StudioProvider({ children }) {
  const [library, setLibrary] = useState({ series: [], project: [], character: [], template: [] });
  const [models, setModels] = useState([]);
  const [voices, setVoices] = useState([]);
  const [styles, setStyles] = useState([]);
  const [defaultPrompt, setDefaultPrompt] = useState('');
  const [jobs, setJobs] = useState([]);
  const [system, setSystem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState([]);
  const [confirmState, setConfirmState] = useState(null);
  const [queueOpen, setQueueOpen] = useState(false);
  const [activeJobDetail, setActiveJobDetail] = useState(null);
  const prevStatusesRef = useRef({});

  const addToast = useCallback((message, tone = 'info', options = {}) => {
    const id = crypto.randomUUID();
    setToasts(prev => [...prev.slice(-4), { id, message, tone, ...options }]);
    const duration = options.duration ?? (tone === 'err' ? 6000 : 4000);
    setTimeout(() => {
      setToasts(prev => prev.filter(item => item.id !== id));
    }, duration);
    return id;
  }, []);

  const dismissToast = useCallback(id => {
    setToasts(prev => prev.filter(item => item.id !== id));
  }, []);

  const confirm = useCallback(options => new Promise(resolve => {
    setConfirmState({ ...options, resolve });
  }), []);

  const resolveConfirm = useCallback(answer => {
    setConfirmState(cur => {
      if (cur?.resolve) cur.resolve(answer);
      return null;
    });
  }, []);

  const refreshLibrary = useCallback(async () => {
    const [records, history] = await Promise.all([apiJson(`${API}/library`), apiJson(`${API}/jobs`)]);
    setLibrary(records);
    setJobs(history.jobs || []);
    return records;
  }, []);

  const refreshCatalog = useCallback(async () => {
    const catalog = await apiJson(`${API}/catalog`);
    setModels(catalog.models || []);
    setVoices(catalog.voices || []);
    setStyles(catalog.styles || []);
    setDefaultPrompt(catalog.default_prompt || '');
    return catalog;
  }, []);

  const refreshSystem = useCallback(async () => {
    try {
      const st = await apiJson(`${API}/system/status`);
      setSystem(st);
      return st;
    } catch {
      return null;
    }
  }, []);

  // Initial load
  useEffect(() => {
    let mounted = true;
    Promise.all([refreshCatalog(), refreshLibrary(), refreshSystem()])
      .catch(err => {
        if (mounted) addToast(err.detail || err.message || 'Stüdyo verileri yüklenemedi.', 'err');
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => { mounted = false; };
  }, [refreshCatalog, refreshLibrary, refreshSystem, addToast]);

  // Live Server-Sent Events stream for queue/job updates + completion notifications
  useEffect(() => {
    let source = null;
    let retryTimer = null;
    let active = true;

    const handleJobsUpdate = incomingJobs => {
      if (!active || !Array.isArray(incomingJobs)) return;
      const prev = prevStatusesRef.current;
      let anyFinished = false;
      for (const item of incomingJobs) {
        const oldStatus = prev[item.id];
        if (oldStatus && ['queued', 'running'].includes(oldStatus) && item.status === 'completed') {
          anyFinished = true;
          const msg = `${item.label || JOB_LABELS[item.kind] || 'Üretim'} tamamlandı!`;
          addToast(msg, 'ok');
          if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
            try { new Notification('ShortsFlow', { body: msg }); } catch {}
          }
        } else if (oldStatus && ['queued', 'running'].includes(oldStatus) && item.status === 'failed' && item.error !== '__CANCEL_REQUESTED__') {
          anyFinished = true;
          addToast(`${item.label || 'Üretim'} başarısız oldu.`, 'err');
        }
        prev[item.id] = item.status;
      }
      setJobs(incomingJobs);
      if (anyFinished) {
        refreshLibrary().catch(() => {});
        refreshCatalog().catch(() => {});
      }
    };

    const connect = () => {
      if (!active) return;
      try {
        source = new EventSource(getApiUrl(`${API}/events/stream`));
        source.onmessage = evt => {
          try {
            const payload = JSON.parse(evt.data);
            if (payload.jobs) handleJobsUpdate(payload.jobs);
          } catch {}
        };
        source.onerror = () => {
          source?.close();
          if (active) retryTimer = setTimeout(connect, 4000);
        };
      } catch {
        retryTimer = setTimeout(connect, 5000);
      }
    };

    connect();
    return () => {
      active = false;
      source?.close();
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, [addToast, refreshLibrary, refreshCatalog]);

  // Periodically refresh system health (every 20s)
  useEffect(() => {
    const t = setInterval(() => { refreshSystem(); }, 20000);
    return () => clearInterval(t);
  }, [refreshSystem]);

  // CRUD & Action helpers
  const saveDoc = useCallback(async (kind, data, existing = null) => {
    const saved = await apiJson(
      existing ? `${API}/documents/${existing.id}` : `${API}/documents/${kind}`,
      requestJson(existing ? 'PUT' : 'POST', { data, revision: existing?.revision }),
    );
    await refreshLibrary();
    return saved;
  }, [refreshLibrary]);

  const deleteDoc = useCallback(async (id, label = 'Bu kayıt') => {
    const ok = await confirm({
      title: 'Kaydı sil',
      body: `"${label}" kalıcı olarak silinsin mi?`,
      confirmLabel: 'Sil',
      danger: true,
    });
    if (!ok) return false;
    await apiJson(`${API}/documents/${id}`, { method: 'DELETE' });
    await refreshLibrary();
    addToast('Kayıt silindi.', 'info');
    return true;
  }, [confirm, refreshLibrary, addToast]);

  const produceJob = useCallback(async (projectId, kind, extra = {}) => {
    const created = await apiJson(`${API}/projects/${projectId}/jobs`, requestJson('POST', { kind, ...extra }));
    await refreshLibrary();
    addToast(`${JOB_LABELS[kind] || 'Üretim'} kuyruğa alındı.`, 'ok');
    return created;
  }, [refreshLibrary, addToast]);

  const cancelJob = useCallback(async id => {
    const ok = await confirm({
      title: 'Üretimi iptal et',
      body: 'Bu üretim durdurulsun mu? Tamamlanmış aşamalar korunur.',
      confirmLabel: 'İptal et',
      danger: true,
    });
    if (!ok) return null;
    const updated = await apiJson(`${API}/jobs/${id}/cancel`, { method: 'POST' });
    await refreshLibrary();
    addToast('İptal isteği gönderildi.', 'info');
    return updated;
  }, [confirm, refreshLibrary, addToast]);

  const retryJob = useCallback(async id => {
    const updated = await apiJson(`${API}/jobs/${id}/retry`, { method: 'POST' });
    await refreshLibrary();
    addToast('Üretim yeniden kuyruğa alındı.', 'ok');
    return updated;
  }, [refreshLibrary, addToast]);

  const prioritizeJob = useCallback(async id => {
    await apiJson(`${API}/queue/prioritize/${id}`, { method: 'POST' });
    await refreshLibrary();
    addToast('İş sıranın en başına alındı.', 'ok');
  }, [refreshLibrary, addToast]);

  const deleteJob = useCallback(async id => {
    const ok = await confirm({
      title: 'Üretim kaydını sil',
      body: 'Bu üretim kaydı ve çıktı dosyaları silinsin mi?',
      confirmLabel: 'Sil',
      danger: true,
    });
    if (!ok) return false;
    await apiJson(`${API}/jobs/${id}`, { method: 'DELETE' });
    if (activeJobDetail?.id === id) setActiveJobDetail(null);
    await refreshLibrary();
    addToast('Üretim kaydı silindi.', 'info');
    return true;
  }, [confirm, refreshLibrary, addToast, activeJobDetail?.id]);

  const uploadImage = useCallback(async file => {
    const body = new FormData();
    body.append('file', file);
    const res = await apiFetch(`${API}/assets`, { method: 'POST', body });
    if (!res.ok) throw new Error((await res.json()).detail || 'Görsel yüklenemedi.');
    return (await res.json()).id;
  }, []);

  const uploadAudio = useCallback(async file => {
    const body = new FormData();
    body.append('file', file);
    const res = await apiFetch(`${API}/assets/audio`, { method: 'POST', body });
    if (!res.ok) throw new Error((await res.json()).detail || 'Ses dosyası yüklenemedi.');
    return (await res.json()).id;
  }, []);

  const startService = useCallback(async serviceId => {
    const res = await apiJson(`${API}/system/service/${serviceId}/start`, { method: 'POST' });
    addToast(res.message || 'Servis başlatılıyor…', 'ok');
    setTimeout(() => { refreshSystem(); refreshCatalog(); }, 4000);
  }, [addToast, refreshSystem, refreshCatalog]);

  // Derived maps for instant O(1) lookup across all pages
  const latestVideoByProject = useMemo(() => {
    const map = {};
    for (const j of jobs) {
      if (j.project_id && j.status === 'completed' && j.result?.video && !map[j.project_id]) {
        map[j.project_id] = j;
      }
    }
    return map;
  }, [jobs]);

  const activeJobByProject = useMemo(() => {
    const map = {};
    for (const j of jobs) {
      if (j.project_id && ['running', 'queued'].includes(j.status) && !map[j.project_id]) {
        map[j.project_id] = j;
      }
    }
    return map;
  }, [jobs]);

  const value = {
    library,
    models,
    voices,
    styles,
    defaultPrompt,
    jobs,
    system,
    loading,
    toasts,
    confirmState,
    queueOpen,
    setQueueOpen,
    activeJobDetail,
    setActiveJobDetail,
    addToast,
    dismissToast,
    confirm,
    resolveConfirm,
    refreshLibrary,
    refreshCatalog,
    refreshSystem,
    saveDoc,
    deleteDoc,
    produceJob,
    cancelJob,
    retryJob,
    prioritizeJob,
    deleteJob,
    uploadImage,
    uploadAudio,
    startService,
    latestVideoByProject,
    activeJobByProject,
  };

  return <StudioContext.Provider value={value}>{children}</StudioContext.Provider>;
}

export function useStudio() {
  const ctx = useContext(StudioContext);
  if (!ctx) throw new Error('useStudio must be used within StudioProvider');
  return ctx;
}
