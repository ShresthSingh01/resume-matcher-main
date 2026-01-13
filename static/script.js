
// State
let sessionData = null;
let synthesis = window.speechSynthesis;
let recognition = null;
let isRecording = false;

// Init
document.addEventListener('DOMContentLoaded', () => {
    setupUpload();
    setupInterview();
});

// ---------- Upload Logic ----------

function setupUpload() {
    const uploadForm = document.getElementById('upload-form');
    if (!uploadForm) return;

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const resumeFiles = document.getElementById('resume-file').files;
        const jdText = document.getElementById('jd-text').value;

        if (resumeFiles.length === 0 || !jdText) {
            alert("Please provide Resumes and Job Description.");
            return;
        }

        const formData = new FormData();
        for (let i = 0; i < resumeFiles.length; i++) {
            formData.append('resumes', resumeFiles[i]);
        }
        formData.append('job_description', jdText);

        setLoading(true);

        try {
            const res = await fetch('/batch-upload', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();

            if (res.ok) {
                renderLeaderboard(data.candidates);
            } else {
                alert("Error: " + (data.message || "Unknown error"));
            }
        } catch (err) {
            alert("Connection Failed: " + err);
        } finally {
            setLoading(false);
        }
    });
}

async function fetchLeaderboard() {
    try {
        const res = await fetch('/leaderboard');
        const candidates = await res.json();

        // Hide other views
        document.getElementById('upload-section').classList.add('hidden');
        document.getElementById('interview-section').classList.add('hidden');
        document.getElementById('report-section').classList.add('hidden');

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
    document.getElementById('upload-section').classList.add('hidden');
    document.getElementById('leaderboard-section').classList.remove('hidden');

    // Sort by Match Score Descending
    candidates.sort((a, b) => b.match_score - a.match_score);

    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '';

    candidates.forEach((c, index) => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid rgba(255,255,255,0.05)';

        let statusColor = c.status === 'Interviewed' ? 'var(--success)' : 'var(--text-muted)';

        tr.innerHTML = `
            <td style="padding:1rem;">#${index + 1}</td>
            <td style="padding:1rem; font-weight:bold;">${c.name}</td>
            <td style="padding:1rem;">
                <div class="tag" style="background:rgba(255,255,255,0.1);">${c.match_score}%</div>
            </td>
            <td style="padding:1rem;">${c.interview_score > 0 ? c.interview_score + '%' : '-'}</td>
            <td style="padding:1rem; color:${statusColor}">${c.status || 'Matched'}</td>
            <td style="padding:1rem;">
                ${c.status !== 'Interviewed' ?
                `<button class="btn btn-primary" onclick="initiateInterview('${c.id}')" style="padding:0.5rem 1rem; font-size:0.8rem;">
                        Interview
                    </button>` :
                `<button class="btn btn-secondary" disabled style="padding:0.5rem 1rem; font-size:0.8rem; opacity:0.5;">Done</button>`
            }
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function initiateInterview(candidateId) {
    // We start interview by passing a flag to use DB
    const context = {
        payload: {
            resume_text: candidateId, // Passing ID in this field for simplicity given backend logic
            job_description: "",
            match_score: -1 // Flag for DB lookup
        }
    };
    startInterview(context);
}



// ---------- Interview Logic ----------

async function startInterview(context) {
    // Switch Views
    document.getElementById('leaderboard-section').classList.add('hidden');
    document.getElementById('interview-section').classList.remove('hidden');

    // Initialize Session
    try {
        const res = await fetch('/interview/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(context.payload)
        });

        const data = await res.json();

        if (!res.ok) {
            console.error("DEBUG: Backend Error:", data);
            addMessage('system', `Error: ${data.message || data.error || "Unknown backend error"}`);
            return;
        }

        // Initialize sessionData if null (Batch mode)
        if (!sessionData) {
            sessionData = {};
        }
        sessionData.id = data.session_id;

        // Clear previous messages
        document.getElementById('chat-container').innerHTML = '';

        console.log("DEBUG: Start Interview response:", data);

        if (data.question) {
            addMessage('ai', data.question);
            speak(data.question);
        } else {
            console.error("DEBUG: Received empty question from backend");
            addMessage('system', "Error: AI failed to generate a question.");
        }

    } catch (err) {
        alert("Failed to start interview: " + err);
    }
}

function setupInterview() {
    const sendBtn = document.getElementById('send-btn');
    const input = document.getElementById('user-input');
    const micBtn = document.getElementById('mic-btn');

    if (!sendBtn) return; // Not on page

    // Send Message
    const handleSend = async () => {
        const text = input.value.trim();
        if (!text) return;

        addMessage('user', text);
        input.value = '';

        // Stop TTS if talking
        synthesis.cancel();

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

            // Removed instant feedback to avoid panic

            if (data.is_finished) {
                addMessage('ai', "Interview Finished! Generating your career report...");
                speak("Interview Finished! Generating your career report...");
                setTimeout(() => showFinalResult(sessionData.id), 2000);
            } else {
                addMessage('ai', data.next_question);
                speak(data.next_question);
            }

        } catch (err) {
            addMessage('system', "Error sending answer.");
        }
    };

    sendBtn.onclick = handleSend;
    input.onkeypress = (e) => { if (e.key === 'Enter') handleSend(); };

    // STT Setup
    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isRecording = true;
            micBtn.classList.add('recording');
        };

        recognition.onend = () => {
            isRecording = false;
            micBtn.classList.remove('recording');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            input.value = transcript;
        };

        micBtn.onclick = () => {
            if (isRecording) recognition.stop();
            else recognition.start();
        };
    } else {
        micBtn.style.display = 'none'; // Hide if not supported
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
        const report = data.career_report;

        // Hide Interview, Show Report
        document.getElementById('interview-section').classList.add('hidden');
        document.getElementById('report-section').classList.remove('hidden');

        // Populate Scores
        document.getElementById('final-total-score').textContent = data.final_score;
        document.getElementById('final-interview-score').textContent = data.interview_score;

        // Populate Motivation
        if (report.motivation) {
            document.getElementById('report-motivation').textContent = `"${report.motivation}"`;
        }

        // Populate Roles
        const roleContainer = document.getElementById('report-roles');
        roleContainer.innerHTML = '';
        report.preferred_roles.forEach(role => {
            const div = document.createElement('div');
            div.className = 'tag';
            div.style.background = 'rgba(255,255,255,0.05)';
            div.style.padding = '1rem';
            div.style.display = 'flex';
            div.style.alignItems = 'center';
            div.style.gap = '0.5rem';
            div.innerHTML = `<ion-icon name="briefcase"></ion-icon> ${role}`;
            roleContainer.appendChild(div);
        });

        // Populate Focus Areas
        const focusContainer = document.getElementById('report-focus');
        focusContainer.innerHTML = '';
        report.focus_areas.forEach(area => {
            const span = document.createElement('span');
            span.className = 'tag';
            span.style.border = '1px solid var(--accent)';
            span.style.color = 'var(--accent)';
            span.textContent = area;
            focusContainer.appendChild(span);
        });

        // Populate Detailed Breakdown
        const breakdownContainer = document.getElementById('report-breakdown');
        breakdownContainer.innerHTML = '';

        data.breakdown.forEach((item, index) => {
            const card = document.createElement('div');
            card.className = 'card';
            card.style.marginBottom = '1rem';
            card.style.background = 'rgba(255,255,255,0.02)';
            card.innerHTML = `
                <div style="margin-bottom:0.5rem; font-weight:bold; color:var(--text-muted);">Question ${index + 1}</div>
                <div style="margin-bottom:1rem; font-style:italic;">"${item.question}"</div>
                <div style="margin-bottom:1rem; padding-left:1rem; border-left:2px solid var(--primary);">"${item.answer}"</div>
                
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; font-size:0.9rem;">
                    <div>
                        <div style="color:var(--success)">✅ Strength</div>
                        <div>${item.strength || '-'}</div>
                    </div>
                    <div>
                        <div style="color:var(--error)">⚠️ Gap</div>
                        <div>${item.gap || '-'}</div>
                    </div>
                    <div style="grid-column:1/-1;">
                        <div style="color:var(--accent)">💡 Tip</div>
                        <div>${item.improvement || '-'}</div>
                    </div>
                </div>
            `;
            breakdownContainer.appendChild(card);
        });

        // Setup Download
        document.getElementById('download-btn').onclick = () => downloadReport(data);

    } catch (e) {
        console.error(e);
        alert("Error generating report.");
    }
}

function downloadReport(data) {
    const report = data.career_report;
    let content = `AI CAREER REPORT\n================\n\n`;
    content += `Role: ${data.role}\n`;
    content += `Final Score: ${data.final_score}/100\n`;
    content += `Interview Score: ${data.interview_score}/100\n\n`;

    content += `CAREER GUIDANCE\n---------------\n`;
    content += `Focus Areas: ${report.focus_areas.join(', ')}\n`;
    content += `Preferred Roles: ${report.preferred_roles.join(', ')}\n`;
    content += `Motivation: "${report.motivation}"\n\n`;

    content += `INTERVIEW BREAKDOWN\n-------------------\n`;
    data.breakdown.forEach((item, index) => {
        content += `\nQ${index + 1}: ${item.question}\n`;
        content += `A: ${item.answer}\n`;
        content += `Score: ${item.score}/10\n`;
        content += `Strength: ${item.strength}\n`;
        content += `Gap: ${item.gap}\n`;
        content += `Tip: ${item.improvement}\n`;
        content += `-------------------\n`;
    });

    const blob = new Blob([content], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `career_report_${Date.now()}.txt`;
    a.click();
    window.URL.revokeObjectURL(url);
}

// ---------- Helpers ----------

function addMessage(role, text, isHtml = false) {
    if (!text) return;

    const container = document.getElementById('chat-container');
    const div = document.createElement('div');
    div.className = `message ${role}`;

    if (isHtml) div.innerHTML = text;
    else div.textContent = text;

    // System message styling
    if (role === 'system') {
        div.style.background = 'rgba(0,0,0,0.3)';
        div.style.border = '1px dashed var(--text-muted)';
        div.style.fontSize = '0.9rem';
        div.style.alignSelf = 'center';
        div.style.width = '100%';
        div.style.maxWidth = '100%';
        div.style.textAlign = 'center';
    }

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function speak(text) {
    if (!synthesis) return;
    synthesis.cancel(); // Stop current

    // Ensure voices are loaded (Chrome quirk)
    const voices = synthesis.getVoices();

    const utter = new SpeechSynthesisUtterance(text);
    // Optional: Pick a better voice if available
    const preferred = voices.find(v => v.name.includes('Google US English') || v.name.includes('Microsoft Zira'));
    if (preferred) utter.voice = preferred;

    synthesis.speak(utter);
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
