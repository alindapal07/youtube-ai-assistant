export const MESSAGE_TYPES = {
  VIDEO_CHANGED: "VIDEO_CHANGED",
  GET_CURRENT_VIDEO: "GET_CURRENT_VIDEO",
  CURRENT_VIDEO_RESPONSE: "CURRENT_VIDEO_RESPONSE",
  PING: "PING",
  PONG: "PONG",
} as const;

export type MessageType = typeof MESSAGE_TYPES[keyof typeof MESSAGE_TYPES];

export interface VideoChangedPayload {
  videoId: string;
  url: string;
  title?: string;
}

export interface CurrentVideoResponsePayload {
  videoId: string | null;
  url: string | null;
  title?: string;
}

export interface ExtensionMessage<T = unknown> {
  type: MessageType;
  payload?: T;
}

