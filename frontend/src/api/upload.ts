import { ApiError, UploadResponse } from './types';

const ALLOWED_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv'];
const API_BASE = import.meta.env.VITE_API_BASE || '/api';

export function validateVideoFile(file: File): string | null {
  const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `Unsupported file type "${ext}". Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
  }
  return null;
}

export function uploadVideo(
  file: File,
  onProgress: (percent: number) => void,
): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}/videos`);
    xhr.responseType = 'json';
    xhr.timeout = 300000; // 5 min timeout for large files

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && e.total > 0) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(xhr.response as UploadResponse);
        return;
      }
      let message = `Upload failed (${xhr.status})`;
      const body = xhr.response;
      if (body && typeof body.detail === 'string') message = body.detail;
      reject(new ApiError(message, xhr.status));
    };

    xhr.onerror = () => reject(new ApiError('Network error during upload', 0));
    xhr.ontimeout = () => reject(new ApiError('Upload timed out (5 min)', 0));

    const form = new FormData();
    form.append('file', file);
    xhr.send(form);
  });
}
