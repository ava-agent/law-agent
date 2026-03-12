DOCUMENT_SYSTEM_PROMPT = """你是一位专业的法律文书撰写助手。你需要根据提供的案件信息和法律依据，生成规范、专业的法律文书内容。

要求：
- 使用正式、规范的法律语言
- 引用具体的法律条文
- 事实陈述要客观、准确、条理清晰
- 诉求/请求要明确、合理、有法律依据
- 不要添加虚构的事实
"""

SECTION_PROMPTS = {
    "demands_section": """基于以下案件信息，生成正式的投诉请求部分。
要求：每条请求单独编号，明确具体，有法律依据。

案件信息：
{case_info}

相关法条：
{relevant_laws}

请生成投诉请求，格式如下：
一、...（具体请求内容及法律依据）
二、...
""",
    "facts_and_reasons": """基于以下案件信息，生成"事实与理由"部分。
要求：
1. 按时间顺序叙述事实
2. 引用具体法律条文作为依据
3. 语言规范、逻辑清晰
4. 将事实与法律依据紧密结合

案件信息：
{case_info}

相关法条：
{relevant_laws}
""",
    "evidence_analysis": """基于以下案件信息，生成证据清单。
为每项证据编号，说明证据名称、证据类型、证明目的。

案件信息：
{case_info}

请以表格形式输出：
序号 | 证据名称 | 证据类型 | 证明目的
""",
    "report_content": """基于以下案件信息，生成举报信正文内容。
要求：
1. 说明被举报人的违法行为
2. 引用违反的具体法律条文
3. 请求市场监管部门依法查处
4. 语言正式、客观

案件信息：
{case_info}

相关法条：
{relevant_laws}
""",
    "demand_content": """基于以下案件信息，生成协商函正文内容。
要求：
1. 阐述事实经过
2. 说明我方合法权益受损情况
3. 引用法律依据
4. 提出明确的协商要求和期限
5. 告知对方如不配合将采取的进一步措施

案件信息：
{case_info}

相关法条：
{relevant_laws}
""",
    "lawsuit_claims": """基于以下案件信息，生成民事起诉状的诉讼请求部分。
要求：每条请求编号，明确、具体、可执行。

案件信息：
{case_info}

相关法条：
{relevant_laws}

格式：
一、判令被告...
二、判令被告...
三、本案诉讼费用由被告承担。
""",
    "lawsuit_facts": """基于以下案件信息，生成民事起诉状的"事实与理由"部分。
要求：
1. 严格按时间顺序叙述
2. 引用具体法律条文
3. 论证充分、逻辑严密
4. 使用法律术语规范表述

案件信息：
{case_info}

相关法条：
{relevant_laws}
""",
    "claim_content": """基于以下案件信息，生成索赔函正文内容。
要求：
1. 阐述事实及损失情况
2. 明确索赔金额和计算依据（引用法条中的赔偿规则）
3. 设定合理回复期限
4. 告知逾期后果

案件信息：
{case_info}

相关法条：
{relevant_laws}
""",
}

DOC_REQUIRED_FIELDS = {
    "complaint_letter": [
        "complainant_name",
        "complainant_phone",
        "merchant_name",
        "purchase_date",
        "purchase_amount",
        "problem_description",
        "desired_outcome",
    ],
    "report_letter": [
        "complainant_name",
        "complainant_phone",
        "merchant_name",
        "problem_description",
    ],
    "demand_letter": [
        "complainant_name",
        "merchant_name",
        "purchase_date",
        "purchase_amount",
        "problem_description",
        "desired_outcome",
    ],
    "civil_lawsuit": [
        "complainant_name",
        "complainant_id_number",
        "complainant_phone",
        "complainant_address",
        "merchant_name",
        "merchant_address",
        "purchase_date",
        "purchase_amount",
        "problem_description",
        "desired_outcome",
    ],
    "evidence_checklist": [
        "evidence_available",
        "problem_description",
    ],
    "claim_letter": [
        "complainant_name",
        "merchant_name",
        "purchase_date",
        "purchase_amount",
        "problem_description",
        "desired_outcome",
    ],
}

DOC_FIELD_LABELS = {
    "complainant_name": "您的姓名",
    "complainant_phone": "您的联系电话",
    "complainant_id_number": "您的身份证号",
    "complainant_address": "您的地址",
    "merchant_name": "商家名称",
    "merchant_address": "商家地址",
    "purchase_date": "购买日期",
    "purchase_amount": "购买金额",
    "problem_description": "问题描述",
    "desired_outcome": "期望结果",
    "evidence_available": "现有证据",
}
