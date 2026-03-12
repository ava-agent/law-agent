import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    StartSessionRequest,
    StartSessionResponse,
    ChatMessageRequest,
)
from app.dependencies import agent_service

router = APIRouter()


@router.post("/start", response_model=StartSessionResponse)
async def start_session(request: StartSessionRequest):
    session_id, welcome = agent_service.create_session(request.case_type)
    return StartSessionResponse(session_id=session_id, welcome_message=welcome)


@router.post("/message")
async def send_message(request: ChatMessageRequest):
    session = agent_service.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    def event_generator():
        for event in agent_service.process_message(request.session_id, request.message):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/history/{session_id}")
async def get_history(session_id: str):
    session = agent_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {
        "session_id": session_id,
        "phase": session.phase.value,
        "messages": session.messages,
        "case_info": session.case_info,
    }
