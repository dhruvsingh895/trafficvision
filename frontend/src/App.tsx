import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import UploadPage from './pages/UploadPage';
import ProcessPage from './pages/ProcessPage';
import ResultsPage from './pages/ResultsPage';
import LivePage from './pages/LivePage';

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/process/:videoId" element={<ProcessPage />} />
          <Route path="/live/:videoId" element={<LivePage />} />
          <Route path="/results/:videoId" element={<ResultsPage />} />
          <Route path="*" element={<Navigate to="/upload" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
