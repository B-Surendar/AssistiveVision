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
  isFrontCamera: boolean;
  toggleCamera: () => void;
}

export function useFrameSender(): UseFrameSenderReturn {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);
  const streamRef = useRef<MediaStream | null>(null);

  const [frameStatus, setFrameStatus] = useState<ConnectionStatus>("connecting");
  const [cameraError, setCameraError] = useState<string | null>(null);
  // Default: back camera (environment) for mobile
  const [isFrontCamera, setIsFrontCamera] = useState(false);

  const startCamera = useCallback(async (useFront: boolean) => {
    // Stop existing stream first
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          // "environment" = back camera, "user" = front camera
          facingMode: useFront ? "user" : "environment",
        },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setCameraError(null);
    } catch (err: unknown) {
      // Fallback: if back camera not found, try any camera
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false,
        });
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setCameraError(null);
      } catch (fallbackErr: unknown) {
        const msg = fallbackErr instanceof Error ? fallbackErr.message : String(fallbackErr);
        setCameraError(`Camera error: ${msg}`);
      }
    }
  }, []);

  const toggleCamera = useCallback(() => {
    setIsFrontCamera((prev) => {
      const next = !prev;
      startCamera(next);
      return next;
    });
  }, [startCamera]);

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
    // Start with back camera by default
    startCamera(false);
    connectWS();
    intervalRef.current = setInterval(sendFrame, FRAME_INTERVAL_MS);
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, [startCamera, connectWS, sendFrame]);

  return { videoRef, canvasRef, frameStatus, cameraError, isFrontCamera, toggleCamera };
}