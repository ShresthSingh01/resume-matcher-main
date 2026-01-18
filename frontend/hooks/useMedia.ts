"use client";

import { useEffect, useRef, useState } from "react";

export function useMedia() {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [stream, setStream] = useState<MediaStream | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Audio Analysis
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const dataArrayRef = useRef<Uint8Array | null>(null);

    const initWebcam = async () => {
        try {
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: true // Needed for STT usually, but here we separate concerns? 
                // Actually, for visualizer we play BACKEND audio. 
                // For STT we need mic. Let's ask for both.
            });

            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
            return true;
        } catch (err: unknown) {
            console.error("Webcam init failed:", err);
            setError("Camera/Mic access denied. Please allow permissions.");
            return false;
        }
    };

    const initAudioContext = () => {
        if (!audioContextRef.current) {
            const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
            const ctx = new AudioCtx();
            const analyser = ctx.createAnalyser();
            analyser.fftSize = 256;

            audioContextRef.current = ctx;
            analyserRef.current = analyser;
            dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount);
        }
        // Resume if suspended
        if (audioContextRef.current?.state === "suspended") {
            audioContextRef.current.resume();
        }
    };

    const connectAudioSource = (sourceNode: MediaElementAudioSourceNode) => {
        if (analyserRef.current && audioContextRef.current) {
            sourceNode.connect(analyserRef.current);
            analyserRef.current.connect(audioContextRef.current.destination);
        }
    };

    const getAudioLevel = (): number => {
        if (!analyserRef.current || !dataArrayRef.current) return 1;

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        analyserRef.current.getByteFrequencyData(dataArrayRef.current as any);

        let sum = 0;
        for (let i = 0; i < dataArrayRef.current.length; i++) {
            sum += dataArrayRef.current[i];
        }
        const average = sum / dataArrayRef.current.length;
        // Scale: 1 to 1.5 usually good for CSS scale transform
        return 1 + (average / 255) * 0.5;
    };

    return {
        videoRef,
        stream,
        error,
        initWebcam,
        initAudioContext,
        audioContextRef,
        analyserRef,
        getAudioLevel,
    };
}
