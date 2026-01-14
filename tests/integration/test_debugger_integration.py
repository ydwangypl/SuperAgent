"""
SystematicDebugger 集成测试 - P1 Task 2.2

测试 SystematicDebugger 与 CodingAgent 的集成
"""

import pytest
from execution.coding_agent import CodingAgent
from execution.systematic_debugger import DebuggingPhase


class TestCodingAgentDebuggerIntegration:
    """测试 CodingAgent 与 SystematicDebugger 的集成"""

    def test_debugger_initialization(self):
        """测试 CodingAgent 初始化时创建 SystematicDebugger"""
        agent = CodingAgent()

        assert hasattr(agent, 'debugger')
        assert hasattr(agent, 'debugging_enabled')
        assert agent.debugging_enabled is True
        assert agent.debugger is not None

    def test_is_debugging_enabled(self):
        """测试调试功能启用检查"""
        agent = CodingAgent()

        assert agent.is_debugging_enabled() is True

    def test_get_current_debugging_phase_initial(self):
        """测试初始调试阶段"""
        agent = CodingAgent()

        # 初始阶段应该是 ERROR_OBSERVATION
        phase = agent.get_current_debugging_phase()
        assert phase == "error_observation"

    def test_debug_error_basic(self):
        """测试基本错误调试"""
        agent = CodingAgent()

        # 模拟错误
        error_type = "ImportError"
        error_message = "No module named 'test_module'"
        stack_trace = [
            'File "main.py", line 10, in <module>',
            "  import test_module"
        ]

        # 执行调试
        report = agent.debug_error(error_type, error_message, stack_trace)

        # 验证报告
        assert report is not None
        assert report["error_type"] == "ImportError"
        assert report["error_message"] == "No module named 'test_module'"
        assert len(report["hypotheses"]) >= 3
        assert report["root_cause"]["id"]
        assert len(report["root_cause"]["fix_suggestions"]) > 0
        assert len(report["root_cause"]["prevention_strategies"]) > 0
        assert report["debugging_phase"] == "root_cause_confirmation"
        assert report["created_at"]
        assert report["completed_at"]

    def test_debug_error_with_code_context(self):
        """测试带代码上下文的错误调试"""
        agent = CodingAgent()

        error_type = "SyntaxError"
        error_message = "invalid syntax"
        stack_trace = [
            'File "script.py", line 15'
        ]
        code_context = {
            "file_path": "script.py",
            "line_number": 15,
            "function": "process_data"
        }

        report = agent.debug_error(error_type, error_message, stack_trace, code_context)

        assert report is not None
        assert report["error_type"] == "SyntaxError"
        # 应该有语法相关的假设
        hypothesis_titles = [h["title"] for h in report["hypotheses"]]
        assert any("语法" in title or "syntax" in title.lower() for title in hypothesis_titles)

    def test_debug_error_value_error(self):
        """测试 ValueError 调试"""
        agent = CodingAgent()

        error_type = "ValueError"
        error_message = "invalid literal for int() with base 10: 'abc'"
        stack_trace = [
            'File "app.py", line 25, in convert',
            "  return int(value)"
        ]

        report = agent.debug_error(error_type, error_message, stack_trace)

        assert report is not None
        assert len(report["hypotheses"]) >= 3
        # 应该有参数相关的假设
        hypothesis_titles = [h["title"] for h in report["hypotheses"]]
        assert any("参数" in title for title in hypothesis_titles)

    def test_debug_error_type_error(self):
        """测试 TypeError 调试"""
        agent = CodingAgent()

        error_type = "TypeError"
        error_message = "unsupported operand type(s) for +: 'int' and 'str'"
        stack_trace = [
            'File "calc.py", line 30, in add',
            "  return a + b"
        ]

        report = agent.debug_error(error_type, error_message, stack_trace)

        assert report is not None
        assert report["error_type"] == "TypeError"
        # 验证修复建议
        assert len(report["root_cause"]["fix_suggestions"]) > 0

    def test_debugger_reset(self):
        """测试调试器重置"""
        agent = CodingAgent()

        # 执行一次调试
        report = agent.debug_error(
            "ValueError",
            "test error",
            ['File "test.py", line 1']
        )

        assert report is not None
        assert agent.get_current_debugging_phase() == "root_cause_confirmation"

        # 重置调试器
        agent.reset_debugger()

        # 验证重置后阶段恢复初始状态
        assert agent.get_current_debugging_phase() == "error_observation"

    def test_debug_error_comprehensive_workflow(self):
        """测试完整的调试工作流"""
        agent = CodingAgent()

        # ImportError 完整流程
        error_type = "ImportError"
        error_message = "No module named 'requests'"
        stack_trace = [
            'File "api_client.py", line 5, in <module>',
            "  import requests"
        ]
        code_context = {
            "file_path": "api_client.py",
            "line_number": 5
        }

        report = agent.debug_error(error_type, error_message, stack_trace, code_context)

        # 验证报告完整性
        assert report is not None

        # 验证假设
        hypotheses = report["hypotheses"]
        assert len(hypotheses) >= 3
        for h in hypotheses:
            assert "id" in h
            assert "title" in h
            assert "description" in h
            assert "likelihood" in h
            assert h["likelihood"] in ["low", "medium", "high"]

        # 验证根因
        root_cause = report["root_cause"]
        assert root_cause["id"]
        assert root_cause["description"]
        assert len(root_cause["fix_suggestions"]) > 0
        assert len(root_cause["prevention_strategies"]) > 0

        # ImportError 应该有安装相关的建议
        assert any("pip install" in s or "安装" in s
                  for s in root_cause["fix_suggestions"])

        # 验证时间戳
        assert report["created_at"]
        assert report["completed_at"]

    def test_multiple_debugging_sessions(self):
        """测试多次调试会话"""
        agent = CodingAgent()

        # 第一次调试
        report1 = agent.debug_error(
            "ValueError",
            "error 1",
            ['File "test1.py"']
        )

        assert report1 is not None
        phase1 = agent.get_current_debugging_phase()

        # 重置
        agent.reset_debugger()

        # 第二次调试
        report2 = agent.debug_error(
            "TypeError",
            "error 2",
            ['File "test2.py"']
        )

        assert report2 is not None
        assert report2["error_type"] == "TypeError"

        # 验证两次调试独立
        assert report1["error_type"] == "ValueError"
        assert report2["error_type"] == "TypeError"

    def test_debugging_disabled_scenario(self):
        """测试调试功能禁用的场景"""
        agent = CodingAgent()

        # 模拟调试器不可用
        original_debugger = agent.debugger
        agent.debugger = None

        # 尝试调试应该返回 None
        report = agent.debug_error(
            "ValueError",
            "test",
            ['File "test.py"']
        )

        assert report is None

        # 恢复
        agent.debugger = original_debugger

    def test_hypothesis_quality(self):
        """测试生成的假设质量"""
        agent = CodingAgent()

        report = agent.debug_error(
            "ImportError",
            "No module named 'numpy'",
            [
                'File "data.py", line 3',
                "  import numpy as np"
            ]
        )

        assert report is not None
        hypotheses = report["hypotheses"]

        # 检查假设多样性
        titles = [h["title"] for h in hypotheses]
        assert len(titles) == len(set(titles)), "假设标题应该是唯一的"

        # 检查至少有一个高可能性假设
        high_likelihood_count = sum(
            1 for h in hypotheses if h["likelihood"] == "high"
        )
        assert high_likelihood_count >= 1, "应该至少有一个高可能性假设"

    def test_fix_suggestions_relevance(self):
        """测试修复建议的相关性"""
        agent = CodingAgent()

        # SyntaxError 应该有语法修复建议
        report = agent.debug_error(
            "SyntaxError",
            "invalid syntax",
            ['File "code.py", line 10']
        )

        assert report is not None
        fix_suggestions = report["root_cause"]["fix_suggestions"]

        # 应该有修复相关的建议
        assert any("修复" in s or "fix" in s.lower() or "语法" in s
                  for s in fix_suggestions)

    def test_prevention_strategies_completeness(self):
        """测试防止策略的完整性"""
        agent = CodingAgent()

        report = agent.debug_error(
            "ValueError",
            "test error",
            ['File "app.py"']
        )

        assert report is not None
        strategies = report["root_cause"]["prevention_strategies"]

        # 应该有测试相关的策略
        assert any("测试" in s or "test" in s.lower()
                  for s in strategies)

        # 应该有防止回归的策略
        assert len(strategies) >= 3


class TestDebuggingPhase:
    """测试调试阶段"""

    def test_four_phases_execution(self):
        """测试 4 个调试阶段依次执行"""
        agent = CodingAgent()

        # 初始阶段
        assert agent.get_current_debugging_phase() == "error_observation"

        # 执行完整调试
        report = agent.debug_error(
            "ImportError",
            "No module",
            ['File "test.py"']
        )

        # 最终阶段应该是根因确认
        assert agent.get_current_debugging_phase() == "root_cause_confirmation"
        assert report["debugging_phase"] == "root_cause_confirmation"

    def test_phase_progression(self):
        """测试阶段推进"""
        agent = CodingAgent()

        # 每次调试都会完整经历 4 个阶段
        agent.debug_error("ValueError", "test", ['File "x.py"'])
        phase_after_first = agent.get_current_debugging_phase()

        agent.reset_debugger()
        agent.debug_error("TypeError", "test", ['File "y.py"'])
        phase_after_second = agent.get_current_debugging_phase()

        # 两次调试都应该到达最终阶段
        assert phase_after_first == "root_cause_confirmation"
        assert phase_after_second == "root_cause_confirmation"
