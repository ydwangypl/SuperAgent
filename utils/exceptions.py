#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent 统一异常类

定义所有 SuperAgent 相关的异常类型,提供统一的错误处理接口。
"""

from typing import Optional, Dict, Any


class SuperAgentError(Exception):
    """
    SuperAgent 基础异常类

    所有 SuperAgent 异常的基类,提供统一的错误信息格式。

    Attributes:
        message: 错误消息
        details: 错误详细信息 (可选)
        error_code: 错误代码 (可选)
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self) -> str:
        """返回格式化的错误信息"""
        parts = [self.message]

        if self.error_code:
            parts.append(f"[{self.error_code}]")

        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            parts.append(f"- {details_str}")

        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "error_code": self.error_code
        }


class ConversationError(SuperAgentError):
    """对话管理异常"""

    pass


class PlanningError(SuperAgentError):
    """计划生成异常"""

    pass


class ExecutionError(SuperAgentError):
    """执行异常"""

    pass


class ReviewError(SuperAgentError):
    """代码审查异常"""

    pass


class ConfigurationError(SuperAgentError):
    """配置异常"""

    pass


class LLMError(SuperAgentError):
    """LLM 调用异常"""

    pass


class MemoryError(SuperAgentError):
    """记忆系统异常"""

    pass


class ValidationError(SuperAgentError):
    """验证异常"""

    pass


class TaskError(SuperAgentError):
    """任务异常"""

    pass


class OrchestratorError(SuperAgentError):
    """编排器异常"""

    pass


# 错误代码常量
class ErrorCodes:
    """错误代码定义"""

    # 对话管理错误 (1xxx)
    INTENT_RECOGNITION_FAILED = "E1001"
    CONTEXT_TOO_LONG = "E1002"
    CONVERSATION_TIMEOUT = "E1003"

    # 计划生成错误 (2xxx)
    PLAN_GENERATION_FAILED = "E2001"
    INVALID_REQUIREMENTS = "E2002"
    PLAN_VALIDATION_FAILED = "E2003"

    # 执行错误 (3xxx)
    TASK_EXECUTION_FAILED = "E3001"
    FILE_OPERATION_FAILED = "E3002"
    DEPENDENCY_NOT_FOUND = "E3003"
    EXECUTION_TIMEOUT = "E3004"

    # 代码审查错误 (4xxx)
    REVIEW_FAILED = "E4001"
    CODE_PARSING_FAILED = "E4002"
    QUALITY_CHECK_FAILED = "E4003"
    RALPH_WIGGUM_FAILED = "E4004"

    # 配置错误 (5xxx)
    INVALID_CONFIG = "E5001"
    MISSING_CONFIG = "E5002"
    CONFIG_VALIDATION_FAILED = "E5003"

    # LLM 错误 (6xxx)
    LLM_API_ERROR = "E6001"
    LLM_RATE_LIMIT = "E6002"
    LLM_TIMEOUT = "E6003"
    LLM_INVALID_RESPONSE = "E6004"

    # 记忆系统错误 (7xxx)
    MEMORY_SAVE_FAILED = "E7001"
    MEMORY_RETRIEVE_FAILED = "E7002"
    MEMORY_VALIDATION_FAILED = "E7003"

    # 验证错误 (8xxx)
    INPUT_VALIDATION_FAILED = "E8001"
    OUTPUT_VALIDATION_FAILED = "E8002"
    PARAMETER_INVALID = "E8003"

    # 任务错误 (9xxx)
    TASK_NOT_FOUND = "E9001"
    TASK_ALREADY_EXISTS = "E9002"
    TASK_INVALID_STATE = "E9003"

    # 编排器错误 (10xxx)
    ORCHESTRATION_FAILED = "E10001"
    WORKFLOW_ERROR = "E10002"
    PARALLEL_EXECUTION_FAILED = "E10003"
