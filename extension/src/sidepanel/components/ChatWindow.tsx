import React, { useEffect, useRef } from "react";
import { ChatMessage as ChatMessageType } from "../types/chat";
import { ChatMessage } from "./ChatMessage";
import { LoadingIndicator } from "./LoadingIndicator";

interface ChatWindowProps {
  messages: ChatMessageType[];
  isLoading: boolean;
  isReady: boolean;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading,
  isReady,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0) {
    return (
      <div className="chat-window">
        <div className="chat-empty-state">
          <svg
            className="empty-state-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          <div style={{ fontWeight: 500, color: "var(--text-secondary)" }}>
            {isReady
              ? "Ask any question about this video"
              : "Process the video above to unlock AI chat & insights"}
          </div>
          <div style={{ fontSize: "12px" }}>
            {isReady
              ? "Answers are strictly grounded in the official transcript with timestamp citations."
              : "Transcripts are chunked and vectorized locally with FAISS."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-window">
      {messages.map((msg) => (
        <ChatMessage key={msg.id} message={msg} />
      ))}

      {isLoading && (
        <div className="chat-message-row assistant">
          <LoadingIndicator message="Analyzing transcript & generating grounded answer..." />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};

