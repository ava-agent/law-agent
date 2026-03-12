class ChatApp {
    constructor() {
        this.sessionId = null;
        this.isProcessing = false;

        this.messagesEl = document.getElementById('chat-messages');
        this.inputEl = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        this.loadingEl = document.getElementById('loading');
        this.caseInfoPanel = document.getElementById('case-info-panel');
        this.docsPanel = document.getElementById('docs-panel');
        this.quickActions = document.getElementById('quick-actions');

        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.inputEl.addEventListener('input', () => this.autoResizeInput());

        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.dataset.type;
                document.querySelectorAll('.quick-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.startSession(type);
            });
        });

        this.startSession();
    }

    async startSession(caseType = null) {
        try {
            const body = caseType ? { case_type: caseType } : {};
            const res = await fetch('/api/chat/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await res.json();
            this.sessionId = data.session_id;

            this.loadingEl.style.display = 'none';
            this.messagesEl.innerHTML = '';
            this.appendMessage('assistant', data.welcome_message);

            this.inputEl.disabled = false;
            this.sendBtn.disabled = false;
            this.inputEl.focus();
        } catch (err) {
            this.loadingEl.innerHTML = '<p style="color: #ef4444;">连接失败，请刷新页面重试</p>';
            console.error('Failed to start session:', err);
        }
    }

    async sendMessage() {
        const text = this.inputEl.value.trim();
        if (!text || this.isProcessing) return;

        this.isProcessing = true;
        this.inputEl.value = '';
        this.inputEl.style.height = 'auto';
        this.sendBtn.disabled = true;

        this.appendMessage('user', text);
        const assistantEl = this.appendMessage('assistant', '');
        const bubbleEl = assistantEl.querySelector('.message-bubble');

        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: text,
                }),
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let fullText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (!line.startsWith('data: ')) continue;
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;

                    try {
                        const parsed = JSON.parse(data);
                        if (parsed.type === 'text') {
                            fullText += parsed.content;
                            bubbleEl.innerHTML = this.renderMarkdown(fullText);
                            this.scrollToBottom();
                        } else if (parsed.type === 'action') {
                            const actions = JSON.parse(parsed.content);
                            this.renderActionCards(bubbleEl, actions);
                        } else if (parsed.type === 'case_info') {
                            const info = JSON.parse(parsed.content);
                            this.updateCaseInfo(info);
                        }
                    } catch (e) {
                        // skip malformed
                    }
                }
            }
        } catch (err) {
            bubbleEl.textContent = '网络错误，请重试。';
            console.error('Message error:', err);
        }

        this.isProcessing = false;
        this.sendBtn.disabled = false;
        this.inputEl.focus();
    }

    appendMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message message-${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'assistant' ? '⚖' : '👤';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        if (content) {
            bubble.innerHTML = this.renderMarkdown(content);
        }

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
        this.messagesEl.appendChild(msgDiv);
        this.scrollToBottom();
        return msgDiv;
    }

    renderActionCards(container, actions) {
        const cardsDiv = document.createElement('div');
        cardsDiv.className = 'action-cards';

        actions.forEach(action => {
            const btn = document.createElement('button');
            btn.className = 'action-card';
            btn.textContent = action.label;
            btn.addEventListener('click', () => this.handleAction(action));
            cardsDiv.appendChild(btn);
        });

        container.appendChild(cardsDiv);
        this.scrollToBottom();
    }

    async handleAction(action) {
        if (action.action === 'generate_doc') {
            await this.generateDocument(action.doc_type);
        } else if (action.action === 'show_platforms') {
            this.inputEl.value = '请告诉我详细的投诉平台和流程';
            this.sendMessage();
        }
    }

    async generateDocument(docType) {
        const labels = {
            complaint_letter: '投诉书',
            report_letter: '举报信',
            demand_letter: '协商函',
            civil_lawsuit: '民事起诉状',
            evidence_checklist: '证据清单',
            claim_letter: '索赔函',
        };
        const label = labels[docType] || docType;

        this.appendMessage('user', `请帮我生成${label}`);
        const loadingMsg = this.appendMessage('assistant', `正在生成【${label}】，请稍候...`);

        try {
            const res = await fetch('/api/document/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    doc_type: docType,
                }),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || '生成失败');
            }

            const data = await res.json();
            const bubble = loadingMsg.querySelector('.message-bubble');
            bubble.innerHTML = `
                <p>【${data.doc_type_label}】已生成！</p>
                <div class="action-cards">
                    <a href="${data.download_url}" class="action-card" download style="text-decoration:none;">
                        📥 下载 ${data.doc_type_label}
                    </a>
                </div>
                <p style="margin-top:8px;font-size:12px;color:#6b7280;">
                    提示：下载后请检查文书内容，补充姓名、身份证号等个人信息。
                </p>
            `;

            this.addDocToPanel(data.doc_type_label, data.download_url);
        } catch (err) {
            const bubble = loadingMsg.querySelector('.message-bubble');
            bubble.textContent = `生成失败：${err.message}`;
            console.error('Doc generation error:', err);
        }
    }

    updateCaseInfo(info) {
        this.caseInfoPanel.innerHTML = '';
        for (const [label, value] of Object.entries(info)) {
            const item = document.createElement('div');
            item.className = 'case-info-item';
            item.innerHTML = `
                <span class="case-info-label">${label}</span>
                <span class="case-info-value">${value}</span>
            `;
            this.caseInfoPanel.appendChild(item);
        }
    }

    addDocToPanel(label, url) {
        const placeholder = this.docsPanel.querySelector('.placeholder-text');
        if (placeholder) placeholder.remove();

        const item = document.createElement('div');
        item.className = 'doc-item';
        item.innerHTML = `<a href="${url}" download>📄 ${label}</a>`;
        this.docsPanel.appendChild(item);
    }

    renderMarkdown(text) {
        // Simple markdown rendering
        let html = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Headers
        html = html.replace(/^### (.+)$/gm, '<strong style="font-size:15px;">$1</strong>');
        html = html.replace(/^## (.+)$/gm, '<strong style="font-size:16px;">$1</strong>');

        // Bold
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

        // Horizontal rule
        html = html.replace(/^---$/gm, '<hr style="margin:12px 0;border:none;border-top:1px solid #e5e7eb;">');

        // List items
        html = html.replace(/^- (.+)$/gm, '• $1');
        html = html.replace(/^\d+\. (.+)$/gm, (match, p1, offset, str) => {
            return match;
        });

        // Line breaks
        html = html.replace(/\n/g, '<br>');

        return html;
    }

    autoResizeInput() {
        this.inputEl.style.height = 'auto';
        this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 120) + 'px';
    }

    scrollToBottom() {
        this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});
