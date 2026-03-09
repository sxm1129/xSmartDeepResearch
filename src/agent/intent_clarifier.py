"""意图澄清器 - 用于在深度研究前生成研究方向选项，引导用户明确研究意图"""

import json
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from openai import AsyncOpenAI
from src.utils.logger import logger


@dataclass
class ClarificationDirection:
    """单个澄清方向"""
    id: str
    title: str
    description: str
    example_query: str


@dataclass
class ClarificationResult:
    """澄清结果"""
    directions: List[ClarificationDirection]
    round: int
    ready_to_research: bool
    refined_query: Optional[str] = None
    original_question: str = ""


# =============================================================================
# Prompts
# =============================================================================

CLARIFICATION_PROMPT_R1 = """You are a research intent clarifier for a deep research assistant.

The user has submitted a research question. Your task is to analyze the question and generate 4 distinct research directions that the user might want to explore. Each direction should represent a meaningfully different angle of investigation.

**Rules:**
1. Generate exactly 4 directions.
2. Each direction must have: a clear title, a 1-2 sentence description, and an example refined query.
3. The directions should cover diverse aspects of the topic.
4. Titles should be concise (under 10 words).
5. The example_query should be a full, specific research question that a deep research agent could execute.
6. {language_instruction}

**Output ONLY a JSON object** in this exact format:
{{
  "directions": [
    {{
      "id": "dir_1",
      "title": "Direction Title",
      "description": "Brief description of what this research angle covers.",
      "example_query": "A specific, detailed research question for this direction."
    }}
  ]
}}

User's Question: {question}"""


CLARIFICATION_PROMPT_R2 = """You are a research intent clarifier. The user has selected a research direction. Your task is to generate a refined, comprehensive research query that a deep research agent should execute.

**Context:**
- Original Question: {original_question}
- Selected Direction Title: {selected_title}
- Selected Direction Description: {selected_description}
- User's Additional Context (if any): {user_context}

**Rules:**
1. Synthesize the original question, selected direction, and any additional context into ONE comprehensive research query.
2. The refined query should be specific, actionable, and contain clear research objectives.
3. Respond in the SAME LANGUAGE as the original question.
4. Output ONLY a JSON object.

**Output format:**
{{
  "refined_query": "The comprehensive, refined research query.",
  "research_scope": "A brief 1-sentence summary of the finalized research scope."
}}"""


CUSTOM_DIRECTION_PROMPT = """You are a research intent clarifier. The user provided a custom research direction for their question.

**Context:**
- Original Question: {original_question}
- User's Custom Direction: {custom_input}

**Rules:**
1. Combine the original question with the user's custom direction into ONE comprehensive research query.
2. The refined query should be specific, actionable, and contain clear research objectives.
3. Respond in the SAME LANGUAGE as the original question.
4. Output ONLY a JSON object.

**Output format:**
{{
  "refined_query": "The comprehensive, refined research query.",
  "research_scope": "A brief 1-sentence summary of the finalized research scope."
}}"""


class IntentClarifier:
    """意图澄清器核心类
    
    负责在深度研究前生成研究方向选项，引导用户明确研究意图。
    完全独立于现有的 IntentClassifier。
    """
    
    def __init__(self, client: AsyncOpenAI, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model
    
    async def clarify_round1(self, question: str, language: str = "en") -> ClarificationResult:
        """第一轮澄清：分析问题，生成研究方向选项
        
        Args:
            question: 用户原始问题
            language: 输出语言 ('zh' 或 'en')
            
        Returns:
            ClarificationResult with directions
        """
        try:
            lang_instruction = self._get_language_instruction(language)
            prompt = CLARIFICATION_PROMPT_R1.format(question=question, language_instruction=lang_instruction)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.7,  # 稍微高一点以产生多样化的方向
                max_tokens=1500
            )
            
            raw_content = response.choices[0].message.content
            logger.debug(f"Clarification R1 Raw Response: {raw_content}")
            
            result = self._parse_json_response(raw_content)
            
            directions = []
            for d in result.get("directions", []):
                directions.append(ClarificationDirection(
                    id=d.get("id", f"dir_{len(directions)+1}"),
                    title=d.get("title", "Unknown Direction"),
                    description=d.get("description", ""),
                    example_query=d.get("example_query", question)
                ))
            
            if not directions:
                # Fallback: 如果 LLM 没有返回有效方向，生成默认方向
                directions = self._generate_fallback_directions(question, language)
            
            logger.info(f"🎯 Clarification R1: Generated {len(directions)} directions for: {question[:50]}...")
            
            return ClarificationResult(
                directions=directions,
                round=1,
                ready_to_research=False,
                original_question=question
            )
            
        except Exception as e:
            logger.error(f"❌ Clarification R1 failed: {e}")
            # 优雅降级：返回默认方向
            return ClarificationResult(
                directions=self._generate_fallback_directions(question, language),
                round=1,
                ready_to_research=False,
                original_question=question
            )
    
    async def clarify_round2(
        self, 
        original_question: str, 
        selected_direction: ClarificationDirection,
        user_context: str = "",
        language: str = "en"
    ) -> ClarificationResult:
        """第二轮澄清：根据用户选择的方向，生成精炼的研究查询
        
        Args:
            original_question: 原始问题
            selected_direction: 用户选择的方向
            user_context: 用户额外补充的上下文
            language: 输出语言
            
        Returns:
            ClarificationResult with refined_query and ready_to_research=True
        """
        try:
            lang_instruction = self._get_language_instruction(language)
            prompt = CLARIFICATION_PROMPT_R2.format(
                original_question=original_question,
                selected_title=selected_direction.title,
                selected_description=selected_direction.description,
                user_context=user_context or "None"
            )
            # Append language instruction
            prompt += f"\n\n**IMPORTANT: {lang_instruction}**"
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500
            )
            
            raw_content = response.choices[0].message.content
            logger.debug(f"Clarification R2 Raw Response: {raw_content}")
            
            result = self._parse_json_response(raw_content)
            refined_query = result.get("refined_query", selected_direction.example_query)
            
            logger.info(f"🎯 Clarification R2: Refined query: {refined_query[:80]}...")
            
            return ClarificationResult(
                directions=[],
                round=2,
                ready_to_research=True,
                refined_query=refined_query,
                original_question=original_question
            )
            
        except Exception as e:
            logger.error(f"❌ Clarification R2 failed: {e}")
            # 降级：直接使用方向中的 example_query
            return ClarificationResult(
                directions=[],
                round=2,
                ready_to_research=True,
                refined_query=selected_direction.example_query,
                original_question=original_question
            )
    
    async def clarify_custom(
        self,
        original_question: str,
        custom_input: str,
        language: str = "en"
    ) -> ClarificationResult:
        """处理用户自定义方向
        
        Args:
            original_question: 原始问题
            custom_input: 用户自定义输入的方向描述
            language: 输出语言
            
        Returns:
            ClarificationResult with refined_query and ready_to_research=True
        """
        try:
            lang_instruction = self._get_language_instruction(language)
            prompt = CUSTOM_DIRECTION_PROMPT.format(
                original_question=original_question,
                custom_input=custom_input
            )
            prompt += f"\n\n**IMPORTANT: {lang_instruction}**"
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=500
            )
            
            raw_content = response.choices[0].message.content
            result = self._parse_json_response(raw_content)
            refined_query = result.get("refined_query", f"{original_question} - {custom_input}")
            
            logger.info(f"🎯 Custom clarification: {refined_query[:80]}...")
            
            return ClarificationResult(
                directions=[],
                round=2,
                ready_to_research=True,
                refined_query=refined_query,
                original_question=original_question
            )
            
        except Exception as e:
            logger.error(f"❌ Custom clarification failed: {e}")
            return ClarificationResult(
                directions=[],
                round=2,
                ready_to_research=True,
                refined_query=f"{original_question} — Focus: {custom_input}",
                original_question=original_question
            )
    
    def _get_language_instruction(self, language: str) -> str:
        """获取语言指令"""
        if language == 'zh':
            return "你必须使用中文回复。所有的 title、description、example_query 都必须是中文。"
        return "Respond in the SAME LANGUAGE as the user's question. If the user asks in Chinese, respond in Chinese. If in English, respond in English."

    def _parse_json_response(self, raw_content: str) -> dict:
        """解析 LLM 返回的 JSON 内容"""
        try:
            return json.loads(raw_content)
        except json.JSONDecodeError:
            # 尝试清洗 Markdown 代码块 (包含或不包含语言标识)
            clean = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', raw_content, flags=re.DOTALL)
            return json.loads(clean.strip())
    
    def _generate_fallback_directions(self, question: str, language: str = "en") -> List[ClarificationDirection]:
        """生成默认方向（LLM 调用失败时的降级方案）"""
        if language == 'zh':
            return [
                ClarificationDirection(
                    id="dir_1",
                    title="概述与现状",
                    description="对该主题进行全面的概述和现状分析。",
                    example_query=f"请全面概述并分析以下主题的现状：{question}"
                ),
                ClarificationDirection(
                    id="dir_2",
                    title="影响与启示",
                    description="分析该主题的广泛影响和深层启示。",
                    example_query=f"分析以下主题的影响和启示：{question}"
                ),
                ClarificationDirection(
                    id="dir_3",
                    title="未来趋势与预测",
                    description="探索与该主题相关的未来发展趋势和预测。",
                    example_query=f"关于以下主题，未来的发展趋势和预测是什么：{question}"
                ),
                ClarificationDirection(
                    id="dir_4",
                    title="实际应用",
                    description="聚焦于实际应用场景、用例和可操作的建议。",
                    example_query=f"关于以下主题，有哪些实际应用和可操作的建议：{question}"
                )
            ]
        return [
            ClarificationDirection(
                id="dir_1",
                title="Overview & Current State",
                description="A comprehensive overview of the topic and its current status.",
                example_query=f"Provide a comprehensive overview and current state analysis of: {question}"
            ),
            ClarificationDirection(
                id="dir_2",
                title="Impact & Implications",
                description="Analyze the broader impact and implications of this topic.",
                example_query=f"Analyze the impact and implications of: {question}"
            ),
            ClarificationDirection(
                id="dir_3",
                title="Future Trends & Predictions",
                description="Explore future trends, forecasts, and predictions related to this topic.",
                example_query=f"What are the future trends and predictions related to: {question}"
            ),
            ClarificationDirection(
                id="dir_4",
                title="Practical Applications",
                description="Focus on practical applications, use cases, and actionable insights.",
                example_query=f"What are the practical applications and actionable insights for: {question}"
            )
        ]
