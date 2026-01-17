
// recruiter.js - Logic for Recruiter Dashboard (Upload & Leaderboard)

let allCandidates = []; // Store candidates globally

document.addEventListener('DOMContentLoaded', () => {
    setupUpload();
    // fetchLeaderboard(); // Optional auto-load
});

// ---------- Leaderboard Logic ----------

async function fetchLeaderboard() {
    try {
        const res = await fetch('/leaderboard');
        if (res.status === 401) {
            window.location.href = '/login';
            return;
        }
        const candidates = await res.json();
        allCandidates = candidates; // Save to global scope

        // Switch Views
        document.getElementById('upload-section').classList.add('hidden');
        document.getElementById('leaderboard-section').classList.remove('hidden');

        renderLeaderboard(candidates);
    } catch (e) {
        console.error("Leaderboard Error:", e);
        alert("Failed to load leaderboard: " + e.message);
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

        let statusColor = 'var(--text-muted)';
        let statusText = 'Pending';

        if (c.status === 'completed') {
            statusColor = 'var(--success)';
            statusText = 'Completed';
        } else if (c.status === 'Interviewed') {
            statusColor = 'var(--success)';
            statusText = 'Completed';
        } else if (c.status === 'Shortlisted') {
            statusColor = 'var(--success)'; // Green
            statusText = 'Shortlisted';
        } else if (c.status === 'Waitlist') {
            statusColor = 'orange';
            statusText = 'Waitlist';
        } else if (c.status === 'Rejected') {
            statusColor = 'var(--error)'; // Red
            statusText = 'Rejected';
        } else {
            statusText = c.status || 'Pending';
        }

        let actionBtn = '';

        if (statusText === 'Completed') {
            actionBtn = `<button class="btn btn-secondary" onclick="showCandidateDetails(${index})" style="padding:0.5rem 1rem; font-size:0.8rem;">View Report</button>`;
        } else {

            // Pending / Shortlisted / Rejected / Waitlist / Invited / ...
            let btnLabel = 'Invite';
            let btnClass = 'btn-primary';
            let confirmMsg = 'Send interview invitation?';
            let isDisabled = false;

            // Normalize for comparison
            const s = (c.status || '').trim().toLowerCase();

            if (s.includes('shortlisted')) {
                btnLabel = 'Next Round';
                btnClass = 'btn-success';
                confirmMsg = 'Send Next Round Hiring email?';
            } else if (s.includes('shortlist') && s.includes('sent')) {
                btnLabel = 'Next Round Sent';
                btnClass = 'btn-success';
                isDisabled = true;
            } else if (s === 'rejected' || (s.includes('reject') && !s.includes('sent'))) {
                btnLabel = 'Send Rejection';
                btnClass = 'btn-danger';
                confirmMsg = 'Send Rejection email?';
            } else if (s.includes('reject') && s.includes('sent')) {
                btnLabel = 'Rejection Sent';
                btnClass = 'btn-danger';
                isDisabled = true;
            } else if (s.includes('invited') || s.includes('invite sent')) {
                btnLabel = 'Invite Sent';
                btnClass = 'btn-secondary';
                isDisabled = true;
            } else {
                // Waitlist or Matched
                btnLabel = 'Invite to Interview';
                confirmMsg = 'Send AI Interview Invitation?';
            }

            const buttonHtml = isDisabled
                ? `<button class="btn ${btnClass}" disabled style="padding:0.5rem 1rem; font-size:0.8rem; opacity:0.6; cursor:not-allowed;">${btnLabel}</button>`
                : `<button class="btn ${btnClass}" onclick="initiateInterviewFromId('${c.id}', '${confirmMsg}', this)" style="padding:0.5rem 1rem; font-size:0.8rem; background-color: ${btnClass === 'btn-danger' ? 'var(--error)' : (btnClass === 'btn-success' ? 'var(--success)' : '')}; color:white;">${btnLabel}</button>`;

            actionBtn = `
            <button class="btn btn-secondary" onclick="showCandidateDetails(${index})" style="padding:0.5rem 1rem; font-size:0.8rem; margin-right:0.5rem;">View</button>
            ${buttonHtml}`;
        }

        tr.innerHTML = `
            <td style="padding:1rem;">#${index + 1}</td>
            <td style="padding:1rem; font-weight:bold;">${c.name || 'Candidate'}</td>
            <td style="padding:1rem;">
                <div class="tag" style="background:rgba(255,255,255,0.1);">${c.match_score.toFixed(1)}%</div>
            </td>
            <td style="padding:1rem;">${c.interview_score > 0 ? c.interview_score + '/100' : '-'}</td>
            <td style="padding:1rem; color:${statusColor}">${statusText}</td>
            <td style="padding:1rem;">${actionBtn}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function initiateInterviewFromId(candidateId, confirmMsg = "Send invitation?", btnElement) {
    if (!confirm(confirmMsg)) return;

    // Optimistic UI update
    const originalText = btnElement.innerText;
    btnElement.disabled = true;
    btnElement.innerText = "Sending...";
    btnElement.style.opacity = "0.7";

    try {
        const res = await fetch(`/invite/candidate/${candidateId}`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            alert(data.message);
            // Persistent success state
            if (originalText.includes("Next Round")) btnElement.innerText = "Next Round Sent";
            else if (originalText.includes("Rejection")) btnElement.innerText = "Rejection Sent";
            else btnElement.innerText = "Invite Sent";
        } else {
            alert("Error sending email: " + (data.detail || "Unknown error"));
            // Revert on error
            btnElement.disabled = false;
            btnElement.innerText = originalText;
            btnElement.style.opacity = "1";
        }
    } catch (e) {
        alert("Failed to send invite: " + e);
        // Revert on error
        btnElement.disabled = false;
        btnElement.innerText = originalText;
        btnElement.style.opacity = "1";
    }
}

// ---------- Upload Logic ----------

function setupUpload() {
    const uploadForm = document.getElementById('upload-form');
    if (!uploadForm) return;

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const resumeFiles = document.getElementById('resume-file').files;
        const jdText = document.getElementById('jd-text').value;

        if (resumeFiles.length === 0 || !jdText) {
            alert("Please provide at least one Resume and a Job Description.");
            return;
        }

        const formData = new FormData();
        // Batch Support: Append all files
        for (let i = 0; i < resumeFiles.length; i++) {
            formData.append('resumes', resumeFiles[i]);
        }
        formData.append('job_description', jdText);

        const templateMode = document.getElementById('template-select').value;
        formData.append('template_mode', templateMode);

        setLoading(true);

        try {
            const res = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (res.status === 401) {
                window.location.href = '/login';
                return;
            }

            const data = await res.json();

            if (res.ok) {
                alert(`Batch Processed: ${Array.isArray(data) ? data.length : 1} resumes. Redirecting to Leaderboard.`);
                fetchLeaderboard();
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

function setLoading(isLoading) {
    const btn = document.querySelector('#upload-form button');
    const loadingText = document.getElementById('loading-text');

    if (btn) {
        btn.innerHTML = isLoading ?
            'Analyzing... <ion-icon name="sync-outline" class="pulse"></ion-icon>' :
            'Batch Analyze <ion-icon name="arrow-forward-outline"></ion-icon>';
        btn.disabled = isLoading;
    }
    if (loadingText) {
        loadingText.style.opacity = isLoading ? '1' : '0';
    }
}

// ---------- Modal Logic ----------

function showCandidateDetails(index) {
    const c = allCandidates[index];
    if (!c) return;

    const modal = document.getElementById('candidate-modal');
    if (!modal) return;

    // 1. Text Fields
    document.getElementById('m-name').textContent = c.name || c.filename;
    document.getElementById('m-email').innerHTML = `<ion-icon name="mail-outline"></ion-icon> ${c.email || 'N/A'}`;
    document.getElementById('m-phone').innerHTML = `<ion-icon name="call-outline"></ion-icon> ${c.phone || 'N/A'}`;

    document.getElementById('m-match-score').textContent = (c.match_score !== undefined && c.match_score !== null) ? Number(c.match_score).toFixed(1) + '%' : '0%';
    document.getElementById('m-interview-score').textContent = c.interview_score ? c.interview_score + '/100' : '-';
    document.getElementById('m-final-score').textContent = c.final_score ? c.final_score.toFixed(1) + '%' : '-';

    // NEW: Evaluation Details
    let evalData = null;
    try {
        if (c.resume_evaluation_data) {
            evalData = typeof c.resume_evaluation_data === 'string' ? JSON.parse(c.resume_evaluation_data) : c.resume_evaluation_data;
        }
    } catch (e) { }

    // Inject Decision Tag if available
    const decisionElem = document.createElement('div');
    if (evalData && evalData.decision) {
        let color = 'var(--text-muted)';
        let bg = 'rgba(0,0,0,0.05)';
        if (evalData.decision.includes('Strong')) { color = 'var(--success)'; bg = 'rgba(0,255,100,0.1)'; }
        if (evalData.decision.includes('Borderline')) { color = '#b35900'; bg = 'rgba(255,165,0,0.1)'; } // Orange-ish
        if (evalData.decision.includes('Weak')) { color = 'var(--error)'; bg = 'rgba(255,0,0,0.1)'; }

        // We can try to guess the role or just say "Role-Based Evaluation"
        decisionElem.innerHTML = `
        <div class="stat-box" style="margin-top:1.5rem; border:1px solid ${color}; background:${bg}; padding:1rem; border-radius:8px;">
            <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:1px; font-weight:bold; color:var(--text-muted); margin-bottom:0.5rem;">Virex Evaluation</div>
            <div class="stat-value" style="font-size:1.1rem; color:${color}; margin-bottom:0.5rem;">${evalData.decision}</div>
            
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.5rem; font-size:0.85rem; margin-top:0.8rem; border-top:1px solid rgba(0,0,0,0.1); padding-top:0.8rem;">
                 <div><span style="opacity:0.6;">Education:</span> <b>${evalData.likert_scores.education}/5</b></div>
                 <div><span style="opacity:0.6;">Experience:</span> <b>${evalData.likert_scores.experience}/5</b></div>
                 <div><span style="opacity:0.6;">Skills:</span> <b>${evalData.likert_scores.skills}/5</b></div>
                 <div><span style="opacity:0.6;">Projects:</span> <b>${evalData.likert_scores.projects}/5</b></div>
                 <div style="grid-column:1/-1;"><span style="opacity:0.6;">Certs:</span> <b>${evalData.likert_scores.certifications}/5</b></div>
            </div>
        </div>`;
    } else {
        // Fallback for legacy candidates
        decisionElem.innerHTML = `<div style="margin-top:1rem; padding:1rem; border:1px dashed #ccc; border-radius:8px; font-size:0.85rem; opacity:0.6; text-align:center;">
            Basic Match (Legacy)<br>Re-upload JSON/Resume to see Virex Evaluation
         </div>`;
    }

    // Remove existing
    const perfContainer = document.getElementById('m-final-score').parentNode.parentNode;
    const existingDecision = perfContainer.querySelector('.decision-box');
    if (existingDecision) existingDecision.remove();

    decisionElem.classList.add('decision-box');
    perfContainer.appendChild(decisionElem);

    // 2. Badges
    const badgeContainer = document.getElementById('m-badges');
    badgeContainer.innerHTML = '';
    if (c.final_score > 75) {
        badgeContainer.innerHTML += `<span class="tag" style="background:var(--success); color:white;">Top Pick</span>`;
    }
    if (c.status === 'completed' || c.status === 'Interviewed') {
        badgeContainer.innerHTML += `<span class="tag" style="background:var(--primary); color:white;">Interviewed</span>`;
    }

    // 3. Skills
    const matchedContainer = document.getElementById('m-matched-skills');
    matchedContainer.innerHTML = '';

    let matched = [];
    try {
        if (typeof c.matched_skills === 'string') {
            matched = JSON.parse(c.matched_skills);
        } else if (Array.isArray(c.matched_skills)) {
            matched = c.matched_skills;
        }
    } catch (e) { console.error("Error parsing matched skills", e); }

    if (matched && matched.length) {
        matched.forEach(s => matchedContainer.innerHTML += `<span class="tag" style="background:var(--success); color:white; border:1px solid black; box-shadow:2px 2px 0px black;">${s}</span>`);
    } else {
        matchedContainer.innerHTML = '<span style="opacity:0.5; font-size:0.8rem;">None detected</span>';
    }

    const missingContainer = document.getElementById('m-missing-skills');
    missingContainer.innerHTML = '';

    let missing = [];
    try {
        if (typeof c.missing_skills === 'string') {
            missing = JSON.parse(c.missing_skills);
        } else if (Array.isArray(c.missing_skills)) {
            missing = c.missing_skills;
        }
    } catch (e) { console.error("Error parsing missing skills", e); }

    if (missing && missing.length) {
        missing.forEach(s => missingContainer.innerHTML += `<span class="tag" style="background:var(--error); color:white; border:1px solid black; box-shadow:2px 2px 0px black;">${s}</span>`);
    } else {
        missingContainer.innerHTML = '<span style="opacity:0.5; font-size:0.8rem;">None missing</span>';
    }

    // 4. Transcript
    const transcriptContainer = document.getElementById('m-transcript');
    transcriptContainer.innerHTML = '';

    let feedback = null;
    try {
        if (c.feedback_data) {
            feedback = typeof c.feedback_data === 'string' ? JSON.parse(c.feedback_data) : c.feedback_data;
        }
    } catch (e) { console.error("Error parsing feedback", e); }

    let transcriptList = [];
    if (feedback) {
        if (Array.isArray(feedback)) {
            transcriptList = feedback;
        } else if (feedback.transcript && Array.isArray(feedback.transcript)) {
            transcriptList = feedback.transcript;
        }
    }

    if (transcriptList.length > 0) {
        transcriptList.forEach((t, i) => {
            const div = document.createElement('div');
            div.className = 'transcript-item';
            div.innerHTML = `
                <div style="font-size:0.8rem; font-weight:bold; color:var(--text-muted); margin-bottom:0.3rem;">Question ${i + 1}</div>
                <div style="font-style:italic; margin-bottom:0.5rem;">"${t.q}"</div>
                <div style="padding-left:0.5rem; border-left:2px solid var(--primary); margin-bottom:0.5rem;">
                    ${t.a}
                </div>
                <div style="display:flex; justify-content:space-between; font-size:0.8rem;">
                    <span style="color:var(--success); font-weight:bold;">Score: ${t.score}/10</span>
                    <span style="opacity:0.7;">${t.feedback || ''}</span>
                </div>
             `;
            transcriptContainer.appendChild(div);
        });
    } else {
        transcriptContainer.innerHTML = `<div style="text-align:center; opacity:0.6; margin-top:2rem;">
            ${c.status === 'completed' ? 'Report structure unavailable or empty.' : 'Candidate has not completed the interview.'}
         </div>`;
    }

    // Show
    modal.classList.remove('hidden');

    // 5. Download Button
    const dlBtn = document.getElementById('m-download-btn');
    if (dlBtn) {
        if (transcriptList.length > 0) {
            dlBtn.classList.remove('hidden');
            dlBtn.onclick = () => downloadRecruiterReport(c);
        } else {
            dlBtn.classList.add('hidden');
        }
    }
}

function downloadRecruiterReport(c) {
    let content = `VIREX AI - CANDIDATE REPORT\n`;
    content += `================================\n`;
    content += `Candidate: ${c.name || c.filename}\n`;
    content += `Email: ${c.email || 'N/A'}\n`;
    content += `Date: ${new Date().toLocaleString()}\n\n`;

    content += `SCORES\n`;
    content += `------\n`;
    content += `Resume Match: ${c.match_score ? c.match_score.toFixed(1) : 0}%\n`;
    content += `Interview Score: ${c.interview_score || 0}/100\n`;
    content += `Final Score: ${c.final_score ? c.final_score.toFixed(1) : 0}%\n\n`;

    content += `SKILLS ANALYSIS\n`;
    content += `---------------\n`;

    let matched = [];
    try { matched = typeof c.matched_skills === 'string' ? JSON.parse(c.matched_skills) : (c.matched_skills || []); } catch (e) { }
    content += `Matched: ${matched.join(', ') || 'None'}\n\n`;

    let missing = [];
    try { missing = typeof c.missing_skills === 'string' ? JSON.parse(c.missing_skills) : (c.missing_skills || []); } catch (e) { }
    content += `Missing: ${missing.join(', ') || 'None'}\n\n`;

    content += `INTERVIEW TRANSCRIPT\n`;
    content += `====================\n\n`;

    let feedback = null;
    try {
        if (c.feedback_data) {
            feedback = typeof c.feedback_data === 'string' ? JSON.parse(c.feedback_data) : c.feedback_data;
        }
    } catch (e) { }

    let transcriptList = [];
    if (feedback) {
        if (Array.isArray(feedback)) {
            transcriptList = feedback;
        } else if (feedback.transcript && Array.isArray(feedback.transcript)) {
            transcriptList = feedback.transcript;
        }
    }

    if (transcriptList.length > 0) {
        transcriptList.forEach((t, i) => {
            content += `Q${i + 1}: ${t.q}\n`;
            content += `Answer: ${t.a}\n`;
            content += `Score: ${t.score}/10\n`;
            content += `Feedback: ${t.feedback || '-'}\n`;
            content += `------------------------------------------------\n\n`;
        });
    } else {
        content += `(Transcript unavailable or incomplete)\n`;
    }

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Report_${(c.name || 'Candidate').replace(/\s+/g, '_')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function closeModal() {
    document.getElementById('candidate-modal').classList.add('hidden');
}
