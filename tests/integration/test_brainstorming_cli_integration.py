"""
CLI 集成测试 - P1 Task 2.1

测试 BrainstormingManager 与 CLI 的集成
"""

import pytest
from cli.main import SuperAgentCLI
from planning.brainstorming_manager import BrainstormingPhase


class TestCLIIntegration:
    """测试 CLI 集成"""

    def test_brainstorming_manager_initialization(self):
        """测试 CLI 初始化时创建 BrainstormingManager"""
        cli = SuperAgentCLI()

        assert hasattr(cli, 'brainstorming_mgr')
        assert hasattr(cli, 'brainstorming_enabled')
        assert cli.brainstorming_enabled is True
        assert cli.brainstorming_mgr is not None

    def test_should_brainstorm_simple_task(self):
        """测试简单任务不触发脑暴"""
        cli = SuperAgentCLI()

        simple_inputs = [
            "帮助",
            "status",
            "查看文件列表",
            "test feature"
        ]

        for user_input in simple_inputs:
            result = cli._should_brainstorm(user_input)
            assert result is False, f"简单任务不应触发脑暴: {user_input}"

    def test_should_brainstorm_complex_task(self):
        """测试复杂任务触发脑暴"""
        cli = SuperAgentCLI()

        complex_inputs = [
            "实现用户登录功能",
            "添加数据库支持",
            "设计新的架构",
            "开发API接口"
        ]

        for user_input in complex_inputs:
            result = cli._should_brainstorm(user_input)
            assert result is True, f"复杂任务应触发脑暴: {user_input}"

    def test_brainstorming_workflow(self):
        """测试完整的脑暴工作流"""
        cli = SuperAgentCLI()

        # 运行脑暴流程
        user_input = "实现用户认证系统"

        # 重置脑暴管理器以确保干净状态
        cli.brainstorming_mgr.reset()

        # 执行脑暴 (会打印输出,这里只验证不报错)
        try:
            cli._run_brainstorming(user_input)
            workflow_completed = True
        except Exception as e:
            workflow_completed = False
            print(f"脑暴流程错误: {e}")

        assert workflow_completed, "脑暴流程应成功完成"

        # 验证脑暴管理器状态
        assert cli.brainstorming_mgr.current_phase == BrainstormingPhase.DECISION_MAKING
        assert len(cli.brainstorming_mgr.design_options) == 3
        assert len(cli.brainstorming_mgr.conversation_history) == 4  # 4 个阶段

    def test_brainstorming_design_spec_generation(self):
        """测试设计规格生成"""
        cli = SuperAgentCLI()
        cli.brainstorming_mgr.reset()

        # 快速完成脑暴流程
        cli.brainstorming_mgr.start_brainstorming("测试功能")
        cli.brainstorming_mgr.explore_solutions({"用户": "测试者"})
        comparison = cli.brainstorming_mgr.compare_alternatives()

        # 选择推荐的方案
        recommended_id = comparison["recommendation"]["option_id"]
        design_spec = cli.brainstorming_mgr.finalize_design(recommended_id)

        # 验证设计规格
        assert design_spec.requirements
        assert design_spec.selected_option
        assert len(design_spec.considered_alternatives) >= 2
        assert design_spec.rationale
        assert len(design_spec.rationale) > 50
        assert design_spec.architecture_notes
        assert len(design_spec.architecture_notes) > 100
        assert len(design_spec.acceptance_criteria) >= 3

    def test_brainstorming_disabled(self):
        """测试脑暴功能禁用的情况"""
        # 模拟脑暴管理器不可用
        cli = SuperAgentCLI()
        original_mgr = cli.brainstorming_mgr
        cli.brainstorming_mgr = None
        cli.brainstorming_enabled = False

        # 即使是复杂任务也不应触发脑暴
        result = cli._should_brainstorm("实现复杂功能")
        assert result is False

        # 恢复
        cli.brainstorming_mgr = original_mgr
        cli.brainstorming_enabled = True


class TestBrainstormingPhases:
    """测试脑暴的各个阶段"""

    def test_requirement_gathering_phase(self):
        """测试需求收集阶段"""
        cli = SuperAgentCLI()
        cli.brainstorming_mgr.reset()

        result = cli.brainstorming_mgr.start_brainstorming("实现API接口")

        assert result["phase"] == "requirement_gathering"
        assert len(result["questions"]) > 0
        assert "用户" in result["questions"][0]

    def test_solution_exploration_phase(self):
        """测试方案探索阶段"""
        cli = SuperAgentCLI()
        cli.brainstorming_mgr.reset()

        cli.brainstorming_mgr.start_brainstorming("测试")
        options = cli.brainstorming_mgr.explore_solutions({"需求": "测试"})

        assert len(options) >= 3
        assert all(opt.option_id for opt in options)
        assert all(opt.title for opt in options)

    def test_alternative_comparison_phase(self):
        """测试方案对比阶段"""
        cli = SuperAgentCLI()
        cli.brainstorming_mgr.reset()

        cli.brainstorming_mgr.start_brainstorming("测试")
        cli.brainstorming_mgr.explore_solutions({})
        comparison = cli.brainstorming_mgr.compare_alternatives()

        assert "options" in comparison
        assert "comparison_matrix" in comparison
        assert "recommendation" in comparison
        assert comparison["recommendation"]["option_id"]

    def test_decision_making_phase(self):
        """测试决策确认阶段"""
        cli = SuperAgentCLI()
        cli.brainstorming_mgr.reset()

        cli.brainstorming_mgr.start_brainstorming("测试")
        cli.brainstorming_mgr.explore_solutions({})
        comparison = cli.brainstorming_mgr.compare_alternatives()

        # 选择推荐的方案
        recommended_id = comparison["recommendation"]["option_id"]
        design_spec = cli.brainstorming_mgr.finalize_design(recommended_id)

        assert design_spec.selected_option.option_id == recommended_id
        assert design_spec.created_at
