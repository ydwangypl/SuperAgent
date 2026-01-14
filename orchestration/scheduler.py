#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务调度器 (TaskScheduler)
负责任务依赖解析、批处理与执行顺序管理
"""

import logging
from typing import List, Dict, Any, Optional

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

    async def schedule_and_run(
        self,
        plan: ExecutionPlan,
        executor: Any,
        worktree_creator_callback: Optional[Any] = None
    ) -> List[TaskExecution]:
        """调度并运行整个计划"""
        # 1. 创建任务执行记录
        remaining = self.create_task_executions(plan)
        executed = []

        logger.info(f"调度器开始执行计划: {plan.project_id}, 总任务数: {len(remaining)}")

        # 2. 调度循环
        while remaining:
            # 2.1 找出就绪的任务
            ready_tasks = self.find_ready_tasks(remaining, executed)

            if not ready_tasks:
                if remaining:
                    # 如果还有剩余任务但没有就绪任务,说明存在循环依赖
                    logger.error("检测到循环依赖,无法继续执行")
                    for t in remaining:
                        t.status = TaskStatus.FAILED
                        t.error = "循环依赖导致任务无法就绪"
                        executed.append(t)
                    break
                else:
                    break

            # 2.2 执行当前批次
            logger.info(f"调度批次: {len(ready_tasks)} 个就绪任务")
            batch_results = await self.execute_batch(ready_tasks, worktree_creator_callback)

            # 2.3 更新状态
            for task in batch_results:
                executed.append(task)
                # 从剩余任务中移除
                remaining = [t for t in remaining if t.task_id != task.task_id]

            # 2.4 检查是否有失败任务(如果配置了失败即停止)
            if any(t.status == TaskStatus.FAILED for t in batch_results):
                logger.warning("批次中有任务失败,根据策略停止调度")
                # 将剩余任务标记为取消
                for t in remaining:
                    t.status = TaskStatus.CANCELLED
                    executed.append(t)
                remaining = []
                break

        logger.info(f"计划执行完成: {plan.project_id}, 完成任务: {len(executed)}")
        return executed

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
