from typing import List
from abc import ABC, abstractmethod
from app.repositories.interfaces import IEmbeddingService
from openai import AsyncOpenAI
from app.config import settings
import dashscope
from dashscope import TextEmbedding

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


class EmbeddingService(IEmbeddingService):
    """向量嵌入服务：支持 OpenAI 和 DashScope"""

    async def generate(self, text: str) -> List[float]:
        if settings.EMBEDDING_PROVIDER == "dashscope":
            return await self._generate_dashscope(text)
        else:
            return await self._generate_openai(text)

    async def _generate_dashscope(self, text: str) -> List[float]:
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        response = TextEmbedding.call(
            model=settings.DASHSCOPE_EMBEDDING_MODEL,
            input=text
        )
        if response.status_code == 200:
            return response.output['embeddings'][0]['embedding']
        else:
            raise Exception(f"DashScope API error: {response.message}")

    async def _generate_openai(self, text: str) -> List[float]:
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
