import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { getVideoStatus, liveStream } from '../api/client';
import { JobStatus, LiveFrameEvent } from '../api/types';
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
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);
  const lineRatioRef = useRef(0.5);

  useEffect(() => {
    let active = true;
    let timer: number | undefined;

    const pollStatus = async () => {
      try {
        const status = await getVideoStatus(videoId);
        if (!active) return;
        setJobStatus(status.status);
        setProgress(status.progress);
        if (status.status === 'completed' || status.status === 'failed') {
          setDone(true);
          if (status.status === 'failed') {
            setError(status.error ?? 'Processing failed.');
          }
          return;
        }
        timer = window.setTimeout(pollStatus, 2000);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Failed to read processing status.');
        timer = window.setTimeout(pollStatus, 3000);
      }
    };

    pollStatus();
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
        // Live frames are optional; status polling continues if the stream drops.
        if (err.message !== 'Connection lost') {
          setError(err.message);
        }
      },
      () => {
        // Final completion is determined by the persisted job status.
      },
    );
    cleanupRef.current = cleanup;
    return () => {
      active = false;
      window.clearTimeout(timer);
      cleanupRef.current?.();
    };
  }, [videoId]);

  return (
    <div className="live-page">
      <h2>Live Processing</h2>
      <p className="video-id">Video ID: {videoId}</p>
      {error && <p className="error-text">{error}</p>}
      {jobStatus === 'completed' && (
        <p>Processing completed. Live preview is optional.</p>
      )}

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

      {done && jobStatus === 'completed' && (
        <Link className="btn primary" to={`/results/${videoId}`}>
          View Final Results
        </Link>
      )}
    </div>
  );
}