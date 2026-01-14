"""
SkillChecker 单元测试 - P1 Task 2.3

测试技能检查器的核心功能:
1. 技能启用/禁用
2. 任务技能检查
3. 技能需求映射
4. 技能历史记录
"""

import pytest
from orchestration.skill_checker import (
    SkillChecker,
    Skill,
    SkillNotAvailableError,
    SkillRequirement
)


class TestSkillCheckerInitialization:
    """测试 SkillChecker 初始化"""

    def test_initialization(self):
        """测试基本初始化"""
        checker = SkillChecker()

        assert checker.available_skills == set()
        assert checker.skill_history == []

    def test_reset(self):
        """测试重置功能"""
        checker = SkillChecker()

        # 修改状态
        checker.enable_skill(Skill.BRAINSTORMING)
        checker.check_task_skills("feature_development", auto_fail=False)

        # 重置
        checker.reset()

        assert checker.available_skills == set()
        assert checker.skill_history == []


class TestSkillManagement:
    """测试技能管理"""

    def test_enable_skill(self):
        """测试启用技能"""
        checker = SkillChecker()

        checker.enable_skill(Skill.BRAINSTORMING)

        assert Skill.BRAINSTORMING in checker.available_skills
        assert len(checker.available_skills) == 1

    def test_disable_skill(self):
        """测试禁用技能"""
        checker = SkillChecker()

        checker.enable_skill(Skill.TEST_DRIVEN_DEVELOPMENT)
        assert Skill.TEST_DRIVEN_DEVELOPMENT in checker.available_skills

        checker.disable_skill(Skill.TEST_DRIVEN_DEVELOPMENT)
        assert Skill.TEST_DRIVEN_DEVELOPMENT not in checker.available_skills

    def test_is_skill_available(self):
        """测试技能可用性检查"""
        checker = SkillChecker()

        # 未启用时
        assert checker.is_skill_available(Skill.BRAINSTORMING) is False

        # 启用后
        checker.enable_skill(Skill.BRAINSTORMING)
        assert checker.is_skill_available(Skill.BRAINSTORMING) is True

    def test_enable_all_skills(self):
        """测试启用所有技能"""
        checker = SkillChecker()

        checker.enable_all_skills()

        assert len(checker.available_skills) == len(Skill)
        for skill in Skill:
            assert skill in checker.available_skills

    def test_enable_p0_skills(self):
        """测试启用 P0 核心技能"""
        checker = SkillChecker()

        checker.enable_p0_skills()

        assert Skill.TEST_DRIVEN_DEVELOPMENT in checker.available_skills
        assert Skill.CODE_REVIEW in checker.available_skills
        assert Skill.BRAINSTORMING not in checker.available_skills
        assert Skill.SYSTEMATIC_DEBUGGING not in checker.available_skills

    def test_enable_p1_skills(self):
        """测试启用 P1 增强技能"""
        checker = SkillChecker()

        checker.enable_p1_skills()

        assert Skill.BRAINSTORMING in checker.available_skills
        assert Skill.SYSTEMATIC_DEBUGGING in checker.available_skills
        assert Skill.TEST_DRIVEN_DEVELOPMENT not in checker.available_skills
        assert Skill.CODE_REVIEW not in checker.available_skills


class TestSkillChecking:
    """测试技能检查"""

    def test_check_task_with_all_skills(self):
        """测试所有技能都可用的情况"""
        checker = SkillChecker()
        checker.enable_all_skills()

        # 功能开发需要脑暴和TDD
        result = checker.check_task_skills("feature_development")

        assert result is True

    def test_check_task_missing_skills_no_fail(self):
        """测试缺少技能但不抛出异常"""
        checker = SkillChecker()
        # 不启用任何技能

        result = checker.check_task_skills("feature_development", auto_fail=False)

        assert result is False

    def test_check_task_missing_skills_auto_fail(self):
        """测试缺少技能时自动抛出异常"""
        checker = SkillChecker()
        # 不启用任何技能

        with pytest.raises(SkillNotAvailableError) as exc_info:
            checker.check_task_skills("feature_development", auto_fail=True)

        assert exc_info.value.task_type == "feature_development"
        assert len(exc_info.value.missing_skills) > 0

    def test_check_task_with_no_requirements(self):
        """测试没有特定技能要求的任务"""
        checker = SkillChecker()
        # 不启用任何技能

        # 简单任务可能不在映射表中
        result = checker.check_task_skills("simple_task", auto_fail=False)

        # 应该通过 (没有特定要求)
        assert result is True

    def test_check_bug_fixing_skills(self):
        """测试 bug 修复任务的技能检查"""
        checker = SkillChecker()

        # 只启用调试技能
        checker.enable_skill(Skill.SYSTEMATIC_DEBUGGING)

        # Bug 修复需要调试和 TDD
        result = checker.check_task_skills("bug_fixing", auto_fail=False)

        assert result is False  # 缺少 TDD

    def test_check_refactoring_skills(self):
        """测试重构任务的技能检查"""
        checker = SkillChecker()

        # 重构需要全部 4 个技能
        checker.enable_skill(Skill.BRAINSTORMING)
        checker.enable_skill(Skill.SYSTEMATIC_DEBUGGING)
        # 缺少 TDD 和 CODE_REVIEW

        result = checker.check_task_skills("refactoring", auto_fail=False)

        assert result is False

    def test_skill_history_tracking(self):
        """测试技能检查历史记录"""
        checker = SkillChecker()
        checker.enable_skill(Skill.BRAINSTORMING)

        checker.check_task_skills("feature_development", auto_fail=False)

        history = checker.get_skill_history()
        assert len(history) == 1
        assert history[0]["task_type"] == "feature_development"
        assert "passed" in history[0]

    def test_multiple_task_checks(self):
        """测试多次任务检查"""
        checker = SkillChecker()
        checker.enable_all_skills()

        # 多次检查
        checker.check_task_skills("feature_development")
        checker.check_task_skills("bug_fixing")
        checker.check_task_skills("code_review")

        history = checker.get_skill_history()
        assert len(history) == 3

        # 验证最后一次通过
        assert history[2]["passed"] is True


class TestSkillMapping:
    """测试技能映射"""

    def test_feature_development_skills(self):
        """测试功能开发的技能映射"""
        checker = SkillChecker()

        required = checker.get_required_skills("feature_development")

        assert Skill.BRAINSTORMING in required
        assert Skill.TEST_DRIVEN_DEVELOPMENT in required
        assert len(required) == 2

    def test_api_development_skills(self):
        """测试 API 开发的技能映射"""
        checker = SkillChecker()

        required = checker.get_required_skills("api_development")

        assert Skill.BRAINSTORMING in required
        assert Skill.TEST_DRIVEN_DEVELOPMENT in required

    def test_bug_fixing_skills(self):
        """测试 bug 修复的技能映射"""
        checker = SkillChecker()

        required = checker.get_required_skills("bug_fixing")

        assert Skill.SYSTEMATIC_DEBUGGING in required
        assert Skill.TEST_DRIVEN_DEVELOPMENT in required

    def test_refactoring_skills(self):
        """测试重构的技能映射"""
        checker = SkillChecker()

        required = checker.get_required_skills("refactoring")

        # 重构需要所有 4 个技能
        assert Skill.BRAINSTORMING in required
        assert Skill.TEST_DRIVEN_DEVELOPMENT in required
        assert Skill.SYSTEMATIC_DEBUGGING in required
        assert Skill.CODE_REVIEW in required
        assert len(required) == 4

    def test_code_review_skills(self):
        """测试代码审查的技能映射"""
        checker = SkillChecker()

        required = checker.get_required_skills("code_review")

        assert Skill.CODE_REVIEW in required
        assert len(required) == 1

    def test_unknown_task_skills(self):
        """测试未知任务的技能映射"""
        checker = SkillChecker()

        required = checker.get_required_skills("unknown_task")

        assert len(required) == 0


class TestSkillRequirement:
    """测试技能需求"""

    def test_get_skill_requirement(self):
        """测试获取技能需求"""
        checker = SkillChecker()

        requirement = checker.get_skill_requirement("feature_development")

        assert requirement is not None
        assert requirement.task_type == "feature_development"
        assert len(requirement.required_skills) > 0
        assert requirement.description
        assert requirement.guidance

    def test_get_skill_requirement_no_requirements(self):
        """测试没有技能需求的任务"""
        checker = SkillChecker()

        requirement = checker.get_skill_requirement("simple_task")

        assert requirement is None

    def test_skill_requirement_guidance_content(self):
        """测试技能需求的指导内容"""
        checker = SkillChecker()

        requirement = checker.get_skill_requirement("feature_development")

        # 应该包含如何启用技能的指导
        assert "启用" in requirement.guidance or "enable" in requirement.guidance.lower()

    def test_debugging_skill_guidance(self):
        """测试调试技能的指导"""
        checker = SkillChecker()

        requirement = checker.get_skill_requirement("bug_fixing")

        assert requirement is not None
        assert Skill.SYSTEMATIC_DEBUGGING in requirement.required_skills
        # 应该有 SystematicDebugger 相关的指导
        assert "调试" in requirement.guidance or "debugging" in requirement.guidance.lower()


class TestSkillStatus:
    """测试技能状态"""

    def test_get_skill_status(self):
        """测试获取技能状态"""
        checker = SkillChecker()

        status = checker.get_skill_status()

        assert len(status) == len(Skill)
        # 初始所有技能都不可用
        for available in status.values():
            assert available is False

    def test_get_skill_status_after_enable(self):
        """测试启用后的技能状态"""
        checker = SkillChecker()

        checker.enable_skill(Skill.BRAINSTORMING)
        status = checker.get_skill_status()

        assert status["brainstorming"] is True
        assert status["test_driven_development"] is False
        assert status["systematic_debugging"] is False
        assert status["code_review"] is False

    def test_print_skill_status(self, capsys):
        """测试打印技能状态"""
        checker = SkillChecker()
        checker.enable_skill(Skill.TEST_DRIVEN_DEVELOPMENT)

        checker.print_skill_status()

        captured = capsys.readouterr()
        assert "技能状态" in captured.out
        assert "test_driven_development" in captured.out


class TestErrorHandling:
    """测试错误处理"""

    def test_skill_not_available_error_content(self):
        """测试技能异常的内容"""
        checker = SkillChecker()
        # 不启用任何技能

        try:
            checker.check_task_skills("feature_development", auto_fail=True)
            assert False, "应该抛出异常"
        except SkillNotAvailableError as e:
            assert e.task_type == "feature_development"
            assert len(e.missing_skills) > 0
            assert "feature_development" in str(e)

    def test_partial_skill_availability(self):
        """测试部分技能可用的情况"""
        checker = SkillChecker()

        # 只启用脑暴,不启用 TDD
        checker.enable_skill(Skill.BRAINSTORMING)

        # 功能开发需要脑暴和 TDD
        result = checker.check_task_skills("feature_development", auto_fail=False)

        assert result is False

        # 验证历史记录
        history = checker.get_skill_history()
        assert history[0]["passed"] is False
        assert "test_driven_development" in history[0]["missing_skills"]


class TestUtilityMethods:
    """测试工具方法"""

    def test_get_available_skills(self):
        """测试获取可用技能"""
        checker = SkillChecker()

        skills = checker.get_available_skills()
        assert len(skills) == 0

        checker.enable_skill(Skill.BRAINSTORMING)
        checker.enable_skill(Skill.CODE_REVIEW)

        skills = checker.get_available_skills()
        assert len(skills) == 2
        assert Skill.BRAINSTORMING in skills
        assert Skill.CODE_REVIEW in skills

    def test_get_skill_history(self):
        """测试获取历史记录"""
        checker = SkillChecker()

        history1 = checker.get_skill_history()
        assert len(history1) == 0

        checker.enable_all_skills()
        checker.check_task_skills("feature_development")

        history2 = checker.get_skill_history()
        assert len(history2) == 1
        assert "timestamp" in history2[0]


class TestCompleteWorkflow:
    """测试完整工作流"""

    def test_complete_skill_checking_workflow(self):
        """测试完整的技能检查工作流"""
        checker = SkillChecker()

        # 初始状态: 无技能
        assert len(checker.get_available_skills()) == 0

        # 启用 P0 技能
        checker.enable_p0_skills()

        # 检查代码审查任务 (只需要 P0 技能)
        result = checker.check_task_skills("code_review")
        assert result is True

        # 检查功能开发任务 (需要 P1 技能)
        result = checker.check_task_skills("feature_development", auto_fail=False)
        assert result is False  # 缺少脑暴技能

        # 2. 启用 P1 技能 (注意: 这会覆盖 P0 技能)
        checker.enable_p1_skills()

        # 再次检查功能开发任务 - 应该仍然失败, 因为缺少 P0 技能 (TDD)
        result = checker.check_task_skills("feature_development", auto_fail=False)
        assert result is False

        # 3. 启用所有技能
        checker.enable_all_skills()

        # 现在检查功能开发任务应该通过
        result = checker.check_task_skills("feature_development")
        assert result is True

        # 验证历史记录有多次检查
        history = checker.get_skill_history()
        assert len(history) >= 3

    def test_workflow_with_refactoring(self):
        """测试重构任务的完整流程"""
        checker = SkillChecker()

        # 重构需要所有技能
        checker.enable_all_skills()

        # 检查重构任务
        result = checker.check_task_skills("refactoring")

        assert result is True

        # 验证需要的技能
        required = checker.get_required_skills("refactoring")
        assert len(required) == 4  # 全部技能

    def test_multiple_tasks_different_requirements(self):
        """测试多个不同需求的任务"""
        checker = SkillChecker()
        checker.enable_all_skills()

        # 测试不同类型的任务
        tasks = [
            "feature_development",
            "bug_fixing",
            "code_review",
            "refactoring"
        ]

        for task in tasks:
            result = checker.check_task_skills(task)
            assert result is True, f"任务 '{task}' 应该通过技能检查"
