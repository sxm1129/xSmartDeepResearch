"""健康检查工具函数"""

import os
import shutil
import pymysql
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from dotenv import load_dotenv

from src.utils.logger import logger

load_dotenv()


async def check_mysql_connection() -> Dict[str, Any]:
    """
    检查 MySQL 数据库连接
    
    Returns:
        ComponentHealth: 数据库连接状态
    """
    try:
        # 获取数据库配置
        host = os.getenv("DB_HOST", "localhost")
        port = int(os.getenv("DB_PORT", 3306))
        user = os.getenv("DB_USER", "root")
        password = os.getenv("DB_PASSWORD", "")
        db_name = os.getenv("DB_NAME", "xsmartdeepresearch")
        
        # 尝试连接
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            connect_timeout=5
        )
        
        # 执行简单查询验证
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            "result": "succeed",
            "message": "MySQL connection OK",
            "details": {"host": host, "database": db_name}
        }
        
    except Exception as e:
        logger.error(f"MySQL health check failed: {e}")
        return {
            "result": "fail",
            "message": f"MySQL connection failed: {str(e)}"
        }


async def check_disk_space(threshold: float = 0.1) -> Dict[str, Any]:
    """
    检查磁盘空间
    
    Args:
        threshold: 最小剩余空间比例 (默认 10%)
        
    Returns:
        ComponentHealth: 磁盘空间状态
    """
    try:
        # 获取根目录磁盘使用情况
        total, used, free = shutil.disk_usage("/")
        
        # 计算使用率和剩余空间
        free_ratio = free / total
        usage_percent = (used / total) * 100
        free_gb = free // (2**30)  # 转换为 GB
        total_gb = total // (2**30)
        
        # 判断是否满足阈值
        is_ok = free_ratio > threshold
        
        return {
            "result": "succeed" if is_ok else "fail",
            "message": f"Disk space {'OK' if is_ok else 'LOW'}",
            "details": {
                "free_gb": f"{free_gb}GB",
                "total_gb": f"{total_gb}GB",
                "usage_percent": f"{usage_percent:.1f}%",
                "free_ratio": f"{free_ratio:.2%}"
            }
        }
        
    except Exception as e:
        logger.error(f"Disk space check failed: {e}")
        return {
            "result": "fail",
            "message": f"Disk check failed: {str(e)}"
        }


async def check_redis_connection() -> Optional[Dict[str, Any]]:
    """
    检查 Redis 连接 (如果配置了)
    
    Returns:
        Optional[ComponentHealth]: Redis 连接状态,如果未配置则返回 None
    """
    redis_url = os.getenv("REDIS_URL", "")
    
    # 如果没有配置 Redis,返回 None
    if not redis_url or redis_url == "redis://localhost:6379":
        # 默认值视为未配置
        return None
    
    try:
        import redis.asyncio as redis
        
        # 解析 Redis URL 并连接
        client = redis.from_url(redis_url, socket_connect_timeout=5)
        
        # 执行 PING 测试
        await client.ping()
        await client.close()
        
        return {
            "result": "succeed",
            "message": "Redis connection OK",
            "details": {"url": redis_url.split("@")[-1]}  # 隐藏密码
        }
        
    except ImportError:
        # Redis 库未安装
        logger.warning("Redis library not installed, skipping Redis check")
        return None
        
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "result": "fail",
            "message": f"Redis connection failed: {str(e)}"
        }


def get_current_timestamp() -> str:
    """
    获取当前时间的 ISO 8601 格式字符串
    
    Returns:
        str: ISO 8601 格式的时间戳
    """
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
