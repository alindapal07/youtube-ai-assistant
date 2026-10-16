import React from "react";

interface ErrorBannerProps {
  message: string;
  onDismiss?: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ message, onDismiss }) => {
  return (
    <div className="error-banner">
      <div style={{ flex: 1 }}>{message}</div>
      {onDismiss && (
        <button
          className="error-banner-close"
          onClick={onDismiss}
          title="Dismiss"
          aria-label="Dismiss error"
        >
          ✕
        </button>
      )}
    </div>
  );
};

