import { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { liveStream } from '../api/client';
import { LiveFrameEvent } from '../api/types';
import StatCard from '../components/StatCard';
import './LivePage.css';

export default function LivePage() {
  const { videoId = '' } = useParams();
  const [frame, setFrame] = useState<string | null>(null);
  const [stats, setStats] = useState<LiveFrameEvent['stats']>({
    total: 0, by_type: { car: 0, motorcycle: 0, bus: 0, truck: 0 },
    entering: 0, exiting: 0,
  });
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const cleanupRef = useRef<(() => void) | null>(null);
  const lineRatioRef = useRef(0.5);

  useEffect(() => {
    const cleanup = liveStream(
      videoId,
      lineRatioRef.current,
      (evt: LiveFrameEvent) => {
        if (evt.jpeg_b64) {
          setFrame(`data:image/jpeg;base64,${evt.jpeg_b64}`);
          setStats(evt.stats);
        }
        setProgress(evt.progress);
      },
      (err) => {
        setError(err.message);
        setDone(true);
      },
      () => {
        setDone(true);
        setProgress(100);
      },
    );
    cleanupRef.current = cleanup;
    return () => cleanupRef.current?.();
  }, [videoId]);

  return (
    <div className="live-page">
      <h2>Live Processing</h2>
      <p className="video-id">Video ID: {videoId}</p>
      {error && <p className="error-text">{error}</p>}

      <div className="live-container">
        <div className="live-video">
          {frame ? (
            <img src={frame} alt="Live annotated frame" className="live-frame" />
          ) : (
            <div className="live-placeholder">Waiting for first frame…</div>
          )}
          <div className="progress-overlay">
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <span>{progress}%</span>
          </div>
        </div>

        <div className="live-stats">
          <StatCard label="Total" value={stats.total} accent="#4f8ef7" />
          <StatCard label="Cars" value={stats.by_type.car} accent="#57c26b" />
          <StatCard label="Motorcycles" value={stats.by_type.motorcycle} accent="#e0b341" />
          <StatCard label="Buses" value={stats.by_type.bus} accent="#b07ae8" />
          <StatCard label="Trucks" value={stats.by_type.truck} accent="#e0703a" />
          <StatCard label="Entering" value={stats.entering} accent="#3ac8c8" />
          <StatCard label="Exiting" value={stats.exiting} accent="#e05a7a" />
        </div>
      </div>

      {done && (
        <a className="btn primary" href={`/results/${videoId}`}>
          View Final Results
        </a>
      )}
    </div>
  );
}