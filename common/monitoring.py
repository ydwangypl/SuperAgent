#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent 运行时监控指标模块

提供基于 prometheus_client 的运行时监控指标
"""

import time
import functools
from typing import Optional, Any, Callable
from prometheus_client import Counter, Histogram, Gauge, Summary

# 任务相关指标
TASK_TOTAL = Counter(
    'superagent_tasks_total',
    'Total number of tasks processed',
    ['agent_type', 'status']
)

TASK_DURATION = Histogram(
    'superagent_task_duration_seconds',
    'Task execution duration in seconds',
    ['agent_type'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600)
)

# 记忆系统指标
MEMORY_OPERATIONS = Counter(
    'superagent_memory_operations_total',
    'Total number of memory operations',
    ['layer', 'operation', 'status']
)

MEMORY_SIZE = Gauge(
    'superagent_memory_size_entries',
    'Current number of entries in memory layers',
    ['layer']
)

# Token 使用指标
TOKEN_USAGE = Counter(
    'superagent_token_usage_total',
    'Total number of tokens consumed',
    ['agent_type', 'usage_type']  # usage_type: prompt, completion, total
)

TOKEN_SAVINGS = Counter(
    'superagent_token_savings_total',
    'Total number of tokens saved via optimization',
    ['agent_type', 'optimization_type']  # optimization_type: compression, incremental
)

# 错误和异常指标
ERRORS_TOTAL = Counter(
    'superagent_errors_total',
    'Total number of errors encountered',
    ['error_type', 'module']
)


def monitor_task_duration(agent_type: str):
    """
    监控任务执行时间的装饰器 (支持同步和异步函数)
    """
    def decorator(func: Callable):
        import asyncio
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except asyncio.CancelledError:
                status = "cancelled"
                raise
            except Exception as e:
                status = "error"
                ERRORS_TOTAL.labels(error_type=type(e).__name__, module=func.__module__).inc()
                raise
            finally:
                duration = time.time() - start_time
                TASK_DURATION.labels(agent_type=agent_type).observe(duration)
                TASK_TOTAL.labels(agent_type=agent_type, status=status).inc()

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                ERRORS_TOTAL.labels(error_type=type(e).__name__, module=func.__module__).inc()
                raise
            finally:
                duration = time.time() - start_time
                TASK_DURATION.labels(agent_type=agent_type).observe(duration)
                TASK_TOTAL.labels(agent_type=agent_type, status=status).inc()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


class MetricsManager:
    """指标管理器，用于手动记录指标"""
    
    @staticmethod
    def record_memory_op(layer: str, operation: str, status: str = "success"):
        MEMORY_OPERATIONS.labels(layer=layer, operation=operation, status=status).inc()

    @staticmethod
    def update_memory_size(layer: str, size: int):
        MEMORY_SIZE.labels(layer=layer).set(size)

    @staticmethod
    def record_token_usage(agent_type: str, prompt: int, completion: int):
        TOKEN_USAGE.labels(agent_type=agent_type, usage_type="prompt").inc(prompt)
        TOKEN_USAGE.labels(agent_type=agent_type, usage_type="completion").inc(completion)
        TOKEN_USAGE.labels(agent_type=agent_type, usage_type="total").inc(prompt + completion)

    @staticmethod
    def record_token_savings(agent_type: str, savings: int, opt_type: str):
        TOKEN_SAVINGS.labels(agent_type=agent_type, optimization_type=opt_type).inc(savings)

    @staticmethod
    def record_error(error_type: str, module: str):
        ERRORS_TOTAL.labels(error_type=error_type, module=module).inc()
