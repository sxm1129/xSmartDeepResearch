"""多模态分析工具 - 使用 VLM 分析图像内容"""

import base64
import os
from typing import Dict, Any, List, Optional, Union

from openai import OpenAI
from .base_tool import BaseTool
from config import settings


class ImageAnalysisTool(BaseTool):
    """图像分析工具
    
    使用视觉语言模型 (VLM) 分析图像并回答相关问题。
    """
    
    name = "analyze_image"
    description = "Analyze image(s) and answer questions about their content. Supports URL or local file path."
    parameters = {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The URL(s) or local file path(s) of the image(s) to analyze."
            },
            "prompt": {
                "type": "string",
                "description": "The question or instruction for the image analysis."
            }
        },
        "required": ["image_path", "prompt"]
    }
    
    def __init__(self, client: Optional[OpenAI] = None, model: str = None, cfg: Optional[Dict] = None):
        super().__init__(cfg)
        self.client = client or OpenAI(
            api_key=settings.openrouter_key or settings.api_key,
            base_url=settings.api_base
        )
        self.model = model or settings.multimodal_model_name
    
    def call(self, params: Union[str, Dict[str, Any]], **kwargs) -> str:
        params = self._parse_params(params)
        
        image_paths = params.get("image_path", [])
        prompt = params.get("prompt", "Describe this image in detail.")
        
        if isinstance(image_paths, str):
            image_paths = [image_paths]
            
        if not image_paths:
            return "[analyze_image] No image path provided."
            
        try:
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
            
            for path in image_paths:
                if path.startswith(("http://", "https://")):
                    messages[0]["content"].append({
                        "type": "image_url",
                        "image_url": {"url": path}
                    })
                else:
                    # 本地文件读取并转为 base64
                    base64_image = self._encode_image(path)
                    mime_type = self._get_mime_type(path)
                    messages[0]["content"].append({
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}
                    })
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"[analyze_image] Error: {str(e)}"
    
    def _encode_image(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
            
    def _get_mime_type(self, path: str) -> str:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".png": return "image/png"
        if ext in [".jpg", ".jpeg"]: return "image/jpeg"
        if ext == ".gif": return "image/gif"
        if ext == ".webp": return "image/webp"
        return "image/jpeg"
