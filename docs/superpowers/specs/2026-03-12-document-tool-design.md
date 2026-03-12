# 文书工具独立入口设计

## 目标

为现有 6 种消费维权文书新增独立生成入口，用户无需走完整对话流程即可快速生成格式规范的 Word 文档。同时保留对话中触发文书生成的能力。

## 范围

- 文书类型不新增，保持现有 6 种：投诉书、举报信、协商函、民事起诉状、证据清单、索赔函
- 新增侧边栏快捷入口 + 混合表单页面
- 对话流程中的文书生成能力不变

## 架构

两个入口共享 `DocumentGenerator` 后端逻辑，不重复实现。

```
侧边栏文书按钮 ──→ 文书表单视图 ──→ POST /api/document/generate-direct ──→ DocumentGenerator
对话中触发     ──→ AgentService  ──→ POST /api/document/generate        ──→ DocumentGenerator
```

## 前端设计

### 侧边栏变化

现有侧边栏底部新增"文书工具"分区，包含 6 个文书类型按钮。点击后主区域从聊天视图切换为文书表单视图。

### 文书表单视图（混合模式）

- **顶部**：文书类型标题 + 一行说明文字
- **表单区**：核心字段用 input 填写（如姓名、电话、商家名称、金额、日期），非必填项标记"选填"
- **描述区**：一个大文本框"请描述您的情况"，用户自然语言输入事件经过
- **生成按钮**：调用 API，返回 .docx 下载链接
- 随时可点侧边栏"智能咨询"切回聊天

### 视图切换

主区域用 CSS `display: none/block` 切换聊天视图和文书表单视图，不销毁 DOM，聊天状态不丢失。

### 字段配置

各文书类型的表单字段复用 `DOC_REQUIRED_FIELDS` 定义，前端通过 `/api/document/types` 获取字段列表动态渲染表单。

## 后端设计

### 新增 API

```
POST /api/document/generate-direct
Content-Type: application/json

{
  "doc_type": "complaint_letter",
  "fields": {
    "complainant_name": "张三",
    "complainant_phone": "13800000000",
    "merchant_name": "某某商店",
    "purchase_date": "2026-01-15",
    "purchase_amount": "299元"
  },
  "description": "我在某某商店买了一台电饭煲，用了两天就坏了，商家拒绝退换..."
}

Response:
{
  "file_id": "abc123",
  "download_url": "/api/document/download/abc123",
  "doc_type": "complaint_letter",
  "doc_type_label": "投诉书"
}
```

### 实现逻辑

1. 将 `fields` 和 `description` 合并为 `case_info`（`description` 映射到 `problem_description` 字段）
2. 调用 `DocumentGenerator.generate(doc_type, case_info)` 复用现有生成逻辑
3. 返回下载链接

### 改动范围

| 文件 | 改动 |
|------|------|
| `app/routers/document.py` | 新增 `generate_direct` 路由 |
| `app/models/schemas.py` | 新增 `DirectGenerateRequest` 模型 |
| `app/routers/document.py` 的 `/types` | 增加返回 `required_fields` 和 `field_labels` |
| `templates/index.html` | 新增文书表单视图 HTML |
| `static/css/style.css` | 文书表单样式 |
| `static/js/chat.js` | 视图切换逻辑 + 表单提交逻辑 |
| **不改** | `DocumentGenerator`、`document_prompts.py`、`agent.py`、`knowledge.py` |

## 交互流程

1. 用户点击侧边栏"投诉书"
2. 主区域切换为投诉书表单（显示 7 个字段 + 描述框）
3. 用户填写表单字段 + 描述文字
4. 点击"生成文书"
5. 前端 POST `/api/document/generate-direct`
6. 后端合并数据 → LLM 生成内容段落 → python-docx 格式化 → 返回下载链接
7. 前端显示下载按钮，用户下载 .docx 文件
