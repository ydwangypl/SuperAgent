#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Executor适配器

连接新的Executor抽象层和现有的Agent系统。

职责:
1. 将Executor的执行请求转换为Agent任务
2. 管理Agent实例的生命周期
3. 转换执行结果格式
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
import uuid

from core.executor import Executor, Task, ExecutionResult, TaskStatus, TaskExecutionError
from execution.base_agent import BaseAgent
from execution.models import AgentContext, AgentConfig, AgentResult, AgentStatus
from orchestration.models import TaskExecution, ExecutionPriority
from orchestration.agent_factory import AgentFactory
from common.models import AgentType


logger = logging.getLogger(__name__)


class AgentExecutor(Executor):
    """
    基于Agent的Executor实现

    这个Executor将新的Executor接口适配到现有的Agent系统。

    示例:
        executor = AgentExecutor(project_root, AgentType.BACKEND_DEV)
        task = Task(task_type="code", description="创建API")
        result = await executor.execute(task)
    """

    def __init__(
        self,
        project_root: Path,
        agent_type: AgentType,
        name: Optional[str] = None,
        config: Optional[AgentConfig] = None
    ):
        """
        初始化Agent执行器

        Args:
            project_root: 项目根目录
            agent_type: Agent类型
            name: 执行器名称
            config: Agent配置
        """
        super().__init__(name)
        self.project_root = project_root
        self.agent_type = agent_type
        self.config = config or AgentConfig()

    def get_supported_types(self) -> List[str]:
        """获取支持的任务类型"""
        # 根据Agent类型返回支持的任务类型
        type_mapping = {
            AgentType.BACKEND_DEV: ["code", "backend", "api"],
            AgentType.FRONTEND_DEV: ["code", "frontend", "ui"],
            AgentType.FULL_STACK_DEV: ["code", "fullstack"],
            AgentType.QA_ENGINEERING: ["test", "testing"],
            AgentType.TECHNICAL_WRITING: ["documentation", "doc"],
            AgentType.CODE_REFACTORING: ["refactor", "refactoring"],
            AgentType.DATABASE_DESIGN: ["database", "db", "schema"],
            AgentType.API_DESIGN: ["api", "interface"],
        }
        return type_mapping.get(self.agent_type, ["code"])

    def execute(self, task: Task) -> ExecutionResult:
        """
        执行任务 - 同步接口

        注意: 底层Agent是异步的,这里在同步函数中运行异步代码

        Args:
            task: 要执行的任务

        Returns:
            ExecutionResult: 执行结果
        """
        if not self.validate_task(task):
            return ExecutionResult(
                success=False,
                content=None,
                status=TaskStatus.FAILED,
                error=f"Invalid task: type={task.task_type}, description={task.description}"
            )

        # 运行异步执行
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果已经在事件循环中,创建任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._execute_async(task)
                    )
                    result = future.result(timeout=300)
            else:
                # 直接运行
                result = asyncio.run(self._execute_async(task))
        except Exception as e:
            logger.error(f"Executor {self.name} failed: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                content=None,
                status=TaskStatus.FAILED,
                error=str(e)
            )

        return result

    async def _execute_async(self, task: Task) -> ExecutionResult:
        """
        异步执行任务

        Args:
            task: 要执行的任务

        Returns:
            ExecutionResult: 执行结果
        """
        start_time = datetime.now()

        try:
            # 1. 创建TaskExecution
            task_execution = self._create_task_execution(task)

            # 2. 创建Agent实例
            agent = AgentFactory.create_agent(self.agent_type, config=self.config)

            # 3. 创建Agent上下文
            agent_context = self._create_agent_context(task, task_execution)

            # 4. 准备任务输入
            task_input = self._prepare_task_input(task)

            # 5. 执行Agent
            logger.info(f"Executor {self.name} executing task {task.task_id if hasattr(task, 'task_id') else 'unknown'}")
            agent_result = await agent.run(agent_context, task_input)

            # 6. 转换结果
            execution_time = (datetime.now() - start_time).total_seconds()

            if agent_result.success:
                return ExecutionResult(
                    success=True,
                    content=self._extract_content(agent_result),
                    status=TaskStatus.COMPLETED,
                    metadata=self._convert_metadata(agent_result),
                    execution_time=execution_time
                )
            else:
                return ExecutionResult(
                    success=False,
                    content=None,
                    status=TaskStatus.FAILED,
                    error=agent_result.error or "Agent execution failed",
                    metadata={"agent_logs": agent_result.logs},
                    execution_time=execution_time
                )

        except Exception as e:
            logger.error(f"Error in _execute_async: {e}", exc_info=True)
            execution_time = (datetime.now() - start_time).total_seconds()
            return ExecutionResult(
                success=False,
                content=None,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )

    def _create_task_execution(self, task: Task) -> TaskExecution:
        """创建TaskExecution对象"""
        task_id = getattr(task, 'task_id', f"task-{uuid.uuid4().hex[:8]}")

        return TaskExecution(
            task_id=task_id,
            step_id=task.task_type,
            status=TaskStatus.PENDING,
            priority=ExecutionPriority.NORMAL,
            inputs={
                "description": task.description,
                "requirements": task.requirements,
                **task.context
            },
            created_at=datetime.now()
        )

    def _create_agent_context(
        self,
        task: Task,
        task_execution: TaskExecution
    ) -> AgentContext:
        """创建Agent上下文"""
        return AgentContext(
            project_root=self.project_root,
            task_id=task_execution.task_id,
            step_id=task_execution.step_id,
            worktree_path=None,  # 暂不使用worktree
            environment=task.context.get("environment", {}),
            dependencies=task.context.get("dependencies", []),
            previous_results=task.context.get("previous_results", {})
        )

    def _prepare_task_input(self, task: Task) -> Dict[str, Any]:
        """准备任务输入"""
        return {
            "description": task.description,
            "requirements": task.requirements,
            "context": task.context,
            "metadata": task.metadata
        }

    def _extract_content(self, agent_result: AgentResult) -> Any:
        """从Agent结果中提取内容"""
        # 优先返回artifacts
        if agent_result.artifacts:
            return [
                {
                    "id": a.artifact_id,
                    "type": a.artifact_type,
                    "path": str(a.path) if a.path else None,
                    "content": a.content
                }
                for a in agent_result.artifacts
            ]

        # 其次返回output
        if agent_result.output:
            return agent_result.output

        # 最后返回logs
        return agent_result.logs

    def _convert_metadata(self, agent_result: AgentResult) -> Dict[str, Any]:
        """转换Agent结果元数据"""
        return {
            "agent_id": agent_result.agent_id,
            "agent_name": agent_result.agent_name,
            "logs": agent_result.logs,
            "metrics": agent_result.metrics,
            "artifacts_count": len(agent_result.artifacts),
            "duration": agent_result.duration
        }


class ExecutorAdapter:
    """
    Executor适配器 - 管理多个AgentExecutor实例

    这个类作为高级接口,简化Executor的使用。

    示例:
        adapter = ExecutorAdapter(project_root)
        result = await adapter.execute("code", {"description": "创建API"})
    """

    def __init__(self, project_root: Path):
        """
        初始化适配器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self._executors: Dict[str, AgentExecutor] = {}

    def get_executor(self, task_type: str) -> AgentExecutor:
        """
        获取适合处理该任务类型的执行器

        Args:
            task_type: 任务类型

        Returns:
            AgentExecutor: 执行器实例
        """
        # 检查是否已有缓存的执行器
        if task_type in self._executors:
            return self._executors[task_type]

        # 映射任务类型到Agent类型
        agent_type = self._map_task_to_agent(task_type)

        # 创建新的执行器
        executor = AgentExecutor(
            project_root=self.project_root,
            agent_type=agent_type,
            name=f"{agent_type.value}_executor"
        )

        # 缓存执行器
        self._executors[task_type] = executor

        return executor

    def _map_task_to_agent(self, task_type: str) -> AgentType:
        """映射任务类型到Agent类型"""
        mapping = {
            # 代码生成
            "code": AgentType.BACKEND_DEV,
            "backend": AgentType.BACKEND_DEV,
            "api": AgentType.API_DESIGN,
            "frontend": AgentType.FRONTEND_DEV,
            "fullstack": AgentType.FULL_STACK_DEV,

            # 测试
            "test": AgentType.QA_ENGINEERING,
            "testing": AgentType.QA_ENGINEERING,

            # 文档
            "documentation": AgentType.TECHNICAL_WRITING,
            "doc": AgentType.TECHNICAL_WRITING,

            # 重构
            "refactor": AgentType.CODE_REFACTORING,
            "refactoring": AgentType.CODE_REFACTORING,

            # 数据库
            "database": AgentType.DATABASE_DESIGN,
            "db": AgentType.DATABASE_DESIGN,
            "schema": AgentType.DATABASE_DESIGN,
        }

        return mapping.get(task_type.lower(), AgentType.BACKEND_DEV)

    async def execute(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行任务 (异步接口)

        Args:
            task_type: 任务类型
            task_data: 任务数据
            context: 执行上下文

        Returns:
            执行结果字典
        """
        executor = self.get_executor(task_type)

        # 创建Task对象
        task = Task(
            task_type=task_type,
            description=task_data.get("description", ""),
            requirements=task_data.get("requirements", []),
            context=context or {},
            metadata=task_data.get("metadata", {})
        )

        # 执行任务
        result = await executor._execute_async(task)

        # 转换为字典格式
        return {
            "success": result.success,
            "content": result.content,
            "status": result.status.value,
            "error": result.error,
            "metadata": result.metadata,
            "execution_time": result.execution_time
        }

    def execute_sync(
        self,
        task_type: str,
        task_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行任务 (同步接口)

        Args:
            task_type: 任务类型
            task_data: 任务数据
            context: 执行上下文

        Returns:
            执行结果字典
        """
        executor = self.get_executor(task_type)

        # 创建Task对象
        task = Task(
            task_type=task_type,
            description=task_data.get("description", ""),
            requirements=task_data.get("requirements", []),
            context=context or {},
            metadata=task_data.get("metadata", {})
        )

        # 执行任务
        result = executor.execute(task)

        # 转换为字典格式
        return {
            "success": result.success,
            "content": result.content,
            "status": result.status.value,
            "error": result.error,
            "metadata": result.metadata,
            "execution_time": result.execution_time
        }
