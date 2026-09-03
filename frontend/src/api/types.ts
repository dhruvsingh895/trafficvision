export interface UploadResponse {
  video_id: string;
  filename: string;
  status: string;
  size_bytes: number;
}

export interface VideoInfo {
  width: number;
  height: number;
  fps: number;
  frame_count: number;
  duration: number;
}

export interface ProcessLine {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface ProcessRequest {
  line_y_ratio?: number;
  line?: ProcessLine;
}

export interface ProcessResponse {
  job_id: string;
  video_id: string;
  status: string;
}

export type JobStatus = 'uploaded' | 'processing' | 'completed' | 'failed';

export interface StatusResponse {
  status: JobStatus;
  progress: number;
  frames_processed: number;
  total_frames: number;
  error: string | null;
}

export interface TimelinePoint {
  t: number;
  count: number;
}

export interface LiveStats {
  total: number;
  by_type: {
    car: number;
    motorcycle: number;
    bus: number;
    truck: number;
  };
  entering: number;
  exiting: number;
}

export interface LiveFrameEvent {
  frame: number;
  total: number;
  progress: number;
  stats: LiveStats;
  jpeg_b64: string;
}

export interface ResultsResponse {
  video_id: string;
  total: number;
  by_type: {
    car: number;
    motorcycle: number;
    bus: number;
    truck: number;
  };
  entering: number;
  exiting: number;
  processing_time_s: number;
  fps: number;
  processing_fps: number;
  timeline: TimelinePoint[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}
