#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent调度器

负责任务到Agent的分配、负载均衡、资源管理
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import (
    TaskExecution,
    TaskStatus,
    AgentAssignment,
    AgentResource,
    ExecutionPriority
)
from .task_executor import TaskExecutor
from .registry import AgentRegistry
from common.models import AgentType


logger = logging.getLogger(__name__)


class AgentDispatcher:
    """Agent调度器 (Phase 3 重构版：基于 Registry 管理资源)"""

    def __init__(self, agent_resources: Optional[Dict[str, AgentResource]] = None) -> None:
        """初始化Agent调度器"""
        self.agent_resources: Dict[str, AgentResource] = (
            agent_resources or self._init_resources_from_registry()
        )
        self.task_executor: Optional[TaskExecutor] = None
        self.assignments: Dict[str, AgentAssignment] = {}
        self._lock: asyncio.Lock = asyncio.Lock()
        self._resource_available: asyncio.Condition = asyncio.Condition(self._lock)

    def _init_resources_from_registry(self) -> Dict[str, AgentResource]:
        """从注册中心自动初始化资源配置"""
        resources = {}
        for atype in AgentRegistry.get_all_types():
            resources[atype.value] = AgentResource(
                agent_type=atype.value,
                max_concurrent=AgentRegistry.get_max_concurrent(atype)
            )
        return resources

    async def assign_agent(
        self,
        task: TaskExecution,
        preferred_agent: Optional[str] = None,
        timeout: Optional[int] = 300
    ) -> Optional[AgentAssignment]:
        """为任务分配Agent (优化类型识别)"""
        start_time = datetime.now()

        async with self._resource_available:
            # 1. 确定目标 Agent 类型 (支持字符串和枚举)
            agent_type_val = preferred_agent

            if not agent_type_val:
                agent_type_val = task.inputs.get("agent_type")

            if not agent_type_val:
                agent_type_val = getattr(task, 'agent_type', None)

            if not agent_type_val:
                agent_type_val = getattr(task, 'agent_type', None)

            if not agent_type_val:
                metadata = getattr(task, 'metadata', {})
                if isinstance(metadata, dict):
                    agent_type_val = metadata.get('agent_type')

            # 2. 规范化为字符串值
            if isinstance(agent_type_val, AgentType):
                agent_type_val = agent_type_val.value

            if not agent_type_val:
                logger.error(f"无法确定任务 {task.task_id} 的Agent类型")
                return None

            # 3. 检查资源定义 (如果 registry 中有新类型但资源池没初始化，动态补全)
            if agent_type_val not in self.agent_resources:
                atype_enum = AgentRegistry.from_string(agent_type_val)
                if atype_enum:
                    self.agent_resources[agent_type_val] = AgentResource(
                        agent_type=agent_type_val,
                        max_concurrent=AgentRegistry.get_max_concurrent(atype_enum)
                    )
                else:
                    logger.error(f"未找到Agent类型定义: {agent_type_val}")
                    return None

            resource = self.agent_resources[agent_type_val]

            # 4. 循环等待资源
            while resource.current_load >= resource.max_concurrent:
                if timeout is not None:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed >= timeout:
                        logger.warning(
                            f"任务 {task.task_id} 等待 Agent {agent_type_val} 资源超时"
                        )
                        return None

                    wait_time = timeout - elapsed
                    try:
                        await asyncio.wait_for(
                            self._resource_available.wait(),
                            timeout=wait_time
                        )
                    except asyncio.TimeoutError:
                        return None
                else:
                    await self._resource_available.wait()

            # 5. 执行分配
            assignment = AgentAssignment(
                agent_type=agent_type_val,
                agent_id=f"{agent_type_val}-{uuid.uuid4().hex[:6]}",
                assigned_at=datetime.now()
            )

            task.assignment = assignment
            task.status = TaskStatus.ASSIGNED
            resource.current_load += 1
            resource.total_executions += 1
            self.assignments[task.task_id] = assignment

            logger.info(
                f"任务 {task.task_id} -> {assignment.agent_id} "
                f"({resource.current_load}/{resource.max_concurrent})"
            )
            return assignment

    async def release_agent(
        self,
        task_id: str,
        success: bool = True,
        duration: float = 0.0
    ) -> None:
        """释放Agent资源并更新统计信息

        Args:
            task_id: 任务ID
            success: 任务是否执行成功
            duration: 任务执行时长(秒)
        """
        async with self._resource_available:
            if task_id not in self.assignments:
                logger.warning(f"未找到任务 {task_id} 的Agent分配")
                return

            assignment = self.assignments[task_id]
            agent_type = assignment.agent_type

            # 减少资源负载并更新统计
            if agent_type in self.agent_resources:
                resource = self.agent_resources[agent_type]
                resource.current_load = max(0, resource.current_load - 1)

                if success:
                    resource.successful_executions += 1
                else:
                    resource.failed_executions += 1

                # 更新平均时长
                if resource.average_duration is None:
                    resource.average_duration = duration
                else:
                    # 移动平均算法
                    total_done = (resource.successful_executions +
                                  resource.failed_executions)
                    if total_done > 1:
                        resource.average_duration = (
                            (resource.average_duration * (total_done - 1) + duration) /
                            total_done
                        )
                    else:
                        resource.average_duration = duration

            # 移除分配记录
            del self.assignments[task_id]

            # 通知其他等待中的任务
            self._resource_available.notify_all()

            logger.info(f"已释放任务 {task_id} 的Agent资源 ({agent_type}), 成功: {success}")

    def get_available_agents(self) -> List[str]:
        """获取可用的Agent类型列表

        Returns:
            List[str]: 可用的Agent类型
        """
        available = []

        for agent_type, resource in self.agent_resources.items():
            if resource.current_load < resource.max_concurrent:
                available.append(agent_type)

        return available

    def get_agent_load(self, agent_type: str) -> tuple[int, int]:
        """获取Agent负载情况

        Args:
            agent_type: Agent类型

        Returns:
            tuple[int, int]: (当前负载, 最大并发数)
        """
        if agent_type not in self.agent_resources:
            return (0, 0)

        resource = self.agent_resources[agent_type]
        return (resource.current_load, resource.max_concurrent)

    async def execute_with_agent(
        self,
        task: TaskExecution,
        preferred_agent: Optional[str] = None
    ) -> TaskExecution:
        """使用分配的Agent执行任务 (带资源生命周期管理)

        Args:
            task: 任务执行对象
            preferred_agent: 优先使用的Agent类型

        Returns:
            TaskExecution: 更新后的任务执行对象
        """
        # 分配Agent (会自动等待资源)
        assignment = await self.assign_agent(task, preferred_agent)

        if not assignment:
            task.status = TaskStatus.FAILED
            task.error = "无法分配Agent资源 (等待超时或类型不支持)"
            task.completed_at = datetime.now()
            return task

        start_time = datetime.now()
        success = False
        duration = 0.0

        try:
            # 执行任务
            if self.task_executor:
                result_task = await self.task_executor.execute(task)
                success = result_task.status == TaskStatus.COMPLETED
                return result_task
            else:
                # 模拟执行
                await asyncio.sleep(0.1)
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                success = True
                task.result = {
                    "agent_id": assignment.agent_id,
                    "agent_type": assignment.agent_type,
                    "output": f"任务由 {assignment.agent_id} 完成"
                }
                return task

        except Exception as e:
            logger.exception(f"执行任务 {task.task_id} 时发生未捕获异常 ({type(e).__name__}): {e}")
            task.status = TaskStatus.FAILED
            task.error = f"执行异常 ({type(e).__name__}): {str(e)}"
            task.completed_at = datetime.now()
            success = False
            return task
        finally:
            # 计算时长
            duration = (datetime.now() - start_time).total_seconds()
            # 释放Agent资源
            await self.release_agent(task.task_id, success=success, duration=duration)

    async def execute_batch(
        self,
        tasks: List[TaskExecution],
        max_concurrent: int = 3
    ) -> List[TaskExecution]:
        """批量执行任务 (尊重资源限制和优先级)

        Args:
            tasks: 任务列表
            max_concurrent: 总最大并行任务数

        Returns:
            List[TaskExecution]: 更新后的任务列表
        """
        logger.info(f"批量执行 {len(tasks)} 个任务, 总并发限制: {max_concurrent}")

        # 按优先级排序
        priority_order = {
            ExecutionPriority.CRITICAL: 0,
            ExecutionPriority.HIGH: 1,
            ExecutionPriority.NORMAL: 2,
            ExecutionPriority.LOW: 3
        }

        sorted_tasks = sorted(
            tasks,
            key=lambda t: priority_order.get(t.priority, 2)
        )

        # 使用信号量限制总并发
        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_one(task: TaskExecution):
            async with semaphore:
                # 调用 execute_with_agent 确保资源管理逻辑生效
                return await self.execute_with_agent(task)

        # 并发执行所有任务 (每个任务内部会等待各自 Agent 类型的资源)
        results = await asyncio.gather(
            *[execute_one(task) for task in sorted_tasks],
            return_exceptions=True
        )

        # 处理结果和可能的异常
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task = sorted_tasks[i]
                task.status = TaskStatus.FAILED
                task.error = f"未捕获的任务执行异常 ({type(result).__name__}): {str(result)}"
                task.completed_at = datetime.now()
                final_results.append(task)
            else:
                final_results.append(result)

        return final_results

    def get_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取Agent统计信息

        Returns:
            Dict[str, Dict[str, Any]]: Agent统计信息
        """
        stats = {}

        for agent_type, resource in self.agent_resources.items():
            current, max_c = self.get_agent_load(agent_type)

            stats[agent_type] = {
                "current_load": current,
                "max_concurrent": max_c,
                "utilization": f"{(current / max_c * 100):.1f}%" if max_c > 0 else "0%",
                "total_executions": resource.total_executions,
                "successful_executions": resource.successful_executions,
                "failed_executions": resource.failed_executions,
                "average_duration": resource.average_duration
            }

        return stats
