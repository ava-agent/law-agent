from app.services.agent import AgentService
from app.services.knowledge import KnowledgeBase
from app.services.llm import LLMService
from config import settings

llm_service = LLMService(settings)
knowledge_base = KnowledgeBase()
agent_service = AgentService(llm_service, knowledge_base)
