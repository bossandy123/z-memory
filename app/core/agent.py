from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
import dashscope
from dashscope import Generation
import json
from app.config import settings

class MemoryExtractor:
    """记忆抽取器，使用 LLM 从对话中抽取重要信息"""
    
    def __init__(self):
        if settings.LLM_PROVIDER == "dashscope":
            dashscope.api_key = settings.DASHSCOPE_API_KEY
            self.model = settings.DASHSCOPE_LLM_MODEL
        else:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = settings.OPENAI_LLM_MODEL
    
    async def extract_memories(
        self, 
        content: str, 
        entity_id: str,
        existing_memories: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        从内容中抽取记忆
        
        Args:
            content: 输入内容（如对话记录）
            entity_id: 实体 ID（user_id 或 agent_id）
            existing_memories: 现有的记忆列表（用于去重和更新判断）
            
        Returns:
            抽取到的记忆列表，每个记忆包含操作类型（insert/update/ignore）
        """
        prompt = self._build_extraction_prompt(content, existing_memories)
        
        if settings.LLM_PROVIDER == "dashscope":
            memories = await self._extract_with_dashscope(prompt)
        else:
            memories = await self._extract_with_openai(prompt)
        
        # 为每个记忆添加 metadata
        for mem in memories:
            mem["metadata"] = mem.get("metadata", {})
            mem["metadata"]["source"] = "auto_extraction"
            mem["metadata"]["entity_id"] = entity_id
            
            # 如果是 update 操作，需要从现有记忆中找到对应的 memory_id
            if mem.get("action") == "update" and existing_memories:
                existing_content = mem.get("existing_content", "")
                for existing in existing_memories:
                    if existing.get("content") == existing_content:
                        mem["memory_id"] = existing.get("id")
                        break
        
        return memories
    
    def _build_extraction_prompt(self, content: str, existing_memories: List[Dict[str, Any]] = None) -> str:
        """构建记忆抽取的提示词"""
        prompt = f"""你是一个专业的记忆抽取助手。请从以下内容中抽取重要的、值得保存的记忆信息。

"""
        
        if existing_memories:
            prompt += f"""【现有记忆】（已存储的记忆，用于去重和更新判断）：
{self._format_existing_memories(existing_memories)}

"""
        
        prompt += f"""【输入内容】：
{content}

【抽取要求】：
1. 识别重要信息：用户偏好、重要事件、关键决策、重要关系等
2. 简洁描述：每条记忆用1-2句话清晰描述
3. 分类标记：为每条记忆添加类型（preference/decision/event/relationship/other）
4. 重要性评估：为每条记忆评分（1-5，5为最重要）
5. **智能去重和更新**：
   - 如果新抽取的记忆与现有记忆**完全相同**，标记 action 为 "ignore"
   - 如果新抽取的记忆是现有记忆的**更新/扩展**，标记 action 为 "update"，并在 existing_content 字段中记录对应的现有记忆内容
   - 如果新抽取的记忆是**全新的**，标记 action 为 "insert"
6. 只抽取有长期保存价值的信息，忽略闲聊和临时对话

【输出格式】（JSON数组）：
[
  {{
    "content": "记忆内容描述",
    "action": "insert|update|ignore",
    "existing_content": "要更新的现有记忆内容（仅 update 时需要）",
    "memory_type": "preference|decision|event|relationship|other",
    "importance": 1-5,
    "metadata": {{"additional_key": "value"}}
  }}
]

如果没有找到值得保存的记忆，返回空数组 []。"""
        
        return prompt
    
    def _format_existing_memories(self, memories: List[Dict[str, Any]]) -> str:
        """格式化现有记忆"""
        if not memories:
            return "（无现有记忆）"
        
        formatted = []
        for mem in memories:
            formatted.append(f"- {mem.get('content', '')} (ID: {mem.get('id', 'N/A')})")
        
        return "\n".join(formatted)
    
    async def _extract_with_dashscope(self, prompt: str) -> List[Dict[str, Any]]:
        """使用 DashScope 进行记忆抽取"""
        response = Generation.call(
            model=self.model,
            prompt=prompt,
            temperature=settings.LLM_TEMPERATURE,
            result_format='message'
        )
        
        if response.status_code == 200:
            content_text = response.output.choices[0].message.content
            return self._parse_memories(content_text)
        else:
            raise Exception(f"DashScope LLM error: {response.message}")
    
    async def _extract_with_openai(self, prompt: str) -> List[Dict[str, Any]]:
        """使用 OpenAI 进行记忆抽取"""
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=settings.LLM_TEMPERATURE
        )
        
        content_text = response.choices[0].message.content
        return self._parse_memories(content_text)
    
    def _parse_memories(self, content: str) -> List[Dict[str, Any]]:
        """解析 LLM 返回的记忆数据"""
        try:
            # 提取 JSON 部分
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                return []
            
            json_str = content[start_idx:end_idx]
            memories = json.loads(json_str)
            
            # 验证和标准化
            valid_memories = []
            for mem in memories:
                if isinstance(mem, dict) and "content" in mem:
                    valid_memories.append({
                        "content": mem["content"],
                        "action": mem.get("action", "insert"),
                        "existing_content": mem.get("existing_content", ""),
                        "metadata": {
                            "memory_type": mem.get("memory_type", "other"),
                            "importance": mem.get("importance", 3),
                            **mem.get("metadata", {})
                        }
                    })
            
            return valid_memories
        except json.JSONDecodeError:
            # 如果 JSON 解析失败，尝试简单的文本匹配
            return []
        except Exception as e:
            print(f"Error parsing memories: {e}")
            return []
