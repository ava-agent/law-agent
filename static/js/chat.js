class ChatApp {
    constructor() {
        this.sessionId = null;
        this.isProcessing = false;

        // Chat elements
        this.messagesEl = document.getElementById('chat-messages');
        this.inputEl = document.getElementById('user-input');
        this.sendBtn = document.getElementById('send-btn');
        this.loadingEl = document.getElementById('loading');
        this.caseInfoPanel = document.getElementById('case-info-panel');
        this.docsPanel = document.getElementById('docs-panel');
        this.quickActions = document.getElementById('quick-actions');
        this.sidebar = document.getElementById('sidebar');
        this.sidebarOverlay = document.getElementById('sidebar-overlay');
        this.sidebarToggle = document.getElementById('sidebar-toggle');

        // Doc tool elements
        this.chatContainer = document.getElementById('chat-container');
        this.docFormContainer = document.getElementById('doc-form-container');
        this.docForm = document.getElementById('doc-form');
        this.docFormFields = document.getElementById('doc-form-fields');
        this.docFormTitle = document.getElementById('doc-form-title');
        this.docFormDesc = document.getElementById('doc-form-desc');
        this.docFormDescription = document.getElementById('doc-form-description');
        this.docFormSubmit = document.getElementById('doc-form-submit');
        this.docFormResult = document.getElementById('doc-form-result');
        this.docToolSection = document.getElementById('doc-tool-section');
        this.docToolButtons = document.getElementById('doc-tool-buttons');
        this.navChat = document.getElementById('nav-chat');
        this.navDocs = document.getElementById('nav-docs');
        this.sidebarCaseInfo = document.getElementById('sidebar-case-info');
        this.sidebarDocs = document.getElementById('sidebar-docs');
        this.currentView = 'chat';
        this.currentDocType = null;
        this.docTypes = [];

        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        this.inputEl.addEventListener('input', () => this.autoResizeInput());

        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }
        if (this.sidebarOverlay) {
            this.sidebarOverlay.addEventListener('click', () => this.closeSidebar());
        }

        // Nav buttons
        this.navChat.addEventListener('click', () => this.switchView('chat'));
        this.navDocs.addEventListener('click', () => this.switchView('doc-tool'));

        // Doc form submit
        this.docForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitDocForm();
        });

        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.dataset.type;
                document.querySelectorAll('.quick-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.startSession(type);
            });
        });

        this.startSession();
        this.loadDocTypes();
    }

    toggleSidebar() {
        this.sidebar.classList.toggle('open');
        this.sidebarOverlay.classList.toggle('open');
    }

    closeSidebar() {
        this.sidebar.classList.remove('open');
        this.sidebarOverlay.classList.remove('open');
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
            this.clearMessages();
            this.appendMessage('assistant', data.welcome_message);

            this.inputEl.disabled = false;
            this.sendBtn.disabled = false;
            this.inputEl.focus();
        } catch (err) {
            this.loadingEl.textContent = '';
            const errIcon = document.createElement('p');
            errIcon.style.cssText = 'font-size:24px;margin-bottom:12px;color:var(--danger)';
            errIcon.textContent = '\u26A0';
            const errText = document.createElement('p');
            errText.style.color = 'var(--danger)';
            errText.textContent = '连接失败，请刷新页面重试';
            this.loadingEl.appendChild(errIcon);
            this.loadingEl.appendChild(errText);
            console.error('Failed to start session:', err);
        }
    }

    clearMessages() {
        while (this.messagesEl.firstChild) {
            this.messagesEl.removeChild(this.messagesEl.firstChild);
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
        const typingEl = this.showTypingIndicator();

        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: text,
                }),
            });

            typingEl.remove();
            const assistantEl = this.appendMessage('assistant', '');
            const bubbleEl = assistantEl.querySelector('.message-bubble');

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
                            this.setRenderedMarkdown(bubbleEl, fullText);
                            this.scrollToBottom();
                        } else if (parsed.type === 'action') {
                            const actions = JSON.parse(parsed.content);
                            this.renderActionCards(bubbleEl, actions);
                        } else if (parsed.type === 'case_info') {
                            const info = JSON.parse(parsed.content);
                            this.updateCaseInfo(info);
                        }
                    } catch (e) {
                        // skip malformed events
                    }
                }
            }
        } catch (err) {
            typingEl.remove();
            const errEl = this.appendMessage('assistant', '');
            errEl.querySelector('.message-bubble').textContent = '网络错误，请重试。';
            console.error('Message error:', err);
        }

        this.isProcessing = false;
        this.sendBtn.disabled = false;
        this.inputEl.focus();
    }

    showTypingIndicator() {
        const wrapper = document.createElement('div');
        wrapper.className = 'message message-assistant';

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '\u2696';

        const dots = document.createElement('div');
        dots.className = 'typing-dots';
        for (let i = 0; i < 3; i++) {
            dots.appendChild(document.createElement('span'));
        }

        wrapper.appendChild(avatar);
        wrapper.appendChild(dots);
        this.messagesEl.appendChild(wrapper);
        this.scrollToBottom();
        return wrapper;
    }

    appendMessage(role, content) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message message-${role}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'assistant' ? '\u2696' : '\u4F60';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        if (content) {
            this.setRenderedMarkdown(bubble, content);
        }

        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
        this.messagesEl.appendChild(msgDiv);
        this.scrollToBottom();
        return msgDiv;
    }

    /**
     * Renders server-generated markdown content into a DOM element.
     * Content is first escaped (& < >) then parsed for markdown syntax.
     * Source: AI model responses from our own backend only.
     */
    setRenderedMarkdown(el, text) {
        // Escape HTML entities first for safety
        let html = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Markdown transformations on escaped content
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/^---$/gm, '<hr>');
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');
        html = html.replace(/\n(?!<)/g, '<br>');
        html = html.replace(/<br>(<(?:h[23]|ul|hr|li))/g, '$1');

        // Use DOM parser to safely set content from escaped+transformed markdown
        const doc = new DOMParser().parseFromString(html, 'text/html');
        el.textContent = '';
        while (doc.body.firstChild) {
            el.appendChild(doc.body.firstChild);
        }
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
            bubble.textContent = '';

            const title = document.createElement('p');
            const strong = document.createElement('strong');
            strong.textContent = `【${data.doc_type_label}】已生成`;
            title.appendChild(strong);
            bubble.appendChild(title);

            const cards = document.createElement('div');
            cards.className = 'action-cards';
            const link = document.createElement('a');
            link.href = data.download_url;
            link.className = 'action-card';
            link.download = '';
            link.textContent = `\uD83D\uDCE5 下载 ${data.doc_type_label}`;
            cards.appendChild(link);
            bubble.appendChild(cards);

            const tip = document.createElement('p');
            tip.style.cssText = 'margin-top:10px;font-size:12px;color:var(--text-muted)';
            tip.textContent = '提示：下载后请检查文书内容，补充姓名、身份证号等个人信息。';
            bubble.appendChild(tip);

            this.addDocToPanel(data.doc_type_label, data.download_url);
        } catch (err) {
            const bubble = loadingMsg.querySelector('.message-bubble');
            bubble.textContent = `生成失败：${err.message}`;
            console.error('Doc generation error:', err);
        }
    }

    updateCaseInfo(info) {
        this.caseInfoPanel.textContent = '';
        for (const [label, value] of Object.entries(info)) {
            const item = document.createElement('div');
            item.className = 'case-info-item';

            const labelSpan = document.createElement('span');
            labelSpan.className = 'case-info-label';
            labelSpan.textContent = label;

            const valueSpan = document.createElement('span');
            valueSpan.className = 'case-info-value';
            valueSpan.textContent = value;

            item.appendChild(labelSpan);
            item.appendChild(valueSpan);
            this.caseInfoPanel.appendChild(item);
        }
    }

    addDocToPanel(label, url) {
        const placeholder = this.docsPanel.querySelector('.placeholder-text');
        if (placeholder) placeholder.remove();

        const item = document.createElement('div');
        item.className = 'doc-item';
        const link = document.createElement('a');
        link.href = url;
        link.download = '';
        link.textContent = `\uD83D\uDCC4 ${label}`;
        item.appendChild(link);
        this.docsPanel.appendChild(item);
    }

    // ─── Doc Tool Methods ─────────────────────

    async loadDocTypes() {
        try {
            const res = await fetch('/api/document/types-ext');
            this.docTypes = await res.json();
        } catch (err) {
            console.error('Failed to load doc types:', err);
        }
    }

    switchView(view) {
        this.navChat.classList.toggle('active', view === 'chat');
        this.navDocs.classList.toggle('active', view === 'doc-tool');

        if (view === 'chat') {
            this.chatContainer.style.display = 'flex';
            this.docFormContainer.style.display = 'none';
            this.docToolSection.style.display = 'none';
            this.sidebarCaseInfo.style.display = '';
            this.sidebarDocs.style.display = '';
            this.currentView = 'chat';
        } else {
            this.chatContainer.style.display = 'none';
            this.docFormContainer.style.display = 'none';
            this.docToolSection.style.display = '';
            this.sidebarCaseInfo.style.display = 'none';
            this.sidebarDocs.style.display = '';
            this.renderDocToolButtons();
            this.currentView = 'doc-tool';
        }
        this.closeSidebar();
    }

    renderDocToolButtons() {
        this.docToolButtons.textContent = '';
        this.docTypes.forEach(dt => {
            const btn = document.createElement('button');
            btn.className = 'doc-tool-btn';
            btn.textContent = dt.label;
            btn.addEventListener('click', () => this.openDocForm(dt));
            this.docToolButtons.appendChild(btn);
        });
    }

    openDocForm(docType) {
        this.currentDocType = docType;
        this.docFormTitle.textContent = docType.label;
        this.docFormDesc.textContent = docType.description;
        this.docFormResult.style.display = 'none';
        this.docFormSubmit.disabled = false;
        this.docFormSubmit.textContent = '生成文书';
        this.docFormDescription.value = '';

        // Render form fields
        this.docFormFields.textContent = '';
        const fields = docType.required_fields || [];
        const labels = docType.field_labels || {};
        fields.forEach(field => {
            // Skip fields handled by the description textarea
            if (field === 'problem_description' || field === 'evidence_available') return;
            const group = document.createElement('div');
            group.className = 'doc-form-group';
            const label = document.createElement('label');
            label.setAttribute('for', 'field-' + field);
            label.textContent = labels[field] || field;
            const input = document.createElement('input');
            input.type = 'text';
            input.id = 'field-' + field;
            input.name = field;
            input.placeholder = labels[field] || field;
            group.appendChild(label);
            group.appendChild(input);
            this.docFormFields.appendChild(group);
        });

        // Highlight active button
        this.docToolButtons.querySelectorAll('.doc-tool-btn').forEach(btn => {
            btn.classList.toggle('active', btn.textContent === docType.label);
        });

        this.chatContainer.style.display = 'none';
        this.docFormContainer.style.display = '';
    }

    async submitDocForm() {
        if (!this.currentDocType) return;

        this.docFormSubmit.disabled = true;
        this.docFormSubmit.textContent = '生成中...';
        this.docFormResult.style.display = 'none';

        const fields = {};
        this.docFormFields.querySelectorAll('input').forEach(input => {
            if (input.value.trim()) {
                fields[input.name] = input.value.trim();
            }
        });
        const description = this.docFormDescription.value.trim();

        try {
            const res = await fetch('/api/document/generate-direct', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    doc_type: this.currentDocType.type,
                    fields: fields,
                    description: description,
                }),
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || '生成失败');
            }

            const data = await res.json();

            this.docFormResult.textContent = '';

            const successText = document.createElement('p');
            successText.style.cssText = 'margin-bottom:12px;color:var(--success);font-weight:600;';
            successText.textContent = '\u2714 ' + data.doc_type_label + ' 已生成';
            this.docFormResult.appendChild(successText);

            const link = document.createElement('a');
            link.href = data.download_url;
            link.download = '';
            link.textContent = '\uD83D\uDCE5 下载 ' + data.doc_type_label;
            this.docFormResult.appendChild(link);

            const tip = document.createElement('p');
            tip.style.cssText = 'margin-top:12px;font-size:12px;color:var(--text-muted);';
            tip.textContent = '提示：下载后请检查文书内容，补充个人敏感信息（如身份证号）。';
            this.docFormResult.appendChild(tip);

            this.docFormResult.style.display = '';
            this.addDocToPanel(data.doc_type_label, data.download_url);
        } catch (err) {
            this.docFormResult.textContent = '';
            const errText = document.createElement('p');
            errText.style.color = 'var(--danger)';
            errText.textContent = '生成失败：' + err.message;
            this.docFormResult.appendChild(errText);
            this.docFormResult.style.display = '';
        }

        this.docFormSubmit.disabled = false;
        this.docFormSubmit.textContent = '生成文书';
    }

    autoResizeInput() {
        this.inputEl.style.height = 'auto';
        this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 120) + 'px';
    }

    scrollToBottom() {
        requestAnimationFrame(() => {
            this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});
