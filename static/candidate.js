
// candidate.js - Dedicated logic for Interview Portal

// State
let sessionData = null;
let synthesis = window.speechSynthesis;
let audioContext = null;
let analyser = null;
let currentAudio = null;
let recognition = null;
let isRecording = false;

// Anti-Cheat & Timer State
let timerInterval = null;
let timeLeft = 40; // Ring 2: Reduced to 40s
let cheatingWarnings = 0;
const TIME_LIMIT = 40;
let handsFreeMode = true;

document.addEventListener('DOMContentLoaded', () => {
    setupInterview();

    // Check for candidate_id in URL
    const urlParams = new URLSearchParams(window.location.search);
    const candidateId = urlParams.get('candidate_id');

    // UI Elements
    const startBtn = document.getElementById('start-btn');
    const landingSection = document.getElementById('landing-section');
    const interviewSection = document.getElementById('interview-section');

    if (candidateId) {
        console.log("Candidate identified:", candidateId);

        // Check if already completed
        checkIfCompleted(candidateId);

        // Setup Start Button
        if (startBtn) {
            console.log("Start button found, attaching listener");
            startBtn.onclick = async () => {
                console.log("Start button clicked");

                // Ring 1: Fullscreen (Must be first for user gesture)
                try {
                    await document.documentElement.requestFullscreen();
                } catch (e) {
                    console.warn("Fullscreen denied - attempting to proceed anyway", e);
                }

                // Ring 3: Webcam init
                // Ring 3: Webcam init
                try {
                    await initWebcam();
                    // Initialize Audio Logic on User Gesture
                    setupAudioContext();
                    if (audioContext && audioContext.state === 'suspended') {
                        await audioContext.resume();
                    }
                } catch (e) {
                    console.error("Init failed", e);
                    alert("Camera/Audio access required.");
                    return;
                }

                landingSection.classList.add('hidden');
                interviewSection.classList.remove('hidden');
                document.getElementById('webcam-container').classList.remove('hidden');

                // Initialize Interview
                startInterview(candidateId);
            };
        }
    } else {
        document.getElementById('welcome-msg').textContent = "Error: Invalid Interview Link";
        startBtn.disabled = true;
        alert("No candidate ID found. Please use the link provided in your email.");
    }
});

// ---------- Interview Logic ----------

async function startInterview(candidateId) {
    try {
        // Call backend with candidate_id only
        // The backend /interview/start needs to support fetching context from DB if only candidate_id is provided.
        // Let's verify if backend supports this. 
        // Looking at main.py: start_interview(request: StartInterviewRequest)
        // schema: candidate_id is optional. 
        // interview_manager.create_session uses existing data if passed, 
        // BUT if we only pass candidate_id, the manager needs to look it up.
        // We might need to update the backend to support "Start by ID" fully or fetch data first.
        // Assuming we update backend to handle this:

        const res = await fetch('/interview/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ candidate_id: candidateId })
        });

        const data = await res.json();

        if (!res.ok) {
            console.error("Backend Error:", data);

            if (res.status === 403) {
                addMessage('system', `<div style="color:red; font-weight:bold;">${data.detail}</div>`, true);
                const startBtn = document.getElementById('start-btn');
                if (startBtn) startBtn.disabled = true;
                alert(data.detail);
                return;
            }

            addMessage('system', `Error: ${data.detail || data.error || "Unknown backend error"}`);
            return;
        }

        sessionData = { id: data.session_id };

        // Clear previous messages
        document.getElementById('chat-container').innerHTML = '';

        if (data.question) {
            addMessage('ai', data.question);
            speak(data.question);
        } else {
            addMessage('system', "Welcome. Retrieving your profile...");
        }

    } catch (err) {
        alert("Failed to start interview: " + err);
    }
}

async function showFinalResult(sessionId) {
    try {
        const res = await fetch('/interview/result', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        const data = await res.json();

        // Hide Interview, Show Report
        document.getElementById('interview-section').classList.add('hidden');
        document.getElementById('report-section').classList.remove('hidden');

        // Populate Scores
        const scoreEl = document.getElementById('final-interview-score');
        if (scoreEl) scoreEl.textContent = data.interview_score;

        document.getElementById('report-motivation').textContent = "Interview Complete. Here is your analysis.";

        // Populate Roles
        const roleContainer = document.getElementById('report-roles');
        if (roleContainer) {
            // Use detected role or fallback
            const role = data.role || "Software Engineer";
            roleContainer.innerHTML = `<div class="tag">${role}</div>`;
            fetchJobs(role);
        }

        // Populate Detailed Breakdown
        const breakdownContainer = document.getElementById('report-breakdown');
        if (breakdownContainer && data.transcript) {
            breakdownContainer.innerHTML = '';
            data.transcript.forEach((item, index) => {
                const card = document.createElement('div');
                card.className = 'card';
                card.style.marginBottom = '1rem';
                card.style.background = 'rgba(255,255,255,0.8)';
                card.innerHTML = `
                    <div style="margin-bottom:0.5rem; font-weight:bold; color:var(--text-muted);">Question ${index + 1}</div>
                    <div style="margin-bottom:1rem; font-style:italic;">"${item.q}"</div>
                    <div style="margin-bottom:1rem; padding-left:1rem; border-left:2px solid var(--primary);">"${item.a}"</div>
                    
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; font-size:0.9rem;">
                        <div>
                            <div style="color:var(--success)">Score</div>
                            <div>${item.score}/10</div>
                        </div>
                        <div style="grid-column:1/-1;">
                            <div style="color:var(--accent)">Feedback</div>
                            <div>${item.feedback || '-'}</div>
                        </div>
                    </div>
                `;
                breakdownContainer.appendChild(card);
            });
        }

        // Add Download Button
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'btn btn-primary';
        downloadBtn.innerHTML = 'Download Full Report <ion-icon name="download-outline"></ion-icon>';
        downloadBtn.style.marginTop = '2rem';
        downloadBtn.onclick = () => downloadReport(data);

        if (breakdownContainer && breakdownContainer.parentElement) {
            breakdownContainer.parentElement.appendChild(downloadBtn);
        }

    } catch (e) {
        console.error(e);
        alert("Error generating report.");
    }
}

async function checkIfCompleted(candidateId) {
    try {
        const res = await fetch(`/candidates/${candidateId}/status`);
        const data = await res.json();

        if (data.status === 'completed') {
            console.log("Candidate already completed. Showing results.");
            // Hide landing, show result
            document.getElementById('landing-section').classList.add('hidden');
            // We can trigger showFinalResult if we had a sessionId, 
            // OR we need to load a simple completed view or re-fetch report.
            // Since /interview/result generally needs a session_id, we should probably 
            // update that endpoint OR just show a generic "Completed" screen if we can't find the session.
            // Ideally /candidates/{id}/status returns enough info to render the score.

            // Simple version: Render report using data from status
            if (data.interview_score !== undefined) {
                document.getElementById('report-section').classList.remove('hidden');
                document.getElementById('final-interview-score').textContent = data.interview_score;
                document.getElementById('report-motivation').textContent = "You have already completed this interview.";
                document.getElementById('report-breakdown').innerHTML = '<div style="text-align:center; padding:2rem;">Full report available with Recruiter.</div>';
                // Hide start button just in case
                const startBtn = document.getElementById('start-btn');
                if (startBtn) startBtn.style.display = 'none';
            }
        }
    } catch (e) {
        console.error("Status check failed", e);
    }
}

async function fetchJobs(role) {
    const container = document.getElementById('jobs-container');
    if (!container) return;

    try {
        const res = await fetch(`/jobs/recommend?role=${encodeURIComponent(role)}`);
        const data = await res.json();

        container.innerHTML = '';

        if (data.jobs && data.jobs.length > 0) {
            data.jobs.forEach(job => {
                const card = document.createElement('div');
                card.className = 'card';
                card.style.padding = '1.5rem';
                card.style.textAlign = 'left';
                card.innerHTML = `
                    <h4 style="font-size:1.1rem; margin-bottom:0.5rem;">${job.title}</h4>
                    <div style="font-weight:bold; color:var(--primary); margin-bottom:0.5rem;">${job.company}</div>
                    <div style="font-size:0.9rem; margin-bottom:1rem; color:var(--text-muted);">
                        <ion-icon name="location-outline"></ion-icon> ${job.location}
                    </div>
                    <a href="${job.url}" target="_blank" class="btn btn-secondary" style="width:100%; justify-content:center; font-size:0.9rem;">
                        Apply Now <ion-icon name="open-outline"></ion-icon>
                    </a>
                `;
                container.appendChild(card);
            });
        } else {
            container.innerHTML = `<div class="card" style="grid-column:1/-1; text-align:center; opacity:0.7;">No active jobs check back later.</div>`;
        }

    } catch (e) {
        console.error("Job fetch failed", e);
    }
}


function downloadReport(data) {
    if (!data || !data.transcript) return;

    let content = `AI INTERVIEW REPORT\n`;
    content += `================================\n`;
    content += `Candidate ID: ${data.session_id}\n`; // Using session ID as proxy if name not avail
    content += `Date: ${new Date().toLocaleString()}\n\n`;

    content += `SCORES\n`;
    content += `------\n`;
    content += `Interview Score: ${data.interview_score}/100\n`;
    content += `Resume Match: ${data.resume_score}%\n`;
    content += `Final Weighted Score: ${data.final_score}%\n\n`;

    content += `TRANSCRIPT & FEEDBACK\n`;
    content += `================================\n\n`;

    data.transcript.forEach((t, i) => {
        content += `Q${i + 1}: ${t.q}\n\n`;
        content += `Answer: ${t.a}\n\n`;
        content += `Score: ${t.score}/10\n`;
        content += `Feedback: ${t.feedback}\n`;
        content += `------------------------------------------------\n\n`;
    });

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Interview_Report_${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ---------- Helpers & UI ----------

function setupInterview() {
    const sendBtn = document.getElementById('send-btn');
    const input = document.getElementById('user-input');
    const micBtn = document.getElementById('mic-btn');
    const handsFreeToggle = document.getElementById('hands-free-toggle');

    // Proctoring (Ring 1 & 2)

    // 1. Fullscreen Enforcement
    document.addEventListener("fullscreenchange", () => {
        if (!document.fullscreenElement && !document.getElementById('interview-section').classList.contains('hidden')) {
            triggerViolation("Fullscreen Exit detected.");
        }
    });

    // 2. Focus Tracking
    document.addEventListener("visibilitychange", () => {
        if (document.hidden && !document.getElementById('interview-section').classList.contains('hidden')) {
            triggerViolation("Tab Switch / Minimize detected.");
        }
    });

    window.onblur = () => {
        if (!document.getElementById('interview-section').classList.contains('hidden')) {
            // Optional: Blur is very sensitive, relies on visibilitychange mostly
            // triggerViolation("Focus Lost.");
        }
    };

    // 3. Input Blocking (Ring 1)
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('copy', event => { event.preventDefault(); alert("Copying is disabled."); });
    document.addEventListener('cut', event => event.preventDefault());
    document.addEventListener('paste', event => { event.preventDefault(); alert("Pasting is disabled."); });


    if (handsFreeToggle) {
        handsFreeToggle.checked = true;
        handsFreeToggle.onchange = (e) => { handsFreeMode = e.target.checked; };
    }

    if (!sendBtn) return;

    // Heuristic: Superhuman Typing (Ring 3)
    let lastInputLen = 0;
    input.addEventListener('input', (e) => {
        const currentLen = input.value.length;
        const diff = currentLen - lastInputLen;

        // If more than 10 chars added instantly (and not via voice)
        if (diff > 10 && !isRecording) {
            // Check time difference? JS 'input' is sync, so diff usually comes from paste or autocomplete
            // We blocked 'paste' event, but some browser extensions or drag-drop bypass it.
            // Let's be strict: clear it.
            alert(" Rapid text entry detected. Please type manually.");
            input.value = ""; // Clear suspicious input
        }
        lastInputLen = input.value.length;
    });

    const handleSend = async () => {
        stopTimer();
        const text = input.value.trim();
        if (!text) return;

        lastInputLen = 0; // Reset tracker
        addMessage('user', text);
        input.value = '';

        synthesis.cancel();
        updateAvatarState('idle');

        try {
            const res = await fetch('/interview/answer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionData.id,
                    answer: text
                })
            });

            const data = await res.json();

            if (data.is_finished) {
                addMessage('ai', "Interview Finished! Generating your report...");
                speak("Interview Finished! Generating your report...");
                setTimeout(() => showFinalResult(sessionData.id), 2000);
            } else {
                addMessage('ai', data.next_question);
                speak(data.next_question);
            }

        } catch (err) {
            console.error(err);
            addMessage('system', "Error sending answer.");
        }
    };

    sendBtn.onclick = handleSend;
    input.onkeypress = (e) => { if (e.key === 'Enter') handleSend(); };

    // STT
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true; // Changed to true for better flow
        recognition.interimResults = true; // Needed for silence detection logic
        recognition.lang = 'en-US';

        let silenceTimer = null;
        const SILENCE_DELAY = 2500; // 2.5 seconds silence to trigger submit

        recognition.onstart = () => {
            isRecording = true;
            micBtn.classList.add('recording');
            updateAvatarState('listening');
        };

        recognition.onend = () => {
            // If we stopped manually (isRecording set to false in handleSend), that's fine.
            // If browser stopped it but we think we are recording, we could restart, 
            // BUT for this specific UX (one answer), it's better to just let it finish if the user stopped speaking.
            // However, with continuous=true, it shouldn't stop unless silence timeout or error.
            if (isRecording) {
                // Determine if we should restart or just stop. 
                // If the user hasn't said anything, maybe restart? 
                // For now, let's treat end as "User finished" or "Silence timeout fired"
            }
            isRecording = false;
            micBtn.classList.remove('recording');
            updateAvatarState('idle');

            // Clear any pending silence timer
            if (silenceTimer) clearTimeout(silenceTimer);
        };

        recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            // We append final to input, but we might want to just set it 
            // depending on if we clear input on start. 
            // Since we are continuous, we need to be careful not to duplicate text if we are just appending.
            // Actually, with continuous, 'event.results' accumulates.
            // So we can just grab the latest combined text.

            // Simpler approach for single-turn answer:
            // Just take the full transcript being built by the engine if possible, 
            // but standard webkitSR with continuous returns a list.

            // To avoid complexity: Join all final results.
            let fullText = "";
            for (let i = 0; i < event.results.length; ++i) {
                fullText += event.results[i][0].transcript;
            }

            input.value = fullText;

            // Silence Detection:
            // Every time we get a result (speech detected), reset the timer.
            if (silenceTimer) clearTimeout(silenceTimer);

            if (input.value.trim().length > 0) {
                silenceTimer = setTimeout(() => {
                    console.log("Silence detected. Auto-submitting.");
                    recognition.stop(); // This triggers onend
                    handleSend();
                }, SILENCE_DELAY);
            }
        };

        // Error handling to prevent "complaints"
        recognition.onerror = (event) => {
            console.warn("Speech Recognition Error:", event.error);
            if (event.error === 'no-speech') {
                // Ignore
            }
            // For network/not-allowed, we should alert user
            if (event.error === 'not-allowed') {
                alert("Microphone access blocked.");
                isRecording = false;
            }
        };

        micBtn.onclick = () => {
            if (isRecording) {
                recognition.stop();
                // Manually stopping implies "I'm done", so send?
                // Or just stop recording? 
                // "User uses mic after a small break it auto submits" -> Implies auto submit is the main way.
                // If they click stop, they probably want to edit or send. 
                // Let's just stop and NOT auto-send immediately, let them click send? 
                // Or follow silence logic? 
                // The silence timer handles the auto-send. Manual stop: just stop.
                if (silenceTimer) clearTimeout(silenceTimer);
            } else {
                input.value = ""; // Clear for new answer
                recognition.start();
            }
        };
    } else {
        micBtn.style.display = 'none';
    }
}

function addMessage(role, text, isHtml = false) {
    if (!text) return;
    const container = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (isHtml) div.innerHTML = text; else div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function startTimer() {
    stopTimer();
    const timerBadge = document.getElementById('interview-timer');
    if (!timerBadge) return;

    timeLeft = TIME_LIMIT;
    timerBadge.classList.remove('hidden');
    timerBadge.textContent = `00:${timeLeft}`;

    timerInterval = setInterval(() => {
        timeLeft--;
        timerBadge.textContent = `00:${timeLeft < 10 ? '0' + timeLeft : timeLeft}`;
        if (timeLeft <= 0) {
            stopTimer();
            const input = document.getElementById('user-input');
            if (input) {
                if (input.value.trim() === "") input.value = "I am not sure how to answer that.";
                document.getElementById('send-btn').click();
            }
        }
    }, 1000);
}

function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
    const timerBadge = document.getElementById('interview-timer');
    if (timerBadge) timerBadge.classList.add('hidden');
}

function updateAvatarState(state) {
    const avatar = document.getElementById('ai-avatar');
    if (!avatar) return;
    avatar.className = 'avatar-sphere';
    if (state === 'speaking') avatar.classList.add('speaking');
    if (state === 'listening') avatar.classList.add('listening');
}

function setupAudioContext() {
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
    }
}

function visualizeAudio() {
    if (!analyser) return;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const avatar = document.getElementById('ai-avatar');

    function draw() {
        if (!currentAudio || currentAudio.paused) {
            updateAvatarState('idle');
            if (avatar) avatar.style.transform = 'scale(1)';
            return;
        }
        requestAnimationFrame(draw);
        analyser.getByteFrequencyData(dataArray);

        // Simple Volume based scale
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
        let average = sum / bufferLength;

        if (avatar) {
            const scale = 1 + (average / 255) * 0.5;
            avatar.style.transform = `scale(${scale})`;
        }
    }
    draw();
}

async function speak(text) {
    // Global safety fuse: If nothing works after 10s (or text length based), force timer.
    const safetyFuseDelay = Math.max(3000, text.length * 100); // ~100ms per char
    const safetyFuse = setTimeout(() => {
        console.warn("Global TTS Safety Fuse triggered. Forcing timer.");
        updateAvatarState('idle');
        startTimer();
    }, safetyFuseDelay + 2000);

    let timerStarted = false;
    const triggerTimer = () => {
        if (timerStarted) return;
        timerStarted = true;
        clearTimeout(safetyFuse);
        updateAvatarState('idle');
        startTimer();
    };

    // Stop existing
    try { synthesis.cancel(); } catch (e) { }
    if (currentAudio) {
        try { currentAudio.pause(); } catch (e) { }
        currentAudio = null;
    }

    let backendSuccess = false;

    // 1. Backend TTS
    try {
        setupAudioContext();
        if (audioContext && audioContext.state === 'suspended') await audioContext.resume();

        const response = await fetch('/interview/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            currentAudio = new Audio(url);

            const source = audioContext.createMediaElementSource(currentAudio);
            source.connect(analyser);
            analyser.connect(audioContext.destination);

            currentAudio.onplay = () => { visualizeAudio(); updateAvatarState('speaking'); };
            currentAudio.onended = () => { triggerTimer(); };

            await currentAudio.play();
            backendSuccess = true;
        } else {
            console.warn("Backend TTS response not OK:", response.status);
        }

    } catch (e) {
        console.warn("Backend TTS failed. Trying browser fallback.", e);
    }

    if (backendSuccess) return;

    // 2. Browser TTS Fallback
    console.log("Using Browser TTS");
    try {
        const utter = new SpeechSynthesisUtterance(text);
        utter.onstart = () => updateAvatarState('speaking');
        utter.onend = () => { triggerTimer(); };
        utter.onerror = (e) => {
            console.error("Browser TTS Error:", e);
            triggerTimer();
        };

        synthesis.speak(utter);

    } catch (err) {
        console.error("Browser TTS fatal error:", err);
        triggerTimer();
    }
}

// ---------- Anti-Cheat Helpers ----------

function triggerViolation(reason) {
    cheatingWarnings++;

    // Send flag to backend
    if (sessionData && sessionData.id) {
        fetch('/interview/flag', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionData.id, reason: reason })
        }).catch(e => console.error("Flag send failed", e));
    }

    const overlay = document.getElementById('warning-overlay');

    if (overlay) {
        overlay.classList.remove('hidden');
        overlay.querySelector('h3').textContent = "Proctoring Alert";
        overlay.querySelector('p').textContent = `${reason} Warning ${cheatingWarnings}/3.`;

        if (cheatingWarnings >= 3) {
            overlay.querySelector('h3').textContent = "Interview Terminated";
            overlay.querySelector('p').textContent = "Maximum violations exceeded.";
            overlay.style.background = "rgba(0,0,0,0.95)";

            // Call Backend to Lock user out
            if (sessionData && sessionData.id) {
                fetch('/interview/terminate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionData.id, reason: reason })
                });
            }

            // Disable inputs
            const input = document.getElementById('user-input');
            if (input) input.disabled = true;
            stopTimer();

            // Reload after delay
            setTimeout(() => {
                location.reload();
            }, 3000);
        } else {
            // Auto-resume after 3s if not fatal
            setTimeout(() => {
                // Return to fullscreen if possible
                try { document.documentElement.requestFullscreen(); } catch (e) { }
                overlay.classList.add('hidden');
            }, 4000);
        }
    }
}

async function initWebcam() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    const video = document.getElementById('webcam-feed');
    if (video) video.srcObject = stream;
}
