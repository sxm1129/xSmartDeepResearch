"""意图分类器 - 用于识别用户查询类型并匹配专家角色"""

import json
import re
from typing import Dict, Any, List, Optional
from openai import OpenAI
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
    
    def __init__(self, client: OpenAI, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model
        
    def classify(self, query: str) -> Dict[str, str]:
        """对原始查询进行分类
        
        Args:
            query: 用户输入的查询
            
        Returns:
            包含 category 和 reason 的字典
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": CLASSIFICATION_PROMPT.format(query=query)}],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=100
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Robustness: Remove extra quotes or whitespace
            if "category" in result and isinstance(result["category"], str):
                result["category"] = result["category"].strip().strip('"').strip("'")
            
            logger.info(f"🔍 Intent Classified: {result.get('category')} | Reason: {result.get('reason')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Intent classification failed: {e}")
            # Ensure we return a valid dict structure even on error
            return {"category": "general", "reason": f"Fallback due to error: {str(e)}"}
            
        except Exception as e:
            logger.error(f"❌ Intent classification failed: {e}")
            return {"category": "general", "reason": "Fallback to general due to error"}
