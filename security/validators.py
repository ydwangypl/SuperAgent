#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
输入验证模块

提供任务请求、配置等输入的验证功能。
"""

from typing import Any, Dict, List, Optional, Set
from pathlib import Path
from pydantic import BaseModel, field_validator, model_validator
from common.exceptions import ValidationError


# 有效的任务类型
VALID_TASK_TYPES: Set[str] = {
    "coding", "research", "review", "planning", "analysis"
}

# 有效的 Agent 类型
VALID_AGENT_TYPES: Set[str] = {
    "FULL_STACK_DEV", "BACKEND_DEV", "FRONTEND_DEV", "CODE_REVIEW",
    "API_DESIGN", "QA_ENGINEERING", "DEVOPS", "PRODUCT_MANAGER",
    "ARCHITECT", "DATA_ARCHITECT", "RESEARCHER", "WRITING_AGENT"
}

# 最大描述长度
MAX_DESCRIPTION_LENGTH = 10000

# 有效的内容类型
VALID_CONTENT_TYPES: Set[str] = {
    "code", "coding", "python", "javascript", "typescript",
    "markdown", "json", "text", "html", "css"
}


class TaskRequest(BaseModel):
    """任务请求验证模型"""

    task_type: str
    description: str
    agent_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("task_type")
    @classmethod
    def validate_task_type(cls, v: str) -> str:
        if v not in VALID_TASK_TYPES:
            raise ValueError(
                f"Invalid task_type: {v}. "
                f"Must be one of: {', '.join(sorted(VALID_TASK_TYPES))}"
            )
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be empty")
        if len(v) > MAX_DESCRIPTION_LENGTH:
            raise ValueError(
                f"Description too long (max {MAX_DESCRIPTION_LENGTH} chars)"
            )
        return v.strip()

    @field_validator("agent_type")
    @classmethod
    def validate_agent_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_AGENT_TYPES:
            raise ValueError(
                f"Invalid agent_type: {v}. "
                f"Must be one of: {', '.join(sorted(VALID_AGENT_TYPES))}"
            )
        return v


class ReviewRequest(BaseModel):
    """代码审查请求验证模型"""

    content: str
    language: str = "python"
    config: Optional[Dict[str, Any]] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be empty")
        if len(v) > 500000:  # 500KB max
            raise ValueError("Content too large (max 500KB)")
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return v.lower().strip()


class TestRequest(BaseModel):
    """测试请求验证模型"""

    test_path: str = "tests"
    config: Optional[Dict[str, Any]] = None

    @field_validator("test_path")
    @classmethod
    def validate_test_path(cls, v: str) -> str:
        # 防止路径遍历攻击
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid test_path")
        return v


class ChatRequest(BaseModel):
    """聊天请求验证模型"""

    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty")
        if len(v) > 5000:
            raise ValueError("Message too long (max 5000 chars)")
        return v


class ArtifactRequest(BaseModel):
    """Artifact 请求验证模型"""

    artifact_type: str
    content: Any
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("artifact_type")
    @classmethod
    def validate_artifact_type(cls, v: str) -> str:
        if v not in VALID_CONTENT_TYPES:
            raise ValueError(
                f"Invalid artifact_type: {v}. "
                f"Must be one of: {', '.join(sorted(VALID_CONTENT_TYPES))}"
            )
        return v

    @model_validator(mode='after')
    def validate_content(self):
        """验证内容类型"""
        if isinstance(self.content, str) and not self.content.strip():
            raise ValueError("Content cannot be empty")
        return self


def validate_path(path: Any, workspace_root: Path) -> Path:
    """验证路径安全性

    Args:
        path: 要验证的路径
        workspace_root: 工作区根目录

    Returns:
        安全的路径

    Raises:
        ValidationError: 路径不安全
    """
    if path is None:
        return workspace_root

    if isinstance(path, str):
        path = Path(path)

    # 解析并规范化路径
    try:
        resolved = path.resolve()
    except (OSError, ValueError) as e:
        raise ValidationError(
            f"Invalid path: {path}",
            reason=str(e)
        )

    # 检查是否在工作区内
    try:
        resolved.relative_to(workspace_root)
    except ValueError:
        raise ValidationError(
            f"Path outside workspace: {path}",
            path=str(path),
            workspace_root=str(workspace_root)
        )

    # 检查路径遍历攻击
    if ".." in str(path):
        raise ValidationError(
            f"Path traversal attempt: {path}",
            path=str(path)
        )

    return path


def validate_filename(filename: Any) -> str:
    """验证文件名安全性

    Args:
        filename: 文件名

    Returns:
        安全的文件名

    Raises:
        ValidationError: 文件名不安全
    """
    if not filename:
        raise ValidationError("Filename cannot be empty")

    if isinstance(filename, Path):
        filename = str(filename)

    # 移除危险字符
    dangerous_chars = ['/', '\\', '..', '\0', '$', '|', ';', '`']
    for char in dangerous_chars:
        if char in filename:
            raise ValidationError(
                f"Invalid filename: contains dangerous character '{char}'",
                filename=filename
            )

    # 检查长度
    if len(filename) > 255:
        raise ValidationError(
            f"Filename too long (max 255 chars)",
            filename=filename[:50] + "..."
        )

    return filename


def validate_tags(tags: Any) -> List[str]:
    """验证标签列表

    Args:
        tags: 标签列表

    Returns:
        验证后的标签列表

    Raises:
        ValidationError: 标签无效
    """
    if tags is None:
        return []

    if not isinstance(tags, (list, tuple, set)):
        raise ValidationError(
            f"Tags must be a list, got {type(tags).__name__}",
            value=tags
        )

    result = []
    for i, tag in enumerate(tags):
        if not isinstance(tag, str):
            raise ValidationError(
                f"Tag at index {i} must be a string",
                value=tag
            )
        # 清理标签
        cleaned = tag.strip().lower()[:50]
        if cleaned:
            result.append(cleaned)

    return result
