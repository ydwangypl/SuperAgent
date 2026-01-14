"""
技能检查器 - P1 Task 2.3

确保在执行任务前具备必要的技能
通过任务类型到技能的映射,强制执行最佳实践
"""

from enum import Enum
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class Skill(Enum):
    """必需技能枚举"""
    BRAINSTORMING = "brainstorming"  # 脑暴设计能力
    TEST_DRIVEN_DEVELOPMENT = "test_driven_development"  # TDD 开发能力
    SYSTEMATIC_DEBUGGING = "systematic_debugging"  # 系统化调试能力
    CODE_REVIEW = "code_review"  # 代码审查能力


class SkillNotAvailableError(Exception):
    """技能不可用异常

    当任务需要的技能不可用时抛出此异常
    """
    def __init__(self, task_type: str, missing_skills: List[Skill]):
        self.task_type = task_type
        self.missing_skills = missing_skills
        skill_names = [s.value for s in missing_skills]
        super().__init__(
            f"任务 '{task_type}' 需要以下技能: {', '.join(skill_names)}, "
            f"但这些技能当前不可用。请确保已启用相应功能。"
        )


@dataclass
class SkillRequirement:
    """技能需求数据类"""
    task_type: str                          # 任务类型
    required_skills: Set[Skill]             # 需要的技能集合
    description: str                         # 任务描述
    guidance: str                            # 缺少技能时的指导


class SkillChecker:
    """技能检查器 - 确保任务执行前具备必要技能"""

    # 任务类型到技能的映射
    TASK_SKILL_MAPPING: Dict[str, Set[Skill]] = {
        # 复杂功能开发需要脑暴
        "feature_development": {Skill.BRAINSTORMING, Skill.TEST_DRIVEN_DEVELOPMENT},
        "api_development": {Skill.BRAINSTORMING, Skill.TEST_DRIVEN_DEVELOPMENT},
        "ui_development": {Skill.BRAINSTORMING, Skill.TEST_DRIVEN_DEVELOPMENT},

        # 代码修复需要调试技能
        "bug_fixing": {Skill.SYSTEMATIC_DEBUGGING, Skill.TEST_DRIVEN_DEVELOPMENT},
        "error_resolution": {Skill.SYSTEMATIC_DEBUGGING, Skill.TEST_DRIVEN_DEVELOPMENT},

        # 代码审查需要审查技能
        "code_review": {Skill.CODE_REVIEW},
        "pr_review": {Skill.CODE_REVIEW},

        # 重构需要全部技能
        "refactoring": {
            Skill.BRAINSTORMING,
            Skill.TEST_DRIVEN_DEVELOPMENT,
            Skill.SYSTEMATIC_DEBUGGING,
            Skill.CODE_REVIEW
        },

        # 架构设计需要脑暴和审查
        "architecture_design": {Skill.BRAINSTORMING, Skill.CODE_REVIEW},
    }

    def __init__(self):
        """初始化技能检查器"""
        self.available_skills: Set[Skill] = set()
        self.skill_history: List[Dict] = []

    def enable_skill(self, skill: Skill):
        """启用技能

        Args:
            skill: 要启用的技能
        """
        self.available_skills.add(skill)
        logger.info(f"技能已启用: {skill.value}")

    def disable_skill(self, skill: Skill):
        """禁用技能

        Args:
            skill: 要禁用的技能
        """
        self.available_skills.discard(skill)
        logger.info(f"技能已禁用: {skill.value}")

    def is_skill_available(self, skill: Skill) -> bool:
        """检查技能是否可用

        Args:
            skill: 要检查的技能

        Returns:
            bool: 如果技能可用返回 True
        """
        return skill in self.available_skills

    def check_task_skills(
        self,
        task_type: str,
        auto_fail: bool = True
    ) -> bool:
        """检查任务需要的技能是否都可用

        Args:
            task_type: 任务类型
            auto_fail: 如果技能缺失是否自动抛出异常

        Returns:
            bool: 如果所有需要的技能都可用返回 True

        Raises:
            SkillNotAvailableError: 当 auto_fail=True 且技能不可用时
        """
        # 获取任务需要的技能
        required_skills = self.TASK_SKILL_MAPPING.get(task_type, set())

        # 如果没有特定的技能要求,默认通过
        if not required_skills:
            logger.debug(f"任务 '{task_type}' 没有特定的技能要求")
            return True

        # 检查每个需要的技能
        missing_skills = [
            skill for skill in required_skills
            if skill not in self.available_skills
        ]

        # 记录检查历史
        self.skill_history.append({
            "task_type": task_type,
            "required_skills": [s.value for s in required_skills],
            "available_skills": [s.value for s in self.available_skills],
            "missing_skills": [s.value for s in missing_skills],
            "passed": len(missing_skills) == 0,
            "timestamp": self._get_timestamp()
        })

        # 如果有缺失技能
        if missing_skills:
            logger.warning(
                f"任务 '{task_type}' 缺少技能: "
                f"{', '.join([s.value for s in missing_skills])}"
            )

            if auto_fail:
                raise SkillNotAvailableError(task_type, missing_skills)

            return False

        logger.info(f"任务 '{task_type}' 所需技能检查通过")
        return True

    def get_required_skills(self, task_type: str) -> Set[Skill]:
        """获取任务需要的技能

        Args:
            task_type: 任务类型

        Returns:
            Set[Skill]: 需要的技能集合
        """
        return self.TASK_SKILL_MAPPING.get(task_type, set()).copy()

    def get_skill_requirement(self, task_type: str) -> Optional[SkillRequirement]:
        """获取技能需求的详细信息

        Args:
            task_type: 任务类型

        Returns:
            Optional[SkillRequirement]: 技能需求对象,如果任务不需要特殊技能返回 None
        """
        required_skills = self.get_required_skills(task_type)

        if not required_skills:
            return None

        # 生成指导信息
        missing_guidance = []
        for skill in required_skills:
            if skill == Skill.BRAINSTORMING:
                missing_guidance.append(
                    "启用脑暴功能: 在配置中设置 brainstorming_enabled=True"
                )
            elif skill == Skill.TEST_DRIVEN_DEVELOPMENT:
                missing_guidance.append(
                    "启用 TDD 验证: 在 CodingAgent 中设置 enable_tdd_validation=True"
                )
            elif skill == Skill.SYSTEMATIC_DEBUGGING:
                missing_guidance.append(
                    "启用调试功能: 确保 SystematicDebugger 已集成到 CodingAgent"
                )
            elif skill == Skill.CODE_REVIEW:
                missing_guidance.append(
                    "启用代码审查: 确保 IssueClassifier 已集成到 ReviewOrchestrator"
                )

        return SkillRequirement(
            task_type=task_type,
            required_skills=required_skills,
            description=f"任务 '{task_type}' 需要 {len(required_skills)} 个技能",
            guidance="\n".join(missing_guidance)
        )

    def get_available_skills(self) -> Set[Skill]:
        """获取当前可用的技能

        Returns:
            Set[Skill]: 可用技能集合
        """
        return self.available_skills.copy()

    def get_skill_history(self) -> List[Dict]:
        """获取技能检查历史

        Returns:
            List[Dict]: 历史记录列表
        """
        return self.skill_history.copy()

    def reset(self):
        """重置技能检查器"""
        self.available_skills.clear()
        self.skill_history.clear()
        logger.info("技能检查器已重置")

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()

    # ========== 便捷方法 ==========

    def enable_all_skills(self):
        """启用所有技能 (用于开发/测试)"""
        for skill in Skill:
            self.enable_skill(skill)
        logger.info("所有技能已启用")

    def enable_p0_skills(self):
        """启用 P0 核心技能"""
        self.available_skills.clear()
        self.enable_skill(Skill.TEST_DRIVEN_DEVELOPMENT)
        self.enable_skill(Skill.CODE_REVIEW)
        logger.info("P0 核心技能已启用 (TDD, Code Review)")

    def enable_p1_skills(self):
        """启用 P1 增强技能"""
        self.available_skills.clear()
        self.enable_skill(Skill.BRAINSTORMING)
        self.enable_skill(Skill.SYSTEMATIC_DEBUGGING)
        logger.info("P1 增强技能已启用 (Brainstorming, Debugging)")

    def get_skill_status(self) -> Dict[str, bool]:
        """获取所有技能的状态

        Returns:
            Dict[str, bool]: 技能名称到可用状态的映射
        """
        return {
            skill.value: self.is_skill_available(skill)
            for skill in Skill
        }

    def print_skill_status(self):
        """打印技能状态 (便于调试)"""
        status = self.get_skill_status()
        print("\n=== 技能状态 ===")
        for skill_name, available in status.items():
            status_str = "✅ 可用" if available else "❌ 不可用"
            print(f"  {skill_name}: {status_str}")
        print()
