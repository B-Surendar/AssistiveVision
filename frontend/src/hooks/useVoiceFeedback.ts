import { useCallback, useRef } from "react";

export function useVoiceFeedback(enabled: boolean) {
  const lastSpokenRef = useRef<string>("");
  const cooldownRef = useRef<boolean>(false);

  const speak = useCallback(
    (text: string) => {
      if (!enabled) return;
      if (!text || text === lastSpokenRef.current) return;
      if (cooldownRef.current) return;
      if (!("speechSynthesis" in window)) return;

      lastSpokenRef.current = text;
      cooldownRef.current = true;

      window.speechSynthesis.cancel();
      const utt = new SpeechSynthesisUtterance(text);
      utt.rate = 1.1;
      utt.pitch = 1.0;
      utt.volume = 1.0;
      utt.lang = "en-US";
      utt.onend = () => {
        setTimeout(() => { cooldownRef.current = false; }, 2000);
      };
      window.speechSynthesis.speak(utt);
    },
    [enabled]
  );

  return { speak };
}
