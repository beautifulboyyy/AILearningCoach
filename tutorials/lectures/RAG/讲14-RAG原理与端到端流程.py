#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
讲14 | RAG原理与端到端流程 - 实践练习
全程使用DeepSeek官方模型，与阿里云的嵌入模型

依赖安装：
pip install langchain langchain-openai langchain-community langchain-text-splitters pymilvus python-dotenv

环境变量配置（.env文件）：
OPENAI_API_KEY=your_deepseek_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key
"""
from dotenv import load_dotenv

_ = load_dotenv()

# ============================================================================
# 练习1：理解RAG流程
# ============================================================================

def exercise_1_rag_flow():
    """
    练习1：理解RAG流程
    画出RAG系统的完整流程图，标注每个步骤的作用
    """
    print("=" * 80)
    print("练习1：RAG系统完整流程图")
    print("=" * 80)

    flow_diagram = """
    RAG（检索增强生成）系统完整流程图
    =====================================
    
    【离线阶段：索引（Indexing）】
    ┌─────────────────────────────────────────────────────────────┐
    │ 1. 文档加载                                                  │
    │    └─ 作用：读取各种格式文档（PDF, Word, Markdown等）      │
    │         ↓                                                    │
    │ 2. 文本分块（Chunking）                                     │
    │    └─ 作用：将长文档切分为小块，保持语义完整               │
    │         ↓                                                    │
    │ 3. 向量化（Embedding）                                      │
    │    └─ 作用：将文本转换为数值向量表示                       │
    │         ↓                                                    │
    │ 4. 存储到向量数据库                                         │
    │    └─ 作用：持久化向量，支持高效检索                       │
    └─────────────────────────────────────────────────────────────┘
    
    【在线阶段：查询处理】
    ┌─────────────────────────────────────────────────────────────┐
    │ 5. 用户提问                                                  │
    │    └─ 输入：自然语言问题                                    │
    │         ↓                                                    │
    │ 6. 查询处理                                                  │
    │    └─ 作用：优化查询、去噪、同义词扩展                     │
    │         ↓                                                    │
    │ 7. 查询向量化                                               │
    │    └─ 作用：将问题转换为向量（与文档同空间）               │
    │         ↓                                                    │
    │ 8. 向量检索                                                  │
    │    └─ 作用：在向量库中搜索相似文档                         │
    │         ↓                                                    │
    │ 9. 获取Top-K文档                                            │
    │    └─ 作用：返回最相关的K个文档片段                        │
    │         ↓                                                    │
    │ 10. 可选：重排序（Reranking）                               │
    │     └─ 作用：使用更精确的模型重新排序                      │
    └─────────────────────────────────────────────────────────────┘
    
    【在线阶段：生成（Generation）】
    ┌─────────────────────────────────────────────────────────────┐
    │ 11. 构造Prompt                                               │
    │     └─ 作用：将查询和检索到的文档组合成完整提示           │
    │         ↓                                                    │
    │ 12. 调用LLM                                                  │
    │     └─ 作用：基于上下文生成回答                            │
    │         ↓                                                    │
    │ 13. 后处理                                                   │
    │     └─ 作用：格式化、添加引用、提取来源                    │
    │         ↓                                                    │
    │ 14. 返回结果                                                 │
    │     └─ 输出：答案 + 来源 + 置信度                          │
    └─────────────────────────────────────────────────────────────┘
    
    【关键技术点】
    - 相似度计算：余弦相似度（最常用）
    - 分块策略：固定大小 + 重叠（避免信息截断）
    - 检索优化：混合检索（向量+关键词）+ 重排序
    - Prompt设计：明确要求基于文档回答，避免幻觉
    """

    print(flow_diagram)
    print("\n✅ 流程图展示完成！")
    print("\n【三大阶段总结】")
    print("1. 索引阶段（离线）：文档 → 分块 → 向量化 → 存储")
    print("2. 检索阶段（在线）：查询 → 向量化 → 搜索 → Top-K")
    print("3. 生成阶段（在线）：Prompt构造 → LLM生成 → 后处理")

    return flow_diagram


from http import HTTPStatus

import dashscope
# ============================================================================
# 练习2：简单实现（基础RAG系统）
# ============================================================================
from pymilvus import MilvusClient, DataType


def get_text_embedding(text: str, dimension: int = 1024):
    """
    Asynchronously get text embedding using DashScope

    Args:
        text: Input text to get embedding for
        dimension: Dimension of the output embedding vector

    Returns:
        Response from DashScope API
    """
    resp = dashscope.TextEmbedding.call(
        model=dashscope.TextEmbedding.Models.text_embedding_v3,
        input=text,
        dimension=dimension,
        output_type="dense",
    )

    if resp.status_code == HTTPStatus.OK:
        return resp
    else:
        raise Exception(f"Error getting embedding: {resp}")


class MilvusOperator:
    """Milvus向量数据库操作类"""

    def __init__(self, uri="http://localhost:19530", collection_name="mix_search_demo"):
        """
        初始化Milvus客户端
        
        Args:
            uri: Milvus连接地址
                - 服务器模式: "http://localhost:19530"
                - 本地文件模式: "./milvus_xxx.db"
            collection_name: 集合名称
        """
        self.milvus_client = MilvusClient(uri=uri)
        self.collection_name = collection_name

    def create_schema(self):
        """创建集合的Schema"""
        schema = self.milvus_client.create_schema(auto_id=True, description="这是测试参数模型")
        schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True, description="这是主键")
        schema.add_field("dense_vector", DataType.FLOAT_VECTOR, dim=1024, description="这是密集向量")
        schema.add_field("text", DataType.VARCHAR, max_length=4096, description="这是文本内容")
        return schema

    def create_collection(self):
        """创建集合并建立索引"""
        collection = self.milvus_client.create_collection(
            collection_name=self.collection_name,
            schema=self.create_schema(),
            description="这是混合检索的demo"
        )
        #构建索引
        index_params = self.milvus_client.prepare_index_params()
        index_params.add_index(field_name="dense_vector", metric_type="COSINE", index_type="IVF_FLAT")
        self.milvus_client.create_index(collection_name=self.collection_name, index_params=index_params)

    def create_collection_simple(self, dimension=1024):
        """创建简化版集合（用于快速演示）"""
        self.milvus_client.create_collection(
            collection_name=self.collection_name,
            dimension=dimension,
            metric_type="COSINE",
            auto_id=True
        )

    def drop_collection_if_exists(self):
        """删除集合（如果存在）"""
        if self.collection_name in self.milvus_client.list_collections():
            self.milvus_client.drop_collection(self.collection_name)
            return True
        return False

    def vector_insert(self, data):
        """插入向量数据"""
        res = self.milvus_client.insert(collection_name=self.collection_name, data=data)
        return res

    def vector_search(self, dense_vector: list, limit: int = 10, output_fields: list = None):
        """
        向量检索
        
        Args:
            dense_vector: 查询向量
            limit: 返回结果数量
            output_fields: 需要返回的字段列表
        """
        if output_fields is None:
            output_fields = ["text"]

        self.milvus_client.load_collection(collection_name=self.collection_name)
        dense_vector_result = self.milvus_client.search(
            collection_name=self.collection_name,
            anns_field="dense_vector",
            search_params={"metric_type": "COSINE"},
            limit=limit,
            output_fields=output_fields,
            data=dense_vector
        )
        return dense_vector_result

    def close(self):
        """关闭数据库连接"""
        self.milvus_client.close()


def exercise_2_simple_implementation():
    """
    练习2：简单实现
    使用LangChain实现一个基础的RAG系统
    """
    print("\n" + "=" * 80)
    print("练习2：简单实现 - 基础RAG系统")
    print("=" * 80)

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from openai import OpenAI

    # 步骤1: 准备示例文档
    print("\n【步骤1】准备示例文档...")

    sample_document = """
    Python是一种高级编程语言，由Guido van Rossum于1991年首次发布。
    Python的设计哲学强调代码的可读性和简洁的语法，尤其是使用空格缩进来表示代码块。
    
    Python的主要特点包括：
    1. 易于学习：语法简单清晰，适合初学者
    2. 功能强大：拥有丰富的标准库和第三方库
    3. 跨平台：可以在Windows、Linux、Mac OS等多种操作系统上运行
    4. 应用广泛：可用于Web开发、数据科学、人工智能、自动化等领域
    
    Python的应用领域：
    - Web开发：Django、Flask等框架
    - 数据科学：NumPy、Pandas、Matplotlib等
    - 机器学习：Scikit-learn、TensorFlow、PyTorch等
    - 自动化脚本：系统管理、测试自动化等
    - 游戏开发：Pygame等
    
    Python 3是目前的主流版本，相比Python 2有许多改进和新特性。
    Python社区非常活跃，提供了大量的学习资源和开源项目。
    """

    print(f"   ✓ 文档长度: {len(sample_document)} 字符")
    print(f"   ✓ 文档内容: Python编程语言介绍")

    # 步骤2: 文本分块
    print("\n【步骤2】文本分块...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,  # 每块200字符
        chunk_overlap=20,  # 重叠20字符
        length_function=len,
        separators=["\n\n", "\n", "。", ". ", " ", ""]
    )

    chunks = text_splitter.split_text(sample_document)
    print(f"   ✓ 分块数量: {len(chunks)} 个")

    for i, chunk in enumerate(chunks, 1):
        print(f"   块 {i}: {chunk[:50]}..." if len(chunk) > 50 else f"   块 {i}: {chunk}")

    # 步骤3: 向量化和存储
    print("\n【步骤3】向量化文本块并存储到向量数据库...")

    # 使用MilvusOperator类（远程服务器模式）
    milvus_op = MilvusOperator(
        uri="http://211.65.101.204:19530",
        collection_name="rag"
    )

    # 删除旧集合（如果存在）
    if milvus_op.drop_collection_if_exists():
        print(f"   ✓ 删除旧集合: {milvus_op.collection_name}")

    # 创建集合（使用完整版本，与练习3-5保持一致）
    print(f"   ✓ 创建集合: {milvus_op.collection_name}")
    milvus_op.create_collection()

    # 向量化并插入
    data_to_insert = []
    for i, chunk in enumerate(chunks):
        # 获取向量
        embedding_resp = get_text_embedding(chunk, dimension=1024)
        vector = embedding_resp.output['embeddings'][0]['embedding']

        data_to_insert.append({
            'dense_vector': vector,
            'text': chunk
        })
        print(f"   ✓ 向量化块 {i + 1}/{len(chunks)}")

    # 批量插入
    milvus_op.vector_insert(data_to_insert)
    print(f"   ✓ 成功插入 {len(data_to_insert)} 个向量")

    # 步骤4: 执行查询
    print("\n【步骤4】执行检索查询...")

    query = "Python有哪些应用领域？"
    print(f"   查询问题: {query}")

    # 查询向量化
    query_embedding_resp = get_text_embedding(query, dimension=1024)
    query_vector = query_embedding_resp.output['embeddings'][0]['embedding']
    print("   ✓ 查询向量化完成")

    # 向量检索（使用MilvusOperator）
    search_results = milvus_op.vector_search(
        dense_vector=[query_vector],
        limit=3,  # 返回Top-3
        output_fields=["text"]
    )

    print(f"   ✓ 检索到 {len(search_results[0])} 个相关文档")

    # 步骤5: 展示检索结果
    print("\n【步骤5】检索结果展示...")

    retrieved_texts = []
    for i, result in enumerate(search_results[0], 1):
        distance = result['distance']
        text = result['entity']['text']
        retrieved_texts.append(text)

        print(f"\n   结果 {i}:")
        print(f"   相似度: {distance:.4f}")
        print(f"   内容: {text}")

    # 步骤6: 使用LLM生成答案
    print("\n【步骤6】基于检索结果生成答案...")

    # 初始化DeepSeek客户端
    client = OpenAI()

    # 构造上下文
    context = "\n\n".join(retrieved_texts)

    # 构造Prompt
    system_prompt = "你是一个AI助手，请根据提供的文档内容回答用户的问题。"

    user_prompt = f"""参考文档：
{context}

问题：{query}

请基于上述文档回答问题。"""

    # 调用LLM
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )

    answer = response.choices[0].message.content

    print("\n" + "─" * 80)
    print(f"问题: {query}")
    print("─" * 80)
    print(f"答案: {answer}")
    print("─" * 80)

    # 步骤7: 总结RAG流程
    print("\n" + "=" * 80)
    print("✅ 基础RAG系统演示完成！")
    print("=" * 80)

    print("\n【RAG流程回顾】")
    print("1. 准备文档 → 加载了Python介绍文档")
    print("2. 文本分块 → 将长文档切分为小块")
    print("3. 向量化   → 使用Embedding模型转换为向量")
    print("4. 存储     → 保存到Milvus向量数据库（使用MilvusOperator）")
    print("5. 查询     → 用户提问并向量化")
    print("6. 检索     → 找到最相关的文档块（使用MilvusOperator）")
    print("7. 生成     → LLM基于文档生成答案")

    print("\n【关键技术】")
    print("- 向量化模型: DashScope text-embedding-v3")
    print("- 向量数据库: Milvus (本地文件模式)")
    print("- 操作封装: MilvusOperator类")
    print("- 相似度计算: 余弦相似度 (COSINE)")
    print("- 生成模型: DeepSeek-chat")

    print("\n【与传统LLM的对比】")
    print("❌ 传统LLM: 只能基于训练数据回答，可能产生幻觉")
    print("✅ RAG系统: 基于实际文档回答，更准确可靠")

    # 清理
    print("\n【清理资源】")
    milvus_op.close()
    print("   ✓ 已关闭数据库连接")

    return {
        'query': query,
        'answer': answer,
        'chunks': chunks,
        'retrieved_texts': retrieved_texts,
        'milvus_operator': milvus_op
    }


# ============================================================================
# 练习3：文档索引（准备多个文档）
# ============================================================================

def exercise_3_document_indexing():
    """
    练习3：文档索引
    准备5-10个文档，进行分块和向量化
    """
    print("\n" + "=" * 80)
    print("练习3：文档索引 - 加载、分块、向量化")
    print("=" * 80)

    import os
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # 1. 加载文档
    print("\n【步骤1】加载文档...")
    data_dir = r"D:\Code\python\teach_llm\lectures\file"
    documents = []

    for filename in os.listdir(data_dir):
        if filename.endswith('.txt'):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                documents.append({
                    'filename': filename,
                    'content': content
                })
                print(f"   ✓ 加载文档: {filename} (长度: {len(content)}字符)")

    print(f"\n   共加载 {len(documents)} 个文档")

    # 2. 文本分块
    print("\n【步骤2】文本分块...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,  # 每块300字符
        chunk_overlap=50,  # 重叠50字符，避免信息截断
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
    )

    all_chunks = []
    for doc in documents:
        chunks = text_splitter.split_text(doc['content'])
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                'filename': doc['filename'],
                'chunk_id': i,
                'text': chunk
            })
        print(f"   ✓ {doc['filename']}: 分成 {len(chunks)} 个块")

    print(f"\n   总共生成 {len(all_chunks)} 个文本块")

    # 3. 向量化并存储到Milvus
    print("\n【步骤3】向量化并存储到Milvus...")

    # 使用MilvusOperator类（远程服务器模式）
    milvus_op = MilvusOperator(
        uri="http://211.65.101.204:19530",
        collection_name="mix_search_demo"
    )

    # 删除旧集合（如果存在）
    if milvus_op.drop_collection_if_exists():
        print("   ✓ 删除旧集合...")

    # 创建新集合
    print("   ✓ 创建新集合...")
    milvus_op.create_collection()

    # 批量向量化和插入
    batch_size = 10
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]

        # 准备插入数据
        insert_data = []
        for chunk in batch:
            # 获取向量
            embedding_resp = get_text_embedding(chunk['text'], dimension=1024)
            vector = embedding_resp.output['embeddings'][0]['embedding']

            # 构造元数据文本（包含文件名和内容）
            metadata_text = f"[文件: {chunk['filename']}]\n{chunk['text']}"

            insert_data.append({
                'dense_vector': vector,
                'text': metadata_text[:4096]  # 限制长度
            })

        # 批量插入
        milvus_op.vector_insert(insert_data)
        print(f"   ✓ 已处理 {min(i + batch_size, len(all_chunks))}/{len(all_chunks)} 个块")

    print(f"\n✅ 文档索引完成！共索引 {len(all_chunks)} 个文本块")

    return {
        'documents': documents,
        'chunks': all_chunks,
        'milvus_operator': milvus_op
    }


# ============================================================================
# 练习4：检索测试
# ============================================================================

def exercise_4_retrieval_test(milvus_op):
    """
    练习4：检索测试
    测试不同查询，观察检索结果的相关性
    """
    print("\n" + "=" * 80)
    print("练习4：检索测试 - 测试不同查询的检索效果")
    print("=" * 80)

    # 准备测试查询
    test_queries = [
        "什么是冰箱？",
        "冰箱有哪些常见架构？",
        "冰箱的优势是什么？",
        "冰箱的主要特点"
    ]

    for idx, query in enumerate(test_queries, 1):
        print(f"\n{'─' * 80}")
        print(f"【测试 {idx}】查询: {query}")
        print('─' * 80)

        # 1. 查询向量化
        query_embedding_resp = get_text_embedding(query, dimension=1024)
        query_vector = query_embedding_resp.output['embeddings'][0]['embedding']

        # 2. 向量检索（Top-10）
        search_results = milvus_op.vector_search(
            dense_vector=[query_vector],
            limit=10,
            output_fields=["text"]
        )

        # 3. 显示检索结果
        print(f"\n检索到 Top-{len(search_results[0])} 相关文档:\n")

        for i, result in enumerate(search_results[0], 1):
            distance = result['distance']
            text = result['entity']['text']

            # 提取文件名
            filename = "未知"
            if text.startswith('[文件:'):
                filename = text.split(']')[0].replace('[文件:', '').strip()
                content = text.split(']', 1)[1].strip()
            else:
                content = text

            # 相似度（余弦相似度，1表示完全相同）
            print(f"   结果 {i}:")
            print(f"   相似度: {distance:.4f}")
            print(f"   来源: {filename}")
            print(f"   内容预览: {content[:150]}...")
            print()

    print("\n✅ 检索测试完成！")
    print("\n【观察总结】")
    print("- 相似度越高（接近1.0），表示文档与查询越相关")
    print("- 检索结果应该能覆盖查询的主要信息")
    print("- 可以通过调整chunk_size、top_k等参数优化检索效果")


# ============================================================================
# 练习5：端到端应用（完整文档问答）
# ============================================================================

def exercise_5_end_to_end_qa(milvus_op):
    """
    练习5：端到端应用
    构建一个完整的文档问答应用
    """
    print("\n" + "=" * 80)
    print("练习5：端到端RAG应用 - 完整的文档问答系统")
    print("=" * 80)

    from openai import OpenAI

    # 初始化DeepSeek客户端
    client = OpenAI()

    def rag_qa(question: str, top_k: int = 3) -> dict:
        """
        RAG问答主函数
        
        Args:
            question: 用户问题
            top_k: 检索文档数量
            
        Returns:
            包含答案、来源等信息的字典
        """
        # 步骤1: 查询向量化
        print(f"\n🔍 步骤1: 向量化查询...")
        query_embedding_resp = get_text_embedding(question, dimension=1024)
        query_vector = query_embedding_resp.output['embeddings'][0]['embedding']

        # 步骤2: 向量检索
        print(f"🔍 步骤2: 检索相关文档 (Top-{top_k})...")
        search_results = milvus_op.vector_search(
            dense_vector=[query_vector],
            limit=top_k,
            output_fields=["text"]
        )

        # 提取检索到的文档
        retrieved_docs = []
        for result in search_results[0][:top_k]:
            text = result['entity']['text']
            distance = result['distance']

            # 提取文件名和内容
            if text.startswith('[文件:'):
                filename = text.split(']')[0].replace('[文件:', '').strip()
                content = text.split(']', 1)[1].strip()
            else:
                filename = "未知"
                content = text

            retrieved_docs.append({
                'filename': filename,
                'content': content,
                'similarity': distance
            })
            print(f"   ✓ {filename} (相似度: {distance:.4f})")

        # 步骤3: 构造Prompt
        print(f"\n📝 步骤3: 构造Prompt...")

        # 组合检索到的文档
        context = "\n\n---\n\n".join([
            f"文档来源: {doc['filename']}\n内容:\n{doc['content']}"
            for doc in retrieved_docs
        ])

        # 构造完整的Prompt
        system_prompt = """你是一个专业的AI助手，擅长根据提供的文档回答问题。

请遵循以下规则：
1. 基于提供的文档内容回答问题
2. 如果文档中没有相关信息，明确告知用户
3. 回答要准确、简洁、有条理
4. 可以引用文档来源增强可信度"""

        user_prompt = f"""参考文档：

{context}

---

问题：{question}

请基于上述文档回答问题。"""

        # 步骤4: 调用LLM生成答案
        print(f"🤖 步骤4: 调用LLM生成答案...")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        answer = response.choices[0].message.content

        # 返回结果
        return {
            'question': question,
            'answer': answer,
            'sources': retrieved_docs,
            'context': context
        }

    # 测试问题
    test_questions = [
        "什么是冰箱？它有什么优势？",
        "冰箱有哪几种类型？",
        "冰箱使用什么技术？",
        "冰箱面临哪些挑战？"
    ]

    print("\n开始问答测试...\n")

    for idx, question in enumerate(test_questions, 1):
        print("\n" + "=" * 80)
        print(f"【问题 {idx}】{question}")
        print("=" * 80)

        result = rag_qa(question, top_k=3)

        print(f"\n💡 答案:")
        print("-" * 80)
        print(result['answer'])
        print("-" * 80)

        print(f"\n📚 参考来源:")
        for i, source in enumerate(result['sources'], 1):
            print(f"   {i}. {source['filename']} (相似度: {source['similarity']:.4f})")

        print()

    print("\n" + "=" * 80)
    print("✅ 端到端RAG应用测试完成！")
    print("=" * 80)

    print("\n【系统特点】")
    print("✓ 离线索引：文档已预处理并存储在向量数据库")
    print("✓ 在线检索：实时向量搜索找到相关文档")
    print("✓ 增强生成：基于检索文档生成准确答案")
    print("✓ 可追溯性：提供答案来源，增强可信度")

    print("\n【可以优化的方向】")
    print("- 改进分块策略（动态chunk size、语义分块）")
    print("- 使用更好的Embedding模型")
    print("- 添加重排序（Reranking）步骤")
    print("- 实现混合检索（向量+关键词）")
    print("- 添加查询改写和扩展")
    print("- 实现对话历史管理")


# ============================================================================
# 主程序
# ============================================================================

def main():
    """主程序：依次运行所有练习"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "RAG 原理与端到端流程 - 实践练习" + " " * 25 + "║")
    print("╚" + "═" * 78 + "╝")

    # 练习1：理解RAG流程
    exercise_1_rag_flow()

    # 练习2：简单实现（基础RAG系统）
    exercise_2_simple_implementation()

    # 练习3：文档索引
    result = exercise_3_document_indexing()
    milvus_op = result['milvus_operator']

    # 练习4：检索测试
    exercise_4_retrieval_test(milvus_op)

    # 练习5：端到端应用
    exercise_5_end_to_end_qa(milvus_op)

    print("\n" + "=" * 80)
    print("🎉 所有练习完成！")
    print("=" * 80)
    print("\n【学习总结】")
    print("1. RAG流程：索引 → 检索 → 生成")
    print("2. 关键组件：文档处理、向量数据库、LLM")
    print("3. 核心优势：实时性、可追溯、成本低")
    print("4. 应用场景：企业知识库、文档问答、智能客服等")
    print("\n继续学习下一讲：《文档处理与分块》，深入了解RAG的第一步！")


if __name__ == "__main__":
    main()
