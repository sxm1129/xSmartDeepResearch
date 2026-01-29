"""网页访问工具 - 使用 Jina Reader 读取网页内容并进行摘要"""

import json
import aiohttp
import asyncio
from typing import Dict, Any, List, Optional, Union
import tiktoken

from .base_tool import BaseTool
from src.utils.cache import cache_manager
from src.utils.semantic_cache import semantic_cache
from config import settings
from src.utils.logger import logger


class VisitTool(BaseTool):
    """网页访问工具
    
    使用 Jina Reader 读取网页内容，并使用 LLM 进行摘要提取
    """
    
    name = "visit"
    description = "Visit webpage(s) and return the summary of the content."
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The URL(s) of the webpage(s) to visit. Can be a single URL or an array of URLs."
            },
            "goal": {
                "type": "string",
                "description": "The specific information goal for visiting webpage(s)."
            }
        },
        "required": ["url", "goal"]
    }
    
    def __init__(
        self, 
        jina_api_key: str = None,
        summary_client: Any = None,
        summary_model: str = "gpt-4o-mini",
        max_content_tokens: int = 95000,
        cfg: Optional[Dict] = None
    ):
        """初始化网页访问工具
        
        Args:
            jina_api_key: Jina API Key
            summary_client: 用于摘要的 OpenAI 客户端
            summary_model: 摘要模型名称
            max_content_tokens: 最大内容token数
            cfg: 配置字典
        """
        super().__init__(cfg)
        self.jina_api_key = jina_api_key or self.cfg.get("jina_api_key", "")
        self.summary_client = summary_client
        self.summary_model = summary_model
        self.max_content_tokens = max_content_tokens
        self._encoding = None
    
    @property
    def encoding(self):
        """懒加载 tiktoken 编码器"""
        if self._encoding is None:
            self._encoding = tiktoken.get_encoding("cl100k_base")
        return self._encoding
    
    def call(self, params: Union[str, Dict[str, Any]], **kwargs) -> str:
        """同步执行网页访问
        
        Args:
            params: 包含 url 和 goal 的参数
            
        Returns:
            网页摘要结果
        """
        # 在同步方法中运行异步方法
        return asyncio.run(self.acall(params, **kwargs))
    
    async def acall(self, params: Union[str, Dict[str, Any]], **kwargs) -> str:
        """异步执行网页访问 (支持并行)"""
        params = self._parse_params(params)
        
        try:
            urls = params.get("url", params.get("params", {}).get("url", []))
            goal = params.get("goal", params.get("params", {}).get("goal", "Summarize the key information"))
        except:
            return "[Visit] Invalid request format: Input must be a JSON object containing 'url' and 'goal' fields"
        
        if not urls:
            return "[Visit] Invalid request format: 'url' field is required"
        
        # 处理单个URL或多个URL
        if isinstance(urls, str):
            urls = [urls]
            
        # 并行执行所有访问任务
        tasks = [self._process_single_url(u, goal) for u in urls]
        results = await asyncio.gather(*tasks)
        
        return "\n\n=======\n\n".join(results)
    
    async def _process_single_url(self, url: str, goal: str) -> str:
        """处理单个URL
        
        Args:
            url: 网页URL
            goal: 访问目标
            
        Returns:
            网页摘要
        """
        # 检查缓存
        cache_key = {"url": url, "goal": goal}
        cached_result = cache_manager.get("visit", cache_key)
        if cached_result:
            logger.info(f"[Visit] Cache hit for: {url}")
            return cached_result
            
        # 语义缓存检查 (基于 goal + url)
        semantic_result = semantic_cache.get("visit", f"{goal}:{url}")
        if semantic_result:
            return semantic_result

        # 1. 读取网页内容
        content = await self._read_page(url)
        
        if not content or content.startswith("[visit] Failed"):
            return self._format_error(url, goal, "The provided webpage content could not be accessed.")
        
        # 2. 截断到最大token数
        content = self._truncate_to_tokens(content, self.max_content_tokens)
        
        # 3. 使用LLM摘要
        if self.summary_client:
            summary = await self._summarize(content, url, goal)
            # 写入缓存
            if not summary.startswith("[Visit] Error"):
                cache_manager.set("visit", cache_key, summary, expire_seconds=settings.cache_expiry_visit)
                semantic_cache.set("visit", f"{goal}:{url}", summary)
            return summary
        else:
            # 如果没有摘要客户端，直接返回截断的内容
            raw_content = self._format_raw_content(url, goal, content)
            cache_manager.set("visit", cache_key, raw_content, expire_seconds=settings.cache_expiry_visit)
            semantic_cache.set("visit", f"{goal}:{url}", raw_content)
            return raw_content
    
    async def _read_page(self, url: str) -> Optional[str]:
        """使用 Jina Reader 读取网页
        
        Args:
            url: 网页URL
            
        Returns:
            网页内容或None
        """
        max_retries = 3
        timeout = aiohttp.ClientTimeout(total=50)
        
        for attempt in range(max_retries):
            try:
                headers = {"Authorization": f"Bearer {self.jina_api_key}"}
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(
                        f"https://r.jina.ai/{url}",
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            logger.error(f"[Visit] Error reading {url}: HTTP {response.status}")
                            
            except asyncio.TimeoutError:
                logger.warning(f"[Visit] Timeout reading {url}, attempt {attempt + 1}/{max_retries}")
            except Exception as e:
                logger.error(f"[Visit] Error reading {url}: {e}")
            
            await asyncio.sleep(0.5)
        
        return None
    
    async def _summarize(self, content: str, url: str, goal: str) -> str:
        """使用LLM摘要内容 (支持 Map-Reduce 处理长文本)"""
        # 定义分次摘要的阈值 (约 25,000 tokens)
        CHUNK_SIZE = 25000
        tokens = self.encoding.encode(content)
        
        if len(tokens) <= CHUNK_SIZE:
            return await self._summarize_chunk(content, url, goal)
        
        # 并行处理多个分段 (Map 阶段)
        print(f"[Visit] Content too large ({len(tokens)} tokens), using Map-Reduce...")
        chunks = []
        for i in range(0, len(tokens), CHUNK_SIZE):
            chunk_tokens = tokens[i : i + CHUNK_SIZE]
            chunks.append(self.encoding.decode(chunk_tokens))
        
        tasks = [self._summarize_chunk(chunk, url, goal, is_partial=True) for chunk in chunks]
        partial_summaries = await asyncio.gather(*tasks)
        
        # 过滤掉失败的分段
        valid_summaries = [s for s in partial_summaries if not s.startswith("[Visit] Error")]
        
        if not valid_summaries:
            return self._format_error(url, goal, "Failed to summarize all content chunks.")
            
        # 聚合分段摘要 (Reduce 阶段)
        combined_summaries = "\n\n".join(valid_summaries)
        reduce_prompt = f"The following are summaries of different parts of the same webpage for the goal: {goal}. Please merge them into a single coherent, comprehensive summary and evidence list.\n\n{combined_summaries}"
        
        return await self._summarize_chunk(reduce_prompt, url, goal, is_reduction=True)

    async def _summarize_chunk(self, content: str, url: str, goal: str, is_partial: bool = False, is_reduction: bool = False) -> str:
        """执行单个分段的摘要"""
        from config.prompts import build_extractor_prompt
        
        if is_reduction:
            prompt = content # 已经是构建好的聚合 prompt
        else:
            prompt = build_extractor_prompt(content, goal)
        
        try:
            # 使用异步方式调用 (如果 summary_client 支持异步，通常 OpenAI 客户端有异步版)
            # 这里先保持同步调用以兼容现有 client，但在线程池运行
            def call_sync():
                return self.summary_client.chat.completions.create(
                    model=self.summary_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3 if is_reduction else 0.7
                )
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, call_sync)
            raw = response.choices[0].message.content
            
            # 解析JSON响应
            raw = raw.replace("```json", "").replace("```", "").strip()
            
            try:
                parsed = json.loads(raw)
                if is_partial:
                    # 返回中间部分的摘要，供聚合使用
                    return f"Evidence:\n{parsed.get('evidence')}\nSummary:\n{parsed.get('summary')}"
                return self._format_summary(url, goal, parsed)
            except json.JSONDecodeError:
                # 尝试提取JSON
                left = raw.find('{')
                right = raw.rfind('}')
                if left != -1 and right != -1 and left <= right:
                    try:
                        parsed = json.loads(raw[left:right+1])
                        if is_partial:
                            return f"Evidence:\n{parsed.get('evidence')}\nSummary:\n{parsed.get('summary')}"
                        return self._format_summary(url, goal, parsed)
                    except: pass
                
                # 如果是最终聚合阶段解析失败，则返回原始文本
                if is_reduction:
                    return f"Merged Result (Raw):\n{raw}"
                return self._format_error(url, goal, "Failed to parse chunk summary.")
                
        except Exception as e:
            return self._format_error(url, goal, f"Chunk summary generation failed: {str(e)}")
    
    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """截断文本到指定token数
        
        Args:
            text: 原始文本
            max_tokens: 最大token数
            
        Returns:
            截断后的文本
        """
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
    
    def _format_summary(self, url: str, goal: str, parsed: Dict) -> str:
        """格式化摘要结果
        
        Args:
            url: 网页URL
            goal: 访问目标
            parsed: 解析后的摘要字典
            
        Returns:
            格式化的摘要字符串
        """
        result = f"The useful information in {url} for user goal {goal} as follows:\n\n"
        result += f"Evidence in page:\n{parsed.get('evidence', 'No evidence extracted')}\n\n"
        result += f"Summary:\n{parsed.get('summary', 'No summary available')}\n\n"
        return result
    
    def _format_error(self, url: str, goal: str, error_msg: str) -> str:
        """格式化错误结果
        
        Args:
            url: 网页URL
            goal: 访问目标
            error_msg: 错误信息
            
        Returns:
            格式化的错误字符串
        """
        result = f"The useful information in {url} for user goal {goal} as follows:\n\n"
        result += f"Evidence in page:\n{error_msg}\n\n"
        result += "Summary:\nThe webpage content could not be processed.\n\n"
        return result
    
    def _format_raw_content(self, url: str, goal: str, content: str) -> str:
        """格式化原始内容（无摘要时使用）
        
        Args:
            url: 网页URL
            goal: 访问目标
            content: 原始内容
            
        Returns:
            格式化的内容字符串
        """
        # 截取前10000字符
        if len(content) > 10000:
            content = content[:10000] + "..."
        
        result = f"Content from {url} for goal: {goal}\n\n"
        result += f"Raw Content:\n{content}\n\n"
        return result
