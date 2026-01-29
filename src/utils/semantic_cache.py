"""语义缓存工具 - 基于 ChromaDB 和向量嵌入实现模糊匹配缓存"""

import os
from typing import Dict, Any, List, Optional, Union
import json

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

from src.utils.logger import logger
from config import settings


class SemanticCacheManager:
    """语义缓存管理器
    
    用于存储和检索具有相似含义的工具执行结果。
    """
    
    def __init__(self, persist_directory: str = "./.chroma_cache"):
        self.enabled = CHROMA_AVAILABLE
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None
        self._embedding_fn = None
        self._initialized = False

    def _lazy_init(self):
        """延迟初始化，避免启动时因网络问题崩溃"""
        if self._initialized or not self.enabled:
            return
            
        try:
            import chromadb
            from chromadb.utils import embedding_functions
            
            logger.info("Initializing semantic cache (lazy)...")
            self._client = chromadb.PersistentClient(path=self.persist_directory)
            
            # 使用默认的 embedding 函数 (可能会下载模型)
            self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            
            self._collection = self._client.get_or_create_collection(
                name="tool_results",
                embedding_function=self._embedding_fn
            )
            self._initialized = True
            logger.info("Semantic cache initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize semantic cache: {e}. Disabling for this session.")
            self.enabled = False
            self._initialized = True

    def get(self, tool_name: str, query: str, threshold: float = 0.3) -> Optional[str]:
        """检索语义相似的缓存结果
        
        Args:
            tool_name: 工具名称
            query: 查询内容
            threshold: 距离阈值 (越小越相似)
            
        Returns:
            缓存的内容或 None
        """
        if not self.enabled:
            return None
        
        if not self._initialized:
            self._lazy_init()
            if not self.enabled: return None
            
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=1,
                where={"tool": tool_name}
            )
            
            if results["documents"] and results["documents"][0] and results["distances"][0][0] < threshold:
                logger.info(f"Semantic cache hit for [{tool_name}]: {query} (dist: {results['distances'][0][0]:.4f})")
                return results["documents"][0][0]
                
        except Exception as e:
            logger.error(f"Semantic cache retrieval failed: {e}")
            
        return None

    def set(self, tool_name: str, query: str, content: str):
        """存储结果到语义缓存"""
        if not self.enabled:
            return
            
        if not self._initialized:
            self._lazy_init()
            if not self.enabled: return
            
        try:
            # 使用 query 的哈希或简单唯一 ID
            import hashlib
            doc_id = hashlib.md5(f"{tool_name}:{query}".encode()).hexdigest()
            
            self._collection.upsert(
                ids=[doc_id],
                documents=[content],
                metadatas=[{"tool": tool_name, "query": query}]
            )
        except Exception as e:
            logger.error(f"Semantic cache storage failed: {e}")

# 全局单例
semantic_cache = SemanticCacheManager()
