import pytest
import asyncio
from pathlib import Path
from orchestration.base import BaseOrchestrator
from orchestration.models import OrchestrationConfig
from orchestration.error_recovery import ErrorRecoverySystem, ErrorType, ErrorSeverity
from orchestration.orchestrator import Orchestrator
from orchestration.review_orchestrator import ReviewOrchestrator
from orchestration.worktree_orchestrator import WorktreeOrchestrator
from common.security import SecurityValidator, SecurityError

class MockOrchestrator(BaseOrchestrator):
    """用于测试的模拟编排器"""
    async def run(self, task_desc: str):
        return f"Executed: {task_desc}"

def test_base_orchestrator_initialization(tmp_path):
    """测试 BaseOrchestrator 的统一初始化逻辑"""
    config = OrchestrationConfig(max_retries=10)
    orchestrator = MockOrchestrator(project_root=tmp_path, config=config)
    
    assert orchestrator.project_root == tmp_path
    assert orchestrator.config.max_retries == 10
    assert isinstance(orchestrator.project_root, Path)

@pytest.mark.asyncio
async def test_orchestrator_subclasses_initialization(tmp_path):
    """测试 Orchestrator 子类是否正确继承了初始化逻辑"""
    # 重置 MemoryManager 单例
    from memory.memory_manager import MemoryManager
    MemoryManager._instance = None
    
    # 测试 Orchestrator
    orch = Orchestrator(project_root=tmp_path)
    assert orch.project_root == tmp_path
    assert orch.config is not None
    await asyncio.sleep(0.1) # 等待异步任务
    
    # 测试 ReviewOrchestrator
    review_orch = ReviewOrchestrator(project_root=tmp_path)
    assert review_orch.project_root == tmp_path
    assert review_orch.agent_dispatcher is None # 默认应为 None
    
    # 测试 WorktreeOrchestrator
    worktree_orch = WorktreeOrchestrator(project_root=tmp_path)
    assert worktree_orch.project_root == tmp_path
    assert worktree_orch.worktree_manager is None # 默认应为 None

@pytest.mark.asyncio
async def test_error_recovery_history_tracking():
    """测试 ErrorRecoverySystem 的错误历史追踪功能"""
    recovery = ErrorRecoverySystem()
    task_id = "test-task-1"
    
    # 模拟一个错误 (带上类型名以便分类)
    exc = ValueError("ValueError: Invalid input data")
    result = await recovery.handle_error(exc, task_id, "coding")
    
    # 验证历史记录是否已更新
    assert task_id in recovery.error_history
    assert len(recovery.error_history[task_id]) == 1
    record = recovery.error_history[task_id][0]
    assert record["error_type"] == "value_error"
    assert "Invalid input data" in record["error_message"]
    assert record["retry_count"] == 0
    
    # 模拟第二次错误（重试）
    result2 = await recovery.handle_error(exc, task_id, "coding", retry_count=1)
    assert len(recovery.error_history[task_id]) == 2
    assert recovery.error_history[task_id][1]["retry_count"] == 1

def test_security_validator_static_methods(tmp_path):
    """测试 SecurityValidator 整合后的静态方法"""
    # 测试路径验证
    safe_path = tmp_path / "src" / "main.py"
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    safe_path.touch()
    
    # validate_path 返回 Path 对象
    SecurityValidator.validate_path(safe_path, tmp_path) 
    
    # 测试输入清理
    dirty_input = "Hello <script>alert(1)</script> World"
    clean_input = SecurityValidator.sanitize_input(dirty_input)
    assert "<script>" not in clean_input
    
    # 测试 Git 引用验证
    SecurityValidator.validate_git_ref("main")
    SecurityValidator.validate_git_ref("feature/new-fix")
    
    with pytest.raises(SecurityError):
        SecurityValidator.validate_git_ref("bad;ref")
    
    with pytest.raises(SecurityError):
        SecurityValidator.validate_git_ref("a" * 256) # 超过 255 字符

@pytest.mark.asyncio
async def test_error_recovery_stats():
    """测试 ErrorRecoverySystem 的统计功能"""
    recovery = ErrorRecoverySystem()
    
    # 触发一个不重试的严重错误 (SyntaxError)
    exc = SyntaxError("SyntaxError: invalid syntax")
    await recovery.handle_error(exc, "task-2", "coding")
    
    assert recovery.recovery_stats["total_errors"] == 1
    # SyntaxError 默认策略是 manual
    assert recovery.recovery_stats["manual"] == 1
    
    # 触发一个可重试的错误 (NetworkError)
    exc2 = ConnectionError("ConnectionError: timeout")
    await recovery.handle_error(exc2, "task-3", "coding")
    assert recovery.recovery_stats["total_errors"] == 2
    assert recovery.recovery_stats["retried"] == 1
