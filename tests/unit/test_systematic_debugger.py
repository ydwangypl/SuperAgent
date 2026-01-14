"""
SystematicDebugger 单元测试 - P1 Task 2.2

测试系统化调试器的核心功能:
1. 错误观察
2. 假设生成
3. 假设验证
4. 根因确认
"""

import pytest
from execution.systematic_debugger import (
    SystematicDebugger,
    DebuggingPhase,
    ErrorObservation,
    Hypothesis,
    VerificationResult,
    RootCause,
    DebuggingReport
)


class TestSystematicDebuggerInitialization:
    """测试 SystematicDebugger 初始化"""

    def test_initialization(self):
        """测试基本初始化"""
        debugger = SystematicDebugger()

        assert debugger.current_phase == DebuggingPhase.ERROR_OBSERVATION
        assert debugger.debugging_history == []
        assert debugger.current_report is None

    def test_reset(self):
        """测试重置功能"""
        debugger = SystematicDebugger()

        # 修改状态
        debugger.current_phase = DebuggingPhase.ROOT_CAUSE_CONFIRMATION
        debugger.debugging_history.append({"test": "data"})

        # 重置
        debugger.reset()

        assert debugger.current_phase == DebuggingPhase.ERROR_OBSERVATION
        assert debugger.debugging_history == []
        assert debugger.current_report is None


class TestErrorObservationPhase:
    """测试错误观察阶段"""

    def test_start_debugging_basic(self):
        """测试开始调试"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "ValueError",
            "error_message": "invalid literal for int()",
            "stack_trace": [
                'File "test.py", line 10, in <module>',
                "  int(value)"
            ]
        }

        observation = debugger.start_debugging(error_info)

        assert isinstance(observation, ErrorObservation)
        assert observation.error_type == "ValueError"
        assert observation.error_message == "invalid literal for int()"
        assert len(observation.stack_trace) == 2
        assert debugger.current_phase == DebuggingPhase.ERROR_OBSERVATION

    def test_error_observation_with_code_context(self):
        """测试带代码上下文的错误观察"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "ImportError",
            "error_message": "No module named 'missing_module'",
            "stack_trace": [],
            "code_context": {
                "file_path": "test.py",
                "line_number": 5,
                "function": "main"
            }
        }

        observation = debugger.start_debugging(error_info)

        assert observation.code_context["file_path"] == "test.py"
        assert observation.code_context["line_number"] == 5
        assert "test.py" in observation.related_files

    def test_extract_related_files_from_stack_trace(self):
        """测试从堆栈跟踪提取相关文件"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "SyntaxError",
            "error_message": "invalid syntax",
            "stack_trace": [
                'File "module1.py", line 10, in func1',
                'File "module2.py", line 20, in func2'
            ]
        }

        observation = debugger.start_debugging(error_info)

        # 应该提取到两个文件
        assert "module1.py" in observation.related_files
        assert "module2.py" in observation.related_files

    def test_reproduction_steps_generation(self):
        """测试复现步骤生成"""
        debugger = SystematicDebugger()

        # 测试 ImportError
        error_info = {
            "error_type": "ImportError",
            "error_message": "No module named 'xyz'",
            "stack_trace": []
        }

        observation = debugger.start_debugging(error_info)

        assert len(observation.reproduction_steps) > 0
        assert any("导入" in step or "import" in step.lower()
                  for step in observation.reproduction_steps)

    def test_debugging_report_creation(self):
        """测试调试报告创建"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "TypeError",
            "error_message": "unsupported operand type(s)",
            "stack_trace": []
        }

        debugger.start_debugging(error_info)

        assert debugger.current_report is not None
        assert isinstance(debugger.current_report, DebuggingReport)
        assert debugger.current_report.observation.error_type == "TypeError"
        assert debugger.current_report.phase == DebuggingPhase.ERROR_OBSERVATION


class TestHypothesisGenerationPhase:
    """测试假设生成阶段"""

    def test_generate_hypotheses(self):
        """测试生成假设"""
        debugger = SystematicDebugger()

        # 先完成观察阶段
        error_info = {
            "error_type": "ImportError",
            "error_message": "No module named 'test'",
            "stack_trace": []
        }
        observation = debugger.start_debugging(error_info)

        # 生成假设
        hypotheses = debugger.generate_hypotheses(observation)

        assert len(hypotheses) >= 3  # 至少 3 个假设
        assert debugger.current_phase == DebuggingPhase.HYPOTHESIS_GENERATION
        assert all(isinstance(h, Hypothesis) for h in hypotheses)

    def test_hypothesis_structure(self):
        """测试假设结构"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "ValueError",
            "error_message": "test error",
            "stack_trace": []
        }
        observation = debugger.start_debugging(error_info)
        hypotheses = debugger.generate_hypotheses(observation)

        # 检查第一个假设
        hypothesis = hypotheses[0]

        assert hypothesis.hypothesis_id
        assert hypothesis.title
        assert hypothesis.description
        assert hypothesis.likelihood in ["low", "medium", "high"]
        assert len(hypothesis.suggested_tests) > 0

    def test_import_error_hypotheses(self):
        """测试 ImportError 专用假设"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "ImportError",
            "error_message": "No module named 'xyz'",
            "stack_trace": []
        }
        observation = debugger.start_debugging(error_info)
        hypotheses = debugger.generate_hypotheses(observation)

        # 应该有导入相关的假设
        titles = [h.title.lower() for h in hypotheses]
        assert any("import" in title or "导入" in title for title in titles)
        assert any("版本" in title or "version" in title for title in titles)

    def test_syntax_error_hypotheses(self):
        """测试 SyntaxError 专用假设"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "SyntaxError",
            "error_message": "invalid syntax",
            "stack_trace": []
        }
        observation = debugger.start_debugging(error_info)
        hypotheses = debugger.generate_hypotheses(observation)

        # 应该有语法相关的假设
        titles = [h.title.lower() for h in hypotheses]
        assert any("语法" in title or "syntax" in title for title in titles)

    def test_hypotheses_added_to_report(self):
        """测试假设添加到报告"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "TypeError",
            "error_message": "test",
            "stack_trace": []
        }
        debugger.start_debugging(error_info)

        observation = debugger.current_report.observation
        hypotheses = debugger.generate_hypotheses(observation)

        assert debugger.current_report.hypotheses == hypotheses
        assert len(debugger.current_report.hypotheses) == len(hypotheses)


class TestVerificationPhase:
    """测试假设验证阶段"""

    def test_verify_hypothesis_success(self):
        """测试验证假设成功"""
        debugger = SystematicDebugger()

        # 准备假设
        hypothesis = Hypothesis(
            hypothesis_id="test-1",
            title="测试假设",
            description="测试描述",
            likelihood="high"
        )

        test_results = [
            "测试 1 通过",
            "测试 2 成功",
            "测试 3 passed"
        ]

        verification = debugger.verify_hypothesis(hypothesis, test_results)

        assert isinstance(verification, VerificationResult)
        assert verification.hypothesis_id == "test-1"
        assert verification.is_valid is True
        assert verification.confidence == 1.0

    def test_verify_hypothesis_failure(self):
        """测试验证假设失败"""
        debugger = SystematicDebugger()

        hypothesis = Hypothesis(
            hypothesis_id="test-2",
            title="测试假设",
            description="测试描述",
            likelihood="medium"
        )

        test_results = [
            "测试 1 失败",
            "测试 2 错误"
        ]

        verification = debugger.verify_hypothesis(hypothesis, test_results)

        assert verification.is_valid is False
        assert verification.confidence == 0.0

    def test_verify_hypothesis_partial_success(self):
        """测试部分成功的验证"""
        debugger = SystematicDebugger()

        hypothesis = Hypothesis(
            hypothesis_id="test-3",
            title="测试假设",
            description="测试描述",
            likelihood="medium"
        )

        test_results = [
            "测试 1 通过",
            "测试 2 失败",
            "测试 3 通过",
            "测试 4 失败"
        ]

        verification = debugger.verify_hypothesis(hypothesis, test_results)

        assert verification.confidence == 0.5
        assert verification.is_valid is False  # 置信度 < 0.5

    def test_verification_added_to_report(self):
        """测试验证结果添加到报告"""
        debugger = SystematicDebugger()

        # 初始化报告
        error_info = {
            "error_type": "ValueError",
            "error_message": "test",
            "stack_trace": []
        }
        debugger.start_debugging(error_info)

        hypothesis = Hypothesis(
            hypothesis_id="test-1",
            title="测试",
            description="测试",
            likelihood="high"
        )

        verification = debugger.verify_hypothesis(hypothesis, ["测试通过"])

        assert len(debugger.current_report.verifications) == 1
        assert debugger.current_report.verifications[0] == verification

    def test_debugging_history_tracking(self):
        """测试调试历史记录"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "TypeError",
            "error_message": "test",
            "stack_trace": []
        }
        debugger.start_debugging(error_info)

        assert len(debugger.debugging_history) == 1
        assert debugger.debugging_history[0]["phase"] == "error_observation"


class TestRootCauseConfirmationPhase:
    """测试根因确认阶段"""

    def test_confirm_root_cause(self):
        """测试确认根因"""
        debugger = SystematicDebugger()

        # 准备调试环境
        error_info = {
            "error_type": "ImportError",
            "error_message": "test",
            "stack_trace": []
        }
        debugger.start_debugging(error_info)

        observation = debugger.current_report.observation
        debugger.generate_hypotheses(observation)

        # 确认第一个假设为根因
        first_hypothesis_id = debugger.current_report.hypotheses[0].hypothesis_id
        root_cause = debugger.confirm_root_cause(first_hypothesis_id)

        assert isinstance(root_cause, RootCause)
        assert root_cause.root_cause_id == f"root-cause-{first_hypothesis_id}"
        assert root_cause.confirmed_hypothesis_id == first_hypothesis_id
        assert debugger.current_phase == DebuggingPhase.ROOT_CAUSE_CONFIRMATION

    def test_invalid_hypothesis_id(self):
        """测试无效的假设 ID"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "ValueError",
            "error_message": "test",
            "stack_trace": []
        }
        debugger.start_debugging(error_info)

        with pytest.raises(ValueError, match="无效的假设 ID"):
            debugger.confirm_root_cause("invalid-id")

    def test_root_cause_completeness(self):
        """测试根因分析完整性"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "SyntaxError",
            "error_message": "test",
            "stack_trace": []
        }
        debugger.start_debugging(error_info)

        observation = debugger.current_report.observation
        debugger.generate_hypotheses(observation)

        first_hypothesis_id = debugger.current_report.hypotheses[0].hypothesis_id
        root_cause = debugger.confirm_root_cause(first_hypothesis_id)

        # 检查所有必要字段
        assert root_cause.description
        assert len(root_cause.fix_suggestions) > 0
        assert len(root_cause.prevention_strategies) > 0
        assert len(root_cause.related_issues) > 0

    def test_fix_suggestions_generation(self):
        """测试修复建议生成"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "ImportError",
            "error_message": "No module",
            "stack_trace": []
        }
        debugger.start_debugging(error_info)

        observation = debugger.current_report.observation
        debugger.generate_hypotheses(observation)

        first_hypothesis_id = debugger.current_report.hypotheses[0].hypothesis_id
        root_cause = debugger.confirm_root_cause(first_hypothesis_id)

        # ImportError 应该有安装模块的建议
        assert any("pip install" in s or "安装" in s
                  for s in root_cause.fix_suggestions)

    def test_prevention_strategies_generation(self):
        """测试防止策略生成"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "SyntaxError",
            "error_message": "invalid syntax",
            "stack_trace": []
        }
        debugger.start_debugging(error_info)

        observation = debugger.current_report.observation
        debugger.generate_hypotheses(observation)

        first_hypothesis_id = debugger.current_report.hypotheses[0].hypothesis_id
        root_cause = debugger.confirm_root_cause(first_hypothesis_id)

        # 应该有测试相关的策略
        assert any("测试" in s or "test" in s.lower()
                  for s in root_cause.prevention_strategies)

    def test_debugging_report_completion(self):
        """测试调试报告完成"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "TypeError",
            "error_message": "test",
            "stack_trace": []
        }
        debugger.start_debugging(error_info)

        observation = debugger.current_report.observation
        debugger.generate_hypotheses(observation)

        first_hypothesis_id = debugger.current_report.hypotheses[0].hypothesis_id
        debugger.confirm_root_cause(first_hypothesis_id)

        # 验证报告完整性
        report = debugger.current_report
        assert report.observation is not None
        assert len(report.hypotheses) > 0
        assert report.root_cause is not None
        assert report.phase == DebuggingPhase.ROOT_CAUSE_CONFIRMATION
        assert report.created_at
        assert report.completed_at


class TestUtilityMethods:
    """测试工具方法"""

    def test_get_current_phase(self):
        """测试获取当前阶段"""
        debugger = SystematicDebugger()

        assert debugger.get_current_phase() == DebuggingPhase.ERROR_OBSERVATION

        debugger.current_phase = DebuggingPhase.VERIFICATION
        assert debugger.get_current_phase() == DebuggingPhase.VERIFICATION

    def test_get_debugging_report(self):
        """测试获取调试报告"""
        debugger = SystematicDebugger()

        # 初始阶段报告为 None
        assert debugger.get_debugging_report() is None

        # 开始调试后报告存在
        error_info = {
            "error_type": "ValueError",
            "error_message": "test",
            "stack_trace": []
        }
        debugger.start_debugging(error_info)

        report = debugger.get_debugging_report()
        assert report is not None
        assert isinstance(report, DebuggingReport)

    def test_get_debugging_history(self):
        """测试获取调试历史"""
        debugger = SystematicDebugger()

        # 初始历史为空
        assert debugger.get_debugging_history() == []

        # 添加历史记录
        error_info = {
            "error_type": "TypeError",
            "error_message": "test",
            "stack_trace": []
        }
        debugger.start_debugging(error_info)

        history = debugger.get_debugging_history()
        assert len(history) == 1
        assert history[0]["phase"] == "error_observation"


class TestCompleteWorkflow:
    """测试完整调试工作流"""

    def test_complete_debugging_workflow(self):
        """测试完整的 4 阶段调试流程"""
        debugger = SystematicDebugger()

        # 阶段 1: 错误观察
        error_info = {
            "error_type": "ImportError",
            "error_message": "No module named 'test_module'",
            "stack_trace": [
                'File "main.py", line 10, in <module>',
                "  import test_module"
            ],
            "code_context": {
                "file_path": "main.py",
                "line_number": 10
            }
        }

        observation = debugger.start_debugging(error_info)
        assert observation.error_type == "ImportError"
        assert debugger.current_phase == DebuggingPhase.ERROR_OBSERVATION
        assert len(debugger.debugging_history) == 1

        # 阶段 2: 假设生成
        hypotheses = debugger.generate_hypotheses(observation)
        assert len(hypotheses) >= 3
        assert debugger.current_phase == DebuggingPhase.HYPOTHESIS_GENERATION
        assert len(debugger.debugging_history) == 2

        # 阶段 3: 假设验证
        first_hypothesis = hypotheses[0]
        test_results = ["测试 1 通过", "测试 2 成功"]
        verification = debugger.verify_hypothesis(first_hypothesis, test_results)
        assert verification.is_valid is True
        assert debugger.current_phase == DebuggingPhase.VERIFICATION
        assert len(debugger.debugging_history) == 3

        # 阶段 4: 根因确认
        root_cause = debugger.confirm_root_cause(first_hypothesis.hypothesis_id)
        assert root_cause.confirmed_hypothesis_id == first_hypothesis.hypothesis_id
        assert debugger.current_phase == DebuggingPhase.ROOT_CAUSE_CONFIRMATION
        assert len(debugger.debugging_history) == 4

        # 验证最终报告
        report = debugger.get_debugging_report()
        assert report.observation == observation
        assert len(report.hypotheses) == len(hypotheses)
        assert report.root_cause == root_cause
        assert report.created_at
        assert report.completed_at

        # 验证调试历史
        history = debugger.get_debugging_history()
        assert len(history) == 4
        phases = [h["phase"] for h in history]
        assert "error_observation" in phases
        assert "hypothesis_generation" in phases
        assert "verification" in phases
        assert "root_cause_confirmation" in phases

    def test_workflow_with_syntax_error(self):
        """测试语法错误的完整流程"""
        debugger = SystematicDebugger()

        error_info = {
            "error_type": "SyntaxError",
            "error_message": "invalid syntax",
            "stack_trace": [
                'File "script.py", line 15'
            ]
        }

        # 完整流程
        observation = debugger.start_debugging(error_info)
        hypotheses = debugger.generate_hypotheses(observation)

        # 验证第一个假设
        verification = debugger.verify_hypothesis(
            hypotheses[0],
            ["语法检查通过", "修复错误后测试通过"]
        )

        # 确认根因
        root_cause = debugger.confirm_root_cause(hypotheses[0].hypothesis_id)

        # 验证
        assert observation.error_type == "SyntaxError"
        assert len(hypotheses) >= 3
        assert verification.is_valid is True
        assert root_cause.root_cause_id
        assert debugger.current_phase == DebuggingPhase.ROOT_CAUSE_CONFIRMATION
