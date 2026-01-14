"""
设计规格验证器 - P1 Task 2.1

验证设计规格的完整性和质量
"""

from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class DesignValidator:
    """设计规格验证器"""

    # 最小要求
    MIN_ALTERNATIVES = 2
    MIN_ACCEPTANCE_CRITERIA = 3
    MIN_PROS_PER_OPTION = 1
    MIN_CONS_PER_OPTION = 1

    def __init__(self, strict_mode: bool = False):
        """初始化验证器

        Args:
            strict_mode: 严格模式,启用更严格的验证规则
        """
        self.strict_mode = strict_mode

    def validate_design_spec(self, design_spec) -> Tuple[bool, List[str]]:
        """验证设计规格完整性

        Args:
            design_spec: DesignSpec 对象

        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误列表)
        """
        errors = []
        warnings = []

        # 1. 检查需求
        if not design_spec.requirements:
            errors.append("缺少需求描述")
        elif len(design_spec.requirements) < 3:
            warnings.append("需求描述较少,建议补充更多细节")

        # 2. 检查方案选项
        if not design_spec.considered_alternatives:
            errors.append("缺少方案选项")
        elif len(design_spec.considered_alternatives) < self.MIN_ALTERNATIVES:
            errors.append(
                f"至少需要考虑 {self.MIN_ALTERNATIVES} 个方案, "
                f"当前只有 {len(design_spec.considered_alternatives)} 个"
            )

        # 3. 检查每个选项的优缺点
        for i, option in enumerate(design_spec.considered_alternatives):
            if not option.pros or len(option.pros) < self.MIN_PROS_PER_OPTION:
                errors.append(
                    f"选项 {i+1} ({option.title}) 至少需要 {self.MIN_PROS_PER_OPTION} 个优点"
                )

            if not option.cons or len(option.cons) < self.MIN_CONS_PER_OPTION:
                errors.append(
                    f"选项 {i+1} ({option.title}) 至少需要 {self.MIN_CONS_PER_OPTION} 个缺点"
                )

            # 严格模式: 检查优缺点数量平衡
            if self.strict_mode and len(option.pros) < 2:
                warnings.append(f"选项 {i+1} 优点较少,建议补充")

            if self.strict_mode and len(option.cons) < 2:
                warnings.append(f"选项 {i+1} 缺点分析不足,建议补充")

        # 4. 检查选择理由
        if not design_spec.rationale or len(design_spec.rationale) < 50:
            errors.append("缺少充分的选择理由 (至少 50 字)")

        # 5. 检查验收标准
        if not design_spec.acceptance_criteria:
            errors.append("缺少验收标准")
        elif len(design_spec.acceptance_criteria) < self.MIN_ACCEPTANCE_CRITERIA:
            errors.append(
                f"至少需要 {self.MIN_ACCEPTANCE_CRITERIA} 条验收标准, "
                f"当前只有 {len(design_spec.acceptance_criteria)} 条"
            )

        # 6. 检查架构说明
        if not design_spec.architecture_notes or len(design_spec.architecture_notes) < 100:
            warnings.append("架构说明较为简短,建议补充技术细节")

        # 7. 检查时间戳
        if not design_spec.created_at:
            warnings.append("缺少创建时间戳")

        # 记录验证结果
        is_valid = len(errors) == 0

        if is_valid:
            logger.info("设计规格验证通过")
            if warnings:
                logger.warning(f"验证通过但有 {len(warnings)} 个警告")
        else:
            logger.error(f"设计规格验证失败: {len(errors)} 个错误")

        return is_valid, errors + [f"警告: {w}" for w in warnings]

    def validate_option_quality(self, option) -> Tuple[bool, List[str]]:
        """验证单个设计选项的质量

        Args:
            option: DesignOption 对象

        Returns:
            Tuple[bool, List[str]]: (是否有效, 问题列表)
        """
        issues = []

        # 检查必要字段
        if not option.option_id:
            issues.append("缺少选项 ID")

        if not option.title or len(option.title) < 5:
            issues.append("标题太短或缺失")

        if not option.description or len(option.description) < 20:
            issues.append("描述太简短 (至少 20 字)")

        # 检查优缺点
        if not option.pros:
            issues.append("缺少优点列表")
        elif len(option.pros) < 2:
            issues.append("优点少于 2 条")

        if not option.cons:
            issues.append("缺少缺点列表")
        elif len(option.cons) < 2:
            issues.append("缺点少于 2 条")

        # 检查复杂度等级
        valid_complexity = ["low", "medium", "high"]
        if option.implementation_complexity not in valid_complexity:
            issues.append(
                f"无效的复杂度等级: {option.implementation_complexity}, "
                f"应为 {', '.join(valid_complexity)}"
            )

        # 检查风险等级
        valid_risk = ["low", "medium", "high"]
        if option.risk_level not in valid_risk:
            issues.append(
                f"无效的风险等级: {option.risk_level}, "
                f"应为 {', '.join(valid_risk)}"
            )

        # 检查时间估算
        if not option.estimated_time:
            issues.append("缺少时间估算")

        is_valid = len(issues) == 0
        return is_valid, issues

    def get_validation_score(self, design_spec) -> Dict[str, any]:
        """获取验证评分

        Args:
            design_spec: DesignSpec 对象

        Returns:
            Dict: 包含各项指标的评分
        """
        is_valid, errors = self.validate_design_spec(design_spec)

        # 计算各项指标得分
        scores = {
            "requirements_score": self._score_requirements(design_spec),
            "options_score": self._score_options(design_spec),
            "rationale_score": self._score_rationale(design_spec),
            "criteria_score": self._score_criteria(design_spec),
            "overall_valid": is_valid,
            "error_count": len([e for e in errors if not e.startswith("警告:")]),
            "warning_count": len([e for e in errors if e.startswith("警告:")])
        }

        # 计算总分 (0-100)
        total_score = (
            scores["requirements_score"] * 0.2 +
            scores["options_score"] * 0.3 +
            scores["rationale_score"] * 0.2 +
            scores["criteria_score"] * 0.3
        )

        scores["total_score"] = int(total_score)

        return scores

    def _score_requirements(self, design_spec) -> float:
        """为需求打分 (0-100)"""
        if not design_spec.requirements:
            return 0.0

        req_count = len(design_spec.requirements)
        # 3-5 个需求为理想数量
        if req_count >= 5:
            return 100.0
        elif req_count >= 3:
            return 80.0
        else:
            return max(0.0, req_count * 20.0)

    def _score_options(self, design_spec) -> float:
        """为选项质量打分 (0-100)"""
        if not design_spec.considered_alternatives:
            return 0.0

        option_count = len(design_spec.considered_alternatives)

        # 基础分: 选项数量
        if option_count >= 3:
            base_score = 100.0
        elif option_count >= 2:
            base_score = 70.0
        else:
            base_score = 0.0

        # 扣分: 选项质量不高
        deduction = 0.0
        for option in design_spec.considered_alternatives:
            if not option.pros or len(option.pros) < 2:
                deduction += 10.0
            if not option.cons or len(option.cons) < 2:
                deduction += 10.0

        return max(0.0, base_score - deduction)

    def _score_rationale(self, design_spec) -> float:
        """为选择理由打分 (0-100)"""
        if not design_spec.rationale:
            return 0.0

        rationale_length = len(design_spec.rationale)

        # 理由长度评分
        if rationale_length >= 200:
            return 100.0
        elif rationale_length >= 100:
            return 80.0
        elif rationale_length >= 50:
            return 60.0
        else:
            return rationale_length  # 50 字以下每字 1 分

    def _score_criteria(self, design_spec) -> float:
        """为验收标准打分 (0-100)"""
        if not design_spec.acceptance_criteria:
            return 0.0

        criteria_count = len(design_spec.acceptance_criteria)

        # 5+ 条为理想
        if criteria_count >= 5:
            return 100.0
        elif criteria_count >= 3:
            return 80.0
        else:
            return criteria_count * 20.0
