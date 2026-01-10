#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
扩展模块

本模块包含新的Executor和Reviewer实现,用于验证架构的可扩展性。
这些实现不依赖现有的Agent系统,是独立的实现。

设计理念:
- 验证新架构确实支持多领域扩展
- 提供完整的示例实现
- 展示如何使用抽象层
"""

from .writing_executor import WritingExecutor
from .content_reviewer import ContentReviewer

__all__ = [
    "WritingExecutor",
    "ContentReviewer",
]

__version__ = "3.0.0"
