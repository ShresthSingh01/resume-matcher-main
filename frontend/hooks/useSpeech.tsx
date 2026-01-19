"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { useMedia } from "./useMedia";

// Type definition for Web Speech API
interface SpeechRecognitionResult {
    isFinal: boolean;
    [key: number]: { transcript: string };
}
interface SpeechRecognitionEvent {
    resultIndex: number;
    results: SpeechRecognitionResult[];
    error: string;
}

interface IWindow extends Window {
    webkitSpeechRecognition: any;
    SpeechRecognition: any;
}

export function useSpeech(
    onTranscriptChange: (text: string) => void,
    onSilence: () => void
) {
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const recognitionRef = useRef(null);
    const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
    const currentAudioRef = useRef<HTMLAudioElement | null>(null);

    // Configuration
    const SILENCE_DELAY = 3000; // 3 seconds silence -> auto submit

    useEffect(() => {
        // Init Recognition
        const { webkitSpeechRecognition, SpeechRecognition } = window as unknown as IWindow;
        const SpeechRecognitionClass = SpeechRecognition || webkitSpeechRecognition;

        if (SpeechRecognitionClass) {
            const recognition = new SpeechRecognitionClass();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = "en-US";

            recognition.onstart = () => setIsListening(true);

            recognition.onend = () => {
                setIsListening(false);
                // If simply stopped, good. Using continuous means it triggers less often.
            };

            recognition.onerror = (event: SpeechRecognitionEvent) => {
                console.warn("STT Error:", event.error);
                if (event.error === "not-allowed") {
                    setError("Microphone access blocked.");
                }
            };

            recognition.onresult = (event: SpeechRecognitionEvent) => {
                let fullTranscript = "";
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const results = event.results as any;
                // Casting to any because TS DOM types for SpeechRecognition are flaky or missing in default lib

                for (let i = 0; i < results.length; ++i) {
                    fullTranscript += results[i][0].transcript;
                }

                // Update parent with text
                onTranscriptChange(fullTranscript);

                // Silence Detection
                if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);

                if (fullTranscript.trim().length > 0) {
                    silenceTimerRef.current = setTimeout(() => {
                        console.log("Silence detected.");
                        recognition.stop();
                        onSilence();
                    }, SILENCE_DELAY);
                }
            };

            recognitionRef.current = recognition;
        } else {
            setError("Speech Recognition not supported in this browser.");
        }
    }, [onTranscriptChange, onSilence]);

    const startListening = () => {
        if (recognitionRef.current && !isListening) {
            try {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (recognitionRef.current as any).start();
                setError(null);
            } catch (e) {
                // sometimes it's already started
                console.warn(e);
            }
        }
    };

    const stopListening = () => {
        if (recognitionRef.current && isListening) {
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (recognitionRef.current as any).stop();
            if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
        }
    };

    const speak = async (text: string, audioCtx: AudioContext | null, analyser: AnalyserNode | null) => {
        setIsSpeaking(true);

        // Stop any current audio
        if (currentAudioRef.current) {
            currentAudioRef.current.pause();
            currentAudioRef.current = null;
        }

        window.speechSynthesis.cancel();

        try {
            // 1. Backend TTS
            const res = await fetch("/api/interview/speak", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text }),
            });

            if (!res.ok) throw new Error("Backend TTS Failed");

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);

            // Connect to Visualizer if Context Available
            if (audioCtx && analyser) {
                // Need to wait for audio element payload? 
                // createMediaElementSource requires the audio element to be in the DOM or playing?
                // Actually, we need to handle the async nature and user interaction requirements usually.
                // Assuming context is resumed.

                const source = audioCtx.createMediaElementSource(audio);
                source.connect(analyser);
                analyser.connect(audioCtx.destination);
            }

            audio.onended = () => setIsSpeaking(false);

            // Handle Auto-Play Policies
            audio.play().catch(playError => {
                console.warn("Auto-play blocked:", playError);
                // If blocked, fallback to browser TTS which might have different permissions or just fail
                // But better to just try browser TTS as backup
                // setIsSpeaking(false); // Removed to keep speaking state active during fallback
                const utter = new SpeechSynthesisUtterance(text);
                utter.onend = () => setIsSpeaking(false);
                window.speechSynthesis.speak(utter);
            });

            currentAudioRef.current = audio;

        } catch (e) {
            console.warn("Using Fallback TTS", e);
            // 2. Browser Fallback
            const utter = new SpeechSynthesisUtterance(text);
            utter.onend = () => setIsSpeaking(false);
            window.speechSynthesis.speak(utter);
        }
    };

    const stopSpeaking = () => {
        if (currentAudioRef.current) {
            currentAudioRef.current.pause();
            currentAudioRef.current = null;
        }
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
    };

    return {
        isListening,
        isSpeaking,
        startListening,
        stopListening,
        speak,
        stopSpeaking,
        error
    };
}
