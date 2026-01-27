# -*- coding: utf-8 -*-
"""Adapters - 适配器模块

提供统一的接口访问执行、审查和测试功能。

模块:
    - UnifiedAdapter: 统一适配器 (执行+审查+测试)
    - ExecutorAdapter: 执行适配器
    - ReviewerAdapter: 审查适配器
    - TestAdapter: 测试适配器

方案A: 主工作流集成
    - 代码审查已集成到 Orchestrator._finalize_execution
    - 测试执行可选集成

方案B: 独立API
    - review_code(): 独立代码审查
    - run_tests(): 独立测试执行
    - execute_and_review_and_test(): 完整工作流
"""

from .unified_adapter import UnifiedAdapter
from .reviewer_adapter import ReviewerAdapter
from .executor_adapter import ExecutorAdapter
from .test_adapter import TestAdapter

__all__ = [
    "UnifiedAdapter",      # 统一适配器
    "ReviewerAdapter",     # 代码审查适配器
    "ExecutorAdapter",     # 任务执行适配器
    "TestAdapter",         # 测试执行适配器
]
