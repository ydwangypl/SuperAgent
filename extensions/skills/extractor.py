"""技能提取器 (SkillExtractor)

实现 Claudeception 风格的质量门禁系统：
1. 触发条件检测 (错误模式/变通方案/验证方案)
2. 特征提取
3. 质量门禁评分 (4维度 ≥ 阈值)
4. 技能分类 + 优化
5. 安全验证 (🆕 Gemini #2)
"""

import hashlib
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging

from .models import SkillCard, SkillCategory, SkillType, SkillQualityScores

logger = logging.getLogger(__name__)


class QualityGateResult:
    """质量门禁检测结果"""

    def __init__(
        self,
        passed: bool,
        reason: str = "",
        scores: Optional[SkillQualityScores] = None,
        category: Optional[str] = None,
        skill_type: Optional[str] = None
    ):
        self.passed = passed
        self.reason = reason
        self.scores = scores
        self.category = category
        self.skill_type = skill_type


class SkillExtractor:
    """技能提取器 - 质量门禁核心实现

    遵循 Claudeception 质量门禁规则：
    - 平均分 ≥ 6.0
    - 重用性 ≥ 7.0
    - 通用性 ≥ 6.0
    - 清晰度 ≥ 6.0
    """

    # 质量门禁阈值 (Claudeception 推荐值)
    MIN_AVG_SCORE = 6.0
    MIN_REUSE_SCORE = 7.0
    MIN_GENERALITY = 6.0
    MIN_CLARITY = 6.0

    # 触发条件关键词
    TRIGGER_CONDITIONS = {
        "error_resolution": [
            r"error", r"exception", r"failed", r"timeout",
            r"assertion", r"permission", r"not found", r"invalid"
        ],
        "workaround": [
            r"workaround", r"alternative", r"instead of",
            r"hack", r"bypass", r"fallback"
        ],
        "verified_solution": [
            r"verified", r"confirmed", r"tested", r"working solution",
            r"correct approach", r"best practice"
        ]
    }

    def __init__(self):
        self.category_keywords = self._build_category_keywords()
        # 🆕 集成安全验证器
        from .validator import SkillValidator
        self.validator = SkillValidator()

    async def evaluate(
        self,
        task: Dict[str, Any],
        result: Any,
        context: Dict[str, Any]
    ) -> QualityGateResult:
        """评估是否应该提取技能

        Args:
            task: 任务信息
            result: 任务执行结果
            context: 执行上下文

        Returns:
            QualityGateResult: 质量门禁结果
        """
        # 1. 触发条件检测
        trigger_info = self._check_trigger_conditions(result, context)
        if not trigger_info["triggered"]:
            return QualityGateResult(
                passed=False,
                reason=trigger_info["reason"]
            )

        # 2. 特征提取
        features = self._extract_features(task, result, context)

        # 3. 质量评分
        scores = self._calculate_scores(features)

        # 4. 质量门禁检查
        if not self._passes_quality_gate(scores):
            return QualityGateResult(
                passed=False,
                reason=f"质量评分未达标: avg={scores.average:.1f}, "
                       f"reuse={scores.reusability}, "
                       f"gen={scores.generality}, "
                       f"clarity={scores.clarity}",
                scores=scores
            )

        # 5. 技能分类
        category, skill_type = self._classify_skill(features, trigger_info)

        # 🆕 6. 安全检查（如果有代码）
        code_safe = True
        security_warnings = []
        if features.get("has_code"):
            _, code_safe, security_warnings = self.validator.validate_skill(
                str(result)[:1000]  # 检查前 1000 字符
            )
            if not code_safe:
                return QualityGateResult(
                    passed=False,
                    reason=f"安全检查失败: {', '.join(security_warnings)}",
                    scores=scores
                )

        return QualityGateResult(
            passed=True,
            reason="通过质量门禁",
            scores=scores,
            category=category,
            skill_type=skill_type
        )

    def _check_trigger_conditions(
        self,
        result: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """检查是否满足触发条件"""
        result_str = str(result).lower()
        context_str = str(context).lower()

        combined = f"{result_str} {context_str}"

        # 检测错误模式
        for keyword in self.TRIGGER_CONDITIONS["error_resolution"]:
            if re.search(keyword, combined):
                return {
                    "triggered": True,
                    "type": "error_resolution",
                    "reason": f"检测到错误关键词: {keyword}"
                }

        # 检测变通方案
        for keyword in self.TRIGGER_CONDITIONS["workaround"]:
            if re.search(keyword, combined):
                return {
                    "triggered": True,
                    "type": "workaround",
                    "reason": f"检测到变通方案关键词: {keyword}"
                }

        # 检测验证解决方案
        for keyword in self.TRIGGER_CONDITIONS["verified_solution"]:
            if re.search(keyword, combined):
                return {
                    "triggered": True,
                    "type": "verified_solution",
                    "reason": f"检测到验证解决方案关键词: {keyword}"
                }

        return {
            "triggered": False,
            "type": None,
            "reason": "未满足任何触发条件"
        }

    def _extract_features(
        self,
        task: Dict[str, Any],
        result: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取任务特征"""
        return {
            "task_type": task.get("type", "unknown"),
            "task_description": task.get("description", ""),
            "result_success": getattr(result, "success", False) if hasattr(result, 'success') else True,
            "result_output": str(result),
            "context_keys": list(context.keys()),
            "has_code": self._contains_code(result),
            "has_solution": self._has_solution_pattern(result),
        }

    def _contains_code(self, result: Any) -> bool:
        """检测结果是否包含代码"""
        result_str = str(result)
        code_indicators = ['def ', 'class ', 'import ', 'from ', '```']
        return any(indicator in result_str for indicator in code_indicators)

    def _has_solution_pattern(self, result: Any) -> bool:
        """检测解决方案模式"""
        result_str = str(result).lower()
        solution_patterns = [
            r"solution", r"fix", r"resolve", r"implement",
            r"step", r"how to", r"use", r"完成", r"实现", r"函数"
        ]
        return any(re.search(p, result_str) for p in solution_patterns)

    def _calculate_scores(self, features: Dict[str, Any]) -> SkillQualityScores:
        """计算质量评分"""
        # 基于特征的智能评分
        base = 5

        # 可复用性评分
        reusability = base
        if features.get("has_code"):
            reusability += 2
        if features.get("has_solution"):
            reusability += 1
        if features["task_type"] != "unknown":
            reusability += 1
        reusability = min(10, reusability)

        # 通用性评分
        generality = base
        if features["task_type"] in ["coding", "refactoring"]:
            generality += 2
        if len(features.get("context_keys", [])) > 2:
            generality += 1
        generality = min(10, generality)

        # 清晰度评分
        clarity = base + 1  # 基础分
        if features.get("result_output"):
            output_len = len(features["result_output"])
            if 50 < output_len < 1000:  # 适中的输出长度
                clarity += 2
        clarity = min(10, clarity)

        # 独特性评分
        uniqueness = base
        if features.get("has_code") and features.get("has_solution"):
            uniqueness += 2
        uniqueness = min(10, uniqueness)

        return SkillQualityScores(
            reusability=reusability,
            generality=generality,
            clarity=clarity,
            uniqueness=uniqueness
        )

    def _passes_quality_gate(self, scores: SkillQualityScores) -> bool:
        """检查是否通过质量门禁"""
        if scores.average < self.MIN_AVG_SCORE:
            return False
        if scores.reusability < self.MIN_REUSE_SCORE:
            return False
        if scores.generality < self.MIN_GENERALITY:
            return False
        if scores.clarity < self.MIN_CLARITY:
            return False
        return True

    def _classify_skill(
        self,
        features: Dict[str, Any],
        trigger_info: Dict[str, Any]
    ) -> Tuple[str, str]:
        """分类技能"""
        trigger_type = trigger_info.get("type", "solution")

        # 映射触发类型到分类
        category_map = {
            "error_resolution": SkillCategory.ERROR_RESOLUTION.value,
            "workaround": SkillCategory.WORKAROUND.value,
            "verified_solution": SkillCategory.BEST_PRACTICE.value,
        }

        category = category_map.get(
            trigger_type,
            SkillCategory.PATTERN.value
        )

        # 确定技能类型
        if features.get("has_code"):
            skill_type = SkillType.PATTERN.value
        else:
            skill_type = SkillType.SOLUTION.value

        return category, skill_type

    def _build_category_keywords(self) -> Dict[str, List[str]]:
        """构建分类关键词"""
        return {
            "error_resolution": ["error", "fix", "bug", "issue"],
            "workaround": ["workaround", "alternative", "instead"],
            "best_practice": ["best practice", "recommended", "standard"],
        }

    def generate_skill_id(self, task: Dict[str, Any]) -> str:
        """生成唯一技能 ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content = f"{timestamp}_{task.get('description', 'unknown')}"
        hash_suffix = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"skill_{timestamp}_{hash_suffix}"
