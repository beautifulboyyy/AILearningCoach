#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
讲17 | 高级检索策略 - 实践练习
实现RAG系统中的所有高级检索技术

依赖安装：
pip install pymilvus dashscope python-dotenv openai numpy

环境变量配置（.env文件）：
DASHSCOPE_API_KEY=your_dashscope_api_key
OPENAI_API_KEY=your_openai_api_key

Milvus要求：
需要启动Milvus服务（默认 http://127.0.0.1:19530）
Docker启动命令：
docker run -d --name milvus -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest
"""

import asyncio
import os
from http import HTTPStatus
from typing import List, Dict, Tuple

import dashscope
from dotenv import load_dotenv
from openai import OpenAI
from pymilvus import AsyncMilvusClient, DataType, RRFRanker, AnnSearchRequest

_ = load_dotenv()


# ============================================================================
# 辅助函数
# ============================================================================

def get_text_embedding(text: str, dimension: int = 1024):
    """使用DashScope获取文本向量（密集向量+BM25稀疏向量）"""
    resp = dashscope.TextEmbedding.call(
        model=dashscope.TextEmbedding.Models.text_embedding_v3,
        input=text,
        dimension=dimension,
        output_type="dense&sparse",  # 同时返回密集向量和BM25稀疏向量
        api_key=os.getenv("DASHSCOPE_API_KEY")
    )

    if resp.status_code == HTTPStatus.OK:
        return resp.output['embeddings'][0]
    else:
        raise Exception(f"Error getting embedding: {resp}")


def call_llm(prompt: str, model: str = "deepseek-chat", temperature: float = 0.3) -> str:
    """调用LLM生成文本"""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature
    )

    return response.choices[0].message.content.strip()


class AsyncMilvusOperator:

    def __init__(self):
        self.async_milvus_client = AsyncMilvusClient(uri="http://127.0.0.1:19530")

    async def create_schema(self):
        schema = self.async_milvus_client.create_schema(auto_id=True, description="这是测试参数模型")
        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, description="这是主键")
        schema.add_field("dense_vector", DataType.FLOAT_VECTOR, dim=1024, description="这是密集向量")
        schema.add_field("sparse_vector", DataType.SPARSE_FLOAT_VECTOR, description="这是稀疏向量")
        schema.add_field("text", DataType.VARCHAR, max_length=4096, description="这是文本内容")
        return schema

    async def create_collection(self):
        collection = await self.async_milvus_client.create_collection(collection_name="mix_search_demo",
                                                                      schema=await self.create_schema(),
                                                                      description="这是混合检索的demo")
        index_params = self.async_milvus_client.prepare_index_params()
        index_params.add_index(field_name="dense_vector", metric_type="COSINE", index_type="IVF_FLAT")
        index_params.add_index(field_name="sparse_vector", metric_type="IP", index_type="SPARSE_INVERTED_INDEX")
        await self.async_milvus_client.create_index(collection_name="mix_search_demo", index_params=index_params)

    async def vector_insert(self, data):
        res = await self.async_milvus_client.insert(collection_name="mix_search_demo", data=data)
        return res

    async def vector_search(self, dense_vector: list, sparse_vector: list):
        await self.async_milvus_client.load_collection(collection_name="mix_search_demo")
        dense_vector_result = await self.async_milvus_client.search(collection_name="mix_search_demo",
                                                                    anns_field="dense_vector",
                                                                    search_params={"metric_type": "COSINE"}, limit=10,
                                                                    output_fields=["text"], data=dense_vector)
        sparse_vector_result = await self.async_milvus_client.search(collection_name="mix_search_demo",
                                                                     anns_field="sparse_vector",
                                                                     search_params={"metric_type": "IP"}, limit=10,
                                                                     output_fields=["text"], data=sparse_vector)

        return dense_vector_result, sparse_vector_result

    async def conduct_hybrid_search(self, collection_name, dense_vector: list, sparse_vector: list):
        await self.async_milvus_client.load_collection(collection_name="mix_search_demo")
        req_dense = AnnSearchRequest(
            data=dense_vector,
            anns_field="dense_vector",
            param={"metric_type": "COSINE"},
            limit=10
        )

        req_sparse = AnnSearchRequest(
            data=sparse_vector,
            anns_field="sparse_vector",
            param={"metric_type": "IP"},
            limit=10
        )
        reqs = [req_dense, req_sparse]
        ranker = RRFRanker(k=10)
        res = await self.async_milvus_client.hybrid_search(collection_name=collection_name, reqs=reqs, ranker=ranker,
                                                           output_fields=["text"])
        return res


def create_sample_documents() -> List[Dict]:
    """创建示例文档"""
    documents = [
        {
            "doc_id": "doc_001",
            "text": "人工智能（Artificial Intelligence, AI）是计算机科学的一个分支，致力于创建能够模拟人类智能行为的系统。AI包括机器学习、深度学习、自然语言处理等多个子领域。",
            "category": "AI基础"
        },
        {
            "doc_id": "doc_002",
            "text": "机器学习是人工智能的核心技术之一。它使计算机能够从数据中学习模式，而无需明确编程。主要的机器学习方法包括监督学习、无监督学习和强化学习。",
            "category": "机器学习"
        },
        {
            "doc_id": "doc_003",
            "text": "深度学习是机器学习的一个子集，使用多层神经网络来学习数据的表示。深度学习在图像识别、语音识别和自然语言处理等领域取得了突破性进展。",
            "category": "深度学习"
        },
        {
            "doc_id": "doc_004",
            "text": "自然语言处理（NLP）是AI的一个重要分支，专注于让计算机理解、解释和生成人类语言。NLP的应用包括机器翻译、情感分析、文本摘要和问答系统。",
            "category": "NLP"
        },
        {
            "doc_id": "doc_005",
            "text": "大语言模型（Large Language Model, LLM）如GPT-4、Claude等，是基于Transformer架构的深度学习模型。它们在海量文本数据上训练，能够理解和生成自然语言。",
            "category": "LLM"
        },
        {
            "doc_id": "doc_006",
            "text": "RAG（Retrieval-Augmented Generation）是一种结合检索和生成的技术。它先从知识库中检索相关信息，然后将检索结果作为上下文输入给LLM生成答案。",
            "category": "RAG"
        },
        {
            "doc_id": "doc_007",
            "text": "向量数据库如Milvus、Pinecone、Weaviate等，专门用于存储和检索高维向量数据。它们在RAG系统中扮演关键角色，支持高效的语义搜索。",
            "category": "向量数据库"
        },
        {
            "doc_id": "doc_008",
            "text": "Embedding是将文本、图像等数据转换为向量表示的过程。常用的文本Embedding模型包括OpenAI的text-embedding-3、sentence-transformers等。",
            "category": "Embedding"
        },
        {
            "doc_id": "doc_009",
            "text": "混合检索结合了向量检索的语义理解能力和关键词检索的精确匹配能力。通过RRF等融合算法，可以显著提升检索准确率。",
            "category": "混合检索"
        },
        {
            "doc_id": "doc_010",
            "text": "Reranking是一种二阶段检索策略。先用快速的检索方法获取候选集，再用精确但较慢的Cross-Encoder模型重新排序，提升最终结果的相关性。",
            "category": "重排序"
        },
        {
            "doc_id": "doc_011",
            "text": "HyDE（Hypothetical Document Embeddings）是一种查询改写技术。它先生成假设的答案文档，再用假设答案的向量进行检索，能显著提升检索准确率。",
            "category": "查询改写"
        },
        {
            "doc_id": "doc_012",
            "text": "多查询检索通过生成多个查询变体来提高召回率。每个变体独立检索后，使用RRF等算法聚合结果，覆盖更多相关文档。",
            "category": "多查询"
        },
        {
            "doc_id": "doc_013",
            "text": "BM25是一种经典的关键词检索算法，基于TF-IDF改进。它考虑词频、逆文档频率和文档长度归一化，在精确匹配场景下效果出色。",
            "category": "BM25"
        },
        {
            "doc_id": "doc_014",
            "text": "Cross-Encoder是Reranker的核心模型架构。不同于Bi-Encoder独立编码查询和文档，Cross-Encoder联合编码，能捕捉更细粒度的语义关系。",
            "category": "重排序"
        },
        {
            "doc_id": "doc_015",
            "text": "查询扩展通过添加同义词和相关术语来丰富查询。查询简化则提取核心关键词。两种策略分别适用于简短查询和冗长查询。",
            "category": "查询改写"
        }
    ]
    return documents


# ============================================================================
# 练习1：混合检索实现（密集向量 + BM25稀疏向量 + RRF融合）
# ============================================================================

async def exercise_1_hybrid_retrieval():
    """
    练习1：混合检索实现

    学习目标：
    1. 理解DashScope的text_embedding_v3模型同时返回密集向量和BM25稀疏向量
    2. 掌握密集向量检索（语义理解）和稀疏向量检索（关键词匹配）的区别
    3. 学习使用Milvus的混合检索功能（内置RRF融合）
    """
    print("\n" + "=" * 80)
    print("练习1：混合检索实现（密集向量 + BM25稀疏向量 + RRF融合）")
    print("=" * 80 + "\n")

    # 1. 准备示例文档
    documents = create_sample_documents()
    print(f"准备了 {len(documents)} 个示例文档")

    # 2. 初始化Milvus并创建集合
    milvus = AsyncMilvusOperator()

    try:
        await milvus.async_milvus_client.drop_collection("mix_search_demo")
    except:
        pass

    await milvus.create_collection()
    print("创建Milvus集合完成")

    # 3. 向量化文档并插入Milvus
    insert_datas = []

    for doc in documents:
        insert_data = {}
        embedding = get_text_embedding(doc['text'])
        insert_data["dense_vector"] = embedding['embedding']
        insert_data["sparse_vector"] = {i["index"]: i["value"] for i in embedding["sparse_embedding"]}
        insert_data["text"] = doc['text']
        insert_datas.append(insert_data)

    await milvus.vector_insert(insert_datas)
    print(f"向量化并插入 {len(documents)} 个文档完成\n")

    # 4. 执行三种检索策略对比
    query = "什么是RAG技术？它如何结合检索和生成？"
    print(f"查询：{query}\n")

    query_embedding = get_text_embedding(query)

    # 策略1：密集向量检索（语义理解）
    print("【策略1】密集向量检索")
    dense_results, _ = await milvus.vector_search(
        [query_embedding['embedding']],
        [{i["index"]: i["value"] for i in query_embedding["sparse_embedding"]}]
    )

    for i, hit in enumerate(dense_results[0][:5], 1):
        doc_text = hit['entity']['text']
        score = hit['distance']
        print(f"{i}. [{score:.4f}] {doc_text[:60]}...")

    # 策略2：BM25稀疏向量检索（关键词匹配）
    print("\n【策略2】BM25稀疏向量检索")
    _, sparse_results = await milvus.vector_search(
        [query_embedding['embedding']],
        [{i["index"]: i["value"] for i in query_embedding["sparse_embedding"]}]
    )

    for i, hit in enumerate(sparse_results[0][:5], 1):
        doc_text = hit['entity']['text']
        score = hit['distance']
        print(f"{i}. [{score:.4f}] {doc_text[:60]}...")

    # 策略3：混合检索（Milvus内置RRF融合）
    print("\n【策略3】混合检索（RRF融合）")
    hybrid_results = await milvus.conduct_hybrid_search(
        "mix_search_demo",
        [query_embedding['embedding']],
        [{i["index"]: i["value"] for i in query_embedding["sparse_embedding"]}]
    )

    for i, hits in enumerate(hybrid_results):
        for j, hit in enumerate(hits[:5], 1):
            doc_text = hit['entity']['text']
            score = hit['distance']
            print(f"{j}. [{score:.4f}] {doc_text[:60]}...")

    # 5. 对比分析
    print("\n" + "=" * 80)
    print("对比分析：")
    print("  策略1（密集向量）：语义理解，找概念相关文档")
    print("  策略2（BM25稀疏）：关键词匹配，精确匹配术语")
    print("  策略3（混合检索）：结合两者优势，准确率更高（推荐）")
    print("\n练习1完成！\n")


# ============================================================================
# 练习2：Reranker模型集成
# ============================================================================

class QwenReranker:
    """阿里云Qwen3 Reranker"""

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        print("初始化Qwen3 Reranker...")

    def rerank(self, query: str, documents: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        使用Qwen3 Reranker对文档进行重排序

        Args:
            query: 查询文本
            documents: 候选文档列表
            top_k: 返回前k个结果

        Returns:
            重排序后的文档列表 [(doc, score), ...]
        """
        try:
            # 调用阿里云TextReRank API
            resp = dashscope.TextReRank.call(
                model="qwen3-rerank",
                query=query,
                documents=documents,
                top_n=top_k,
                return_documents=False,  # 不需要返回文档，我们用index获取
                api_key=self.api_key
            )

            if resp.status_code == HTTPStatus.OK:
                # 解析返回结果
                results = []
                for item in resp.output.results:
                    # 使用index从原始文档列表获取文档内容
                    doc_index = item.index
                    doc_text = documents[doc_index]
                    score = item.relevance_score
                    results.append((doc_text, score))
                return results
            else:
                print(f"❌ Reranking失败: {resp.message}")
                return [(doc, 0.0) for doc in documents[:top_k]]

        except Exception as e:
            print(f"❌ Reranking错误: {e}")
            import traceback
            traceback.print_exc()
            return [(doc, 0.0) for doc in documents[:top_k]]


async def exercise_2_reranker_integration():
    """练习2：Reranker模型集成（使用Qwen3 Reranker）"""
    print("\n" + "=" * 80)
    print("练习2：Reranker模型集成（Qwen3 Reranker）")
    print("=" * 80 + "\n")

    # 1. 准备文档和查询
    documents = create_sample_documents()
    query = "RAG技术如何工作？"
    print(f"查询：{query}\n")

    # 2. 初步检索（使用向量检索获取候选文档）
    milvus = AsyncMilvusOperator()
    await milvus.async_milvus_client.load_collection("mix_search_demo")

    print("执行初步向量检索...")
    query_embedding = get_text_embedding(query)
    dense_results, _ = await milvus.vector_search(
        [query_embedding['embedding']],
        [{i["index"]: i["value"] for i in query_embedding["sparse_embedding"]}]
    )

    # 获取候选文档
    candidate_docs = []
    for hit in dense_results[0]:
        candidate_docs.append(hit['entity']['text'])

    print(f"获取了 {len(candidate_docs)} 个候选文档\n")

    # 显示初步检索结果
    print("【初步检索结果】")
    for i, doc in enumerate(candidate_docs[:5], 1):
        print(f"{i}. {doc[:70]}...")

    # 3. 使用Qwen3 Reranker重排序
    print("\n使用Qwen3 Reranker重排序...")
    reranker = QwenReranker()
    reranked_results = reranker.rerank(query, candidate_docs, top_k=10)

    print("\n【Reranking后的结果】")
    for i, (doc, score) in enumerate(reranked_results[:5], 1):
        print(f"{i}. [分数: {score:.4f}] {doc[:70]}...")

    print("\n练习2完成！\n")


# ============================================================================
# 练习3：查询改写与HyDE
# ============================================================================

class QueryRewriter:
    """查询改写器"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def expand_query(self, query: str) -> str:
        """查询扩展：添加同义词和相关术语"""
        prompt = f"""请对以下查询进行扩展，添加同义词、相关术语和背景信息，使查询更丰富。
保持查询的核心意图不变，只需要返回扩展后的查询文本。

原始查询：{query}

扩展后的查询："""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        return response.choices[0].message.content.strip()

    def simplify_query(self, query: str) -> str:
        """查询简化：提取核心关键词"""
        prompt = f"""请从以下查询中提取最核心的关键词，去除冗余信息。
只需要返回简化后的关键词或短语，用空格分隔。

原始查询：{query}

核心关键词："""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    def hyde_generate(self, query: str) -> str:
        """HyDE：生成假设的答案文档"""
        prompt = f"""假设你需要回答以下问题，请生成一个详细、准确的假设答案。
这个答案将用于文档检索，所以要包含相关的术语和概念。

问题：{query}

假设答案："""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()


async def exercise_3_query_rewriting():
    """练习3：查询改写与HyDE"""
    print("\n" + "=" * 80)
    print("练习3：查询改写与HyDE")
    print("=" * 80 + "\n")

    # 1. 准备查询
    original_query = "RAG是什么"
    print(f"📝 原始查询：{original_query}\n")

    # 2. 初始化查询改写器
    rewriter = QueryRewriter()

    # 3. 查询扩展
    print("--- 策略1：查询扩展 ---")
    expanded_query = rewriter.expand_query(original_query)
    print(f"扩展后：{expanded_query}\n")

    # 4. 查询简化
    long_query = "我想知道RAG这个技术到底是什么东西，它是如何工作的，有什么应用场景"
    print(f"📝 冗长查询：{long_query}")
    print("--- 策略2：查询简化 ---")
    simplified_query = rewriter.simplify_query(long_query)
    print(f"简化后：{simplified_query}\n")

    # 5. HyDE生成假设文档
    print("--- 策略3：HyDE（假设文档嵌入）---")
    hyde_doc = rewriter.hyde_generate(original_query)
    print(f"假设答案：\n{hyde_doc}\n")

    # 6. 使用不同策略进行检索并对比
    milvus = AsyncMilvusOperator()
    await milvus.async_milvus_client.load_collection("mix_search_demo")

    queries_to_test = {
        "原始查询": original_query,
        "扩展查询": expanded_query,
        "简化查询": simplified_query,
        "HyDE查询": hyde_doc
    }

    print("=" * 80)
    print("检索效果对比")
    print("=" * 80 + "\n")

    for strategy, query_text in queries_to_test.items():
        print(f"--- {strategy} ---")
        print(f"查询文本：{query_text[:100]}...")

        # 执行检索
        query_embedding = get_text_embedding(query_text)
        dense_results, _ = await milvus.vector_search(
            [query_embedding['embedding']],
            [{i["index"]: i["value"] for i in query_embedding["sparse_embedding"]}]
        )

        # 显示Top-3结果
        print("检索结果（Top-3）：")
        for i, hit in enumerate(dense_results[0][:3], 1):
            doc_text = hit['entity']['text']
            score = hit['distance']
            print(f"  {i}. [分数: {score:.4f}] {doc_text[:60]}...")
        print()

    print("✅ 练习3完成！不同的查询改写策略适用于不同场景：")
    print("  - 查询扩展：适用于简短查询，增加召回率")
    print("  - 查询简化：适用于冗长查询，提高精确度")
    print("  - HyDE：生成假设答案，提升语义匹配准确率\n")


# ============================================================================
# 练习4：多查询检索与结果聚合
# ============================================================================

class MultiQueryGenerator:
    """多查询生成器"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_variants(self, query: str, num_variants: int = 3) -> List[str]:
        """生成查询变体"""
        prompt = f"""请为以下查询生成{num_variants}个不同的变体。
每个变体应该：
1. 保持原始查询的核心意图
2. 使用不同的表达方式或角度
3. 可以包含同义词、相关概念或更具体的描述

原始查询：{query}

请用JSON格式返回，例如：
{{"variants": ["变体1", "变体2", "变体3"]}}
"""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        result_text = response.choices[0].message.content.strip()

        # 解析JSON
        import json
        import re

        # 提取JSON部分
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return result.get("variants", [query])
            except:
                pass

        # 如果解析失败，返回原查询
        return [query]


async def multi_query_retrieval(milvus: AsyncMilvusOperator, queries: List[str],
                                top_k: int = 10) -> List[Tuple[str, float]]:
    """
    多查询检索并聚合结果（使用Milvus内置RRF）
    
    Args:
        milvus: Milvus操作器
        queries: 查询列表
        top_k: 每个查询返回的结果数
    
    Returns:
        聚合后的结果列表
    """
    # 收集所有查询结果（使用混合检索+RRF）
    all_docs = {}  # {doc_text: total_score}

    for query in queries:
        query_embedding = get_text_embedding(query)
        hybrid_results = await milvus.conduct_hybrid_search(
            "mix_search_demo",
            [query_embedding['embedding']],
            [{i["index"]: i["value"] for i in query_embedding["sparse_embedding"]}]
        )

        # 聚合分数
        for hits in hybrid_results:
            for hit in hits:
                doc_text = hit['entity']['text']
                score = hit['distance']
                if doc_text in all_docs:
                    all_docs[doc_text] += score
                else:
                    all_docs[doc_text] = score

    # 按分数排序
    sorted_results = sorted(all_docs.items(), key=lambda x: x[1], reverse=True)
    return sorted_results[:top_k]


def calculate_recall(retrieved_docs: List[str], relevant_docs: List[str]) -> float:
    """计算召回率"""
    if not relevant_docs:
        return 0.0

    retrieved_relevant = sum(1 for doc in retrieved_docs if any(rel in doc for rel in relevant_docs))
    return retrieved_relevant / len(relevant_docs)


async def exercise_4_multi_query_retrieval():
    """练习4：多查询检索与结果聚合"""
    print("\n" + "=" * 80)
    print("练习4：多查询检索与结果聚合")
    print("=" * 80 + "\n")

    # 1. 准备查询
    original_query = "向量数据库在AI系统中有什么作用？"
    print(f"📝 原始查询：{original_query}\n")

    # 2. 生成查询变体
    print("🔄 生成查询变体...")
    generator = MultiQueryGenerator()
    query_variants = generator.generate_variants(original_query, num_variants=4)

    print(f"✅ 生成了 {len(query_variants)} 个查询变体：")
    for i, variant in enumerate(query_variants, 1):
        print(f"  {i}. {variant}")
    print()

    # 3. 单查询检索（基准）
    print("--- 基准：单查询检索 ---")
    milvus = AsyncMilvusOperator()
    await milvus.async_milvus_client.load_collection("mix_search_demo")

    import time
    start_time = time.time()

    query_embedding = get_text_embedding(original_query)
    hybrid_results = await milvus.conduct_hybrid_search(
        "mix_search_demo",
        [query_embedding['embedding']],
        [{i["index"]: i["value"] for i in query_embedding["sparse_embedding"]}]
    )

    single_time = time.time() - start_time

    single_query_docs = []
    for hits in hybrid_results:
        for i, hit in enumerate(hits[:5], 1):
            doc_text = hit['entity']['text']
            score = hit['distance']
            single_query_docs.append(doc_text)
            print(f"{i}. [分数: {score:.4f}] {doc_text[:60]}...")

    print(f"⏱️  耗时: {single_time:.3f}秒")

    # 4. 多查询检索
    print("\n--- 多查询检索（聚合多个查询结果）---")
    start_time = time.time()

    multi_results = await multi_query_retrieval(
        milvus,
        [original_query] + query_variants,
        top_k=10
    )

    multi_time = time.time() - start_time

    multi_docs = []
    for i, (doc_text, agg_score) in enumerate(multi_results[:5], 1):
        multi_docs.append(doc_text)
        print(f"{i}. [聚合分数: {agg_score:.4f}] {doc_text[:60]}...")

    print(f"⏱️  耗时: {multi_time:.3f}秒")

    # 5. 评估召回率
    relevant_keywords = ["向量", "数据库", "Milvus", "检索", "AI"]

    print("\n📊 召回率对比：")
    single_recall = calculate_recall(single_query_docs, relevant_keywords)
    multi_recall = calculate_recall(multi_docs, relevant_keywords)

    print(f"  单查询召回率: {single_recall:.3f}")
    print(f"  多查询召回率: {multi_recall:.3f}")
    print(f"  召回率提升: {(multi_recall - single_recall):.3f}")

    # 6. 分析文档覆盖度
    single_set = set(single_query_docs)
    multi_set = set(multi_docs)

    new_docs = multi_set - single_set
    print(f"\n📈 文档覆盖度分析：")
    print(f"  单查询文档数: {len(single_set)}")
    print(f"  多查询文档数: {len(multi_set)}")
    print(f"  新增文档数: {len(new_docs)}")

    if new_docs:
        print(f"\n  新增的文档：")
        for doc in list(new_docs)[:3]:
            print(f"    - {doc[:60]}...")

    print("\n✅ 练习4完成！")
    print("💡 优化亮点：")
    print("  ✨ 使用Milvus内置RRF融合，无需自己实现")
    print("  ✨ 多查询检索提高召回率和覆盖度")
    print("  ✨ 适合需要高质量结果的场景\n")


# ============================================================================
# 练习5：高级检索策略综合评估
# ============================================================================

class RetrievalPipeline:
    """完整的检索Pipeline"""

    def __init__(self, milvus: AsyncMilvusOperator, documents: List[Dict]):
        self.milvus = milvus
        self.documents = documents
        self.reranker = QwenReranker()
        self.query_rewriter = QueryRewriter()
        self.multi_query_generator = MultiQueryGenerator()

    async def retrieve(self, query: str, strategy: str = "basic", top_k: int = 5) -> List[Tuple[str, float]]:
        """
        执行检索
        
        Args:
            query: 查询文本
            strategy: 检索策略
                - basic: 基础向量检索
                - hybrid: 混合检索（向量+BM25+RRF）
                - rerank: 混合检索+Reranking
                - query_rewrite: 查询改写+混合检索
                - multi_query: 多查询+混合检索
                - full: 完整Pipeline（查询改写+多查询+混合检索+Reranking）
            top_k: 返回结果数
        
        Returns:
            检索结果列表
        """
        await self.milvus.async_milvus_client.load_collection("mix_search_demo")

        if strategy == "basic":
            # 基础向量检索
            query_embedding = get_text_embedding(query)
            dense_results, _ = await self.milvus.vector_search(
                [query_embedding['embedding']],
                [{i["index"]: i["value"] for i in query_embedding["sparse_embedding"]}]
            )
            results = [(hit['entity']['text'], hit['distance']) for hit in dense_results[0][:top_k]]
            return results

        elif strategy == "hybrid":
            # 混合检索
            query_embedding = get_text_embedding(query)
            hybrid_results = await self.milvus.conduct_hybrid_search(
                "mix_search_demo",
                [query_embedding['embedding']],
                [{i["index"]: i["value"] for i in query_embedding["sparse_embedding"]}]
            )
            results = [(hit['entity']['text'], hit['distance']) for hits in hybrid_results for hit in hits[:top_k]]
            return results

        elif strategy == "rerank":
            # 混合检索 + Reranking
            query_embedding = get_text_embedding(query)
            hybrid_results = await self.milvus.conduct_hybrid_search(
                "mix_search_demo",
                [query_embedding['embedding']],
                [{i["index"]: i["value"] for i in query_embedding["sparse_embedding"]}]
            )
            candidate_docs = [hit['entity']['text'] for hits in hybrid_results for hit in hits[:20]]
            reranked = self.reranker.rerank(query, candidate_docs, top_k=top_k)
            return reranked

        elif strategy == "query_rewrite":
            # 查询改写 + 混合检索（使用HyDE）
            hyde_doc = self.query_rewriter.hyde_generate(query)
            query_embedding = get_text_embedding(hyde_doc)
            hybrid_results = await self.milvus.conduct_hybrid_search(
                "mix_search_demo",
                [query_embedding['embedding']],
                [{i["index"]: i["value"] for i in query_embedding["sparse_embedding"]}]
            )
            results = [(hit['entity']['text'], hit['distance']) for hits in hybrid_results for hit in hits[:top_k]]
            return results

        elif strategy == "multi_query":
            # 多查询 + 混合检索
            variants = self.multi_query_generator.generate_variants(query, num_variants=3)
            all_queries = [query] + variants

            # 使用多查询检索
            results = await multi_query_retrieval(self.milvus, all_queries, top_k=top_k)
            return results

        elif strategy == "full":
            # 完整Pipeline
            # 1. 查询改写
            hyde_doc = self.query_rewriter.hyde_generate(query)

            # 2. 多查询
            variants = self.multi_query_generator.generate_variants(query, num_variants=2)
            all_queries = [query, hyde_doc] + variants

            # 3. 多查询混合检索
            fused_results = await multi_query_retrieval(self.milvus, all_queries, top_k=20)
            candidate_docs = [doc for doc, _ in fused_results]

            # 4. Reranking
            reranked = self.reranker.rerank(query, candidate_docs, top_k=top_k)
            return reranked

        else:
            raise ValueError(f"Unknown strategy: {strategy}")


async def exercise_5_comprehensive_evaluation():
    """练习5：高级检索策略综合评估"""
    print("\n" + "=" * 80)
    print("练习5：高级检索策略综合评估")
    print("=" * 80 + "\n")

    # 1. 初始化
    documents = create_sample_documents()
    milvus = AsyncMilvusOperator()
    pipeline = RetrievalPipeline(milvus, documents)

    # 2. 准备测试查询
    test_queries = [
        "什么是RAG技术？",
        "向量数据库的作用",
        "深度学习和机器学习的关系"
    ]

    # 3. 测试不同策略
    strategies = ["basic", "hybrid", "rerank", "query_rewrite", "multi_query", "full"]

    print("🧪 开始策略对比测试...\n")
    print("=" * 80)

    import time

    for query in test_queries:
        print(f"\n📝 测试查询：{query}")
        print("-" * 80)

        for strategy in strategies:
            try:
                start_time = time.time()

                # 执行检索
                results = await pipeline.retrieve(query, strategy=strategy, top_k=5)

                elapsed_time = time.time() - start_time

                # 显示结果
                print(f"\n【{strategy}】策略结果 (耗时: {elapsed_time:.2f}秒):")
                for i, (doc, score) in enumerate(results[:3], 1):
                    print(f"  {i}. [分数: {score:.4f}] {doc[:60]}...")

            except Exception as e:
                print(f"\n【{strategy}】策略执行失败: {e}")

    print("\n" + "=" * 80)
    print("策略对比总结")
    print("=" * 80)

    print("""
各策略特点：

1. basic (基础向量检索)
   - 只使用密集向量检索
   - 速度最快
   - 适合：简单语义匹配

2. hybrid (混合检索)
   - 密集向量 + BM25稀疏向量 + RRF融合
   - 平衡语义和关键词
   - 适合：大多数场景（推荐）

3. rerank (混合检索+重排序)
   - 在hybrid基础上使用Qwen3 Reranker
   - 提升Top-K精确度
   - 适合：高质量要求场景

4. query_rewrite (查询改写+混合检索)
   - 使用HyDE生成假设答案
   - 提升语义匹配
   - 适合：短查询或模糊查询

5. multi_query (多查询+混合检索)
   - 生成多个查询变体
   - 提高召回率
   - 适合：需要全面覆盖的场景

6. full (完整Pipeline)
   - 结合所有技术
   - 最高准确率，最慢速度
   - 适合：离线分析或关键场景
    """)

    print("\n✅ 练习5完成！")
    print("\n🎯 核心优化亮点：")
    print("  ✨ 充分利用DashScope的BM25稀疏向量")
    print("  ✨ 使用Milvus内置RRF融合")
    print("  ✨ 使用阿里云Qwen3 Reranker")
    print("  ✨ 多种检索策略灵活组合")
    print("\n💡 使用建议：")
    print(f"  • 日常使用: hybrid 策略（平衡性能和效果）")
    print(f"  • 高质量场景: rerank 或 full 策略")
    print(f"  • 快速响应: basic 策略")
    print()


# ============================================================================
# 主程序
# ============================================================================

async def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("🎯 讲17 | 高级检索策略 - 实践练习")
    print("=" * 80)

    try:
        # 运行所有练习
        await exercise_1_hybrid_retrieval()
        await exercise_2_reranker_integration()
        await exercise_3_query_rewriting()
        await exercise_4_multi_query_retrieval()
        await exercise_5_comprehensive_evaluation()

        print("\n" + "=" * 80)
        print("🎉 所有练习完成！")
        print("=" * 80)
        print("\n总结：")
        print("✅ 练习1：实现了混合检索（向量检索+BM25+RRF融合）")
        print("✅ 练习2：集成了Reranker模型进行结果重排序")
        print("✅ 练习3：实现了三种查询改写策略（扩展、简化、HyDE）")
        print("✅ 练习4：实现了多查询检索与结果聚合")
        print("✅ 练习5：构建了完整的检索Pipeline并进行综合评估")
        print("\n💡 关键收获：")
        print("  • 混合检索结合了语义理解和精确匹配的优势")
        print("  • Reranking能显著提升Top-K结果的相关性")
        print("  • 查询改写可以根据不同场景优化检索效果")
        print("  • 多查询检索能够提高召回率和覆盖度")
        print("  • 使用Milvus内置RRF融合简化实现")
        print()

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
