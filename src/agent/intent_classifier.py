"""意图分类器 - 用于识别用户查询类型并匹配专家角色"""

import json
import re
from typing import Dict, Any, List, Optional
from openai import AsyncOpenAI
from src.utils.logger import logger

CLASSIFICATION_PROMPT = """You are an intent classifier for a deep research assistant. 
Your task is to classify the user's research query into one of the following categories:

- **coding_tech**: Deep technical/coding/architecture questions, software engineering, AI/ML implementation details.
- **finance_market**: Stock analysis, investment, macroeconomics, financial reports, market trends.
- **strategy_biz**: Business models, competitive landscape, product strategy, GTM, supply chain.
- **medical_health**: Medicine, health, biotech, clinical research, public health policy.
- **legal_policy**: Law, regulation, government policy, compliance, IP, jurisdiction-specific rules.
- **academic_sci**: Fundamental science (physics, math, etc.), formal academic research, peer-review methodology.
- **media_creative**: Marketing, content trends, brand analysis, consumer psychology, entertainment.
- **lifestyle_con**: Consumer goods reviews, travel planning, hobbies, daily life optimization.

Output ONLY a JSON object in the following format:
{"category": "coding_tech" | "finance_market" | "strategy_biz" | "medical_health" | "legal_policy" | "academic_sci" | "media_creative" | "lifestyle_con", "reason": "brief reason"}

Query: {query}"""

class IntentClassifier:
    """意图分类器核心类"""
    
    def __init__(self, client: AsyncOpenAI, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model
        
    async def aclassify(self, query: str) -> Dict[str, str]:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": CLASSIFICATION_PROMPT.format(query=query)}],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=100
            )
            
            raw_content = response.choices[0].message.content
            logger.debug(f"Raw Intent Response: {raw_content}")
            
            try:
                result = json.loads(raw_content)
            except Exception as json_err:
                # 尝试清洗 JSON (处理可能的 Markdown 代码块)
                clean_json = re.sub(r'```json\s*(.*?)\s*```', r'\1', raw_content, flags=re.DOTALL)
                result = json.loads(clean_json)
            
            # 兼容嵌套结构 (有些模型即使要求 json_object 也会嵌套一层)
            if "intent" in result and isinstance(result["intent"], dict):
                result = result["intent"]
            
            # 提取 category 和 reason，确保不抛出 KeyError
            category = result.get("category", result.get("type", "general"))
            reason = result.get("reason", result.get("explanation", "No reason provided"))
            
            # 清理字符串
            if isinstance(category, str):
                category = category.strip().strip('"').strip("'").lower()
            if isinstance(reason, str):
                reason = reason.strip()
            
            logger.info(f"🔍 Intent Classified: {category} | Reason: {reason}")
            return {"category": category, "reason": reason}
            
        except Exception as e:
            logger.error(f"❌ Intent classification failed: {e}. Raw response: {raw_content if 'raw_content' in locals() else 'None'}")
            return {"category": "general", "reason": f"Fallback due to error: {str(e)}"}

    def classify(self, query: str) -> Dict[str, str]:
        """对原始查询进行分类 (同步版本 - 供非异步环境使用)"""
        import asyncio
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(self.aclassify(query))
