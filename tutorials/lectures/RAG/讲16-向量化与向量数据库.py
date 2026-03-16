#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
讲16 | 向量化与向量数据库 - 实践练习
使用Milvus向量数据库和DashScope Embedding API

依赖安装：
pip install pymilvus dashscope python-dotenv langchain langchain-community numpy

环境变量配置（.env文件）：
DASHSCOPE_API_KEY=your_dashscope_api_key

Milvus要求：
需要启动Milvus服务（默认 http://211.65.101.204:19530）
Docker启动命令：
docker run -d --name milvus -p 19530:19530 -p 9091:9091 milvusdb/milvus:latest
"""

import os
import time
from http import HTTPStatus

import dashscope
import numpy as np
from dotenv import load_dotenv
from pymilvus import MilvusClient, DataType

_ = load_dotenv()


# ============================================================================
# 辅助函数：获取文本向量
# ============================================================================

def get_text_embedding(text: str, dimension: int = 1024):
    """使用DashScope获取文本向量"""
    resp = dashscope.TextEmbedding.call(
        model=dashscope.TextEmbedding.Models.text_embedding_v3,
        input=text,
        dimension=dimension,
        output_type="dense",
    )

    if resp.status_code == HTTPStatus.OK:
        return resp.output['embeddings'][0]['embedding']
    else:
        raise Exception(f"Error getting embedding: {resp}")


# ============================================================================
# 练习1：向量数据库部署与基础操作
# ============================================================================

def exercise_1_milvus_basic_operations():
    """
    练习1：向量数据库部署与基础操作
    包括：创建Collection、批量插入、向量检索、结果过滤
    """
    print("=" * 80)
    print("练习1：向量数据库部署与基础操作")
    print("=" * 80)

    # 准备测试数据
    test_texts = [
        "Python是一种高级编程语言，适合初学者学习。",
        "机器学习是人工智能的一个重要分支。",
        "深度学习使用神经网络来处理复杂的数据。",
        "自然语言处理让计算机理解人类语言。",
        "向量数据库专门用于存储和检索向量数据。",
        "RAG技术结合了检索和生成两种方法。",
        "Transformer模型revolutionized NLP领域。",
        "BERT和GPT是两种流行的预训练模型。",
        "数据科学需要统计学和编程技能。",
        "云计算提供了弹性的计算资源。",
    ]

    print(f"\n准备 {len(test_texts)} 条测试数据")

    # 步骤1：连接Milvus并创建Collection
    print("\n步骤1: 创建Collection")

    client = MilvusClient(uri="http://211.65.101.204:19530")
    collection_name = "basic_demo"

    # 删除旧集合（如果存在）
    if collection_name in client.list_collections():
        client.drop_collection(collection_name)
        print(f"删除旧集合: {collection_name}")

    # 创建schema
    schema = client.create_schema(
        auto_id=True,
        description="基础操作演示集合"
    )

    schema.add_field("id", DataType.INT64, is_primary=True)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=1024)
    schema.add_field("text", DataType.VARCHAR, max_length=1000)
    schema.add_field("category", DataType.VARCHAR, max_length=50)  # 用于过滤

    # 创建集合
    client.create_collection(
        collection_name=collection_name,
        schema=schema
    )

    print(f"创建集合: {collection_name}")

    # 创建索引（使用HNSW）
    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="vector",
        index_type="HNSW",
        metric_type="COSINE",
        params={"M": 16, "efConstruction": 200}
    )
    client.create_index(collection_name, index_params)
    print("创建HNSW索引")

    # 步骤2：批量插入数据
    print("\n步骤2: 批量插入数据")

    # 为每条文本分配类别（用于演示过滤）
    categories = ["AI", "AI", "AI", "AI", "Database", "AI", "AI", "AI", "DataScience", "Cloud"]

    data_to_insert = []
    for i, text in enumerate(test_texts):
        vector = get_text_embedding(text, dimension=1024)
        data_to_insert.append({
            'vector': vector,
            'text': text,
            'category': categories[i]
        })
        print(f"向量化 {i + 1}/{len(test_texts)}")

    # 批量插入
    insert_result = client.insert(collection_name, data_to_insert)
    print(f"成功插入 {len(data_to_insert)} 条数据")

    # 步骤3：向量检索（无过滤）
    print("\n步骤3: 基础向量检索")

    query_text = "什么是深度学习？"
    print(f"查询: {query_text}")

    query_vector = get_text_embedding(query_text, dimension=1024)

    # 加载集合并搜索
    client.load_collection(collection_name)

    search_results = client.search(
        collection_name=collection_name,
        data=[query_vector],
        anns_field="vector",
        search_params={"metric_type": "COSINE", "params": {"ef": 100}},
        limit=3,
        output_fields=["text", "category"]
    )

    print(f"\nTop-3 结果:")
    for i, result in enumerate(search_results[0], 1):
        print(f"{i}. 相似度:{result['distance']:.3f} 类别:{result['entity']['category']}")
        print(f"   {result['entity']['text']}")

    # 步骤4：带过滤条件的检索
    print("\n步骤4: 带过滤条件的检索")

    query_text2 = "人工智能相关技术"
    print(f"查询: {query_text2} (只搜索AI类别)")

    query_vector2 = get_text_embedding(query_text2, dimension=1024)

    # 使用filter参数
    search_results_filtered = client.search(
        collection_name=collection_name,
        data=[query_vector2],
        anns_field="vector",
        search_params={"metric_type": "COSINE", "params": {"ef": 100}},
        limit=5,
        output_fields=["text", "category"],
        filter='category == "AI"'  # 过滤条件
    )

    print(f"\nTop-5 结果 (仅AI类别):")
    for i, result in enumerate(search_results_filtered[0], 1):
        print(f"{i}. 相似度:{result['distance']:.3f}")
        print(f"   {result['entity']['text']}")

    # 步骤5：性能测试
    print("\n步骤5: 检索性能测试")

    # 测试多次查询的平均响应时间
    num_queries = 10
    start_time = time.time()

    for _ in range(num_queries):
        client.search(
            collection_name=collection_name,
            data=[query_vector],
            anns_field="vector",
            search_params={"metric_type": "COSINE"},
            limit=10,
            output_fields=["text"]
        )

    elapsed = time.time() - start_time
    avg_latency = elapsed / num_queries * 1000  # 毫秒

    print(f"执行 {num_queries} 次查询")
    print(f"平均延迟: {avg_latency:.2f} ms")
    print(f"QPS: {num_queries / elapsed:.2f}")

    # 清理
    client.close()

    print("\n✅ 练习1完成\n")

    return {
        'collection_name': collection_name,
        'num_vectors': len(data_to_insert),
        'avg_latency_ms': avg_latency
    }


# ============================================================================
# 练习2：相似度度量对比
# ============================================================================

def exercise_2_similarity_metrics_comparison():
    """
    练习2：相似度度量对比
    对比三种相似度计算方法：余弦相似度、欧氏距离、内积
    """
    print("=" * 80)
    print("练习2：相似度度量对比")
    print("=" * 80)

    # 准备测试数据
    test_texts = [
        "Python编程语言非常适合数据分析",
        "Python是数据科学的首选语言",
        "Java是面向对象的编程语言",
        "机器学习需要大量的数据",
        "深度学习是机器学习的子集",
        "今天天气很好，适合出门",
    ]

    print(f"\n准备 {len(test_texts)} 条测试数据")

    # 创建三个Collection，使用不同的相似度度量
    metrics = {
        "COSINE": "余弦相似度",
        "L2": "欧氏距离",
        "IP": "内积"
    }

    client = MilvusClient(uri="http://211.65.101.204:19530")

    collections = {}

    for metric_type, metric_name in metrics.items():
        collection_name = f"similarity_demo_{metric_type.lower()}"

        print(f"\n创建集合: {collection_name} ({metric_name})")

        # 删除旧集合
        if collection_name in client.list_collections():
            client.drop_collection(collection_name)

        # 创建schema
        schema = client.create_schema(auto_id=True)
        schema.add_field("id", DataType.INT64, is_primary=True)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=1024)
        schema.add_field("text", DataType.VARCHAR, max_length=1000)

        # 创建集合
        client.create_collection(collection_name, schema=schema)

        # 创建索引（使用对应的度量类型）
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="HNSW",
            metric_type=metric_type,
            params={"M": 16, "efConstruction": 200}
        )
        client.create_index(collection_name, index_params)

        # 插入数据
        data_to_insert = []
        for text in test_texts:
            vector = get_text_embedding(text, dimension=1024)

            # 对于内积(IP)，需要归一化向量以便比较
            if metric_type == "IP":
                norm = np.linalg.norm(vector)
                vector = [v / norm for v in vector]

            data_to_insert.append({
                'vector': vector,
                'text': text
            })

        client.insert(collection_name, data_to_insert)
        collections[metric_type] = collection_name

        print(f"插入 {len(data_to_insert)} 条数据")

    # 使用相同的查询测试不同度量方式
    query_text = "Python用于数据分析"
    print(f"\n查询文本: {query_text}")

    query_vector = get_text_embedding(query_text, dimension=1024)

    # 对比不同度量的检索结果
    print(f"\n{'=' * 80}")
    print("检索结果对比")
    print(f"{'=' * 80}")

    all_results = {}

    for metric_type, collection_name in collections.items():
        metric_name = metrics[metric_type]

        # 对于IP，也需要归一化查询向量
        search_vector = query_vector.copy()
        if metric_type == "IP":
            norm = np.linalg.norm(search_vector)
            search_vector = [v / norm for v in search_vector]

        client.load_collection(collection_name)

        search_results = client.search(
            collection_name=collection_name,
            data=[search_vector],
            anns_field="vector",
            search_params={"metric_type": metric_type},
            limit=5,
            output_fields=["text"]
        )

        print(f"\n【{metric_name} ({metric_type})】")
        print(f"{'排名':<6} {'相似度/距离':<15} {'文本':<50}")
        print("-" * 75)

        results = []
        for i, result in enumerate(search_results[0], 1):
            distance = result['distance']
            text = result['entity']['text']
            print(f"{i:<6} {distance:<15.4f} {text:<50}")
            results.append({'rank': i, 'score': distance, 'text': text})

        all_results[metric_type] = results

    # 分析结果差异
    print(f"\n{'=' * 80}")
    print("结果分析")
    print(f"{'=' * 80}")

    # 检查Top-1结果是否一致
    top1_texts = [results[0]['text'] for results in all_results.values()]
    if len(set(top1_texts)) == 1:
        print("\n✓ 所有度量方式的Top-1结果一致")
    else:
        print("\n⚠ 不同度量方式的Top-1结果不同:")
        for metric_type, results in all_results.items():
            print(f"  {metrics[metric_type]}: {results[0]['text']}")

    # 解释每种度量
    print(f"\n度量方式说明:")
    print("• 余弦相似度(COSINE): 衡量向量方向的相似性，取值[0,1]，越大越相似")
    print("• 欧氏距离(L2): 衡量向量在空间中的直线距离，越小越相似")
    print("• 内积(IP): 归一化后类似余弦，适用于已归一化的向量，越大越相似")

    print(f"\n推荐:")
    print("• 文本检索: 余弦相似度 (最常用)")
    print("• 图像检索: 欧氏距离或余弦相似度")
    print("• 已归一化数据: 内积 (计算最快)")

    # 清理
    client.close()

    print("\n✅ 练习2完成\n")

    return all_results


# ============================================================================
# 练习3：索引参数调优
# ============================================================================

def exercise_3_index_tuning():
    """
    练习3：索引参数调优
    测试不同索引类型和参数配置，对比性能
    """
    print("=" * 80)
    print("练习3：索引参数调优")
    print("=" * 80)

    # 准备较大规模的测试数据
    print("\n准备测试数据...")

    # 使用讲15的data目录中的文档
    data_dir = "../data"
    test_file = os.path.join(data_dir, "doc1_ai_intro.txt")

    if os.path.exists(test_file):
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 简单分句
        sentences = [s.strip() for s in content.split('。') if len(s.strip()) > 20]
        test_texts = sentences[:100]  # 取前100句
        print(f"从文件加载 {len(test_texts)} 条数据")
    else:
        # 备用：生成测试数据
        base_texts = [
            "机器学习是人工智能的核心技术",
            "深度学习使用神经网络处理数据",
            "自然语言处理让计算机理解语言",
            "计算机视觉处理图像和视频",
            "强化学习通过奖励机制学习策略",
        ]
        test_texts = [f"{text} 变体{i}" for text in base_texts for i in range(20)]
        print(f"生成 {len(test_texts)} 条测试数据")

    # 定义要测试的索引配置
    index_configs = [
        {
            'name': 'FLAT',
            'type': 'FLAT',
            'params': {},
            'description': '暴力搜索，准确率100%'
        },
        {
            'name': 'IVF_FLAT_128',
            'type': 'IVF_FLAT',
            'params': {'nlist': 128},
            'description': 'IVF索引，nlist=128'
        },
        {
            'name': 'HNSW_M8',
            'type': 'HNSW',
            'params': {'M': 8, 'efConstruction': 100},
            'description': 'HNSW索引，M=8'
        },
        {
            'name': 'HNSW_M16',
            'type': 'HNSW',
            'params': {'M': 16, 'efConstruction': 200},
            'description': 'HNSW索引，M=16 (推荐)'
        },
        {
            'name': 'HNSW_M32',
            'type': 'HNSW',
            'params': {'M': 32, 'efConstruction': 400},
            'description': 'HNSW索引，M=32 (高精度)'
        },
    ]

    client = MilvusClient(uri="http://211.65.101.204:19530")

    results = []

    # 准备查询
    query_texts = [
        "什么是机器学习？",
        "深度学习的应用",
        "如何处理自然语言"
    ]

    print(f"\n测试 {len(index_configs)} 种索引配置...\n")

    for config in index_configs:
        print(f"{'=' * 80}")
        print(f"测试配置: {config['name']}")
        print(f"说明: {config['description']}")
        print(f"{'=' * 80}")

        collection_name = f"index_tuning_{config['name'].lower()}"

        # 删除旧集合
        if collection_name in client.list_collections():
            client.drop_collection(collection_name)

        # 创建集合
        schema = client.create_schema(auto_id=True)
        schema.add_field("id", DataType.INT64, is_primary=True)
        schema.add_field("vector", DataType.FLOAT_VECTOR, dim=1024)
        schema.add_field("text", DataType.VARCHAR, max_length=1000)

        client.create_collection(collection_name, schema=schema)

        # 插入数据
        print(f"\n插入数据...")
        data_to_insert = []
        for i, text in enumerate(test_texts):
            vector = get_text_embedding(text, dimension=1024)
            data_to_insert.append({'vector': vector, 'text': text})

            if (i + 1) % 20 == 0:
                print(f"  已处理 {i + 1}/{len(test_texts)}")

        client.insert(collection_name, data_to_insert)

        # 创建索引并计时
        print(f"\n创建索引...")
        index_start = time.time()

        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type=config['type'],
            metric_type="COSINE",
            params=config['params']
        )
        client.create_index(collection_name, index_params)

        index_time = time.time() - index_start
        print(f"索引创建时间: {index_time:.2f}秒")

        # 加载集合
        client.load_collection(collection_name)

        # 测试检索性能
        print(f"\n测试检索性能...")

        search_params = {"metric_type": "COSINE"}
        if config['type'] == 'HNSW':
            search_params['params'] = {'ef': 100}
        elif config['type'] == 'IVF_FLAT':
            search_params['params'] = {'nprobe': 16}

        query_times = []
        all_search_results = []

        for query_text in query_texts:
            query_vector = get_text_embedding(query_text, dimension=1024)

            # 多次查询取平均
            num_runs = 5
            start = time.time()

            for _ in range(num_runs):
                search_results = client.search(
                    collection_name=collection_name,
                    data=[query_vector],
                    anns_field="vector",
                    search_params=search_params,
                    limit=10,
                    output_fields=["text"]
                )

            elapsed = (time.time() - start) / num_runs
            query_times.append(elapsed)
            all_search_results.append(search_results[0])

        avg_query_time = np.mean(query_times) * 1000  # 毫秒

        print(f"平均查询延迟: {avg_query_time:.2f} ms")
        print(f"QPS: {1000 / avg_query_time:.2f}")

        # 保存结果
        results.append({
            'config': config['name'],
            'description': config['description'],
            'index_type': config['type'],
            'index_params': config['params'],
            'index_time': index_time,
            'avg_query_time_ms': avg_query_time,
            'qps': 1000 / avg_query_time,
            'num_vectors': len(test_texts)
        })

        print()

    # 对比分析
    print(f"{'=' * 80}")
    print("性能对比汇总")
    print(f"{'=' * 80}\n")

    print(f"{'配置':<20} {'索引类型':<15} {'索引时间(s)':<15} {'查询延迟(ms)':<15} {'QPS':<10}")
    print("-" * 85)
    for r in results:
        print(f"{r['config']:<20} {r['index_type']:<15} {r['index_time']:<15.2f} "
              f"{r['avg_query_time_ms']:<15.2f} {r['qps']:<10.2f}")

    # 分析和建议
    print(f"\n{'=' * 80}")
    print("分析与建议")
    print(f"{'=' * 80}\n")

    # 找出最快的配置
    fastest = min(results, key=lambda x: x['avg_query_time_ms'])
    print(f"✓ 查询最快: {fastest['config']} ({fastest['avg_query_time_ms']:.2f}ms)")

    # 找出索引构建最快的
    fastest_index = min(results, key=lambda x: x['index_time'])
    print(f"✓ 索引构建最快: {fastest_index['config']} ({fastest_index['index_time']:.2f}s)")

    print(f"\n推荐配置:")
    print(f"• 小规模(<10万): FLAT (简单，准确率100%)")
    print(f"• 中等规模(10万-100万): HNSW M=16 (平衡性能)")
    print(f"• 大规模(>100万): IVF_FLAT 或 HNSW M=8 (速度优先)")
    print(f"• 超大规模(>1000万): IVF_SQ8 或 IVF_PQ (压缩+速度)")

    print(f"\n参数调优技巧:")
    print(f"• HNSW: M越大越准确但更慢，推荐M=16")
    print(f"• IVF: nlist约为sqrt(N)，nprobe控制查询时探查的聚类数")
    print(f"• 搜索参数: ef(HNSW)或nprobe(IVF)越大越准确但更慢")

    # 清理
    client.close()

    print("\n✅ 练习3完成\n")

    return results


# ============================================================================
# 主程序
# ============================================================================

def main():
    """主程序：依次运行所有练习"""
    print("\n向量化与向量数据库 - 实践练习\n")

    try:
        # 练习1：向量数据库部署与基础操作
        exercise_1_milvus_basic_operations()

        # 练习2：相似度度量对比
        exercise_2_similarity_metrics_comparison()

        # 练习3：索引参数调优
        exercise_3_index_tuning()

        print("=" * 80)
        print("🎉 所有练习完成")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
