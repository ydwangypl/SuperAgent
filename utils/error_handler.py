#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一错误处理器

提供错误处理装饰器和工具函数,简化错误处理逻辑。
"""

import logging
import traceback
from typing import Callable, Any, Optional, Type, Dict
from functools import wraps
from collections import Counter
import time
import asyncio

from .exceptions import SuperAgentError


# 配置日志
logger = logging.getLogger(__name__)


def handle_errors(
    error_type: Type[SuperAgentError] = SuperAgentError,
    fallback: Any = None,
    log: bool = True,
    raise_on_unexpected: bool = False,
    error_callback: Optional[Callable] = None
):
    """
    错误处理装饰器

    自动捕获并处理函数中的异常,支持同步和异步函数。

    Args:
        error_type: 要捕获的异常类型 (默认: SuperAgentError)
        fallback: 发生异常时的返回值 (默认: None)
        log: 是否记录日志 (默认: True)
        raise_on_unexpected: 是否重新抛出未预期的异常 (默认: False)
        error_callback: 错误回调函数,签名为 callback(error, func, args, kwargs)

    Returns:
        装饰后的函数

    Example:
        >>> @handle_errors(error_type=ConversationError, fallback=None)
        >>> async def my_function():
        ...     # 可能抛出 ConversationError 的代码
        ...     pass
    """

    def decorator(func: Callable) -> Callable:
        # 获取原始函数的完整限定名
        func_name = f"{func.__module__}.{func.__qualname__}"

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            """异步函数包装器"""
            try:
                return await func(*args, **kwargs)
            except error_type as e:
                if log:
                    logger.error(f"[{func_name}] {error_type.__name__}: {e}")
                if error_callback:
                    error_callback(e, func, args, kwargs)
                return fallback
            except Exception as e:
                logger.exception(f"[{func_name}] Unexpected error: {e}")
                if error_callback:
                    error_callback(e, func, args, kwargs)
                if raise_on_unexpected:
                    raise
                return fallback

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            """同步函数包装器"""
            try:
                return func(*args, **kwargs)
            except error_type as e:
                if log:
                    logger.error(f"[{func_name}] {error_type.__name__}: {e}")
                if error_callback:
                    error_callback(e, func, args, kwargs)
                return fallback
            except Exception as e:
                logger.exception(f"[{func_name}] Unexpected error: {e}")
                if error_callback:
                    error_callback(e, func, args, kwargs)
                if raise_on_unexpected:
                    raise
                return fallback

        # 根据函数类型返回对应的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def safe_execute(
    func: Callable,
    *args,
    fallback: Any = None,
    log: bool = True,
    error_callback: Optional[Callable] = None,
    **kwargs
) -> Any:
    """
    安全执行函数

    捕获函数执行过程中的异常,返回 fallback 值或重新抛出异常。

    Args:
        func: 要执行的函数
        *args: 位置参数
        fallback: 失败时的返回值 (默认: None)
        log: 是否记录日志 (默认: True)
        error_callback: 错误回调函数
        **kwargs: 关键字参数

    Returns:
        函数执行结果或 fallback

    Example:
        >>> result = safe_execute(
        ...     risky_function,
        ...     arg1, arg2,
        ...     fallback="default_value",
        ...     log=True
        ... )
    """
    func_name = f"{func.__module__}.{func.__qualname__}"

    try:
        return func(*args, **kwargs)
    except SuperAgentError as e:
        if log:
            logger.error(f"[safe_execute][{func_name}] {e.__class__.__name__}: {e}")
        if error_callback:
            error_callback(e, func, args, kwargs)
        return fallback
    except Exception as e:
        logger.exception(f"[safe_execute][{func_name}] Unexpected error: {e}")
        if error_callback:
            error_callback(e, func, args, kwargs)
        return fallback


async def safe_execute_async(
    func: Callable,
    *args,
    fallback: Any = None,
    log: bool = True,
    error_callback: Optional[Callable] = None,
    **kwargs
) -> Any:
    """
    安全执行异步函数

    捕获异步函数执行过程中的异常,返回 fallback 值或重新抛出异常。

    Args:
        func: 要执行的异步函数
        *args: 位置参数
        fallback: 失败时的返回值 (默认: None)
        log: 是否记录日志 (默认: True)
        error_callback: 错误回调函数
        **kwargs: 关键字参数

    Returns:
        函数执行结果或 fallback
    """
    func_name = f"{func.__module__}.{func.__qualname__}"

    try:
        return await func(*args, **kwargs)
    except SuperAgentError as e:
        if log:
            logger.error(f"[safe_execute_async][{func_name}] {e.__class__.__name__}: {e}")
        if error_callback:
            error_callback(e, func, args, kwargs)
        return fallback
    except Exception as e:
        logger.exception(f"[safe_execute_async][{func_name}] Unexpected error: {e}")
        if error_callback:
            error_callback(e, func, args, kwargs)
        return fallback


class ErrorHandler:
    """
    错误处理器类

    提供更灵活的错误处理方式,支持错误计数、阈值控制等功能。
    """

    def __init__(
        self,
        max_errors: int = 10,
        reset_interval: int = 300,
        log_errors: bool = True
    ):
        """
        初始化错误处理器

        Args:
            max_errors: 最大错误次数 (超过后将触发错误恢复机制)
            reset_interval: 错误计数重置间隔 (秒)
            log_errors: 是否记录错误日志
        """
        self.max_errors = max_errors
        self.reset_interval = reset_interval
        self.log_errors = log_errors
        self.error_count = 0
        self.last_error_time = None
        self.error_history = []

    def record_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        记录错误

        Args:
            error: 异常对象
            context: 错误上下文信息

        Returns:
            是否超过错误阈值
        """
        import time

        self.error_count += 1
        self.last_error_time = time.time()

        error_info = {
            "error_type": type(error).__name__,
            "message": str(error),
            "timestamp": self.last_error_time,
            "context": context
        }

        self.error_history.append(error_info)

        if self.log_errors:
            logger.error(f"Error recorded: {error_info}")

        # 检查是否超过阈值
        return self.error_count >= self.max_errors

    def reset(self):
        """重置错误计数"""
        self.error_count = 0
        self.last_error_time = None
        self.error_history.clear()

    def get_error_summary(self) -> Dict[str, Any]:
        """
        获取错误摘要

        Returns:
            错误统计信息
        """
        from collections import Counter

        error_types = Counter(
            e["error_type"] for e in self.error_history
        )

        return {
            "total_errors": self.error_count,
            "last_error_time": self.last_error_time,
            "error_types": dict(error_types),
            "recent_errors": self.error_history[-10:]  # 最近 10 个错误
        }

    def should_trigger_recovery(self) -> bool:
        """
        判断是否应该触发错误恢复机制

        Returns:
            是否需要触发恢复
        """
        import time

        # 如果没有错误,不需要恢复
        if self.error_count == 0:
            return False

        # 如果超过最大错误次数,需要恢复
        if self.error_count >= self.max_errors:
            return True

        # 如果距离上次错误时间超过重置间隔,重置计数
        if self.last_error_time and (time.time() - self.last_error_time) > self.reset_interval:
            self.reset()
            return False

        return False
