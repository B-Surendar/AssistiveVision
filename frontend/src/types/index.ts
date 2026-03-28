export interface DetectedObject {
  id: string;
  label: string;
  distance_m: number;
  direction: "approaching" | "moving away" | "stationary";
  confidence: number;
}

export interface SceneData {
  objects: DetectedObject[];
  ocr: string[];
  caption: string;
  confidence: "high" | "low";
  timestamp: number;
}

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";
