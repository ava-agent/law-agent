import json
from typing import Optional

from app.models.enums import ConversationPhase
from app.models.schemas import SessionState


class SessionStore:
    def __init__(self, supabase_client):
        self.client = supabase_client

    def save(self, session: SessionState):
        data = {
            "session_id": session.session_id,
            "phase": session.phase.value,
            "case_type": session.case_type,
            "case_info": session.case_info,
            "messages": session.messages,
            "collected_fields": list(session.collected_fields),
            "generated_documents": session.generated_documents,
        }
        self.client.table("sessions").upsert(data).execute()

    def load(self, session_id: str) -> Optional[SessionState]:
        result = (
            self.client.table("sessions")
            .select("*")
            .eq("session_id", session_id)
            .execute()
        )
        if not result.data:
            return None
        row = result.data[0]
        session = SessionState(row["session_id"])
        session.phase = ConversationPhase(row["phase"])
        session.case_type = row.get("case_type")
        session.case_info = row.get("case_info", {})
        session.messages = row.get("messages", [])
        session.collected_fields = set(row.get("collected_fields", []))
        session.generated_documents = row.get("generated_documents", [])
        return session

    def delete(self, session_id: str):
        self.client.table("sessions").delete().eq("session_id", session_id).execute()
