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
from datetime import datetime, timedelta
from pathlib import Path

from .models import (
    TaskExecution,
    TaskStatus,
    ExecutionContext,
    ExecutionPriority
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
        self._lock: asyncio.Lock = asyncio.Lock() # 用于同步操作的锁

    async def _persist_artifacts(
        self,
        artifacts: List[Any],
        project_root: Path,
        worktree_path: Optional[Path] = None
    ):
        """将 Agent 生成的工件持久化到磁盘 (安全增强版)
        
        审计优化: 引入增强型路径验证、原子写入和符号链接检查，防止路径穿越
        """
        from common.security import validate_path, SecurityError
        
        for artifact in artifacts:
            if not artifact.path or not artifact.content:
                continue
            
            try:
                raw_path = Path(artifact.path)
                
                # 步骤1: 确定并验证目标基础目录
                # 如果提供了 worktree_path，优先使用它作为基础，否则使用 project_root
                target_base = worktree_path or project_root
                
                # 步骤2: 验证并构造最终安全路径
                try:
                    # 使用增强型路径验证函数
                    file_path = validate_path(raw_path, target_base)
                except SecurityError as se:
                    logger.error(f"安全策略阻止工件写入: {se}")
                    continue
                
                # 步骤3: 检查是否为恶意符号链接 (validate_path 已检查，这里做双重保险)
                if file_path.exists() and file_path.is_symlink():
                    logger.error(f"安全警报：不允许覆盖或通过符号链接写入: {file_path}")
                    continue
                
                # 步骤4: 创建父目录
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 步骤5: 原子性写入 (防止写入过程中的竞态条件或部分写入)
                temp_file = file_path.with_suffix(file_path.suffix + '.tmp')
                try:
                    async with aiofiles.open(temp_file, "w", encoding="utf-8") as f:
                        await f.write(artifact.content)
                    
                    # 步骤6: 原子重命名
                    # 在 Windows 上，如果目标文件已存在，replace 会失败，需要先删除
                    if file_path.exists():
                        file_path.unlink()
                    temp_file.replace(file_path)
                    
                    logger.info(f"工件已安全持久化: {file_path}")
                finally:
                    # 确保临时文件在出错时被清理
                    if temp_file.exists():
                        try:
                            temp_file.unlink()
                        except (OSError, IOError) as e:
                            logger.error(f"清理临时工件文件失败 (IO错误): {e}")
                        except Exception as e:
                            logger.error(f"清理临时工件文件时遇到非预期错误 ({type(e).__name__}): {e}")

            except SecurityError as e:
                logger.error(f"持久化工件失败 (安全策略违规) {artifact.path}: {e}")
            except (OSError, IOError) as e:
                logger.error(f"持久化工件失败 (系统或磁盘错误) {artifact.path}: {e}")
            except Exception as e:
                logger.error(f"持久化工件遇到未知异常 ({type(e).__name__}) {artifact.path}: {e}")

    async def execute(
        self,
        task_execution: TaskExecution,
        timeout: int = 3600
    ) -> TaskExecution:
        """执行任务 (线程安全且支持物理取消)"""
        logger.info(f"开始执行任务: {task_execution.task_id}")

        async with self._lock:
            task_execution.status = TaskStatus.RUNNING
            task_execution.started_at = datetime.now()
            self.running_tasks[task_execution.task_id] = task_execution

            # 创建并记录实际的 asyncio Task
            coro = self._execute_task_with_timeout(task_execution, timeout)
            async_task = asyncio.create_task(coro)
            self._active_async_tasks[task_execution.task_id] = async_task

        try:
            return await async_task
        except asyncio.CancelledError:
            task_execution.status = TaskStatus.CANCELLED
            task_execution.completed_at = datetime.now()
            task_execution.error = "任务被用户或系统物理取消"
            logger.warning(f"任务已被物理取消并成功中断: {task_execution.task_id}")
            return task_execution
        finally:
            async with self._lock:
                self._active_async_tasks.pop(task_execution.task_id, None)
                self.running_tasks.pop(task_execution.task_id, None)

    async def _execute_task_with_timeout(self, task_execution: TaskExecution, timeout: int) -> TaskExecution:
        """内部带超时处理的执行逻辑"""
        try:
            result = await asyncio.wait_for(
                self._execute_task(task_execution),
                timeout=timeout
            )
            task_execution.status = TaskStatus.COMPLETED
            task_execution.completed_at = datetime.now()
            task_execution.result = result
            task_execution.outputs = result
            task_execution.logs.append("任务执行成功")
            logger.info(f"任务执行成功: {task_execution.task_id}")
        except asyncio.TimeoutError:
            task_execution.status = TaskStatus.FAILED
            task_execution.completed_at = datetime.now()
            task_execution.error = f"任务超时({timeout}秒)"
            logger.error(f"任务超时: {task_execution.task_id}")
        except (ValueError, TypeError, AttributeError) as e:
            task_execution.status = TaskStatus.FAILED
            task_execution.completed_at = datetime.now()
            task_execution.error = f"任务参数或配置错误: {str(e)}"
            logger.error(f"任务执行失败 (配置错误): {task_execution.task_id}, 错误: {e}")
        except (RuntimeError, OSError) as e:
            task_execution.status = TaskStatus.FAILED
            task_execution.completed_at = datetime.now()
            task_execution.error = f"任务执行遇到运行时或系统错误: {str(e)}"
            logger.error(f"任务执行失败 (运行时/系统错误): {task_execution.task_id}, 错误: {e}")
        except Exception as e:
            task_execution.status = TaskStatus.FAILED
            task_execution.completed_at = datetime.now()
            task_execution.error = f"任务执行遇到非预期异常 ({type(e).__name__}): {str(e)}"
            logger.error(f"任务执行失败 (非预期异常): {task_execution.task_id}, 错误类型: {type(e).__name__}, 错误内容: {e}")
        
        return task_execution

    async def _execute_task(self, task_execution: TaskExecution) -> Dict[str, Any]:
        """执行任务的具体实现

        Args:
            task_execution: 任务执行对象

        Returns:
            Dict[str, Any]: 执行结果
        """
        # 获取Agent类型
        agent_type_str = task_execution.inputs.get("agent_type")
        if not agent_type_str:
            raise ValueError(f"任务 {task_execution.task_id} 缺少agent_type")

        # 转换为AgentType枚举
        try:
            agent_type = AgentType(agent_type_str)
        except (ValueError, KeyError):
            raise ValueError(f"不支持的Agent类型: {agent_type_str}")

        # 获取或创建Agent实例 (每个任务使用独立的Agent实例以确保隔离性)
        # 创建Agent配置
        agent_config = AgentConfig(
            timeout=3600,
            max_retries=3,
            enable_auto_review=True
        )

        # 使用工厂创建Agent (不再从缓存获取，保证并发安全)
        agent = AgentFactory.create_agent(agent_type, config=agent_config)

        # 创建Agent执行上下文
        # 审计优化: 优先使用任务关联的独立 worktree_path, 解决并行竞态问题
        worktree_path = task_execution.worktree_path or self.context.worktree_path

        agent_context = AgentContext(
            project_root=self.context.project_root,
            task_id=task_execution.task_id,
            step_id=task_execution.step_id,
            worktree_path=worktree_path
        )

        # 准备任务输入
        task_input = task_execution.inputs.copy()
        task_input.pop('agent_type', None)  # 移除agent_type,因为不需要传给Agent

        # 执行Agent
        logger.info(f"使用Agent {agent.agent_id} 执行任务 {task_execution.task_id}")
        try:
            agent_result = await agent.run(agent_context, task_input)
        except (RuntimeError, ValueError, AttributeError) as e:
            logger.error(f"Agent {agent.agent_id} 执行失败 (参数或运行时错误): {e}")
            raise
        except (OSError, IOError) as e:
            logger.error(f"Agent {agent.agent_id} 执行过程中遇到系统错误: {e}")
            raise
        except Exception as e:
            logger.exception(f"Agent {agent.agent_id} 执行过程中抛出非预期异常 ({type(e).__name__}): {e}")
            raise

        # 持久化工件
        if agent_result.success and agent_result.artifacts:
            await self._persist_artifacts(
                agent_result.artifacts,
                self.context.project_root,
                worktree_path=worktree_path
            )

        # 转换结果
        result = {
            "task_id": task_execution.task_id,
            "step_id": task_execution.step_id,
            "agent_id": agent.agent_id,
            "agent_type": agent_type_str,
            "status": agent_result.status.value,
            "success": agent_result.success,
            "message": agent_result.message,
            "artifacts": [
                {
                    "artifact_id": a.artifact_id,
                    "artifact_type": a.artifact_type,
                    "path": str(a.path) if a.path else None,
                    "content_length": len(a.content) if a.content else 0,
                    "quality_score": a.quality_score
                }
                for a in agent_result.artifacts
            ],
            "logs": agent_result.logs,
            "metrics": agent_result.metrics,
            "error": agent_result.error,
            "files": [
                str(a.path)
                for a in agent_result.artifacts
                if a.path
            ]
        }

        # 特殊处理：如果是修复任务，提取改进后的内容
        if agent_result.success and agent_result.artifacts:
            # 优先找 artifact_id 包含 'improved' 或 'fix' 的，或者第一个
            target_artifact = next(
                (a for a in agent_result.artifacts if "improved" in a.artifact_id or "fix" in a.artifact_id),
                agent_result.artifacts[0]
            )
            if target_artifact and target_artifact.content:
                result["improved_content"] = target_artifact.content

        return result

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
