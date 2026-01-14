
// State
let sessionData = null;
let currentPayload = null;
let synthesis = window.speechSynthesis;
let audioContext = null;
let analyser = null;
let audioSource = null;
let currentAudio = null;
let recognition = null;
let isRecording = false;

// Init
// Anti-Cheat & Timer State
let timerInterval = null;
let timeLeft = 45;
let cheatingWarnings = 0;
const TIME_LIMIT = 45;

// Init
document.addEventListener('DOMContentLoaded', () => {
    setupUpload();
    setupInterview();

    // Initial fetch if we want to show leaderboard immediately? 
    // Usually we wait for user action. 
    // But let's check if there are candidates.
    // fetchLeaderboard(); // Optional auto-load

    // Setup Start Interview Button in Match Results
    const startBtn = document.getElementById('start-interview-btn');
    if (startBtn) {
        startBtn.onclick = () => {
            if (currentPayload) {
                startInterview(currentPayload);
            } else {
                alert("No interview context found.");
            }
        };
    }
});

// ---------- Leaderboard Logic ----------

async function fetchLeaderboard() {
    try {
        const res = await fetch('/leaderboard');
        const candidates = await res.json();

        // Switch Views
        document.getElementById('upload-section').classList.add('hidden');
        document.getElementById('match-results').classList.add('hidden');
        document.getElementById('interview-section').classList.add('hidden');
        document.getElementById('report-section').classList.add('hidden');
        document.getElementById('leaderboard-section').classList.remove('hidden');

        renderLeaderboard(candidates);
    } catch (e) {
        alert("Failed to load leaderboard.");
    }
}

async function clearLeaderboard() {
    if (!confirm("Are you sure you want to clear all candidates? This cannot be undone.")) return;

    try {
        const res = await fetch('/candidates', { method: 'DELETE' });
        if (res.ok) {
            alert("Leaderboard cleared.");
            fetchLeaderboard(); // Refresh empty list
        } else {
            alert("Failed to clear leaderboard.");
        }
    } catch (e) {
        alert("Error clearing leaderboard: " + e);
    }
}

function renderLeaderboard(candidates) {
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '';

    if (!candidates || candidates.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:2rem; opacity:0.5;">No candidates found. Upload a resume to start.</td></tr>';
        return;
    }

    candidates.forEach((c, index) => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid rgba(255,255,255,0.05)';

        let statusColor = c.status === 'Interviewed' ? 'var(--success)' : 'var(--text-muted)';

        // We need a way to restart interview for a candidate.
        // Since we don't have full Resume Text in this view easily unless we fetch it,
        // we'll disable re-interview for now or implement a specific endpoint fetch.
        // For simplicity, we disable if done.

        const actionBtn = c.status !== 'Interviewed' ?
            `<button class="btn btn-primary" onclick="initiateInterviewFromId('${c.id}')" style="padding:0.5rem 1rem; font-size:0.8rem;">
                        Interview
                </button>` :
            `<button class="btn btn-secondary" disabled style="padding:0.5rem 1rem; font-size:0.8rem; opacity:0.5;">Done</button>`;

        tr.innerHTML = `
            <td style="padding:1rem;">#${index + 1}</td>
            <td style="padding:1rem; font-weight:bold;">${c.name || 'Candidate'}</td>
            <td style="padding:1rem;">
                <div class="tag" style="background:rgba(255,255,255,0.1);">${c.match_score.toFixed(1)}%</div>
            </td>
            <td style="padding:1rem;">${c.interview_score > 0 ? c.interview_score + '%' : '-'}</td>
            <td style="padding:1rem; color:${statusColor}">${c.status || 'Matched'}</td>
            <td style="padding:1rem;">${actionBtn}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Helper to start interview from Leaderboard (requires fetching context first)
// For now, we'll just mock or alert since we need Resume Text to start context.
// Ideally, backend session creation should support candidate_id lookup.
async function initiateInterviewFromId(candidateId) {
    // In a real app, we call backend to get resume_text by ID.
    // For now, we alert limitation.
    alert("Please restart the session via Upload to ensure fresh context.");
}

// ---------- Upload Logic ----------

function setupUpload() {
    const uploadForm = document.getElementById('upload-form');
    if (!uploadForm) return;

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const resumeFile = document.getElementById('resume-file').files[0];
        const jdText = document.getElementById('jd-text').value;

        if (!resumeFile || !jdText) {
            alert("Please provide a Resume and Job Description.");
            return;
        }

        const formData = new FormData();
        formData.append('resume', resumeFile); // Key must match backend 'resume'
        formData.append('job_description', jdText);

        setLoading(true);

        try {
            const res = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();

            if (res.ok) {
                // Show Match Results
                showMatchResults(data);
                // Store payload for interview
                currentPayload = data.interview_context.payload;
            } else {
                alert("Error: " + (data.detail || data.error || "Unknown error"));
            }
        } catch (err) {
            alert("Connection Failed: " + err);
        } finally {
            setLoading(false);
        }
    });
}

function showMatchResults(data) {
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('match-results').classList.remove('hidden');

    // Score
    document.getElementById('score-value').textContent = data.match_score + "%";

    // Skills
    const foundContainer = document.getElementById('found-skills-container');
    const missingContainer = document.getElementById('missing-skills-container');

    foundContainer.innerHTML = '';
    missingContainer.innerHTML = '';

    if (data.matched_skills && data.matched_skills.length > 0) {
        data.matched_skills.forEach(skill => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.style.background = 'rgba(0, 255, 100, 0.1)';
            span.textContent = skill;
            foundContainer.appendChild(span);
        });
    } else {
        foundContainer.innerHTML = '<span class="tag" style="opacity:0.5;">None</span>';
    }

    if (data.missing_skills && data.missing_skills.length > 0) {
        data.missing_skills.forEach(skill => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.textContent = skill;
            missingContainer.appendChild(span);
        });
    } else {
        missingContainer.innerHTML = '<span class="tag" style="opacity:0.5;">None</span>';
    }
}

// ---------- Interview Logic ----------

async function startInterview(payload) {
    // Switch Views
    document.getElementById('match-results').classList.add('hidden');
    document.getElementById('leaderboard-section').classList.add('hidden');
    document.getElementById('interview-section').classList.remove('hidden');

    // Initialize Session
    try {
        const res = await fetch('/interview/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
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
            addMessage('system', "Error: AI failed to generate a question.");
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
        document.getElementById('final-total-score').textContent = data.final_score;
        document.getElementById('final-interview-score').textContent = data.interview_score;

        // Mock Motivation (Backend doesn't provide yet)
        const motivationEl = document.getElementById('report-motivation');
        if (motivationEl) motivationEl.textContent = "Great job! Keep practicing to improve your depth.";

        // Hide Roles/Focus if not present or Mock
        const roleContainer = document.getElementById('report-roles');
        if (roleContainer) {
            roleContainer.innerHTML = '<div class="tag">Software Engineer</div>';

            // Trigger Job Search for this role
            fetchJobs("Software Engineer");
        }

        const focusContainer = document.getElementById('report-focus');
        if (focusContainer) {
            focusContainer.innerHTML = '<span class="tag" style="border:1px solid var(--accent); color:var(--accent);">System Design</span>';
        }

        // Populate Detailed Breakdown
        const breakdownContainer = document.getElementById('report-breakdown');
        if (breakdownContainer && data.transcript) {
            breakdownContainer.innerHTML = '';
            // Flatten transcript to breakdown format
            data.transcript.forEach((item, index) => {
                const card = document.createElement('div');
                card.className = 'card';
                card.style.marginBottom = '1rem';
                card.style.background = 'rgba(255,255,255,0.02)';
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

        // Disable download for now
        const dlBtn = document.getElementById('download-btn');
        if (dlBtn) dlBtn.style.display = 'none';

    } catch (e) {
        console.error(e);
        alert("Error generating report.");
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
            container.innerHTML = `<div class="card" style="grid-column:1/-1; text-align:center; opacity:0.7;">No active jobs found for "${role}".</div>`;
        }

    } catch (e) {
        console.error("Job fetch failed", e);
        container.innerHTML = `<div class="card" style="grid-column:1/-1; text-align:center; color:var(--error);">Failed to load jobs. Check Adzuna keys.</div>`;
    }
}

// ---------- Helpers ----------

function addMessage(role, text, isHtml = false) {
    if (!text) return;
    const container = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    if (isHtml) div.innerHTML = text; else div.textContent = text;

    if (role === 'system') {
        div.style.background = 'rgba(0,0,0,0.3)';
        div.style.border = '1px dashed var(--text-muted)';
        div.style.fontSize = '0.9rem';
        div.style.textAlign = 'center';
    }

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// Helper to manage Timer
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
            // Auto Submit
            const input = document.getElementById('user-input');
            if (input) {
                if (input.value.trim() === "") {
                    input.value = "I am not sure how to answer that yet.";
                }
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

// State
let handsFreeMode = true; // Default True for Real-Time feel

function updateAvatarState(state) {
    const avatar = document.getElementById('ai-avatar');
    if (!avatar) return;
    avatar.className = 'avatar-sphere'; // Reset
    if (state === 'speaking') avatar.classList.add('speaking');
    if (state === 'listening') avatar.classList.add('listening');
}


// Audio Visualizer Setup
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
            // reset style
            if (avatar) {
                avatar.style.transform = 'scale(1)';
                avatar.style.boxShadow = '';
            }
            return;
        }

        requestAnimationFrame(draw);
        analyser.getByteFrequencyData(dataArray);

        // Calculate average volume
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) {
            sum += dataArray[i];
        }
        let average = sum / bufferLength;

        // Bass focus for scaling
        let bassSum = 0;
        let bassCount = bufferLength / 4;
        for (let i = 0; i < bassCount; i++) {
            bassSum += dataArray[i];
        }
        let bassAvg = bassSum / bassCount;

        if (avatar) {
            // Scale based on bass
            const scale = 1 + (bassAvg / 255) * 0.4;
            avatar.style.transform = `scale(${scale})`;

            // Glow based on overall volume
            const glow = (average / 255) * 60;
            const glowColor = `rgba(0, 242, 255, ${average / 255})`;
            avatar.style.boxShadow = `0 0 ${glow}px ${glowColor}, inset 0 0 20px rgba(255,255,255,0.4)`;
        }
    }

    draw();
}

async function speak(text) {
    // 1. Try Backend TTS (ElevenLabs)
    try {
        setupAudioContext();
        if (audioContext.state === 'suspended') await audioContext.resume();

        // Stop previous
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }
        synthesis.cancel();

        const response = await fetch('/interview/speak', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        if (response.status === 503) {
            throw new Error("TTS_DISABLED");
        }

        if (!response.ok) throw new Error("TTS Failed");

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);

        currentAudio = new Audio(url);

        // Connect to Analyser
        const source = audioContext.createMediaElementSource(currentAudio);
        source.connect(analyser);
        analyser.connect(audioContext.destination);

        currentAudio.onplay = () => {
            updateAvatarState('speaking'); // This class animation might conflict with manual transform,
            // but we can remove the class or let visualizer override
            const avatar = document.getElementById('ai-avatar');
            if (avatar) avatar.classList.remove('speaking'); // Disable CSS animation to let JS drive it
            visualizeAudio();
        };

        currentAudio.onended = () => {
            updateAvatarState('idle');
            startTimer(); // Start countdown after AI speaks
            if (handsFreeMode) {
                setTimeout(() => {
                    const micBtn = document.getElementById('mic-btn');
                    if (micBtn && !isRecording) micBtn.click();
                }, 500);
            }
        };

        currentAudio.play();
        return;

    } catch (e) {
        console.warn("ElevenLabs TTS unavailable, falling back to Browser TTS:", e);
    }

    // 2. Fallback to Browser TTS
    if (!synthesis) return;
    synthesis.cancel();
    const voices = synthesis.getVoices();
    const utter = new SpeechSynthesisUtterance(text);
    const preferred = voices.find(v => v.name.includes('Google US English') || v.name.includes('Microsoft Zira'));
    if (preferred) utter.voice = preferred;

    utter.onstart = () => updateAvatarState('speaking');
    utter.onend = () => {
        updateAvatarState('idle');
        startTimer(); // Start countdown after AI speaks
        if (handsFreeMode) {
            setTimeout(() => {
                const micBtn = document.getElementById('mic-btn');
                if (micBtn && !isRecording) micBtn.click();
            }, 500);
        }
    };

    synthesis.speak(utter);
}



function setupInterview() {
    const sendBtn = document.getElementById('send-btn');
    const input = document.getElementById('user-input');
    const micBtn = document.getElementById('mic-btn');
    const handsFreeToggle = document.getElementById('hands-free-toggle');

    // Proctoring - Tab Switch Detection
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
        handsFreeToggle.checked = true; // Set UI to checked by default
        handsFreeToggle.onchange = (e) => {
            handsFreeMode = e.target.checked;
        };
    }

    if (!sendBtn) return;

    // Send Message
    const handleSend = async () => {
        stopTimer(); // Stop countdown
        const text = input.value.trim();
        if (!text) return;

        addMessage('user', text);
        input.value = '';

        // Stop TTS if talking
        synthesis.cancel();
        updateAvatarState('idle');

        // Call API
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
                addMessage('ai', "Interview Finished! Generating your career report...");
                speak("Interview Finished! Generating your career report...");
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

    // STT Setup checks
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isRecording = true;
            micBtn.classList.add('recording');
            micBtn.style.color = 'red';
            updateAvatarState('listening');
        };

        recognition.onend = () => {
            isRecording = false;
            micBtn.classList.remove('recording');
            micBtn.style.color = '';
            updateAvatarState('idle');

            // Auto-submit in Hands-Free Mode if input has text
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
        console.warn("Speech Recognition not supported in this browser.");
    }
}

function setLoading(isLoading) {
    const btn = document.querySelector('#upload-form button');
    const loadingText = document.getElementById('loading-text');

    if (btn) {
        btn.innerHTML = isLoading ?
            'Analyzing... <ion-icon name="sync-outline" class="pulse"></ion-icon>' :
            'Analyze & Match <ion-icon name="arrow-forward-outline"></ion-icon>';
        btn.disabled = isLoading;
    }
    if (loadingText) {
        loadingText.style.opacity = isLoading ? '1' : '0';
    }
}
