#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
钩子管理器

管理生命周期钩子的注册、执行和优先级排序。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime

from .hook_types import (
    LifecycleHookType,
    HookPriority,
    HookContext,
    HookResult,
    BaseHook,
    HookRegistration,
)
from memory.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


class HookManager:
    """生命周期钩子管理器"""

    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory_manager = memory_manager
        self._registrations: Dict[LifecycleHookType, List[HookRegistration]] = {
            hook_type: [] for hook_type in LifecycleHookType
        }
        self._execution_counters: Dict[str, int] = {}
        self._enabled = True

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self):
        """启用钩子系统"""
        self._enabled = True
        logger.info("钩子系统已启用")

    def disable(self):
        """禁用钩子系统"""
        self._enabled = False
        logger.info("钩子系统已禁用")

    def register(
        self,
        hook: BaseHook,
        enabled: bool = True,
        conditions: Optional[Dict[str, Any]] = None
    ) -> None:
        """注册钩子"""
        registration = HookRegistration(hook, enabled, conditions)
        self._registrations[hook.hook_type].append(registration)
        # 按优先级排序
        self._registrations[hook.hook_type].sort(
            key=lambda r: r.hook.priority.value,
            reverse=True
        )
        logger.debug(f"已注册钩子: {hook.name} ({hook.hook_type.value})")

    def unregister(self, hook_name: str, hook_type: Optional[LifecycleHookType] = None) -> bool:
        """注销钩子"""
        if hook_type:
            registrations = self._registrations.get(hook_type, [])
            for i, reg in enumerate(registrations):
                if reg.hook.name == hook_name:
                    registrations.pop(i)
                    logger.debug(f"已注销钩子: {hook_name}")
                    return True
            return False
        else:
            # 遍历所有类型查找
            for hook_type in LifecycleHookType:
                registrations = self._registrations.get(hook_type, [])
                for i, reg in enumerate(registrations):
                    if reg.hook.name == hook_name:
                        registrations.pop(i)
                        logger.debug(f"已注销钩子: {hook_name}")
                        return True
            return False

    def clear(self, hook_type: Optional[LifecycleHookType] = None) -> None:
        """清空钩子注册"""
        if hook_type:
            self._registrations[hook_type] = []
        else:
            for hook_type in LifecycleHookType:
                self._registrations[hook_type] = []
        logger.info("钩子注册已清空")

    async def execute_hooks(
        self,
        hook_type: LifecycleHookType,
        context: HookContext,
        raise_on_error: bool = False
    ) -> List[HookResult]:
        """执行指定类型的所有钩子"""
        if not self._enabled:
            return []

        results = []
        registrations = self._registrations.get(hook_type, [])

        for registration in registrations:
            if not registration.enabled:
                continue

            hook = registration.hook
            hook_id = f"{hook.name}:{hook_type.value}"

            try:
                # 检查执行条件
                if not await self._check_conditions(registration.conditions, context):
                    continue

                # 检查是否应该执行
                if not await hook.can_execute(context):
                    continue

                # 执行钩子
                self._execution_counters[hook_id] = \
                    self._execution_counters.get(hook_id, 0) + 1

                result = await hook.execute(context)
                results.append(result)

                # 记录到记忆系统
                if self.memory_manager and result.suggestion:
                    await self.memory_manager.save_episodic_memory(
                        event=f"钩子 {hook.name} 执行建议: {result.suggestion[:200]}",
                        metadata={"hook_type": hook_type.value, "hook_name": hook.name}
                    )

                # 如果钩子要求停止执行
                if not result.should_continue:
                    logger.info(f"钩子 {hook.name} 要求停止执行")
                    break

            except Exception as e:
                logger.error(f"钩子 {hook.name} 执行失败: {e}")
                if raise_on_error:
                    raise
                results.append(HookResult(
                    suggestion=f"钩子执行失败: {str(e)}",
                    should_continue=not raise_on_error
                ))

        return results

    async def execute_pre_execute(
        self,
        session_state: Optional[Dict[str, Any]] = None
    ) -> HookContext:
        """执行 PreExecute 钩子"""
        context = HookContext(
            phase="pre_execute",
            session_state=session_state or {},
            metadata={"timestamp": datetime.now().isoformat()}
        )
        results = await self.execute_hooks(LifecycleHookType.PRE_EXECUTE, context)

        # 聚合所有结果
        combined_injection = "\n".join(
            r.context_injection for r in results if r.context_injection
        )
        suggestions = [r.suggestion for r in results if r.suggestion]

        return HookContext(
            phase="pre_execute",
            session_state=session_state or {},
            context_injection=combined_injection if combined_injection else None,
            suggestion="\n".join(suggestions) if suggestions else None,
            execution_history=results,
            metadata={"timestamp": datetime.now().isoformat()}
        )

    async def execute_post_execute(
        self,
        session_state: Optional[Dict[str, Any]] = None,
        execution_history: Optional[List[Dict[str, Any]]] = None
    ) -> HookContext:
        """执行 PostExecute 钩子"""
        context = HookContext(
            phase="post_execute",
            session_state=session_state or {},
            execution_history=execution_history or [],
            metadata={"timestamp": datetime.now().isoformat()}
        )
        results = await self.execute_hooks(LifecycleHookType.POST_EXECUTE, context)

        return HookContext(
            phase="post_execute",
            session_state=session_state or {},
            execution_history=execution_history or [],
            metadata={"timestamp": datetime.now().isoformat()}
        )

    async def execute_pre_task(
        self,
        task: Dict[str, Any],
        session_state: Optional[Dict[str, Any]] = None
    ) -> HookContext:
        """执行 PreTask 钩子"""
        context = HookContext(
            phase="pre_task",
            current_task=task,
            session_state=session_state or {},
            metadata={"timestamp": datetime.now().isoformat()}
        )
        results = await self.execute_hooks(LifecycleHookType.PRE_TASK, context)

        combined_injection = "\n".join(
            r.context_injection for r in results if r.context_injection
        )
        suggestions = [r.suggestion for r in results if r.suggestion]
        should_skip = any(r.should_skip for r in results)

        return HookContext(
            phase="pre_task",
            current_task=task,
            session_state=session_state or {},
            context_injection=combined_injection if combined_injection else None,
            suggestion="\n".join(suggestions) if suggestions else None,
            should_skip=should_skip,
            execution_history=results,
            metadata={"timestamp": datetime.now().isoformat()}
        )

    async def execute_post_task(
        self,
        task: Dict[str, Any],
        result: Any,
        session_state: Optional[Dict[str, Any]] = None
    ) -> None:
        """执行 PostTask 钩子"""
        task_with_result = {
            **(task if isinstance(task, dict) else {"task": task}),
            "result": result,
            "completed_at": datetime.now().isoformat()
        }
        context = HookContext(
            phase="post_task",
            current_task=task_with_result,
            session_state=session_state or {},
            execution_history=[task_with_result],
            metadata={"timestamp": datetime.now().isoformat()}
        )
        await self.execute_hooks(LifecycleHookType.POST_TASK, context)

    async def execute_stop(self, session_state: Dict[str, Any]) -> HookResult:
        """执行 Stop 钩子，返回完成度报告"""
        context = HookContext(
            phase="stop",
            session_state=session_state,
            metadata={"timestamp": datetime.now().isoformat()}
        )
        results = await self.execute_hooks(LifecycleHookType.STOP, context)

        # 聚合结果
        suggestions = [r.suggestion for r in results if r.suggestion]
        context_injection = "\n".join(
            r.context_injection for r in results if r.context_injection
        )

        return HookResult(
            context_injection=context_injection if context_injection else None,
            suggestion="\n".join(suggestions) if suggestions else None,
            cleanup_actions=[action for r in results for action in r.cleanup_actions],
            metadata={"hook_count": len(results)}
        )

    async def _check_conditions(
        self,
        conditions: Dict[str, Any],
        context: HookContext
    ) -> bool:
        """检查钩子执行条件"""
        if not conditions:
            return True

        # 检查任务类型条件
        if "task_types" in conditions:
            if context.current_task:
                task_type = context.current_task.get("type", "")
                if task_type not in conditions["task_types"]:
                    return False

        # 检查阶段条件
        if "phases" in conditions:
            if context.phase not in conditions["phases"]:
                return False

        # 检查 Agent 类型条件
        if "agent_types" in conditions:
            if context.current_task:
                agent_type = context.current_task.get("agent_type", "")
                if agent_type not in conditions["agent_types"]:
                    return False

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """获取钩子执行统计"""
        return {
            "enabled": self._enabled,
            "registered_hooks": {
                hook_type.value: len(regs)
                for hook_type, regs in self._registrations.items()
            },
            "execution_counters": self._execution_counters
        }
