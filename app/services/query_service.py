from typing import List, Dict, Any, Optional
from app.services.memory_service import MemoryService
from app.domain.enums import MemoryType, MemoryLayer


class QueryService:
    """查询服务：融合多源记忆的查询"""

    def __init__(
        self,
        user_memory_service: Optional[MemoryService] = None,
        agent_memory_service: Optional[MemoryService] = None
    ):
        self.user_memory_service = user_memory_service
        self.agent_memory_service = agent_memory_service

    async def query(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """融合查询用户和 Agent 记忆"""
        user_memories = []
        agent_memories = []

        if user_id and self.user_memory_service:
            user_memories = await self.user_memory_service.query(
                MemoryType.USER, user_id, query_text, top_k
            )

        if agent_id and self.agent_memory_service:
            agent_memories = await self.agent_memory_service.query(
                MemoryType.AGENT, agent_id, query_text, top_k
            )

        fused = self._fuse_and_rank(user_memories, agent_memories)
        recommendations = self._generate_recommendations(query_text, fused)

        return {
            "query": query_text,
            "user_memories": user_memories,
            "agent_memories": agent_memories,
            "fused_context": fused,
            "recommendations": recommendations
        }

    def _fuse_and_rank(
        self,
        user_memories: List[Dict[str, Any]],
        agent_memories: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """融合和排序记忆"""
        fused = []

        for mem in user_memories:
            fused.append({
                "id": mem.get("id"),
                "content": mem.get("content"),
                "type": "user",
                "created_at": mem.get("created_at")
            })

        for mem in agent_memories:
            fused.append({
                "id": mem.get("id"),
                "content": mem.get("content"),
                "type": "agent",
                "created_at": mem.get("created_at")
            })

        return sorted(fused, key=lambda x: x.get("created_at", ""), reverse=True)

    def _generate_recommendations(
        self,
        query: str,
        context: List[Dict[str, Any]]
    ) -> List[str]:
        """生成推荐"""
        if not context:
            return ["No relevant memories found"]

        recommendations = []
        for item in context[:3]:
            content = item.get("content", "")[:100]
            recommendations.append(
                f"Related {item['type']} memory: {content}..."
            )

        return recommendations
