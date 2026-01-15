
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
let timeLeft = 45;
let cheatingWarnings = 0;
const TIME_LIMIT = 45;
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
            startBtn.onclick = () => {
                console.log("Start button clicked");
                landingSection.classList.add('hidden');
                interviewSection.classList.remove('hidden');

                // Initialize Interview
                // We need to fetch the context first or just start. 
                // The current API /interview/start requires a 'payload' with resume_text/match_score 
                // OR getting it from DB via candidate_id.
                // The current backend endpoint takes 'StartInterviewRequest' with optional candidate_id.
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

    // Proctoring
    document.addEventListener("visibilitychange", () => {
        if (document.hidden && !document.getElementById('interview-section').classList.contains('hidden')) {
            cheatingWarnings++;
            const overlay = document.getElementById('warning-overlay');
            if (overlay) {
                overlay.classList.remove('hidden');
                if (cheatingWarnings >= 2) {
                    overlay.querySelector('h3').textContent = "Interview Terminated";
                    overlay.querySelector('p').textContent = "Multiple focus violations detected.";
                    setTimeout(() => location.reload(), 3000);
                } else {
                    setTimeout(() => overlay.classList.add('hidden'), 3000);
                }
            }
        }
    });

    if (handsFreeToggle) {
        handsFreeToggle.checked = true;
        handsFreeToggle.onchange = (e) => { handsFreeMode = e.target.checked; };
    }

    if (!sendBtn) return;

    const handleSend = async () => {
        stopTimer();
        const text = input.value.trim();
        if (!text) return;

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
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isRecording = true;
            micBtn.classList.add('recording');
            updateAvatarState('listening');
        };

        recognition.onend = () => {
            isRecording = false;
            micBtn.classList.remove('recording');
            updateAvatarState('idle');
            if (handsFreeMode && input.value.trim().length > 0) {
                setTimeout(() => handleSend(), 500);
            }
        };

        recognition.onresult = (event) => {
            input.value = event.results[0][0].transcript;
        };

        micBtn.onclick = () => { isRecording ? recognition.stop() : recognition.start(); };
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
    // 1. Backend TTS
    try {
        setupAudioContext();
        if (audioContext.state === 'suspended') await audioContext.resume();
        if (currentAudio) { currentAudio.pause(); currentAudio = null; }
        synthesis.cancel();

        const response = await fetch('/interview/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        if (!response.ok) throw new Error("TTS Failed");

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        currentAudio = new Audio(url);

        const source = audioContext.createMediaElementSource(currentAudio);
        source.connect(analyser);
        analyser.connect(audioContext.destination);

        currentAudio.onplay = () => { visualizeAudio(); };
        currentAudio.onended = () => { updateAvatarState('idle'); startTimer(); };
        currentAudio.play();
        return;

    } catch (e) {
        console.warn("Falling back to browser TTS", e);
    }

    // 2. Browser TTS Fallback
    const utter = new SpeechSynthesisUtterance(text);
    utter.onstart = () => updateAvatarState('speaking');
    utter.onend = () => { updateAvatarState('idle'); startTimer(); };
    synthesis.speak(utter);
}
