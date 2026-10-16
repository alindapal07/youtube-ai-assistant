import React from "react";

interface HeaderProps {
  hasActiveVideo: boolean;
}

export const Header: React.FC<HeaderProps> = ({ hasActiveVideo }) => {
  return (
    <header className="app-header">
      <div className="header-brand">
        <svg
          className="header-logo"
          viewBox="0 0 24 24"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <rect width="24" height="24" rx="6" fill="#EF4444" />
          <path d="M10 8L16 12L10 16V8Z" fill="white" />
          <circle cx="18" cy="6" r="3" fill="#8B5CF6" />
        </svg>
        <h1 className="header-title">YouTube AI Assistant</h1>
      </div>

      <div className="header-status-badge">
        <span className={`status-dot ${hasActiveVideo ? "active" : ""}`} />
        <span>{hasActiveVideo ? "Video Connected" : "No Video"}</span>
      </div>
    </header>
  );
};

