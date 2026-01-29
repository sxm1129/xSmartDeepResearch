#!/bin/bash

# xSmartDeepResearch 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# 检查环境文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在，正在从 .env.example 复制..."
    cp .env.example .env
    echo "📝 请编辑 .env 文件配置 API Keys 后重新运行"
    exit 1
fi

# 加载环境变量
source .env

# 启动 Gradio Demo
echo "🚀 启动 xSmartDeepResearch Gradio Demo..."
python demo/gradio_demo.py
