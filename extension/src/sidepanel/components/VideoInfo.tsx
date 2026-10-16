import React from "react";
import { ProcessingStatus } from "../hooks/useVideoProcessing";

interface VideoInfoProps {
  videoId: string | null;
  videoTitle: string | null;
  status: ProcessingStatus;
  indexed: boolean;
  chunksCount: number | null;
  error: string | null;
  onProcess: () => void;
  onRetry: () => void;
}

export const VideoInfo: React.FC<VideoInfoProps> = ({
  videoId,
  videoTitle,
  status,
  indexed,
  chunksCount,
  error,
  onProcess,
  onRetry,
}) => {
  if (!videoId) {
    return (
      <div className="video-info-card">
        <div style={{ color: "var(--text-muted)", fontSize: "13px", textAlign: "center", padding: "8px 0" }}>
          Open any YouTube video to start analyzing its transcript.
        </div>
      </div>
    );
  }

  return (
    <div className="video-info-card">
      <div className="video-info-header">
        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="video-title-text" title={videoTitle || videoId}>
            {videoTitle || `YouTube Video (${videoId})`}
          </div>
        </div>
        <span className="video-id-badge">{videoId}</span>
      </div>

      <div className="video-status-row">
        <div>
          {status === "checking" && (
            <span style={{ color: "var(--text-muted)", fontSize: "12px" }}>
              Checking index status...
            </span>
          )}

          {status === "processing" && (
            <span style={{ color: "var(--accent-purple)", fontSize: "12px", display: "inline-flex", alignItems: "center", gap: "6px" }}>
              <span className="spinner" /> Indexing transcript chunks...
            </span>
          )}

          {status === "ready" && indexed && (
            <span className="badge-ready">
              ✓ Ready ({chunksCount || 0} chunks indexed)
            </span>
          )}

          {status === "idle" && !indexed && (
            <span className="badge-unprocessed">Transcript not processed</span>
          )}

          {status === "error" && (
            <span style={{ color: "var(--danger)", fontSize: "12px" }}>
              Processing failed
            </span>
          )}
        </div>

        <div>
          {status === "idle" && !indexed && (
            <button className="btn-primary" onClick={onProcess}>
              Process Video
            </button>
          )}

          {status === "error" && (
            <button className="btn-secondary" onClick={onRetry}>
              Retry
            </button>
          )}
        </div>
      </div>

      {error && (
        <div style={{ fontSize: "11px", color: "var(--danger)", marginTop: "2px" }}>
          {error}
        </div>
      )}
    </div>
  );
};

