#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
编排器(Orchestrator)

SuperAgent的核心协调引擎,负责任务编排、Agent调度、执行管理
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import aiofiles
from planning.models import ExecutionPlan, Step
from common.monitoring import MetricsManager, monitor_task_duration
from common.exceptions import ExecutionError, MemorySystemError, AgentError

from .base import BaseOrchestrator
from .models import (
    TaskExecution,
    TaskStatus,
    ExecutionContext,
    ExecutionResult,
    OrchestrationState,
    OrchestrationConfig,
    AgentResource,
    ExecutionPriority
)
from .worktree_manager import GitWorktreeManager
from .task_executor import TaskExecutor
from .distributed_executor import DistributedTaskExecutor
from .agent_dispatcher import AgentDispatcher
from .error_recovery import ErrorRecoverySystem
from .review_orchestrator import ReviewOrchestrator
from .scheduler import TaskScheduler
from .result_handler import ExecutionResultHandler
from .worktree_orchestrator import WorktreeOrchestrator
from config.settings import SuperAgentConfig, load_config


logger = logging.getLogger(__name__)

# 记忆管理层
try:
    from memory import MemoryManager
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    MemoryManager = None
    logger.warning("记忆管理层不可用")


class Orchestrator(BaseOrchestrator):
    """SuperAgent编排器 (重构版 - 关注点分离)"""

    def __init__(
        self,
        project_root: Path,
        config: Optional[OrchestrationConfig] = None,
        global_config: Optional[SuperAgentConfig] = None
    ) -> None:
        """初始化编排器"""
        super().__init__(project_root, config)
        self.global_config = global_config or load_config(project_root=self.project_root)

        # 1. 初始化执行上下文
        self.context = ExecutionContext(project_root=self.project_root)

        # 2. 初始化底层组件 (Executor & Dispatcher)
        self.task_executor = self._init_executor()
        self.agent_dispatcher = self._init_dispatcher()

        # 3. 初始化外部服务 (Memory & Recovery)
        self.memory_manager = MemoryManager(self.project_root) if MEMORY_AVAILABLE else None
        self.error_recovery = ErrorRecoverySystem(self.memory_manager) if self.memory_manager else None

        # 4. 初始化子编排器
        self.review_orchestrator = ReviewOrchestrator(self.project_root, self.config, self.agent_dispatcher)
        
        # 5. 初始化业务逻辑组件 (解耦核心)
        try:
            worktree_mgr = GitWorktreeManager(self.project_root, self.config.worktree)
        except ValueError:
            worktree_mgr = None
        
        self.worktree_orchestrator = WorktreeOrchestrator(self.project_root, worktree_mgr)
        self.scheduler = TaskScheduler(self.config, self.agent_dispatcher)
        
        # 执行状态
        self.state = OrchestrationState(
            project_id=f"project-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            total_tasks=0
        )
        self.result_handler = ExecutionResultHandler(self.state, self.memory_manager)

    def _init_executor(self):
        """初始化任务执行器"""
        if self.global_config.distribution.enabled:
            try:
                executor = DistributedTaskExecutor(self.context, self.global_config)
                logger.info("分布式任务执行器已启用")
                return executor
            except Exception as e:
                logger.error(f"分布式任务执行器启动失败: {type(e).__name__}: {e}。自动降级。")
        
        logger.info("本地任务执行器已启用")
        return TaskExecutor(self.context)

    def _init_dispatcher(self) -> AgentDispatcher:
        """初始化Agent调度器"""
        if not self.config.agent_resources:
            from common.models import AgentType
            self.config.agent_resources = {
                agent_type.value: AgentResource(
                    agent_type=agent_type.value,
                    available_instances=1,
                    max_concurrent=self.config.max_concurrent_per_agent
                ) for agent_type in AgentType
            }
        
        dispatcher = AgentDispatcher(self.config.agent_resources)
        dispatcher.task_executor = self.task_executor
        return dispatcher

    @monitor_task_duration(agent_type="orchestrator")
    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionResult:
        """
        执行完整的项目计划。
        
        该方法是 Orchestrator 的核心入口，执行流程包括：
        1. 初始化执行上下文和状态统计。
        2. 查询相关历史记忆以优化当前执行。
        3. 委托 Scheduler 创建具体的任务执行对象。
        4. 按依赖关系并行或串行执行任务，并为敏感任务创建隔离的 Worktree。
        5. 委托 ResultHandler 汇总执行结果。
        6. 调用 ReviewOrchestrator 进行自动化代码审查。
        7. 清理临时资源（如 Worktree）。
        8. 在执行失败时，通过 ErrorRecoverySystem 记录教训并存入记忆。

        Args:
            plan: 经过规划器生成的 ExecutionPlan 对象。

        Returns:
            ExecutionResult: 包含执行进度、成功标志、审查报告和错误信息的汇总对象。

        Raises:
            ExecutionError: 核心流程执行异常。
            MemorySystemError: 记忆系统操作异常。
        """
        logger.info(f"开始执行项目计划: {self.state.project_id} (步骤数: {len(plan.steps)})")

        self.state.status = TaskStatus.RUNNING
        self.state.started_at = datetime.now()
        self.state.total_tasks = len(plan.steps)
        
        # 预先初始化结果对象，防止异常时未定义
        result = ExecutionResult(
            success=False,
            project_id=self.state.project_id,
            total_tasks=self.state.total_tasks,
            completed_tasks=0,
            failed_tasks=0
        )

        try:
            # 步骤0: 查询相关记忆
            if self.memory_manager:
                await self.memory_manager.query_relevant_memory(task=plan.description, agent_type=None)

            # 步骤1: 创建任务执行对象 (委托给 Scheduler)
            task_executions = self.scheduler.create_task_executions(plan)

            # 步骤2: 按依赖关系分组执行 (核心循环)
            executed_tasks = await self._execute_by_dependencies(task_executions, plan)

            # 步骤3: 收集结果 (委托给 ResultHandler)
            result = self.result_handler.collect_results(executed_tasks)

            # 步骤4: 代码审查
            result.code_review_summary = await self.review_orchestrator.run_review(
                self.state.project_id, executed_tasks
            )

            # 步骤5: 清理 (委托给 WorktreeOrchestrator)
            if self.config.worktree.auto_cleanup:
                await self.worktree_orchestrator.cleanup_all()

        except Exception as e:
            logger.error(f"执行计划失败 ({type(e).__name__}): {e}")
            result.success = False
            result.errors.append(str(e))
            result.completed_tasks = self.state.completed_tasks
            result.failed_tasks = self.state.failed_tasks
            
            if self.memory_manager:
                # 增强监控元数据
                error_context = (
                    f"项目执行: {self.state.project_id}\n"
                    f"任务描述: {plan.description}\n"
                    f"状态统计: 已完成 {self.state.completed_tasks}, 失败 {self.state.failed_tasks}, 总计 {self.state.total_tasks}\n"
                    f"运行时长: {(datetime.now() - self.state.started_at).total_seconds():.2f}s"
                )
                
                learning = (
                    f"在项目 {self.state.project_id} 执行期间发生非预期异常。\n"
                    f"执行进度: {self.state.completed_tasks}/{self.state.total_tasks}\n"
                    f"异常详情: {str(e)}"
                )
                
                await self.memory_manager.save_mistake(
                    error=e, 
                    context=error_context,
                    fix="检查系统日志，分析执行过程中的具体失败点并尝试手动恢复或调整计划。",
                    learning=learning
                )
        finally:
            self.state.completed_at = datetime.now()
            self.state.status = TaskStatus.COMPLETED
            result.completed_at = self.state.completed_at

        result.success = (result.failed_tasks == 0 and result.completed_tasks == result.total_tasks)
        logger.info(f"计划执行完成: {result.completed_tasks}/{result.total_tasks} 成功, 耗时 {result.duration_seconds}s")
        return result

    async def _execute_by_dependencies(
        self,
        tasks: List[TaskExecution],
        plan: ExecutionPlan
    ) -> List[TaskExecution]:
        """按依赖关系执行任务 (重构版)"""
        executed = []
        remaining = tasks.copy()

        while remaining:
            ready_tasks = self.scheduler.find_ready_tasks(remaining, executed)
            if not ready_tasks:
                if remaining: logger.error("检测到可能的循环依赖")
                break

            logger.info(f"执行批次: {len(ready_tasks)} 个任务")
            
            # 定义 Worktree 创建回调
            async def create_wt(task):
                step = plan.get_step_by_id(task.step_id)
                if step: await self.worktree_orchestrator.create_for_task(task, step.agent_type.value)

            # 执行批次 (委托给 Scheduler)
            batch_results = await self.scheduler.execute_batch(ready_tasks, worktree_creator_callback=create_wt)

            # 后处理: 同步 Worktree + 保存记忆 + 更新状态
            for task in batch_results:
                await self.worktree_orchestrator.sync_to_root(task)
                await self.result_handler.save_task_memory(task, plan.description)
            
            executed.extend(batch_results)
            remaining = [t for t in remaining if t not in batch_results]
            self.result_handler.update_state(executed)

            # 快速失败逻辑
            if self.config.enable_early_failure and any(t.status == TaskStatus.FAILED for t in batch_results):
                logger.error("检测到任务失败, 停止后续执行")
                for task in remaining:
                    task.status = TaskStatus.SKIPPED
                executed.extend(remaining)
                break

        return executed

    def get_status(self) -> OrchestrationState:
        """获取当前编排状态"""
        return self.state

    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        stats = {
            "total": self.state.total_tasks,
            "completed": self.state.completed_tasks,
            "failed": self.state.failed_tasks,
            "running": self.task_executor.get_running_task_count(),
            "agent_stats": self.agent_dispatcher.get_statistics()
        }
        if self.memory_manager:
            stats["memory_stats"] = self.memory_manager.get_statistics()
        if self.error_recovery:
            stats["error_recovery_stats"] = self.error_recovery.get_statistics()
        return stats
