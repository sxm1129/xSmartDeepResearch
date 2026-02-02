"""搜索工具 - 使用 Serper API 进行 Google 搜索"""

import json
import http.client
from typing import Dict, Any, List, Optional, Union

from .base_tool import BaseTool
from src.utils.cache import cache_manager
from src.utils.semantic_cache import semantic_cache
from config import settings
from src.utils.logger import logger
import asyncio
import aiohttp


class SearchTool(BaseTool):
    """Google 搜索工具
    
    使用 Serper.dev API 进行 Google 搜索，支持批量查询和语言/地区自适应
    """
    
    name = "search"
    description = "Perform Google web searches then returns a string of the top search results. Accepts multiple queries."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "array",
                "items": {"type": "string", "description": "The search query."},
                "minItems": 1,
                "description": "The list of search queries."
            }
        },
        "required": ["query"]
    }
    
    def __init__(self, api_key: str = None, cfg: Optional[Dict] = None):
        """初始化搜索工具
        
        Args:
            api_key: Serper API Key
            cfg: 配置字典
        """
        super().__init__(cfg)
        self.api_key = api_key or self.cfg.get("api_key", "")
        self.base_host = "google.serper.dev"
    
    async def call(self, params: Union[str, Dict[str, Any]], **kwargs) -> str:
        """异步执行搜索
        
        Args:
            params: 包含 query 字段的参数
            
        Returns:
            搜索结果字符串
        """
        params = self._parse_params(params)
        
        try:
            queries = params.get("query", params.get("params", {}).get("query", []))
        except:
            return "[Search] Invalid request format: Input must be a JSON object containing 'query' field"
        
        if not queries:
            return "[Search] Invalid request format: 'query' field is required"
        
        # 处理单个查询或多个查询
        if isinstance(queries, str):
            queries = [queries]
        
        # 并行执行所有查询
        return await self._search_parallel(queries)

    async def _search_parallel(self, queries: List[str]) -> str:
        tasks = [self._search_single_async(q) for q in queries]
        results = await asyncio.gather(*tasks)
        return "\n\n=======\n\n".join(results)

    async def _search_single_async(self, query: str) -> str:
        """异步执行单个搜索"""
        # 检查缓存
        cached_result = cache_manager.get("search", query)
        if cached_result:
            return cached_result

        # 检测语言
        is_chinese = self._contains_chinese(query)
        if is_chinese:
            payload = {"q": query, "location": "China", "gl": "cn", "hl": "zh-cn"}
        else:
            payload = {"q": query, "location": "United States", "gl": "us", "hl": "en"}
        
        headers = {'X-API-KEY': self.api_key, 'Content-Type': 'application/json'}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"https://{self.base_host}/search", headers=headers, json=payload, timeout=30) as response:
                    if response.status == 200:
                        results = await response.json()
                        formatted_result = self._format_results(query, results)
                        cache_manager.set("search", query, formatted_result, expire_seconds=settings.cache_expiry_search)
                        semantic_cache.set("search", query, formatted_result)
                        return formatted_result
                    else:
                        return f"[Search] API error: {response.status}"
        except Exception as e:
            return f"[Search] Error: {str(e)}"
    
    def _search_single(self, query: str) -> str:
        """执行单个搜索查询
        
        Args:
            query: 搜索查询
            
        Returns:
            格式化的搜索结果
        """
        # 检查缓存
        cached_result = cache_manager.get("search", query)
        if cached_result:
            logger.info(f"[Search] Cache hit for: {query}")
            return cached_result
            
        # 语义缓存检查
        semantic_result = semantic_cache.get("search", query)
        if semantic_result:
            return semantic_result

        # 检测语言，设置搜索地区
        is_chinese = self._contains_chinese(query)
        
        if is_chinese:
            payload = {
                "q": query,
                "location": "China",
                "gl": "cn",
                "hl": "zh-cn"
            }
        else:
            payload = {
                "q": query,
                "location": "United States",
                "gl": "us",
                "hl": "en"
            }
        
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # 请求重试
        for attempt in range(5):
            try:
                conn = http.client.HTTPSConnection(self.base_host)
                conn.request("POST", "/search", json.dumps(payload), headers)
                res = conn.getresponse()
                data = res.read()
                conn.close()
                
                results = json.loads(data.decode("utf-8"))
                formatted_result = self._format_results(query, results)
                
                # 写入缓存
                cache_manager.set("search", query, formatted_result, expire_seconds=settings.cache_expiry_search)
                semantic_cache.set("search", query, formatted_result)
                
                return formatted_result
                
            except Exception as e:
                if attempt == 4:
                    return f"Google search Timeout for '{query}'. Please try again later."
                continue
        
        return f"Google search failed for '{query}'"
    
    def _format_results(self, query: str, results: Dict) -> str:
        """格式化搜索结果
        
        Args:
            query: 原始查询
            results: API返回的结果
            
        Returns:
            格式化的结果字符串
        """
        try:
            if "organic" not in results:
                return f"No results found for '{query}'. Try with a more general query."
            
            web_snippets = []
            idx = 0
            
            for page in results.get("organic", []):
                idx += 1
                
                # 构建结果条目
                date_published = ""
                if "date" in page:
                    date_published = f"\nDate published: {page['date']}"
                
                source = ""
                if "source" in page:
                    source = f"\nSource: {page['source']}"
                
                snippet = ""
                if "snippet" in page:
                    snippet = f"\n{page['snippet']}"
                
                title = page.get('title', 'No title')
                link = page.get('link', '#')
                
                redacted_version = f"{idx}. [{title}]({link}){date_published}{source}{snippet}"
                redacted_version = redacted_version.replace("Your browser can't play this video.", "")
                web_snippets.append(redacted_version)
            
            content = f"A Google search for '{query}' found {len(web_snippets)} results:\n\n## Web Results\n"
            content += "\n\n".join(web_snippets)
            
            return content
            
        except Exception as e:
            return f"No results found for '{query}'. Try with a more general query."
    
    def _contains_chinese(self, text: str) -> bool:
        """检测文本是否包含中文
        
        Args:
            text: 要检测的文本
            
        Returns:
            是否包含中文
        """
        return any('\u4E00' <= char <= '\u9FFF' for char in text)
