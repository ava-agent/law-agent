from enum import Enum


class CaseType(str, Enum):
    PRODUCT_QUALITY = "product_quality"
    FALSE_ADVERTISING = "false_advertising"
    REFUND_DISPUTE = "refund_dispute"
    FOOD_SAFETY = "food_safety"
    SERVICE_QUALITY = "service_quality"


CASE_TYPE_LABELS = {
    CaseType.PRODUCT_QUALITY: "商品质量问题",
    CaseType.FALSE_ADVERTISING: "虚假宣传",
    CaseType.REFUND_DISPUTE: "退款纠纷",
    CaseType.FOOD_SAFETY: "食品安全",
    CaseType.SERVICE_QUALITY: "服务质量问题",
}


class DocumentType(str, Enum):
    COMPLAINT_LETTER = "complaint_letter"
    REPORT_LETTER = "report_letter"
    DEMAND_LETTER = "demand_letter"
    CIVIL_LAWSUIT = "civil_lawsuit"
    EVIDENCE_CHECKLIST = "evidence_checklist"
    CLAIM_LETTER = "claim_letter"


DOCUMENT_TYPE_LABELS = {
    DocumentType.COMPLAINT_LETTER: "投诉书",
    DocumentType.REPORT_LETTER: "举报信",
    DocumentType.DEMAND_LETTER: "协商函",
    DocumentType.CIVIL_LAWSUIT: "民事起诉状",
    DocumentType.EVIDENCE_CHECKLIST: "证据清单",
    DocumentType.CLAIM_LETTER: "索赔函",
}


class ConversationPhase(str, Enum):
    GREETING = "greeting"
    SITUATION_ANALYSIS = "situation_analysis"
    CASE_SUMMARY = "case_summary"
    GUIDANCE = "guidance"
    DOCUMENT_PREPARATION = "document_preparation"
    FOLLOW_UP = "follow_up"


class PlatformType(str, Enum):
    GOVERNMENT = "government"
    MEDIA = "media"
    JUDICIAL = "judicial"
    ORGANIZATION = "organization"
