#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务列表管理器 (TaskListManager)

管理任务的持久化状态,支持断点续传和进度可视化。
借鉴自 autonomous-coding 的 feature_list.json 模式。

v3.3 新增:
- TaskPlanManager 集成: JSON → MD 单向同步
- 自动更新 task_plan.md checkbox
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pathlib import Path

if TYPE_CHECKING:
    from planning.models import ExecutionPlan

logger = logging.getLogger(__name__)


@dataclass
class TaskItem:
    """任务项

    代表单个待执行任务,包含状态、依赖关系等信息。
    """
    id: str                                     # 任务 ID (例如: "task-001")
    description: str                            # 任务描述
    status: str = "pending"                     # pending | running | completed | failed
    assigned_agent: Optional[str] = None        # 分配的 Agent 类型
    test_steps: List[str] = field(default_factory=list)  # 测试步骤
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务 ID 列表

    # 时间信息
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    # 错误信息
    error: Optional[str] = None

    # 额外元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskItem':
        """从字典创建"""
        return cls(**data)


@dataclass
class TaskList:
    """任务列表

    管理所有任务的集合,提供统计和查询功能。
    """
    project_name: str                          # 项目名称
    total_tasks: int                           # 总任务数
    completed: int = 0                         # 已完成数量
    pending: int = 0                           # 待执行数量
    failed: int = 0                            # 失败数量
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    tasks: List[TaskItem] = field(default_factory=list)

    def update_statistics(self):
        """更新统计信息"""
        self.completed = sum(1 for t in self.tasks if t.status == "completed")
        self.pending = sum(1 for t in self.tasks if t.status == "pending")
        self.failed = sum(1 for t in self.tasks if t.status == "failed")
        self.last_updated = datetime.now().isoformat()

    def save(self, path: Path):
        """保存到文件

        Args:
            path: 保存路径 (通常是 tasks.json)
        """
        self.update_statistics()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
        logger.info(f"✅ 任务列表已保存: {path}")

    @classmethod
    def load(cls, path: Path) -> 'TaskList':
        """从文件加载

        Args:
            path: 文件路径

        Returns:
            TaskList 对象
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tasks = [TaskItem(**t) for t in data.pop('tasks', [])]
        return cls(tasks=tasks, **data)

    def get_next_pending(
        self,
        agent_type: Optional[str] = None
    ) -> Optional[TaskItem]:
        """获取下一个待执行任务

        Args:
            agent_type: 过滤特定 Agent 类型的任务

        Returns:
            下一个待执行的任务,如果没有则返回 None
        """
        # 过滤待执行任务
        pending_tasks = [
            t for t in self.tasks
            if t.status == "pending"
            and (agent_type is None or t.assigned_agent == agent_type)
            and self._dependencies_satisfied(t)
        ]

        return pending_tasks[0] if pending_tasks else None

    def _dependencies_satisfied(self, task: TaskItem) -> bool:
        """检查任务的依赖是否已满足

        Args:
            task: 任务对象

        Returns:
            是否满足依赖条件
        """
        for dep_id in task.dependencies:
            dep_task = next((t for t in self.tasks if t.id == dep_id), None)
            if not dep_task or dep_task.status != "completed":
                return False
        return True

    def mark_progress(
        self,
        task_id: str,
        status: str,
        error: Optional[str] = None
    ):
        """标记任务进度

        Args:
            task_id: 任务 ID
            status: 新状态 (pending | running | completed | failed)
            error: 错误信息 (可选)
        """
        for task in self.tasks:
            if task.id == task_id:
                task.status = status

                if status == "running":
                    task.started_at = datetime.now().isoformat()
                elif status in ["completed", "failed"]:
                    task.completed_at = datetime.now().isoformat()
                    if error:
                        task.error = error

                self.update_statistics()
                break

    def get_progress_report(self) -> Dict[str, Any]:
        """获取进度报告

        Returns:
            包含进度信息的字典
        """
        self.update_statistics()
        percentage = (self.completed / self.total_tasks * 100) if self.total_tasks > 0 else 0

        return {
            "project_name": self.project_name,
            "total": self.total_tasks,
            "completed": self.completed,
            "pending": self.pending,
            "failed": self.failed,
            "percentage": round(percentage, 1),
            "last_updated": self.last_updated
        }

    def print_progress(self):
        """打印进度报告到控制台"""
        report = self.get_progress_report()

        # 使用 ASCII 字符避免 Windows 编码问题
        print(f"""
任务进度报告: {report['project_name']}
=======================================
已完成: {report['completed']}
待执行: {report['pending']}
失败: {report['failed']}
=======================================
总进度: {report['percentage']}%
完成度: {report['completed']}/{report['total']}
=======================================
""")


class TaskListManager:
    """任务列表管理器

    负责任务列表的创建、加载、更新和查询。

    v3.3 新增:
        - TaskPlanManager 集成: JSON → MD 单向同步
        - 自动同步到 task_plan.md
    """

    def __init__(
        self,
        project_root: Path,
        enable_markdown_sync: bool = True
    ):
        """初始化任务列表管理器

        Args:
            project_root: 项目根目录
            enable_markdown_sync: 是否启用 Markdown 同步
        """
        self.project_root = Path(project_root)
        self.tasks_json_path = self.project_root / ".superagent" / "tasks.json"
        self.task_list: Optional[TaskList] = None
        self.enable_markdown_sync = enable_markdown_sync

        # v3.3: TaskPlanManager 集成
        self._task_plan_manager = None
        if self.enable_markdown_sync:
            self._init_task_plan_manager()

    def _init_task_plan_manager(self):
        """初始化 TaskPlanManager"""
        try:
            from extensions.planning_files import TaskPlanManager
            self._task_plan_manager = TaskPlanManager(
                self.project_root,
                self.project_root / "task_plan.md",
                auto_save=True
            )
            logger.info("TaskPlanManager 已初始化")
        except ImportError as e:
            logger.warning(f"无法导入 TaskPlanManager: {e}")
            self._task_plan_manager = None

    def _schedule_async_task(
        self,
        coro,
        timeout: Optional[float] = None
    ) -> Optional[asyncio.Task]:
        """安全地调度异步任务 (v3.3 优化)

        在同步方法中安全地调度异步任务。
        如果有运行中的事件循环则使用它，否则创建新循环。

        Args:
            coro: 协程对象
            timeout: 可选超时时间（秒）

        Returns:
            asyncio.Task 如果有运行中的事件循环，否则 None
        """
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(coro)
            # v3.3 优化：添加超时处理
            if timeout:
                # 在后台任务中设置超时
                async def with_timeout():
                    try:
                        await asyncio.wait_for(coro, timeout=timeout)
                    except asyncio.TimeoutError:
                        logger.warning(f"异步任务超时: {timeout}秒")
                loop.create_task(with_timeout())
            return task
        except RuntimeError:
            # 没有运行中的事件循环时，同步执行
            if timeout:
                try:
                    asyncio.run(asyncio.wait_for(coro, timeout=timeout))
                except asyncio.TimeoutError:
                    logger.warning(f"异步任务超时: {timeout}秒")
            else:
                asyncio.run(coro)
            return None

    async def sync_to_markdown(self) -> bool:
        """同步任务状态到 task_plan.md (JSON → MD 单向)

        Returns:
            是否同步成功
        """
        if not self._task_plan_manager or not self.task_list:
            return False

        try:
            # 准备步骤数据
            steps = []
            for task in self.task_list.tasks:
                steps.append({
                    "step_id": task.id,
                    "name": task.id,
                    "description": task.description,
                    "agent_type": task.assigned_agent,
                    "status": task.status
                })

            # 准备依赖数据
            dependencies = {}
            for task in self.task_list.tasks:
                if task.dependencies:
                    dependencies[task.id] = task.dependencies

            # 生成 requirements 格式
            requirements = {
                "user_input": self.task_list.project_name,
                "analysis": {
                    "complexity": "medium",
                    "tech_stack": "Python"
                }
            }

            # 创建/更新 task_plan.md
            await self._task_plan_manager.create_plan(
                requirements=requirements,
                steps=steps,
                dependencies=dependencies
            )

            logger.info("任务状态已同步到 task_plan.md")
            return True

        except Exception as e:
            logger.error(f"同步到 Markdown 失败: {e}")
            return False

    async def update_task_status_in_md(self, task_id: str, status: str) -> bool:
        """在 task_plan.md 中更新任务状态

        Args:
            task_id: 任务 ID
            status: 新状态 (pending/running/completed/failed)

        Returns:
            是否更新成功
        """
        if not self._task_plan_manager:
            return False

        try:
            return await self._task_plan_manager.update_task_status(task_id, status)
        except Exception as e:
            logger.error(f"更新 MD 状态失败: {e}")
            return False

    def create_from_plan(
        self,
        plan: Any,
        project_name: Optional[str] = None
    ) -> TaskList:
        """从执行计划创建任务列表

        Args:
            plan: ExecutionPlan 对象
            project_name: 项目名称 (可选,默认从 plan 获取)

        Returns:
            TaskList 对象
        """
        # 导入 ExecutionPlan (避免循环导入)
        from planning.models import ExecutionPlan

        if project_name is None:
            # v3.2 使用 requirements.user_input 作为项目标识
            if hasattr(plan, 'requirements') and plan.requirements:
                project_name = getattr(plan.requirements, 'user_input', 'New Project')
            else:
                project_name = getattr(plan, 'project_id', 'New Project')

        tasks = []
        for step in plan.steps:
            agent_type = getattr(step, 'agent_type', 'general')
            # 确保 AgentType 被转换为字符串 (Enum 兼容性)
            if hasattr(agent_type, 'value'):
                agent_type = agent_type.value

            tasks.append(TaskItem(
                id=step.id,
                description=step.description,
                assigned_agent=str(agent_type),
                test_steps=getattr(step, 'test_steps', []),
                dependencies=getattr(step, 'dependencies', [])
            ))

        self.task_list = TaskList(
            project_name=project_name,
            total_tasks=len(tasks),
            tasks=tasks
        )

        self.save()

        # v3.3: 同步到 task_plan.md (安全处理无事件循环的情况)
        if self.enable_markdown_sync:
            self._schedule_async_task(self.sync_to_markdown())

        logger.info(f"✅ 已创建任务列表: {len(tasks)} 个任务")
        return self.task_list

    async def create_from_plan_async(
        self,
        plan: Any,
        project_name: Optional[str] = None
    ) -> TaskList:
        """从执行计划创建任务列表 (异步版本)

        Args:
            plan: ExecutionPlan 对象
            project_name: 项目名称 (可选,默认从 plan 获取)

        Returns:
            TaskList 对象
        """
        self.create_from_plan(plan, project_name)
        await self.sync_to_markdown()
        return self.task_list

    def load_or_create(self) -> Optional[TaskList]:
        """加载或创建任务列表

        Returns:
            TaskList 对象,如果文件不存在则返回 None
        """
        if self.tasks_json_path.exists():
            logger.info(f"📂 加载任务列表: {self.tasks_json_path}")
            self.task_list = TaskList.load(self.tasks_json_path)
            return self.task_list
        else:
            logger.info("📝 任务列表不存在,将在首次运行时创建")
            return None

    def save(self):
        """保存当前任务列表"""
        if self.task_list:
            self.task_list.save(self.tasks_json_path)

    def get_next_task(
        self,
        agent_type: Optional[str] = None
    ) -> Optional[TaskItem]:
        """获取下一个待执行任务

        Args:
            agent_type: 过滤特定 Agent 类型的任务

        Returns:
            下一个待执行的任务,如果没有则返回 None
        """
        if not self.task_list:
            self.load_or_create()

        if not self.task_list:
            return None

        return self.task_list.get_next_pending(agent_type)

    def update_task(
        self,
        task_id: str,
        status: str,
        error: Optional[str] = None
    ):
        """更新任务状态

        Args:
            task_id: 任务 ID
            status: 新状态
            error: 错误信息 (可选)
        """
        if not self.task_list:
            self.load_or_create()

        if self.task_list:
            self.task_list.mark_progress(task_id, status, error)
            self.save()

            # v3.3: 同步到 task_plan.md (安全处理无事件循环的情况)
            if self.enable_markdown_sync:
                self._schedule_async_task(self.update_task_status_in_md(task_id, status))

    def batch_update_tasks(
        self,
        updates: List[Dict[str, Any]],
        defer_markdown_sync: bool = False
    ) -> int:
        """批量更新多个任务状态 (v3.3 优化)

        Args:
            updates: 更新列表，每个元素包含 task_id, status, 可选 error
            defer_markdown_sync: 是否延迟 Markdown 同步（合并更新）

        Returns:
            成功更新的任务数
        """
        if not self.task_list:
            self.load_or_create()

        if not self.task_list:
            return 0

        updated_count = 0

        for update in updates:
            task_id = update.get("task_id")
            status = update.get("status")
            error = update.get("error")

            if task_id and status:
                self.task_list.mark_progress(task_id, status, error)
                updated_count += 1

        # 只保存一次
        if updated_count > 0:
            self.save()

        # v3.3: 批量同步到 Markdown
        if self.enable_markdown_sync and updated_count > 0 and not defer_markdown_sync:
            # v3.3 安全增强：收集并过滤有效的 task_id
            task_ids = [
                u.get("task_id") for u in updates
                if u.get("task_id") is not None
            ]
            if task_ids:
                self._schedule_async_task(self.batch_update_markdown(task_ids))

        return updated_count

    async def batch_update_markdown(self, task_ids: List[str]) -> bool:
        """批量更新 task_plan.md 中的多个任务状态 (v3.3 优化)

        Args:
            task_ids: 任务 ID 列表

        Returns:
            是否更新成功
        """
        if not self._task_plan_manager or not task_ids:
            return False

        try:
            for task_id in task_ids:
                # 从 task_list 获取状态
                task = next(
                    (t for t in self.task_list.tasks if t.id == task_id),
                    None
                )
                if task:
                    await self._task_plan_manager.update_task_status(
                        task_id, task.status
                    )
            return True
        except Exception as e:
            logger.error(f"批量更新 Markdown 状态失败: {e}")
            return False

    def print_progress(self):
        """打印当前进度"""
        if self.task_list:
            self.task_list.print_progress()
        else:
            print("📝 任务列表未初始化")

    def get_status(self) -> Dict[str, Any]:
        """获取当前状态

        Returns:
            包含状态信息的字典
        """
        if not self.task_list:
            return {
                "initialized": False,
                "message": "任务列表未初始化"
            }

        report = self.task_list.get_progress_report()

        return {
            "initialized": True,
            "project_name": report["project_name"],
            "total_tasks": report["total"],
            "completed": report["completed"],
            "pending": report["pending"],
            "failed": report["failed"],
            "percentage": report["percentage"],
            "last_updated": report["last_updated"]
        }
