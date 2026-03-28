import React from "react";
import { ConnectionStatus } from "../types";

interface Props {
  status: ConnectionStatus;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
}

const STATUS_LABELS: Record<ConnectionStatus, string> = {
  connecting: "Connecting…",
  connected: "Live",
  disconnected: "Disconnected",
  error: "Error",
};

const STATUS_CLASS: Record<ConnectionStatus, string> = {
  connecting: "status-connecting",
  connected: "status-connected",
  disconnected: "status-disconnected",
  error: "status-error",
};

const AssistantStatus: React.FC<Props> = ({ status, voiceEnabled, onToggleVoice }) => (
  <div className="status-bar" role="status" aria-live="polite">
    <div className={`status-dot-wrap ${STATUS_CLASS[status]}`}>
      <span className="status-dot" />
      <span className="status-label">{STATUS_LABELS[status]}</span>
    </div>

    <div className="status-title">
      <span className="eye-icon" aria-hidden="true">⬡</span>
      <span>AssistiveVision</span>
    </div>

    <button
      className={`voice-btn ${voiceEnabled ? "voice-on" : "voice-off"}`}
      onClick={onToggleVoice}
      aria-label={voiceEnabled ? "Disable voice feedback" : "Enable voice feedback"}
    >
      {voiceEnabled ? "🔊 Voice ON" : "🔇 Voice OFF"}
    </button>
  </div>
);

export default AssistantStatus;
