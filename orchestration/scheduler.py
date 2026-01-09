#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务调度器 (TaskScheduler)
负责任务依赖解析、批处理与执行顺序管理
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from planning.models import ExecutionPlan
from .models import TaskExecution, TaskStatus, ExecutionPriority

logger = logging.getLogger(__name__)

class TaskScheduler:
    """任务调度逻辑抽象"""

    def __init__(self, config: Any, agent_dispatcher: Any):
        self.config = config
        self.agent_dispatcher = agent_dispatcher
        self.task_executions: Dict[str, TaskExecution] = {}

    def create_task_executions(self, plan: ExecutionPlan) -> List[TaskExecution]:
        """从执行计划创建任务执行对象"""
        task_executions = []
        for step in plan.steps:
            task = TaskExecution(
                task_id=f"task-{step.id}",
                step_id=step.id,
                status=TaskStatus.PENDING,
                priority=ExecutionPriority.NORMAL,
                dependencies=step.dependencies
            )
            task.inputs = step.inputs.copy()
            task.inputs.update({
                "name": step.name,
                "description": step.description,
                "agent_type": step.agent_type.value
            })
            self.task_executions[task.task_id] = task
            task_executions.append(task)
            logger.debug(f"创建任务: {task.task_id} ({step.name})")
        return task_executions

    def find_ready_tasks(
        self,
        remaining: List[TaskExecution],
        executed: List[TaskExecution]
    ) -> List[TaskExecution]:
        """找出就绪的任务"""
        ready_tasks = []
        executed_ids = {t.step_id for t in executed if t.status == TaskStatus.COMPLETED}

        for task in remaining:
            dependencies_met = all(
                dep_id in executed_ids for dep_id in task.dependencies
            )
            if dependencies_met:
                task.status = TaskStatus.READY
                ready_tasks.append(task)
        return ready_tasks

    async def execute_batch(
        self,
        tasks: List[TaskExecution],
        worktree_creator_callback: Optional[Any] = None
    ) -> List[TaskExecution]:
        """执行一批任务"""
        if worktree_creator_callback:
            for task in tasks:
                await worktree_creator_callback(task)

        if self.config.enable_parallel_execution and len(tasks) > 1:
            logger.info(f"并行执行 {len(tasks)} 个任务")
            results = await self.agent_dispatcher.execute_batch(
                tasks,
                self.config.max_parallel_tasks
            )
        else:
            logger.info(f"串行执行 {len(tasks)} 个任务")
            results = []
            for task in tasks:
                result = await self.agent_dispatcher.execute_with_agent(task)
                results.append(result)
        return results
