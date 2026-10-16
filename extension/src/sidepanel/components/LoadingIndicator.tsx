import React from "react";

interface LoadingIndicatorProps {
  message?: string;
}

export const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  message = "Thinking...",
}) => {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px", padding: "8px 0" }}>
      <span className="spinner" />
      <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>{message}</span>
    </div>
  );
};

