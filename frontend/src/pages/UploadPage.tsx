import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getVideoInfo, startProcessing } from '../api/client';
import { uploadVideo } from '../api/upload';
import { UploadResponse, VideoInfo } from '../api/types';
import DropZone from '../components/DropZone';
import LineConfig from '../components/LineConfig';
import './UploadPage.css';

export default function UploadPage() {
  const navigate = useNavigate();
  const [progress, setProgress] = useState<number | null>(null);
  const [upload, setUpload] = useState<UploadResponse | null>(null);
  const [info, setInfo] = useState<VideoInfo | null>(null);
  const [lineRatio, setLineRatio] = useState(0.5);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  const handleFile = async (file: File) => {
    setError(null);
    setUpload(null);
    setInfo(null);
    setProgress(0);
    try {
      const res = await uploadVideo(file, setProgress);
      setUpload(res);
      setProgress(null);
      try {
        setInfo(await getVideoInfo(res.video_id));
      } catch {
        setError('Upload succeeded but failed to read video info.');
      }
    } catch (e) {
      setProgress(null);
      setError(e instanceof Error ? e.message : 'Upload failed');
    }
  };

  const handleStart = async () => {
    if (!upload) return;
    setStarting(true);
    setError(null);
    try {
      await startProcessing(upload.video_id, { line_y_ratio: lineRatio });
      navigate(`/process/${upload.video_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start processing');
      setStarting(false);
    }
  };

  return (
    <div className="upload-page">
      <h2>Upload Video</h2>
      <DropZone onFile={handleFile} disabled={progress !== null} />

      {progress !== null && (
        <div className="progress-block">
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
          <span>{progress}%</span>
        </div>
      )}

      {error && <p className="error-text">{error}</p>}

      {upload && (
        <div className="upload-result">
          <h3>Uploaded</h3>
          <p>
            {upload.filename} ({(upload.size_bytes / 1048576).toFixed(1)} MB)
          </p>
          {info && (
            <div className="info-grid">
              <span>Resolution</span>
              <span>{info.width}×{info.height}</span>
              <span>Duration</span>
              <span>{info.duration.toFixed(1)} s</span>
              <span>FPS</span>
              <span>{info.fps}</span>
              <span>Frames</span>
              <span>{info.frame_count}</span>
            </div>
          )}
          <LineConfig videoId={upload.video_id} ratio={lineRatio} onChange={setLineRatio} />
          <button className="btn primary" onClick={handleStart} disabled={starting}>
            {starting ? 'Starting…' : 'Start Processing'}
          </button>
        </div>
      )}
    </div>
  );
}
