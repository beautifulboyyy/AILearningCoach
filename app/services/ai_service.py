from typing import AsyncGenerator, List
import json
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Milvus
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from app.core.config import settings

class AIService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            streaming=True,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.vector_store = Milvus(
            embedding_function=self.embeddings,
            connection_args={"host": settings.MILVUS_HOST, "port": settings.MILVUS_PORT},
            collection_name="CourseKnowledge"
        )

    async def get_chat_response(
        self, 
        query: str, 
        history: List[dict] = None,
        user_context: dict = None
    ) -> AsyncGenerator[str, None]:
        # 1. Retrieve relevant documents
        docs = self.vector_store.similarity_search(query, k=5)
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        # 2. Build references for citation
        references = [
            {"content": doc.page_content, "metadata": doc.metadata} 
            for doc in docs
        ]

        # 3. Prepare Prompt
        system_prompt = """你是一个专业的智能学习教练。
请根据提供的课程知识库内容回答学习者的问题。
如果知识库中没有相关信息，请明确告知，不要胡编乱造。
在回答时，请结合学习者的背景信息：{user_context}。
请在回答中引用来源，例如 [1], [2]。

课程知识库内容：
{context}
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{query}")
        ])

        # 4. Stream response
        chain = prompt | self.llm
        
        # We'll first yield the references as a special JSON chunk
        yield f"data: {json.dumps({'type': 'references', 'data': references})}\n\n"

        async for chunk in chain.astream({
            "context": context_text,
            "query": query,
            "user_context": json.dumps(user_context or {})
        }):
            if chunk.content:
                yield f"data: {json.dumps({'type': 'content', 'data': chunk.content})}\n\n"
        
        yield "data: [DONE]\n\n"

ai_service = AIService()
