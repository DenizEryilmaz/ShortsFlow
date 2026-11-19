import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-react';
import { QUALITY_PROFILES } from '../../constants';

export function ToastStack({ toasts, onDismiss }) {
  if (!toasts.length) return null;
  return (
    <div className="st-toast-stack" role="status" aria-live="polite">
      {toasts.map(item => (
        <div key={item.id} className={`st-toast st-toast-${item.tone || 'info'}`}>
          {item.tone === 'ok' ? <CheckCircle2 size={16} /> : item.tone === 'err' ? <AlertTriangle size={16} /> : <Info size={16} />}
          <span>{item.message}</span>
          {item.actionLabel && item.onAction && (
            <button type="button" className="st-toast-act" onClick={() => { item.onAction(); onDismiss(item.id); }}>
              {item.actionLabel}
            </button>
          )}
          <button type="button" className="st-icon-btn" aria-label="Kapat" onClick={() => onDismiss(item.id)}>
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

export function ConfirmModal({ state, onResolve }) {
  if (!state) return null;
  return (
    <div className="st-modal-backdrop" role="dialog" aria-modal="true" onClick={() => onResolve(false)}>
      <div className="st-modal" onClick={e => e.stopPropagation()}>
        <h3>{state.title || 'Onay'}</h3>
        <p>{state.body}</p>
        <div className="st-modal-actions">
          <button type="button" className="st-btn" onClick={() => onResolve(false)}>
            {state.cancelLabel || 'Vazgeç'}
          </button>
          <button
            type="button"
            className={state.danger ? 'st-btn st-btn-danger-solid' : 'st-btn st-btn-primary'}
            onClick={() => onResolve(true)}
          >
            {state.confirmLabel || 'Onayla'}
          </button>
        </div>
      </div>
    </div>
  );
}

export function EmptyState({ icon, title, description, body, action }) {
  const text = description || body;
  return (
    <div className="st-empty">
      {icon && <div className="st-empty-icon">{icon}</div>}
      <h3>{title}</h3>
      {text && <p>{text}</p>}
      {action && <div className="st-empty-act">{action}</div>}
    </div>
  );
}

export function SkeletonGrid({ count = 4 }) {
  return (
    <div className="st-grid-cards">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="st-skeleton-card">
          <div className="st-skel-media" />
          <div className="st-skel-line" />
          <div className="st-skel-line short" />
        </div>
      ))}
    </div>
  );
}

export function QualityPicker({ image, video, onChange }) {
  return (
    <div className="st-quality-grid" role="group" aria-label="Kalite ve hız profili">
      {QUALITY_PROFILES.map(profile => {
        const active = image === profile.image && video === profile.video;
        return (
          <button
            key={profile.id}
            type="button"
            className={active ? 'st-quality-card active' : 'st-quality-card'}
            onClick={() => onChange(profile.image, profile.video)}
          >
            <div className="st-quality-top">
              <strong>{profile.title}</strong>
              {profile.recommended && <span className="st-badge st-badge-accent">Önerilen</span>}
            </div>
            <small>{profile.desc}</small>
          </button>
        );
      })}
    </div>
  );
}
