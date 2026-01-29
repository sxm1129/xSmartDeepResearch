"""统一日志管理工具"""

import logging
import sys
from typing import Optional

# 配置日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"

def setup_logger(name: str = "xSmartDeepResearch", level: int = logging.INFO) -> logging.Logger:
    """初始化并配置日志对象"""
    logger = logging.getLogger(name)
    
    # 如果已经配置过处理器，则直接返回
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # 格式化器
    try:
        from rich.logging import RichHandler
        handler = RichHandler(rich_tracebacks=True, markup=True)
    except ImportError:
        handler = console_handler
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        
    logger.addHandler(handler)
    
    # 避免日志向上传递到根日志记录器（如果需要的话）
    logger.propagate = False
    
    return logger

# 创建全局默认日志对象
logger = setup_logger()
