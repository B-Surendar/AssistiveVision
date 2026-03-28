import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useCallback,
} from "react";
import { SceneData, ConnectionStatus } from "../types";

// Production: uses VITE_WS_URL from Vercel env variables
// Development: falls back to localhost
const WS_BASE = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
const WS_SCENE_URL = `${WS_BASE}/ws/scene`;

const RECONNECT_DELAY_MS = 2500;

interface SceneContextValue {
  sceneData: SceneData | null;
  status: ConnectionStatus;
}

const SceneContext = createContext<SceneContextValue>({
  sceneData: null,
  status: "disconnected",
});

export const SceneProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sceneData, setSceneData] = useState<SceneData | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    if (wsRef.current && wsRef.current.readyState < 2) return;

    setStatus("connecting");
    const ws = new WebSocket(WS_SCENE_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) return;
      setStatus("connected");
    };

    ws.onmessage = (ev: MessageEvent) => {
      if (!mountedRef.current) return;
      try {
        const data: SceneData = JSON.parse(ev.data as string);
        setSceneData(data);
      } catch {
        // ignore malformed
      }
    };

    ws.onerror = () => {
      if (!mountedRef.current) return;
      setStatus("error");
    };

    ws.onclose = () => {
      if (!mountedRef.current) return;
      setStatus("disconnected");
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY_MS);
    };
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return (
    <SceneContext.Provider value={{ sceneData, status }}>
      {children}
    </SceneContext.Provider>
  );
};

export const useScene = () => useContext(SceneContext);
