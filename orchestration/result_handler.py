#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
执行结果处理器 (ExecutionResultHandler)
负责收集结果、更新状态、保存记忆
"""

import logging
from typing import List, Any
from datetime import datetime

from .models import TaskExecution, TaskStatus, ProjectExecutionResult, OrchestrationState

logger = logging.getLogger(__name__)


class ExecutionResultHandler:
    """结果处理逻辑抽象"""

    def __init__(self, state: OrchestrationState, memory_manager: Any = None):
        self.state = state
        self.memory_manager = memory_manager

    def collect_results(self, executed_tasks: List[TaskExecution]) -> ProjectExecutionResult:
        """汇总任务执行结果"""
        completed = [t for t in executed_tasks if t.status == TaskStatus.COMPLETED]
        failed = [t for t in executed_tasks if t.status == TaskStatus.FAILED]
        skipped = [t for t in executed_tasks if t.status == TaskStatus.SKIPPED]

        result = ProjectExecutionResult(
            success=(len(failed) == 0 and len(completed) + len(skipped) == self.state.total_tasks),
            project_id=self.state.project_id,
            total_tasks=self.state.total_tasks,
            completed_tasks=len(completed),
            failed_tasks=len(failed),
            started_at=self.state.started_at,
            completed_at=datetime.now()
        )

        for task in failed:
            if task.error:
                result.errors.append(f"Task {task.task_id} failed: {task.error}")

        return result

    def update_state(self, executed_tasks: List[TaskExecution]) -> None:
        """更新编排状态"""
        completed_count = sum(1 for t in executed_tasks if t.status == TaskStatus.COMPLETED)
        failed_count = sum(1 for t in executed_tasks if t.status == TaskStatus.FAILED)

        self.state.completed_tasks = completed_count
        self.state.failed_tasks = failed_count

        if self.state.total_tasks > 0:
            self.state.progress = (completed_count + failed_count) / self.state.total_tasks * 100

        msg = f"进度更新: {self.state.progress:.1f}% ({completed_count}/{self.state.total_tasks})"
        logger.debug(msg)

    async def save_task_memory(self, task: TaskExecution, plan_description: str) -> None:
        """保存任务执行到记忆系统"""
        if not self.memory_manager:
            return

        try:
            from memory.models import MemoryEntry, MemoryType

            # 创建情节记忆
            entry = MemoryEntry(
                memory_type=MemoryType.EPISODIC,
                content=f"Task {task.task_id} ({task.inputs.get('name')}) executed.",
                metadata={
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "plan_context": plan_description,
                    "agent_type": task.inputs.get("agent_type"),
                    "duration": task.duration_seconds
                }
            )

            if task.status == TaskStatus.COMPLETED:
                entry.content += f" Result: {str(task.result)[:200]}..."
            elif task.status == TaskStatus.FAILED:
                entry.content += f" Error: {task.error}"

            await self.memory_manager.save_memory(entry)

        except Exception as e:
            logger.warning(f"保存任务记忆失败 ({type(e).__name__}): {e}")
