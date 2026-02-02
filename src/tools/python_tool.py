"""Python 代码执行工具 - 沙箱化代码执行"""

import re
import random
import time
import os
import signal
from typing import Dict, Any, List, Optional, Union

from .base_tool import BaseTool
from config import settings
from src.utils.logger import logger


def _run_with_limits_worker(code, queue, timeout):
    """Worker function for local execution (global scope for pickling)"""
    import sys
    from io import StringIO
    import resource
    try:
        # CPU 时间 (秒)
        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
        # 地址空间 (字节)
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    except Exception as e:
        logger.warning(f"Failed to set resource limits: {e}")

    # 捕获输出
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    
    try:
        exec_globals = {"__builtins__": __builtins__}
        exec(code, exec_globals)
        stdout_val = sys.stdout.getvalue()
        stderr_val = sys.stderr.getvalue()
        queue.put((stdout_val, stderr_val, None))
    except Exception as e:
        queue.put(("", "", str(e)))
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


class PythonInterpreterTool(BaseTool):
    """Python 代码执行工具
    
    在沙箱环境中执行 Python 代码，支持负载均衡
    """
    
    name = "PythonInterpreter"
    description = """Executes Python code in a sandboxed environment. To use this tool, you must follow this format:
1. The 'arguments' JSON object must be empty: {}.
2. The Python code to be executed must be placed immediately after the JSON block, enclosed within <code> and </code> tags.

IMPORTANT: Any output you want to see MUST be printed to standard output using the print() function.

Example of a correct call:
<tool_call>
{"name": "PythonInterpreter", "arguments": {}}
<code>
import numpy as np
# Your code here
print(f"The result is: {np.mean([1,2,3])}")
</code>
</tool_call>"""
    
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    def __init__(
        self, 
        sandbox_endpoints: List[str] = None,
        timeout: int = 50,
        max_retries: int = 5,
        cfg: Optional[Dict] = None
    ):
        """初始化 Python 执行工具
        
        Args:
            sandbox_endpoints: 沙箱服务端点列表
            timeout: 执行超时时间（秒）
            max_retries: 最大重试次数
            cfg: 配置字典
        """
        super().__init__(cfg)
        self.endpoints = sandbox_endpoints or self.cfg.get("sandbox_endpoints", [])
        self.timeout = timeout
        self.max_retries = max_retries
    
    async def call(self, params: Union[str, Dict[str, Any]], **kwargs) -> str:
        """异步执行 Python 代码
        
        Args:
            params: 代码字符串或包含代码的参数
            
        Returns:
            执行结果
        """
        # 提取代码
        code = self._extract_code(params)
        
        if not code or not code.strip():
            return "[Python Interpreter Error]: Empty code."
        
        if not self.endpoints:
            if not settings.allow_local_python:
                return "[Python Interpreter Error]: Sandbox endpoints not configured and local execution is disabled for security."
            return self._local_execute(code)
        
        # 使用沙箱执行
        return self._sandbox_execute(code)
    
    def _extract_code(self, params: Union[str, Dict[str, Any]]) -> str:
        """从参数中提取代码
        
        Args:
            params: 代码字符串或参数字典
            
        Returns:
            提取的代码
        """
        if isinstance(params, str):
            # 尝试从 <code></code> 标签中提取
            code_match = re.search(r'<code>(.*?)</code>', params, re.DOTALL)
            if code_match:
                return code_match.group(1).strip()
            
            # 尝试从 ``` 代码块中提取
            triple_match = re.search(r'```[^\n]*\n(.+?)```', params, re.DOTALL)
            if triple_match:
                return triple_match.group(1).strip()
            
            return params
        
        # 从字典中提取
        if isinstance(params, dict):
            code = params.get("code", "")
            if code:
                return self._extract_code(code)
            
            raw = params.get("raw", "")
            if raw:
                return self._extract_code(raw)
        
        return ""
    
    def _sandbox_execute(self, code: str) -> str:
        """在沙箱中执行代码
        
        Args:
            code: Python 代码
            
        Returns:
            执行结果
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # 随机选择端点进行负载均衡
                endpoint = random.choice(self.endpoints)
                logger.info(f"[Python] Attempt {attempt + 1}/{self.max_retries} using endpoint: {endpoint}")
                
                # 使用 sandbox_fusion 执行代码
                try:
                    from sandbox_fusion import run_code, RunCodeRequest
                    
                    code_result = run_code(
                        RunCodeRequest(
                            code=code, 
                            language='python', 
                            run_timeout=self.timeout
                        ),
                        max_attempts=1,
                        client_timeout=self.timeout,
                        endpoint=endpoint
                    )
                    
                    return self._format_result(code_result)
                    
                except ImportError:
                    # 如果没有安装 sandbox_fusion，回退到本地执行
                    if settings.allow_local_python:
                        return self._local_execute(code)
                    return "[Python Interpreter Error]: sandbox_fusion client not found and local execution is disabled."
                    
            except Exception as e:
                last_error = f'[Python Interpreter Error]: {str(e)} on endpoint {endpoint}'
                logger.error(f"Error on attempt {attempt + 1}: {last_error}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(0.5)
                    continue
        
        return last_error if last_error else '[Python Interpreter Error]: All attempts failed.'
    
    def _format_result(self, code_result) -> str:
        """格式化执行结果
        
        Args:
            code_result: sandbox_fusion 返回的结果
            
        Returns:
            格式化的结果字符串
        """
        result = []
        
        if hasattr(code_result, 'run_result'):
            run_result = code_result.run_result
            
            if hasattr(run_result, 'stdout') and run_result.stdout:
                result.append(f"stdout:\n{run_result.stdout}")
            
            if hasattr(run_result, 'stderr') and run_result.stderr:
                result.append(f"stderr:\n{run_result.stderr}")
            
            if hasattr(run_result, 'execution_time'):
                if run_result.execution_time >= self.timeout - 1:
                    result.append("[PythonInterpreter Error] TimeoutError: Execution timed out.")
        
        if not result:
            return 'Finished execution.'
        
        return '\n'.join(result)
    
    def _local_execute(self, code: str) -> str:
        """本地执行代码（仅用于测试/开发，生产环境应使用沙箱）"""
        import sys
        from io import StringIO
        import resource
        import multiprocessing
        
        # 使用进程池或 Process 运行以确保资源限制在子进程生效且不影响主进程
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=_run_with_limits_worker, args=(code, queue, self.timeout))
        p.start()
        p.join(timeout=self.timeout + 1)
        
        if p.is_alive():
            p.terminate()
            return "[Python Interpreter Error]: Execution timed out or exceeded resource limits."
        
        try:
            stdout_output, stderr_output, error = queue.get_nowait()
            if error:
                return f"[Python Interpreter Error]: {error}"
            
            result = []
            if stdout_output:
                result.append(f"stdout:\n{stdout_output}")
            if stderr_output:
                result.append(f"stderr:\n{stderr_output}")
            
            return '\n'.join(result) if result else 'Finished execution.'
        except:
            return "[Python Interpreter Error]: Failed to get execution results."
