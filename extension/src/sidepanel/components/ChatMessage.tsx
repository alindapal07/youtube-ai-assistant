import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import { ChatMessage as ChatMessageType, SourceReference } from "../types/chat";

interface ChatMessageProps {
  message: ChatMessageType;
}

function formatTimestamp(seconds: number): string {
  const total = Math.floor(seconds);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s < 10 ? "0" : ""}${s}`;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.warn("Failed to copy message:", err);
    }
  };

  const handleSourceClick = (e: React.MouseEvent, source: SourceReference) => {
    e.preventDefault();
    if (typeof chrome !== "undefined" && chrome.tabs && chrome.tabs.update) {
      chrome.tabs.update({ url: source.video_url });
    } else {
      window.open(source.video_url, "_blank");
    }
  };

  return (
    <div
      className={`chat-message-row ${isUser ? "user" : "assistant"} ${
        message.error ? "error" : ""
      }`}
    >
      <div className={`message-bubble ${!isUser ? "markdown-body" : ""}`}>
        {isUser ? (
          message.content
        ) : (
          <ReactMarkdown
            components={{
              a: ({ href, children }) => (
                <a href={href} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
              code: ({ className, children, ...props }) => {
                const match = /language-(\w+)/.exec(className || "");
                const isInline = !match && !String(children).includes("\n");
                return isInline ? (
                  <code className="inline-code" {...props}>
                    {children}
                  </code>
                ) : (
                  <div className="code-block-wrapper">
                    <pre className="code-pre">
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </pre>
                  </div>
                );
              },
            }}
          >
            {message.content}
          </ReactMarkdown>
        )}
      </div>

      <div className="message-meta-row">
        <span>
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>

        {!isUser && !message.error && (
          <button className="copy-btn" onClick={handleCopy} title="Copy answer">
            {copied ? "✓ Copied" : "Copy"}
          </button>
        )}
      </div>

      {message.sources && message.sources.length > 0 && (
        <div className="message-sources-container">
          <div className="sources-header">Verified Video Citations:</div>
          <div className="sources-list">
            {message.sources.map((src, idx) => (
              <a
                key={idx}
                href={src.video_url}
                className="source-chip"
                onClick={(e) => handleSourceClick(e, src)}
                title={`Excerpt: "${src.text.slice(0, 80)}..."`}
              >
                ⏱ {formatTimestamp(src.start_seconds)} - {formatTimestamp(src.end_seconds)}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
