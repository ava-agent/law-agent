from app.services.agent import AgentService
from app.services.knowledge import KnowledgeBase
from app.services.llm import LLMService
from config import settings

llm_service = LLMService(settings)
knowledge_base = KnowledgeBase()

# Initialize Supabase if configured
session_store = None
doc_storage = None

if settings.SUPABASE_URL and settings.SUPABASE_KEY:
    from supabase import create_client
    from app.services.session_store import SessionStore
    from app.services.doc_storage import DocStorage

    supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    session_store = SessionStore(supabase_client)
    doc_storage = DocStorage(supabase_client)

agent_service = AgentService(llm_service, knowledge_base, session_store)
