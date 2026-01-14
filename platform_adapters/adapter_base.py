"""
平台适配器基类 - P2 Task 3.1

定义跨平台适配的统一接口,支持多个 AI 平台:
- Claude Code
- OpenAI Codex
- OpenCode
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import os
import subprocess
import re
import fnmatch

logger = logging.getLogger(__name__)


class Platform(Enum):
    """支持的 AI 平台"""
    CLAUDE_CODE = "claude_code"
    OPENAI_CODEX = "openai_codex"
    OPENCODE = "opencode"


@dataclass
class Tool:
    """工具定义"""
    name: str
    description: str
    parameters: Dict[str, Any]
    platform_specific: bool = False


@dataclass
class ToolExecutionResult:
    """工具执行结果"""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class PlatformAdapter(ABC):
    """平台适配器基类 - 定义所有平台适配器必须实现的接口"""

    def __init__(self):
        self.platform_name: str = ""
        self.available_tools: List[Tool] = []
        self.context: Dict[str, Any] = {}

    @abstractmethod
    def get_platform_name(self) -> str:
        """获取平台名称

        Returns:
            str: 平台名称 (例如: "Claude Code", "OpenAI Codex")
        """
        pass

    @abstractmethod
    def get_available_tools(self) -> List[Tool]:
        """获取平台可用的工具列表

        Returns:
            List[Tool]: 工具列表
        """
        pass


    @abstractmethod
    def get_context(self) -> Dict[str, Any]:
        """获取平台上下文信息

        Returns:
            Dict[str, Any]: 上下文信息,可能包含:
                - workspace: 工作区路径
                - environment: 环境变量
                - user_config: 用户配置
                - platform_version: 平台版本
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查平台是否可用

        Returns:
            bool: 如果平台可用返回 True
        """
        pass

    def initialize(self):
        """初始化适配器

        在首次使用时调用,用于设置初始状态
        """
        logger.info(f"初始化平台适配器: {self.get_platform_name()}")
        self.context = self.get_context()
        self.available_tools = self.get_available_tools()

    def execute_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> ToolExecutionResult:
        """执行工具 (通用实现)

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            ToolExecutionResult: 执行结果
        """
        logger.info(f"{self.get_platform_name()} 执行工具: {tool_name}")

        try:
            # 1. 验证参数
            if not self.validate_tool_parameters(tool_name, kwargs):
                return ToolExecutionResult(
                    success=False,
                    result=None,
                    error="参数验证失败",
                    metadata={"tool_name": tool_name}
                )

            # 2. 派发工具执行 (优先尝试子类覆盖的特定派发)
            result = self._dispatch_tool(tool_name, **kwargs)

            # 3. 格式化结果
            return self.format_result(result, tool_name)

        except Exception as e:
            return self.handle_error(e, tool_name)

    def _dispatch_tool(self, tool_name: str, **kwargs) -> Any:
        """工具派发逻辑,子类可覆盖以支持更多工具"""
        # 默认实现: 查找对应的私有方法
        # 注意: 不同平台工具名不同,这里需要根据工具名映射到统一的实现方法
        
        # 映射逻辑示例 (可由 ToolMapper 辅助)
        normalized_name = tool_name.lower()
        
        if normalized_name in ["read", "read_file"]:
            # 处理可能的参数名差异
            path = kwargs.get("file_path") or kwargs.get("file") or kwargs.get("path")
            return self._read_file(path)
        
        elif normalized_name in ["write", "write_file"]:
            path = kwargs.get("file_path") or kwargs.get("file") or kwargs.get("path")
            content = kwargs.get("content") or kwargs.get("contents") or kwargs.get("data")
            return self._write_file(path, content)
            
        elif normalized_name in ["edit", "edit_file"]:
            path = kwargs.get("file_path") or kwargs.get("file") or kwargs.get("path")
            old = kwargs.get("old_str") or kwargs.get("old_text") or kwargs.get("old")
            new = kwargs.get("new_str") or kwargs.get("new_text") or kwargs.get("new")
            return self._edit_file(path, old, new)
            
        elif normalized_name in ["bash", "run_bash", "execute"]:
            cmd = kwargs.get("command") or kwargs.get("cmd")
            return self._run_bash(cmd)
            
        elif normalized_name in ["search", "search_files", "grep"]:
            pattern = kwargs.get("pattern")
            path = kwargs.get("path", ".")
            return self._search_files(pattern, path)
            
        raise ValueError(f"平台 {self.get_platform_name()} 不支持工具: {tool_name}")

    def get_tool_info(self, tool_name: str) -> Optional[Tool]:
        """获取工具信息

        Args:
            tool_name: 工具名称

        Returns:
            Optional[Tool]: 工具定义,如果不存在返回 None
        """
        for tool in self.available_tools:
            if tool.name == tool_name:
                return tool
        return None

    def validate_tool_parameters(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> bool:
        """验证工具参数

        Args:
            tool_name: 工具名称
            parameters: 参数字典

        Returns:
            bool: 如果参数有效返回 True
        """
        tool = self.get_tool_info(tool_name)
        if not tool:
            logger.warning(f"工具不存在: {tool_name}")
            return False

        # 检查必需参数
        required_params = tool.parameters.get("required", [])
        for param in required_params:
            if param not in parameters:
                logger.error(f"缺少必需参数: {param}")
                return False

        return True

    def format_result(
        self,
        result: Any,
        tool_name: str
    ) -> ToolExecutionResult:
        """格式化工具执行结果

        Args:
            result: 原始结果
            tool_name: 工具名称

        Returns:
            ToolExecutionResult: 格式化后的结果
        """
        return ToolExecutionResult(
            success=True,
            result=result,
            metadata={"tool_name": tool_name}
        )

    def handle_error(
        self,
        error: Exception,
        tool_name: str
    ) -> ToolExecutionResult:
        """处理工具执行错误

        Args:
            error: 异常对象
            tool_name: 工具名称

        Returns:
            ToolExecutionResult: 错误结果
        """
        logger.error(f"工具执行失败 {tool_name}: {error}")
        return ToolExecutionResult(
            success=False,
            result=None,
            error=str(error),
            metadata={"tool_name": tool_name}
        )

    # --- 默认工具实现 (可由子类覆盖) ---

    def _read_file(self, file_path: str) -> str:
        """读取文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _write_file(self, file_path: str, content: str) -> str:
        """写入文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"已写入 {len(content)} 字节到 {file_path}"

    def _edit_file(self, file_path: str, old_str: str, new_str: str) -> str:
        """编辑文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if old_str not in content:
            raise ValueError(f"未找到要替换的内容: {old_str[:50]}...")

        content = content.replace(old_str, new_str, 1)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"已替换 {len(old_str)} 字符"

    def _run_bash(self, command: str) -> str:
        """执行 Bash 命令"""
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr

        return output

    def _search_files(self, pattern: str, path: str = ".") -> List[str]:
        """搜索文件"""
        matches = []
        for root, dirs, files in os.walk(path):
            for file in files:
                # 默认搜索 Python 和 Markdown 文件,子类可扩展
                if file.endswith('.py') or file.endswith('.md'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if re.search(pattern, content):
                                matches.append(file_path)
                    except Exception:
                        pass

        return matches


class AdapterFactory:
    """适配器工厂 - 用于创建和管理平台适配器"""

    _adapters: Dict[Platform, PlatformAdapter] = {}

    @classmethod
    def register_adapter(
        cls,
        platform: Platform,
        adapter: PlatformAdapter
    ):
        """注册平台适配器

        Args:
            platform: 平台类型
            adapter: 适配器实例
        """
        cls._adapters[platform] = adapter
        logger.info(f"注册适配器: {platform.value}")

    @classmethod
    def get_adapter(cls, platform: Platform) -> Optional[PlatformAdapter]:
        """获取平台适配器

        Args:
            platform: 平台类型

        Returns:
            Optional[PlatformAdapter]: 适配器实例,如果不存在返回 None
        """
        adapter = cls._adapters.get(platform)
        if adapter:
            if not adapter.context:
                adapter.initialize()
        return adapter

    @classmethod
    def list_supported_platforms(cls) -> List[Platform]:
        """列出所有支持的平台

        Returns:
            List[Platform]: 支持的平台列表
        """
        return list(cls._adapters.keys())

    @classmethod
    def create_auto_adapter(cls) -> Optional[PlatformAdapter]:
        """自动创建当前平台的适配器

        Returns:
            Optional[PlatformAdapter]: 适配器实例,如果检测失败返回 None
        """
        from .platform_detector import PlatformDetector

        detector = PlatformDetector()
        detected_platform = detector.detect_platform()

        if detected_platform:
            return cls.get_adapter(detected_platform)

        logger.error("无法检测当前平台")
        return None
