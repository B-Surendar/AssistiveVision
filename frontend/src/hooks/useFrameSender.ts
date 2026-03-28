import { useEffect, useRef, useCallback, useState } from "react";
import { ConnectionStatus } from "../types";

const WS_BASE = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
const WS_FRAME_URL = `${WS_BASE}/ws/frame`;

const FRAME_INTERVAL_MS = 200;
const RECONNECT_DELAY_MS = 3000;

interface UseFrameSenderReturn {
  videoRef: React.RefObject<HTMLVideoElement>;
  canvasRef: React.RefObject<HTMLCanvasElement>;
  frameStatus: ConnectionStatus;
  cameraError: string | null;
}

export function useFrameSender(): UseFrameSenderReturn {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const [frameStatus, setFrameStatus] = useState<ConnectionStatus>("connecting");
  const [cameraError, setCameraError] = useState<string | null>(null);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: false,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setCameraError(`Camera error: ${msg}`);
    }
  }, []);

  const connectWS = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current && wsRef.current.readyState < 2) return;

    setFrameStatus("connecting");
    const ws = new WebSocket(WS_FRAME_URL);
    wsRef.current = ws;

    ws.onopen = () => { if (mountedRef.current) setFrameStatus("connected"); };
    ws.onerror = () => { if (mountedRef.current) setFrameStatus("error"); };
    ws.onclose = () => {
      if (!mountedRef.current) return;
      setFrameStatus("disconnected");
      reconnectRef.current = setTimeout(connectWS, RECONNECT_DELAY_MS);
    };
  }, []);

  const sendFrame = useCallback(() => {
    const ws = wsRef.current;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    if (!video || video.readyState < 2 || !canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    canvas.width = 640;
    canvas.height = 480;
    ctx.drawImage(video, 0, 0, 640, 480);
    const b64 = canvas.toDataURL("image/jpeg", 0.7);
    ws.send(b64);
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    startCamera();
    connectWS();
    intervalRef.current = setInterval(sendFrame, FRAME_INTERVAL_MS);
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
      if (videoRef.current?.srcObject) {
        (videoRef.current.srcObject as MediaStream)
          .getTracks()
          .forEach((t) => t.stop());
      }
    };
  }, [startCamera, connectWS, sendFrame]);

  return { videoRef, canvasRef, frameStatus, cameraError };
}
