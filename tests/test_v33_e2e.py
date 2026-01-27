#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent v3.3 端到端测试

测试内容：
1. MemoryManager 单例和缓存功能
2. TaskListManager JSON → MD 同步
3. BaseAgent findings/progress 功能
4. Orchestrator 扩展模块集成
5. Hook 系统功能
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("SuperAgent v3.3 端到端测试")
print("=" * 60)


async def test_memory_manager():
    """测试 MemoryManager 的 v3.3 改进"""
    print("\n[TEST 1] MemoryManager 单例和缓存功能")
    print("-" * 40)

    from memory.memory_manager import MemoryManager

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # 测试单例模式
        print("  ✓ 测试单例模式...")
        mm1 = MemoryManager(project_root)
        mm2 = MemoryManager(project_root)
        assert mm1 is mm2, "单例模式失败"
        print("    单例模式: PASS")

        # 测试缓存操作
        print("  ✓ 测试缓存操作...")
        test_entry = {"content": "测试记忆", "type": "test"}
        mm1._save_to_cache("episodic", "test_id", test_entry)
        cached = mm1._get_from_cache("episodic", "test_id")
        assert cached is not None, "缓存写入失败"
        assert cached["content"] == "测试记忆", "缓存读取失败"
        print("    缓存操作: PASS")

        # 测试缓存淘汰策略
        print("  ✓ 测试缓存淘汰策略...")
        for i in range(1005):  # 超过 max_cache_size (1000)
            mm1._save_to_cache("semantic", f"test_{i}", {"id": i})
        assert len(mm1._cache["semantic"]) <= 1001, "缓存淘汰失败"
        print("    缓存淘汰: PASS")

        # 测试统计信息
        print("  ✓ 测试统计信息...")
        stats = mm1.get_statistics()
        assert "cache_hit_rate" in stats, "缺少 cache_hit_rate"
        assert "index_ready" in stats, "缺少 index_ready"
        print(f"    缓存命中率: {stats['cache_hit_rate']}%")
        print("    统计信息: PASS")

    print("\n[TEST 1] MemoryManager: ALL PASS ✓")


async def test_task_list_manager():
    """测试 TaskListManager 的 JSON → MD 同步"""
    print("\n[TEST 2] TaskListManager JSON → MD 同步")
    print("-" * 40)

    from core.task_list_manager import TaskListManager, TaskItem, TaskList

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # 创建 TaskListManager
        print("  ✓ 创建 TaskListManager...")
        manager = TaskListManager(project_root, enable_markdown_sync=True)
        assert manager._task_plan_manager is not None, "TaskPlanManager 未初始化"
        print("    TaskListManager: PASS")

        # 创建模拟计划
        class MockStep:
            def __init__(self, id, description, agent_type):
                self.id = id
                self.description = description
                self.agent_type = agent_type
                self.test_steps = []
                self.dependencies = []

        class MockPlan:
            def __init__(self):
                self.steps = [
                    MockStep("task-001", "第一步任务", "CodingAgent"),
                    MockStep("task-002", "第二步任务", "CodingAgent"),
                ]
                self.requirements = type('obj', (object,), {'user_input': '测试项目'})()

        # 创建任务列表
        print("  ✓ 测试 create_from_plan...")
        manager.create_from_plan(MockPlan())

        # 等待异步任务完成
        await asyncio.sleep(0.5)

        # 检查 task_plan.md 是否创建
        task_plan_file = project_root / "task_plan.md"
        assert task_plan_file.exists(), f"task_plan.md 未创建, 实际路径: {task_plan_file}"
        print("    task_plan.md 创建: PASS")

        # 读取内容验证格式
        content = task_plan_file.read_text(encoding='utf-8')
        assert "task-001" in content, "task-001 未找到"
        assert "task-002" in content, "task-002 未找到"
        assert "[ ]" in content, "checkbox 未创建"
        print("    task_plan.md 格式: PASS")

        # 测试异步版本
        print("  ✓ 测试 create_from_plan_async...")
        manager2 = TaskListManager(project_root, enable_markdown_sync=True)
        result = await manager2.create_from_plan_async(MockPlan())
        assert result is not None, "异步版本失败"
        print("    异步版本: PASS")

    print("\n[TEST 2] TaskListManager: ALL PASS ✓")


async def test_planning_files():
    """测试 Planning Files 模块"""
    print("\n[TEST 3] Planning Files 模块")
    print("-" * 40)

    from extensions.planning_files import (
        TaskPlanManager, FindingsManager, ProgressManager, CompletionChecker
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # 测试 TaskPlanManager
        print("  ✓ 测试 TaskPlanManager...")
        task_plan = project_root / "test_plan.md"
        tpm = TaskPlanManager(project_root, task_plan, auto_save=True)

        requirements = {
            "user_input": "测试项目",
            "analysis": {"complexity": "low", "tech_stack": "Python"}
        }
        steps = [
            {"step_id": "step-1", "name": "Step 1", "description": "第一步", "agent_type": "Agent"},
        ]
        dependencies = {}

        await tpm.create_plan(requirements, steps, dependencies)
        assert task_plan.exists(), "task_plan.md 未创建"
        print("    TaskPlanManager: PASS")

        # 测试更新 checkbox
        print("  ✓ 测试更新 checkbox...")
        result = await tpm.update_task_status("step-1", "completed")
        assert result, "更新 checkbox 失败"

        content = task_plan.read_text(encoding='utf-8')
        assert "[x]" in content, "checkbox 未更新为已完成"
        print("    Checkbox 更新: PASS")

        # 测试 FindingsManager
        print("  ✓ 测试 FindingsManager...")
        fm = FindingsManager(
            project_root=project_root,
            findings_file=project_root / "docs" / "findings.md"
        )
        finding_id = await fm.add_finding(
            content="这是一个测试发现",
            category="test",
            impact="低",
            source="unit_test"
        )
        assert finding_id is not None, "添加发现失败"
        print("    FindingsManager: PASS")

        # 测试 ProgressManager
        print("  ✓ 测试 ProgressManager...")
        pm = ProgressManager(
            project_root=project_root,
            progress_file=project_root / "docs" / "progress.md",
            session_id="test-session"
        )
        await pm.log_progress(action="测试动作", status="started", details="测试详情")
        await pm.log_progress(action="测试动作", status="completed", details="完成")
        print("    ProgressManager: PASS")

        # 测试 CompletionChecker
        print("  ✓ 测试 CompletionChecker...")
        cc = CompletionChecker(tpm)
        report = await cc.check_all()
        assert report is not None, "完成度检查失败"
        print("    CompletionChecker: PASS")

    print("\n[TEST 3] Planning Files: ALL PASS ✓")


async def test_hooks():
    """测试 Hook 系统"""
    print("\n[TEST 4] Hook 系统")
    print("-" * 40)

    from extensions.hooks import (
        HookManager, HookContext, HookResult, LifecycleHookType,
        ReReadPlanHook, UpdateStatusHook, LogProgressHook
    )

    # 测试 HookManager
    print("  ✓ 测试 HookManager...")
    manager = HookManager(memory_manager=None)

    # 创建模拟的 managers
    class MockTaskPlanManager:
        async def read_plan(self):
            return "# 测试计划\n- Task step-1: 第一步"

    class MockProgressManager:
        async def log_progress(self, **kwargs):
            pass

        async def log_session_summary(self, task_count: int, status: str, errors = None):
            pass

    mock_tpm = MockTaskPlanManager()
    mock_pm = MockProgressManager()

    # 注册钩子
    hook1 = ReReadPlanHook(task_plan_manager=mock_tpm)
    hook2 = UpdateStatusHook(task_plan_manager=mock_tpm, progress_manager=mock_pm)
    hook3 = LogProgressHook(progress_manager=mock_pm)

    manager.register(hook1)
    manager.register(hook2)
    manager.register(hook3)

    # 统计所有已注册的钩子数量
    total_hooks = sum(len(hooks) for hooks in manager._registrations.values())
    assert total_hooks == 3, f"钩子注册失败 (期望3个,实际{total_hooks}个)"
    print("    HookManager: PASS")

    # 测试执行 PreExecute
    print("  ✓ 测试 PreExecute 钩子执行...")
    result = await manager.execute_pre_execute({
        "project_id": "test-project",
        "total_tasks": 5
    })
    assert isinstance(result, HookContext), "PreExecute 返回类型错误"
    print("    PreExecute: PASS")

    # 测试执行 PostExecute
    print("  ✓ 测试 PostExecute 钩子执行...")
    result = await manager.execute_post_execute(
        session_state={"completed_tasks": 3},
        execution_history=[]
    )
    assert isinstance(result, HookContext), "PostExecute 返回类型错误"
    print("    PostExecute: PASS")

    # 测试执行 Stop
    print("  ✓ 测试 Stop 钩子执行...")
    result = await manager.execute_stop({
        "completed": 3,
        "failed": 1,
        "total": 5
    })
    assert isinstance(result, HookResult), "Stop 返回类型错误"
    assert result.should_continue is True, "Stop should_continue 错误"
    print("    Stop: PASS")

    print("\n[TEST 4] Hook 系统: ALL PASS ✓")


async def test_state_persistence():
    """测试状态持久化模块"""
    print("\n[TEST 5] 状态持久化模块")
    print("-" * 40)

    from extensions.state_persistence import (
        StateSerializer, JSONSerializer, SessionManager, SessionStatus
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # 测试 SessionManager
        print("  ✓ 测试 SessionManager...")
        sm = SessionManager(project_root)

        # 开始会话
        await sm.start_session(
            session_id="test-session-001",
            initial_state={"test": "data"}
        )
        assert sm._current_session_id is not None, "会话未开始"
        print("    会话开始: PASS")

        # 创建检查点
        print("  ✓ 测试检查点创建...")
        checkpoint = await sm.create_checkpoint(
            task_status={"task-1": "completed"},
            memory_summary={"total": 10},
            context_summary="测试检查点"
        )
        assert checkpoint is not None, "检查点创建失败"
        print("    检查点创建: PASS")

        # 获取会话状态
        print("  ✓ 测试会话状态查询...")
        status = sm.current_session_id is not None
        assert status is True, "会话状态错误"
        print("    会话状态: PASS")

        # 结束会话
        print("  ✓ 测试会话结束...")
        await sm.end_session(
            status=SessionStatus.COMPLETED,
            final_state={"result": "success"}
        )
        status = sm.current_session_id is None
        assert status is True, "会话未正确结束"
        print("    会话结束: PASS")

        # 测试恢复
        print("  ✓ 测试会话恢复...")
        report = await sm.recover_session("test-session-001")
        assert report is not None, "会话恢复失败"
        print("    会话恢复: PASS")

    print("\n[TEST 5] 状态持久化: ALL PASS ✓")


async def test_base_agent_extensions():
    """测试 BaseAgent 的 v3.3 扩展功能"""
    print("\n[TEST 6] BaseAgent v3.3 扩展功能")
    print("-" * 40)

    from execution.base_agent import BaseAgent

    # 检查动态导入
    print("  ✓ 测试 FindingsManager 动态导入...")
    from execution.base_agent import FINDINGS_AVAILABLE, PROGRESS_AVAILABLE
    print(f"    FindingsManager 可用: {FINDINGS_AVAILABLE}")
    print(f"    ProgressManager 可用: {PROGRESS_AVAILABLE}")

    # 创建测试 Agent
    class TestAgent(BaseAgent):
        @classmethod
        def get_capabilities(cls):
            return set()

        @property
        def name(self):
            return "TestAgent"

        async def execute_impl(self, context, task_input):
            return []

        async def plan(self, context, task_input):
            return []

    agent = TestAgent("test-agent")

    # 测试 setup_findings_manager
    print("  ✓ 测试 setup_findings_manager...")
    with tempfile.TemporaryDirectory() as tmpdir:
        agent.setup_findings_manager(Path(tmpdir))
        # 即使 FindingsManager 不可用，也不应报错
        print("    setup_findings_manager: PASS")

        # 测试 setup_progress_manager
        print("  ✓ 测试 setup_progress_manager...")
        agent.setup_progress_manager(Path(tmpdir), session_id="test-session")
        print("    setup_progress_manager: PASS")

    print("\n[TEST 6] BaseAgent 扩展: ALL PASS ✓")


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("开始执行 v3.3 端到端测试...")
    print("=" * 60)

    try:
        await test_memory_manager()
        await test_task_list_manager()
        await test_planning_files()
        await test_hooks()
        await test_state_persistence()
        await test_base_agent_extensions()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！SuperAgent v3.3 功能验证成功")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)


# ============================================================================
# 以下是 v3.3 双轨质量保障 (方案A + 方案B) 的端到端测试
# ============================================================================

def test_dual_mode_qa_e2e():
    """双轨质量保障端到端测试"""
    from pathlib import Path
    import sys

    print("\n" + "=" * 70)
    print("SuperAgent v3.3 双轨质量保障 - 端到端测试")
    print("=" * 70)

    # 1. 测试 pytest_utils 工具模块
    print("\n[TEST 1] pytest_utils 工具模块")
    print("-" * 50)

    from core.pytest_utils import build_pytest_command, parse_pytest_output

    cmd1 = build_pytest_command()
    assert cmd1 == ["pytest", "-v", "--tb=short", "--disable-warnings"], f"Default cmd failed: {cmd1}"
    print("  ✓ 默认命令构建正确")

    cmd2 = build_pytest_command(test_path="tests/unit", verbose=False)
    assert cmd2 == ["pytest", "tests/unit", "-q", "--tb=line", "--disable-warnings"]
    print("  ✓ 自定义路径命令构建正确")

    sample_output = """
============================= test session starts =============================
tests/test_example.py::test_passed PASSED
tests/test_example.py::test_failed FAILED
tests/test_example.py::test_error ERROR
2 passed, 1 failed, 1 error in 0.05s
"""
    result = parse_pytest_output(sample_output)
    assert result["passed"] == 2
    assert result["failed"] == 1
    assert result["errors"] == 1
    assert result["success"] == False
    print("  ✓ 输出解析正确 (失败场景)")

    success_output = "\n5 passed in 0.12s\n"
    success_result = parse_pytest_output(success_output)
    assert success_result["success"] == True
    print("  ✅ pytest_utils 模块测试通过")

    # 2. 测试 TestRunner (方案A)
    print("\n[TEST 2] TestRunner - 方案A (主工作流集成)")
    print("-" * 50)

    from core.test_runner import TestRunner, TestResult

    runner = TestRunner(project_root=Path("."), timeout=60)
    print(f"  ✓ TestRunner 初始化成功 (timeout={runner._timeout}s)")

    sync_result = runner.run_pytest_sync(test_path="tests/test_dual_mode_qa.py", verbose=True)
    assert isinstance(sync_result, TestResult)
    assert sync_result.total_tests >= 0
    print(f"  ✓ run_pytest_sync 返回 TestResult (passed={sync_result.passed}, failed={sync_result.failed})")

    result_dict = sync_result.to_dict()
    assert "success" in result_dict
    assert "total_tests" in result_dict
    print("  ✓ to_dict() 转换正确")

    runner.set_timeout(120)
    assert runner._timeout == 120
    print("  ✓ set_timeout() 正常工作")

    print("  ✅ TestRunner 测试通过")

    # 3. 测试 TestAdapter (方案B)
    print("\n[TEST 3] TestAdapter - 方案B (独立API)")
    print("-" * 50)

    from adapters.test_adapter import TestAdapter

    adapter = TestAdapter(project_root=Path("."), timeout=60)
    print(f"  ✓ TestAdapter 初始化成功 (timeout={adapter._timeout}s)")

    sync_result = adapter.run_tests_sync(test_path="tests/test_dual_mode_qa.py")
    assert isinstance(sync_result, dict)
    assert "status" in sync_result
    assert "success" in sync_result
    print(f"  ✓ run_tests_sync 返回正确结构 (status={sync_result['status']})")

    adapter.set_timeout(120)
    assert adapter._timeout == 120
    print("  ✓ set_timeout() 正常工作")

    print("  ✅ TestAdapter 测试通过")

    # 4. 测试 UnifiedAdapter 集成
    print("\n[TEST 4] UnifiedAdapter - 完整流程集成")
    print("-" * 50)

    from adapters.unified_adapter import UnifiedAdapter

    unified = UnifiedAdapter(project_root=Path("."))
    print("  ✓ UnifiedAdapter 初始化成功")

    assert hasattr(unified, 'tester')
    assert isinstance(unified.tester, TestAdapter)
    print("  ✓ tester 属性正确初始化")

    assert hasattr(unified, 'run_tests')
    assert hasattr(unified, 'run_tests_sync')
    print("  ✓ 测试方法正确暴露")

    assert hasattr(unified, 'execute_and_review_and_test')
    assert hasattr(unified, 'execute_and_review_and_test_sync')
    print("  ✓ 完整工作流方法正确暴露")

    result = unified.run_tests_sync(test_path="tests/test_dual_mode_qa.py")
    assert result["status"] == "completed"
    assert result["success"] == True
    assert result["passed"] >= 21
    print(f"  ✓ run_tests_sync 实际执行测试 (passed={result['passed']})")

    print("  ✅ UnifiedAdapter 测试通过")

    # 5. 测试配置集成
    print("\n[TEST 5] 配置集成测试")
    print("-" * 50)

    from orchestration.models import TestingConfig, OrchestrationConfig

    config = TestingConfig()
    assert config.enabled == True
    assert config.timeout == 300
    print(f"  ✓ TestingConfig 默认值正确 (enabled={config.enabled}, timeout={config.timeout})")

    custom_config = TestingConfig(enabled=False, test_path="tests/unit", timeout=600)
    assert custom_config.enabled == False
    assert custom_config.timeout == 600
    print("  ✓ TestingConfig 自定义值正确")

    orch_config = OrchestrationConfig()
    assert hasattr(orch_config, 'testing')
    assert isinstance(orch_config.testing, TestingConfig)
    print("  ✓ OrchestrationConfig.testing 集成正确")

    print("  ✅ 配置集成测试通过")

    # 6. 模块导出测试
    print("\n[TEST 6] 模块导出测试")
    print("-" * 50)

    from adapters import TestAdapter as TA1
    from adapters.test_adapter import TestAdapter as TA2
    from core.test_runner import TestRunner as TR1
    from core.test_runner import TestResult
    from core.pytest_utils import build_pytest_command as bpc

    assert TA1 is TA2
    print("  ✓ TestAdapter 导出正确")

    from SuperAgent import TestRunner as SA_TR
    from SuperAgent import TestAdapter as SA_TA
    print("  ✓ SuperAgent 简洁导入包含 TestRunner 和 TestAdapter")

    print("  ✅ 模块导出测试通过")

    # 7. 实际执行测试
    print("\n[TEST 7] 完整工作流实际执行测试")
    print("-" * 50)

    print("\n  [7.1] 方案B: 独立测试执行")
    test_result = unified.run_tests_sync(test_path="tests/test_dual_mode_qa.py")
    assert test_result["status"] == "completed"
    assert test_result["success"] == True
    print(f"      ✓ 独立测试执行成功: {test_result['passed']} passed")

    print("\n  [7.2] 方案B: 快速测试")
    quick_result = adapter.run_quick_tests()
    print(f"      ✓ 快速测试完成: status={quick_result['status']}")

    print("\n  [7.3] 方案A: TestRunner 实际执行")
    runner_result = runner.run_pytest_sync(test_path="tests/test_dual_mode_qa.py", verbose=False)
    assert runner_result.success == True
    assert runner_result.passed >= 21
    print(f"      ✓ TestRunner 执行成功: {runner_result.passed} passed")

    print("  ✅ 完整工作流测试通过")

    # 8. 异常处理测试
    print("\n[TEST 8] 异常处理测试")
    print("-" * 50)

    error_result = adapter.run_tests_sync(test_path="tests/nonexistent_file.py")
    assert error_result["status"] == "completed"
    assert "output" in error_result
    print("  ✓ 不存在的测试文件处理正确")

    print("  ✅ 异常处理测试通过")

    print("\n" + "=" * 70)
    print("🎉 所有端到端测试通过!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        test_dual_mode_qa_e2e()
        print("\n双轨质量保障端到端测试: SUCCESS")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
