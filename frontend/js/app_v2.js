/**
 * Frontend Logic & API Integration
 * Agentic Clinical Intelligence Platform
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── DOM Elements ────────────────────────────────────────────────────────
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    
    const sections = {
        upload: document.getElementById('upload-section'),
        loading: document.getElementById('loading-section'),
        results: document.getElementById('results-section')
    };

    const statusText = document.getElementById('loading-status');
    const API_BASE = 'http://localhost:8000/api/v1'; // Assuming default local port

    let confidenceChartInstance = null;
    
    // ── Tactical Hackathon Nav Fallback ──────────────────────────────────────
    document.querySelectorAll('nav a').forEach(link => {
        if (link.textContent.trim() !== 'Dashboard') {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                alert("Observability & Settings modules are currently in Beta/Enterprise mode. Please view the Agentic Pipeline on the Dashboard.");
            });
        }
    });

    // ── File Drag & Drop Logic ──────────────────────────────────────────────
    dropZone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('dragover'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) handleFile(files[0]);
    });

    fileInput.addEventListener('change', function() {
        if (this.files.length) handleFile(this.files[0]);
    });

    let isAnalyzing = false;

    // ── File Upload & Pipeline Execution ────────────────────────────────────
    async function handleFile(file) {
        if (isAnalyzing) return;
        
        // Validate
        if (!file.name.match(/\.(txt|pdf)$/i)) {
            alert("Only TXT and PDF files are supported.");
            return;
        }

        isAnalyzing = true;
        fileInput.disabled = true;

        // Transition to Loading State
        transitionSection(sections.upload, sections.loading);
        
        // Dynamic loading text updates to simulate pipeline steps
        const pipelineSteps = [
            "Orchestrator extracting raw text...",
            "Context Agent retrieving Fivetran history...",
            "Gemini 2.5 Flash analyzing clinical entities...",
            "Critic Agent validating confidence...",
            "DevSecOps monitoring pipeline..."
        ];
        
        let stepIdx = 0;
        const stepInterval = setInterval(() => {
            if (stepIdx < pipelineSteps.length) {
                statusText.innerText = pipelineSteps[stepIdx++];
            }
        }, 1500);

        // API Call
        const formData = new FormData();
        formData.append("file", file);
        // formData.append("patient_id", "pt-12345"); // Optional context injection

        try {
            const response = await fetch(`${API_BASE}/reports/analyze`, {
                method: 'POST',
                body: formData,
                cache: 'no-store'
            });

            clearInterval(stepInterval);
            
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Analysis failed");
            }

            const data = await response.json();
            
            // Populate Results
            populateResults(data);
            
            // Transition to Results State
            transitionSection(sections.loading, sections.results);
            
            // Trigger WebSocket connection for Chat
            if (window.initChat) {
                window.initChat(data.report_id);
            }

        } catch (error) {
            clearInterval(stepInterval);
            document.querySelector('#devsecops-status').innerHTML = `<span style="color: #EF4444;">Pipeline Failed: ${error.message}</span>`;
            document.querySelector('#upload-status').innerHTML = `<span style="color: #EF4444;">Error occurred during analysis.</span>`;
            setTimeout(() => {
                transitionSection(sections.loading, sections.upload);
                document.querySelector('#upload-status').innerHTML = '';
            }, 3000);
        } finally {
            isAnalyzing = false;
            fileInput.disabled = false;
            fileInput.value = '';
        }
    }

    // ── Populate Results UI ────────────────────────────────────────────────
    function safeParseMarkdown(data) {
        if (!data) return "Not available.";
        
        // If LLM returned an array, convert it to a markdown bulleted list
        if (Array.isArray(data)) {
            const bulletList = data.map(item => `- ${item}`).join('\n');
            return marked.parse(bulletList);
        }
        
        // If it's a string, parse it directly
        if (typeof data === 'string') {
            return marked.parse(data);
        }
        
        // Fallback for any other object type
        return marked.parse("```json\n" + JSON.stringify(data, null, 2) + "\n```");
    }

    function populateResults(data) {
        // Fallback in case the backend returns analysis directly or nested
        const result = data.analysis || data;

        // Map the 4 specific keys to their respective UI containers
        document.querySelector('#summary-content').innerHTML = typeof result.executive_summary === 'string' ? result.executive_summary : JSON.stringify(result.executive_summary || "No summary generated.");
        document.querySelector('#biomarkers-content').innerHTML = safeParseMarkdown(result.extracted_biomarkers);
        document.querySelector('#risks-content').innerHTML = safeParseMarkdown(result.critical_risks);
        document.querySelector('#suggestions-content').innerHTML = safeParseMarkdown(result.recommended_next_steps);

        // Map New Hackathon Panels
        const timelineContainer = document.querySelector('#reasoning-timeline') || document.querySelector('#timeline-content');
        if (timelineContainer) {
            const timelineData = data.reasoning_timeline || data.timeline || [];
            if (timelineData && Array.isArray(timelineData)) {
                timelineContainer.innerHTML = timelineData.map(step => `
                    <div style="padding: 5px; border-bottom: 1px solid #333;">
                        <strong>${step.step || 'Step'}:</strong> ${step.thought || ''}
                    </div>
                `).join('');
            }
        }

        window.updateObservability = function(liveData) {
            // Hook for live SSE/WebSocket updates during orchestration
            if (liveData.timeline) {
                const tl = document.querySelector('#timeline-content');
                const t = liveData.timeline;
                const li = document.createElement('li');
                li.innerHTML = `<span style="color:#00d4ff;">[${t.step || 'Agent'}]</span> ${t.thought}`;
                tl.appendChild(li);
            }
        };

        const ehr = data.analysis?.ehr_context || data.ehr_context || {};
        document.querySelector('#ehr-content').innerText = JSON.stringify(ehr, null, 2);

        const incident = data.incident || {};
        const incidentEl = document.querySelector('#incident-content');
        if (incident.escalation_triggered) {
            incidentEl.innerHTML = `<span class="risk-high">${incident.status}</span><br><strong>ID:</strong> ${incident.incident_id}`;
            document.querySelector('#gitlab-card').style.borderLeft = "6px solid #EF4444";
        } else {
            incidentEl.innerHTML = `<span class="status-safe">No Escalation</span>`;
        }

        const metadata = data.metadata || {};
        document.querySelector('#confidence-score').innerText = metadata.confidence ? (metadata.confidence * 100).toFixed(1) + "%" : "--";
        
        const actions = data.actions || [];
        document.querySelector('#actions-content').innerHTML = actions.join(', ') || "--";

        // Setup Exports
        const reportId = data.report_id;
        const pdfBtn = document.querySelector('#export-pdf-btn');
        const jsonBtn = document.querySelector('#export-json-btn');
        if (reportId) {
            pdfBtn.style.display = 'block';
            jsonBtn.style.display = 'block';
            pdfBtn.onclick = () => window.open(`${API_BASE}/export/${reportId}/pdf`, '_blank');
            jsonBtn.onclick = () => window.open(`${API_BASE}/export/${reportId}/json`, '_blank');
        }

        // Setup Chat Copilot
        window.currentReportId = reportId;
    }

    // ── Clinical Copilot Logic ──────────────────────────────────────────────
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatBody = document.getElementById('chat-body');

    async function sendChatMessage() {
        const msg = chatInput.value.trim();
        if (!msg) return;

        // Append User Message
        chatBody.innerHTML += `<div class="message user-message"><div class="message-content">${msg}</div></div>`;
        chatInput.value = '';
        chatBody.scrollTop = chatBody.scrollHeight;

        try {
            const res = await fetch(`${API_BASE}/chat/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: msg,
                    report_id: window.currentReportId
                })
            });

            if (!res.ok) throw new Error("Chat failed");
            
            const data = await res.json();
            const aiMsg = safeParseMarkdown(data.response);
            
            chatBody.innerHTML += `<div class="message ai-message"><div class="message-content">${aiMsg}</div></div>`;
            chatBody.scrollTop = chatBody.scrollHeight;
        } catch (e) {
            chatBody.innerHTML += `<div class="message ai-message"><div class="message-content" style="color:red;">Error: Copilot unavailable.</div></div>`;
        }
    }

    if (chatSendBtn && chatInput) {
        chatSendBtn.addEventListener('click', sendChatMessage);
        chatInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendChatMessage(); });
    }
    // ── GSAP Transitions ───────────────────────────────────────────────────
    function transitionSection(hideElement, showElement) {
        gsap.to(hideElement, {
            opacity: 0,
            y: -20,
            duration: 0.4,
            onComplete: () => {
                hideElement.classList.add('hidden');
                showElement.classList.remove('hidden');
                
                // Set initial state for entrance
                gsap.set(showElement, { opacity: 0, y: 20 });
                
                // Animate entrance
                gsap.to(showElement, {
                    opacity: 1,
                    y: 0,
                    duration: 0.6,
                    ease: "power3.out"
                });

                // CSS fade-in-up handles card animations now
                if (showElement.id === 'results-section') {
                    // Trigger chat widget appearance
                    setTimeout(() => {
                        const chatWidget = document.getElementById('chat-widget');
                        chatWidget.classList.remove('hidden');
                        gsap.fromTo(chatWidget,
                            { opacity: 0, y: 50, scale: 0.95 },
                            { opacity: 1, y: 0, scale: 1, duration: 0.6, ease: "back.out(1.7)" }
                        );
                    }, 1000);
                }
            }
        });
    }
});
