from fastapi import APIRouter, HTTPException, Depends
from app.api.dependencies import container
from app.api.schemas.query import QueryRequest, QueryResponse
from app.config import settings

router = APIRouter()


@router.post("/memory/query", response_model=QueryResponse)
async def query_memory(
    request: QueryRequest,
    query_service=Depends(lambda: container.query_service)
):
    """
    融合多源记忆查询

    - **query**: 查询文本
    - **user_id**: 用户 ID（可选）
    - **agent_id**: 代理 ID（可选）
    - **top_k**: 返回的最大结果数
    """
    if not query_service:
        raise HTTPException(status_code=503, detail="No memory modules enabled")

    if not request.user_id and not request.agent_id:
        raise HTTPException(status_code=400, detail="Either user_id or agent_id is required")

    if request.user_id and not settings.ENABLE_USER_MEMORY:
        raise HTTPException(status_code=400, detail="User memory is not enabled")

    if request.agent_id and not settings.ENABLE_AGENT_MEMORY:
        raise HTTPException(status_code=400, detail="Agent memory is not enabled")

    results = await query_service.query(
        request.query,
        request.user_id,
        request.agent_id,
        request.top_k
    )

    return QueryResponse(
        query=request.query,
        total_results=len(results.get("user_memories", [])) + len(results.get("agent_memories", [])),
        user_memories=[],
        agent_memories=[]
    )
