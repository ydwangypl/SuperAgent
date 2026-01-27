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

v3.3 新增:
- hooks: 生命周期钩子系统
- planning_files: 3-File 模式管理
- state_persistence: 状态持久化
"""

from .executors.writing_executor import WritingExecutor
from .reviewers.content_reviewer import ContentReviewer
from .executors.n8n_executor import N8nExecutor
from .executors.n8n_knowledge_base import N8nKnowledgeBase
from .executors.prompt_executor import PromptExecutor
from .executors.prompt_templates import PromptTemplateLibrary, PromptTemplate

# 生命周期钩子系统
from .hooks.hook_manager import HookManager
from .hooks.hook_types import HookContext, HookResult, HookPriority, BaseHook
from .hooks.lifecycle_hooks import (
    LifecycleHookType,
    create_default_hooks,
    ReReadPlanHook,
    CheckDependenciesHook,
    UpdateStatusHook,
    VerifyCompletionHook,
    LogProgressHook,
    MemorySyncHook,
    ErrorRecoveryHook,
)

# 3-File 模式管理
from .planning_files import (
    TaskPlanManager,
    FindingsManager,
    ProgressManager,
    CompletionChecker,
    CompletionReport,
)

# 状态持久化
from .state_persistence import (
    SessionManager,
    SessionStatus,
    RecoveryReport,
    StateSerializer,
    JSONSerializer,
    PickleSerializer,
    StateFileManager,
)

# 🆕 v3.4.1 技能提取系统
from . import skills

__all__ = [
    # 原有导出
    "WritingExecutor",
    "ContentReviewer",
    "N8nExecutor",
    "N8nKnowledgeBase",
    "PromptExecutor",
    "PromptTemplateLibrary",
    "PromptTemplate",
    # 生命周期钩子系统
    "HookManager",
    "HookContext",
    "HookResult",
    "LifecycleHookType",
    "HookPriority",
    "BaseHook",
    "ReReadPlanHook",
    "CheckDependenciesHook",
    "UpdateStatusHook",
    "VerifyCompletionHook",
    "LogProgressHook",
    "MemorySyncHook",
    "ErrorRecoveryHook",
    "create_default_hooks",
    # 3-File 模式管理
    "TaskPlanManager",
    "FindingsManager",
    "ProgressManager",
    "CompletionChecker",
    "CompletionReport",
    # 状态持久化
    "SessionStatus",
    "SessionManager",
    "StateFileManager",
    "StateSerializer",
    "JSONSerializer",
    "PickleSerializer",
    "RecoveryReport",
    # 🆕 v3.4.1 技能提取系统
    "skills",
]

__version__ = "3.4.1"
