"""
TDD Validator - Test-Driven Development 流程强制验证器

强制 Agent 遵循 RED-GREEN-REFACTOR 循环:
1. 先写失败的测试 (RED)
2. 验证测试失败
3. 写最小实现代码 (GREEN)
4. 验证测试通过
5. 提交代码 (REFACTOR 可选)

作者: SuperAgent Team
版本: v3.2.0
日期: 2026-01-13
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class TDDStep(Enum):
    """TDD 流程步骤枚举"""
    WRITE_FAILING_TEST = "write_failing_test"
    VERIFY_FAILING = "verify_failing"
    WRITE_MINIMAL_CODE = "write_minimal_code"
    VERIFY_PASSING = "verify_passing"
    COMMIT_CODE = "commit_code"
    REFACTOR = "refactor"  # 可选


@dataclass
class TDDTraceEntry:
    """TDD 执行跟踪条目"""
    step: TDDStep
    timestamp: str
    details: Dict[str, Any]
    success: bool


class TDDViolationError(Exception):
    """TDD 流程违规异常"""

    def __init__(self, message: str, violation_type: str = "unknown"):
        self.violation_type = violation_type
        super().__init__(message)


class TDDValidator:
    """
    TDD 流程强制验证器

    确保所有代码开发遵循 Test-Driven Development 最佳实践
    """

    # 必需的 TDD 步骤
    REQUIRED_STEPS = [
        TDDStep.WRITE_FAILING_TEST,
        TDDStep.VERIFY_FAILING,
        TDDStep.WRITE_MINIMAL_CODE,
        TDDStep.VERIFY_PASSING,
        TDDStep.COMMIT_CODE
    ]

    # 可选的 TDD 步骤
    OPTIONAL_STEPS = [
        TDDStep.REFACTOR
    ]

    def __init__(self, strict_mode: bool = True):
        """
        初始化 TDD 验证器

        Args:
            strict_mode: 严格模式,如果为 True 则任何违规都会抛出异常
        """
        self.strict_mode = strict_mode
        self.violations: List[str] = []

    def validate_execution_flow(self, task_result: Any) -> bool:
        """
        验证任务执行结果是否遵循 TDD 流程

        Args:
            task_result: ExecutionResult 对象,必须包含 tdd_trace 字段

        Returns:
            bool: 如果遵循 TDD 返回 True

        Raises:
            TDDViolationError: 当违反 TDD 规则时
            ValueError: 当 task_result 格式不正确时
        """
        self.violations = []

        # 检查 task_result 是否有 tdd_trace
        if not hasattr(task_result, 'tdd_trace'):
            error_msg = "TDD 违规: 缺少 tdd_trace 字段"
            self._handle_violation(error_msg, "missing_trace")
            if self.strict_mode:
                raise TDDViolationError(error_msg, "missing_trace")
            return False

        trace = task_result.tdd_trace

        # 检查是否包含所有必需步骤
        for required_step in self.REQUIRED_STEPS:
            if not any(entry.step == required_step for entry in trace):
                error_msg = f"TDD 违规: 缺少必需步骤 {required_step.value}"
                self._handle_violation(error_msg, "missing_step")
                if self.strict_mode:
                    raise TDDViolationError(error_msg, "missing_step")

        # 验证步骤顺序
        self._validate_step_order(trace)

        # 验证 RED-GREEN 循环
        self._validate_red_green_cycle(trace)

        # 如果没有违规,返回 True
        return len(self.violations) == 0

    def _validate_step_order(self, trace: List[TDDTraceEntry]) -> None:
        """
        验证 TDD 步骤顺序是否正确

        规则:
        - 测试必须在代码之前
        - 验证失败必须在验证通过之前
        - 提交必须是最后一步
        """
        try:
            # 获取各个步骤的索引
            test_idx = next(
                i for i, entry in enumerate(trace)
                if entry.step == TDDStep.WRITE_FAILING_TEST
            )
            code_idx = next(
                i for i, entry in enumerate(trace)
                if entry.step == TDDStep.WRITE_MINIMAL_CODE
            )

            # 测试必须在代码之前
            if test_idx >= code_idx:
                error_msg = "TDD 违规: 必须先写测试,再写代码"
                self._handle_violation(error_msg, "wrong_order")
                if self.strict_mode:
                    raise TDDViolationError(error_msg, "wrong_order")

            # 验证失败必须在验证通过之前
            verify_fail_idx = next(
                (i for i, entry in enumerate(trace)
                 if entry.step == TDDStep.VERIFY_FAILING),
                None
            )
            verify_pass_idx = next(
                (i for i, entry in enumerate(trace)
                 if entry.step == TDDStep.VERIFY_PASSING),
                None
            )

            if verify_fail_idx is not None and verify_pass_idx is not None:
                if verify_fail_idx >= verify_pass_idx:
                    error_msg = "TDD 违规: 必须先验证测试失败,再验证测试通过"
                    self._handle_violation(error_msg, "wrong_order")
                    if self.strict_mode:
                        raise TDDViolationError(error_msg, "wrong_order")

        except StopIteration:
            # 某些步骤不存在,会在其他检查中捕获
            pass

    def _validate_red_green_cycle(self, trace: List[TDDTraceEntry]) -> None:
        """
        验证 RED-GREEN 循环是否完整

        规则:
        - 测试必须先失败 (RED)
        - 然后测试必须通过 (GREEN)
        """
        test_failed = False
        test_passed = False

        for entry in trace:
            if entry.step == TDDStep.VERIFY_FAILING:
                # 验证测试是否真的失败了
                if not entry.success:
                    test_failed = True
                else:
                    error_msg = "TDD 违规: 第一个测试应该失败 (RED)"
                    self._handle_violation(error_msg, "not_red")
                    if self.strict_mode:
                        raise TDDViolationError(error_msg, "not_red")

            if entry.step == TDDStep.VERIFY_PASSING:
                # 验证测试是否通过了
                if entry.success:
                    test_passed = True
                else:
                    error_msg = "TDD 违规: 测试应该通过 (GREEN)"
                    self._handle_violation(error_msg, "not_green")
                    if self.strict_mode:
                        raise TDDViolationError(error_msg, "not_green")

        # 确保完整经历了 RED-GREEN 循环
        if not test_failed:
            error_msg = "TDD 违规: 缺少 RED 阶段 (测试必须先失败)"
            self._handle_violation(error_msg, "missing_red")
            if self.strict_mode:
                raise TDDViolationError(error_msg, "missing_red")

        if not test_passed:
            error_msg = "TDD 违规: 缺少 GREEN 阶段 (测试必须通过)"
            self._handle_violation(error_msg, "missing_green")
            if self.strict_mode:
                raise TDDViolationError(error_msg, "missing_green")

    def _handle_violation(self, message: str, violation_type: str) -> None:
        """
        处理违规情况

        Args:
            message: 违规消息
            violation_type: 违规类型
        """
        self.violations.append(message)
        logger.warning(f"TDD Violation: {message}")

    def get_violations(self) -> List[str]:
        """
        获取所有违规消息

        Returns:
            List[str]: 违规消息列表
        """
        return self.violations.copy()

    def has_violations(self) -> bool:
        """
        检查是否有违规

        Returns:
            bool: 如果有违规返回 True
        """
        return len(self.violations) > 0


# 便捷函数

def validate_tdd_execution(task_result: Any, strict_mode: bool = True) -> bool:
    """
    验证任务执行是否遵循 TDD

    Args:
        task_result: ExecutionResult 对象
        strict_mode: 严格模式

    Returns:
        bool: 如果遵循 TDD 返回 True

    Example:
        >>> result = ExecutionResult(...)
        >>> if validate_tdd_execution(result):
        ...     print("TDD 流程正确")
    """
    validator = TDDValidator(strict_mode=strict_mode)
    return validator.validate_execution_flow(task_result)


def create_tdd_trace_entry(step: TDDStep, details: Dict[str, Any], success: bool = True) -> TDDTraceEntry:
    """
    创建 TDD 跟踪条目

    Args:
        step: TDD 步骤
        details: 详细信息
        success: 是否成功

    Returns:
        TDDTraceEntry: 跟踪条目

    Example:
        >>> from datetime import datetime
        >>> entry = create_tdd_trace_entry(
        ...     TDDStep.WRITE_FAILING_TEST,
        ...     {"test_file": "test_login.py", "test_name": "test_login_success"},
        ...     success=True
        ... )
    """
    from datetime import datetime

    return TDDTraceEntry(
        step=step,
        timestamp=datetime.now().isoformat(),
        details=details,
        success=success
    )
