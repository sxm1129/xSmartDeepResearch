"""xSmartDeepResearch 命令行演示"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from config import settings
from src.agent import xSmartReactAgent
from src.tools import SearchTool, VisitTool, PythonInterpreterTool, ScholarTool


def create_agent() -> xSmartReactAgent:
    """创建研究代理"""
    
    # 创建 OpenAI 客户端
    client = OpenAI(
        api_key=settings.api_key,
        base_url=settings.api_base,
        timeout=600.0
    )
    
    # 创建用于摘要的客户端
    summary_client = OpenAI(
        api_key=settings.api_key,
        base_url=settings.api_base,
        timeout=60.0
    )
    
    # 初始化工具
    tools = []
    
    # 搜索工具
    if settings.serper_api_key:
        tools.append(SearchTool(api_key=settings.serper_api_key))
        tools.append(ScholarTool(api_key=settings.serper_api_key))
        print("✓ Search and Scholar tools enabled")
    else:
        print("✗ Search tools disabled (no SERPER_API_KEY)")
    
    # 网页访问工具
    if settings.jina_api_key:
        tools.append(VisitTool(
            jina_api_key=settings.jina_api_key,
            summary_client=summary_client,
            summary_model=settings.summary_model_name
        ))
        print("✓ Visit tool enabled")
    else:
        print("✗ Visit tool disabled (no JINA_API_KEY)")
    
    # Python 执行工具
    tools.append(PythonInterpreterTool(
        sandbox_endpoints=settings.sandbox_endpoints_list
    ))
    if settings.sandbox_endpoints_list:
        print(f"✓ Python tool enabled (sandbox: {len(settings.sandbox_endpoints_list)} endpoints)")
    else:
        print("✓ Python tool enabled (local execution mode)")
    
    # 创建 Agent
    agent = xSmartReactAgent(
        client=client,
        model=settings.model_name,
        tools=tools
    )
    
    return agent


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🔬 xSmartDeepResearch - 智能深度研究系统")
    print("="*60)
    print(f"Model: {settings.model_name}")
    print(f"Max iterations: {settings.max_llm_call_per_run}")
    print(f"Max tokens: {settings.max_context_tokens}")
    print("="*60 + "\n")
    
    # 创建 Agent
    agent = create_agent()
    
    print("\n输入你的问题开始研究 (输入 'quit' 退出):\n")
    
    while True:
        try:
            question = input("📝 问题: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 再见!")
                break
            
            print("\n🔍 开始研究...\n")
            
            # 执行研究
            result = agent.run(question)
            
            print("\n" + "="*60)
            print("📊 研究结果")
            print("="*60)
            print(f"\n✅ 答案:\n{result.prediction}")
            print(f"\n📈 统计:")
            print(f"  - 迭代次数: {result.iterations}")
            print(f"  - 执行时间: {result.execution_time:.2f} 秒")
            print(f"  - 终止原因: {result.termination}")
            print("="*60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 再见!")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}\n")


if __name__ == "__main__":
    main()
