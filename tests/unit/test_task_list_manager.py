#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TaskListManager 单元测试
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from core.task_list_manager import TaskItem, TaskList, TaskListManager


class TestTaskItem:
    """TaskItem 测试"""

    def test_task_item_creation(self):
        """测试任务项创建"""
        task = TaskItem(
            id="task-001",
            description="实现用户注册功能"
        )

        assert task.id == "task-001"
        assert task.description == "实现用户注册功能"
        assert task.status == "pending"
        assert task.assigned_agent is None
        assert task.test_steps == []
        assert task.dependencies == []

    def test_task_item_with_dependencies(self):
        """测试带依赖的任务项"""
        task = TaskItem(
            id="task-002",
            description="实现用户登录",
            dependencies=["task-001"]
        )

        assert task.dependencies == ["task-001"]

    def test_task_item_serialization(self):
        """测试任务项序列化"""
        task = TaskItem(
            id="task-001",
            description="测试任务",
            assigned_agent="backend-dev"
        )

        # 转换为字典
        data = task.to_dict()
        assert data["id"] == "task-001"
        assert data["description"] == "测试任务"
        assert data["assigned_agent"] == "backend-dev"

        # 从字典恢复
        restored = TaskItem.from_dict(data)
        assert restored.id == task.id
        assert restored.description == task.description
        assert restored.assigned_agent == task.assigned_agent


class TestTaskList:
    """TaskList 测试"""

    @pytest.fixture
    def sample_tasks(self):
        """创建示例任务列表"""
        return [
            TaskItem(
                id="task-001",
                description="功能1",
                status="pending"
            ),
            TaskItem(
                id="task-002",
                description="功能2",
                status="completed"
            ),
            TaskItem(
                id="task-003",
                description="功能3",
                status="pending",
                dependencies=["task-002"]
            )
        ]

    @pytest.fixture
    def task_list(self, sample_tasks):
        """创建任务列表"""
        return TaskList(
            project_name="TestProject",
            total_tasks=3,
            tasks=sample_tasks
        )

    def test_task_list_creation(self, task_list):
        """测试任务列表创建"""
        assert task_list.project_name == "TestProject"
        assert task_list.total_tasks == 3
        assert len(task_list.tasks) == 3

    def test_update_statistics(self, task_list):
        """测试统计信息更新"""
        task_list.update_statistics()

        assert task_list.completed == 1  # task-002
        assert task_list.pending == 2   # task-001, task-003
        assert task_list.failed == 0

    def test_get_next_pending(self, task_list):
        """测试获取下一个待执行任务"""
        next_task = task_list.get_next_pending()

        assert next_task is not None
        assert next_task.id == "task-001"
        assert next_task.status == "pending"

    def test_get_next_pending_with_dependencies(self, task_list):
        """测试带依赖的任务获取"""
        # task-003 依赖 task-002 (已完成),所以可以执行
        next_task = task_list.get_next_pending()

        # 应该返回 task-001 或 task-003
        assert next_task.id in ["task-001", "task-003"]
        assert next_task.status == "pending"

    def test_mark_progress(self, task_list):
        """测试标记进度"""
        task_list.mark_progress("task-001", "running")

        task = next(t for t in task_list.tasks if t.id == "task-001")
        assert task.status == "running"
        assert task.started_at is not None

        task_list.mark_progress("task-001", "completed")
        assert task.status == "completed"
        assert task.completed_at is not None

    def test_mark_progress_with_error(self, task_list):
        """测试标记失败"""
        task_list.mark_progress("task-001", "failed", error="测试错误")

        task = next(t for t in task_list.tasks if t.id == "task-001")
        assert task.status == "failed"
        assert task.error == "测试错误"

    def test_get_progress_report(self, task_list):
        """测试获取进度报告"""
        report = task_list.get_progress_report()

        assert report["project_name"] == "TestProject"
        assert report["total"] == 3
        assert report["completed"] == 1
        assert report["pending"] == 2
        assert report["percentage"] == 33.3

    def test_dependencies_satisfied(self, task_list):
        """测试依赖满足检查"""
        task_003 = next(t for t in task_list.tasks if t.id == "task-003")

        # task-003 依赖 task-002 (已完成),所以依赖满足
        assert task_list._dependencies_satisfied(task_003) is True

    def test_dependencies_not_satisfied(self, sample_tasks):
        """测试依赖不满足"""
        # 添加一个未满足依赖的任务
        sample_tasks.append(
            TaskItem(
                id="task-004",
                description="功能4",
                dependencies=["task-005"]  # 不存在的任务
            )
        )

        task_list = TaskList(
            project_name="TestProject",
            total_tasks=4,
            tasks=sample_tasks
        )

        task_004 = next(t for t in task_list.tasks if t.id == "task-004")
        assert task_list._dependencies_satisfied(task_004) is False

    def test_save_and_load(self, task_list, tmp_path):
        """测试保存和加载"""
        # 保存
        save_path = tmp_path / "tasks.json"
        task_list.save(save_path)

        # 验证文件存在
        assert save_path.exists()

        # 加载
        loaded_list = TaskList.load(save_path)

        assert loaded_list.project_name == task_list.project_name
        assert loaded_list.total_tasks == task_list.total_tasks
        assert len(loaded_list.tasks) == len(task_list.tasks)

        # 验证任务数据
        for original, loaded in zip(task_list.tasks, loaded_list.tasks):
            assert original.id == loaded.id
            assert original.description == loaded.description
            assert original.status == loaded.status


class TestTaskListManager:
    """TaskListManager 测试"""

    @pytest.fixture
    def project_root(self, tmp_path):
        """创建临时项目根目录"""
        return tmp_path

    @pytest.fixture
    def manager(self, project_root):
        """创建管理器"""
        return TaskListManager(project_root)

    def test_manager_initialization(self, manager, project_root):
        """测试管理器初始化"""
        assert manager.project_root == project_root
        assert manager.tasks_json_path == project_root / "tasks.json"
        assert manager.task_list is None

    def test_create_from_plan(self, manager, tmp_path):
        """测试从计划创建任务列表"""
        # 模拟 ExecutionPlan
        class MockStep:
            def __init__(self, id, description):
                self.id = id
                self.description = description
                self.agent_type = "backend-dev"

        class MockPlan:
            project_id = "TestProject"
            steps = [
                MockStep("step-001", "功能1"),
                MockStep("step-002", "功能2")
            ]

        plan = MockPlan()

        # 创建任务列表
        task_list = manager.create_from_plan(plan)

        assert task_list is not None
        assert task_list.project_name == "TestProject"
        assert task_list.total_tasks == 2
        assert len(task_list.tasks) == 2

        # 验证文件已创建
        assert manager.tasks_json_path.exists()

    def test_load_or_create_when_exists(self, manager, tmp_path):
        """测试加载已存在的任务列表"""
        # 先创建一个任务列表
        task_list = TaskList(
            project_name="TestProject",
            total_tasks=1,
            tasks=[
                TaskItem(id="task-001", description="测试")
            ]
        )
        task_list.save(manager.tasks_json_path)

        # 加载
        loaded = manager.load_or_create()

        assert loaded is not None
        assert loaded.project_name == "TestProject"
        assert len(loaded.tasks) == 1

    def test_load_or_create_when_not_exists(self, manager):
        """测试任务列表不存在时返回 None"""
        loaded = manager.load_or_create()

        assert loaded is None

    def test_get_next_task(self, manager, tmp_path):
        """测试获取下一个任务"""
        # 创建任务列表
        task_list = TaskList(
            project_name="TestProject",
            total_tasks=2,
            tasks=[
                TaskItem(id="task-001", description="功能1", status="pending"),
                TaskItem(id="task-002", description="功能2", status="completed")
            ]
        )
        manager.task_list = task_list

        # 获取下一个任务
        next_task = manager.get_next_task()

        assert next_task is not None
        assert next_task.id == "task-001"
        assert next_task.status == "pending"

    def test_update_task(self, manager, tmp_path):
        """测试更新任务"""
        # 创建任务列表
        task_list = TaskList(
            project_name="TestProject",
            total_tasks=1,
            tasks=[
                TaskItem(id="task-001", description="功能1", status="pending")
            ]
        )
        manager.task_list = task_list

        # 更新任务
        manager.update_task("task-001", "completed")

        # 验证更新
        assert task_list.tasks[0].status == "completed"
        assert task_list.tasks[0].completed_at is not None

    def test_get_status(self, manager):
        """测试获取状态"""
        # 未初始化
        status = manager.get_status()
        assert status["initialized"] is False

        # 已初始化
        task_list = TaskList(
            project_name="TestProject",
            total_tasks=5,
            tasks=[
                TaskItem(id="task-001", description="功能1", status="completed"),
                TaskItem(id="task-002", description="功能2", status="pending")
            ]
        )
        manager.task_list = task_list

        status = manager.get_status()
        assert status["initialized"] is True
        assert status["project_name"] == "TestProject"
        assert status["total_tasks"] == 5
        assert status["completed"] == 1
        assert status["percentage"] == 20.0


@pytest.mark.integration
class TestTaskListIntegration:
    """集成测试"""

    def test_full_workflow(self, tmp_path):
        """测试完整工作流程"""
        manager = TaskListManager(tmp_path)

        # 1. 创建任务列表
        class MockStep:
            def __init__(self, id, description):
                self.id = id
                self.description = description
                self.agent_type = "general"

        class MockPlan:
            project_id = "IntegrationTest"
            steps = [
                MockStep("step-001", "功能1"),
                MockStep("step-002", "功能2"),
                MockStep("step-003", "功能3")
            ]

        plan = MockPlan()
        task_list = manager.create_from_plan(plan)

        assert task_list.total_tasks == 3

        # 2. 执行第一个任务
        next_task = manager.get_next_task()
        assert next_task.id == "step-001"

        manager.update_task(next_task.id, "running")
        manager.update_task(next_task.id, "completed")

        # 3. 验证进度
        manager.print_progress()
        status = manager.get_status()

        assert status["completed"] == 1
        assert status["percentage"] == 33.3

        # 4. 测试断点续传
        # 重新加载管理器
        manager2 = TaskListManager(tmp_path)
        loaded_list = manager2.load_or_create()

        assert loaded_list is not None
        assert loaded_list.total_tasks == 3
        assert loaded_list.completed == 1

        # 5. 继续执行
        next_task = manager2.get_next_task()
        assert next_task.status == "pending"
        assert next_task.id in ["step-002", "step-003"]

    def test_serialization_roundtrip(self, tmp_path):
        """测试序列化往返"""
        # 创建复杂任务列表
        task_list = TaskList(
            project_name="SerializationTest",
            total_tasks=2,
            tasks=[
                TaskItem(
                    id="task-001",
                    description="复杂任务1",
                    assigned_agent="backend-dev",
                    test_steps=["步骤1", "步骤2"],
                    dependencies=[],
                    metadata={"priority": "high"}
                ),
                TaskItem(
                    id="task-002",
                    description="复杂任务2",
                    status="running",
                    started_at=datetime.now().isoformat()
                )
            ]
        )

        # 保存
        save_path = tmp_path / "tasks.json"
        task_list.save(save_path)

        # 加载
        loaded_list = TaskList.load(save_path)

        # 验证
        assert loaded_list.project_name == task_list.project_name
        assert len(loaded_list.tasks) == len(task_list.tasks)

        # 验证每个任务
        for original, loaded in zip(task_list.tasks, loaded_list.tasks):
            assert original.id == loaded.id
            assert original.description == loaded.description
            assert original.status == loaded.status
            assert original.assigned_agent == loaded.assigned_agent
            assert original.test_steps == loaded.test_steps
            assert original.dependencies == loaded.dependencies
            assert original.metadata == loaded.metadata
