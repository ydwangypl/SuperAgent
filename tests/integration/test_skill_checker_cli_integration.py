"""
SkillChecker CLI 集成测试 - P1 Task 2.3

测试 SkillChecker 与 CLI 的集成
"""

import pytest
from cli.main import SuperAgentCLI


class TestSkillCheckerCLIInitialization:
    """测试 CLI 中 SkillChecker 的初始化"""

    def test_skill_checker_initialization(self):
        """测试 CLI 初始化时创建 SkillChecker"""
        cli = SuperAgentCLI()

        assert hasattr(cli, 'skill_checker')
        assert hasattr(cli, 'skill_checker_enabled')
        assert cli.skill_checker_enabled is True
        assert cli.skill_checker is not None

    def test_skill_checker_default_skills_enabled(self):
        """测试默认情况下所有技能已启用"""
        cli = SuperAgentCLI()

        # CLI 初始化时默认启用所有技能
        from orchestration.skill_checker import Skill
        assert cli.skill_checker.is_skill_available(Skill.BRAINSTORMING)
        assert cli.skill_checker.is_skill_available(Skill.TEST_DRIVEN_DEVELOPMENT)
        assert cli.skill_checker.is_skill_available(Skill.SYSTEMATIC_DEBUGGING)
        assert cli.skill_checker.is_skill_available(Skill.CODE_REVIEW)


class TestSkillsCommand:
    """测试 skills 命令"""

    def test_skills_status_command(self, capsys):
        """测试 skills status 命令"""
        cli = SuperAgentCLI()

        cli.onecmd("skills status")

        captured = capsys.readouterr()
        assert "技能状态" in captured.out
        assert "brainstorming" in captured.out
        assert "test_driven_development" in captured.out
        assert "systematic_debugging" in captured.out
        assert "code_review" in captured.out

    def test_skills_enable_command(self, capsys):
        """测试 skills enable 命令"""
        cli = SuperAgentCLI()

        # 先禁用一个技能
        from orchestration.skill_checker import Skill
        cli.skill_checker.disable_skill(Skill.BRAINSTORMING)

        # 通过 CLI 启用
        cli.onecmd("skills enable brainstorming")

        captured = capsys.readouterr()
        assert "已启用技能" in captured.out
        assert "brainstorming" in captured.out

        # 验证确实启用了
        assert cli.skill_checker.is_skill_available(Skill.BRAINSTORMING)

    def test_skills_disable_command(self, capsys):
        """测试 skills disable 命令"""
        cli = SuperAgentCLI()

        from orchestration.skill_checker import Skill
        assert cli.skill_checker.is_skill_available(Skill.CODE_REVIEW)

        # 通过 CLI 禁用
        cli.onecmd("skills disable code_review")

        captured = capsys.readouterr()
        assert "已禁用技能" in captured.out
        assert "code_review" in captured.out

        # 验证确实禁用了
        assert cli.skill_checker.is_skill_available(Skill.CODE_REVIEW) is False

    def test_skills_check_command_passed(self, capsys):
        """测试 skills check 命令 - 通过场景"""
        cli = SuperAgentCLI()

        # 确保所有技能都启用
        cli.skill_checker.enable_all_skills()

        # 检查功能开发任务
        cli.onecmd("skills check feature_development")

        captured = capsys.readouterr()
        assert "技能检查通过" in captured.out

    def test_skills_check_command_failed(self, capsys):
        """测试 skills check 命令 - 失败场景"""
        cli = SuperAgentCLI()

        # 禁用所有技能
        cli.skill_checker.available_skills.clear()

        # 检查功能开发任务
        cli.onecmd("skills check feature_development")

        captured = capsys.readouterr()
        assert "缺少必要技能" in captured.out
        assert "需要的技能" in captured.out
        assert "brainstorming" in captured.out
        assert "test_driven_development" in captured.out

    def test_skills_history_command(self, capsys):
        """测试 skills history 命令"""
        cli = SuperAgentCLI()

        # 执行一些检查
        cli.skill_checker.check_task_skills("feature_development", auto_fail=False)
        cli.skill_checker.check_task_skills("bug_fixing", auto_fail=False)

        # 查看历史
        cli.onecmd("skills history")

        captured = capsys.readouterr()
        assert "技能检查历史" in captured.out
        assert "feature_development" in captured.out
        assert "bug_fixing" in captured.out

    def test_skills_p0_command(self, capsys):
        """测试 skills p0 命令"""
        cli = SuperAgentCLI()

        # 清空所有技能
        cli.skill_checker.available_skills.clear()

        # 启用 P0 技能
        cli.onecmd("skills p0")

        captured = capsys.readouterr()
        assert "P0 核心技能" in captured.out

        # 验证只启用了 P0 技能
        from orchestration.skill_checker import Skill
        assert cli.skill_checker.is_skill_available(Skill.TEST_DRIVEN_DEVELOPMENT)
        assert cli.skill_checker.is_skill_available(Skill.CODE_REVIEW)
        assert cli.skill_checker.is_skill_available(Skill.BRAINSTORMING) is False
        assert cli.skill_checker.is_skill_available(Skill.SYSTEMATIC_DEBUGGING) is False

    def test_skills_p1_command(self, capsys):
        """测试 skills p1 命令"""
        cli = SuperAgentCLI()

        # 清空所有技能
        cli.skill_checker.available_skills.clear()

        # 启用 P1 技能
        cli.onecmd("skills p1")

        captured = capsys.readouterr()
        assert "P1 增强技能" in captured.out

        # 验证只启用了 P1 技能
        from orchestration.skill_checker import Skill
        assert cli.skill_checker.is_skill_available(Skill.BRAINSTORMING)
        assert cli.skill_checker.is_skill_available(Skill.SYSTEMATIC_DEBUGGING)
        assert cli.skill_checker.is_skill_available(Skill.TEST_DRIVEN_DEVELOPMENT) is False
        assert cli.skill_checker.is_skill_available(Skill.CODE_REVIEW) is False

    def test_skills_all_command(self, capsys):
        """测试 skills all 命令"""
        cli = SuperAgentCLI()

        # 清空所有技能
        cli.skill_checker.available_skills.clear()

        # 启用所有技能
        cli.onecmd("skills all")

        captured = capsys.readouterr()
        assert "所有技能" in captured.out

        # 验证所有技能都启用了
        from orchestration.skill_checker import Skill
        for skill in Skill:
            assert cli.skill_checker.is_skill_available(skill)

    def test_skills_invalid_command(self, capsys):
        """测试无效的 skills 命令"""
        cli = SuperAgentCLI()

        cli.onecmd("skills invalid_command")

        captured = capsys.readouterr()
        assert "未知命令" in captured.out

    def test_skills_enable_missing_arg(self, capsys):
        """测试 skills enable 缺少参数"""
        cli = SuperAgentCLI()

        cli.onecmd("skills enable")

        captured = capsys.readouterr()
        assert "请指定要启用的技能" in captured.out

    def test_skills_check_missing_arg(self, capsys):
        """测试 skills check 缺少参数"""
        cli = SuperAgentCLI()

        cli.onecmd("skills check")

        captured = capsys.readouterr()
        assert "请指定任务类型" in captured.out

    def test_skills_invalid_skill_name(self, capsys):
        """测试无效的技能名称"""
        cli = SuperAgentCLI()

        cli.onecmd("skills enable invalid_skill")

        captured = capsys.readouterr()
        assert "未知技能" in captured.out


class TestSkillCheckerIntegrationWorkflow:
    """测试 SkillChecker 与 CLI 的集成工作流"""

    def test_complete_skill_checking_workflow(self, capsys):
        """测试完整的技能检查工作流"""
        cli = SuperAgentCLI()

        # 1. 查看初始状态
        cli.onecmd("skills status")
        captured = capsys.readouterr()
        assert "技能状态" in captured.out

        # 2. 禁用某个技能
        cli.onecmd("skills disable brainstorming")
        captured = capsys.readouterr()
        assert "已禁用技能" in captured.out

        # 3. 检查任务 - 应该失败
        cli.onecmd("skills check feature_development")
        captured = capsys.readouterr()
        assert "缺少必要技能" in captured.out

        # 4. 重新启用技能
        cli.onecmd("skills enable brainstorming")
        captured = capsys.readouterr()
        assert "已启用技能" in captured.out

        # 5. 再次检查 - 应该通过
        cli.onecmd("skills check feature_development")
        captured = capsys.readouterr()
        assert "技能检查通过" in captured.out

        # 6. 查看历史
        cli.onecmd("skills history")
        captured = capsys.readouterr()
        assert "feature_development" in captured.out

    def test_p0_p1_skill_workflow(self, capsys):
        """测试 P0/P1 技能切换工作流"""
        cli = SuperAgentCLI()

        # 清空所有技能
        cli.skill_checker.available_skills.clear()

        # 1. 启用 P0 技能
        cli.onecmd("skills p0")
        captured = capsys.readouterr()
        assert "P0 核心技能" in captured.out

        # 检查代码审查任务 (只需要 P0 技能)
        cli.onecmd("skills check code_review")
        captured = capsys.readouterr()
        assert "技能检查通过" in captured.out

        # 检查功能开发任务 (需要 P1 技能)
        cli.onecmd("skills check feature_development")
        captured = capsys.readouterr()
        assert "缺少必要技能" in captured.out

        # 2. 启用 P1 技能
        cli.onecmd("skills p1")
        captured = capsys.readouterr()
        assert "P1 增强技能" in captured.out

        # 再次检查功能开发任务
        cli.onecmd("skills check feature_development")
        captured = capsys.readouterr()
        assert "缺少必要技能" in captured.out  # 因为 P0 技能被覆盖了

        # 3. 启用所有技能
        cli.onecmd("skills all")
        captured = capsys.readouterr()
        assert "所有技能" in captured.out

        # 现在应该可以通过了
        cli.onecmd("skills check feature_development")
        captured = capsys.readouterr()
        assert "技能检查通过" in captured.out

    def test_refactoring_requires_all_skills(self, capsys):
        """测试重构任务需要所有技能"""
        cli = SuperAgentCLI()

        # 只启用 P0 技能
        cli.onecmd("skills p0")

        # 检查重构任务
        cli.onecmd("skills check refactoring")
        captured = capsys.readouterr()
        assert "缺少必要技能" in captured.out

        # 启用所有技能
        cli.onecmd("skills all")

        # 再次检查
        cli.onecmd("skills check refactoring")
        captured = capsys.readouterr()
        assert "技能检查通过" in captured.out
