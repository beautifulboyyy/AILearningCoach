"""
BM25关键词检索模块
"""
from typing import List, Dict, Any
import math
from collections import Counter
import re


class BM25:
    """BM25算法实现"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化BM25
        
        Args:
            k1: 词频饱和参数（通常1.2-2.0）
            b: 长度归一化参数（0-1之间）
        """
        self.k1 = k1
        self.b = b
        self.corpus = []
        self.corpus_size = 0
        self.avgdl = 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
    
    def tokenize(self, text: str) -> List[str]:
        """
        分词（简化版本）
        
        Args:
            text: 输入文本
        
        Returns:
            词列表
        """
        # 简化的中文分词：按字符分割，保留2-4个字的词
        # 实际生产环境应使用jieba等专业分词工具
        text = text.lower()
        # 移除标点符号
        text = re.sub(r'[^\w\s]', ' ', text)
        # 分割成词
        words = text.split()
        return words
    
    def build_index(self, documents: List[str]):
        """
        构建BM25索引
        
        Args:
            documents: 文档列表
        """
        self.corpus = documents
        self.corpus_size = len(documents)
        
        # 计算文档长度和平均文档长度
        self.doc_len = [len(self.tokenize(doc)) for doc in documents]
        self.avgdl = sum(self.doc_len) / self.corpus_size if self.corpus_size > 0 else 0
        
        # 计算文档频率
        df = {}
        for doc in documents:
            tokens = set(self.tokenize(doc))
            for token in tokens:
                df[token] = df.get(token, 0) + 1
        
        # 计算IDF
        self.idf = {}
        for token, freq in df.items():
            self.idf[token] = math.log((self.corpus_size - freq + 0.5) / (freq + 0.5) + 1.0)
    
    def get_scores(self, query: str) -> List[float]:
        """
        计算查询与所有文档的BM25分数
        
        Args:
            query: 查询文本
        
        Returns:
            分数列表
        """
        query_tokens = self.tokenize(query)
        scores = []
        
        for i, doc in enumerate(self.corpus):
            doc_tokens = self.tokenize(doc)
            doc_token_counts = Counter(doc_tokens)
            
            score = 0.0
            for token in query_tokens:
                if token not in doc_token_counts:
                    continue
                
                # 词频
                tf = doc_token_counts[token]
                
                # IDF
                idf = self.idf.get(token, 0)
                
                # 文档长度归一化
                doc_length = self.doc_len[i]
                norm_factor = (1 - self.b) + self.b * (doc_length / self.avgdl)
                
                # BM25分数
                token_score = idf * (tf * (self.k1 + 1)) / (tf + self.k1 * norm_factor)
                score += token_score
            
            scores.append(score)
        
        return scores
    
    def search(self, query: str, top_k: int = 5) -> List[int]:
        """
        搜索最相关的文档
        
        Args:
            query: 查询文本
            top_k: 返回数量
        
        Returns:
            文档索引列表
        """
        scores = self.get_scores(query)
        
        # 获取Top-K索引
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]
        
        return top_indices
