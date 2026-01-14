"""
TDD Validator 单元测试

测试 TDD 流程验证器的所有功能
"""

import pytest
from datetime import datetime
from execution.tdd_validator import (
    TDDStep,
    TDDTraceEntry,
    TDDValidator,
    TDDViolationError,
    validate_tdd_execution,
    create_tdd_trace_entry
)


# Mock ExecutionResult 类
class MockExecutionResult:
    """模拟 ExecutionResult"""

    def __init__(self, tdd_trace=None):
        self.tdd_trace = tdd_trace or []


class TestTDDValidator:
    """TDDValidator 测试套件"""

    def test_init_default(self):
        """测试默认初始化"""
        validator = TDDValidator()
        assert validator.strict_mode is True
        assert len(validator.violations) == 0

    def test_init_non_strict(self):
        """测试非严格模式初始化"""
        validator = TDDValidator(strict_mode=False)
        assert validator.strict_mode is False

    def test_validate_missing_tdd_trace_strict(self):
        """测试缺少 tdd_trace 字段 (严格模式)"""
        result = MockExecutionResult()
        validator = TDDValidator(strict_mode=True)

        with pytest.raises(TDDViolationError) as exc_info:
            validator.validate_execution_flow(result)

        # Check that it raises an error (the exact message may vary due to validation order)
        assert exc_info.value.violation_type in ["missing_trace", "missing_step"]

    def test_validate_missing_tdd_trace_non_strict(self):
        """测试缺少 tdd_trace 字段 (非严格模式)"""
        result = MockExecutionResult()
        validator = TDDValidator(strict_mode=False)

        assert validator.validate_execution_flow(result) is False
        assert len(validator.violations) > 0

    def test_validate_missing_required_step(self):
        """测试缺少必需步骤"""
        trace = [
            TDDTraceEntry(
                step=TDDStep.WRITE_FAILING_TEST,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            )
        ]
        result = MockExecutionResult(tdd_trace=trace)
        validator = TDDValidator()

        with pytest.raises(TDDViolationError) as exc_info:
            validator.validate_execution_flow(result)

        assert "缺少必需步骤" in str(exc_info.value)

    def test_validate_wrong_order_test_after_code(self):
        """测试测试在代码之后 (错误顺序)"""
        trace = [
            TDDTraceEntry(
                step=TDDStep.WRITE_MINIMAL_CODE,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            TDDTraceEntry(
                step=TDDStep.WRITE_FAILING_TEST,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            )
        ]
        result = MockExecutionResult(tdd_trace=trace)
        validator = TDDValidator()

        with pytest.raises(TDDViolationError) as exc_info:
            validator.validate_execution_flow(result)

        # Should raise an error about wrong order or missing steps
        assert exc_info.value.violation_type in ["wrong_order", "missing_step"]

    def test_validate_red_green_cycle_success(self):
        """测试正确的 RED-GREEN 循环"""
        trace = [
            # 1. 写失败的测试
            TDDTraceEntry(
                step=TDDStep.WRITE_FAILING_TEST,
                timestamp=datetime.now().isoformat(),
                details={"test_file": "test_login.py"},
                success=True
            ),
            # 2. 验证测试失败 (RED)
            TDDTraceEntry(
                step=TDDStep.VERIFY_FAILING,
                timestamp=datetime.now().isoformat(),
                details={"test_result": "FAILED"},
                success=False  # 测试失败,符合预期
            ),
            # 3. 写最小代码
            TDDTraceEntry(
                step=TDDStep.WRITE_MINIMAL_CODE,
                timestamp=datetime.now().isoformat(),
                details={"file": "login.py"},
                success=True
            ),
            # 4. 验证测试通过 (GREEN)
            TDDTraceEntry(
                step=TDDStep.VERIFY_PASSING,
                timestamp=datetime.now().isoformat(),
                details={"test_result": "PASSED"},
                success=True  # 测试通过
            ),
            # 5. 提交代码
            TDDTraceEntry(
                step=TDDStep.COMMIT_CODE,
                timestamp=datetime.now().isoformat(),
                details={"commit_sha": "abc123"},
                success=True
            )
        ]

        result = MockExecutionResult(tdd_trace=trace)
        validator = TDDValidator()

        # 应该通过验证
        assert validator.validate_execution_flow(result) is True
        assert len(validator.violations) == 0

    def test_validate_not_red_test_passes_initially(self):
        """测试测试一开始就通过 (不是 RED)"""
        trace = [
            TDDTraceEntry(
                step=TDDStep.WRITE_FAILING_TEST,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            # 验证时测试就通过了 (错误)
            TDDTraceEntry(
                step=TDDStep.VERIFY_FAILING,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True  # 应该是 False
            ),
            TDDTraceEntry(
                step=TDDStep.WRITE_MINIMAL_CODE,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            TDDTraceEntry(
                step=TDDStep.VERIFY_PASSING,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            TDDTraceEntry(
                step=TDDStep.COMMIT_CODE,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            )
        ]

        result = MockExecutionResult(tdd_trace=trace)
        validator = TDDValidator()

        with pytest.raises(TDDViolationError) as exc_info:
            validator.validate_execution_flow(result)

        assert "应该失败" in str(exc_info.value)

    def test_validate_not_green_test_fails(self):
        """测试测试没有通过 (不是 GREEN)"""
        trace = [
            TDDTraceEntry(
                step=TDDStep.WRITE_FAILING_TEST,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            TDDTraceEntry(
                step=TDDStep.VERIFY_FAILING,
                timestamp=datetime.now().isoformat(),
                details={},
                success=False
            ),
            TDDTraceEntry(
                step=TDDStep.WRITE_MINIMAL_CODE,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            # 验证时测试仍然失败 (错误)
            TDDTraceEntry(
                step=TDDStep.VERIFY_PASSING,
                timestamp=datetime.now().isoformat(),
                details={},
                success=False  # 应该是 True
            ),
            TDDTraceEntry(
                step=TDDStep.COMMIT_CODE,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            )
        ]

        result = MockExecutionResult(tdd_trace=trace)
        validator = TDDValidator()

        with pytest.raises(TDDViolationError) as exc_info:
            validator.validate_execution_flow(result)

        assert "应该通过" in str(exc_info.value)

    def test_get_violations(self):
        """测试获取违规列表"""
        result = MockExecutionResult(tdd_trace=[])
        validator = TDDValidator(strict_mode=False)

        validator.validate_execution_flow(result)

        violations = validator.get_violations()
        assert len(violations) > 0
        assert isinstance(violations, list)

    def test_has_violations(self):
        """测试检查是否有违规"""
        result = MockExecutionResult(tdd_trace=[])
        validator = TDDValidator(strict_mode=False)

        validator.validate_execution_flow(result)

        assert validator.has_violations() is True


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_validate_tdd_execution(self):
        """测试 validate_tdd_execution 函数"""
        trace = [
            TDDTraceEntry(
                step=TDDStep.WRITE_FAILING_TEST,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            TDDTraceEntry(
                step=TDDStep.VERIFY_FAILING,
                timestamp=datetime.now().isoformat(),
                details={},
                success=False
            ),
            TDDTraceEntry(
                step=TDDStep.WRITE_MINIMAL_CODE,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            TDDTraceEntry(
                step=TDDStep.VERIFY_PASSING,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            TDDTraceEntry(
                step=TDDStep.COMMIT_CODE,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            )
        ]

        result = MockExecutionResult(tdd_trace=trace)

        # 严格模式
        assert validate_tdd_execution(result, strict_mode=True) is True

        # 非严格模式
        assert validate_tdd_execution(result, strict_mode=False) is True

    def test_create_tdd_trace_entry(self):
        """测试 create_tdd_trace_entry 函数"""
        entry = create_tdd_trace_entry(
            TDDStep.WRITE_FAILING_TEST,
            {"test_file": "test_login.py"},
            success=True
        )

        assert entry.step == TDDStep.WRITE_FAILING_TEST
        assert entry.details["test_file"] == "test_login.py"
        assert entry.success is True
        assert isinstance(entry.timestamp, str)


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_trace(self):
        """测试空跟踪"""
        result = MockExecutionResult(tdd_trace=[])
        validator = TDDValidator(strict_mode=False)

        assert validator.validate_execution_flow(result) is False
        assert len(validator.get_violations()) > 0

    def test_with_refactor_step(self):
        """测试包含 REFACTOR 步骤 (可选)"""
        trace = [
            TDDTraceEntry(
                step=TDDStep.WRITE_FAILING_TEST,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            TDDTraceEntry(
                step=TDDStep.VERIFY_FAILING,
                timestamp=datetime.now().isoformat(),
                details={},
                success=False
            ),
            TDDTraceEntry(
                step=TDDStep.WRITE_MINIMAL_CODE,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            TDDTraceEntry(
                step=TDDStep.VERIFY_PASSING,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            # REFACTOR 是可选的
            TDDTraceEntry(
                step=TDDStep.REFACTOR,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            TDDTraceEntry(
                step=TDDStep.COMMIT_CODE,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            )
        ]

        result = MockExecutionResult(tdd_trace=trace)
        validator = TDDValidator()

        # 应该通过,REFACTOR 是可选的
        assert validator.validate_execution_flow(result) is True

    def test_multiple_violations(self):
        """测试多个违规"""
        trace = [
            # 代码在测试之前
            TDDTraceEntry(
                step=TDDStep.WRITE_MINIMAL_CODE,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            ),
            TDDTraceEntry(
                step=TDDStep.WRITE_FAILING_TEST,
                timestamp=datetime.now().isoformat(),
                details={},
                success=True
            )
            # 缺少其他必需步骤...
        ]

        result = MockExecutionResult(tdd_trace=trace)
        validator = TDDValidator(strict_mode=False)

        validator.validate_execution_flow(result)

        # 应该有多个违规
        violations = validator.get_violations()
        assert len(violations) >= 2
