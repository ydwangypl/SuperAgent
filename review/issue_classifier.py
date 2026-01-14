"""
Issue Classifier - 问题分级器

自动将代码审查问题按照严重程度分级

规则:
1. P0 (Critical): 阻塞进度,必须立即修复
   - 安全漏洞、崩溃、数据丢失
   - 测试全部失败
   - 核心功能无法使用

2. P1 (Important): 应该在下个任务前修复
   - 性能问题、逻辑错误
   - 部分测试失败
   - 重要功能缺陷

3. P2 (Minor): 可以延后处理
   - 代码风格、最佳实践
   - 文档问题
   - 非关键优化

4. P3 (Trivial): 琐碎问题
   - 格式问题
   - 注释建议
   - 可选优化

作者: SuperAgent Team
版本: v3.2.0
日期: 2026-01-13
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from review.models import CodeIssue, IssueCategory, ReviewSeverity
import logging

logger = logging.getLogger(__name__)


class PriorityLevel(Enum):
    """优先级等级 (P0-P3)"""
    P0_CRITICAL = "P0"    # 阻塞进度,必须立即修复
    P1_IMPORTANT = "P1"   # 应该在下个任务前修复
    P2_MINOR = "P2"       # 可以延后处理
    P3_TRIVIAL = "P3"     # 琐碎问题


@dataclass
class ClassificationResult:
    """分类结果"""
    priority: PriorityLevel          # 优先级
    reason: str                      # 分类原因
    suggested_action: str            # 建议行动
    requires_immediate_fix: bool     # 是否需要立即修复
    should_block_next_task: bool     # 是否应该阻塞下一个任务


class IssueClassifier:
    """
    问题分级器

    根据问题内容自动分类严重程度
    """

    # P0 关键词 - 阻塞级别
    P0_KEYWORDS = [
        # 安全相关
        "security", "vulnerability", "sql injection", "xss",
        "authentication bypass", "injection", "breach", "leak",
        "exploit", "hack", "attack", "compromise",

        # 崩溃相关
        "crash", "segfault", "panic", "fatal", "abort",
        "data loss", "data corruption", "memory corruption",

        # 功能完全失效
        "completely broken", "doesn't work at all", "total failure",
        "unusable", "non-functional", "cannot start",

        # 测试全部失败
        "all tests fail", "100% tests failing", "zero tests passing"
    ]

    # P1 关键词 - 重要级别
    P1_KEYWORDS = [
        # 性能问题
        "slow", "timeout", "performance", "latency",
        "memory leak", "high memory", "cpu spike",

        # 逻辑错误
        "logic error", "incorrect", "wrong", "bug",
        "unexpected behavior", "not working as expected",

        # 测试失败
        "test fails", "tests failing", "test broken",

        # 并发问题
        "race condition", "deadlock", "concurrency issue",
        "thread safety", "synchronization",

        # 重要功能缺陷
        "broken feature", "missing functionality", "regression"
    ]

    # P2 关键词 - 次要级别
    P2_KEYWORDS = [
        # 代码质量
        "code smell", "code quality", "maintainability",
        "complex", "complicated", "hard to understand",

        # 最佳实践
        "best practice", "anti-pattern", "design pattern",
        "refactor", "improvement", "optimization",

        # 文档
        "documentation", "comment", "docstring",
        "missing docs", "poor documentation",

        # 测试覆盖
        "test coverage", "missing test", "not tested"
    ]

    # P3 关键词 - 琐碎级别
    P3_KEYWORDS = [
        # 格式问题
        "format", "indentation", "whitespace",
        "line length", "style", "formatting",

        # 命名
        "naming", "rename", "convention",

        # 注释
        "comment style", "comment format",

        # 可选优化
        "optional", "nice to have", "suggestion",
        "cosmetic", "minor issue"
    ]

    # 问题分类到优先级的映射
    CATEGORY_PRIORITY_MAP = {
        IssueCategory.SECURITY: PriorityLevel.P0_CRITICAL,
        IssueCategory.ERROR_HANDLING: PriorityLevel.P1_IMPORTANT,
        IssueCategory.PERFORMANCE: PriorityLevel.P1_IMPORTANT,
        IssueCategory.TESTING: PriorityLevel.P1_IMPORTANT,
        IssueCategory.ARCHITECTURE: PriorityLevel.P1_IMPORTANT,
        IssueCategory.BEST_PRACTICES: PriorityLevel.P2_MINOR,
        IssueCategory.CODE_STYLE: PriorityLevel.P3_TRIVIAL,
        IssueCategory.DOCUMENTATION: PriorityLevel.P3_TRIVIAL,
    }

    def __init__(self, strict_mode: bool = False):
        """
        初始化问题分级器

        Args:
            strict_mode: 严格模式,如果为 True 则倾向于升级优先级
        """
        self.strict_mode = strict_mode
        self.classification_history: List[Dict] = []

    def classify_issue(self, issue: CodeIssue) -> ClassificationResult:
        """
        分类单个问题

        Args:
            issue: 代码问题

        Returns:
            ClassificationResult: 分类结果
        """
        # 1. 首先检查明确的严重程度标记 (BLOCKER/CRITICAL 立即返回)
        if issue.severity == ReviewSeverity.BLOCKER:
            return self._create_result(
                PriorityLevel.P0_CRITICAL,
                "问题标记为 BLOCKER",
                "立即修复此问题,否则无法继续",
                requires_immediate_fix=True,
                should_block_next_task=True
            )

        if issue.severity == ReviewSeverity.CRITICAL:
            return self._create_result(
                PriorityLevel.P0_CRITICAL,
                "问题标记为 CRITICAL",
                "立即修复此问题",
                requires_immediate_fix=True,
                should_block_next_task=True
            )

        # 2. 对于其他严重程度,结合内容分析
        # MAJOR, MINOR, INFO 都需要进一步检查
        # 使用基于内容的分类,它会综合考虑 category 和关键词
        return self._classify_by_content(issue)

    def classify_by_description(self, description: str, category: IssueCategory) -> ClassificationResult:
        """
        基于描述和分类快速分类

        Args:
            description: 问题描述
            category: 问题分类

        Returns:
            ClassificationResult: 分类结果
        """
        # 创建临时问题对象
        issue = CodeIssue(
            issue_id="temp",
            category=category,
            severity=ReviewSeverity.INFO,  # 默认,会被重新分类
            title="",
            description=description
        )

        return self.classify_issue(issue)

    def batch_classify(self, issues: List[CodeIssue]) -> Dict[PriorityLevel, List[CodeIssue]]:
        """
        批量分类问题

        Args:
            issues: 问题列表

        Returns:
            Dict: 按优先级分组的问题列表
        """
        grouped = {
            PriorityLevel.P0_CRITICAL: [],
            PriorityLevel.P1_IMPORTANT: [],
            PriorityLevel.P2_MINOR: [],
            PriorityLevel.P3_TRIVIAL: []
        }

        for issue in issues:
            result = self.classify_issue(issue)
            grouped[result.priority].append(issue)

            # 记录分类历史
            self.classification_history.append({
                "issue_id": issue.issue_id,
                "priority": result.priority.value,
                "reason": result.reason
            })

        return grouped

    def get_summary(self, issues: List[CodeIssue]) -> Dict[str, any]:
        """
        获取分类统计摘要

        Args:
            issues: 问题列表

        Returns:
            Dict: 统计摘要
        """
        grouped = self.batch_classify(issues)

        total = len(issues)
        p0_count = len(grouped[PriorityLevel.P0_CRITICAL])
        p1_count = len(grouped[PriorityLevel.P1_IMPORTANT])
        p2_count = len(grouped[PriorityLevel.P2_MINOR])
        p3_count = len(grouped[PriorityLevel.P3_TRIVIAL])

        return {
            "total_issues": total,
            "p0_critical": p0_count,
            "p1_important": p1_count,
            "p2_minor": p2_count,
            "p3_trivial": p3_count,
            "has_blocking_issues": p0_count > 0,
            "requires_attention": p0_count + p1_count > 0,
            "can_proceed": p0_count == 0
        }

    def should_block_progress(self, issues: List[CodeIssue]) -> bool:
        """
        检查是否应该阻塞进度

        Args:
            issues: 问题列表

        Returns:
            bool: 如果有 P0 问题返回 True
        """
        grouped = self.batch_classify(issues)
        return len(grouped[PriorityLevel.P0_CRITICAL]) > 0

    def _classify_by_content(self, issue: CodeIssue) -> ClassificationResult:
        """基于问题内容进行分类"""
        description_lower = issue.description.lower()
        title_lower = issue.title.lower()
        combined = f"{title_lower} {description_lower}"

        # 0. 首先检查明确的严重程度标记 (MAJOR/MINOR)
        if issue.severity == ReviewSeverity.MAJOR:
            # MAJOR 直接映射到 P1,但可以基于内容升级
            # 检查是否有 P0 关键词,如果有则升级
            if any(keyword in combined for keyword in self.P0_KEYWORDS):
                return self._create_result(
                    PriorityLevel.P0_CRITICAL,
                    "MAJOR + 检测到阻塞性关键词",
                    "立即修复此问题",
                    requires_immediate_fix=True,
                    should_block_next_task=True
                )
            return self._create_result(
                PriorityLevel.P1_IMPORTANT,
                "问题标记为 MAJOR",
                "在下个任务前修复此问题",
                requires_immediate_fix=False,
                should_block_next_task=True
            )

        if issue.severity == ReviewSeverity.MINOR:
            # MINOR 直接映射到 P2
            return self._create_result(
                PriorityLevel.P2_MINOR,
                "问题标记为 MINOR",
                "可以延后处理,但应在迭代结束前修复",
                requires_immediate_fix=False,
                should_block_next_task=False
            )

        # 1. 基于关键词分类 (优先于分类映射)
        # P0 检查
        if any(keyword in combined for keyword in self.P0_KEYWORDS):
            priority = PriorityLevel.P0_CRITICAL
            if self.strict_mode:
                # 严格模式下,所有问题至少是 P1
                pass
            return self._create_result(
                priority,
                "检测到阻塞性关键词",
                "立即修复此问题,否则无法继续",
                requires_immediate_fix=True,
                should_block_next_task=True
            )

        # P1 检查
        if any(keyword in combined for keyword in self.P1_KEYWORDS):
            priority = PriorityLevel.P1_IMPORTANT
            if self.strict_mode:
                priority = PriorityLevel.P0_CRITICAL  # 严格模式下升级
            return self._create_result(
                priority,
                "检测到重要问题关键词",
                "在下个任务前修复此问题",
                requires_immediate_fix=(priority == PriorityLevel.P0_CRITICAL),
                should_block_next_task=True
            )

        # P2 检查
        if any(keyword in combined for keyword in self.P2_KEYWORDS):
            priority = PriorityLevel.P2_MINOR
            return self._create_result(
                priority,
                "检测到代码质量/最佳实践问题",
                "可以延后处理,但应在迭代结束前修复",
                requires_immediate_fix=False,
                should_block_next_task=False
            )

        # P3 检查
        if any(keyword in combined for keyword in self.P3_KEYWORDS):
            priority = PriorityLevel.P3_TRIVIAL
            return self._create_result(
                priority,
                "检测到格式/风格问题",
                "建议性改进,不强制要求",
                requires_immediate_fix=False,
                should_block_next_task=False
            )

        # 2. 检查问题分类映射 (作为后备方案)
        default_priority = self.CATEGORY_PRIORITY_MAP.get(issue.category, None)
        if default_priority:
            return self._create_result(
                default_priority,
                f"问题分类为 {issue.category.value}",
                self._get_action_for_priority(default_priority),
                requires_immediate_fix=(default_priority == PriorityLevel.P0_CRITICAL),
                should_block_next_task=(default_priority in [PriorityLevel.P0_CRITICAL, PriorityLevel.P1_IMPORTANT])
            )

        # 默认为 P2
        return self._create_result(
            PriorityLevel.P2_MINOR,
            "默认分类",
            "需要人工审查确认优先级",
            requires_immediate_fix=False,
            should_block_next_task=False
        )

    def _create_result(
        self,
        priority: PriorityLevel,
        reason: str,
        suggested_action: str,
        requires_immediate_fix: bool,
        should_block_next_task: bool
    ) -> ClassificationResult:
        """创建分类结果"""
        return ClassificationResult(
            priority=priority,
            reason=reason,
            suggested_action=suggested_action,
            requires_immediate_fix=requires_immediate_fix,
            should_block_next_task=should_block_next_task
        )

    def _get_action_for_priority(self, priority: PriorityLevel) -> str:
        """获取优先级对应的建议行动"""
        actions = {
            PriorityLevel.P0_CRITICAL: "立即修复此问题,否则无法继续",
            PriorityLevel.P1_IMPORTANT: "在下个任务前修复此问题",
            PriorityLevel.P2_MINOR: "可以延后处理,但应在迭代结束前修复",
            PriorityLevel.P3_TRIVIAL: "建议性改进,不强制要求"
        }
        return actions.get(priority, "需要人工审查")


# 便捷函数

def classify_issue(issue: CodeIssue, strict_mode: bool = False) -> ClassificationResult:
    """
    分类单个问题 (便捷函数)

    Args:
        issue: 代码问题
        strict_mode: 严格模式

    Returns:
        ClassificationResult: 分类结果

    Example:
        >>> from review.models import CodeIssue, IssueCategory, ReviewSeverity
        >>> from review.issue_classifier import classify_issue
        >>> issue = CodeIssue(
        ...     issue_id="issue-1",
        ...     category=IssueCategory.SECURITY,
        ...     severity=ReviewSeverity.CRITICAL,
        ...     title="SQL Injection",
        ...     description="User input not sanitized"
        ... )
        >>> result = classify_issue(issue)
        >>> print(f"Priority: {result.priority}")
        Priority: P0
    """
    classifier = IssueClassifier(strict_mode=strict_mode)
    return classifier.classify_issue(issue)


def classify_batch(issues: List[CodeIssue], strict_mode: bool = False) -> Dict[PriorityLevel, List[CodeIssue]]:
    """
    批量分类问题 (便捷函数)

    Args:
        issues: 问题列表
        strict_mode: 严格模式

    Returns:
        Dict: 按优先级分组的问题列表

    Example:
        >>> results = classify_batch(issues)
        >>> print(f"P0 issues: {len(results[PriorityLevel.P0_CRITICAL])}")
        >>> print(f"Can proceed: {len(results[PriorityLevel.P0_CRITICAL]) == 0}")
    """
    classifier = IssueClassifier(strict_mode=strict_mode)
    return classifier.batch_classify(issues)


def should_block_development(issues: List[CodeIssue]) -> bool:
    """
    检查是否应该阻塞开发 (便捷函数)

    Args:
        issues: 问题列表

    Returns:
        bool: 如果有 P0 问题返回 True

    Example:
        >>> if should_block_development(issues):
        ...     print("有阻塞问题,需要先修复!")
    """
    classifier = IssueClassifier()
    return classifier.should_block_progress(issues)
