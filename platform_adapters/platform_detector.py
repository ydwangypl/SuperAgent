"""
平台检测器 - P2 Task 3.1

自动检测当前运行的 AI 平台
"""

import os
import sys
from typing import Optional
from enum import Enum
import logging

from .adapter_base import Platform

logger = logging.getLogger(__name__)


class PlatformDetector:
    """平台检测器 - 自动检测当前运行平台"""

    # 检测优先级 (从高到低)
    DETECTION_PRIORITY = [
        Platform.CLAUDE_CODE,
        Platform.OPENAI_CODEX,
        Platform.OPENCODE,
    ]

    def __init__(self):
        self.cached_platform: Optional[Platform] = None
        self.detection_methods = {
            Platform.CLAUDE_CODE: self._detect_claude_code,
            Platform.OPENAI_CODEX: self._detect_openai_codex,
            Platform.OPENCODE: self._detect_opencode,
        }

    def detect_platform(self) -> Optional[Platform]:
        """检测当前平台

        Returns:
            Optional[Platform]: 检测到的平台,如果无法确定返回 None
        """
        if self.cached_platform:
            return self.cached_platform

        # 按优先级检测
        for platform in self.DETECTION_PRIORITY:
            try:
                detection_method = self.detection_methods[platform]
                if detection_method():
                    self.cached_platform = platform
                    logger.info(f"检测到平台: {platform.value}")
                    return platform
            except Exception as e:
                logger.debug(f"平台 {platform.value} 检测失败: {e}")
                continue

        logger.warning("无法自动检测平台")
        return None

    def _detect_claude_code(self) -> bool:
        """检测是否运行在 Claude Code 上

        Claude Code 特征:
        - 特定的环境变量
        - 特定的模块路径
        - 特定的全局对象
        """
        # 检查环境变量
        if "ANTHROPIC_API_KEY" in os.environ:
            return True

        # 检查是否在 VS Code 扩展中运行
        if "VSCODE_PID" in os.environ or "CODE_PID" in os.environ:
            # 进一步检查是否有 Claude 相关的模块
            try:
                # Claude Code 扩展会注入特定的全局变量
                import sys
                if "claude" in sys.modules or "anthropic" in sys.modules:
                    return True
            except ImportError:
                pass

        # 检查特定的全局对象
        try:
            if "claude_code_integration" in dir():
                return True
        except:
            pass

        return False

    def _detect_openai_codex(self) -> bool:
        """检测是否运行在 OpenAI Codex 上

        OpenAI Codex 特征:
        - OPENAI_API_KEY 环境变量
        - 特定的模块结构
        """
        # 检查 OpenAI API 密钥
        if "OPENAI_API_KEY" in os.environ:
            return True

        # 检查是否有 openai 模块
        try:
            import openai
            # 如果能导入 openai 且没有其他平台的特征
            return True
        except ImportError:
            pass

        return False

    def _detect_opencode(self) -> bool:
        """检测是否运行在 OpenCode (开源兼容平台) 上

        OpenCode 特征:
        - 没有商业平台的特征
        - 有特定的开源项目标识
        """
        # 检查是否是开源项目
        if os.path.exists(".git"):
            # 检查是否是 SuperAgent 自己
            try:
                with open(".git/config", "r", encoding="utf-8") as f:
                    config = f.read()
                    if "superagent" in config.lower():
                        return True
            except:
                pass

        # 检查是否有特定的开源标识
        if os.path.exists("LICENSE"):
            try:
                with open("LICENSE", "r", encoding="utf-8") as f:
                    content = f.read().lower()
                    if "mit" in content or "apache" in content:
                        return True
            except:
                pass

        # 默认情况: 如果没有检测到其他平台,假设是 OpenCode
        return True

    def get_platform_info(self, platform: Platform) -> dict:
        """获取平台信息

        Args:
            platform: 平台类型

        Returns:
            dict: 平台信息
        """
        info = {
            Platform.CLAUDE_CODE: {
                "name": "Claude Code",
                "company": "Anthropic",
                "website": "https://code.anthropic.com",
                "description": "Claude 的官方代码助手平台",
                "features": [
                    "强大的代码理解能力",
                    "多语言支持",
                    "实时协作"
                ]
            },
            Platform.OPENAI_CODEX: {
                "name": "OpenAI Codex",
                "company": "OpenAI",
                "website": "https://openai.com",
                "description": "OpenAI 的代码生成平台",
                "features": [
                    "代码生成",
                    "代码补全",
                    "多语言支持"
                ]
            },
            Platform.OPENCODE: {
                "name": "OpenCode",
                "company": "Community",
                "website": "https://github.com",
                "description": "开源兼容平台",
                "features": [
                    "完全开源",
                    "社区驱动",
                    "可扩展"
                ]
            }
        }

        return info.get(platform, {})

    def is_compatible(self, platform: Platform) -> bool:
        """检查平台是否兼容

        Args:
            platform: 平台类型

        Returns:
            bool: 如果平台兼容返回 True
        """
        # 检查平台是否支持
        if platform not in self.DETECTION_PRIORITY:
            return False

        # 检查是否有必要的依赖
        try:
            detection_method = self.detection_methods[platform]
            return detection_method()
        except Exception as e:
            logger.debug(f"兼容性检查失败 {platform.value}: {e}")
            return False

    def list_compatible_platforms(self) -> list:
        """列出所有兼容的平台

        Returns:
            list: 兼容的平台列表
        """
        compatible = []
        for platform in self.DETECTION_PRIORITY:
            if self.is_compatible(platform):
                compatible.append(platform)
        return compatible
