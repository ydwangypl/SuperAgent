#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务执行器

负责任务的实际执行、超时控制、结果收集
"""

import asyncio
import logging
import aiofiles
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from .models import (
    TaskExecution,
    TaskStatus,
    ExecutionContext
)
from .agent_factory import AgentFactory
from common.models import AgentType
from execution import AgentContext, AgentConfig


logger = logging.getLogger(__name__)


class TaskExecutor:
    """任务执行器"""

    def __init__(self, context: ExecutionContext) -> None:
        """初始化任务执行器

        Args:
            context: 执行上下文
        """
        self.context: ExecutionContext = context
        self.running_tasks: Dict[str, TaskExecution] = {}
        self._active_async_tasks: Dict[str, asyncio.Task] = {}  # 存储实际的 asyncio.Task
        self._lock: asyncio.Lock = asyncio.Lock()  # 用于同步操作的锁

    async def _persist_artifacts(
        self,
        artifacts: List[Any],
        project_root: Path,
        worktree_path: Optional[Path] = None
    ):
        """将 Agent 生成的工件持久化到磁盘"""
        # 审计优化: 将结果持久化到 artifacts 目录
        artifacts_dir = project_root / "artifacts"
        if worktree_path:
            artifacts_dir = worktree_path / "artifacts"

        artifacts_dir.mkdir(parents=True, exist_ok=True)

        for i, artifact in enumerate(artifacts):
            file_path = artifacts_dir / f"result_{i}.json"
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(str(artifact))

    async def execute(self, task: TaskExecution, timeout: int = 3600) -> TaskExecution:
        """执行任务 (线程安全且支持物理取消)"""
        logger.info(f"开始执行任务: {task.task_id}")

        async with self._lock:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self.running_tasks[task.task_id] = task

            # 创建并记录实际的 asyncio Task
            coro = self._execute_task_with_timeout(task, timeout)
            async_task = asyncio.create_task(coro)
            self._active_async_tasks[task.task_id] = async_task

        try:
            return await async_task
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            task.error = "任务被用户或系统物理取消"
            logger.warning(f"任务已被物理取消并成功中断: {task.task_id}")
            return task
        finally:
            async with self._lock:
                self._active_async_tasks.pop(task.task_id, None)
                self.running_tasks.pop(task.task_id, None)

    async def _execute_task_with_timeout(self, task: TaskExecution, timeout: int) -> TaskExecution:
        """内部带超时处理的执行逻辑"""
        try:
            result = await asyncio.wait_for(
                self._execute_task(task),
                timeout=timeout
            )
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.outputs = result
            task.logs.append("任务执行成功")
            logger.info(f"任务执行成功: {task.task_id}")
        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = f"任务超时({timeout}秒)"
            logger.error(f"任务超时: {task.task_id}")
        except (ValueError, TypeError, AttributeError) as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = f"任务参数或配置错误: {str(e)}"
            logger.error(f"任务执行失败 (配置错误): {task.task_id}, 错误: {e}")
        except (RuntimeError, OSError) as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = f"任务执行遇到运行时或系统错误: {str(e)}"
            logger.error(f"任务执行失败 (运行时/系统错误): {task.task_id}, 错误: {e}")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = f"任务执行遇到非预期异常 ({type(e).__name__}): {str(e)}"
            logger.error(f"任务执行失败 (非预期异常): {task.task_id}, 错误类型: {type(e).__name__}, 错误内容: {e}")

        return task

    async def _execute_task(self, task: TaskExecution) -> Dict[str, Any]:
        """执行任务的具体实现

        Args:
            task: 任务执行对象

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 获取Agent类型
        # 审计优化: 从 task.agent_type 直接获取 (如果存在)
        agent_type = getattr(task, 'agent_type', None)
        if not agent_type:
            agent_type_str = task.inputs.get("agent_type")
            if not agent_type_str:
                raise ValueError(f"任务 {task.task_id} 缺少agent_type")
            try:
                agent_type = AgentType(agent_type_str)
            except (ValueError, KeyError):
                raise ValueError(f"不支持的Agent类型: {agent_type_str}")

        # 获取或创建Agent实例 (每个任务使用独立的Agent实例以确保隔离性)
        # 创建Agent配置
        agent_config = AgentConfig(
            agent_type=agent_type,
            # 审计优化: 从配置中读取 agent_id 或生成唯一 ID
            agent_id=f"{agent_type.value}-{task.task_id}",
            project_root=self.context.project_root,
            worktree_path=task.worktree_path or self.context.worktree_path,
        )

        # 准备上下文
        agent_context = AgentContext(
            config=agent_config,
            env_vars=self.context.environment,
            metadata=task.inputs
        )

        # 获取 Agent
        agent = AgentFactory.get_agent(agent_type, agent_context)

        # 执行任务
        description = task.inputs.get("description", "执行任务")
        result = await agent.run(description)

        # 5. 持久化产出物 (如果有)
        if hasattr(result, 'artifacts') and result.artifacts:
            await self._persist_artifacts(
                result.artifacts,
                self.context.project_root,
                task.worktree_path
            )

        return result if isinstance(result, dict) else {"result": str(result)}

    async def execute_batch(
        self,
        task_executions: list[TaskExecution],
        max_concurrent: int = 3
    ) -> list[TaskExecution]:
        """批量执行任务(并行)

        Args:
            task_executions: 任务执行对象列表
            max_concurrent: 最大并发数

        Returns:
            list[TaskExecution]: 更新后的任务执行对象列表
        """
        logger.info(f"批量执行 {len(task_executions)} 个任务, 最大并发数: {max_concurrent}")

        # 创建信号量控制并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_semaphore(task: TaskExecution):
            async with semaphore:
                return await self.execute(task)

        # 并发执行所有任务
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in task_executions],
            return_exceptions=True
        )

        # 处理结果
        executed_tasks = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 执行失败
                task = task_executions[i]
                task.status = TaskStatus.FAILED
                task.error = f"并发执行异常 ({type(result).__name__}): {result}"
                task.completed_at = datetime.now()
                logger.error(f"批量执行任务失败 ({task.task_id}): {type(result).__name__}: {result}")
                executed_tasks.append(task)
            else:
                executed_tasks.append(result)

        return executed_tasks

    async def cancel_task(self, task_id: str) -> bool:
        """取消正在运行的任务 (带物理取消支持)"""
        async with self._lock:
            if task_id not in self._active_async_tasks:
                logger.warning(f"任务未在运行或无法物理取消: {task_id}")
                return False

            # 获取物理 asyncio.Task 并尝试取消
            async_task = self._active_async_tasks.get(task_id)
            if async_task and not async_task.done():
                async_task.cancel()
                logger.info(f"已向任务发送取消信号: {task_id}")
                return True

            return False

    def get_running_task_count(self) -> int:
        """获取正在运行的任务数

        Returns:
            int: 运行中的任务数
        """
        return len(self.running_tasks)

    def get_task_by_id(self, task_id: str) -> Optional[TaskExecution]:
        """根据ID获取任务

        Args:
            task_id: 任务ID

        Returns:
            Optional[TaskExecution]: 任务执行对象
        """
        return self.running_tasks.get(task_id)
