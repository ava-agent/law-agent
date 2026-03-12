QUICK_START_PROMPTS = {
    "product_quality": "我买的商品有质量问题",
    "false_advertising": "商家虚假宣传，实际商品与宣传不符",
    "refund_dispute": "商家拒绝退款",
    "food_safety": "买到了过期/变质的食品",
    "service_quality": "商家的服务质量很差",
}

CASE_TYPE_DETECTION_PROMPT = """根据用户的描述，判断这属于哪种消费纠纷类型：

用户描述：{user_message}

纠纷类型选项：
- product_quality: 商品质量问题（假货、损坏、与描述不符等）
- false_advertising: 虚假宣传（夸大宣传、虚假广告等）
- refund_dispute: 退款纠纷（拒绝退款、拖延退款等）
- food_safety: 食品安全（过期、变质、不卫生等）
- service_quality: 服务质量（服务态度差、服务缩水等）

请在回复最后用以下格式输出判断结果：
<!--EXTRACTED_JSON
{{"case_type": "类型值"}}
-->
"""

ALL_REQUIRED_FIELDS = [
    "problem_description",
    "case_type",
    "merchant_name",
    "purchase_date",
    "purchase_amount",
    "purchase_channel",
    "problem_date",
    "evidence_available",
    "desired_outcome",
    "previous_communication",
]

FIELD_LABELS = {
    "problem_description": "问题概述",
    "case_type": "纠纷类型",
    "merchant_name": "商家名称",
    "purchase_date": "购买日期",
    "purchase_amount": "购买金额",
    "purchase_channel": "购买渠道",
    "problem_date": "发现问题日期",
    "evidence_available": "现有证据",
    "desired_outcome": "期望结果",
    "previous_communication": "与商家沟通情况",
}

MIN_FIELDS_FOR_SUMMARY = {"problem_description", "case_type", "merchant_name", "purchase_amount"}
