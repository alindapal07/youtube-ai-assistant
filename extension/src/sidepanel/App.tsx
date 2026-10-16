import React from "react";
import { Header } from "./components/Header";
import { VideoInfo } from "./components/VideoInfo";
import { VideoActions } from "./components/VideoActions";
import { ChatWindow } from "./components/ChatWindow";
import { ChatInput } from "./components/ChatInput";
import { ErrorBanner } from "./components/ErrorBanner";
import { useCurrentVideo } from "./hooks/useCurrentVideo";
import { useVideoProcessing } from "./hooks/useVideoProcessing";
import { useChat } from "./hooks/useChat";

export const App: React.FC = () => {
  const { videoId, title: currentVideoTitle } = useCurrentVideo();

  const {
    status: processingStatus,
    indexed,
    chunksCount,
    error: processingError,
    processVideo,
    retry: retryProcessing,
    title: backendTitle,
  } = useVideoProcessing(videoId);

  const displayTitle = backendTitle || currentVideoTitle;

  const {
    messages,
    isLoading: isChatLoading,
    error: chatError,
    sendMessage,
    requestSummary,
    requestNotes,
    requestQuestions,
    clearMessages,
  } = useChat(videoId);

  const isReady = indexed && processingStatus === "ready";
  const actionsDisabled = !isReady || isChatLoading;

  return (
    <>
      <Header hasActiveVideo={!!videoId} />

      <VideoInfo
        videoId={videoId}
        videoTitle={displayTitle}
        status={processingStatus}
        indexed={indexed}
        chunksCount={chunksCount}
        error={processingError}
        onProcess={() => processVideo("en")}
        onRetry={retryProcessing}
      />

      {isReady && (
        <VideoActions
          onSummarize={requestSummary}
          onGenerateNotes={requestNotes}
          onGenerateQuestions={requestQuestions}
          onClear={clearMessages}
          disabled={actionsDisabled}
        />
      )}

      {chatError && <ErrorBanner message={chatError} />}

      <ChatWindow
        messages={messages}
        isLoading={isChatLoading}
        isReady={isReady}
      />

      <ChatInput
        onSendMessage={sendMessage}
        disabled={!isReady || isChatLoading}
        placeholder={
          isReady
            ? "Ask a question about the video transcript..."
            : "Process the video to ask questions..."
        }
      />
    </>
  );
};

export default App;

