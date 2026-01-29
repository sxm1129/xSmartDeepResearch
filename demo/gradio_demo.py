"""xSmartDeepResearch Gradio Web 演示"""

import sys
import os
import json
import time
import tempfile
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import gradio as gr
from openai import OpenAI
from config import settings
from src.agent import xSmartReactAgent
from src.tools import SearchTool, VisitTool, PythonInterpreterTool, ScholarTool, FileParserTool
from src.utils.session_manager import SessionManager
from src.utils.project_manager import ProjectManager

# 全局 Agent 实例
_agent = None

# Global Project State
_current_project_id = None


def get_agent() -> xSmartReactAgent:
    """获取或创建 Agent 实例"""
    global _agent
    
    if _agent is None:
        # 优先使用 OpenRouter
        api_key = settings.openrouter_key or settings.api_key
        api_base = settings.api_base
        
        client = OpenAI(
            api_key=api_key,
            base_url=api_base,
            timeout=600.0,
            default_headers={
                "HTTP-Referer": "https://github.com/sxm1129/DeepResearch", 
                "X-Title": "xSmartDeepResearch", 
            }
        )
        
        summary_client = OpenAI(
            api_key=api_key,
            base_url=api_base,
            timeout=60.0
        )
        
        tools = []
        
        if settings.serper_api_key:
            tools.append(SearchTool(api_key=settings.serper_api_key))
            tools.append(ScholarTool(api_key=settings.serper_api_key))
        
        if settings.jina_api_key:
            tools.append(VisitTool(
                jina_api_key=settings.jina_api_key,
                summary_client=summary_client,
                summary_model=settings.summary_model_name
            ))
        
        tools.append(PythonInterpreterTool(
            sandbox_endpoints=settings.sandbox_endpoints_list
        ))
        tools.append(FileParserTool())
        
        _agent = xSmartReactAgent(
            client=client,
            model=settings.model_name,
            tools=tools
        )
    
    return _agent


def research(question: str, max_iterations: int = 50):
    """执行流式研究并更新 UI"""
    print(f"\n[DEMO] Research requested: {question[:50]}...")
    if not question.strip():
        yield "请输入问题", "", "", None
        return
    
    agent = get_agent()
    agent.max_iterations = max_iterations
    
    print(f"[DEMO] Agent iterations set to {max_iterations}")
    answer = ""
    reasoning = ""
    status_updates = "🚀 研究任务已提交，正在初始化环境...\n"
    print("[DEMO] Yielding initial status...")
    yield answer, reasoning, status_updates, None
    
    try:
        start_time = time.time()
        print("[DEMO] Calling agent.stream_run...")
        for event in agent.stream_run(question):
            event_type = event.get("type")
            content = event.get("content", "")
            iteration = event.get("iteration", "?")
            now = datetime.now().strftime("%H:%M:%S")
            print(f"[{now}] [DEMO] Event received: {event_type}")
            
            if event_type == "think":
                reasoning += f"\n---\n**思考 {int(time.time()-start_time)}s**:\n{content}\n"
            elif event_type == "status":
                status_updates += f"[{now}] ℹ️ {content}\n"
            elif event_type == "tool_start":
                tool_name = event.get("tool", "tool")
                tool_args = event.get("arguments", {})
                args_str = json.dumps(tool_args, ensure_ascii=False)
                status_updates += f"[{now}] [迭代 {iteration}] 🔧 启动工具: `{tool_name}`\n    └─ 参数: {args_str}\n"
            elif event_type == "tool_response":
                tool_name = event.get("tool", "tool")
                # 提取摘要显示 (适当放开截断长度)
                res_str = str(content)
                if len(res_str) > 1500:
                    summary = res_str[:1500] + "... (已截断，详见报告或推理详情)"
                else:
                    summary = res_str
                status_updates += f"[{now}] [迭代 {iteration}] ✅ `{tool_name}` 返回成功\n    └─ 结果概要: {summary}\n"
            elif event_type == "answer":
                answer = content
            elif event_type == "final_answer":
                exec_time = time.time() - start_time
                status_updates += f"\n[{now}] 🏁 **研究圆满完成！**\n"
                status_updates += f"- 总耗时: {exec_time:.1f}s\n"
                status_updates += f"- 迭代次数: {event.get('iterations')}\n"
                status_updates += f"- 结束原因: {event.get('termination')}\n"
            elif event_type == "error":
                status_updates += f"[{now}] ❌ 错误: {content}\n"
            
            # 如果还没有最终答案，在报告区显示进度提示
            display_answer = answer if answer else f"### ⏳ 研究正在进行中...\n\n> 当前状态: {status_updates.splitlines()[-1] if status_updates.strip() else '初始化'}\n\n*请通过「执行日志」查看完整步骤。*"
            
            yield display_answer, reasoning, status_updates, None
            
        # 生成下载链接文件路径
        if answer:
            ts = int(time.time())
            filename = f"research_result_{ts}.md"
            filepath = os.path.join(tempfile.gettempdir(), filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# 研究课题: {question}\n\n## 研究结论\n{answer}\n\n## 推理过程\n{reasoning}")
            yield answer, reasoning, status_updates, filepath
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        yield f"⚠️ 错误发生: {str(e)}", reasoning, status_updates, None


def get_projects():
    """获取项目列表 for Dropdown"""
    pm = ProjectManager()
    projects = pm.list_projects()
    if not projects:
         # Consider ensuring default project here if list is empty, though migrate_legacy should have run.
         pm.ensure_default_project()
         projects = pm.list_projects()
    # 返回列表格式 [(Name, ID), ...]
    return [(p['name'], p['id']) for p in projects]


def create_new_project(name, desc):
    """创建新项目"""
    if not name:
        return gr.update(), "Please enter a project name."
    pm = ProjectManager()
    pid = pm.create_project(name, desc)
    if pid:
        return gr.Dropdown(choices=get_projects(), value=pid), f"✅ Project '{name}' created!"
    else:
        return gr.update(), "❌ Failed to create project."


def refresh_session_list(project_id):
    """根据 Project ID 刷新 Session 列表"""
    if not project_id:
        return []
    
    pm = ProjectManager()
    sessions = pm.get_project_sessions(project_id)
    result = []
    for s in sessions:
        title = s['title'] or "Untitled"
        time_str = s['updated_at'].split("T")[0]
        result.append([s['id'], f"{time_str} | {title}"])
    return result


def on_project_select(project_id):
    """选择项目后触发"""
    global _current_project_id
    _current_project_id = project_id
    return refresh_session_list(project_id)


def load_history_session(evt: gr.SelectData, history_list):
    """加载选中的历史会话"""
    try:
        if not evt or not evt.index: return "", "", "请选择一个会话"
        selected_index = evt.index[0]
        # history_list is a dataframe, data is in 'value' if not raw, usually gr.Dataframe returns data in structure
        # evt.index is [row, col]
        # history_list input from state is just list, but from Dataframe interactive is different
        # Let's rely on the dataframe 'value' passed as input
        
        # If history_list is passed from the component input, it is a Dataframe object (pandas or list of lists)
        # Gradio DataFrame 'value' is list of lists
        
        session_id = history_list.iloc[selected_index][0] if hasattr(history_list, 'iloc') else history_list['data'][selected_index][0]
        
        sm = SessionManager()
        history = sm.get_session_history(session_id)
        
        answer = ""
        reasoning = ""
        updates = f"📝 Loaded Session: {session_id}\n"
        
        for msg in history:
            role = msg['role']
            content = msg['content']
            meta = msg['metadata'] or {}
            timestamp = msg.get('created_at', '')
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%H:%M:%S")
            elif isinstance(timestamp, str) and 'T' in timestamp:
                 # Simple isoformat parse
                 try:
                     timestamp = timestamp.split('T')[1].split('.')[0]
                 except:
                     pass

            time_prefix = f"[{timestamp}] " if timestamp else ""
            
            if role == "user":
                updates += f"{time_prefix}❓ 用户问题: {content}\n"
            elif role == "thought":
                reasoning += f"{content}\n\n"
            elif role == "tool":
                tool_name = meta.get('tool_name', 'tool')
                tool_args = meta.get('args', {})
                args_str = json.dumps(tool_args, ensure_ascii=False) if tool_args else ""
                updates += f"{time_prefix}🔧 工具调用: {tool_name}\n    └─ 参数: {args_str}\n"
            elif role == "tool_response":
                updates += f"{time_prefix}✅ 工具返回: {content}\n"
            elif role == "status": # If we store status updates
                updates += f"{time_prefix}ℹ️ {content}\n"
            elif role == "system":
                updates += f"{time_prefix}🖥️ 系统: {content}\n"
            elif role == "answer":
                answer = content
                updates += f"{time_prefix}🏁 由于达到目标或迭代限制，研究结束。\n"
        
        # Fallback: If no status messages found (old sessions?), try to infer from what we have
        
        return answer, reasoning, updates
    except Exception as e:
        return "", "", f"❌ Load failed: {e}"


def research_shim(project_id, question, max_iter):
    """包装 research 函数以注入 Project Context"""
    if not project_id:
        yield "", "", "❌ 请先在左侧选择或创建一个项目 (Project)。", None
        return

    # 注入 Project Context
    pm = ProjectManager()
    context = pm.get_project_context(project_id)
    if context:
        print(f"[Project Context] Injecting {len(context)} chars")
    
    # 修改 Agent 实例的 current_project_id 属性
    agent = get_agent()
    agent.current_project_id = project_id 
    
    yield from research(question, max_iterations=max_iter)


def create_demo():
    """创建 Gradio 界面 (Premium 版)"""
    custom_css = """
    .container { max-width: 1400px; margin: auto; }
    .main-header { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    """
    
    with gr.Blocks(title="xSmartDeepResearch Pro", css=custom_css, theme=gr.themes.Soft(primary_hue="purple")) as demo:
        
        with gr.Row(elem_classes="container"):
            # 👈 左侧边栏：项目与会话管理
            with gr.Column(scale=1, min_width=300, variant="panel"):
                gr.Markdown("### 🗂️ 项目空间 (Workspaces)")
                
                with gr.Group():
                    project_dropdown = gr.Dropdown(
                        choices=[],  # Init empty, load on load
                        label="选择当前项目", 
                        interactive=True
                    )
                    with gr.Accordion("➕ 新建项目", open=False):
                        new_proj_name = gr.Textbox(label="项目名称", placeholder="e.g. 2024新能源调研")
                        new_proj_desc = gr.Textbox(label="描述", placeholder="可选")
                        create_proj_btn = gr.Button("创建", size="sm")
                        create_msg = gr.Markdown()

                gr.Markdown("---")
                gr.Markdown("### 📄 会话历史")
                refresh_sess_btn = gr.Button("🔄 刷新会话", size="sm")
                session_list = gr.DataFrame(
                    headers=["ID", "最近会话"],
                    datatype=["str", "str"],
                    interactive=False,
                    visible=True,
                    column_widths=["0%", "100%"]
                )

            # 👉 右侧主区域
            with gr.Column(scale=4):
                gr.HTML("""
                <div class="main-header">
                    <h1>🔬 xSmartDeepResearch</h1>
                    <p>项目化深度研究 · 知识上下文共享 · 专家矩阵</p>
                </div>
                """)
                
                with gr.Row():
                    with gr.Column(scale=3):
                        input_text = gr.Textbox(
                            label="💡 研究课题",
                            placeholder="在该项目背景下，请输入您的研究问题...",
                            lines=3
                        )
                    with gr.Column(scale=1):
                        max_iter_slider = gr.Slider(minimum=5, maximum=100, value=30, label="最大深度")
                        run_btn = gr.Button("🚀 开始研究", variant="primary")
                        stop_btn = gr.Button("🛑 停止")

                with gr.Tabs():
                    with gr.TabItem("📊 最终研报"):
                        md_output = gr.Markdown(label="报告内容")
                        file_output = gr.File(label="📥 下载报告")
                    with gr.TabItem("🧠 专家思维链"):
                        reasoning_output = gr.Markdown(label="思维过程")
                    with gr.TabItem("📅 执行日志"):
                        log_output = gr.Textbox(label="实时日志", lines=15, interactive=False)

        # =========================================================================
        # 事件绑定
        # =========================================================================
        
        # 1. 项目管理
        create_proj_btn.click(
            fn=create_new_project,
            inputs=[new_proj_name, new_proj_desc],
            outputs=[project_dropdown, create_msg]
        )
        
        project_dropdown.change(
            fn=on_project_select,
            inputs=[project_dropdown],
            outputs=[session_list]
        )
        
        refresh_sess_btn.click(
            fn=refresh_session_list,
            inputs=[project_dropdown],
            outputs=[session_list]
        )

        # 2. 运行研究 (使用 shim 包装)
        research_event = run_btn.click(
            fn=research_shim, # Use shim to handle project context
            inputs=[project_dropdown, input_text, max_iter_slider],
            outputs=[md_output, reasoning_output, log_output, file_output]
        )
        
        # 研究完成后刷新列表
        research_event.then(
            fn=refresh_session_list,
            inputs=[project_dropdown],
            outputs=[session_list]
        )
        
        stop_btn.click(fn=None, cancels=[research_event])
        
        # 3. 加载历史
        session_list.select(
            fn=load_history_session,
            inputs=[session_list], # Pass the dataframe component itself to get data
            outputs=[md_output, reasoning_output, log_output]
        )
        
        # 初始化
        def init_view():
            projs = get_projects()
            default_proj = projs[0][1] if projs else None
            # Need to manually trigger project select logic if default exists
            if default_proj:
                on_project_select(default_proj)
                return gr.Dropdown(choices=projs, value=default_proj), refresh_session_list(default_proj)
            return gr.Dropdown(choices=projs, value=None), []

        demo.load(
            fn=init_view,
            outputs=[project_dropdown, session_list]
        )

    return demo


if __name__ == "__main__":
    # 确保 temp 目录存在
    os.makedirs(tempfile.gettempdir(), exist_ok=True)
    
    # 定义高级 CSS - Reused in create_demo now or passed here? 
    # Actually passed in create_demo.
    
    demo = create_demo()
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False, 
        # Theme and css are already set in Blocks
    )
