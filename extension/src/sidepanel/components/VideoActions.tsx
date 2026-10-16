import React from "react";

interface VideoActionsProps {
  onSummarize: () => void;
  onGenerateNotes: () => void;
  onGenerateQuestions: () => void;
  onClear: () => void;
  disabled: boolean;
}

export const VideoActions: React.FC<VideoActionsProps> = ({
  onSummarize,
  onGenerateNotes,
  onGenerateQuestions,
  onClear,
  disabled,
}) => {
  return (
    <div className="actions-toolbar">
      <button
        className="action-chip"
        onClick={onSummarize}
        disabled={disabled}
        title="Generate concise executive summary"
      >
        ⚡ Summarize
      </button>

      <button
        className="action-chip"
        onClick={onGenerateNotes}
        disabled={disabled}
        title="Generate structured study notes and key takeaways"
      >
        📝 Study Notes
      </button>

      <button
        className="action-chip"
        onClick={onGenerateQuestions}
        disabled={disabled}
        title="Generate grounded interview and revision questions"
      >
        🎯 Interview Qs
      </button>

      <button
        className="action-chip"
        onClick={onClear}
        disabled={disabled}
        title="Clear chat messages for this video"
      >
        🗑 Clear
      </button>
    </div>
  );
};

