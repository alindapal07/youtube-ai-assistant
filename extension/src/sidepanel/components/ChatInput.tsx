import React, { KeyboardEvent, useState } from "react";
import { APP_LIMITS } from "../../shared/constants";

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  disabled: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled,
  placeholder = "Ask a question about the video...",
}) => {
  const [text, setText] = useState("");

  const handleSubmit = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSendMessage(trimmed);
    setText("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="chat-input-bar">
      <textarea
        className="chat-textarea"
        rows={1}
        value={text}
        onChange={(e) => setText(e.target.value.slice(0, APP_LIMITS.MAX_QUESTION_LENGTH))}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
      />
      <button
        className="chat-send-btn"
        onClick={handleSubmit}
        disabled={disabled || !text.trim()}
        title="Send (Enter)"
        aria-label="Send message"
      >
        <svg
          viewBox="0 0 24 24"
          width="18"
          height="18"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </div>
  );
};

