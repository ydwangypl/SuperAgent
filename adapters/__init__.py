#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
适配器层

本模块提供适配器,连接新的抽象层(Executor/Reviewer)和现有的Agent系统。

设计理念:
- 不修改现有的Agent系统
- 提供高级抽象接口
- 保持向后兼容
- 支持未来扩展
"""

from .executor_adapter import ExecutorAdapter
from .reviewer_adapter import ReviewerAdapter
from .unified_adapter import UnifiedAdapter

__all__ = [
    "ExecutorAdapter",
    "ReviewerAdapter",
    "UnifiedAdapter",
]

__version__ = "3.0.0"
