"""
工具映射器 - P2 Task 3.1

实现不同平台之间的工具名称和参数映射:
- 工具名称映射 (Claude Code ↔ OpenAI ↔ OpenCode)
- 参数格式转换
- 结果格式统一
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolMapping:
    """工具映射定义"""
    source_platform: str  # 源平台
    target_platform: str  # 目标平台
    tool_name: str        # 源平台工具名
    mapped_name: str      # 目标平台工具名
    parameter_map: Dict[str, str]  # 参数名映射
    parameter_transforms: Dict[str, Any]  # 参数转换规则


class ToolMapper:
    """工具映射器 - 处理跨平台工具调用转换"""

    def __init__(self):
        # 定义工具映射规则
        self.mappings: Dict[str, ToolMapping] = {}
        self._initialize_mappings()

    def _initialize_mappings(self):
        """初始化工具映射规则"""

        # Claude Code ↔ OpenAI Codex 映射
        self._register_mapping(
            source_platform="claude_code",
            target_platform="openai_codex",
            tool_name="read_file",
            mapped_name="read",
            parameter_map={
                "file_path": "file"
            }
        )

        self._register_mapping(
            source_platform="claude_code",
            target_platform="openai_codex",
            tool_name="write_file",
            mapped_name="write",
            parameter_map={
                "file_path": "file",
                "content": "contents"
            }
        )

        self._register_mapping(
            source_platform="claude_code",
            target_platform="openai_codex",
            tool_name="edit_file",
            mapped_name="edit",
            parameter_map={
                "file_path": "file",
                "old_str": "old_text",
                "new_str": "new_text"
            }
        )

        self._register_mapping(
            source_platform="claude_code",
            target_platform="openai_codex",
            tool_name="run_bash",
            mapped_name="execute",
            parameter_map={
                "command": "command"
            }
        )

        self._register_mapping(
            source_platform="claude_code",
            target_platform="openai_codex",
            tool_name="search_files",
            mapped_name="search",
            parameter_map={
                "pattern": "pattern",
                "path": "path"
            }
        )

        # OpenAI Codex ↔ Claude Code 映射
        self._register_mapping(
            source_platform="openai_codex",
            target_platform="claude_code",
            tool_name="read",
            mapped_name="read_file",
            parameter_map={
                "file": "file_path"
            }
        )

        self._register_mapping(
            source_platform="openai_codex",
            target_platform="claude_code",
            tool_name="write",
            mapped_name="write_file",
            parameter_map={
                "file": "file_path",
                "contents": "content"
            }
        )

        self._register_mapping(
            source_platform="openai_codex",
            target_platform="claude_code",
            tool_name="edit",
            mapped_name="edit_file",
            parameter_map={
                "file": "file_path",
                "old_text": "old_str",
                "new_text": "new_str"
            }
        )

        self._register_mapping(
            source_platform="openai_codex",
            target_platform="claude_code",
            tool_name="execute",
            mapped_name="run_bash",
            parameter_map={
                "command": "command"
            }
        )

        self._register_mapping(
            source_platform="openai_codex",
            target_platform="claude_code",
            tool_name="search",
            mapped_name="search_files",
            parameter_map={
                "pattern": "pattern",
                "path": "path"
            }
        )

        # Claude Code ↔ OpenCode 映射
        self._register_mapping(
            source_platform="claude_code",
            target_platform="opencode",
            tool_name="read_file",
            mapped_name="read",
            parameter_map={
                "file_path": "path"
            }
        )

        self._register_mapping(
            source_platform="claude_code",
            target_platform="opencode",
            tool_name="write_file",
            mapped_name="write",
            parameter_map={
                "file_path": "path",
                "content": "data"
            }
        )

        self._register_mapping(
            source_platform="claude_code",
            target_platform="opencode",
            tool_name="edit_file",
            mapped_name="edit",
            parameter_map={
                "file_path": "path",
                "old_str": "old",
                "new_str": "new"
            }
        )

        self._register_mapping(
            source_platform="claude_code",
            target_platform="opencode",
            tool_name="run_bash",
            mapped_name="bash",
            parameter_map={
                "command": "cmd"
            }
        )

        self._register_mapping(
            source_platform="claude_code",
            target_platform="opencode",
            tool_name="search_files",
            mapped_name="grep",
            parameter_map={
                "pattern": "pattern",
                "path": "path"
            }
        )

        # OpenCode ↔ Claude Code 映射
        self._register_mapping(
            source_platform="opencode",
            target_platform="claude_code",
            tool_name="read",
            mapped_name="read_file",
            parameter_map={
                "path": "file_path"
            }
        )

        self._register_mapping(
            source_platform="opencode",
            target_platform="claude_code",
            tool_name="write",
            mapped_name="write_file",
            parameter_map={
                "path": "file_path",
                "data": "content"
            }
        )

        self._register_mapping(
            source_platform="opencode",
            target_platform="claude_code",
            tool_name="edit",
            mapped_name="edit_file",
            parameter_map={
                "path": "file_path",
                "old": "old_str",
                "new": "new_str"
            }
        )

        self._register_mapping(
            source_platform="opencode",
            target_platform="claude_code",
            tool_name="bash",
            mapped_name="run_bash",
            parameter_map={
                "cmd": "command"
            }
        )

        self._register_mapping(
            source_platform="opencode",
            target_platform="claude_code",
            tool_name="grep",
            mapped_name="search_files",
            parameter_map={
                "pattern": "pattern",
                "path": "path"
            }
        )

    def _register_mapping(
        self,
        source_platform: str,
        target_platform: str,
        tool_name: str,
        mapped_name: str,
        parameter_map: Dict[str, str],
        parameter_transforms: Optional[Dict[str, Any]] = None
    ):
        """注册工具映射

        Args:
            source_platform: 源平台
            target_platform: 目标平台
            tool_name: 源工具名
            mapped_name: 目标工具名
            parameter_map: 参数名映射
            parameter_transforms: 参数转换规则
        """
        key = f"{source_platform}:{target_platform}:{tool_name}"
        mapping = ToolMapping(
            source_platform=source_platform,
            target_platform=target_platform,
            tool_name=tool_name,
            mapped_name=mapped_name,
            parameter_map=parameter_map,
            parameter_transforms=parameter_transforms or {}
        )
        self.mappings[key] = mapping
        logger.debug(f"注册工具映射: {key}")

    def map_tool_name(
        self,
        tool_name: str,
        source_platform: str,
        target_platform: str
    ) -> str:
        """映射工具名称

        Args:
            tool_name: 源平台工具名
            source_platform: 源平台
            target_platform: 目标平台

        Returns:
            str: 目标平台工具名,如果未找到映射返回原工具名
        """
        key = f"{source_platform}:{target_platform}:{tool_name}"
        mapping = self.mappings.get(key)

        if mapping:
            logger.debug(f"工具名映射: {tool_name} -> {mapping.mapped_name}")
            return mapping.mapped_name

        # 尝试通用映射
        if tool_name == source_platform:
            return target_platform

        # 未找到映射,返回原名称
        logger.warning(f"未找到工具映射: {key}, 使用原名称")
        return tool_name

    def map_parameters(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        source_platform: str,
        target_platform: str
    ) -> Dict[str, Any]:
        """映射工具参数

        Args:
            tool_name: 源平台工具名
            parameters: 源平台参数
            source_platform: 源平台
            target_platform: 目标平台

        Returns:
            Dict[str, Any]: 目标平台参数
        """
        key = f"{source_platform}:{target_platform}:{tool_name}"
        mapping = self.mappings.get(key)

        if not mapping:
            # 没有映射,返回原参数
            return parameters

        # 应用参数名映射
        mapped_params = {}
        for source_param, source_value in parameters.items():
            # 查找映射后的参数名
            target_param = mapping.parameter_map.get(source_param, source_param)
            mapped_params[target_param] = source_value

        # 应用参数转换规则
        if mapping.parameter_transforms:
            mapped_params = self._apply_transforms(
                mapped_params,
                mapping.parameter_transforms
            )

        logger.debug(f"参数映射: {parameters} -> {mapped_params}")
        return mapped_params

    def _apply_transforms(
        self,
        parameters: Dict[str, Any],
        transforms: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用参数转换规则

        Args:
            parameters: 原始参数
            transforms: 转换规则

        Returns:
            Dict[str, Any]: 转换后的参数
        """
        result = parameters.copy()

        for param, transform in transforms.items():
            if param in result:
                try:
                    # 应用转换函数
                    if callable(transform):
                        result[param] = transform(result[param])
                    # 应用类型转换
                    elif isinstance(transform, type):
                        result[param] = transform(result[param])
                    # 应用值映射
                    elif isinstance(transform, dict):
                        original_value = result[param]
                        result[param] = transform.get(original_value, original_value)
                except Exception as e:
                    logger.error(f"参数转换失败 {param}: {e}")

        return result

    def map_result(
        self,
        tool_name: str,
        result: Any,
        source_platform: str,
        target_platform: str
    ) -> Any:
        """映射工具执行结果

        Args:
            tool_name: 工具名
            result: 源平台结果
            source_platform: 源平台
            target_platform: 目标平台

        Returns:
            Any: 目标平台格式的结果
        """
        # 大多数情况下,结果格式可以直接使用
        # 如果需要特殊转换,可以在这里添加逻辑

        # 示例: 将不同平台的错误格式统一
        if isinstance(result, dict):
            # 标准化错误信息
            if "error" in result and "message" not in result:
                result["message"] = result["error"]
            elif "failure" in result:
                result["error"] = result["failure"]
                result["message"] = result.get("description", "Unknown error")

        return result

    def get_mapping_info(
        self,
        tool_name: str,
        source_platform: str,
        target_platform: str
    ) -> Optional[ToolMapping]:
        """获取工具映射信息

        Args:
            tool_name: 源平台工具名
            source_platform: 源平台
            target_platform: 目标平台

        Returns:
            Optional[ToolMapping]: 映射信息,如果不存在返回 None
        """
        key = f"{source_platform}:{target_platform}:{tool_name}"
        return self.mappings.get(key)

    def has_mapping(
        self,
        tool_name: str,
        source_platform: str,
        target_platform: str
    ) -> bool:
        """检查是否存在工具映射

        Args:
            tool_name: 源平台工具名
            source_platform: 源平台
            target_platform: 目标平台

        Returns:
            bool: 如果存在映射返回 True
        """
        key = f"{source_platform}:{target_platform}:{tool_name}"
        return key in self.mappings

    def list_mappings_for_platforms(
        self,
        source_platform: str,
        target_platform: str
    ) -> List[ToolMapping]:
        """列出两个平台之间的所有映射

        Args:
            source_platform: 源平台
            target_platform: 目标平台

        Returns:
            List[ToolMapping]: 映射列表
        """
        prefix = f"{source_platform}:{target_platform}:"
        return [
            mapping for key, mapping in self.mappings.items()
            if key.startswith(prefix)
        ]

    def add_custom_mapping(
        self,
        source_platform: str,
        target_platform: str,
        tool_name: str,
        mapped_name: str,
        parameter_map: Dict[str, str],
        parameter_transforms: Optional[Dict[str, Any]] = None
    ):
        """添加自定义工具映射

        允许用户在运行时添加新的工具映射

        Args:
            source_platform: 源平台
            target_platform: 目标平台
            tool_name: 源工具名
            mapped_name: 目标工具名
            parameter_map: 参数名映射
            parameter_transforms: 参数转换规则
        """
        self._register_mapping(
            source_platform=source_platform,
            target_platform=target_platform,
            tool_name=tool_name,
            mapped_name=mapped_name,
            parameter_map=parameter_map,
            parameter_transforms=parameter_transforms
        )
        logger.info(f"添加自定义映射: {source_platform}:{target_platform}:{tool_name}")

    def remove_mapping(
        self,
        source_platform: str,
        target_platform: str,
        tool_name: str
    ):
        """移除工具映射

        Args:
            source_platform: 源平台
            target_platform: 目标平台
            tool_name: 源工具名
        """
        key = f"{source_platform}:{target_platform}:{tool_name}"
        if key in self.mappings:
            del self.mappings[key]
            logger.info(f"移除工具映射: {key}")
        else:
            logger.warning(f"工具映射不存在: {key}")
