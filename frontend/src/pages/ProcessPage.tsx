import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getVideoStatus } from '../api/client';
import { StatusResponse } from '../api/types';
import './ProcessPage.css';

export default function ProcessPage() {
  const { videoId = '' } = useParams();
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => {
    let active = true;

    const poll = async () => {
      try {
        const s = await getVideoStatus(videoId);
        if (!active) return;
        setStatus(s);
        setError(null);
        if (s.status === 'processing' || s.status === 'uploaded') {
          timer.current = window.setTimeout(poll, 1000);
        }
      } catch (e) {
        if (!active) return;
        setError(e instanceof Error ? e.message : 'Failed to fetch status');
        timer.current = window.setTimeout(poll, 2000);
      }
    };

    poll();
    return () => {
      active = false;
      clearTimeout(timer.current);
    };
  }, [videoId]);

  const running = status?.status === 'processing' || status?.status === 'uploaded';

  return (
    <div className="process-page">
      <h2>Processing Video</h2>
      <p className="video-id">Video ID: {videoId}</p>
      {error && <p className="error-text">{error}</p>}

      {status && (
        <div className="status-card">
          <p className={`status-label ${status.status}`}>
            Status: <strong>{status.status}</strong>
          </p>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${status.progress}%` }} />
          </div>
          <p>{status.progress}% — {status.frames_processed} / {status.total_frames} frames</p>
          {running && (
            <>
              <p className="spinner-text">Processing… this page updates live.</p>
              <Link className="btn secondary" to={`/live/${videoId}`}>
                Watch Live
              </Link>
            </>
          )}
          {status.status === 'failed' && (
            <p className="error-text">Error: {status.error ?? 'Unknown error'}</p>
          )}
          {status.status === 'completed' && (
            <Link className="btn primary" to={`/results/${videoId}`}>
              View Results
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
