"""xSmartDeepResearch ReAct Agent 核心实现"""

import json
import time
import asyncio
import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from openai import AsyncOpenAI

from config import settings, build_system_prompt, FORCE_SUMMARIZE_PROMPT
from src.tools import BaseTool, ToolRegistry
from src.agent.intent_classifier import IntentClassifier
from src.utils.logger import logger
from src.utils.session_manager import SessionManager


@dataclass
class ResearchResult:
    """研究结果"""
    question: str
    answer: str
    prediction: str
    messages: List[Dict[str, str]]
    termination: str
    execution_time: float = 0.0
    iterations: int = 0
    
    def dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "prediction": self.prediction,
            "messages": self.messages,
            "termination": self.termination,
            "execution_time": self.execution_time,
            "iterations": self.iterations
        }


class xSmartReactAgent:
    """xSmartDeepResearch ReAct Agent
    
    基于 ReAct (Reasoning + Acting) 框架的智能研究代理，
    支持多轮思考-行动-观察循环，能够自主进行深度信息检索和推理。
    """
    
    # 特殊标记
    TOOL_CALL_START = "<tool_call>"
    TOOL_CALL_END = "</tool_call>"
    TOOL_RESPONSE_START = "<tool_response>"
    TOOL_RESPONSE_END = "</tool_response>"
    THINK_START = "<think>"
    THINK_END = "</think>"
    ANSWER_START = "<answer>"
    ANSWER_END = "</answer>"
    CODE_START = "<code>"
    CODE_END = "</code>"
    
    def __init__(
        self,
        client: AsyncOpenAI = None,
        model: str = None,
        tools: List[BaseTool] = None,
        max_iterations: int = None,
        max_tokens: int = None,
        temperature: float = None,
        top_p: float = None,
        presence_penalty: float = None,
        timeout_minutes: int = 150,
        classifier_model: str = "gpt-4o-mini"
    ):
        """初始化 ReAct Agent"""
        # 客户端配置
        self.client = client or AsyncOpenAI(
            api_key=settings.openrouter_key or settings.api_key,
            base_url=settings.api_base,
            timeout=600.0
        )
        self.model = model or settings.model_name
        
        # Agent 配置
        self.max_iterations = max_iterations or settings.max_llm_call_per_run
        self.max_tokens = max_tokens or settings.max_context_tokens
        self.temperature = temperature or settings.temperature
        self.top_p = top_p or settings.top_p
        self.presence_penalty = presence_penalty or settings.presence_penalty
        self.timeout_minutes = timeout_minutes
        
        # 意图分类器
        self.classifier = IntentClassifier(self.client, model=classifier_model)
        
        # 会话管理器
        self.session_manager = SessionManager()
        self.current_session_id = None
        self.current_project_id = None # 用于绑定当前 Project
        
        # 工具配置
        self.tools = {tool.name: tool for tool in (tools or [])}
        
        # Token 计数器 (懒加载)
        self._tokenizer = None
    
    @property
    def tokenizer(self):
        """懒加载 tokenizer"""
        if self._tokenizer is None:
            try:
                import tiktoken
                self._tokenizer = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                self._tokenizer = None
        return self._tokenizer
    
    def register_tool(self, tool: BaseTool) -> None:
        """注册工具
        
        Args:
            tool: 工具实例
        """
        self.tools[tool.name] = tool
    
    async def run(self, question: str, ground_truth: str = "", max_iterations: int = None) -> ResearchResult:
        """执行研究任务 (异步版本)"""
        start_time = time.time()
        
        # 使用生成器运行并累积结果
        messages = []
        prediction = ""
        iterations = 0
        termination = "unknown"
        
        async for event in self.stream_run(question, max_iterations=max_iterations):
            event_type = event.get("type")
            
            if event_type == "final_answer":
                prediction = event.get("content", "")
                messages = event.get("messages", [])
                iterations = event.get("iterations", 0)
                termination = event.get("termination", "answer")
            elif event_type == "error":
                prediction = event.get("content", "Error occurred")
                termination = "error"
            elif event_type == "timeout":
                prediction = "Timeout"
                termination = "timeout"
        
        return ResearchResult(
            question=question,
            answer=ground_truth,
            prediction=prediction,
            messages=messages,
            termination=termination,
            execution_time=time.time() - start_time,
            iterations=iterations
        )

    async def stream_run(self, question: str, max_iterations: int = None):
        """执行研究任务 (流式生成器版本)
        
        Args:
            question: 用户的研究问题
            max_iterations: 本次运行的最大迭代次数 (不修改实例属性)
        
        Yields:
            Dict[str, Any]: 包含 type 和 content 的事件字典
        """
        start_time = time.time()
        effective_max_iterations = max_iterations or self.max_iterations
        
        # 🟢 步骤 1: 意图识别 (动态人设注入)
        yield {"type": "status", "content": "🔍 Identifying research intent..."}
        # PERSIST: status
        if self.current_session_id:
             await asyncio.to_thread(self.session_manager.add_message, self.current_session_id, "status", "🔍 Identifying research intent...")

        intent = await self.classifier.aclassify(question)
        category = intent.get("category", "general")
        reason = intent.get("reason", "")
        status_msg = f"🎯 Intent: **{category.upper()}** ({reason})"
        yield {"type": "status", "content": status_msg}
        # PERSIST: status (Create session happens next, so we can't persist this one yet unless we move session creation up. 
        # Actually session creation is the next step. So we should persist this AFTER session creation.)

        # 🔵 步骤 2: 创建会话持久化
        self.current_session_id = await asyncio.to_thread(
            self.session_manager.create_session,
            title=question[:50],  # 简单取前50字符作为标题
            intent_category=category,
            project_id=self.current_project_id
        )
        # 记录用户问题
        await asyncio.to_thread(self.session_manager.add_message, self.current_session_id, "user", question)
        # PERSIST: Delayed status messages
        await asyncio.to_thread(self.session_manager.add_message, self.current_session_id, "status", status_msg)

        # 构建初始消息
        tool_definitions = [tool.get_function_definition() for tool in self.tools.values()]
        system_prompt = build_system_prompt(tool_definitions, category=category)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        iterations = 0
        
        while iterations < effective_max_iterations:
            elapsed_minutes = (time.time() - start_time) / 60
            if elapsed_minutes > self.timeout_minutes:
                yield {"type": "timeout", "content": "Research timeout"}
                return

            iterations += 1
            yield {"type": "status", "content": f"Iteration {iterations}...", "iteration": iterations}
            await asyncio.to_thread(self.session_manager.add_message, self.current_session_id, "status", f"Iteration {iterations}...")
            
            # 调用 LLM
            response = await self._call_llm(messages)
            
            if self.TOOL_RESPONSE_START in response:
                pos = response.find(self.TOOL_RESPONSE_START)
                response = response[:pos]
            
            messages.append({"role": "assistant", "content": response.strip()})
            
            # 提取思考过程
            if self.THINK_START in response:
                think_match = re.search(f"{re.escape(self.THINK_START)}(.*?){re.escape(self.THINK_END)}", response, re.DOTALL)
                if think_match:
                    think_content = think_match.group(1).strip()
                else:
                    # 容错：处理未闭合标签
                    think_content = response.split(self.THINK_START)[-1].strip()
                    # 如果后面有工具调用或答案标签，截断它们
                    for tag in [self.TOOL_CALL_START, self.ANSWER_START]:
                        if tag in think_content:
                            think_content = think_content.split(tag)[0].strip()
                
                if think_content:
                    yield {"type": "think", "content": think_content}
                    # 记录思考步骤
                    await asyncio.to_thread(self.session_manager.add_message, self.current_session_id, "thought", think_content)
            
            # 检查是否有最终答案
            if self._has_answer(response):
                prediction = self._extract_answer(response)
                
                # 记录最终答案
                await asyncio.to_thread(self.session_manager.add_message, self.current_session_id, "answer", prediction)
                
                yield {"type": "answer", "content": prediction}
                yield {
                    "type": "final_answer", 
                    "content": prediction, 
                    "messages": messages, 
                    "iterations": iterations,
                    "termination": "answer"
                }
                return
            
            # 检查并执行工具调用
            tool_calls = self._extract_tool_calls(response)
            if tool_calls:
                # 1. 产生 tool_start 事件
                execution_tasks = []
                tool_names = []
                
                for tc in tool_calls:
                    tool_name = tc.get("name")
                    tool_args = tc.get("arguments", {})
                    
                    yield {
                        "type": "tool_start", 
                        "content": f"Calling tool: {tool_name}", 
                        "tool": tool_name,
                        "arguments": tool_args,
                        "iteration": iterations
                    }
                    
                    logger.info(f"🔧 Check tool: {tool_name}")
                    
                    if tool_name in self.tools:
                        logger.info(f"🔧 Executing tool (Parallel): {tool_name}")
                        execution_tasks.append(self.tools[tool_name].call(tool_args))
                        tool_names.append(tool_name)
                    else:
                        # 对于不存在的工具，我们创建一个直接返回错误的 mock task
                        async def _not_found_task(t_name=tool_name):
                            return f"[Error] Tool '{t_name}' not found. Available: {list(self.tools.keys())}"
                        execution_tasks.append(_not_found_task())
                        tool_names.append(tool_name)

                # 2. 并行执行
                if execution_tasks:
                    results = await asyncio.gather(*execution_tasks)
                    
                    # 3. 处理结果并反馈
                    combined_tool_outputs = []
                    
                    for i, result in enumerate(results):
                        tool_name = tool_names[i]
                        
                        # 记录工具调用的详细信息
                        await asyncio.to_thread(
                            self.session_manager.add_message,
                            self.current_session_id, 
                            "tool", 
                            f"Call: {tool_name}\nResult Length: {len(str(result))}",
                            metadata={"tool_name": tool_name}
                        )

                        # PERSIST: tool_response
                        await asyncio.to_thread(
                            self.session_manager.add_message,
                            self.current_session_id,
                            "tool_response",
                            result,
                            metadata={"tool_name": tool_name}
                        )

                        yield {
                            "type": "tool_response", 
                            "content": result, 
                            "tool": tool_name,
                            "iteration": iterations
                        }
                        
                        combined_tool_outputs.append(f"Tool '{tool_name}' Output:\n{result}")

                    # 将所有结果合并为一个 User Message 反馈给 LLM
                    # 这样 LLM 可以一次性看到所有并行执行的结果
                    full_response_content = "\n\n".join(combined_tool_outputs)
                    messages.append({
                        "role": "user",
                        "content": f"{self.TOOL_RESPONSE_START}\n{full_response_content}\n{self.TOOL_RESPONSE_END}"
                    })
            
            # 检查 token 限制
            token_count = self._count_tokens(messages)
            if token_count > self.max_tokens:
                # 如果还有很多步可以走，尝试剪枝而不是立即总结
                if iterations < effective_max_iterations - 3:
                    logger.info(f"Token count {token_count} exceeds {self.max_tokens}. Pruning context.")
                    messages = self._prune_messages(messages)
                    yield {"type": "status", "content": "Context pruned to save tokens."}
                    await asyncio.to_thread(self.session_manager.add_message, self.current_session_id, "status", "Context pruned to save tokens.")
                else:
                    yield {"type": "status", "content": "Token limit reached, forcing final summary..."}
                    await asyncio.to_thread(self.session_manager.add_message, self.current_session_id, "status", "Token limit reached, forcing final summary...")
                    res = await self._force_summarize(messages, question, "", start_time, iterations)
                    yield {"type": "answer", "content": res.prediction}
                    yield {
                        "type": "final_answer", 
                        "content": res.prediction, 
                        "messages": messages, 
                        "iterations": iterations,
                        "termination": res.termination
                    }
                    return

        # Max iterations reached — force summarize from collected data
        yield {"type": "status", "content": "Max iterations reached, generating final summary from collected research..."}
        try:
            res = await self._force_summarize(messages, question, "", start_time, iterations)
            prediction = res.prediction
            termination = res.termination
            yield {"type": "answer", "content": prediction}
        except Exception as e:
            logger.error(f"Force summarize failed: {e}")
            prediction = "Max iterations reached without final answer"
            termination = "max_iterations_exceeded"
        
        yield {
            "type": "final_answer", 
            "content": prediction, 
            "messages": messages, 
            "iterations": iterations,
            "termination": termination
        }

    
    async def _call_llm(self, messages: List[Dict], max_retries: int = 10) -> str:
        """调用 LLM (异步)"""
        base_sleep_time = 1
        
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stop=[f"\n{self.TOOL_RESPONSE_START}", self.TOOL_RESPONSE_START],
                    temperature=self.temperature,
                    top_p=self.top_p,
                    presence_penalty=self.presence_penalty,
                    max_tokens=10000
                )
                
                content = response.choices[0].message.content
                if content and content.strip():
                    return content.strip()
                    
            except Exception as e:
                logger.error(f"[LLM] Attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                sleep_time = min(base_sleep_time * (2 ** attempt), 30)
                await asyncio.sleep(sleep_time)
        
        return "LLM call failed after all retries"
    
    def _has_answer(self, content: str) -> bool:
        """检查内容中是否包含最终答案"""
        return self.ANSWER_START in content # 容错：只要有开始标签就认为有答案
    
    def _extract_answer(self, content: str) -> str:
        """从响应内容中提取最终答案"""
        # 尝试匹配闭合标签
        match = re.search(f"{re.escape(self.ANSWER_START)}(.*?){re.escape(self.ANSWER_END)}", content, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # 容错：尝试匹配未闭合的开始标签
        if self.ANSWER_START in content:
            return content.split(self.ANSWER_START)[-1].strip()
            
        return content.strip()
    
    def _has_tool_call(self, content: str) -> bool:
        """检查内容中是否包含工具调用"""
        return bool(re.search(r'<tool_call>.*?</tool_call>', content, re.DOTALL)) or \
               bool(re.search(r'<tool_call>.*', content, re.DOTALL)) # 容错：允许未闭合标签
    
    def _extract_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """从响应中提取所有工具调用"""
        tool_calls = []
        
        # 匹配所有 <tool_call>...</tool_call> 块
        # 使用非贪婪匹配，并尽量匹配闭合标签
        # 如果有多个不带换行符的 tool_call，正则可能需要调整，但通常 LLM 会换行
        pattern = r'<tool_call>(.*?)</tool_call>'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            tool_call_str = match.group(1).strip()
            # 清理常见幻觉
            tool_call_str = tool_call_str.replace("</arg_value>", "").replace("<arg_value>", "")
            tool_call_str = tool_call_str.replace("</tool_code>", "").replace("<tool_code>", "")
            
            try:
                import json5
                try:
                    tool_call_json = json5.loads(tool_call_str)
                except:
                    # 简单修复尝试
                    fixed_str = tool_call_str.strip()
                    if not fixed_str.endswith('}'): fixed_str += '}'
                    tool_call_json = json5.loads(fixed_str)
                
                tool_name = tool_call_json.get("name")
                tool_args = tool_call_json.get("arguments", tool_call_json.get("parameters", {}))
                
                if tool_name:
                    tool_calls.append({
                        "name": tool_name,
                        "arguments": tool_args,
                        "raw": tool_call_str
                    })
            except Exception as e:
                logger.error(f"Failed to parse tool call: {tool_call_str[:50]}... Error: {e}")
                
        # 特殊处理：如果没找到闭合的 tool_call，尝试找未闭合的 (通常是流式输出中断或错误截断)
        if not tool_calls and "<tool_call>" in content:
            # 尝试提取最后一个未闭合的
            last_start = content.rfind("<tool_call>")
            potential_content = content[last_start + 11:].strip()
            if potential_content:
                try:
                    import json5
                    # 尝试补全并解析
                    if not potential_content.endswith('}'): potential_content += '}'
                    tool_call_json = json5.loads(potential_content)
                    if tool_call_json.get("name"):
                        tool_calls.append({
                            "name": tool_call_json.get("name"),
                            "arguments": tool_call_json.get("arguments", {}),
                            "raw": potential_content
                        })
                except: pass

        # 检查 PythonInterpreter 的 code 快捷方式
        # 其实 xSmart 的 PythonInterpreter 并不总是用 <tool_call>，有时用 <code>
        # 这里为了保持兼容性，还是保留 _execute_tool_call 里对 PythonInterpreter 的特殊逻辑吗？
        # 不，_execute_tool_call 即将被废弃。我们需要在这里处理 <code> 块。
        if self.CODE_START in content and self.CODE_END in content:
             # 如果已经通过 tool_call 解析出了 PythonInterpreter 且有 code 参数，则不用重复
             # 如果没有，则添加一个隐式的 PythonInterpreter 调用
             has_pi = any(tc['name'] == 'PythonInterpreter' for tc in tool_calls)
             if not has_pi:
                 code_match = re.search(f"{re.escape(self.CODE_START)}(.*?){re.escape(self.CODE_END)}", content, re.DOTALL)
                 if code_match:
                     code_content = code_match.group(1).strip()
                     tool_calls.append({
                         "name": "PythonInterpreter",
                         "arguments": code_content, # PythonInterpreter tool 接受 string 或 dict
                         "raw": code_content
                     })
        
        return tool_calls
    
    def _count_tokens(self, messages: List[Dict]) -> int:
        """计算消息的 token 数
        
        Args:
            messages: 消息列表
            
        Returns:
            token 数量
        """
        if self.tokenizer is None:
            # 粗略估计：4个字符约等于1个token
            total_chars = sum(len(m.get("content", "")) for m in messages)
            return total_chars // 4
        
        full_text = "\n".join(m.get("content", "") for m in messages)
        tokens = self.tokenizer.encode(full_text)
        return len(tokens)
    
    async def _force_summarize(
        self, 
        messages: List[Dict],
        question: str,
        ground_truth: str,
        start_time: float,
        iterations: int
    ) -> ResearchResult:
        """强制总结（token 超限时使用）"""
        # 添加强制总结提示 (追加新消息，不覆盖原始内容)
        messages.append({"role": "user", "content": FORCE_SUMMARIZE_PROMPT})
        
        # 再次调用 LLM
        response = await self._call_llm(messages)
        messages.append({"role": "assistant", "content": response.strip()})
        
        if self._has_answer(response):
            prediction = self._extract_answer(response)
            termination = "token_limit_forced_answer"
        else:
            prediction = response
            termination = "token_limit_format_error"
        
        return ResearchResult(
            question=question,
            answer=ground_truth,
            prediction=prediction,
            messages=messages,
            termination=termination,
            execution_time=time.time() - start_time,
            iterations=iterations
        )

    def _prune_messages(self, messages: List[Dict]) -> List[Dict]:
        """剪枝消息历史，保留核心上下文"""
        if len(messages) <= 8:
            return messages
            
        # 1. 保留 System Prompt 和原始 User Question
        # 注意：有时候第一个消息不是 system，或者第二个不是 user，但这里做一般性假设
        kept_head = messages[:2]
        
        # 2. 保留最近的 3 次交互 (Assistant + User 共 6 条消息)
        kept_tail = messages[-6:]
        
        # 3. 构造剪枝提示
        pruned_notice = {
            "role": "system", 
            "content": f"[System Note: Earlier conversation turns have been removed to save tokens. Current token usage: {self._count_tokens(kept_head + kept_tail)}]"
        }
        
        return kept_head + [pruned_notice] + kept_tail
