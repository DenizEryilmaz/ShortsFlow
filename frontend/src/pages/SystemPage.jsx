import { useState } from 'react';
import {
  Cpu, HardDrive, Loader2, Play, RefreshCw, Server, Trash2, Zap,
} from 'lucide-react';
import { apiJson } from '../api';
import { API, KIND_LABELS } from '../constants';
import { useStudio } from '../context/StudioContext';

export default function SystemPage() {
  const { system, models, refreshSystem, refreshCatalog, startService, addToast, confirm } = useStudio();
  const [clearing, setClearing] = useState(false);
  const [startingId, setStartingId] = useState('');

  const handleStart = async id => {
    setStartingId(id);
    try {
      await startService(id);
    } catch (err) {
      addToast(err.detail || err.message || 'Servis başlatılamadı.', 'err');
    } finally {
      setTimeout(() => setStartingId(''), 1500);
    }
  };

  const handleClearCache = async () => {
    const ok = await confirm({
      title: 'Önbelleği temizle',
      body: 'Ara üretim önbelleği silinsin mi? Tamamlanmış videolarınız ve projeleriniz etkilenmez.',
      confirmLabel: 'Temizle',
    });
    if (!ok) return;
    setClearing(true);
    try {
      const res = await apiJson(`${API}/system/cache/clear`, { method: 'POST' });
      await refreshSystem();
      addToast(`Önbellek temizlendi (${res.freed_mb} MB yer açıldı).`, 'ok');
    } catch (err) {
      addToast(err.detail || err.message || 'Önbellek temizlenemedi.', 'err');
    } finally {
      setClearing(false);
    }
  };

  const gpu = system?.hardware?.gpu;
  const ram = system?.hardware?.ram;
  const disk = system?.hardware?.disk;
  const storage = system?.storage;

  const vramPct = gpu?.vram_total_mb ? Math.round((gpu.vram_used_mb / gpu.vram_total_mb) * 100) : 0;
  const ramTotalGb = ram?.total_mb ? (ram.total_mb / 1024).toFixed(1) : null;
  const ramUsedGb = ram?.total_mb ? (ram.used_mb / 1024).toFixed(1) : null;
  const ramPct = ram?.total_mb ? Math.round((ram.used_mb / ram.total_mb) * 100) : 0;
  const diskPct = disk?.total_gb ? Math.round((disk.used_gb / disk.total_gb) * 100) : 0;
  const studioTotalMb = storage ? ((storage.cache_mb || 0) + (storage.jobs_mb || 0) + (storage.assets_mb || 0)).toFixed(1) : '0';

  return (
    <div className="st-page">
      <div className="st-page-head">
        <div>
          <h1>Sistem, GPU &amp; Motorlar</h1>
          <p className="st-muted">Yerel yapay zekâ servislerinin durumu, bellek kullanımı ve kurulu modeller.</p>
        </div>
        <button type="button" className="st-btn" onClick={() => { refreshSystem(); refreshCatalog(); }}>
          <RefreshCw size={15} />Yenile
        </button>
      </div>

      {/* Services */}
      <section className="st-section">
        <div className="st-section-head">
          <h2><Server size={18} />Yerel Servisler</h2>
        </div>
        <div className="st-grid-four">
          {(system?.services || []).map(svc => (
            <div key={svc.id} className="st-card st-service-card">
              <div className="st-row-between">
                <strong>{svc.name}</strong>
                <span className={svc.ready ? 'st-badge st-badge-ok' : 'st-badge st-badge-err'}>
                  {svc.ready ? 'Çalışıyor' : 'Kapalı'}
                </span>
              </div>
              <p className="st-muted" style={{ fontSize: 12, margin: '8px 0 12px' }}>{svc.detail}</p>
              {!svc.ready && svc.can_start && (
                <button
                  type="button"
                  className="st-btn st-btn-sm st-btn-primary"
                  disabled={startingId === svc.id}
                  onClick={() => handleStart(svc.id)}
                >
                  {startingId === svc.id ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} />}
                  Tek Tıkla Başlat
                </button>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Hardware Telemetry */}
      <section className="st-section">
        <div className="st-section-head">
          <h2><Cpu size={18} />Donanım &amp; Depolama</h2>
        </div>
        <div className="st-grid-three">
          <div className="st-card">
            <div className="st-row-between">
              <strong><Zap size={15} /> Ekran Kartı (VRAM)</strong>
              <span className="st-badge">{gpu ? `%${vramPct}` : 'Tespit edilemedi'}</span>
            </div>
            <p className="st-muted" style={{ fontSize: 12, margin: '6px 0 10px' }}>
              {gpu ? `${gpu.name} · ${(gpu.vram_used_mb / 1024).toFixed(1)} / ${(gpu.vram_total_mb / 1024).toFixed(1)} GB` : 'NVIDIA GPU bilgisi alınamadı'}
            </p>
            <div className="st-mini-bar"><div style={{ width: `${vramPct}%` }} /></div>
          </div>

          <div className="st-card">
            <div className="st-row-between">
              <strong><Cpu size={15} /> Sistem Belleği (RAM)</strong>
              <span className="st-badge">{ramTotalGb ? `%${ramPct}` : '—'}</span>
            </div>
            <p className="st-muted" style={{ fontSize: 12, margin: '6px 0 10px' }}>
              {ramTotalGb ? `${ramUsedGb} / ${ramTotalGb} GB kullanımda` : 'RAM bilgisi alınamadı'}
            </p>
            <div className="st-mini-bar"><div style={{ width: `${ramPct}%` }} /></div>
          </div>

          <div className="st-card">
            <div className="st-row-between">
              <strong><HardDrive size={15} /> Disk &amp; Önbellek</strong>
              <span className="st-badge">{disk ? `${disk.free_gb} GB boş` : '—'}</span>
            </div>
            <p className="st-muted" style={{ fontSize: 12, margin: '6px 0 10px' }}>
              Stüdyo verisi: {studioTotalMb} MB · Önbellek: {storage?.cache_mb ?? 0} MB
            </p>
            <div className="st-mini-bar" style={{ marginBottom: 10 }}><div style={{ width: `${diskPct}%` }} /></div>
            <button
              type="button"
              className="st-btn st-btn-sm"
              disabled={clearing || !(storage?.cache_mb > 0)}
              onClick={handleClearCache}
            >
              {clearing ? <Loader2 size={13} className="animate-spin" /> : <Trash2 size={13} />}
              Önbelleği Temizle ({storage?.cache_mb ?? 0} MB)
            </button>
          </div>
        </div>
      </section>

      {/* Installed Models */}
      <section className="st-section">
        <div className="st-section-head">
          <h2>Kurulu Yapay Zekâ Modelleri ({models.filter(m => m.ready).length}/{models.length})</h2>
        </div>
        <div className="st-card">
          <div className="st-models-grid">
            {models.map(m => (
              <div key={`${m.kind}-${m.id}`} className="st-model-row">
                <div>
                  <span className="st-kicker">{KIND_LABELS[m.kind] || m.kind}</span>
                  <strong>{m.name}</strong>
                  <small className="st-muted">{m.note || m.id}</small>
                </div>
                <span className={m.ready ? 'st-badge st-badge-ok' : 'st-badge'}>
                  {m.ready ? 'Hazır' : 'Eksik'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
