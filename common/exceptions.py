#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一异常体系

定义项目中使用的所有自定义异常，建立清晰的异常层次结构。
支持错误代码、详细信息、时间戳等。
"""

from typing import Any, Optional
from datetime import datetime
from pathlib import Path


class SuperAgentError(Exception):
    """
    SuperAgent 基础异常
    所有项目自定义异常都应继承此类
    """
    error_code: str = "UNKNOWN_ERROR"

    def __init__(
        self,
        message: str,
        details: Optional[Any] = None,
        code: Optional[str] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.error_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.now().isoformat()

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }


class ValidationError(SuperAgentError):
    """输入验证错误"""
    error_code = "VALIDATION_ERROR"

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        details = {"field": field, "value": value}
        details.update(kwargs)
        super().__init__(message, details=details, code="VALIDATION_ERROR")


class PlanningError(SuperAgentError):
    """规划模块错误"""
    error_code = "PLANNING_ERROR"
    pass


class ExecutionError(SuperAgentError):
    """执行/编排模块错误"""
    error_code = "EXECUTION_ERROR"

    def __init__(
        self,
        message: str,
        task_id: Optional[str] = None,
        **kwargs
    ):
        details = {"task_id": task_id}
        details.update(kwargs)
        super().__init__(message, details=details, code="EXECUTION_ERROR")


class MemorySystemError(SuperAgentError):
    """记忆系统错误"""
    error_code = "MEMORY_ERROR"
    pass


class ConfigurationError(SuperAgentError):
    """配置验证或加载错误"""
    error_code = "CONFIGURATION_ERROR"

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        details = {"config_key": config_key}
        details.update(kwargs)
        super().__init__(message, details=details, code="CONFIGURATION_ERROR")


class ContextError(SuperAgentError):
    """上下文处理或压缩错误"""
    error_code = "CONTEXT_ERROR"
    pass


class SecurityError(SuperAgentError):
    """安全验证错误"""
    error_code = "SECURITY_ERROR"

    def __init__(
        self,
        message: str,
        reason: Optional[str] = None,
        **kwargs
    ):
        details = {"reason": reason}
        details.update(kwargs)
        super().__init__(message, details=details, code="SECURITY_ERROR")


class AgentError(SuperAgentError):
    """Agent 执行相关错误"""
    error_code = "AGENT_ERROR"

    def __init__(
        self,
        message: str,
        agent_type: Optional[str] = None,
        **kwargs
    ):
        details = {"agent_type": agent_type}
        details.update(kwargs)
        super().__init__(message, details=details, code="AGENT_ERROR")


class ToolError(SuperAgentError):
    """工具调用错误"""
    error_code = "TOOL_ERROR"

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        **kwargs
    ):
        details = {"tool_name": tool_name}
        details.update(kwargs)
        super().__init__(message, details=details, code="TOOL_ERROR")


class ReviewError(SuperAgentError):
    """代码审查错误"""
    error_code = "REVIEW_ERROR"

    def __init__(
        self,
        message: str,
        review_id: Optional[str] = None,
        **kwargs
    ):
        details = {"review_id": review_id}
        details.update(kwargs)
        super().__init__(message, details=details, code="REVIEW_ERROR")


class TimeoutError(SuperAgentError):
    """超时错误"""
    error_code = "TIMEOUT_ERROR"

    def __init__(
        self,
        message: str,
        timeout: Optional[int] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = {"timeout": timeout, "operation": operation}
        details.update(kwargs)
        super().__init__(message, details=details, code="TIMEOUT_ERROR")


class FileOperationError(SuperAgentError):
    """文件操作错误"""
    error_code = "FILE_OPERATION_ERROR"

    def __init__(
        self,
        message: str,
        path: Optional[Path] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = {"path": str(path) if path else None, "operation": operation}
        details.update(kwargs)
        super().__init__(message, details=details, code="FILE_OPERATION_ERROR")
