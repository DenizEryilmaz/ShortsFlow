import { useState } from 'react';
import { Check, Copy, Download, FileText, Loader2, Sparkles } from 'lucide-react';
import { apiJson, getApiUrl } from '../api';
import { API, jobFileUrl } from '../constants';
import { useStudio } from '../context/StudioContext';

export default function DeliveryTheater({ job, projectName, aspectRatio, onClose, compact = false }) {
  const { addToast, refreshLibrary } = useStudio();
  const [publish, setPublish] = useState(job?.result?.publish || null);
  const [generating, setGenerating] = useState(false);
  const [copiedKey, setCopiedKey] = useState('');

  if (!job?.result?.video) return null;

  const generatePack = async () => {
    setGenerating(true);
    try {
      const meta = await apiJson(`${API}/jobs/${job.id}/publish-pack`, { method: 'POST' });
      setPublish(meta);
      await refreshLibrary();
      addToast('Yayın paketi (başlık, açıklama, etiketler) hazırlandı.', 'ok');
    } catch (err) {
      addToast(err.detail || err.message || 'Yayın paketi oluşturulamadı.', 'err');
    } finally {
      setGenerating(false);
    }
  };

  const copyText = async (key, value) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedKey(key);
      addToast('Panoya kopyalandı.', 'ok', { duration: 2000 });
      setTimeout(() => setCopiedKey(''), 1800);
    } catch {
      addToast('Kopyalama başarısız oldu.', 'err');
    }
  };

  const title = projectName || job.label || job.snapshot?.project?.name || 'Üretilen Video';
  const ratio = aspectRatio || job.aspect_ratio || job.snapshot?.project?.settings?.aspect_ratio || '9:16';
  const scenes = job.result?.scenes || [];

  return (
    <div className={compact ? 'st-delivery compact' : 'st-delivery'}>
      <div className="st-delivery-media">
        <video key={job.id} controls playsInline preload="metadata" src={jobFileUrl(job.id, 'final.mp4')} />
      </div>
      <div className="st-delivery-panel">
        <div className="st-row-between">
          <span className="st-kicker">FİNAL ÇIKTI HAZIR</span>
          {onClose && <button type="button" className="st-btn st-btn-sm" onClick={onClose}>Kapat</button>}
        </div>
        <h3>{title}</h3>
        <div className="st-chips">
          {job.result?.duration && <span className="st-badge st-badge-ok">{Number(job.result.duration).toFixed(1)} sn</span>}
          {scenes.length > 0 && <span className="st-badge">{scenes.length} sahne</span>}
          <span className="st-badge">{ratio}</span>
          <span className="st-badge">H.264 · MP4</span>
        </div>

        <div className="st-actions">
          <a className="st-btn st-btn-primary" download href={jobFileUrl(job.id, 'final.mp4')}>
            <Download size={15} />MP4 Videoyu İndir
          </a>
          {job.result?.srt && (
            <a className="st-btn" download href={jobFileUrl(job.id, 'captions.srt')}>
              <FileText size={15} />Altyazı (.srt)
            </a>
          )}
          <a className="st-btn" download href={getApiUrl(`${API}/jobs/${job.id}/export.zip`)}>
            <Download size={15} />Tüm Paket (.zip)
          </a>
        </div>

        <div className="st-publish-box">
          <div className="st-row-between">
            <strong>Yayın Paketi (YouTube Shorts / TikTok / Reels)</strong>
            <button type="button" className="st-btn st-btn-sm" disabled={generating} onClick={generatePack}>
              {generating ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
              {publish ? 'Yenile' : 'Başlık & Etiket Üret'}
            </button>
          </div>
          {publish ? (
            <div className="st-publish-fields">
              <div className="st-publish-row">
                <label>Başlık</label>
                <div>
                  <span>{publish.title}</span>
                  <button type="button" className="st-icon-btn" onClick={() => copyText('title', publish.title)}>
                    {copiedKey === 'title' ? <Check size={13} /> : <Copy size={13} />}
                  </button>
                </div>
              </div>
              {publish.hook && (
                <div className="st-publish-row">
                  <label>Açılış kancası</label>
                  <div>
                    <span>{publish.hook}</span>
                    <button type="button" className="st-icon-btn" onClick={() => copyText('hook', publish.hook)}>
                      {copiedKey === 'hook' ? <Check size={13} /> : <Copy size={13} />}
                    </button>
                  </div>
                </div>
              )}
              <div className="st-publish-row">
                <label>Açıklama</label>
                <div>
                  <span>{publish.description}</span>
                  <button type="button" className="st-icon-btn" onClick={() => copyText('desc', `${publish.description}\n\n${(publish.hashtags || []).join(' ')}`)}>
                    {copiedKey === 'desc' ? <Check size={13} /> : <Copy size={13} />}
                  </button>
                </div>
              </div>
              {publish.hashtags?.length > 0 && (
                <div className="st-chips">
                  {publish.hashtags.map(tag => <span key={tag} className="st-badge">{tag}</span>)}
                </div>
              )}
            </div>
          ) : (
            <p className="st-muted" style={{ fontSize: 12, margin: '6px 0 0' }}>
              Tek tıkla videonuza uygun başlık, açıklama ve hashtag paketi hazırlayın.
            </p>
          )}
        </div>

        {scenes.length > 0 && (
          <div className="st-delivery-scenes">
            <strong>Sahne akışı</strong>
            <ol>
              {scenes.map((sc, i) => (
                <li key={sc.stem || i}>
                  <span>Sahne {i + 1} · {sc.duration} sn</span>
                  <small>{sc.narration || sc.caption || ''}</small>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}
