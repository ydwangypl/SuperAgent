#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GitAutoCommitManager 单元测试
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime

from orchestration.git_manager import GitAutoCommitManager


class TestGitAutoCommitManager:
    """GitAutoCommitManager 测试套件"""

    @pytest.fixture
    def temp_project(self):
        """创建临时项目目录"""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)

        # 初始化 Git 仓库
        import subprocess
        subprocess.run(
            ["git", "init"],
            cwd=project_root,
            capture_output=True,
            check=True
        )
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

        yield project_root

        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def git_manager(self, temp_project):
        """创建 GitAutoCommitManager 实例"""
        return GitAutoCommitManager(
            project_root=temp_project,
            enabled=True,
            auto_push=False
        )

    def test_initialization(self, temp_project):
        """测试初始化"""
        manager = GitAutoCommitManager(
            project_root=temp_project,
            enabled=True,
            commit_message_template="custom: {task_id} {description}",
            auto_push=True
        )

        assert manager.enabled is True
        assert manager.auto_push is True
        assert manager.commit_message_template == "custom: {task_id} {description}"
        assert manager.project_root == temp_project

    def test_initialization_disabled(self, temp_project):
        """测试禁用状态初始化"""
        manager = GitAutoCommitManager(
            project_root=temp_project,
            enabled=False
        )

        assert manager.enabled is False

    def test_generate_commit_message(self, git_manager):
        """测试生成 commit message"""
        # 基本消息
        message = git_manager._generate_commit_message(
            task_id="task-001",
            description="实现用户登录功能",
            summary=None
        )

        assert "task-001" in message
        assert "实现用户登录功能" in message

        # 带摘要的消息
        message_with_summary = git_manager._generate_commit_message(
            task_id="task-002",
            description="添加数据库支持",
            summary="创建用户表和会话表"
        )

        assert "task-002" in message_with_summary
        assert "添加数据库支持" in message_with_summary
        assert "创建用户表和会话表" in message_with_summary

    def test_commit_message_truncation(self, git_manager):
        """测试 commit message 长度限制"""
        # 创建一个超长的描述
        long_description = "测试" * 100  # 300 字符

        message = git_manager._generate_commit_message(
            task_id="task-001",
            description=long_description,
            summary=None
        )

        # 检查标题行不超过 50 字符
        title_line = message.split('\n')[0]
        assert len(title_line) <= 50

    @pytest.mark.asyncio
    async def test_stage_files(self, git_manager, temp_project):
        """测试文件暂存"""
        # 创建测试文件
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')")

        # 暂存文件
        staged_count = await git_manager._stage_files(["test.py"])

        assert staged_count == 1

    @pytest.mark.asyncio
    async def test_stage_files_nonexistent(self, git_manager):
        """测试暂存不存在的文件"""
        staged_count = await git_manager._stage_files(["nonexistent.py"])

        assert staged_count == 0

    @pytest.mark.asyncio
    async def test_create_commit(self, git_manager, temp_project):
        """测试创建 commit"""
        # 创建并暂存文件
        test_file = temp_project / "test.py"
        test_file.write_text("print('hello')")
        await git_manager._stage_files(["test.py"])

        # 创建 commit
        success = await git_manager._create_commit("test commit")

        assert success is True

    @pytest.mark.asyncio
    async def test_commit_task(self, git_manager, temp_project):
        """测试提交任务"""
        # 创建测试文件
        test_file = temp_project / "feature.py"
        test_file.write_text("def feature(): pass")

        # 提交任务
        success = await git_manager.commit_task(
            task_id="task-001",
            description="实现新功能",
            changed_files=["feature.py"],
            summary="添加核心功能模块"
        )

        assert success is True

    @pytest.mark.asyncio
    async def test_commit_task_no_files(self, git_manager):
        """测试提交空任务"""
        success = await git_manager.commit_task(
            task_id="task-002",
            description="空任务",
            changed_files=[]
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_commit_tasks_json(self, git_manager, temp_project):
        """测试提交 tasks.json"""
        # 创建 tasks.json
        tasks_json = temp_project / "tasks.json"
        tasks_json.write_text('{"project": "test"}')

        # 提交
        success = await git_manager.commit_tasks_json()

        assert success is True

    @pytest.mark.asyncio
    async def test_commit_tasks_json_not_exists(self, git_manager):
        """测试提交不存在的 tasks.json"""
        # 文件不存在时不应该报错
        success = await git_manager.commit_tasks_json()

        # 应该返回 False (文件不存在)
        assert success in (False, None)  # None 表示没有执行

    def test_get_commit_history(self, git_manager, temp_project):
        """测试获取提交历史"""
        # 创建一些提交
        import subprocess
        for i in range(3):
            test_file = temp_project / f"test{i}.py"
            test_file.write_text(f"print('{i}')")
            subprocess.run(["git", "add", "."], cwd=temp_project, capture_output=True)
            subprocess.run(
                ["git", "commit", "-m", f"commit {i}"],
                cwd=temp_project,
                capture_output=True
            )

        # 获取历史
        history = git_manager.get_commit_history(limit=3)

        assert len(history) == 3
        assert all("hash" in item for item in history)
        assert all("message" in item for item in history)
        assert all("author" in item for item in history)

    def test_get_status(self, git_manager):
        """测试获取状态"""
        status = git_manager.get_status()

        assert "enabled" in status
        assert status["enabled"] is True
        assert "repository_exists" in status
        assert "branch" in status
        assert "latest_commit" in status

    def test_get_status_disabled(self, temp_project):
        """测试禁用状态"""
        manager = GitAutoCommitManager(
            project_root=temp_project,
            enabled=False
        )

        status = manager.get_status()

        assert status["enabled"] is False

    @pytest.mark.asyncio
    async def test_initialize_repository(self, temp_project):
        """测试初始化仓库"""
        # 删除 .git 目录
        git_dir = temp_project / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)

        manager = GitAutoCommitManager(project_root=temp_project, enabled=True)
        success = await manager.initialize_repository()

        assert success is True
        assert git_dir.exists()
        assert (temp_project / ".gitignore").exists()

    @pytest.mark.asyncio
    async def test_initialize_repository_already_exists(self, git_manager):
        """测试初始化已存在的仓库"""
        success = await git_manager.initialize_repository()

        assert success is True

    @pytest.mark.asyncio
    async def test_commit_with_gitpython_mock(self, temp_project):
        """测试使用 gitpython 的提交 (Mock)"""
        manager = GitAutoCommitManager(
            project_root=temp_project,
            enabled=True
        )

        # Mock gitpython
        mock_repo = MagicMock()
        manager.repo = mock_repo

        # 创建测试文件
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")

        # 提交
        success = await manager.commit_task(
            task_id="task-001",
            description="测试任务",
            changed_files=["test.py"]
        )

        # 验证调用
        assert success is True
        mock_repo.index.add.assert_called_once()
        mock_repo.index.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_push_to_remote_disabled(self, git_manager, temp_project):
        """测试禁用自动推送"""
        manager = GitAutoCommitManager(
            project_root=temp_project,
            enabled=True,
            auto_push=False
        )

        # 创建一个提交
        test_file = temp_project / "test.py"
        test_file.write_text("print('test')")
        await manager.commit_task(
            task_id="task-001",
            description="测试",
            changed_files=["test.py"]
        )

        # 不应该调用 push (因为没有配置远程,但也不应该抛出异常)
        # 这里只测试不会抛出异常
        assert True


class TestGitAutoCommitManagerIntegration:
    """集成测试"""

    @pytest.fixture
    def temp_project(self):
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

        yield project_root

        shutil.rmtree(project_root, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_full_workflow(self, temp_project):
        """测试完整工作流程"""
        manager = GitAutoCommitManager(
            project_root=temp_project,
            enabled=True
        )

        # 1. 创建并提交第一个任务
        file1 = temp_project / "module1.py"
        file1.write_text("# Module 1")

        success1 = await manager.commit_task(
            task_id="task-001",
            description="创建模块1",
            changed_files=["module1.py"]
        )

        assert success1 is True

        # 2. 创建并提交第二个任务
        file2 = temp_project / "module2.py"
        file2.write_text("# Module 2")

        success2 = await manager.commit_task(
            task_id="task-002",
            description="创建模块2",
            changed_files=["module2.py"],
            summary="添加核心功能模块"
        )

        assert success2 is True

        # 3. 验证提交历史
        history = manager.get_commit_history(limit=2)

        assert len(history) == 2
        assert "task-001" in history[1]["message"] or "task-001" in history[0]["message"]
        assert "task-002" in history[1]["message"] or "task-002" in history[0]["message"]

        # 4. 验证状态
        status = manager.get_status()

        assert status["repository_exists"] is True
        assert status["latest_commit"] is not None
