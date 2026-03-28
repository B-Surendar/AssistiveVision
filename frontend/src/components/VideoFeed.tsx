import React from "react";
import { useFrameSender } from "../hooks/useFrameSender";

const VideoFeed: React.FC = () => {
  const { videoRef, canvasRef, cameraError } = useFrameSender();

  return (
    <div className="video-wrap">
      {cameraError && (
        <div className="camera-error">
          <span>⚠</span> {cameraError}
        </div>
      )}
      <video
        ref={videoRef}
        className="video-el"
        autoPlay
        muted
        playsInline
        aria-label="Live camera feed"
      />
      <canvas ref={canvasRef} style={{ display: "none" }} />
      <div className="video-corner-tl" />
      <div className="video-corner-tr" />
      <div className="video-corner-bl" />
      <div className="video-corner-br" />
    </div>
  );
};

export default VideoFeed;
