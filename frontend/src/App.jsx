import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { StudioProvider } from './context/StudioContext';
import AppShell from './components/AppShell';
import HomePage from './pages/HomePage';
import SeriesListPage from './pages/SeriesListPage';
import SeriesHubPage from './pages/SeriesHubPage';
import EpisodeWorkspacePage from './pages/EpisodeWorkspacePage';
import WizardPage from './pages/WizardPage';
import LibraryPage from './pages/LibraryPage';
import AssetsPage from './pages/AssetsPage';
import SystemPage from './pages/SystemPage';

export default function App() {
  return (
    <BrowserRouter>
      <StudioProvider>
        <AppShell>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/new" element={<WizardPage />} />
            <Route path="/series" element={<SeriesListPage />} />
            <Route path="/series/:seriesId" element={<SeriesHubPage />} />
            <Route path="/series/:seriesId/episodes/:episodeId" element={<EpisodeWorkspacePage />} />
            <Route path="/episodes/:episodeId" element={<EpisodeWorkspacePage />} />
            <Route path="/library" element={<LibraryPage />} />
            <Route path="/assets" element={<AssetsPage />} />
            <Route path="/system" element={<SystemPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppShell>
      </StudioProvider>
    </BrowserRouter>
  );
}
