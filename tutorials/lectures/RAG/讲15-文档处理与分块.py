#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
讲15 | 文档处理与分块 - 实践练习
全程使用LangChain框架实现文档处理与分块
使用Milvus向量数据库计算向量相似度

依赖安装：
pip install langchain langchain-community langchain-text-splitters python-docx pypdf beautifulsoup4 python-dotenv tiktoken pymilvus dashscope

环境变量配置（.env文件）：
OPENAI_API_KEY=your_deepseek_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key

Milvus要求：
需要启动Milvus服务（默认 http://211.65.101.204:19530）
"""

from dotenv import load_dotenv
import os
import json
from typing import List, Dict, Any
from datetime import datetime
import numpy as np

_ = load_dotenv()


# ============================================================================
# 练习1：分块策略对比
# ============================================================================

def exercise_1_chunking_strategies_comparison():
    """
    练习1：分块策略对比
    实现并对比三种分块策略：固定大小、递归、结构化
    """
    print("=" * 80)
    print("练习1：分块策略对比")
    print("=" * 80)

    from langchain_text_splitters import (
        CharacterTextSplitter,
        RecursiveCharacterTextSplitter,
        MarkdownHeaderTextSplitter
    )

    # 准备测试文档（包含多个段落和结构）
    sample_document = """# Python编程语言

## 简介

Python是一种高级编程语言，由Guido van Rossum于1991年首次发布。Python的设计哲学强调代码的可读性和简洁的语法，尤其是使用空格缩进来表示代码块。这种设计使得Python代码非常容易阅读和理解。

## 主要特点

### 易于学习
Python的语法简单清晰，非常适合编程初学者。与其他编程语言相比，Python的学习曲线较为平缓，初学者可以快速上手并编写有用的程序。

### 功能强大
Python拥有丰富的标准库和第三方库，涵盖了从Web开发到数据科学的各个领域。这些库为开发者提供了强大的工具集，大大提高了开发效率。

### 跨平台支持
Python可以在Windows、Linux、Mac OS等多种操作系统上运行。这种跨平台特性使得Python程序具有很好的可移植性，开发者无需为不同平台重写代码。

## 应用领域

### Web开发
Python在Web开发领域有着广泛的应用。Django和Flask是两个最流行的Python Web框架。Django提供了完整的全栈开发工具，而Flask则更加轻量级和灵活。

### 数据科学
在数据科学领域，Python是最受欢迎的编程语言之一。NumPy、Pandas、Matplotlib等库为数据分析和可视化提供了强大的支持。这些工具使得Python成为数据科学家的首选语言。

### 机器学习
Python在机器学习领域占据主导地位。Scikit-learn提供了丰富的机器学习算法，TensorFlow和PyTorch则是深度学习的主流框架。这些工具让研究人员和工程师能够快速构建和部署机器学习模型。

## 版本与社区

Python 3是目前的主流版本，相比Python 2有许多改进和新特性。Python 2已经在2020年停止支持，现在所有新项目都应该使用Python 3。

Python社区非常活跃，提供了大量的学习资源和开源项目。无论你是初学者还是专家，都能在社区中找到帮助和灵感。这个充满活力的社区是Python成功的重要因素之一。"""

    print(f"\n文档长度: {len(sample_document)} 字符\n")

    # 策略1：固定大小分块
    print("固定大小分块 (CharacterTextSplitter)")

    fixed_splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=200,  # 固定200字符
        chunk_overlap=20,
        length_function=len,
    )

    fixed_chunks = fixed_splitter.split_text(sample_document)

    print(f"分块数量: {len(fixed_chunks)}")
    print(f"平均长度: {np.mean([len(c) for c in fixed_chunks]):.1f} 字符")
    print(f"前3个块预览:")
    for i, chunk in enumerate(fixed_chunks[:3], 1):
        print(f"块{i}({len(chunk)}字符): {chunk[:80]}...")

    # 策略2：递归分块
    print(f"\n递归分块 (RecursiveCharacterTextSplitter)")

    recursive_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=20,
        length_function=len,
        separators=["\n\n", "\n", "。", ".", " ", ""]  # 优先级递减
    )

    recursive_chunks = recursive_splitter.split_text(sample_document)

    print(f"分块数量: {len(recursive_chunks)}")
    print(f"平均长度: {np.mean([len(c) for c in recursive_chunks]):.1f} 字符")
    print(f"前3个块预览:")
    for i, chunk in enumerate(recursive_chunks[:3], 1):
        print(f"块{i}({len(chunk)}字符): {chunk[:80]}...")

    # 策略3：结构化分块（基于Markdown标题）
    print(f"\n结构化分块 (MarkdownHeaderTextSplitter)")

    # 定义要分割的标题层级
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )

    structured_chunks = markdown_splitter.split_text(sample_document)

    print(f"分块数量: {len(structured_chunks)}")
    print(f"平均长度: {np.mean([len(doc.page_content) for doc in structured_chunks]):.1f} 字符")
    print(f"前3个块预览:")
    for i, doc in enumerate(structured_chunks[:3], 1):
        print(f"块{i}({len(doc.page_content)}字符) 元数据:{doc.metadata}")

    # 对比分析
    print(f"\n对比统计:")

    comparison_data = {
        '固定大小': {
            'chunks': fixed_chunks,
            'count': len(fixed_chunks),
            'avg_length': np.mean([len(c) for c in fixed_chunks]),
            'std_length': np.std([len(c) for c in fixed_chunks]),
        },
        '递归': {
            'chunks': recursive_chunks,
            'count': len(recursive_chunks),
            'avg_length': np.mean([len(c) for c in recursive_chunks]),
            'std_length': np.std([len(c) for c in recursive_chunks]),
        },
        '结构化': {
            'chunks': [doc.page_content for doc in structured_chunks],
            'count': len(structured_chunks),
            'avg_length': np.mean([len(doc.page_content) for doc in structured_chunks]),
            'std_length': np.std([len(doc.page_content) for doc in structured_chunks]),
        }
    }

    print(f"{'策略':<10} {'块数量':<10} {'平均长度':<15} {'标准差':<15}")
    print("─" * 50)
    for strategy, data in comparison_data.items():
        print(f"{strategy:<10} {data['count']:<10} {data['avg_length']:<15.1f} {data['std_length']:<15.1f}")

    # 语义完整性评估
    print(f"\n语义完整性:")

    def check_semantic_integrity(chunks):
        """检查块的语义完整性"""
        issues = []
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue
            if chunk[0].islower() and i > 0:
                issues.append(f"块{i + 1}可能以句子中间开始")
            if not chunk[-1] in '.。!！?？\n':
                issues.append(f"块{i + 1}可能未完整结束")
        return issues

    for strategy, data in comparison_data.items():
        issues = check_semantic_integrity(data['chunks'][:5])
        print(f"{strategy}: {len(issues)}个问题" if issues else f"{strategy}: 完整性良好")

    print("\n✅ 练习1完成\n")

    return comparison_data


# ============================================================================
# 练习2：Chunk Size调优
# ============================================================================

def exercise_2_chunk_size_tuning():
    """
    练习2：Chunk Size调优
    测试不同chunk_size的效果
    """
    print("\n" + "=" * 80)
    print("练习2：Chunk Size调优")
    print("=" * 80)

    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # 加载测试文档（使用更长的文档）
    data_dir = "../data"
    test_file = os.path.join(data_dir, "doc1_ai_intro.txt")

    if os.path.exists(test_file):
        with open(test_file, 'r', encoding='utf-8') as f:
            test_document = f.read()
        print(f"\n加载文档: {test_file}")
    else:
        # 使用示例文档
        test_document = """
        人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，致力于创建能够模拟人类智能的系统。
        
        机器学习是人工智能的核心技术之一。通过让计算机从数据中学习规律，而不是显式编程，机器学习使得AI系统能够不断改进性能。
        
        深度学习是机器学习的一个子领域，使用多层神经网络来学习数据的层次化表示。深度学习在图像识别、语音识别等领域取得了突破性进展。
        
        自然语言处理（NLP）使计算机能够理解、解释和生成人类语言。现代NLP技术结合了深度学习和大规模预训练模型。
        
        计算机视觉让机器能够理解和分析视觉信息。从简单的图像分类到复杂的场景理解，计算机视觉技术正在快速发展。
        
        强化学习通过试错学习，使AI系统能够在环境中学习最优策略。AlphaGo就是强化学习的成功应用案例。
        """ * 10
        print(f"\n使用示例文档")

    print(f"文档长度: {len(test_document)} 字符\n")

    # 测试不同的chunk_size
    chunk_sizes = [200, 400, 600, 800, 1000]
    overlap_ratio = 0.1

    results = {}

    print("测试不同chunk_size:")

    for chunk_size in chunk_sizes:
        chunk_overlap = int(chunk_size * overlap_ratio)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", ". ", " ", ""]
        )

        chunks = splitter.split_text(test_document)
        chunk_lengths = [len(c) for c in chunks]

        results[chunk_size] = {
            'chunks': chunks,
            'count': len(chunks),
            'avg_length': np.mean(chunk_lengths),
            'std_length': np.std(chunk_lengths),
            'min_length': min(chunk_lengths),
            'max_length': max(chunk_lengths),
            'overlap': chunk_overlap
        }

        print(
            f"Size:{chunk_size} Count:{len(chunks)} Avg:{np.mean(chunk_lengths):.1f} Range:[{min(chunk_lengths)},{max(chunk_lengths)}]")

    # 分析结果
    print(f"\n详细对比:")
    print(f"{'Chunk Size':<12} {'块数量':<10} {'平均长度':<12} {'标准差':<12}")
    print("─" * 50)
    for size, data in results.items():
        print(f"{size:<12} {data['count']:<10} {data['avg_length']:<12.1f} {data['std_length']:<12.1f}")

    print("\n✅ 练习2完成\n")

    return results


# ============================================================================
# 练习3：多格式文档处理
# ============================================================================

def exercise_3_multi_format_processing():
    """
    练习3：多格式文档处理
    支持TXT、Markdown、PDF三种格式
    """
    print("\n" + "=" * 80)
    print("练习3：多格式文档处理")
    print("=" * 80)

    from langchain_community.document_loaders import (
        TextLoader,
        UnstructuredMarkdownLoader,
        PyPDFLoader
    )
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    class MultiFormatDocumentProcessor:
        """多格式文档处理器"""

        def __init__(self, chunk_size=500, chunk_overlap=50):
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", "。", ". ", " ", ""]
            )

        def load_txt(self, filepath: str) -> List[str]:
            """加载TXT文件"""
            try:
                loader = TextLoader(filepath, encoding='utf-8')
                documents = loader.load()
                return [doc.page_content for doc in documents]
            except Exception as e:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return [f.read()]

        def load_markdown(self, filepath: str) -> List[str]:
            """加载Markdown文件"""
            try:
                loader = UnstructuredMarkdownLoader(filepath)
                documents = loader.load()
                return [doc.page_content for doc in documents]
            except Exception as e:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return [f.read()]

        def load_pdf(self, filepath: str) -> List[str]:
            """加载PDF文件"""
            try:
                loader = PyPDFLoader(filepath)
                documents = loader.load()
                return [doc.page_content for doc in documents]
            except Exception as e:
                return []

        def process_document(self, filepath: str) -> Dict[str, Any]:
            """
            处理文档并返回标准化的分块结果
            
            Returns:
                包含原始文本、分块结果和元数据的字典
            """
            # 1. 根据文件扩展名选择加载器
            ext = os.path.splitext(filepath)[1].lower()

            if ext == '.txt':
                raw_texts = self.load_txt(filepath)
                doc_type = 'text'
            elif ext == '.md':
                raw_texts = self.load_markdown(filepath)
                doc_type = 'markdown'
            elif ext == '.pdf':
                raw_texts = self.load_pdf(filepath)
                doc_type = 'pdf'
            else:
                return None

            # 2. 合并所有文本
            full_text = "\n\n".join(raw_texts)

            # 3. 文本分块
            chunks = self.splitter.split_text(full_text)

            # 4. 构造标准化输出
            result = {
                'filepath': filepath,
                'filename': os.path.basename(filepath),
                'doc_type': doc_type,
                'raw_text': full_text,
                'chunks': chunks,
                'metadata': {
                    'total_chars': len(full_text),
                    'chunk_count': len(chunks),
                    'avg_chunk_length': np.mean([len(c) for c in chunks]),
                    'chunk_size_config': self.chunk_size,
                    'overlap_config': self.chunk_overlap,
                    'processed_at': datetime.now().isoformat()
                }
            }

            return result

        def batch_process(self, filepaths: List[str]) -> List[Dict[str, Any]]:
            """批量处理多个文档"""
            results = []
            for filepath in filepaths:
                if os.path.exists(filepath):
                    result = self.process_document(filepath)
                    if result:
                        results.append(result)
            return results

    # 使用示例
    print("\n初始化文档处理器")
    processor = MultiFormatDocumentProcessor(chunk_size=400, chunk_overlap=40)
    print(f"Chunk Size:{processor.chunk_size}, Overlap:{processor.chunk_overlap}")

    # 准备测试文件
    data_dir = "../data"
    test_files = []

    # TXT文件
    txt_files = [f for f in os.listdir(data_dir) if f.endswith('.txt')]
    if txt_files:
        test_files.append(os.path.join(data_dir, txt_files[0]))

    # Markdown文件（如果有）
    md_dir = "../lectures_md"
    md_files = [f for f in os.listdir(md_dir) if f.endswith('.md')]
    if md_files:
        test_files.append(os.path.join(md_dir, md_files[0]))

    if not test_files:
        print("\n⚠️  未找到测试文件，使用演示模式")
        # 创建临时测试文件
        import tempfile

        # 创建TXT测试文件
        txt_content = "这是一个TXT测试文件。\n\n它包含多个段落。\n\n每个段落都会被正确处理。"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(txt_content)
            test_files.append(f.name)

        # 创建Markdown测试文件
        md_content = "# 标题\n\n## 子标题\n\n这是Markdown内容。\n\n- 列表项1\n- 列表项2"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(md_content)
            test_files.append(f.name)

    print(f"\n批量处理 {len(test_files)} 个文档")

    results = processor.batch_process(test_files)

    # 汇总统计
    print(f"\n成功处理 {len(results)} 个文档")
    print(f"{'文件名':<30} {'类型':<10} {'字符数':<12} {'块数':<10}")
    print("─" * 65)
    for result in results:
        print(f"{result['filename']:<30} {result['doc_type']:<10} "
              f"{result['metadata']['total_chars']:<12} {result['metadata']['chunk_count']:<10}")

    # 展示第一个文档的分块示例
    if results:
        print(f"\n示例块(前3个):")
        for i, chunk in enumerate(results[0]['chunks'][:3], 1):
            preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
            print(f"{i}. {preview}")

    print("\n✅ 练习3完成\n")

    return results


# ============================================================================
# 练习4：元数据提取与管理
# ============================================================================

def exercise_4_metadata_extraction():
    """
    练习4：元数据提取与管理
    为文本块添加完整的元数据并保存为JSON
    """
    print("\n" + "=" * 80)
    print("练习4：元数据提取与管理")
    print("=" * 80)

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    import hashlib
    import re

    class MetadataExtractor:
        """元数据提取器"""

        def __init__(self):
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                length_function=len
            )

        def extract_keywords(self, text: str, top_k: int = 5) -> List[str]:
            """
            简单的关键词提取（基于词频）
            实际应用可使用TF-IDF或更复杂的NLP方法
            """
            # 简单分词（中文按字符，英文按单词）
            words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text.lower())

            # 过滤停用词（简化版）
            stop_words = {'的', '是', '在', '了', '和', '有', '我', '你', '他',
                          'the', 'is', 'in', 'and', 'of', 'to', 'a', 'it'}
            words = [w for w in words if w not in stop_words and len(w) > 1]

            # 统计词频
            from collections import Counter
            word_freq = Counter(words)

            # 返回top-k
            return [word for word, _ in word_freq.most_common(top_k)]

        def detect_language(self, text: str) -> str:
            """检测文本语言"""
            # 简单判断：统计中文字符比例
            chinese_chars = re.findall(r'[\u4e00-\u9fa5]', text)
            if len(chinese_chars) / max(len(text), 1) > 0.3:
                return 'zh'
            return 'en'

        def generate_chunk_id(self, doc_id: str, chunk_index: int) -> str:
            """生成块的唯一ID"""
            return f"{doc_id}_chunk_{chunk_index:04d}"

        def generate_doc_id(self, filepath: str) -> str:
            """生成文档ID（基于文件路径的哈希）"""
            hash_obj = hashlib.md5(filepath.encode())
            return f"doc_{hash_obj.hexdigest()[:12]}"

        def extract_file_metadata(self, filepath: str) -> Dict[str, Any]:
            """提取文件级元数据"""
            stat = os.stat(filepath)

            return {
                'doc_id': self.generate_doc_id(filepath),
                'title': os.path.splitext(os.path.basename(filepath))[0],
                'source': filepath,
                'filename': os.path.basename(filepath),
                'file_size': stat.st_size,
                'doc_type': os.path.splitext(filepath)[1][1:],
                'created_date': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified_date': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'language': None,
            }

        def process_document_with_metadata(self, filepath: str) -> List[Dict[str, Any]]:
            """处理文档并为每个块提取完整的元数据"""

            # 1. 提取文档级元数据
            doc_metadata = self.extract_file_metadata(filepath)

            # 2. 读取文档内容
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 检测语言
            doc_metadata['language'] = self.detect_language(content)

            # 3. 文本分块
            chunks = self.splitter.split_text(content)

            # 4. 为每个块构建完整的元数据
            chunks_with_metadata = []

            for i, chunk_text in enumerate(chunks):
                # 生成块ID
                chunk_id = self.generate_chunk_id(doc_metadata['doc_id'], i)

                # 提取关键词
                keywords = self.extract_keywords(chunk_text)

                # 构建完整的元数据结构
                chunk_with_meta = {
                    'chunk_id': chunk_id,
                    'content': chunk_text,

                    # 文档级元数据
                    'document_metadata': {
                        'doc_id': doc_metadata['doc_id'],
                        'title': doc_metadata['title'],
                        'source': doc_metadata['source'],
                        'filename': doc_metadata['filename'],
                        'doc_type': doc_metadata['doc_type'],
                        'language': doc_metadata['language'],
                        'created_date': doc_metadata['created_date'],
                        'modified_date': doc_metadata['modified_date'],
                    },

                    # 块级元数据
                    'chunk_metadata': {
                        'chunk_index': i,
                        'char_count': len(chunk_text),
                        'token_count': len(chunk_text.split()),  # 简化估算
                        'chunk_position': f"{i + 1}/{len(chunks)}",
                    },

                    # 内容级元数据
                    'content_metadata': {
                        'keywords': keywords,
                        'has_numbers': bool(re.search(r'\d', chunk_text)),
                        'has_url': bool(re.search(r'http[s]?://', chunk_text)),
                        'has_email': bool(
                            re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', chunk_text)),
                    },

                    # 技术元数据
                    'technical_metadata': {
                        'extracted_at': datetime.now().isoformat(),
                        'extractor_version': '1.0',
                        'chunk_size_config': self.splitter._chunk_size,
                        'overlap_config': self.splitter._chunk_overlap,
                    }
                }

                chunks_with_metadata.append(chunk_with_meta)

            return chunks_with_metadata

    # 使用示例
    print("\n初始化元数据提取器")
    extractor = MetadataExtractor()

    # 处理测试文件
    data_dir = "../data"
    test_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir)
                  if f.endswith('.txt')][:2]

    if not test_files:
        return None

    print(f"\n处理 {len(test_files)} 个文档")
    all_chunks = []

    for filepath in test_files:
        if os.path.exists(filepath):
            chunks = extractor.process_document_with_metadata(filepath)
            all_chunks.extend(chunks)

    print(f"\n提取 {len(all_chunks)} 个文本块（含元数据）")

    # 展示元数据结构示例
    if all_chunks:
        example = all_chunks[0]
        print(f"\n元数据示例(Chunk ID: {example['chunk_id']}):")
        print(json.dumps({
            'chunk_id': example['chunk_id'],
            'content': example['content'][:50] + "...",
            'document_metadata': example['document_metadata'],
            'chunk_metadata': example['chunk_metadata'],
            'content_metadata': example['content_metadata'],
            'technical_metadata': example['technical_metadata']
        }, indent=2, ensure_ascii=False))

    # 保存为JSON文件
    output_dir = "../file"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "chunks_with_metadata.json")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"\n保存到: {output_file}")
    print(f"文件大小: {os.path.getsize(output_file) / 1024:.1f} KB")

    print("\n✅ 练习4完成\n")

    return all_chunks


# ============================================================================
# 练习5：分块质量评估
# ============================================================================

def exercise_5_chunking_quality_evaluation():
    """
    练习5：分块质量评估
    自动检测文本块的质量并生成评估报告
    """
    print("\n" + "=" * 80)
    print("练习5：分块质量评估")
    print("=" * 80)

    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from pymilvus import MilvusClient, DataType
    from http import HTTPStatus
    import dashscope
    import re

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

    class ChunkQualityEvaluator:
        """分块质量评估器（使用Milvus计算向量相似度）"""

        def __init__(self, use_milvus=True, milvus_uri="http://211.65.101.204:19530"):
            self.use_milvus = use_milvus
            self.milvus_uri = milvus_uri
            self.dimension = 1024

            if use_milvus:
                self.milvus_client = MilvusClient(uri=milvus_uri)
                self.collection_name = "chunk_quality_eval"

        def _create_milvus_collection(self):
            """创建临时Milvus集合用于相似度计算"""
            # 删除旧集合
            if self.collection_name in self.milvus_client.list_collections():
                self.milvus_client.drop_collection(self.collection_name)

            # 创建schema
            schema = self.milvus_client.create_schema(
                auto_id=True,
                description="文本块质量评估临时集合"
            )

            schema.add_field("id", DataType.INT64, is_primary=True)
            schema.add_field("vector", DataType.FLOAT_VECTOR, dim=self.dimension)
            schema.add_field("chunk_index", DataType.INT64)

            # 创建集合
            self.milvus_client.create_collection(
                collection_name=self.collection_name,
                schema=schema
            )

            # 创建索引（使用HNSW + COSINE）
            index_params = self.milvus_client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_type="HNSW",
                metric_type="COSINE",
                params={"M": 16, "efConstruction": 200}
            )
            self.milvus_client.create_index(
                collection_name=self.collection_name,
                index_params=index_params
            )

        def _insert_chunks_to_milvus(self, chunks: List[str]):
            """将chunks向量化并插入Milvus"""
            data_to_insert = []

            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue

                # 获取向量
                vector = get_text_embedding(chunk, dimension=self.dimension)

                data_to_insert.append({
                    'vector': vector,
                    'chunk_index': i
                })

            # 批量插入
            if data_to_insert:
                self.milvus_client.insert(
                    collection_name=self.collection_name,
                    data=data_to_insert
                )

        def _calculate_similarity_using_milvus(self, chunk_index1: int, chunk_index2: int) -> float:
            """使用Milvus计算两个chunk的相似度"""
            # 加载集合
            self.milvus_client.load_collection(self.collection_name)

            # 查询chunk1的向量
            results1 = self.milvus_client.query(
                collection_name=self.collection_name,
                filter=f'chunk_index == {chunk_index1}',
                output_fields=["vector"]
            )

            if not results1:
                return 0.0

            vector1 = results1[0]['vector']

            # 使用chunk1的向量搜索，找到chunk2的相似度
            search_results = self.milvus_client.search(
                collection_name=self.collection_name,
                data=[vector1],
                anns_field="vector",
                search_params={"metric_type": "COSINE", "params": {"ef": 100}},
                limit=100,
                output_fields=["chunk_index"]
            )

            # 找到chunk2的相似度
            for result in search_results[0]:
                if result['entity']['chunk_index'] == chunk_index2:
                    return result['distance']  # COSINE相似度

            return 0.0

        def evaluate_semantic_integrity(self, chunks: List[str]) -> Dict[str, Any]:
            """
            评估语义完整性
            
            检查项：
            - 基于规则的检查（标点、代词等）
            - 基于Milvus的相邻块语义连贯性检查
            """
            issues = []
            scores = []

            # 如果使用Milvus，先创建集合并插入数据
            if self.use_milvus and len(chunks) > 1:
                print("    • 使用Milvus计算语义连贯性...")
                self._create_milvus_collection()
                self._insert_chunks_to_milvus(chunks)

            for i, chunk in enumerate(chunks):
                chunk = chunk.strip()
                if not chunk:
                    continue

                score = 100  # 满分100
                chunk_issues = []

                # 检查1：是否以小写字母开始（可能表示不完整）
                if i > 0 and chunk[0].islower():
                    score -= 15
                    chunk_issues.append("以小写字母开始")

                # 检查2：是否以完整句子结束
                if not chunk[-1] in '.。!！?？\n':
                    score -= 10
                    chunk_issues.append("未以标点符号结束")

                # 检查3：开头是否有孤立的指代词
                pronouns = ['它', '他', '她', '这', '那', '其', 'it', 'this', 'that', 'they']
                first_words = chunk[:20].lower()
                for pronoun in pronouns:
                    if first_words.startswith(pronoun):
                        score -= 20
                        chunk_issues.append(f"开头有指代词: {pronoun}")
                        break

                # 检查4：长度是否合理（太短可能不完整）
                if len(chunk) < 50:
                    score -= 10
                    chunk_issues.append("内容过短")

                # 检查5：使用Milvus计算与前一个chunk的语义连贯性
                if self.use_milvus and i > 0:
                    try:
                        similarity = self._calculate_similarity_using_milvus(i - 1, i)

                        # 相邻chunk的语义相似度应该在合理范围内
                        # 太低（<0.3）可能表示主题跳跃太大
                        # 太高（>0.95）可能表示重复内容
                        if similarity < 0.3:
                            score -= 15
                            chunk_issues.append(f"与前块语义连贯性低 (相似度: {similarity:.3f})")
                        elif similarity > 0.95:
                            score -= 10
                            chunk_issues.append(f"与前块内容高度重复 (相似度: {similarity:.3f})")
                    except Exception as e:
                        # Milvus计算失败时不影响其他检查
                        pass

                scores.append(score)
                if chunk_issues:
                    issues.append({
                        'chunk_index': i,
                        'score': score,
                        'issues': chunk_issues,
                        'preview': chunk[:50] + "..."
                    })

            # 清理临时集合
            if self.use_milvus and hasattr(self, 'milvus_client'):
                try:
                    if self.collection_name in self.milvus_client.list_collections():
                        self.milvus_client.drop_collection(self.collection_name)
                except:
                    pass

            return {
                'avg_score': np.mean(scores) if scores else 0,
                'min_score': min(scores) if scores else 0,
                'max_score': max(scores) if scores else 0,
                'issues_count': len(issues),
                'issues': issues[:10],  # 只保留前10个问题
                'total_chunks': len(chunks),
                'used_milvus': self.use_milvus
            }

        def evaluate_size_distribution(self, chunks: List[str]) -> Dict[str, Any]:
            """
            评估大小分布
            
            检查项：
            - 平均长度
            - 标准差（越小越均匀）
            - 长度分布
            """
            lengths = [len(c) for c in chunks if c.strip()]

            if not lengths:
                return {'error': '没有有效的块'}

            avg_length = np.mean(lengths)
            std_length = np.std(lengths)

            # 计算变异系数（标准差/平均值）
            cv = std_length / avg_length if avg_length > 0 else 0

            # 评分：变异系数越小越好
            # 理想情况：cv < 0.2 (优秀)
            # cv 0.2-0.4 (良好)
            # cv 0.4-0.6 (一般)
            # cv > 0.6 (较差)
            if cv < 0.2:
                score = 100
                grade = "优秀"
            elif cv < 0.4:
                score = 80
                grade = "良好"
            elif cv < 0.6:
                score = 60
                grade = "一般"
            else:
                score = 40
                grade = "较差"

            return {
                'avg_length': avg_length,
                'std_length': std_length,
                'min_length': min(lengths),
                'max_length': max(lengths),
                'coefficient_of_variation': cv,
                'score': score,
                'grade': grade,
                'distribution': {
                    '0-200': sum(1 for l in lengths if l < 200),
                    '200-400': sum(1 for l in lengths if 200 <= l < 400),
                    '400-600': sum(1 for l in lengths if 400 <= l < 600),
                    '600-800': sum(1 for l in lengths if 600 <= l < 800),
                    '800+': sum(1 for l in lengths if l >= 800),
                }
            }

        def evaluate_overlap_effect(self, chunks: List[str], chunk_overlap: int) -> Dict[str, Any]:
            """
            评估overlap效果
            
            检查实际overlap与配置是否一致
            """
            if len(chunks) < 2:
                return {'message': '块数量太少，无法评估overlap'}

            actual_overlaps = []

            for i in range(len(chunks) - 1):
                chunk1 = chunks[i]
                chunk2 = chunks[i + 1]

                # 查找重叠部分（简化版：比较后缀和前缀）
                max_overlap = min(len(chunk1), len(chunk2), chunk_overlap * 2)

                for length in range(max_overlap, 0, -1):
                    if chunk1[-length:] == chunk2[:length]:
                        actual_overlaps.append(length)
                        break
                else:
                    actual_overlaps.append(0)

            if not actual_overlaps:
                return {'message': '无overlap数据'}

            avg_overlap = np.mean(actual_overlaps)

            # 评分：实际overlap应接近配置值
            if chunk_overlap == 0:
                score = 100 if avg_overlap == 0 else 80
            else:
                ratio = avg_overlap / chunk_overlap
                if 0.8 <= ratio <= 1.2:
                    score = 100
                elif 0.6 <= ratio <= 1.4:
                    score = 80
                else:
                    score = 60

            return {
                'configured_overlap': chunk_overlap,
                'avg_actual_overlap': avg_overlap,
                'min_actual_overlap': min(actual_overlaps),
                'max_actual_overlap': max(actual_overlaps),
                'score': score,
                'consistency': 'good' if score >= 80 else 'needs_improvement'
            }

        def generate_evaluation_report(self,
                                       chunks: List[str],
                                       chunk_size: int,
                                       chunk_overlap: int) -> Dict[str, Any]:
            """生成完整的评估报告"""

            # 1. 语义完整性评估
            semantic_eval = self.evaluate_semantic_integrity(chunks)

            # 2. 大小分布评估
            size_eval = self.evaluate_size_distribution(chunks)

            # 3. Overlap效果评估
            overlap_eval = self.evaluate_overlap_effect(chunks, chunk_overlap)

            # 4. 计算总体评分
            total_score = (
                    semantic_eval['avg_score'] * 0.4 +  # 语义完整性权重40%
                    size_eval['score'] * 0.35 +  # 大小分布权重35%
                    overlap_eval.get('score', 80) * 0.25  # overlap效果权重25%
            )

            # 5. 生成优化建议
            recommendations = self._generate_recommendations(
                semantic_eval, size_eval, overlap_eval,
                chunk_size, chunk_overlap
            )

            return {
                'summary': {
                    'total_score': total_score,
                    'grade': self._score_to_grade(total_score),
                    'total_chunks': len(chunks),
                    'chunk_size_config': chunk_size,
                    'overlap_config': chunk_overlap,
                },
                'semantic_integrity': semantic_eval,
                'size_distribution': size_eval,
                'overlap_effect': overlap_eval,
                'recommendations': recommendations,
                'evaluated_at': datetime.now().isoformat()
            }

        def _score_to_grade(self, score: float) -> str:
            """分数转等级"""
            if score >= 90:
                return "A (优秀)"
            elif score >= 80:
                return "B (良好)"
            elif score >= 70:
                return "C (中等)"
            elif score >= 60:
                return "D (及格)"
            else:
                return "F (需改进)"

        def _generate_recommendations(self, semantic_eval, size_eval,
                                      overlap_eval, chunk_size, chunk_overlap):
            """生成优化建议"""
            recommendations = []

            # 语义完整性建议
            if semantic_eval['avg_score'] < 80:
                recommendations.append({
                    'category': '语义完整性',
                    'issue': f"发现 {semantic_eval['issues_count']} 个语义完整性问题",
                    'suggestion': "考虑增加chunk_overlap或调整separator优先级"
                })

            # 大小分布建议
            if size_eval['grade'] in ['一般', '较差']:
                recommendations.append({
                    'category': '大小分布',
                    'issue': f"块大小分布不均匀（变异系数: {size_eval['coefficient_of_variation']:.2f}）",
                    'suggestion': f"当前chunk_size={chunk_size}，考虑调整到 {int(size_eval['avg_length'])} 左右"
                })

            # Overlap建议
            if overlap_eval.get('consistency') == 'needs_improvement':
                recommendations.append({
                    'category': 'Overlap效果',
                    'issue': "实际overlap与配置不一致",
                    'suggestion': f"考虑调整overlap从 {chunk_overlap} 到 {int(overlap_eval.get('avg_actual_overlap', chunk_overlap))}"
                })

            # 通用建议
            if not recommendations:
                recommendations.append({
                    'category': '总体',
                    'issue': '无',
                    'suggestion': '当前配置良好，建议通过实际检索测试进一步验证'
                })

            return recommendations

    # 使用示例
    print("\n【准备测试数据】")

    # 加载测试文档
    data_dir = "../data"
    test_file = os.path.join(data_dir, "doc1_ai_intro.txt")

    if os.path.exists(test_file):
        with open(test_file, 'r', encoding='utf-8') as f:
            test_document = f.read()
        print(f"✓ 加载文档: {os.path.basename(test_file)}")
    else:
        test_document = """
        人工智能是计算机科学的一个分支。它致力于创建能够模拟人类智能的系统。
        
        机器学习是人工智能的核心技术。通过让计算机从数据中学习规律，机器学习使得AI系统能够不断改进。
        
        深度学习使用多层神经网络。它在图像识别、语音识别等领域取得了突破性进展。
        """ * 20
        print("✓ 使用示例文档")

    print(f"✓ 文档长度: {len(test_document)} 字符")

    # 测试不同配置
    configs = [
        {'chunk_size': 400, 'chunk_overlap': 40},
        {'chunk_size': 600, 'chunk_overlap': 60},
        {'chunk_size': 400, 'chunk_overlap': 0},  # 无overlap
    ]

    evaluator = ChunkQualityEvaluator(
        use_milvus=True,
        milvus_uri="http://211.65.101.204:19530"
    )

    print("\n评估不同配置:")

    all_reports = []

    for config in configs:
        print(f"\nConfig: size={config['chunk_size']}, overlap={config['chunk_overlap']}")

        # 分块
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=config['chunk_size'],
            chunk_overlap=config['chunk_overlap'],
            length_function=len,
            separators=["\n\n", "\n", "。", ". ", " ", ""]
        )
        chunks = splitter.split_text(test_document)

        # 评估
        report = evaluator.generate_evaluation_report(
            chunks,
            config['chunk_size'],
            config['chunk_overlap']
        )

        all_reports.append({
            'config': config,
            'report': report
        })

        # 显示评估结果
        print(
            f"总分:{report['summary']['total_score']:.1f} 语义:{report['semantic_integrity']['avg_score']:.1f} 大小:{report['size_distribution']['score']:.1f}")

    # 对比分析
    print(f"\n配置对比:")
    print(f"{'配置':<25} {'总分':<10} {'语义':<10} {'大小':<10}")
    print("─" * 60)
    for item in all_reports:
        config_str = f"size={item['config']['chunk_size']},ovlp={item['config']['chunk_overlap']}"
        report = item['report']
        print(f"{config_str:<25} "
              f"{report['summary']['total_score']:<10.1f} "
              f"{report['semantic_integrity']['avg_score']:<10.1f} "
              f"{report['size_distribution']['score']:<10.1f}")

    # 推荐最佳配置
    best_config = max(all_reports, key=lambda x: x['report']['summary']['total_score'])
    print(
        f"\n推荐: size={best_config['config']['chunk_size']}, overlap={best_config['config']['chunk_overlap']} (总分:{best_config['report']['summary']['total_score']:.1f})")

    # 保存评估报告
    output_file = "../file/chunking_evaluation_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_reports, f, indent=2, ensure_ascii=False)

    print(f"\n保存评估报告到: {output_file}")

    print("\n✅ 练习5完成\n")

    return all_reports


# ============================================================================
# 主程序
# ============================================================================

def main():
    """主程序：依次运行所有练习"""
    print("\n文档处理与分块 - 实践练习\n")

    try:
        exercise_1_chunking_strategies_comparison()
        exercise_2_chunk_size_tuning()
        exercise_3_multi_format_processing()
        exercise_4_metadata_extraction()
        exercise_5_chunking_quality_evaluation()

        print("=" * 80)
        print("🎉 所有练习完成")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
    # from langchain_community.document_loaders import TextLoader,CSVLoader,PyPDFLoader,UnstructuredMarkdownLoader
    # from langchain_text_splitters import RecursiveCharacterTextSplitter

    # txt格式文档的加载
    # text_loader = TextLoader("../data/doc1_ai_intro.txt")
    # doc_loader = text_loader.load()
    # print(doc_loader)
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=100,
    #                                                chunk_overlap=50,
    #                                                length_function=len)
    # text_splitter = text_splitter.split_documents(doc_loader)
    # print(text_splitter)

    # 表格文档格式的加载
    # csv_loader = CSVLoader("../data/体育商品数据.csv")
    # csv_loader = csv_loader.load()
    # print(csv_loader)



