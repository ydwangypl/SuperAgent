#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
预定义的生命周期钩子实现

提供常用的钩子实现，包括：
- ReReadPlanHook: 强制重新读取计划
- UpdateStatusHook: 更新状态
- VerifyCompletionHook: 验证完成度
- LogProgressHook: 记录进度
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from .hook_types import (
    LifecycleHookType,
    HookPriority,
    HookContext,
    HookResult,
    BaseHook,
)
from ..planning_files import TaskPlanManager, FindingsManager, ProgressManager

logger = logging.getLogger(__name__)


class ReReadPlanHook(BaseHook):
    """重新读取计划钩子 - 在任务执行前提醒 Agent 参考计划"""

    def __init__(
        self,
        task_plan_manager: TaskPlanManager,
        priority: HookPriority = HookPriority.HIGH
    ):
        super().__init__("re-read-plan", LifecycleHookType.PRE_TASK, priority)
        self.task_plan_manager = task_plan_manager

    async def execute(self, context: HookContext) -> HookResult:
        """执行重新读取计划"""
        try:
            # 读取当前计划
            plan_content = await self.task_plan_manager.read_plan()

            if plan_content:
                return HookResult(
                    context_injection=f"\n\n## 📋 当前任务计划:\n\n{plan_content}",
                    suggestion="请在执行前参考最新的任务计划，确保方向正确"
                )
        except Exception as e:
            logger.error(f"读取计划失败: {e}")

        return HookResult()


class CheckDependenciesHook(BaseHook):
    """检查依赖钩子 - 验证任务依赖是否满足"""

    def __init__(self, priority: HookPriority = HookPriority.HIGH):
        super().__init__("check-dependencies", LifecycleHookType.PRE_TASK, priority)

    async def execute(self, context: HookContext) -> HookResult:
        """检查依赖"""
        task = context.current_task
        if not task:
            return HookResult()

        dependencies = task.get("dependencies", [])
        completed_ids = context.session_state.get("completed_task_ids", [])

        missing_deps = [dep for dep in dependencies if dep not in completed_ids]

        if missing_deps:
            return HookResult(
                should_continue=False,
                suggestion=f"❌ 任务 '{task.get('name', 'Unknown')}' 的依赖未满足: {', '.join(missing_deps)}"
            )

        return HookResult()


class UpdateStatusHook(BaseHook):
    """更新状态钩子 - 在任务执行后更新状态"""

    def __init__(
        self,
        task_plan_manager: TaskPlanManager,
        progress_manager: Optional[ProgressManager] = None,
        priority: HookPriority = HookPriority.NORMAL
    ):
        super().__init__("update-status", LifecycleHookType.POST_TASK, priority)
        self.task_plan_manager = task_plan_manager
        self.progress_manager = progress_manager

    async def execute(self, context: HookContext) -> HookResult:
        """更新状态"""
        task = context.current_task
        if not task:
            return HookResult()

        task_id = task.get("task_id") or task.get("id")
        status = task.get("status", "unknown")

        try:
            # 更新 task_plan.md 中的 checkbox
            if task_id:
                await self.task_plan_manager.update_task_status(task_id, status)

            # 记录到 progress.md
            if self.progress_manager and context.execution_history:
                for exec_item in context.execution_history:
                    await self.progress_manager.log_progress(
                        action=f"执行任务: {task.get('name', 'Unknown')}",
                        status=status,
                        details=str(exec_item)[:500]
                    )

        except Exception as e:
            logger.error(f"更新状态失败: {e}")

        return HookResult()


class VerifyCompletionHook(BaseHook):
    """验证完成度钩子 - 在停止时验证所有任务是否完成"""

    def __init__(
        self,
        task_plan_manager: TaskPlanManager,
        priority: HookPriority = HookPriority.HIGH
    ):
        super().__init__("verify-completion", LifecycleHookType.STOP, priority)
        self.task_plan_manager = task_plan_manager

    async def execute(self, context: HookContext) -> HookResult:
        """验证完成度"""
        try:
            completion_report = await self.task_plan_manager.get_completion_report()

            if completion_report.is_complete:
                return HookResult(
                    context_injection=f"\n\n## ✅ 执行完成\n\n{completion_report.summary}",
                    suggestion="🎉 所有任务已完成！"
                )
            else:
                return HookResult(
                    context_injection=f"\n\n## 📊 执行进度\n\n{completion_report.summary}",
                    suggestion=f"还有 {completion_report.remaining_count} 个任务未完成",
                    cleanup_actions=["review_remaining_tasks"]
                )
        except Exception as e:
            logger.error(f"验证完成度失败: {e}")
            return HookResult(suggestion=f"验证完成度时出错: {str(e)}")


class LogProgressHook(BaseHook):
    """记录进度钩子 - 记录会话进度"""

    def __init__(
        self,
        progress_manager: ProgressManager,
        priority: HookPriority = HookPriority.LOW
    ):
        super().__init__("log-progress", LifecycleHookType.POST_EXECUTE, priority)
        self.progress_manager = progress_manager

    async def execute(self, context: HookContext) -> HookResult:
        """记录进度"""
        try:
            await self.progress_manager.log_session_summary(
                task_count=len(context.execution_history),
                status="completed"
            )
        except Exception as e:
            logger.error(f"记录进度失败: {e}")

        return HookResult()


class MemorySyncHook(BaseHook):
    """记忆同步钩子 - 将执行历史同步到 MemoryManager"""

    def __init__(
        self,
        memory_manager,
        priority: HookPriority = HookPriority.NORMAL
    ):
        super().__init__("memory-sync", LifecycleHookType.POST_TASK, priority)
        self.memory_manager = memory_manager

    async def execute(self, context: HookContext) -> HookResult:
        """同步到记忆系统"""
        if not self.memory_manager or not context.current_task:
            return HookResult()

        task = context.current_task
        task_name = task.get("name", "Unknown")
        status = task.get("status", "unknown")

        try:
            await self.memory_manager.save_episodic_memory(
                event=f"任务 '{task_name}' 状态更新为: {status}",
                task_id=task.get("task_id"),
                agent_type=task.get("agent_type"),
                metadata={"phase": context.phase}
            )
        except Exception as e:
            logger.error(f"记忆同步失败: {e}")

        return HookResult()


class ErrorRecoveryHook(BaseHook):
    """错误恢复钩子 - 处理执行错误"""

    def __init__(self, priority: HookPriority = HookPriority.HIGH):
        super().__init__("error-recovery", LifecycleHookType.POST_TASK, priority)

    async def execute(self, context: HookContext) -> HookResult:
        """处理错误"""
        # 检查是否有错误记录
        execution_history = context.execution_history

        errors = []
        for item in execution_history:
            if isinstance(item, dict) and item.get("status") == "failed":
                error_info = item.get("error", {})
                errors.append({
                    "task": item.get("task", "Unknown"),
                    "error": str(error_info)
                })

        if errors:
            error_summary = "\n".join(
                f"- {e['task']}: {e['error'][:100]}" for e in errors[:5]
            )
            return HookResult(
                suggestion=f"检测到 {len(errors)} 个任务执行失败，请检查：\n{error_summary}",
                cleanup_actions=["review_failed_tasks", "retry_or_skip"]
            )

        return HookResult()


def create_default_hooks(
    task_plan_manager: TaskPlanManager,
    progress_manager: ProgressManager,
    memory_manager=None
) -> List[BaseHook]:
    """创建默认钩子集合"""
    return [
        ReReadPlanHook(task_plan_manager),
        CheckDependenciesHook(),
        UpdateStatusHook(task_plan_manager, progress_manager),
        VerifyCompletionHook(task_plan_manager),
        LogProgressHook(progress_manager),
        MemorySyncHook(memory_manager) if memory_manager else None,
        ErrorRecoveryHook(),
    ]
