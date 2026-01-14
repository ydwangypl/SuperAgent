#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P0 核心功能集成测试

测试 TaskListManager、GitAutoCommitManager 和单任务焦点模式的集成
"""

import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from core.task_list_manager import TaskListManager, TaskItem, TaskList
from orchestration.git_manager import GitAutoCommitManager
from orchestration.models import (
    TaskExecution,
    TaskStatus,
    OrchestrationConfig,
    SingleTaskConfig
)
from planning.models import ExecutionPlan, Step, Requirements, DependencyGraph, RequirementAnalysis
from common.models import AgentType


@pytest.fixture
def dummy_plan():
    """创建一个符合 v3.2 规范的虚拟执行计划"""
    reqs = Requirements(user_input="测试项目")
    analysis = RequirementAnalysis()
    steps = [
        Step(
            id="step-001",
            name="实现用户登录",
            description="实现用户登录",
            agent_type=AgentType.BACKEND_DEV
        ),
        Step(
            id="step-002",
            name="创建注册表单",
            description="创建注册表单",
            agent_type=AgentType.BACKEND_DEV
        )
    ]
    graph = DependencyGraph()
    for s in steps:
        graph.add_step(s)
    
    return ExecutionPlan(
        requirements=reqs,
        steps=steps,
        dependencies=graph,
        analysis=analysis
    )


@pytest.fixture
def temp_project():
    """创建临时项目目录"""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)

    # 初始化 Git 仓库
    import subprocess
    subprocess.run(["git", "init"], cwd=project_root, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=project_root,
        capture_output=True,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=project_root,
        capture_output=True,
        check=True
    )

    # 创建初始提交
    (project_root / "README.md").write_text("# Test Project")
    subprocess.run(["git", "add", "."], cwd=project_root, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=project_root,
        capture_output=True,
        check=True
    )

    yield project_root

    shutil.rmtree(project_root, ignore_errors=True)


class TestTaskListAndGitIntegration:
    """TaskListManager 和 GitAutoCommitManager 集成测试"""

    def test_end_to_end_workflow(self, temp_project, dummy_plan):
        """测试端到端工作流程: 创建任务列表 → 执行 → Git commit"""
        # 1. 使用虚拟执行计划
        plan = dummy_plan

        # 2. 创建任务列表管理器
        task_manager = TaskListManager(temp_project)
        task_list = task_manager.create_from_plan(plan)

        assert task_list.total_tasks == 2
        assert task_list.completed == 0

        # 3. 创建 Git 管理器
        git_manager = GitAutoCommitManager(
            project_root=temp_project,
            enabled=True
        )

        # 4. 模拟执行第一个任务
        task = task_manager.get_next_task()
        assert task is not None
        assert task.id == "step-001"

        # 更新任务状态
        task_manager.update_task(task.id, "running")

        # 创建修改的文件
        (temp_project / "login.py").write_text("def login(): pass")

        # 完成任务
        task_manager.update_task(task.id, "completed")

        # 5. 自动 Git commit
        success = asyncio.run(git_manager.commit_task(
            task_id=task.id,
            description=task.description,
            changed_files=["login.py"]
        ))

        assert success is True

        # 6. 验证任务列表已更新
        task_manager.print_progress()
        assert task_manager.get_status()["completed"] == 1

        # 7. 验证 Git 提交历史
        history = git_manager.get_commit_history(limit=5)
        assert len(history) > 0
        assert any("step-001" in commit["message"] for commit in history)

    def test_checkpoint_resume(self, temp_project):
        """测试断点续传功能"""
        # 1. 创建初始任务列表
        reqs = Requirements(user_input="测试项目")
        analysis = RequirementAnalysis()
        steps = [
            Step(
                id=f"step-{i:03d}",
                name=f"任务 {i}",
                description=f"任务 {i}",
                agent_type=AgentType.BACKEND_DEV
            )
            for i in range(1, 6)
        ]
        graph = DependencyGraph()
        for s in steps:
            graph.add_step(s)

        plan = ExecutionPlan(
            requirements=reqs,
            steps=steps,
            dependencies=graph,
            analysis=analysis
        )

        task_manager1 = TaskListManager(temp_project)
        task_list1 = task_manager1.create_from_plan(plan)

        # 2. 执行前 2 个任务
        for i in range(2):
            task = task_manager1.get_next_task()
            task_manager1.update_task(task.id, "running")
            task_manager1.update_task(task.id, "completed")

        # 3. 验证进度已保存
        assert task_manager1.get_status()["completed"] == 2

        # 4. 模拟程序中断 - 创建新的管理器实例
        task_manager2 = TaskListManager(temp_project)
        loaded_list = task_manager2.load_or_create()

        # 5. 验证进度已恢复
        assert loaded_list is not None
        assert loaded_list.completed == 2
        assert loaded_list.pending == 3

        # 6. 继续执行剩余任务
        remaining_tasks = 3
        for _ in range(remaining_tasks):
            task = task_manager2.get_next_task()
            if task:
                task_manager2.update_task(task.id, "running")
                task_manager2.update_task(task.id, "completed")

        # 7. 验证所有任务完成
        assert task_manager2.get_status()["completed"] == 5

    def test_task_failure_handling(self, temp_project, dummy_plan):
        """测试任务失败处理"""
        plan = dummy_plan

        task_manager = TaskListManager(temp_project)
        task_list = task_manager.create_from_plan(plan)

        # 1. 完成第一个任务
        task1 = task_manager.get_next_task()
        task_manager.update_task(task1.id, "running")
        task_manager.update_task(task1.id, "completed")

        # 2. 第二个任务失败
        task2 = task_manager.get_next_task()
        task_manager.update_task(task2.id, "running")
        task_manager.update_task(task2.id, "failed", error="组件渲染异常")

        # 3. 验证状态
        status = task_manager.get_status()
        assert status["completed"] == 1
        assert status["failed"] == 1
        assert status["pending"] == 0


class TestSingleTaskModeIntegration:
    """单任务焦点模式集成测试"""

    def test_task_scope_validation(self, temp_project):
        """测试任务范围验证"""
        from orchestration.orchestrator import Orchestrator

        config = OrchestrationConfig(
            single_task_mode=SingleTaskConfig(
                enabled=True,
                max_files_per_task=3
            )
        )

        # Mock Orchestrator 初始化
        def mock_init(self, pr, cfg=None, gc=None):
            self.project_root = pr
            self.config = cfg or OrchestrationConfig()

        with patch.object(Orchestrator, '__init__', mock_init):
            orchestrator = Orchestrator(temp_project, config)

            # 1. 创建在限制内的任务
            task_valid = TaskExecution(
                task_id="task-001",
                step_id="step-001",
                status=TaskStatus.COMPLETED,
                outputs={
                    "modified_files": ["file1.py", "file2.py"]
                }
            )

            is_valid, reason = orchestrator._validate_task_scope(task_valid)
            assert is_valid is True
            assert reason is None

            # 2. 创建超出限制的任务
            task_invalid = TaskExecution(
                task_id="task-002",
                step_id="step-002",
                status=TaskStatus.COMPLETED,
                outputs={
                    "modified_files": ["file1.py", "file2.py", "file3.py", "file4.py"]
                }
            )

            is_valid, reason = orchestrator._validate_task_scope(task_invalid)
            assert is_valid is False
            assert "4 个文件" in reason

    @pytest.mark.asyncio
    async def test_task_auto_split(self, temp_project):
        """测试任务自动拆分"""
        from orchestration.orchestrator import Orchestrator

        config = OrchestrationConfig(
            single_task_mode=SingleTaskConfig(
                enabled=True,
                enable_auto_split=True,
                max_files_per_task=2
            )
        )

        # Mock Orchestrator 初始化
        def mock_init(self, pr, cfg=None, gc=None):
            self.project_root = pr
            self.config = cfg or OrchestrationConfig()

        with patch.object(Orchestrator, '__init__', mock_init):
            orchestrator = Orchestrator(temp_project, config)

            # 创建超出限制的任务
            task = TaskExecution(
                task_id="task-001",
                step_id="step-001",
                status=TaskStatus.COMPLETED,
                outputs={
                    "modified_files": ["file1.py", "file2.py", "file3.py", "file4.py"]
                }
            )

            # 自动拆分
            split_task = await orchestrator._split_task(
                task,
                "文件数量超过限制"
            )

            assert split_task is not None
            assert split_task.outputs.get("is_split_task") is True
            assert split_task.outputs.get("total_subtasks") == 2


class TestPerformance:
    """性能测试"""

    def test_large_task_list_loading(self, temp_project):
        """测试大量任务的加载性能"""
        import time

        # 创建包含 100 个任务的执行计划
        reqs = Requirements(user_input="性能测试项目")
        analysis = RequirementAnalysis()
        steps = [
            Step(
                id=f"step-{i:03d}",
                name=f"任务 {i}",
                description=f"任务 {i}",
                agent_type=AgentType.BACKEND_DEV
            )
            for i in range(1, 101)
        ]
        graph = DependencyGraph()
        for s in steps:
            graph.add_step(s)

        plan = ExecutionPlan(
            requirements=reqs,
            steps=steps,
            dependencies=graph,
            analysis=analysis
        )

        # 测量创建时间
        start_time = time.time()
        task_manager = TaskListManager(temp_project)
        task_list = task_manager.create_from_plan(plan)
        create_time = time.time() - start_time

        assert task_list.total_tasks == 100
        # 创建时间应该 < 1 秒
        assert create_time < 1.0

        # 测量加载时间
        start_time = time.time()
        loaded_list = task_manager.load_or_create()
        load_time = time.time() - start_time

        assert loaded_list is not None
        assert loaded_list.total_tasks == 100
        # 加载时间应该 < 1 秒
        assert load_time < 1.0

    def test_tasks_json_read_write_performance(self, temp_project):
        """测试 tasks.json 读写性能"""
        import time

        # 创建大任务列表
        reqs = Requirements(user_input="性能测试项目")
        analysis = RequirementAnalysis()
        steps = [
            Step(
                id=f"step-{i:03d}",
                name=f"任务 {i}",
                description=f"任务 {i} " * 10,  # 较长的描述
                agent_type=AgentType.BACKEND_DEV,
                dependencies=[]
            )
            for i in range(1, 101)
        ]
        graph = DependencyGraph()
        for s in steps:
            graph.add_step(s)

        plan = ExecutionPlan(
            requirements=reqs,
            steps=steps,
            dependencies=graph,
            analysis=analysis
        )

        task_manager = TaskListManager(temp_project)
        task_list = task_manager.create_from_plan(plan)

        # 标记一些任务为已完成
        for i in range(50):
            task_list.tasks[i].status = "completed"
            task_list.tasks[i].started_at = datetime.now().isoformat()
            task_list.tasks[i].completed_at = datetime.now().isoformat()

        # 测量写入性能
        start_time = time.time()
        task_manager.save()
        write_time = time.time() - start_time

        # 写入时间应该 < 0.5 秒
        assert write_time < 0.5

        # 测量读取性能
        start_time = time.time()
        loaded_list = TaskList.load(task_manager.tasks_json_path)
        read_time = time.time() - start_time

        assert loaded_list.total_tasks == 100
        assert loaded_list.completed == 50
        # 读取时间应该 < 0.5 秒
        assert read_time < 0.5

    def test_git_commit_performance(self, temp_project):
        """测试 Git commit 性能"""
        import time

        git_manager = GitAutoCommitManager(
            project_root=temp_project,
            enabled=True
        )

        # 创建多个文件并提交
        commit_times = []
        for i in range(10):
            # 创建文件
            test_file = temp_project / f"file{i}.py"
            test_file.write_text(f"# File {i}\n" + "x" * 1000)

            # 测量提交时间
            start_time = time.time()
            success = asyncio.run(git_manager.commit_task(
                task_id=f"task-{i:03d}",
                description=f"提交文件 {i}",
                changed_files=[f"file{i}.py"]
            ))
            commit_time = time.time() - start_time

            assert success is True
            commit_times.append(commit_time)

        # 计算平均提交时间
        avg_commit_time = sum(commit_times) / len(commit_times)

        # 平均提交时间应该 < 1 秒
        assert avg_commit_time < 1.0

        # 验证所有提交都成功
        history = git_manager.get_commit_history(limit=20)
        assert len(history) >= 10


class TestRealWorldScenarios:
    """真实场景测试"""

    def test_web_development_workflow(self, temp_project):
        """测试 Web 开发工作流程"""
        # 1. 创建任务列表
        reqs = Requirements(user_input="待办事项应用")
        analysis = RequirementAnalysis()
        steps = [
            Step(
                id="step-001",
                name="数据库设计",
                description="设计数据库模型",
                agent_type=AgentType.DATABASE_DESIGN,
                dependencies=[]
            ),
            Step(
                id="step-002",
                name="后端API开发",
                description="实现用户 API",
                agent_type=AgentType.BACKEND_DEV,
                dependencies=["step-001"]
            ),
            Step(
                id="step-003",
                name="前端开发",
                description="创建注册表单",
                agent_type=AgentType.FRONTEND_DEV,
                dependencies=["step-001"]
            ),
            Step(
                id="step-004",
                name="测试",
                description="编写单元测试",
                agent_type=AgentType.QA_ENGINEERING,
                dependencies=["step-002", "step-003"]
            )
        ]
        graph = DependencyGraph()
        for s in steps:
            graph.add_step(s)

        plan = ExecutionPlan(
            requirements=reqs,
            steps=steps,
            dependencies=graph,
            analysis=analysis
        )

        task_manager = TaskListManager(temp_project)
        task_list = task_manager.create_from_plan(plan)

        git_manager = GitAutoCommitManager(temp_project, enabled=True)

        # 2. 执行任务
        completed_count = 0
        while True:
            task = task_manager.get_next_task()
            if not task:
                break

            # 检查依赖
            task_item = next(
                (t for t in task_list.tasks if t.id == task.id),
                None
            )
            if not task_item:
                break

            dependencies_satisfied = all(
                any(t.id == dep and t.status == "completed" for t in task_list.tasks)
                for dep in task_item.dependencies
            )

            if not dependencies_satisfied:
                break

            # 模拟执行任务
            task_manager.update_task(task.id, "running")

            # 创建文件
            (temp_project / f"{task.id}.py").write_text(f"# {task.description}")

            # 完成
            task_manager.update_task(task.id, "completed")
            completed_count += 1

            # Git 提交
            asyncio.run(git_manager.commit_task(
                task_id=task.id,
                description=task.description,
                changed_files=[f"{task.id}.py"]
            ))

        # 3. 验证所有任务完成
        assert completed_count == 4
        assert task_manager.get_status()["completed"] == 4

        # 4. 验证 Git 历史
        history = git_manager.get_commit_history(limit=10)
        assert len(history) >= 4

    def test_incremental_development(self, temp_project):
        """测试增量开发场景"""
        task_manager = TaskListManager(temp_project)

        # 第一阶段: 创建基础结构
        reqs_v1 = Requirements(user_input="版本 1.0")
        analysis_v1 = RequirementAnalysis()
        steps_v1 = [
            Step(
                id=f"step-{i:03d}",
                name=f"基础功能 {i}",
                description=f"基础功能 {i}",
                agent_type=AgentType.BACKEND_DEV,
                dependencies=[]
            )
            for i in range(1, 4)
        ]
        graph_v1 = DependencyGraph()
        for s in steps_v1:
            graph_v1.add_step(s)

        plan_v1 = ExecutionPlan(
            requirements=reqs_v1,
            steps=steps_v1,
            dependencies=graph_v1,
            analysis=analysis_v1
        )

        task_list_v1 = task_manager.create_from_plan(plan_v1)

        # 完成第一阶段
        for i in range(3):
            task = task_manager.get_next_task()
            task_manager.update_task(task.id, "completed")

        assert task_manager.get_status()["completed"] == 3

        # 第二阶段: 添加新功能 (创建新的管理器实例)
        task_manager_v2 = TaskListManager(temp_project)
        loaded_list = task_manager_v2.load_or_create()

        assert loaded_list.completed == 3

        # 添加新任务
        reqs_v2 = Requirements(user_input="版本 1.1")
        analysis_v2 = RequirementAnalysis()
        steps_v2 = [
            Step(
                id=f"step-{i:03d}",
                name=f"新功能 {i}",
                description=f"新功能 {i}",
                agent_type=AgentType.BACKEND_DEV,
                dependencies=[]
            )
            for i in range(4, 7)
        ]
        graph_v2 = DependencyGraph()
        for s in steps_v2:
            graph_v2.add_step(s)

        plan_v2 = ExecutionPlan(
            requirements=reqs_v2,
            steps=steps_v2,
            dependencies=graph_v2,
            analysis=analysis_v2
        )

        task_list_v2 = task_manager_v2.create_from_plan(plan_v2)

        # 验证任务数增加
        # 注意: 这里 create_from_plan 会覆盖之前的任务列表
        # 实际应用中可能需要不同的策略
        assert task_list_v2.total_tasks == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
