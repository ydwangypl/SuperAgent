#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent 核心抽象层

本模块定义了 SuperAgent 的核心抽象接口,包括:
- Executor: 任务执行器抽象基类
- Reviewer: 代码审查器抽象基类

这些抽象使得 SuperAgent 可以支持多种领域的工作,
而不仅限于代码生成和审查。
"""

from .executor import Executor, Task, ExecutionResult, TaskStatus
from .reviewer import Reviewer, Artifact, ReviewResult, QualityMetric

__all__ = [
    # Executor 相关
    "Executor",
    "Task",
    "ExecutionResult",
    "TaskStatus",

    # Reviewer 相关
    "Reviewer",
    "Artifact",
    "ReviewResult",
    "QualityMetric",
]

__version__ = "3.0.0"
