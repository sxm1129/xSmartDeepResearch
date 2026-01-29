"""学术搜索工具 - 使用 Serper API 进行 Google Scholar 搜索"""

import json
import http.client
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, List, Optional, Union

from .base_tool import BaseTool


class ScholarTool(BaseTool):
    """Google Scholar 学术搜索工具
    
    使用 Serper.dev API 进行 Google Scholar 搜索
    """
    
    name = "google_scholar"
    description = "Leverage Google Scholar to retrieve relevant information from academic publications. Accepts multiple queries."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "array",
                "items": {"type": "string", "description": "The search query."},
                "minItems": 1,
                "description": "The list of search queries for Google Scholar."
            }
        },
        "required": ["query"]
    }
    
    def __init__(self, api_key: str = None, cfg: Optional[Dict] = None):
        """初始化学术搜索工具
        
        Args:
            api_key: Serper API Key
            cfg: 配置字典
        """
        super().__init__(cfg)
        self.api_key = api_key or self.cfg.get("api_key", "")
        self.base_host = "google.serper.dev"
    
    def call(self, params: Union[str, Dict[str, Any]], **kwargs) -> str:
        """执行学术搜索
        
        Args:
            params: 包含 query 字段的参数
            
        Returns:
            学术搜索结果字符串
        """
        params = self._parse_params(params)
        
        try:
            query = params.get("query", params.get("params", {}).get("query", []))
        except:
            return "[google_scholar] Invalid request format: Input must be a JSON object containing 'query' field"
        
        if not query:
            return "[google_scholar] Invalid request format: 'query' field is required"
        
        # 处理单个查询或多个查询
        if isinstance(query, str):
            return self._search_single(query)
        
        # 多个查询 - 并行执行
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(self._search_single, query))
        
        return "\n=======\n".join(results)
    
    def _search_single(self, query: str) -> str:
        """执行单个学术搜索查询
        
        Args:
            query: 搜索查询
            
        Returns:
            格式化的搜索结果
        """
        payload = {"q": query}
        
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # 请求重试
        for attempt in range(5):
            try:
                conn = http.client.HTTPSConnection(self.base_host)
                conn.request("POST", "/scholar", json.dumps(payload), headers)
                res = conn.getresponse()
                data = res.read()
                conn.close()
                
                results = json.loads(data.decode("utf-8"))
                return self._format_results(query, results)
                
            except Exception as e:
                if attempt == 4:
                    return f"Google Scholar Timeout for '{query}'. Please try again later."
                continue
        
        return f"Google Scholar search failed for '{query}'"
    
    def _format_results(self, query: str, results: Dict) -> str:
        """格式化学术搜索结果
        
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
                if "year" in page:
                    date_published = f"\nDate published: {page['year']}"
                
                publication_info = ""
                if "publicationInfo" in page:
                    publication_info = f"\nPublication: {page['publicationInfo']}"
                
                snippet = ""
                if "snippet" in page:
                    snippet = f"\n{page['snippet']}"
                
                # PDF链接
                link_info = "no available link"
                if "pdfUrl" in page:
                    link_info = f"pdfUrl: {page['pdfUrl']}"
                elif "link" in page:
                    link_info = page['link']
                
                cited_by = ""
                if "citedBy" in page:
                    cited_by = f"\nCited by: {page['citedBy']}"
                
                title = page.get('title', 'No title')
                
                redacted_version = f"{idx}. [{title}]({link_info}){publication_info}{date_published}{cited_by}{snippet}"
                redacted_version = redacted_version.replace("Your browser can't play this video.", "")
                web_snippets.append(redacted_version)
            
            content = f"A Google Scholar search for '{query}' found {len(web_snippets)} results:\n\n## Scholar Results\n"
            content += "\n\n".join(web_snippets)
            
            return content
            
        except Exception as e:
            return f"No results found for '{query}'. Try with a more general query."
