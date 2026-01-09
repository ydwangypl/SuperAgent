import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from orchestration.worktree_orchestrator import WorktreeOrchestrator
from orchestration.models import TaskExecution, TaskStatus, OrchestrationConfig
from orchestration.worktree_manager import GitWorktreeManager

@pytest.mark.asyncio
async def test_worktree_orchestrator_create_for_task(tmp_path):
    # 准备环境
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    mock_manager = MagicMock(spec=GitWorktreeManager)
    mock_manager.create_worktree.return_value = project_root / ".worktrees" / "task-1"
    
    orchestrator = WorktreeOrchestrator(project_root=project_root, worktree_manager=mock_manager)
    
    # 准备任务
    task = TaskExecution(task_id="task-1", step_id="step-1", status=TaskStatus.PENDING)
    
    # 1. 测试不需要隔离的 Agent 类型
    await orchestrator.create_for_task(task, "manager")
    assert task.worktree_path is None
    mock_manager.create_worktree.assert_not_called()
    
    # 2. 测试需要隔离的 Agent 类型 (如 backend-dev)
    await orchestrator.create_for_task(task, "backend-dev")
    assert task.worktree_path == project_root / ".worktrees" / "task-1"
    mock_manager.create_worktree.assert_called_once_with(
        task_id="task-1",
        branch_name="task/step-1"
    )

@pytest.mark.asyncio
async def test_worktree_orchestrator_sync_to_root(tmp_path):
    # 准备环境
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    # 在 worktree 中创建一个文件
    test_file_rel = "src/main.py"
    test_file_src = worktree_path / test_file_rel
    test_file_src.parent.mkdir(parents=True, exist_ok=True)
    test_file_src.write_text("print('hello from worktree')")
    
    orchestrator = WorktreeOrchestrator(project_root=project_root)
    
    # 准备任务
    task = TaskExecution(
        task_id="task-1", 
        step_id="step-1", 
        status=TaskStatus.COMPLETED,
        worktree_path=worktree_path,
        result={"files": [test_file_rel]}
    )
    
    # 同步
    await orchestrator.sync_to_root(task)
    
    # 验证文件是否同步到了 project_root
    dest_path = project_root / test_file_rel
    assert dest_path.exists()
    assert dest_path.read_text() == "print('hello from worktree')"

@pytest.mark.asyncio
async def test_worktree_orchestrator_sync_security_block(tmp_path):
    # 准备环境
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    worktree_path = tmp_path / "worktree"
    worktree_path.mkdir()
    
    orchestrator = WorktreeOrchestrator(project_root=project_root)
    
    # 准备任务 - 尝试路径穿越攻击
    task = TaskExecution(
        task_id="task-1", 
        step_id="step-1", 
        status=TaskStatus.COMPLETED,
        worktree_path=worktree_path,
        result={"files": ["../../outside.txt"]}
    )
    
    # 同步 - 应该由于安全原因跳过
    await orchestrator.sync_to_root(task)
    
    # 验证文件没有被创建在 project_root 之外
    outside_file = tmp_path / "outside.txt"
    assert not outside_file.exists()
    
    # 验证文件没有被创建在 project_root 内部的非法位置
    assert not (project_root / "../../outside.txt").exists()
