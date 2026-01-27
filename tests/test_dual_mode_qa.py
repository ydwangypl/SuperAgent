#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
方案A+方案B 双模式质量保障测试

验证代码审查与测试功能的实现:
- 方案A: 主工作流集成 (Orchestrator)
- 方案B: 独立API (UnifiedAdapter)
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


class TestUnifiedAdapterTestMethods:
    """验证 UnifiedAdapter 的测试方法"""

    def test_unified_adapter_has_run_tests(self):
        """验证 UnifiedAdapter 有 run_tests 方法"""
        try:
            from adapters.unified_adapter import UnifiedAdapter
            adapter = UnifiedAdapter(Path("."))
            assert hasattr(adapter, 'run_tests'), "缺少 run_tests 方法"
            assert hasattr(adapter, 'run_tests_sync'), "缺少 run_tests_sync 方法"
        except ImportError as e:
            pytest.fail(f"无法导入 UnifiedAdapter: {e}")

    def test_unified_adapter_has_full_workflow(self):
        """验证 UnifiedAdapter 有 execute_and_review_and_test 方法"""
        from adapters.unified_adapter import UnifiedAdapter
        adapter = UnifiedAdapter(Path("."))
        assert hasattr(adapter, 'execute_and_review_and_test'), "缺少 execute_and_review_and_test 方法"
        assert hasattr(adapter, 'execute_and_review_and_test_sync'), "缺少 execute_and_review_and_test_sync 方法"

    def test_unified_adapter_has_tester(self):
        """验证 UnifiedAdapter 初始化了 tester 属性"""
        from adapters.unified_adapter import UnifiedAdapter
        adapter = UnifiedAdapter(Path("."))
        assert hasattr(adapter, 'tester'), "缺少 tester 属性"


class TestAdaptersExports:
    """验证适配器导出"""

    def test_adapters_module_exports_unified_adapter(self):
        """验证 adapters 模块导出 UnifiedAdapter"""
        from adapters import UnifiedAdapter
        assert UnifiedAdapter is not None

    def test_adapters_module_exports_test_adapter(self):
        """验证 adapters 模块导出 TestAdapter"""
        from adapters import TestAdapter
        assert TestAdapter is not None

    def test_adapters_module_exports_all(self):
        """验证 __all__ 包含所有适配器"""
        import adapters
        expected = ["UnifiedAdapter", "ReviewerAdapter", "ExecutorAdapter", "TestAdapter"]
        for name in expected:
            assert name in adapters.__all__, f"__all__ 缺少 {name}"
        assert len(adapters.__all__) == 4


class TestTestRunner:
    """测试运行器测试"""

    def test_test_runner_import(self):
        """验证 TestRunner 可以导入"""
        from core.test_runner import TestRunner
        assert TestRunner is not None

    def test_test_result_dataclass(self):
        """验证 TestResult 数据类"""
        from core.test_runner import TestResult

        result = TestResult(
            success=True,
            total_tests=10,
            passed=10,
            failed=0
        )
        assert result.success is True
        assert result.total_tests == 10
        assert result.passed == 10
        assert result.failed == 0

    def test_test_result_to_dict(self):
        """验证 TestResult.to_dict()"""
        from core.test_runner import TestResult

        result = TestResult(
            success=True,
            total_tests=5,
            passed=5
        )
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["total_tests"] == 5


class TestTestAdapter:
    """测试适配器测试"""

    def test_test_adapter_import(self):
        """验证 TestAdapter 可以导入"""
        from adapters.test_adapter import TestAdapter
        assert TestAdapter is not None

    def test_test_adapter_init(self):
        """验证 TestAdapter 初始化"""
        from adapters.test_adapter import TestAdapter

        adapter = TestAdapter(Path("."))
        assert adapter.project_root == Path(".")

    def test_test_adapter_has_run_tests(self):
        """验证 TestAdapter 有 run_tests 方法"""
        from adapters.test_adapter import TestAdapter

        adapter = TestAdapter(Path("."))
        assert hasattr(adapter, 'run_tests')
        assert hasattr(adapter, 'run_tests_sync')

    def test_test_adapter_has_quick_tests(self):
        """验证 TestAdapter 有 run_quick_tests 方法"""
        from adapters.test_adapter import TestAdapter

        adapter = TestAdapter(Path("."))
        assert hasattr(adapter, 'run_quick_tests')


class TestTestingConfig:
    """测试配置测试"""

    def test_testing_config_import(self):
        """验证 TestingConfig 可以导入"""
        from orchestration.models import TestingConfig
        assert TestingConfig is not None

    def test_testing_config_defaults(self):
        """验证 TestingConfig 默认值"""
        from orchestration.models import TestingConfig

        config = TestingConfig()
        assert config.enabled is True
        assert config.test_path is None
        assert config.fail_on_failure is False
        assert config.coverage is False
        assert config.verbose is True
        assert config.timeout == 300


class TestOrchestrationConfigTesting:
    """OrchestrationConfig 测试配置测试"""

    def test_orchestration_config_has_testing(self):
        """验证 OrchestrationConfig 有 testing 属性"""
        from orchestration.models import OrchestrationConfig

        config = OrchestrationConfig()
        assert hasattr(config, 'testing')
        assert config.testing.enabled is True

    def test_project_execution_result_has_test_summary(self):
        """验证 ProjectExecutionResult 有 test_summary 属性"""
        from orchestration.models import ProjectExecutionResult

        result = ProjectExecutionResult(
            success=True,
            project_id="test",
            total_tasks=5,
            completed_tasks=5,
            failed_tasks=0
        )
        assert hasattr(result, 'test_summary')
        assert result.test_summary is None


class TestIntegrationScenarios:
    """集成场景测试"""

    def test_superagent_import_unified_adapter(self):
        """验证可以从 SuperAgent 导入 UnifiedAdapter"""
        try:
            from SuperAgent import UnifiedAdapter
            assert UnifiedAdapter is not None
        except ImportError:
            # 检查根包导入
            try:
                import adapters
                from adapters import UnifiedAdapter
                assert UnifiedAdapter is not None
            except ImportError:
                pytest.fail("无法从任何路径导入 UnifiedAdapter")

    def test_superagent_import_test_adapter(self):
        """验证可以从 SuperAgent 导入 TestAdapter"""
        try:
            from SuperAgent import TestAdapter
            assert TestAdapter is not None
        except ImportError:
            try:
                import adapters
                from adapters import TestAdapter
                assert TestAdapter is not None
            except ImportError:
                pytest.fail("无法从任何路径导入 TestAdapter")


class TestMockedExecution:
    """模拟执行测试"""

    @pytest.mark.asyncio
    async def test_unified_adapter_run_tests_returns_dict(self):
        """验证 run_tests 返回字典格式"""
        from adapters.unified_adapter import UnifiedAdapter

        adapter = UnifiedAdapter(Path("."))

        # 模拟 tester.run_tests 返回
        mock_result = {
            "status": "completed",
            "success": True,
            "total_tests": 10,
            "passed": 10,
            "failed": 0
        }

        adapter.tester.run_tests = AsyncMock(return_value=mock_result)

        result = await adapter.run_tests()

        assert isinstance(result, dict)
        assert "status" in result
        assert "success" in result
        assert "total_tests" in result

    def test_unified_adapter_run_tests_sync_returns_dict(self):
        """验证 run_tests_sync 返回字典格式"""
        from adapters.unified_adapter import UnifiedAdapter

        adapter = UnifiedAdapter(Path("."))

        mock_result = {
            "status": "completed",
            "success": True,
            "total_tests": 5,
            "passed": 5
        }

        adapter.tester.run_tests_sync = MagicMock(return_value=mock_result)

        result = adapter.run_tests_sync()

        assert isinstance(result, dict)
        assert result["success"] is True


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
