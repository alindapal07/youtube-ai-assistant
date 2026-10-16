export interface VideoMetadata {
  video_id: string;
  video_url: string;
  language: string;
  is_generated: boolean;
  total_chunks: number;
  created_at: string;
  expires_at?: string;
}

export interface VideoInfoResponse {
  video_id: string;
  title?: string;
  status: "ready" | "not_indexed";
  indexed: boolean;
  chunks_count: number | null;
  metadata?: VideoMetadata;
}

export interface VideoProcessResponse {
  success: boolean;
  video_id: string;
  title?: string;
  status: string;
  chunks_created: number;
  cached: boolean;
}

