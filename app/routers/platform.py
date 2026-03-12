from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    PlatformRecommendRequest,
    PlatformRecommendResponse,
    PlatformRecommendation,
)
from app.dependencies import agent_service, knowledge_base
from app.services.platform_recommender import PlatformRecommender

router = APIRouter()
platform_recommender = PlatformRecommender(knowledge_base)


@router.post("/recommend", response_model=PlatformRecommendResponse)
async def recommend_platforms(request: PlatformRecommendRequest):
    session = agent_service.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    results = platform_recommender.recommend(session.case_info)
    recommendations = [PlatformRecommendation(**r) for r in results]
    return PlatformRecommendResponse(recommendations=recommendations)
