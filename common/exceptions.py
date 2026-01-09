#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一异常体系

定义项目中使用的所有自定义异常，建立清晰的异常层次结构
"""

from typing import Any, Optional


class SuperAgentError(Exception):
    """
    SuperAgent 基础异常
    所有项目自定义异常都应继承此类
    """
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self):
        if self.details:
            return f"{self.message} (详情: {self.details})"
        return self.message


class PlanningError(SuperAgentError):
    """规划模块错误"""
    pass


class ExecutionError(SuperAgentError):
    """执行/编排模块错误"""
    pass


class MemorySystemError(SuperAgentError):
    """记忆系统错误"""
    pass


class ConfigurationError(SuperAgentError):
    """配置验证或加载错误"""
    pass


class ContextError(SuperAgentError):
    """上下文处理或压缩错误"""
    pass


class SecurityError(SuperAgentError):
    """安全验证错误"""
    pass


class AgentError(SuperAgentError):
    """Agent 执行相关错误"""
    pass


class ToolError(SuperAgentError):
    """工具调用错误"""
    pass


class ReviewError(SuperAgentError):
    """代码审查错误"""
    pass
