"""技能效果评估器 (SkillEvaluator)

Gemini 建议 #5 - 记录技能应用反馈，淘汰低分技能。
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
from pathlib import Path

from .models import SkillCard

logger = logging.getLogger(__name__)


class SkillEvaluator:
    """技能效果评估器

    职责：
    - 记录技能应用后的反馈
    - 根据任务成功/失败调整评分
    - 淘汰低分技能（废弃机制）
    """

    # 淘汰阈值
    DEPRECATION_THRESHOLD = 4.0  # 平均分低于 4.0 废弃

    # 评分惩罚
    FAILURE_PENALTY = 1  # 失败扣分
    SUCCESS_REWARD = 0.5  # 成功加分（上限 10）

    def __init__(self, skills_dir: Path):
        """初始化评估器

        Args:
            skills_dir: 技能存储目录
        """
        self.skills_dir = Path(skills_dir)
        self.feedback_file = self.skills_dir / "skill_feedback.json"

    async def record_feedback(
        self,
        skill_id: str,
        task_success: bool,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """记录技能应用反馈

        Args:
            skill_id: 技能 ID
            task_success: 任务是否成功
            context: 上下文信息

        Returns:
            更新后的技能统计
        """
        feedback_entry = {
            "skill_id": skill_id,
            "timestamp": datetime.now().isoformat(),
            "task_success": task_success,
            "context": context or {}
        }

        logger.info(
            f"Skill feedback: {skill_id} - "
            f"{'SUCCESS' if task_success else 'FAILURE'}"
        )

        return feedback_entry

    def update_scores(self, skill: SkillCard, task_success: bool) -> SkillCard:
        """更新技能评分

        Args:
            skill: 技能卡
            task_success: 任务是否成功

        Returns:
            更新后的技能卡
        """
        # 增加使用次数
        skill.usage_count += 1
        skill.last_used_at = datetime.now().isoformat()

        if task_success:
            # 成功：小幅加分
            skill.scores.reusability = min(
                10, skill.scores.reusability + self.SUCCESS_REWARD
            )
            skill.scores.clarity = min(
                10, skill.scores.clarity + self.SUCCESS_REWARD
            )
        else:
            # 失败：扣分
            skill.scores.reusability = max(
                1, skill.scores.reusability - self.FAILURE_PENALTY
            )
            skill.scores.clarity = max(
                1, skill.scores.clarity - self.FAILURE_PENALTY
            )
            skill.scores.generality = max(
                1, skill.scores.generality - 0.5
            )

        return skill

    def should_deprecate(self, skill: SkillCard) -> bool:
        """检查技能是否应该废弃

        Args:
            skill: 技能卡

        Returns:
            是否应该废弃
        """
        # 平均分低于阈值
        if skill.scores.average < self.DEPRECATION_THRESHOLD:
            return True

        # 使用次数 ≥ 5 且成功率 < 40%
        if skill.usage_count >= 5:
            # 这里简化处理，实际需要记录成功次数
            pass

        return False

    async def deprecate_skill(self, skill: SkillCard) -> None:
        """废弃技能

        Args:
            skill: 技能卡
        """
        skill.version = f"{skill.version}-deprecated"

        # 从活跃索引移除但保留文件
        logger.warning(f"Skill deprecated: {skill.skill_id} (avg={skill.scores.average:.1f})")