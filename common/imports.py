#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一导入模块

提供 SuperAgent 项目的一致性导入入口。
遵循 PEP 8 导入规范，避免循环导入和硬编码路径。

使用方式:
    from common.imports import MemoryManager, OrchestrationConfig
"""

# 核心组件
from memory.memory_manager import MemoryManager
from orchestration.models import OrchestrationConfig

# Agent 相关
from execution.base_agent import BaseAgent
from common.models import AgentType, TaskStatus, StepStatus

# 适配器
from adapters.unified_adapter import UnifiedAdapter
from adapters.test_adapter import TestAdapter

# 服务层
from server.interaction_service import (
    NaturalLanguageParser,
    AgentDispatcher,
    ProjectGuide,
    ProjectPhase
)

# 规划文件管理
from extensions.planning_files import (
    TaskPlanManager,
    FindingsManager,
    ProgressManager,
    CompletionChecker
)

# Hook 系统
from extensions.hooks import HookManager

# __all__ 导出
__all__ = [
    # 核心
    "MemoryManager",
    "OrchestrationConfig",
    # Agent
    "BaseAgent",
    "AgentType",
    "TaskStatus",
    "StepStatus",
    # 适配器
    "UnifiedAdapter",
    "TestAdapter",
    # 服务层
    "NaturalLanguageParser",
    "AgentDispatcher",
    "ProjectGuide",
    "ProjectPhase",
    # 规划文件
    "TaskPlanManager",
    "FindingsManager",
    "ProgressManager",
    "CompletionChecker",
    # Hook
    "HookManager",
]
