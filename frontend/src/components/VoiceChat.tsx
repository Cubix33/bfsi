// VoiceChat.tsx
import React, { useCallback, useEffect, useRef, useState } from "react";

type Props = {
  sessionId?: string | null;
  language?: string; // e.g. "en", "hi" etc.
  onAddMessage?: (role: "user" | "assistant", content: string) => void;
};

const VoiceChat: React.FC<Props> = ({ sessionId, language = "en", onAddMessage }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [reply, setReply] = useState("");

  // Using `any` because SpeechRecognition types can be missing in some TS setups
  const recognitionRef = useRef<any | null>(null);
  const mountedRef = useRef(true);
  const shouldContinueRef = useRef(false); // whether we should auto-restart after a result
  const voicesRef = useRef<SpeechSynthesisVoice[]>([]);
  const speakTimeoutRef = useRef<number | null>(null);
  const restartTimeoutRef = useRef<number | null>(null);
  const isSpeakingRef = useRef(false); // track if TTS is currently active
  const processingRef = useRef(false); // prevent concurrent API calls

  useEffect(() => {
    mountedRef.current = true;

    // Preload available voices for better locale matching
    const loadVoices = () => {
      const v = window.speechSynthesis?.getVoices?.() || [];
      if (v.length) {
        voicesRef.current = v;
      }
    };
    loadVoices();
    window.speechSynthesis?.addEventListener?.("voiceschanged", loadVoices);

    return () => {
      mountedRef.current = false;
      processingRef.current = false;
      isSpeakingRef.current = false;
      if (speakTimeoutRef.current) window.clearTimeout(speakTimeoutRef.current);
      if (restartTimeoutRef.current) window.clearTimeout(restartTimeoutRef.current);
      try {
        if (window.speechSynthesis?.speaking) {
          window.speechSynthesis.cancel();
        }
      } catch {}
      window.speechSynthesis?.removeEventListener?.("voiceschanged", loadVoices);
    };
  }, []);

  const getOrInitSessionId = (): string => {
    const key = "loan_session_id";
    let sid = localStorage.getItem(key);
    if (!sid) {
      sid = (crypto as any).randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`;
      localStorage.setItem(key, sid);
    }
    return sid;
  };

  // Unified locale resolver for recognition + synthesis
  const getLocale = (langCode: string): string => {
    const map: Record<string, string> = {
      en: "en-GB", // prefer UK English
      hi: "hi-IN",
      ta: "ta-IN",
      te: "te-IN",
      bn: "bn-IN",
      mr: "mr-IN",
      gu: "gu-IN",
    };
    return map[langCode] || "en-GB";
  };

  const speak = useCallback(
    (text: string, onEnd?: () => void) => {
      try {
        // Cancel any existing speech
        if (window.speechSynthesis && window.speechSynthesis.speaking) {
          window.speechSynthesis.cancel();
        }
        
        isSpeakingRef.current = true;
        const utter = new SpeechSynthesisUtterance(text);
        const locale = getLocale(language);
        utter.lang = locale;

        const voices = voicesRef.current.length
          ? voicesRef.current
          : window.speechSynthesis?.getVoices?.() || [];

        let preferredVoice =
          voices.find(v => v.lang === locale) ||
          voices.find(v => v.lang?.toLowerCase().startsWith(locale.toLowerCase())) ||
          null;

        if (!preferredVoice) {
          const tryMatch = (label: RegExp) => voices.find(v => label.test(v.lang) || label.test(v.name)) || null;
          if (/^hi-IN/i.test(locale)) preferredVoice = tryMatch(/Hindi|hi\-IN/i);
          else if (/^ta-IN/i.test(locale)) preferredVoice = tryMatch(/Tamil|ta\-IN/i);
          else if (/^te-IN/i.test(locale)) preferredVoice = tryMatch(/Telugu|te\-IN/i);
          else if (/^bn-IN/i.test(locale)) preferredVoice = tryMatch(/Bengali|Bangla|bn\-(IN|BD)/i);
          else if (/^mr-IN/i.test(locale)) preferredVoice = tryMatch(/Marathi|mr\-IN/i);
          else if (/^gu-IN/i.test(locale)) preferredVoice = tryMatch(/Gujarati|gu\-IN/i);
        }

        if (!preferredVoice) {
          preferredVoice =
            voices.find(v => /India/i.test(v.name || "") || /en\-IN/i.test(v.lang || "")) ||
            voices.find(v => /en\-GB/i.test(v.lang || "")) ||
            voices.find(v => /en\-/i.test(v.lang || "")) ||
            null;
        }

        if (!preferredVoice && voices.length) {
          preferredVoice = voices[0];
        }

        if (preferredVoice) {
          utter.voice = preferredVoice;
        }

        utter.rate = 0.95;
        
        const handleEnd = () => {
          isSpeakingRef.current = false;
          if (onEnd) onEnd();
        };
        
        utter.onend = handleEnd;
        utter.onerror = () => {
          isSpeakingRef.current = false;
        };
        
        if (speakTimeoutRef.current) {
          window.clearTimeout(speakTimeoutRef.current);
        }
        const tid = window.setTimeout(() => {
          window.speechSynthesis.speak(utter);
        }, 50); // Minimal delay for smoother flow
        speakTimeoutRef.current = tid;
      } catch (e) {
        isSpeakingRef.current = false;
        console.error("Speech synthesis error:", e);
      }
    },
    [language]
  );

  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      // eslint-disable-next-line no-console
      console.warn("SpeechRecognition not supported in this browser.");
      recognitionRef.current = null;
      return;
    }

    const recognition = new SpeechRecognition();

    const locale = getLocale(language);
    recognition.lang = locale;
    recognition.interimResults = true; // Enable interim results for instant feedback
    recognition.maxAlternatives = 1;
    recognition.continuous = true; // continuous listening until stopped

    recognition.onstart = () => {
      if (!mountedRef.current) return;
      setIsListening(true);
    };

    recognition.onresult = async (event: any) => {
      if (!mountedRef.current) return;
      
      try {
        // Find the latest final result
        let finalTranscript = "";
        let hasNewFinal = false;
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalTranscript = result[0].transcript.trim();
            hasNewFinal = true;
          }
        }
        
        // If user speaks while TTS is playing, interrupt it immediately
        if (isSpeakingRef.current) {
          try {
            window.speechSynthesis.cancel();
            isSpeakingRef.current = false;
          } catch {}
        }
        
        // Only process final results to avoid duplicates
        if (!hasNewFinal || !finalTranscript) return;
        
        // Prevent concurrent processing
        if (processingRef.current) return;
        processingRef.current = true;
        
        setTranscript(finalTranscript);

        // Add user message to chat
        if (onAddMessage) {
          onAddMessage("user", finalTranscript);
        }

        // Stop recognition completely during API call and TTS
        try {
          recognitionRef.current?.stop();
          setIsListening(false);
        } catch {}

        const finalSessionId = sessionId || getOrInitSessionId();

        // Call backend
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: finalTranscript, session_id: finalSessionId, language }),
        });

        if (!res.ok) {
          const plain = await res.text().catch(() => "");
          console.error("Chat API returned error:", res.status, plain);
          const fallback = "Sorry, something went wrong while contacting the server.";
          setReply(fallback);
          if (onAddMessage) {
            onAddMessage("assistant", fallback);
          }
          processingRef.current = false;
          
          speak(fallback, () => {
            if (shouldContinueRef.current && mountedRef.current) {
              setTimeout(() => {
                try {
                  recognitionRef.current?.start();
                  setIsListening(true);
                } catch {}
              }, 500);
            }
          });
          return;
        }

        const data = await res.json().catch(() => null);
        const replyText = data?.reply ?? "Sorry, I couldn't process that.";
        setReply(replyText);
        
        if (onAddMessage) {
          onAddMessage("assistant", replyText);
        }
        
        processingRef.current = false;
        
        // Speak and restart listening after TTS completes
        speak(replyText, () => {
          if (!mountedRef.current || !shouldContinueRef.current) return;
          
          // Wait a bit before restarting to avoid capturing echo
          if (restartTimeoutRef.current) {
            window.clearTimeout(restartTimeoutRef.current);
          }
          
          const rid = window.setTimeout(() => {
            if (!mountedRef.current || !shouldContinueRef.current) return;
            try {
              recognitionRef.current?.start();
              setIsListening(true);
            } catch (e) {
              console.warn("Failed to restart recognition:", e);
            }
          }, 500); // Longer delay to ensure clean restart
          
          restartTimeoutRef.current = rid;
        });
      } catch (e) {
        console.error("VoiceChat onresult error:", e);
        processingRef.current = false;
      }
    };

    recognition.onerror = (e: any) => {
      console.error("Speech recognition error:", e.error);
      if (!mountedRef.current) return;
      
      // Only restart on no-speech if we're not processing and should continue
      if (e.error === 'no-speech' && !processingRef.current && shouldContinueRef.current) {
        setTimeout(() => {
          if (shouldContinueRef.current && recognitionRef.current && !processingRef.current) {
            try {
              recognitionRef.current.start();
              setIsListening(true);
            } catch {}
          }
        }, 200);
        return;
      }
      
      // On other errors, only stop if not processing
      if (!processingRef.current) {
        setIsListening(false);
      }
    };

    recognition.onend = () => {
      if (!mountedRef.current) return;
      
      // Only restart if not processing (to avoid conflict with speak callback restart)
      if (shouldContinueRef.current && !processingRef.current && recognitionRef.current) {
        setTimeout(() => {
          if (!mountedRef.current || !shouldContinueRef.current || processingRef.current) return;
          try {
            recognitionRef.current.start();
            setIsListening(true);
          } catch (e) {
            console.warn("recognition.onend restart failed:", e);
          }
        }, 200);
        return;
      }
      
      if (!processingRef.current) {
        setIsListening(false);
      }
    };

    recognitionRef.current = recognition;

    // cleanup on unmount
    return () => {
      try {
        recognition.stop();
      } catch {}
      if (restartTimeoutRef.current) {
        window.clearTimeout(restartTimeoutRef.current);
        restartTimeoutRef.current = null;
      }
      recognitionRef.current = null;
    };
    // We intentionally exclude sessionId and getOrInitSessionId from deps to keep instance stable.
    // language and speak are included because recognition.lang depends on language and speak callback may change.
  }, [language, speak]);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      console.warn("SpeechRecognition not available.");
      return;
    }

    if (isListening) {
      // Stop listening
      shouldContinueRef.current = false;
      processingRef.current = false;
      
      if (restartTimeoutRef.current) {
        window.clearTimeout(restartTimeoutRef.current);
        restartTimeoutRef.current = null;
      }
      
      // Cancel any ongoing TTS
      try {
        if (window.speechSynthesis?.speaking) {
          window.speechSynthesis.cancel();
        }
        isSpeakingRef.current = false;
      } catch {}
      
      try {
        recognitionRef.current.stop();
        setIsListening(false);
      } catch (e) {
        console.warn("recognition.stop() failed:", e);
        setIsListening(false);
      }
    } else {
      // Start listening
      // Cancel any ongoing speech first
      if (window.speechSynthesis?.speaking) {
        window.speechSynthesis.cancel();
      }
      isSpeakingRef.current = false;
      processingRef.current = false;
      
      try {
        recognitionRef.current.abort();
      } catch {}

      shouldContinueRef.current = true;
      
      setTimeout(() => {
        try {
          recognitionRef.current.start();
          setIsListening(true);
        } catch (e) {
          console.warn("recognition.start() failed:", e);
          setIsListening(false);
          shouldContinueRef.current = false;
        }
      }, 100);
    }
  };

  return (
    <div className="flex items-center gap-2">
      {/* Circular mic button with Material Icons */}
      <button
        onClick={toggleListening}
        type="button"
        aria-label={isListening ? "Stop listening" : "Tap to speak"}
        className={`w-12 h-12 rounded-full shadow-md flex items-center justify-center transition-all ${
          isListening ? "ring-4 ring-red-500 animate-pulse scale-110" : "hover:scale-105"
        }`}
        style={{
          backgroundImage: "var(--gradient-primary)",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <span
          className={`material-symbols-outlined ${
            isListening ? "text-white" : "text-gray-200"
          }`}
          style={{ fontSize: "24px" }}
        >
          mic
        </span>
      </button>
      
      {isListening && (
        <span className="text-sm text-muted-foreground animate-pulse">
          Listening...
        </span>
      )}
    </div>
  );
};

export default VoiceChat;
