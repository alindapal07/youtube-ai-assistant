export interface SourceReference {
  text: string;
  start_seconds: number;
  end_seconds: number;
  video_url: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceReference[];
  timestamp: string;
  error?: boolean;
}

export interface ChatResponse {
  success: boolean;
  video_id: string;
  answer: string;
  sources: SourceReference[];
}

export interface VideoSummaryResponse {
  success: boolean;
  video_id: string;
  summary: string;
  sources: SourceReference[];
}

export interface StudyNotesResponse {
  success: boolean;
  video_id: string;
  notes: string;
  key_takeaways: string[];
  sources: SourceReference[];
}

export interface InterviewQuestionsResponse {
  success: boolean;
  video_id: string;
  questions: string[];
  sources: SourceReference[];
}

