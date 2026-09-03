import { DragEvent, useRef, useState } from 'react';
import { validateVideoFile } from '../api/upload';
import './DropZone.css';

interface Props {
  onFile: (file: File) => void;
  disabled?: boolean;
}

export default function DropZone({ onFile, disabled }: Props) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File | undefined) => {
    if (!file) return;
    const err = validateVideoFile(file);
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    onFile(file);
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (disabled) return;
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div>
      <div
        className={`dropzone ${dragging ? 'dragging' : ''} ${disabled ? 'disabled' : ''}`}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        role="button"
        tabIndex={0}
      >
        <p className="dropzone-title">Drag &amp; drop a video here</p>
        <p className="dropzone-sub">or click to browse (.mp4, .avi, .mov, .mkv)</p>
        <input
          ref={inputRef}
          type="file"
          accept=".mp4,.avi,.mov,.mkv,video/*"
          hidden
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}
