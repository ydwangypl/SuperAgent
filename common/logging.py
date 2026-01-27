#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
上下文日志模块

提供带上下文的日志记录功能，支持 request_id、task_id 等上下文追踪。
"""

import logging
from contextvars import ContextVar
from typing import Any, Dict, Optional
from datetime import datetime


# 上下文变量
request_id: ContextVar[str] = ContextVar('request_id', default='')
task_id: ContextVar[str] = ContextVar('task_id', default='')
session_id: ContextVar[str] = ContextVar('session_id', default='')
agent_type: ContextVar[str] = ContextVar('agent_type', default='')


class ContextLogger:
    """带上下文的日志记录器

    自动在日志中添加 request_id、task_id、session_id 等上下文信息。

    使用示例:
        logger = ContextLogger(__name__)
        logger.info("Task started")
        # 输出: [request_id=xxx] [task_id=yyy] Task started
    """

    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(name)

    def _format_message(self, message: str, **context) -> str:
        """格式化日志消息，添加上下文"""
        parts = []

        # 添加标准上下文
        req_id = request_id.get()
        if req_id:
            parts.append(f"[req_id={req_id}]")

        t_id = task_id.get()
        if t_id:
            parts.append(f"[task_id={t_id}]")

        s_id = session_id.get()
        if s_id:
            parts.append(f"[session_id={s_id}]")

        a_type = agent_type.get()
        if a_type:
            parts.append(f"[agent={a_type}]")

        # 添加额外上下文
        for key, value in context.items():
            parts.append(f"[{key}={value}]")

        context_str = ' '.join(parts)
        if context_str:
            return f"{context_str} {message}"
        return message

    def debug(self, message: str, **context: Any) -> None:
        """DEBUG 级别日志"""
        self._logger.debug(self._format_message(message, **context))

    def info(self, message: str, **context: Any) -> None:
        """INFO 级别日志"""
        self._logger.info(self._format_message(message, **context))

    def warning(self, message: str, **context: Any) -> None:
        """WARNING 级别日志"""
        self._logger.warning(self._format_message(message, **context))

    def error(self, message: str, **context: Any) -> None:
        """ERROR 级别日志"""
        self._logger.error(self._format_message(message, **context))

    def exception(self, message: str, **context: Any) -> None:
        """EXCEPTION 级别日志（包含异常信息）"""
        self._logger.exception(self._format_message(message, **context))

    def critical(self, message: str, **context: Any) -> None:
        """CRITICAL 级别日志"""
        self._logger.critical(self._format_message(message, **context))


def get_logger(name: str) -> ContextLogger:
    """获取 ContextLogger 实例"""
    return ContextLogger(name)


def set_context(
    request_id_: Optional[str] = None,
    task_id_: Optional[str] = None,
    session_id_: Optional[str] = None,
    agent_type_: Optional[str] = None
) -> None:
    """设置上下文变量

    Args:
        request_id_: 请求 ID
        task_id_: 任务 ID
        session_id_: 会话 ID
        agent_type_: Agent 类型
    """
    if request_id_ is not None:
        request_id.set(request_id_)
    if task_id_ is not None:
        task_id.set(task_id_)
    if session_id_ is not None:
        session_id.set(session_id_)
    if agent_type_ is not None:
        agent_type.set(agent_type_)


def clear_context() -> None:
    """清除所有上下文变量"""
    request_id.set('')
    task_id.set('')
    session_id.set('')
    agent_type.set('')


class log_context:
    """上下文管理器，用于临时设置上下文

    使用示例:
        with log_context(task_id="task_123", agent_type="CodingAgent"):
            logger.info("Processing task")
        # 离开 with 块后上下文自动清除
    """

    def __init__(
        self,
        request_id_: Optional[str] = None,
        task_id_: Optional[str] = None,
        session_id_: Optional[str] = None,
        agent_type_: Optional[str] = None
    ):
        self.prev_context = {
            'request_id': request_id.get(),
            'task_id': task_id.get(),
            'session_id': session_id.get(),
            'agent_type': agent_type.get()
        }
        self.new_context = {
            'request_id': request_id_,
            'task_id': task_id_,
            'session_id': session_id_,
            'agent_type': agent_type_
        }

    def __enter__(self) -> 'log_context':
        for key, value in self.new_context.items():
            if value is not None:
                setattr(sys.modules[__name__], key, value)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # 恢复之前的上下文
        request_id.set(self.prev_context['request_id'])
        task_id.set(self.prev_context['task_id'])
        session_id.set(self.prev_context['session_id'])
        agent_type.set(self.prev_context['agent_type'])


# 导入 sys 以支持上下文管理器
import sys
