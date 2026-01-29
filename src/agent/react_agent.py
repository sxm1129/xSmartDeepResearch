"""xSmartDeepResearch ReAct Agent 核心实现"""

import json
import time
import re
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

from openai import OpenAI

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
        client: OpenAI = None,
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
        """初始化 ReAct Agent
        
        Args:
            client: OpenAI 兼容的客户端
            model: 模型名称
            tools: 工具列表
            max_iterations: 最大迭代次数
            max_tokens: 最大上下文 token 数
            temperature: 采样温度
            top_p: nucleus 采样参数
            presence_penalty: 存在惩罚
            timeout_minutes: 超时分钟数
        """
        # 客户端配置
        self.client = client or OpenAI(
            api_key=settings.api_key,
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
    
    def run(self, question: str, ground_truth: str = "") -> ResearchResult:
        """执行研究任务 (同步版本)"""
        start_time = time.time()
        
        # 使用生成器运行并累积结果
        messages = []
        prediction = ""
        iterations = 0
        termination = "unknown"
        
        for event in self.stream_run(question):
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

    def stream_run(self, question: str):
        """执行研究任务 (流式生成器版本)
        
        Yields:
            Dict[str, Any]: 包含 type 和 content 的事件字典
        """
        start_time = time.time()
        
        # 🟢 步骤 1: 意图识别 (动态人设注入)
        yield {"type": "status", "content": "🔍 Identifying research intent..."}
        # PERSIST: status
        if self.current_session_id:
             self.session_manager.add_message(self.current_session_id, "status", "🔍 Identifying research intent...")

        intent = self.classifier.classify(question)
        category = intent.get("category", "general")
        reason = intent.get("reason", "")
        status_msg = f"🎯 Intent: **{category.upper()}** ({reason})"
        yield {"type": "status", "content": status_msg}
        # PERSIST: status (Create session happens next, so we can't persist this one yet unless we move session creation up. 
        # Actually session creation is the next step. So we should persist this AFTER session creation.)

        # 🔵 步骤 2: 创建会话持久化
        self.current_session_id = self.session_manager.create_session(
            title=question[:50],  # 简单取前50字符作为标题
            intent_category=category,
            project_id=self.current_project_id
        )
        # 记录用户问题
        self.session_manager.add_message(self.current_session_id, "user", question)
        # PERSIST: Delayed status messages
        self.session_manager.add_message(self.current_session_id, "status", status_msg)

        # 构建初始消息
        tool_definitions = [tool.get_function_definition() for tool in self.tools.values()]
        system_prompt = build_system_prompt(tool_definitions, category=category)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
        
        iterations = 0
        
        while iterations < self.max_iterations:
            elapsed_minutes = (time.time() - start_time) / 60
            if elapsed_minutes > self.timeout_minutes:
                yield {"type": "timeout", "content": "Research timeout"}
                return

            iterations += 1
            yield {"type": "status", "content": f"Iteration {iterations}...", "iteration": iterations}
            self.session_manager.add_message(self.current_session_id, "status", f"Iteration {iterations}...")
            
            # 调用 LLM
            response = self._call_llm(messages)
            
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
                    self.session_manager.add_message(self.current_session_id, "thought", think_content)
            
            # 检查是否有最终答案
            if self._has_answer(response):
                prediction = self._extract_answer(response)
                
                # 记录最终答案
                self.session_manager.add_message(self.current_session_id, "answer", prediction)
                
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
            if self._has_tool_call(response):
                # 提取工具名与参数用于状态提示
                tool_match = re.search(r'<tool_call>(.*?)</tool_call>', response, re.DOTALL)
                tool_name = "unknown"
                tool_args = {}
                if tool_match:
                    try:
                        import json5
                        tc_json = json5.loads(tool_match.group(1).strip())
                        tool_name = tc_json.get("name", "tool")
                        tool_args = tc_json.get("arguments", {})
                    except: pass
                
                yield {
                    "type": "tool_start", 
                    "content": f"Calling tool: {tool_name}", 
                    "tool": tool_name,
                    "arguments": tool_args,
                    "iteration": iterations
                }
                
                logger.info(f"🔧 Executing tool: {tool_name} with args: {tool_args}")
                tool_result = self._execute_tool_call(response)
                
                # 记录工具调用的详细信息
                self.session_manager.add_message(
                    self.current_session_id, 
                    "tool", 
                    f"Call: {tool_name}\nArgs: {json.dumps(tool_args, ensure_ascii=False)}\nResult: {tool_result}",
                    metadata={"tool_name": tool_name, "args": tool_args}
                )

                # PERSIST: tool_response
                self.session_manager.add_message(
                    self.current_session_id,
                    "tool_response",
                    tool_result,
                    metadata={"tool_name": tool_name}
                )

                yield {
                    "type": "tool_response", 
                    "content": tool_result, 
                    "tool": tool_name,
                    "iteration": iterations
                }
                
                messages.append({
                    "role": "user",
                    "content": f"{self.TOOL_RESPONSE_START}\n{tool_result}\n{self.TOOL_RESPONSE_END}"
                })
            
            # 检查 token 限制
            token_count = self._count_tokens(messages)
            if token_count > self.max_tokens:
                # 如果还有很多步可以走，尝试剪枝而不是立即总结
                if iterations < self.max_iterations - 3:
                    logger.info(f"Token count {token_count} exceeds {self.max_tokens}. Pruning context.")
                    messages = self._prune_messages(messages)
                    yield {"type": "status", "content": "Context pruned to save tokens."}
                    self.session_manager.add_message(self.current_session_id, "status", "Context pruned to save tokens.")
                else:
                    yield {"type": "status", "content": "Token limit reached, forcing final summary..."}
                    self.session_manager.add_message(self.current_session_id, "status", "Token limit reached, forcing final summary...")
                    res = self._force_summarize(messages, question, "", start_time, iterations)
                    yield {"type": "answer", "content": res.prediction}
                    yield {
                        "type": "final_answer", 
                        "content": res.prediction, 
                        "messages": messages, 
                        "iterations": iterations,
                        "termination": res.termination
                    }
                    return

        yield {"type": "error", "content": "Max iterations exceeded"}
        yield {
            "type": "final_answer", 
            "content": "Max iterations reached without final answer", 
            "messages": messages, 
            "iterations": iterations,
            "termination": "max_iterations_exceeded"
        }

    
    def _call_llm(self, messages: List[Dict], max_retries: int = 10) -> str:
        """调用 LLM
        
        Args:
            messages: 消息历史
            max_retries: 最大重试次数
            
        Returns:
            LLM 响应内容
        """
        base_sleep_time = 1
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
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
                time.sleep(sleep_time)
        
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
    
    def _execute_tool_call(self, content: str) -> str:
        """解析并执行工具调用"""
        # 使用正则表达式提取工具调用内容，处理多种边界情况
        # 使用正则表达式提取工具调用内容，处理多种边界情况
        patterns = [
            r'<tool_call>\s*(.*?)\s*</tool_call>',
            r'<tool_call>(.*?)(?:</tool_call>|$)', # 非贪婪匹配，防止吞掉后面的内容，并允许省略闭合标签
        ]
        
        tool_call_str = ""
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                tool_call_str = match.group(1).strip()
                if tool_call_str: break
        
        if not tool_call_str:
            return "[Error] No valid <tool_call> content found."

        # 清理常见的幻觉标签
        tool_call_str = tool_call_str.replace("</arg_value>", "").replace("<arg_value>", "")
        tool_call_str = tool_call_str.replace("</tool_code>", "").replace("<tool_code>", "")

        try:
            # 尝试解析 JSON
            import json5
            try:
                tool_call_json = json5.loads(tool_call_str)
            except:
                # 简单修复：尝试平衡括号和处理引号
                # 这里只是最简单的启发式修复
                fixed_str = tool_call_str.strip()
                if not fixed_str.endswith('}'): fixed_str += '}'
                tool_call_json = json5.loads(fixed_str)
            
            tool_name = tool_call_json.get("name")
            tool_args = tool_call_json.get("arguments", tool_call_json.get("parameters", {}))
            
            # 特殊处理 PythonInterpreter 快捷调用
            if tool_name == "PythonInterpreter" and "code" not in tool_args and self.CODE_START in content:
                code_start = content.find(self.CODE_START) + len(self.CODE_START)
                code_end = content.find(self.CODE_END)
                if code_end != -1:
                    tool_args = content[code_start:code_end].strip()
            
            if tool_name in self.tools:
                print(f"🔧 Tool Call: {tool_name}")
                return self.tools[tool_name].call(tool_args)
            else:
                return f"[Error] Tool '{tool_name}' not found. Available: {list(self.tools.keys())}"
                
        except Exception as e:
            return f"[Error] Failed to parse tool call JSON: {tool_call_str[:200]}... Error: {str(e)}"
    
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
    
    def _force_summarize(
        self, 
        messages: List[Dict],
        question: str,
        ground_truth: str,
        start_time: float,
        iterations: int
    ) -> ResearchResult:
        """强制总结（token 超限时使用）
        
        Args:
            messages: 当前消息历史
            question: 原始问题
            ground_truth: 参考答案
            start_time: 开始时间
            iterations: 已迭代次数
            
        Returns:
            研究结果
        """
        # 添加强制总结提示
        messages[-1]["content"] = FORCE_SUMMARIZE_PROMPT
        
        # 再次调用 LLM
        response = self._call_llm(messages)
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
