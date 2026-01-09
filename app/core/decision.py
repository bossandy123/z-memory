from typing import List, Dict, Any, Optional
from app.core.memory import Memory, UserMemory, AgentMemory
from sqlalchemy import select

class DecisionLayer:
    def __init__(self, user_memory: Optional[UserMemory] = None, 
                 agent_memory: Optional[AgentMemory] = None):
        self.user_memory = user_memory
        self.agent_memory = agent_memory

    async def query(self, query: str, user_id: Optional[str] = None, 
                   agent_id: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        results = {
            "user_memories": [],
            "agent_memories": [],
            "fused_context": None,
            "recommendations": []
        }

        # Query user memories if enabled and user_id provided
        if user_id and self.user_memory:
            results["user_memories"] = await self.user_memory.query(user_id, query, top_k)

        # Query agent memories if enabled and agent_id provided
        if agent_id and self.agent_memory:
            results["agent_memories"] = await self.agent_memory.query(agent_id, query, top_k)

        # Fuse and rank memories
        results["fused_context"] = await self._fuse_and_rank(query, results["user_memories"], 
                                                            results["agent_memories"])
        
        # Generate recommendations
        results["recommendations"] = await self._generate_recommendations(
            query, results["fused_context"]
        )
        
        return results

    async def _fuse_and_rank(self, query: str, user_memories: List[Memory], 
                            agent_memories: List[Memory]) -> List[Dict[str, Any]]:
        fused = []
        
        for mem in user_memories:
            fused.append({
                "id": mem.id,
                "content": mem.content,
                "type": "user",
                "metadata": mem.meta_info,
                "created_at": mem.created_at
            })
        
        for mem in agent_memories:
            fused.append({
                "id": mem.id,
                "content": mem.content,
                "type": "agent",
                "metadata": mem.meta_info,
                "created_at": mem.created_at
            })
        
        return sorted(fused, key=lambda x: x["created_at"], reverse=True)

    async def _generate_recommendations(self, query: str, 
                                       context: List[Dict[str, Any]]) -> List[str]:
        if not context:
            return ["No relevant memories found"]
        
        recommendations = []
        for item in context[:3]:
            recommendations.append(f"Related {item['type']} memory: {item['content'][:100]}...")
        
        return recommendations
