import os
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.enums import DOCUMENT_TYPE_LABELS, DocumentType
from app.models.schemas import (
    GenerateDocumentRequest,
    GenerateDocumentResponse,
    DocumentTypeInfo,
    DirectGenerateRequest,
)
from app.prompts.document_prompts import DOC_REQUIRED_FIELDS, DOC_FIELD_LABELS
from app.dependencies import agent_service, llm_service, knowledge_base, doc_storage
from app.services.document_generator import DocumentGenerator
from config import settings

router = APIRouter()
doc_generator = DocumentGenerator(llm_service, knowledge_base, doc_storage)


@router.post("/generate", response_model=GenerateDocumentResponse)
async def generate_document(request: GenerateDocumentRequest):
    session = agent_service.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    case_info = dict(session.case_info)
    if request.overrides:
        case_info.update(request.overrides)

    file_id, result = doc_generator.generate(request.doc_type.value, case_info)

    doc_label = DOCUMENT_TYPE_LABELS.get(request.doc_type, request.doc_type.value)
    session.generated_documents.append(doc_label)

    # Save session after modification (for Supabase persistence)
    if hasattr(agent_service, '_save_session'):
        agent_service._save_session(session)

    # If result is a URL (Supabase Storage), use it directly; otherwise local path
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


@router.get("/download/{file_id}")
async def download_document(file_id: str):
    filepath = os.path.join(settings.GENERATED_DOCS_DIR, f"{file_id}.docx")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=f"法律文书_{file_id}.docx",
    )


DOC_DESCRIPTIONS = {
    DocumentType.COMPLAINT_LETTER: "向市场监督管理局提交的消费者投诉书",
    DocumentType.REPORT_LETTER: "举报商家违法经营行为的举报信",
    DocumentType.DEMAND_LETTER: "向商家发送的正式协商/要求函",
    DocumentType.CIVIL_LAWSUIT: "向人民法院提起诉讼的民事起诉状",
    DocumentType.EVIDENCE_CHECKLIST: "整理维权证据的清单",
    DocumentType.CLAIM_LETTER: "向商家发送的正式索赔函",
}


@router.get("/types", response_model=List[DocumentTypeInfo])
async def list_document_types():
    return [
        DocumentTypeInfo(
            type=dt.value,
            label=DOCUMENT_TYPE_LABELS[dt],
            description=DOC_DESCRIPTIONS.get(dt, ""),
        )
        for dt in DocumentType
    ]


@router.get("/types-ext")
async def list_document_types_extended():
    result = []
    for dt in DocumentType:
        fields = DOC_REQUIRED_FIELDS.get(dt.value, [])
        labels = {f: DOC_FIELD_LABELS.get(f, f) for f in fields}
        result.append({
            "type": dt.value,
            "label": DOCUMENT_TYPE_LABELS[dt],
            "description": DOC_DESCRIPTIONS.get(dt, ""),
            "required_fields": fields,
            "field_labels": labels,
        })
    return result
