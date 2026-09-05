import { lazy, Suspense } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';

const UploadPage = lazy(() => import('./pages/UploadPage'));
const ProcessPage = lazy(() => import('./pages/ProcessPage'));
const ResultsPage = lazy(() => import('./pages/ResultsPage'));
const LivePage = lazy(() => import('./pages/LivePage'));

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Suspense fallback={<p className="loading">Loading…</p>}>
          <Routes>
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/process/:videoId" element={<ProcessPage />} />
            <Route path="/live/:videoId" element={<LivePage />} />
            <Route path="/results/:videoId" element={<ResultsPage />} />
            <Route path="*" element={<Navigate to="/upload" replace />} />
          </Routes>
        </Suspense>
      </Layout>
    </BrowserRouter>
  );
}
