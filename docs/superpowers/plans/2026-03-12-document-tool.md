# Document Tool Independent Entry Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a standalone document generation tool accessible from the sidebar, using a hybrid form (structured fields + free-text description) that shares the existing DocumentGenerator backend.

**Architecture:** New `/api/document/generate-direct` endpoint accepts form fields + description text without requiring a session. Frontend adds a document form view to the main content area, toggled via sidebar buttons. Both entry points (sidebar tool and in-chat) share `DocumentGenerator`.

**Tech Stack:** FastAPI, python-docx, Jinja2 HTML, vanilla CSS/JS (existing stack, no new deps)

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `app/models/schemas.py` | Modify | Add `DirectGenerateRequest` model |
| `app/routers/document.py` | Modify | Add `generate-direct` route, enhance `/types` to return field info |
| `templates/index.html` | Modify | Add document form view HTML, sidebar document tool section |
| `static/css/style.css` | Modify | Add form view styles |
| `static/js/chat.js` | Modify | Add view switching, form rendering, form submission logic |

---

## Task 1: Backend — New API endpoint and enhanced types

**Files:**
- Modify: `app/models/schemas.py`
- Modify: `app/routers/document.py`

- [ ] **Step 1: Add DirectGenerateRequest model to schemas.py**

Add after `GenerateDocumentRequest`:

```python
class DirectGenerateRequest(BaseModel):
    doc_type: DocumentType
    fields: Dict[str, str] = {}
    description: str = ""
```

- [ ] **Step 2: Add generate-direct route to document.py**

Add new import and route:

```python
from app.models.schemas import (
    GenerateDocumentRequest,
    GenerateDocumentResponse,
    DocumentTypeInfo,
    DirectGenerateRequest,
)

@router.post("/generate-direct", response_model=GenerateDocumentResponse)
async def generate_document_direct(request: DirectGenerateRequest):
    case_info = dict(request.fields)
    if request.description:
        case_info["problem_description"] = request.description

    file_id, result = doc_generator.generate(request.doc_type.value, case_info)

    doc_label = DOCUMENT_TYPE_LABELS.get(request.doc_type, request.doc_type.value)

    if result.startswith("http"):
        download_url = result
    else:
        download_url = f"/api/document/download/{file_id}"

    return GenerateDocumentResponse(
        file_id=file_id,
        download_url=download_url,
        doc_type=request.doc_type.value,
        doc_type_label=doc_label,
    )
```

- [ ] **Step 3: Enhance /types endpoint to return field info**

Update the `/types` route to include `required_fields` and `field_labels`:

```python
from app.prompts.document_prompts import DOC_REQUIRED_FIELDS, DOC_FIELD_LABELS

class DocumentTypeInfoExt(BaseModel):
    type: str
    label: str
    description: str
    required_fields: List[str] = []
    field_labels: Dict[str, str] = {}

@router.get("/types-ext")
async def list_document_types_extended():
    descriptions = {
        DocumentType.COMPLAINT_LETTER: "向市场监督管理局提交的消费者投诉书",
        DocumentType.REPORT_LETTER: "举报商家违法经营行为的举报信",
        DocumentType.DEMAND_LETTER: "向商家发送的正式协商/要求函",
        DocumentType.CIVIL_LAWSUIT: "向人民法院提起诉讼的民事起诉状",
        DocumentType.EVIDENCE_CHECKLIST: "整理维权证据的清单",
        DocumentType.CLAIM_LETTER: "向商家发送的正式索赔函",
    }
    result = []
    for dt in DocumentType:
        fields = DOC_REQUIRED_FIELDS.get(dt.value, [])
        labels = {f: DOC_FIELD_LABELS.get(f, f) for f in fields}
        result.append({
            "type": dt.value,
            "label": DOCUMENT_TYPE_LABELS[dt],
            "description": descriptions.get(dt, ""),
            "required_fields": fields,
            "field_labels": labels,
        })
    return result
```

- [ ] **Step 4: Test the new endpoints**

Run locally and verify:
```bash
# Test types-ext
curl http://localhost:8000/api/document/types-ext | python3 -m json.tool

# Test generate-direct
curl -X POST http://localhost:8000/api/document/generate-direct \
  -H "Content-Type: application/json" \
  -d '{"doc_type": "complaint_letter", "fields": {"complainant_name": "张三", "merchant_name": "某商店"}, "description": "买到假货"}'
```

- [ ] **Step 5: Commit**

```bash
git add app/models/schemas.py app/routers/document.py
git commit -m "feat: 新增文书直接生成 API 端点"
```

---

## Task 2: Frontend — Sidebar document tool buttons

**Files:**
- Modify: `templates/index.html`
- Modify: `static/css/style.css`

- [ ] **Step 1: Add document tool section to sidebar in index.html**

Add a new sidebar section before the existing "案件信息" section, plus a "智能咨询" nav button:

```html
<!-- Inside <aside class="sidebar">, as the FIRST child -->
<div class="sidebar-section">
    <h3>功能导航</h3>
    <div class="sidebar-nav">
        <button class="sidebar-nav-btn active" id="nav-chat">智能咨询</button>
        <button class="sidebar-nav-btn" id="nav-docs">文书工具</button>
    </div>
</div>
<div class="sidebar-section" id="doc-tool-section" style="display:none;">
    <h3>选择文书类型</h3>
    <div id="doc-tool-buttons" class="doc-tool-buttons">
        <!-- Populated by JS -->
    </div>
</div>
```

- [ ] **Step 2: Add document form view container to main content in index.html**

Add after `.chat-container` div, as a sibling inside `.main-content`:

```html
<!-- Document Form View (hidden by default) -->
<div class="doc-form-container" id="doc-form-container" style="display:none;">
    <div class="doc-form-inner">
        <div class="doc-form-header">
            <h2 id="doc-form-title">投诉书</h2>
            <p id="doc-form-desc" class="doc-form-description"></p>
        </div>
        <form id="doc-form" class="doc-form">
            <div id="doc-form-fields" class="doc-form-fields">
                <!-- Dynamic fields rendered by JS -->
            </div>
            <div class="doc-form-group">
                <label for="doc-form-description">情况描述</label>
                <textarea id="doc-form-description" rows="5" placeholder="请详细描述您遇到的问题、经过和诉求..."></textarea>
            </div>
            <div class="doc-form-actions">
                <button type="submit" class="doc-form-submit" id="doc-form-submit">生成文书</button>
            </div>
        </form>
        <div id="doc-form-result" class="doc-form-result" style="display:none;">
            <!-- Download link rendered by JS -->
        </div>
    </div>
</div>
```

- [ ] **Step 3: Add CSS styles for sidebar nav and document form**

Append to `static/css/style.css`:

```css
/* ─── Sidebar Nav ─────────────────────────── */

.sidebar-nav {
    display: flex;
    gap: 6px;
}

.sidebar-nav-btn {
    flex: 1;
    padding: 8px 12px;
    border: 1px solid var(--border-dark);
    border-radius: var(--radius-sm);
    background: transparent;
    color: var(--text-on-dark-muted);
    font-size: 12px;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all 0.25s;
}

.sidebar-nav-btn.active {
    background: var(--gold-dim);
    border-color: var(--gold);
    color: var(--gold-light);
}

.sidebar-nav-btn:hover:not(.active) {
    border-color: var(--text-on-dark-muted);
    color: var(--text-on-dark);
}

/* ─── Doc Tool Buttons ────────────────────── */

.doc-tool-buttons {
    display: flex;
    flex-direction: column;
    gap: 6px;
}

.doc-tool-btn {
    padding: 10px 14px;
    border: 1px solid var(--border-dark);
    border-radius: var(--radius-sm);
    background: var(--ink-light);
    color: var(--text-on-dark);
    font-size: 13px;
    font-family: var(--font-sans);
    cursor: pointer;
    transition: all 0.25s;
    text-align: left;
}

.doc-tool-btn:hover {
    border-color: var(--gold);
    background: var(--ink-lighter);
    box-shadow: var(--shadow-gold);
}

.doc-tool-btn.active {
    border-color: var(--gold);
    background: var(--gold-dim);
    color: var(--gold-light);
}

/* ─── Document Form ───────────────────────── */

.doc-form-container {
    flex: 1;
    background: var(--parchment);
    overflow-y: auto;
    padding: 40px;
}

.doc-form-inner {
    max-width: 640px;
    margin: 0 auto;
}

.doc-form-header {
    margin-bottom: 32px;
}

.doc-form-header h2 {
    font-family: var(--font-serif);
    font-size: 24px;
    color: var(--ink);
    margin-bottom: 8px;
}

.doc-form-description {
    color: var(--text-secondary);
    font-size: 14px;
}

.doc-form-fields {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 20px;
}

.doc-form-group {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 16px;
}

.doc-form-group.full-width {
    grid-column: 1 / -1;
}

.doc-form-group label {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
}

.doc-form-group input,
.doc-form-group textarea {
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    background: var(--white);
    font-size: 14px;
    font-family: var(--font-sans);
    color: var(--text-primary);
    transition: border-color 0.25s, box-shadow 0.25s;
}

.doc-form-group input:focus,
.doc-form-group textarea:focus {
    outline: none;
    border-color: var(--gold);
    box-shadow: 0 0 0 3px var(--gold-dim);
}

.doc-form-group textarea {
    resize: vertical;
    min-height: 100px;
}

.doc-form-actions {
    margin-top: 24px;
}

.doc-form-submit {
    padding: 12px 32px;
    background: linear-gradient(135deg, var(--ink) 0%, var(--ink-light) 100%);
    color: var(--gold-light);
    border: none;
    border-radius: var(--radius-sm);
    font-size: 15px;
    font-family: var(--font-sans);
    font-weight: 500;
    cursor: pointer;
    transition: all 0.25s;
    letter-spacing: 0.5px;
}

.doc-form-submit:hover:not(:disabled) {
    box-shadow: var(--shadow-lg);
    transform: translateY(-1px);
}

.doc-form-submit:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.doc-form-result {
    margin-top: 24px;
    padding: 20px;
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    text-align: center;
}

.doc-form-result a {
    display: inline-block;
    padding: 12px 28px;
    background: linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%);
    color: var(--ink);
    border-radius: var(--radius-sm);
    text-decoration: none;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.25s;
}

.doc-form-result a:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-gold);
}

@media (max-width: 640px) {
    .doc-form-container {
        padding: 20px 16px;
    }
    .doc-form-fields {
        grid-template-columns: 1fr;
    }
}
```

- [ ] **Step 4: Commit**

```bash
git add templates/index.html static/css/style.css
git commit -m "feat: 添加文书工具侧边栏和表单视图 HTML/CSS"
```

---

## Task 3: Frontend — JavaScript view switching and form logic

**Files:**
- Modify: `static/js/chat.js`

- [ ] **Step 1: Add properties and init logic for doc tool to ChatApp constructor**

Add after existing property assignments in `constructor()`:

```javascript
// Doc tool elements
this.chatContainer = document.querySelector('.chat-container');
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
this.currentView = 'chat'; // 'chat' or 'doc-form'
this.currentDocType = null;
this.docTypes = [];

// Nav buttons
this.navChat.addEventListener('click', () => this.switchView('chat'));
this.navDocs.addEventListener('click', () => this.switchView('doc-tool'));

// Form submit
this.docForm.addEventListener('submit', (e) => {
    e.preventDefault();
    this.submitDocForm();
});

// Load doc types
this.loadDocTypes();
```

- [ ] **Step 2: Add loadDocTypes method**

```javascript
async loadDocTypes() {
    try {
        const res = await fetch('/api/document/types-ext');
        this.docTypes = await res.json();
    } catch (err) {
        console.error('Failed to load doc types:', err);
    }
}
```

- [ ] **Step 3: Add switchView method**

```javascript
switchView(view) {
    // Update nav buttons
    this.navChat.classList.toggle('active', view === 'chat');
    this.navDocs.classList.toggle('active', view === 'doc-tool');

    if (view === 'chat') {
        this.chatContainer.style.display = 'flex';
        this.docFormContainer.style.display = 'none';
        this.docToolSection.style.display = 'none';
        // Show existing sidebar sections
        document.querySelectorAll('.sidebar-section').forEach(s => {
            if (s.id !== 'doc-tool-section') s.style.display = '';
        });
        this.currentView = 'chat';
    } else if (view === 'doc-tool') {
        this.chatContainer.style.display = 'none';
        this.docFormContainer.style.display = 'none';
        // Hide chat sidebar sections, show doc tool section
        document.querySelectorAll('.sidebar-section').forEach(s => {
            if (s.id === 'doc-tool-section') {
                s.style.display = '';
            } else if (s.querySelector('.sidebar-nav')) {
                s.style.display = ''; // keep nav visible
            } else {
                s.style.display = 'none';
            }
        });
        this.docToolSection.style.display = '';
        this.renderDocToolButtons();
        this.currentView = 'doc-tool';
    }
    this.closeSidebar();
}
```

- [ ] **Step 4: Add renderDocToolButtons and openDocForm methods**

```javascript
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

    // Highlight active button in sidebar
    this.docToolButtons.querySelectorAll('.doc-tool-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent === docType.label);
    });

    this.chatContainer.style.display = 'none';
    this.docFormContainer.style.display = '';
}
```

- [ ] **Step 5: Add submitDocForm method**

```javascript
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
```

- [ ] **Step 6: Commit**

```bash
git add static/js/chat.js
git commit -m "feat: 添加文书工具前端视图切换和表单提交逻辑"
```

---

## Task 4: Integration test and deploy

- [ ] **Step 1: Local test**

Run `python main.py`, verify:
1. Sidebar shows "智能咨询" / "文书工具" nav
2. Clicking "文书工具" shows 6 document type buttons
3. Clicking a type shows the form with correct fields
4. Filling and submitting generates a .docx and shows download link
5. Switching back to "智能咨询" restores chat view with state intact

- [ ] **Step 2: Push and deploy**

```bash
git push origin main
vercel --prod
```

- [ ] **Step 3: Verify on production**

Visit https://law-agent-eosin.vercel.app and test the document tool flow end-to-end.
