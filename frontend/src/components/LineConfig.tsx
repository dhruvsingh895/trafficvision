import { MouseEvent, useRef, useState } from 'react';
import { frameUrl } from '../api/client';
import './LineConfig.css';

interface Props {
  videoId: string;
  ratio: number;
  onChange: (ratio: number) => void;
}

export default function LineConfig({ videoId, ratio, onChange }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dragging, setDragging] = useState(false);
  const [imgError, setImgError] = useState(false);

  const updateFromEvent = (e: MouseEvent) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect || rect.height === 0) return;
    const y = Math.min(Math.max(e.clientY - rect.top, 0), rect.height);
    onChange(Number((y / rect.height).toFixed(4)));
  };

  return (
    <div className="line-config">
      <h3>Counting Line</h3>
      <p className="hint">Drag the line to set where vehicles are counted.</p>
      <div
        ref={containerRef}
        className={`line-container ${dragging ? 'dragging' : ''}`}
        onMouseDown={(e) => {
          setDragging(true);
          updateFromEvent(e);
        }}
        onMouseMove={(e) => dragging && updateFromEvent(e)}
        onMouseUp={() => setDragging(false)}
        onMouseLeave={() => setDragging(false)}
      >
        {imgError ? (
          <div className="frame-fallback">Frame preview unavailable</div>
        ) : (
          <img
            src={frameUrl(videoId, 0)}
            alt="First frame preview"
            draggable={false}
            onError={() => setImgError(true)}
          />
        )}
        <div className="line-overlay" style={{ top: `${ratio * 100}%` }} />
      </div>
      <p className="line-value">Line position: {(ratio * 100).toFixed(1)}% from top</p>
    </div>
  );
}
