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
  const videoRef   = useRef<HTMLVideoElement>(null);
  const canvasRef  = useRef<HTMLCanvasElement>(null);
  const wsRef      = useRef<WebSocket | null>(null);
  const intervalRef   = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectRef  = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef    = useRef(true);
  const streamRef     = useRef<MediaStream | null>(null);
  // track whether camera is mid-switch so sendFrame skips those frames
  const switchingRef  = useRef(false);

  const [frameStatus,  setFrameStatus]  = useState<ConnectionStatus>("connecting");
  const [cameraError,  setCameraError]  = useState<string | null>(null);
  const [isFrontCamera, setIsFrontCamera] = useState(false);

  // ── WebSocket (completely independent of camera) ──────────────────────────
  const connectWS = useCallback(() => {
    if (!mountedRef.current) return;
    // Already open or connecting — don't create a second socket
    if (wsRef.current && wsRef.current.readyState < 2) return;

    setFrameStatus("connecting");
    const ws = new WebSocket(WS_FRAME_URL);
    wsRef.current = ws;

    ws.onopen  = () => { if (mountedRef.current) setFrameStatus("connected"); };
    ws.onerror = () => { if (mountedRef.current) setFrameStatus("error"); };
    ws.onclose = () => {
      if (!mountedRef.current) return;
      setFrameStatus("disconnected");
      // Auto-reconnect — camera state is irrelevant here
      reconnectRef.current = setTimeout(connectWS, RECONNECT_DELAY_MS);
    };
  }, []);

  // ── Camera start (does NOT touch WebSocket at all) ────────────────────────
  const startCamera = useCallback(async (useFront: boolean) => {
    switchingRef.current = true;

    // Stop previous tracks cleanly
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }

    // Detach old stream from video element to avoid flicker errors
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width:  { ideal: 640 },
          height: { ideal: 480 },
          facingMode: useFront ? "user" : "environment",
        },
        audio: false,
      });
      streamRef.current = stream;

      if (videoRef.current && mountedRef.current) {
        videoRef.current.srcObject = stream;
        // Wait for video to be ready before resuming frame sends
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play().catch(() => {});
          switchingRef.current = false;
        };
      } else {
        switchingRef.current = false;
      }
      setCameraError(null);

    } catch {
      // Fallback: try any available camera
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false,
        });
        streamRef.current = stream;
        if (videoRef.current && mountedRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.onloadedmetadata = () => {
            videoRef.current?.play().catch(() => {});
            switchingRef.current = false;
          };
        } else {
          switchingRef.current = false;
        }
        setCameraError(null);
      } catch (fallbackErr: unknown) {
        switchingRef.current = false;
        const msg = fallbackErr instanceof Error ? fallbackErr.message : String(fallbackErr);
        setCameraError(`Camera error: ${msg}`);
      }
    }
  }, []);

  // ── Toggle camera (only affects camera, never touches WebSocket) ──────────
  const toggleCamera = useCallback(() => {
    setIsFrontCamera((prev) => {
      const next = !prev;
      startCamera(next);   // WebSocket keeps running unchanged
      return next;
    });
  }, [startCamera]);

  // ── Frame sender — skips frames while camera is switching ─────────────────
  const sendFrame = useCallback(() => {
    // Skip if switching cameras — avoids sending a black / corrupt frame
    if (switchingRef.current) return;

    const ws     = wsRef.current;
    const video  = videoRef.current;
    const canvas = canvasRef.current;

    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    if (!video || video.readyState < 2 || !canvas)  return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width  = 640;
    canvas.height = 480;
    ctx.drawImage(video, 0, 0, 640, 480);
    const b64 = canvas.toDataURL("image/jpeg", 0.7);
    ws.send(b64);
  }, []);

  // ── Lifecycle ─────────────────────────────────────────────────────────────
  useEffect(() => {
    mountedRef.current = true;

    // Start camera and WebSocket independently
    startCamera(false);   // back camera by default
    connectWS();

    // Frame send loop — runs regardless of camera state
    intervalRef.current = setInterval(sendFrame, FRAME_INTERVAL_MS);

    return () => {
      mountedRef.current = false;
      if (intervalRef.current)  clearInterval(intervalRef.current);
      if (reconnectRef.current) clearTimeout(reconnectRef.current);
      wsRef.current?.close();
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, [startCamera, connectWS, sendFrame]);

  return { videoRef, canvasRef, frameStatus, cameraError, isFrontCamera, toggleCamera };
}