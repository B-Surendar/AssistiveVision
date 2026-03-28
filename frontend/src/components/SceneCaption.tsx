import React, { useRef } from "react";
import { SceneData } from "../types";

interface Props {
  sceneData: SceneData | null;
}

const SceneCaption: React.FC<Props> = ({ sceneData }) => {
  const prevCaption = useRef<string>("");
  const caption = sceneData?.caption ?? "Waiting for scene analysis…";
  const isNew = caption !== prevCaption.current;
  if (isNew) prevCaption.current = caption;

  return (
    <section className="caption-panel" aria-live="assertive" aria-label="Scene description">
      <div className="caption-header">
        <span className="caption-icon" aria-hidden="true">◈</span>
        Scene Description
        {sceneData && (
          <span className={`conf-badge ${sceneData.confidence === "high" ? "conf-high" : "conf-low"}`}>
            {sceneData.confidence}
          </span>
        )}
      </div>

      <p className={`caption-text ${isNew ? "caption-flash" : ""}`} key={caption}>
        {caption}
      </p>

      {sceneData?.ocr && sceneData.ocr.length > 0 && (
        <div className="ocr-strip" aria-label="Visible text in scene">
          <span className="ocr-label">TEXT:</span>
          {sceneData.ocr.map((t) => (
            <span key={t} className="ocr-chip">{t}</span>
          ))}
        </div>
      )}
    </section>
  );
};

export default SceneCaption;
