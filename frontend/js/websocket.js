/**
 * WebSocket Chat Client
 * Agentic Clinical Intelligence Platform
 */

(function() {
    let ws = null;
    const chatBody = document.getElementById('chat-body');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send-btn');
    const toggleBtn = document.getElementById('chat-toggle-btn');
    const widget = document.getElementById('chat-widget');
    const statusIndicator = document.querySelector('.status-indicator');
    
    let isMinimized = false;
    let isTyping = false;
    let currentReportId = null;

    // Expose init function to app.js
    window.initChat = function(reportId) {
        currentReportId = reportId;
        connectWebSocket(reportId);
    };

    function connectWebSocket(reportId) {
        // Close existing connection if any
        if (ws) {
            ws.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Assume backend is running on localhost:8000
        const wsUrl = `${protocol}//localhost:8000/api/v1/chat/ws/${reportId}`;
        
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket Connected');
            statusIndicator.classList.add('online');
            statusIndicator.style.backgroundColor = 'var(--safe-green)';
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.status === 'ready') {
                // Connection established message
                return;
            }

            if (data.error) {
                appendMessage(data.error, 'ai');
                return;
            }

            if (data.text) {
                removeTypingIndicator();
                appendMessage(data.text, 'ai', true); // Use typewriter for AI
            }
        };

        ws.onclose = () => {
            console.log('WebSocket Disconnected');
            statusIndicator.style.backgroundColor = 'var(--text-slate)';
            statusIndicator.classList.remove('online');
        };

        ws.onerror = (error) => {
            console.error('WebSocket Error:', error);
            statusIndicator.style.backgroundColor = 'var(--risk-red)';
        };
    }

    // ── UI Interactions ──────────────────────────────────────────────────

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    toggleBtn.addEventListener('click', () => {
        isMinimized = !isMinimized;
        if (isMinimized) {
            gsap.to(widget, { height: '60px', duration: 0.3, ease: 'power2.inOut' });
            toggleBtn.style.transform = 'rotate(180deg)';
        } else {
            gsap.to(widget, { height: '500px', duration: 0.3, ease: 'power2.inOut' });
            toggleBtn.style.transform = 'rotate(0deg)';
            scrollToBottom();
        }
    });

    function sendMessage() {
        const text = chatInput.value.trim();
        if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

        // Display user message
        appendMessage(text, 'user');
        chatInput.value = '';

        // Send to backend
        ws.send(text);

        // Show typing indicator
        showTypingIndicator();
    }

    function appendMessage(text, sender, useTypewriter = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `chat-message msg-${sender}`;
        
        // Initial state for animation
        msgDiv.style.opacity = '0';
        msgDiv.style.transform = 'translateY(10px)';
        
        chatBody.appendChild(msgDiv);
        scrollToBottom();

        // Animate message entry
        gsap.to(msgDiv, {
            opacity: 1,
            y: 0,
            duration: 0.3,
            ease: "back.out(1.5)"
        });

        if (useTypewriter && sender === 'ai') {
            typeWriterEffect(msgDiv, text, 0);
        } else {
            msgDiv.innerText = text;
        }
    }

    function typeWriterEffect(element, text, index) {
        if (index < text.length) {
            element.innerHTML += text.charAt(index);
            scrollToBottom();
            
            // Randomize typing speed slightly for realism (10ms - 30ms)
            const speed = Math.floor(Math.random() * 20) + 10;
            setTimeout(() => typeWriterEffect(element, text, index + 1), speed);
        }
    }

    function showTypingIndicator() {
        if (isTyping) return;
        isTyping = true;
        
        const wrapper = document.createElement('div');
        wrapper.id = 'typing-indicator-wrapper';
        wrapper.className = 'chat-message msg-ai';
        wrapper.style.padding = '0';
        wrapper.style.background = 'transparent';
        wrapper.style.border = 'none';
        wrapper.style.boxShadow = 'none';

        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        
        wrapper.appendChild(indicator);
        chatBody.appendChild(wrapper);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator-wrapper');
        if (indicator) {
            indicator.remove();
        }
        isTyping = false;
    }

    function scrollToBottom() {
        chatBody.scrollTop = chatBody.scrollHeight;
    }

})();
