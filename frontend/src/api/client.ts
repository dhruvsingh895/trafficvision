import {
  ApiError,
  LiveFrameEvent,
  ProcessRequest,
  ProcessResponse,
  ResultsResponse,
  StatusResponse,
  VideoInfo,
} from './types';

const BASE = '/api';

async function parseError(res: Response): Promise<never> {
  let message = `Request failed (${res.status})`;
  try {
    const data = await res.json();
    if (typeof data.detail === 'string') message = data.detail;
  } catch {
    /* keep default message */
  }
  throw new ApiError(message, res.status);
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) await parseError(res);
  return (await res.json()) as T;
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) await parseError(res);
  return (await res.json()) as T;
}

export function getHealth(): Promise<{ status: string }> {
  return get('/health');
}

export function getVideoInfo(videoId: string): Promise<VideoInfo> {
  return get(`/videos/${videoId}/info`);
}

export function startProcessing(
  videoId: string,
  req: ProcessRequest = {},
): Promise<ProcessResponse> {
  return post(`/videos/${videoId}/process`, req);
}

export function getVideoStatus(videoId: string): Promise<StatusResponse> {
  return get(`/videos/${videoId}/status`);
}

export function getVideoResults(videoId: string): Promise<ResultsResponse> {
  return get(`/videos/${videoId}/results`);
}

export function outputVideoUrl(videoId: string): string {
  return `${BASE}/videos/${videoId}/output`;
}

export function frameUrl(videoId: string, n: number): string {
  return `${BASE}/videos/${videoId}/frame?n=${n}`;
}

export function liveStream(
  videoId: string,
  lineYRatio: number,
  onFrame: (evt: LiveFrameEvent) => void,
  onError?: (err: Error) => void,
  onDone?: () => void,
): () => void {
  const es = new EventSource(`${BASE}/videos/${videoId}/live?line_y_ratio=${lineYRatio}`);
  es.addEventListener('frame', (e) => {
    try {
      onFrame(JSON.parse(e.data) as LiveFrameEvent);
    } catch {
      /* ignore malformed */
    }
  });
  es.addEventListener('progress', (e) => {
    try {
      const p = JSON.parse(e.data);
      onFrame({ frame: p.done, total: p.total, progress: Math.round(p.done / p.total * 100), stats: { total: 0, by_type: { car: 0, motorcycle: 0, bus: 0, truck: 0 }, entering: 0, exiting: 0 }, jpeg_b64: '' });
    } catch { /* ignore */ }
  });
  es.addEventListener('error', (e) => {
    const err = JSON.parse((e as MessageEvent).data || '{}');
    onError?.(new Error(err.detail || 'Stream error'));
    es.close();
  });
  es.addEventListener('done', () => {
    es.close();
    onDone?.();
  });
  es.onerror = () => {
    es.close();
    onError?.(new Error('Connection lost'));
  };
  return () => es.close();
}
