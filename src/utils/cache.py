"""Redis 缓存管理器"""

import json
import hashlib
from typing import Any, Optional, Union
import pickle

import redis
from config import settings


class CacheManager:
    """Redis 缓存管理器
    
    用于在多轮研究过程中缓存工具调用结果，减少 API 消耗并提高性能。
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                cls._instance.redis_client = redis.from_url(settings.redis_url)
                # 测试连接
                cls._instance.redis_client.ping()
                cls._instance.enabled = True
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}. Caching disabled.")
                cls._instance.enabled = False
        return cls._instance
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """生成唯一的缓存键"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        hash_str = hashlib.md5(data_str.encode()).hexdigest()
        return f"xsmart:{prefix}:{hash_str}"
    
    def get(self, prefix: str, key_data: Any) -> Optional[Any]:
        """获取缓存"""
        if not self.enabled:
            return None
        
        try:
            key = self._generate_key(prefix, key_data)
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    def set(self, prefix: str, key_data: Any, value: Any, expire_seconds: int = None) -> bool:
        """设置缓存"""
        if not self.enabled:
            return False
        
        try:
            key = self._generate_key(prefix, key_data)
            data = pickle.dumps(value)
            return self.redis_client.set(key, data, ex=expire_seconds)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, prefix: str, key_data: Any) -> bool:
        """删除缓存"""
        if not self.enabled:
            return False
        
        try:
            key = self._generate_key(prefix, key_data)
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False


# 全局缓存实例
cache_manager = CacheManager()
