#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生命周期钩子类型定义

定义 SuperAgent 的生命周期钩子类型，区别于 Claude Code 原生的 PreToolUse/PostToolUse。
这些钩子在 Agent 执行层面拦截，提供更细粒度的控制。
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class LifecycleHookType(Enum):
    """生命周期钩子类型（区别于 Claude Code Hook）"""
    PRE_EXECUTE = "PreExecute"      # 执行前全局拦截
    POST_EXECUTE = "PostExecute"    # 执行后全局拦截
    PRE_TASK = "PreTask"            # 任务执行前
    POST_TASK = "PostTask"          # 任务执行后
    PRE_STEP = "PreStep"            # 步骤执行前
    POST_STEP = "PostStep"          # 步骤执行后
    STOP = "Stop"                   # 停止时验证


class HookPriority(Enum):
    """钩子优先级"""
    LOW = 0
    NORMAL = 50
    HIGH = 100


class HookContext(BaseModel):
    """钩子上下文"""
    phase: str                      # 当前阶段标识
    current_task: Optional[Dict[str, Any]] = None
    current_step: Optional[Dict[str, Any]] = None
    session_state: Dict[str, Any] = {}
    execution_history: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}


class HookResult(BaseModel):
    """钩子执行结果"""
    context_injection: Optional[str] = None     # 注入到上下文的内容
    suggestion: Optional[str] = None            # 给用户的建议
    should_continue: bool = True                # 是否继续执行
    should_skip: bool = False                   # 是否跳过当前任务
    cleanup_actions: List[str] = []             # 需要执行的清理操作
    metadata: Dict[str, Any] = {}


class BaseHook:
    """钩子基类"""

    def __init__(self, name: str, hook_type: LifecycleHookType, priority: HookPriority = HookPriority.NORMAL):
        self.name = name
        self.hook_type = hook_type
        self.priority = priority

    async def execute(self, context: HookContext) -> HookResult:
        """执行钩子逻辑（子类重写）"""
        raise NotImplementedError

    async def can_execute(self, context: HookContext) -> bool:
        """判断钩子是否应该执行"""
        return True


class HookRegistration:
    """钩子注册信息"""

    def __init__(
        self,
        hook: BaseHook,
        enabled: bool = True,
        conditions: Optional[Dict[str, Any]] = None
    ):
        self.hook = hook
        self.enabled = enabled
        self.conditions = conditions or {}
