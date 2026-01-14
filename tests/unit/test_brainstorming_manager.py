"""
BrainstormingManager 单元测试 - P1 Task 2.1

测试脑暴管理器的核心功能:
1. 需求收集
2. 方案探索
3. 方案对比
4. 决策确认
"""

import pytest
from planning.brainstorming_manager import (
    BrainstormingManager,
    BrainstormingPhase,
    DesignOption,
    DesignSpec
)


class TestBrainstormingManagerInitialization:
    """测试 BrainstormingManager 初始化"""

    def test_initialization(self):
        """测试基本初始化"""
        manager = BrainstormingManager()

        assert manager.current_phase == BrainstormingPhase.REQUIREMENT_GATHERING
        assert manager.conversation_history == []
        assert manager.design_options == []
        assert manager.current_requirements == {}

    def test_reset(self):
        """测试重置功能"""
        manager = BrainstormingManager()

        # 修改状态
        manager.current_phase = BrainstormingPhase.DECISION_MAKING
        manager.conversation_history.append({"test": "data"})

        # 重置
        manager.reset()

        assert manager.current_phase == BrainstormingPhase.REQUIREMENT_GATHERING
        assert manager.conversation_history == []
        assert manager.design_options == []
        assert manager.current_requirements == {}


class TestRequirementGathering:
    """测试需求收集阶段"""

    def test_start_brainstorming(self):
        """测试开始脑暴"""
        manager = BrainstormingManager()

        result = manager.start_brainstorming("实现用户登录功能")

        assert result["phase"] == "requirement_gathering"
        assert "questions" in result
        assert len(result["questions"]) > 0
        assert result["user_request"] == "实现用户登录功能"
        assert manager.current_phase == BrainstormingPhase.REQUIREMENT_GATHERING

    def test_generate_questions_for_api_request(self):
        """测试为 API 请求生成问题"""
        manager = BrainstormingManager()

        result = manager.start_brainstorming("实现用户登录 API")

        questions = result["questions"]

        # 检查基础问题
        base_questions = [
            "这个功能的主要用户是谁?",
            "核心功能需求是什么?"
        ]

        for q in base_questions:
            assert q in questions

        # 检查 API 特定问题
        api_questions = [
            "API 需要支持哪些操作",
            "需要认证和授权吗?"
        ]

        has_api_question = any(any(q in question for q in api_questions) for question in questions)
        assert has_api_question

    def test_conversation_history_tracking(self):
        """测试对话历史记录"""
        manager = BrainstormingManager()

        manager.start_brainstorming("测试请求")

        assert len(manager.conversation_history) == 1
        assert manager.conversation_history[0]["phase"] == "requirement_gathering"
        assert "user_request" in manager.conversation_history[0]
        assert "timestamp" in manager.conversation_history[0]


class TestSolutionExploration:
    """测试方案探索阶段"""

    def test_explore_solutions(self):
        """测试探索解决方案"""
        manager = BrainstormingManager()

        # 先完成需求收集
        manager.start_brainstorming("测试功能")

        # 探索方案
        requirements = {
            "用户": "开发者",
            "核心功能": "数据存储",
            "性能要求": "中等"
        }

        options = manager.explore_solutions(requirements)

        assert len(options) >= 3  # 至少 3 个选项
        assert manager.current_phase == BrainstormingPhase.SOLUTION_EXPLORATION
        assert manager.current_requirements == requirements
        assert len(manager.design_options) == len(options)

    def test_design_options_structure(self):
        """测试设计选项结构"""
        manager = BrainstormingManager()

        manager.start_brainstorming("测试")
        options = manager.explore_solutions({})

        # 检查第一个选项
        option = options[0]

        assert isinstance(option, DesignOption)
        assert option.option_id  # 非空
        assert option.title
        assert option.description
        assert len(option.pros) > 0
        assert len(option.cons) > 0
        assert option.implementation_complexity in ["low", "medium", "high"]
        assert option.risk_level in ["low", "medium", "high"]
        assert option.estimated_time

    def test_three_default_options(self):
        """测试默认生成 3 个选项"""
        manager = BrainstormingManager()

        manager.start_brainstorming("测试")
        options = manager.explore_solutions({})

        assert len(options) == 3

        # 检查选项类型
        titles = [opt.title for opt in options]
        assert any("简单" in title for title in titles)
        assert any("平衡" in title for title in titles)
        assert any("性能" in title or "高性能" in title for title in titles)


class TestAlternativeComparison:
    """测试方案对比阶段"""

    def test_compare_alternatives(self):
        """测试方案对比"""
        manager = BrainstormingManager()

        # 完成前两个阶段
        manager.start_brainstorming("测试")
        manager.explore_solutions({})

        # 对比方案
        comparison = manager.compare_alternatives()

        assert "options" in comparison
        assert "comparison_matrix" in comparison
        assert "recommendation" in comparison
        assert manager.current_phase == BrainstormingPhase.ALTERNATIVE_COMPARISON

    def test_comparison_matrix(self):
        """测试对比矩阵"""
        manager = BrainstormingManager()

        manager.start_brainstorming("测试")
        manager.explore_solutions({})

        comparison = manager.compare_alternatives()
        matrix = comparison["comparison_matrix"]

        assert "complexity" in matrix
        assert "time" in matrix
        assert "risk" in matrix
        assert len(matrix["complexity"]) == len(manager.design_options)

    def test_recommendation(self):
        """测试推荐功能"""
        manager = BrainstormingManager()

        manager.start_brainstorming("测试")
        manager.explore_solutions({})

        comparison = manager.compare_alternatives()
        recommendation = comparison["recommendation"]

        assert "option_id" in recommendation
        assert "title" in recommendation
        assert "reason" in recommendation


class TestDecisionMaking:
    """测试决策确认阶段"""

    def test_finalize_design(self):
        """测试确认设计"""
        manager = BrainstormingManager()

        # 完成前面所有阶段
        manager.start_brainstorming("测试功能")
        manager.explore_solutions({"需求": "测试"})
        manager.compare_alternatives()

        # 选择第一个选项
        selected_id = manager.design_options[0].option_id
        design_spec = manager.finalize_design(selected_id)

        assert isinstance(design_spec, DesignSpec)
        assert design_spec.selected_option.option_id == selected_id
        assert len(design_spec.considered_alternatives) >= 2
        assert design_spec.rationale
        assert design_spec.architecture_notes
        assert len(design_spec.acceptance_criteria) > 0
        assert manager.current_phase == BrainstormingPhase.DECISION_MAKING

    def test_invalid_option_id(self):
        """测试无效的选项 ID"""
        manager = BrainstormingManager()

        manager.start_brainstorming("测试")
        manager.explore_solutions({})
        manager.compare_alternatives()

        # 使用无效 ID
        with pytest.raises(ValueError, match="无效的选项 ID"):
            manager.finalize_design("invalid-id")

    def test_design_spec_completeness(self):
        """测试设计规格完整性"""
        manager = BrainstormingManager()

        manager.start_brainstorming("测试功能")
        manager.explore_solutions({"用户": "开发者", "功能": "API"})
        manager.compare_alternatives()

        selected_id = manager.design_options[1].option_id
        design_spec = manager.finalize_design(selected_id)

        # 检查所有必要字段
        assert design_spec.requirements
        assert design_spec.selected_option
        assert design_spec.considered_alternatives
        assert design_spec.rationale
        assert len(design_spec.rationale) > 50  # 至少 50 字
        assert design_spec.architecture_notes
        assert len(design_spec.architecture_notes) > 100  # 至少 100 字
        assert design_spec.acceptance_criteria
        assert len(design_spec.acceptance_criteria) >= 3  # 至少 3 条
        assert design_spec.created_at


class TestUtilityMethods:
    """测试工具方法"""

    def test_get_current_phase(self):
        """测试获取当前阶段"""
        manager = BrainstormingManager()

        assert manager.get_current_phase() == BrainstormingPhase.REQUIREMENT_GATHERING

        manager.start_brainstorming("测试")
        assert manager.get_current_phase() == BrainstormingPhase.REQUIREMENT_GATHERING

        manager.explore_solutions({})
        assert manager.get_current_phase() == BrainstormingPhase.SOLUTION_EXPLORATION

    def test_get_conversation_history(self):
        """测试获取对话历史"""
        manager = BrainstormingManager()

        manager.start_brainstorming("测试")
        manager.explore_solutions({})

        history = manager.get_conversation_history()

        assert len(history) == 2
        assert history[0]["phase"] == "requirement_gathering"
        assert history[1]["phase"] == "solution_exploration"


class TestErrorHandling:
    """测试错误处理"""

    def test_compare_without_options(self):
        """测试在没有选项时对比"""
        manager = BrainstormingManager()

        with pytest.raises(ValueError, match="没有设计选项可对比"):
            manager.compare_alternatives()

    def test_finalize_without_exploration(self):
        """测试在未探索方案时确认设计"""
        manager = BrainstormingManager()

        manager.start_brainstorming("测试")
        # 跳过 explore_solutions()

        with pytest.raises(ValueError, match="无效的选项 ID"):
            manager.finalize_design("option-1")


class TestCompleteWorkflow:
    """测试完整工作流"""

    def test_complete_brainstorming_workflow(self):
        """测试完整的脑暴流程"""
        manager = BrainstormingManager()

        # 阶段 1: 需求收集
        result1 = manager.start_brainstorming("实现用户登录 API")
        assert result1["phase"] == "requirement_gathering"
        assert len(result1["questions"]) > 0

        # 阶段 2: 方案探索
        requirements = {
            "用户": "Web 应用用户",
            "核心功能": "登录认证",
            "性能要求": "支持 1000 并发"
        }
        options = manager.explore_solutions(requirements)
        assert len(options) >= 3

        # 阶段 3: 方案对比
        comparison = manager.compare_alternatives()
        assert "recommendation" in comparison
        recommended_id = comparison["recommendation"]["option_id"]

        # 阶段 4: 决策确认
        design_spec = manager.finalize_design(recommended_id)

        # 验证最终结果
        assert isinstance(design_spec, DesignSpec)
        assert design_spec.requirements == requirements
        assert len(design_spec.considered_alternatives) >= 3
        assert design_spec.selected_option.option_id == recommended_id
        assert len(design_spec.acceptance_criteria) >= 5  # 应该有 5+ 条验收标准

        # 验证对话历史
        history = manager.get_conversation_history()
        assert len(history) == 4  # 4 个阶段
        phases = [h["phase"] for h in history]
        assert "requirement_gathering" in phases
        assert "solution_exploration" in phases
        assert "alternative_comparison" in phases
        assert "decision_making" in phases
