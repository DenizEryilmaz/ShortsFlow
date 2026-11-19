import { NavLink, useNavigate } from 'react-router-dom';
import {
  Clapperboard, Cpu, Film, FolderKanban, Home, Layers, Plus,
} from 'lucide-react';
import { useStudio } from '../context/StudioContext';
import { ConfirmModal, ToastStack } from './ui/Primitives';
import QueueDrawer from './QueueDrawer';

const NAV = [
  { to: '/', label: 'Ana Sayfa', icon: Home, end: true },
  { to: '/series', label: 'Diziler', icon: Clapperboard },
  { to: '/library', label: 'Kütüphane', icon: FolderKanban },
  { to: '/assets', label: 'Varlıklar', icon: Layers },
  { to: '/system', label: 'Sistem', icon: Cpu },
];

export default function AppShell({ children }) {
  const navigate = useNavigate();
  const { toasts, dismissToast, confirmState, resolveConfirm, system } = useStudio();

  const offlineServices = (system?.services || []).filter(s => s.id !== 'worker' && !s.ready);

  return (
    <div className="st-shell">
      <aside className="st-rail" aria-label="Ana gezinme">
        <button type="button" className="st-rail-brand" onClick={() => navigate('/')}>
          <span className="st-brand-mark"><Film size={19} /></span>
          <div>
            <strong>ShortsFlow</strong>
            <small>Yerel Prodüksiyon</small>
          </div>
        </button>

        <button type="button" className="st-btn st-btn-primary st-rail-cta" onClick={() => navigate('/new')}>
          <Plus size={16} />Yeni Oluştur
        </button>

        <nav className="st-rail-nav">
          {NAV.map(item => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) => (isActive ? 'st-rail-link active' : 'st-rail-link')}
              >
                <Icon size={17} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <button type="button" className="st-rail-status" onClick={() => navigate('/system')}>
          <span className={offlineServices.length ? 'st-dot err' : 'st-dot ok'} />
          <span>{offlineServices.length ? `${offlineServices.length} servis kapalı` : 'GPU & Motorlar hazır'}</span>
        </button>
      </aside>

      <main className="st-main">
        {children}
      </main>

      <QueueDrawer />
      <ToastStack toasts={toasts} onDismiss={dismissToast} />
      <ConfirmModal state={confirmState} onResolve={resolveConfirm} />
    </div>
  );
}
