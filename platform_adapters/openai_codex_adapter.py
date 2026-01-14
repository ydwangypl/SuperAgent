"""
OpenAI Codex 平台适配器 - P2 Task 3.1

实现 OpenAI Codex 平台的具体适配逻辑
"""

import os
from typing import List, Dict, Any, Optional
from platform_adapters.adapter_base import (
    PlatformAdapter,
    Platform,
    Tool,
    ToolExecutionResult
)
from platform_adapters.tool_mapper import ToolMapper
import logging

logger = logging.getLogger(__name__)


class OpenAICodexAdapter(PlatformAdapter):
    """OpenAI Codex 平台适配器"""

    def __init__(self):
        super().__init__()
        self.platform_name = "OpenAI Codex"
        self.tool_mapper = ToolMapper()

    def get_platform_name(self) -> str:
        """获取平台名称"""
        return self.platform_name

    def get_available_tools(self) -> List[Tool]:
        """获取平台可用的工具列表

        OpenAI Codex 提供的工具包括:
        - 文件操作: read, write, edit
        - 搜索: search
        - 执行: execute
        - 其他: browse, ask 等
        """
        tools = [
            Tool(
                name="read",
                description="读取文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "file": {
                            "type": "string",
                            "description": "文件路径"
                        }
                    },
                    "required": ["file"]
                },
                platform_specific=False
            ),
            Tool(
                name="write",
                description="写入文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "file": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "contents": {
                            "type": "string",
                            "description": "文件内容"
                        }
                    },
                    "required": ["file", "contents"]
                },
                platform_specific=False
            ),
            Tool(
                name="edit",
                description="编辑文件 (查找替换)",
                parameters={
                    "type": "object",
                    "properties": {
                        "file": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "old_text": {
                            "type": "string",
                            "description": "要查找的旧文本"
                        },
                        "new_text": {
                            "type": "string",
                            "description": "新文本"
                        }
                    },
                    "required": ["file", "old_text", "new_text"]
                },
                platform_specific=False
            ),
            Tool(
                name="execute",
                description="执行命令",
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "要执行的命令"
                        }
                    },
                    "required": ["command"]
                },
                platform_specific=True  # 执行命令特定于环境
            ),
            Tool(
                name="search",
                description="搜索文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "搜索模式"
                        },
                        "path": {
                            "type": "string",
                            "description": "搜索路径"
                        }
                    },
                    "required": ["pattern"]
                },
                platform_specific=False
            )
        ]

        logger.info(f"OpenAI Codex 可用工具数: {len(tools)}")
        return tools

    def get_context(self) -> Dict[str, Any]:
        """获取平台上下文信息"""
        context = {
            "platform": "openai_codex",
            "platform_version": "1.0",
            "workspace": os.getcwd(),
            "environment": os.environ.copy(),
            "capabilities": {
                "file_operations": True,
                "command_execution": True,
                "search": True
            }
        }
        return context

    def is_available(self) -> bool:
        """检查平台是否可用"""
        # 检查是否有 OPENAI_API_KEY
        has_api_key = "OPENAI_API_KEY" in os.environ

        # 检查是否能导入 openai 模块
        has_openai = False
        try:
            import openai
            has_openai = True
        except ImportError:
            pass

        is_available = has_api_key and has_openai
        logger.info(f"OpenAI Codex 平台可用性: {is_available}")
        return is_available
