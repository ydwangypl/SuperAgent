#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
单任务焦点模式单元测试
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from orchestration.models import (
    TaskExecution,
    TaskStatus,
    OrchestrationConfig,
    SingleTaskConfig,
    ExecutionPriority
)
from orchestration.orchestrator import Orchestrator


class TestSingleTaskConfig:
    """单任务配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = SingleTaskConfig()

        assert config.enabled is True
        assert config.max_parallel_tasks == 1
        assert config.max_files_per_task == 5
        assert config.max_file_size_kb == 100
        assert config.force_incremental is True
        assert config.enable_auto_split is True

    def test_custom_config(self):
        """测试自定义配置"""
        config = SingleTaskConfig(
            enabled=False,
            max_parallel_tasks=2,
            max_files_per_task=10,
            max_file_size_kb=200,
            force_incremental=False,
            enable_auto_split=False
        )

        assert config.enabled is False
        assert config.max_parallel_tasks == 2
        assert config.max_files_per_task == 10
        assert config.max_file_size_kb == 200
        assert config.force_incremental is False
        assert config.enable_auto_split is False


class TestTaskScopeValidation:
    """任务范围验证测试"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)

        # 创建一些测试文件
        (project_root / "file1.py").write_text("x" * 50)  # 50 bytes
        (project_root / "file2.py").write_text("x" * 150)  # 150 bytes
        (project_root / "large_file.py").write_text("x" * 200 * 1024)  # 200 KB

        yield project_root

        shutil.rmtree(project_root, ignore_errors=True)

    @pytest.fixture
    def orchestrator(self, temp_project):
        """创建 Orchestrator 实例"""
        from orchestration.orchestrator import Orchestrator

        config = OrchestrationConfig(
            single_task_mode=SingleTaskConfig(
                enabled=True,
                max_files_per_task=5,
                max_file_size_kb=100
            )
        )

        # 使用 mock 来避免 MemoryManager 的事件循环问题
        import unittest.mock as mock

        def mock_init(self, pr, cfg=None, gc=None):
            self.project_root = pr
            self.config = cfg or OrchestrationConfig()
            self.context = None
            self.task_executor = None
            self.agent_dispatcher = None
            self.memory_manager = None
            self.error_recovery = None
            self.review_orchestrator = None
            self.worktree_orchestrator = None
            self.scheduler = None
            self.git_manager = None
            self.state = None
            self.result_handler = None

        with mock.patch.object(Orchestrator, '__init__', mock_init):
            orchestrator = Orchestrator(temp_project, config)

        return orchestrator

    def test_validate_task_scope_disabled(self, temp_project):
        """测试禁用单任务模式时的验证"""
        config = OrchestrationConfig(
            single_task_mode=SingleTaskConfig(enabled=False)
        )

        # 直接创建配置对象,不初始化完整的 Orchestrator
        # 以避免 MemoryManager 的事件循环问题
        from orchestration.orchestrator import Orchestrator

        # 使用 patch 来避免真实的初始化
        import unittest.mock as mock

        with mock.patch.object(Orchestrator, '__init__', lambda self, pr, cfg=None, gc=None: None):
            orchestrator = Orchestrator(temp_project, config)
            orchestrator.config = config
            orchestrator.project_root = temp_project

            task = TaskExecution(
                task_id="task-001",
                step_id="step-001",
                status=TaskStatus.COMPLETED,
                outputs={
                    "modified_files": ["file1.py", "file2.py", "file3.py",
                                     "file4.py", "file5.py", "file6.py"]
                }
            )

            is_valid, reason = orchestrator._validate_task_scope(task)

            # 禁用模式下应该总是返回有效
            assert is_valid is True
            assert reason is None

    def test_validate_task_scope_within_limits(self, orchestrator):
        """测试在限制内的任务验证"""
        task = TaskExecution(
            task_id="task-001",
            step_id="step-001",
            status=TaskStatus.COMPLETED,
            outputs={
                "modified_files": ["file1.py", "file2.py"]  # 2个文件, < 5
            }
        )

        is_valid, reason = orchestrator._validate_task_scope(task)

        assert is_valid is True
        assert reason is None

    def test_validate_task_scope_too_many_files(self, orchestrator):
        """测试文件数量超限"""
        task = TaskExecution(
            task_id="task-002",
            step_id="step-002",
            status=TaskStatus.COMPLETED,
            outputs={
                "modified_files": [
                    "file1.py", "file2.py", "file3.py",
                    "file4.py", "file5.py", "file6.py"  # 6个文件, > 5
                ]
            }
        )

        is_valid, reason = orchestrator._validate_task_scope(task)

        assert is_valid is False
        assert reason is not None
        assert "6 个文件" in reason
        assert "超过单任务模式限制" in reason

    def test_validate_task_scope_single_file_string(self, orchestrator):
        """测试单个文件作为字符串的情况"""
        task = TaskExecution(
            task_id="task-003",
            step_id="step-003",
            status=TaskStatus.COMPLETED,
            outputs={
                "modified_files": "file1.py"  # 字符串而不是列表
            }
        )

        is_valid, reason = orchestrator._validate_task_scope(task)

        assert is_valid is True
        assert reason is None

    def test_validate_task_scope_file_too_large(self, orchestrator):
        """测试文件大小超限"""
        task = TaskExecution(
            task_id="task-004",
            step_id="step-004",
            status=TaskStatus.COMPLETED,
            outputs={
                "modified_files": ["large_file.py"]  # 200KB > 100KB
            }
        )

        is_valid, reason = orchestrator._validate_task_scope(task)

        assert is_valid is False
        assert reason is not None
        assert "large_file.py" in reason
        assert "超过单任务模式限制" in reason

    def test_validate_task_scope_no_files(self, orchestrator):
        """测试没有修改文件的情况"""
        task = TaskExecution(
            task_id="task-005",
            step_id="step-005",
            status=TaskStatus.COMPLETED,
            outputs={}
        )

        is_valid, reason = orchestrator._validate_task_scope(task)

        assert is_valid is True
        assert reason is None


class TestTaskSplitting:
    """任务拆分测试"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def orchestrator(self, temp_project):
        """创建 Orchestrator 实例"""
        config = OrchestrationConfig(
            single_task_mode=SingleTaskConfig(
                enabled=True,
                enable_auto_split=True,
                max_files_per_task=5
            )
        )

        return Orchestrator(
            project_root=temp_project,
            config=config
        )

    @pytest.mark.asyncio
    async def test_split_task_disabled(self, temp_project):
        """测试禁用自动拆分"""
        config = OrchestrationConfig(
            single_task_mode=SingleTaskConfig(
                enabled=True,
                enable_auto_split=False
            )
        )

        orchestrator = Orchestrator(
            project_root=temp_project,
            config=config
        )

        task = TaskExecution(
            task_id="task-001",
            step_id="step-001",
            status=TaskStatus.COMPLETED,
            outputs={
                "modified_files": [f"file{i}.py" for i in range(10)]
            }
        )

        result = await orchestrator._split_task(task, "测试")

        # 禁用拆分时应该返回 None
        assert result is None

    @pytest.mark.asyncio
    async def test_split_task_within_limits(self, orchestrator):
        """测试在限制内的任务不拆分"""
        task = TaskExecution(
            task_id="task-001",
            step_id="step-001",
            status=TaskStatus.COMPLETED,
            outputs={
                "modified_files": ["file1.py", "file2.py", "file3.py"]
            }
        )

        result = await orchestrator._split_task(task, "测试")

        # 文件数量在限制内,不应该拆分
        assert result is not None
        assert result.task_id == "task-001"

    @pytest.mark.asyncio
    async def test_split_task_exceeds_limits(self, orchestrator):
        """测试超出限制的任务拆分"""
        task = TaskExecution(
            task_id="task-001",
            step_id="step-001",
            status=TaskStatus.COMPLETED,
            outputs={
                "modified_files": [f"file{i}.py" for i in range(10)]
            }
        )

        result = await orchestrator._split_task(task, "文件数量过多")

        # 应该拆分任务
        assert result is not None
        assert "modified_files" in result.outputs

        # 检查第一批文件
        first_batch = result.outputs["modified_files"]
        assert len(first_batch) <= 5  # max_files_per_task

        # 检查拆分标记
        assert result.outputs.get("is_split_task") is True
        assert result.outputs.get("total_subtasks") == 2  # 10个文件 / 5 = 2个子任务
        assert result.outputs.get("subtask_index") == 0

    @pytest.mark.asyncio
    async def test_split_task_single_file_string(self, orchestrator):
        """测试单个文件作为字符串的拆分"""
        task = TaskExecution(
            task_id="task-001",
            step_id="step-001",
            status=TaskStatus.COMPLETED,
            outputs={
                "modified_files": "file1.py"
            }
        )

        result = await orchestrator._split_task(task, "测试")

        # 单个文件不应该拆分,直接返回原始任务
        assert result is not None
        # 由于只有1个文件且在限制内,任务未被拆分,outputs保持不变
        # 但我们需要验证方法能够正确处理字符串输入
        # 重新验证一下这个任务对象
        assert result.task_id == "task-001"


class TestSingleTaskModeIntegration:
    """单任务焦点模式集成测试"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)

        # 创建测试文件
        for i in range(3):
            (project_root / f"file{i}.py").write_text(f"# File {i}")

        yield project_root

        shutil.rmtree(project_root, ignore_errors=True)

    def test_orchestrator_initialization_with_single_task_mode(self, temp_project):
        """测试使用单任务模式初始化 Orchestrator"""
        config = OrchestrationConfig(
            single_task_mode=SingleTaskConfig(
                enabled=True,
                max_parallel_tasks=1
            )
        )

        orchestrator = Orchestrator(
            project_root=temp_project,
            config=config
        )

        # 验证配置已应用
        assert orchestrator.config.single_task_mode.enabled is True
        assert orchestrator.config.single_task_mode.max_parallel_tasks == 1

    def test_validate_and_split_workflow(self, temp_project):
        """测试验证和拆分的完整工作流程"""
        config = OrchestrationConfig(
            single_task_mode=SingleTaskConfig(
                enabled=True,
                enable_auto_split=True,
                max_files_per_task=2  # 设置较小的限制以测试拆分
            )
        )

        orchestrator = Orchestrator(
            project_root=temp_project,
            config=config
        )

        # 创建一个超出限制的任务
        task = TaskExecution(
            task_id="task-001",
            step_id="step-001",
            status=TaskStatus.COMPLETED,
            outputs={
                "modified_files": ["file0.py", "file1.py", "file2.py"]  # 3个文件 > 2
            }
        )

        # 1. 验证任务范围
        is_valid, reason = orchestrator._validate_task_scope(task)
        assert is_valid is False
        assert reason is not None

        # 2. 拆分任务
        import asyncio

        async def test_split():
            split_task = await orchestrator._split_task(task, reason)
            assert split_task is not None
            assert split_task.outputs.get("is_split_task") is True

        asyncio.run(test_split())
