"""
OpenCode 平台适配器 - P2 Task 3.1

实现 OpenCode 社区平台的具体适配逻辑
这是默认的开源平台适配器,用于社区驱动的 AI 编码助手
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


class OpenCodeAdapter(PlatformAdapter):
    """OpenCode 社区平台适配器"""

    def __init__(self):
        super().__init__()
        self.platform_name = "OpenCode"
        self.tool_mapper = ToolMapper()

    def get_platform_name(self) -> str:
        """获取平台名称"""
        return self.platform_name

    def get_available_tools(self) -> List[Tool]:
        """获取平台可用的工具列表

        OpenCode 提供的工具包括:
        - 文件操作: read, write, edit
        - 搜索: grep, glob
        - 执行: bash
        - 其他: git, ask 等
        """
        tools = [
            Tool(
                name="read",
                description="读取文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径"
                        }
                    },
                    "required": ["path"]
                },
                platform_specific=False
            ),
            Tool(
                name="write",
                description="写入文件内容",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "data": {
                            "type": "string",
                            "description": "文件内容"
                        }
                    },
                    "required": ["path", "data"]
                },
                platform_specific=False
            ),
            Tool(
                name="edit",
                description="编辑文件 (替换内容)",
                parameters={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "文件路径"
                        },
                        "old": {
                            "type": "string",
                            "description": "要替换的旧内容"
                        },
                        "new": {
                            "type": "string",
                            "description": "新内容"
                        }
                    },
                    "required": ["path", "old", "new"]
                },
                platform_specific=False
            ),
            Tool(
                name="bash",
                description="执行 Bash 命令",
                parameters={
                    "type": "object",
                    "properties": {
                        "cmd": {
                            "type": "string",
                            "description": "要执行的命令"
                        }
                    },
                    "required": ["cmd"]
                },
                platform_specific=True  # Bash 特定于环境
            ),
            Tool(
                name="grep",
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
            ),
            Tool(
                name="glob",
                description="查找文件路径",
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "文件模式"
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

        logger.info(f"OpenCode 可用工具数: {len(tools)}")
        return tools

    def get_context(self) -> Dict[str, Any]:
        """获取平台上下文信息"""
        context = {
            "platform": "opencode",
            "platform_version": "1.0",
            "workspace": os.getcwd(),
            "environment": os.environ.copy(),
            "capabilities": {
                "file_operations": True,
                "command_execution": True,
                "search": True,
                "git_operations": True
            }
        }
        return context

    def is_available(self) -> bool:
        """检查平台是否可用

        OpenCode 是默认平台,始终可用
        """
        # 检查是否在 Git 仓库中 (开源项目)
        is_git_repo = os.path.exists(".git")

        # 检查是否有 LICENSE 文件
        has_license = os.path.exists("LICENSE")

        # 检查是否有 README 文件
        has_readme = os.path.exists("README.md") or os.path.exists("README.rst")

        # 满足任一条件即认为是 OpenCode 环境
        is_available = is_git_repo or has_license or has_readme

        logger.info(f"OpenCode 平台可用性: {is_available}")
        return is_available
