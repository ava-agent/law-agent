from typing import Optional, List, Dict, Set

from pydantic import BaseModel

from app.models.enums import DocumentType, ConversationPhase


class StartSessionRequest(BaseModel):
    case_type: Optional[str] = None


class StartSessionResponse(BaseModel):
    session_id: str
    welcome_message: str


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str


class ChatEvent(BaseModel):
    type: str  # "text", "action", "case_info", "done"
    content: str = ""
    metadata: Optional[Dict] = None


class GenerateDocumentRequest(BaseModel):
    session_id: str
    doc_type: DocumentType
    overrides: Optional[Dict] = None


class GenerateDocumentResponse(BaseModel):
    file_id: str
    download_url: str
    doc_type: str
    doc_type_label: str


class DocumentTypeInfo(BaseModel):
    type: str
    label: str
    description: str


class PlatformRecommendRequest(BaseModel):
    session_id: str


class PlatformRecommendation(BaseModel):
    name: str
    full_name: str
    url: str
    reason: str
    suitability: str
    steps_summary: str


class PlatformRecommendResponse(BaseModel):
    recommendations: List[PlatformRecommendation]


class SessionState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.phase = ConversationPhase.GREETING
        self.case_type: Optional[str] = None
        self.case_info: Dict = {}
        self.messages: List[Dict] = []
        self.collected_fields: Set[str] = set()
        self.generated_documents: List[str] = []
