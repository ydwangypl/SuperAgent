"""
Claude Code 平台适配器 - P2 Task 3.1

实现 Claude Code 平台的具体适配逻辑
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


class ClaudeCodeAdapter(PlatformAdapter):
    """Claude Code 平台适配器"""

    def __init__(self):
        super().__init__()
        self.platform_name = "Claude Code"
        self.tool_mapper = ToolMapper()

    def get_platform_name(self) -> str:
        """获取平台名称"""
        return self.platform_name

    def get_available_tools(self) -> List[Tool]:
        """获取平台可用的工具列表

        Claude Code 提供的工具包括:
        - 文件操作: Read, Write, Edit
        - 搜索: Grep, Glob
        - 执行: Bash
        - 其他: AskUser, Browse 等
        """
        tools = [
            Tool(
                name="read_file",
                description="读取文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径"
                        }
                    },
                    "required": ["file_path"]
                },
                platform_specific=False
            ),
            Tool(
                name="write_file",
                description="写入文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "content": {
                            "type": "string",
                            "description": "文件内容"
                        }
                    },
                    "required": ["file_path", "content"]
                },
                platform_specific=False
            ),
            Tool(
                name="edit_file",
                description="编辑文件 (替换内容)",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "old_str": {
                            "type": "string",
                            "description": "要替换的旧内容"
                        },
                        "new_str": {
                            "type": "string",
                            "description": "新内容"
                        }
                    },
                    "required": ["file_path", "old_str", "new_str"]
                },
                platform_specific=False
            ),
            Tool(
                name="run_bash",
                description="执行 Bash 命令",
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
                platform_specific=True  # Bash 特定于环境
            ),
            Tool(
                name="search_files",
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

        logger.info(f"Claude Code 可用工具数: {len(tools)}")
        return tools

    def get_context(self) -> Dict[str, Any]:
        """获取平台上下文信息"""
        context = {
            "platform": "claude_code",
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
        # 检查是否有 ANTHROPIC_API_KEY
        has_api_key = "ANTHROPIC_API_KEY" in os.environ

        # 检查是否在 VS Code 环境中
        has_vscode = "VSCODE_PID" in os.environ or "CODE_PID" in os.environ

        is_available = has_api_key or has_vscode
        logger.info(f"Claude Code 平台可用性: {is_available}")
        return is_available
