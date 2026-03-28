import React, { useState, useEffect } from "react";
import { SceneProvider, useScene } from "./context/SceneContext";
import { useVoiceFeedback } from "./hooks/useVoiceFeedback";
import VideoFeed from "./components/VideoFeed";
import SceneCaption from "./components/SceneCaption";
import ObjectList from "./components/ObjectList";
import AssistantStatus from "./components/AssistantStatus";
import "./App.css";

const AppInner: React.FC = () => {
  const { sceneData, status } = useScene();
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const { speak } = useVoiceFeedback(voiceEnabled);

  useEffect(() => {
    if (sceneData?.caption) speak(sceneData.caption);
  }, [sceneData?.caption, speak]);

  return (
    <div className="app-root">
      <AssistantStatus
        status={status}
        voiceEnabled={voiceEnabled}
        onToggleVoice={() => setVoiceEnabled((v) => !v)}
      />
      <main className="app-main">
        <div className="left-col">
          <VideoFeed />
          <SceneCaption sceneData={sceneData} />
        </div>
        <div className="right-col">
          <ObjectList objects={sceneData?.objects ?? []} />
        </div>
      </main>
    </div>
  );
};

const App: React.FC = () => (
  <SceneProvider>
    <AppInner />
  </SceneProvider>
);

export default App;
