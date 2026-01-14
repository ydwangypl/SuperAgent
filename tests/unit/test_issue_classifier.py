"""
Issue Classifier 单元测试

测试问题分级器的所有功能
"""

import pytest
from review.issue_classifier import (
    IssueClassifier,
    PriorityLevel,
    ClassificationResult,
    classify_issue,
    classify_batch,
    should_block_development
)
from review.models import CodeIssue, IssueCategory, ReviewSeverity


class TestPriorityLevel:
    """PriorityLevel 枚举测试"""

    def test_priority_values(self):
        """测试优先级枚举值"""
        assert PriorityLevel.P0_CRITICAL.value == "P0"
        assert PriorityLevel.P1_IMPORTANT.value == "P1"
        assert PriorityLevel.P2_MINOR.value == "P2"
        assert PriorityLevel.P3_TRIVIAL.value == "P3"


class TestIssueClassifier:
    """IssueClassifier 测试套件"""

    def test_init_default(self):
        """测试默认初始化"""
        classifier = IssueClassifier()
        assert classifier.strict_mode is False
        assert len(classifier.classification_history) == 0

    def test_init_strict_mode(self):
        """测试严格模式初始化"""
        classifier = IssueClassifier(strict_mode=True)
        assert classifier.strict_mode is True

    def test_classify_blocker_issue(self):
        """测试分类 BLOCKER 问题"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.SECURITY,
            severity=ReviewSeverity.BLOCKER,
            title="Security vulnerability",
            description="SQL injection in login form"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        assert result.priority == PriorityLevel.P0_CRITICAL
        assert result.requires_immediate_fix is True
        assert result.should_block_next_task is True
        assert "BLOCKER" in result.reason

    def test_classify_critical_issue(self):
        """测试分类 CRITICAL 问题"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.ERROR_HANDLING,
            severity=ReviewSeverity.CRITICAL,
            title="Application crash",
            description="App crashes on startup"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        assert result.priority == PriorityLevel.P0_CRITICAL
        assert result.requires_immediate_fix is True

    def test_classify_major_issue(self):
        """测试分类 MAJOR 问题"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.PERFORMANCE,
            severity=ReviewSeverity.MAJOR,
            title="Slow query",
            description="Query takes 10 seconds"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        assert result.priority == PriorityLevel.P1_IMPORTANT
        assert result.requires_immediate_fix is False
        assert result.should_block_next_task is True

    def test_classify_minor_issue(self):
        """测试分类 MINOR 问题"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.CODE_STYLE,
            severity=ReviewSeverity.MINOR,
            title="Style issue",
            description="Line too long"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        assert result.priority == PriorityLevel.P2_MINOR
        assert result.requires_immediate_fix is False
        assert result.should_block_next_task is False

    def test_classify_info_issue(self):
        """测试分类 INFO 问题"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.DOCUMENTATION,
            severity=ReviewSeverity.INFO,
            title="Indentation",
            description="Inconsistent indentation in file"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        # "indentation" 匹配 P3 关键词,应该是 P3
        assert result.priority == PriorityLevel.P3_TRIVIAL
        assert result.requires_immediate_fix is False
        assert result.should_block_next_task is False

    def test_classify_security_issue_by_content(self):
        """测试基于内容分类安全问题"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.SECURITY,
            severity=ReviewSeverity.INFO,  # 即使是 INFO
            title="XSS vulnerability",
            description="Cross-site scripting in user input"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        # 基于分类映射,安全问题应该是 P0
        assert result.priority == PriorityLevel.P0_CRITICAL

    def test_classify_performance_issue_by_content(self):
        """测试基于内容分类性能问题"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.PERFORMANCE,
            severity=ReviewSeverity.INFO,
            title="Slow performance",
            description="API timeout after 30 seconds"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        # 基于分类映射,性能问题应该是 P1
        assert result.priority == PriorityLevel.P1_IMPORTANT

    def test_classify_by_keywords_p0(self):
        """测试基于关键词分类 P0"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.ERROR_HANDLING,
            severity=ReviewSeverity.INFO,
            title="Data loss",
            description="User data deleted accidentally"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        assert result.priority == PriorityLevel.P0_CRITICAL
        assert "关键词" in result.reason

    def test_classify_by_keywords_p1(self):
        """测试基于关键词分类 P1"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.BEST_PRACTICES,
            severity=ReviewSeverity.INFO,
            title="Logic error",
            description="Condition is inverted"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        assert result.priority == PriorityLevel.P1_IMPORTANT

    def test_classify_by_keywords_p2(self):
        """测试基于关键词分类 P2"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.CODE_STYLE,
            severity=ReviewSeverity.INFO,
            title="Code smell",
            description="Function is too complex"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        assert result.priority == PriorityLevel.P2_MINOR

    def test_classify_by_keywords_p3(self):
        """测试基于关键词分类 P3"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.DOCUMENTATION,
            severity=ReviewSeverity.INFO,
            title="Formatting",
            description="Indentation is inconsistent"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        assert result.priority == PriorityLevel.P3_TRIVIAL

    def test_strict_mode_upgrade(self):
        """测试严格模式升级优先级"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.TESTING,
            severity=ReviewSeverity.INFO,
            title="Test fails",
            description="Unit test for login is failing"
        )
        classifier = IssueClassifier(strict_mode=True)

        result = classifier.classify_issue(issue)

        # 严格模式下,P1 应该升级到 P0
        assert result.priority == PriorityLevel.P0_CRITICAL


class TestBatchClassification:
    """批量分类测试"""

    def test_batch_classify(self):
        """测试批量分类"""
        issues = [
            CodeIssue(
                issue_id="issue-1",
                category=IssueCategory.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                title="Security bug",
                description="SQL injection"
            ),
            CodeIssue(
                issue_id="issue-2",
                category=IssueCategory.PERFORMANCE,
                severity=ReviewSeverity.MAJOR,
                title="Slow query",
                description="Query timeout"
            ),
            CodeIssue(
                issue_id="issue-3",
                category=IssueCategory.CODE_STYLE,
                severity=ReviewSeverity.MINOR,
                title="Style",
                description="Formatting issue"
            )
        ]
        classifier = IssueClassifier()

        result = classifier.batch_classify(issues)

        assert len(result[PriorityLevel.P0_CRITICAL]) == 1
        assert len(result[PriorityLevel.P1_IMPORTANT]) == 1
        assert len(result[PriorityLevel.P2_MINOR]) == 1
        assert result[PriorityLevel.P0_CRITICAL][0].issue_id == "issue-1"
        assert result[PriorityLevel.P1_IMPORTANT][0].issue_id == "issue-2"
        assert result[PriorityLevel.P2_MINOR][0].issue_id == "issue-3"

    def test_get_summary(self):
        """测试获取分类摘要"""
        issues = [
            CodeIssue(
                issue_id="issue-1",
                category=IssueCategory.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                title="Security",
                description="Bug"
            ),
            CodeIssue(
                issue_id="issue-2",
                category=IssueCategory.PERFORMANCE,
                severity=ReviewSeverity.MAJOR,
                title="Performance",
                description="Issue"
            ),
            CodeIssue(
                issue_id="issue-3",
                category=IssueCategory.CODE_STYLE,
                severity=ReviewSeverity.MINOR,
                title="Style",
                description="Issue"
            )
        ]
        classifier = IssueClassifier()

        summary = classifier.get_summary(issues)

        assert summary["total_issues"] == 3
        assert summary["p0_critical"] == 1
        assert summary["p1_important"] == 1
        assert summary["p2_minor"] == 1
        assert summary["has_blocking_issues"] is True
        assert summary["requires_attention"] is True
        assert summary["can_proceed"] is False

    def test_should_block_progress(self):
        """测试是否阻塞进度"""
        issues_with_p0 = [
            CodeIssue(
                issue_id="issue-1",
                category=IssueCategory.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                title="Critical",
                description="Bug"
            )
        ]
        issues_without_p0 = [
            CodeIssue(
                issue_id="issue-1",
                category=IssueCategory.CODE_STYLE,
                severity=ReviewSeverity.MINOR,
                title="Style",
                description="Issue"
            )
        ]
        classifier = IssueClassifier()

        assert classifier.should_block_progress(issues_with_p0) is True
        assert classifier.should_block_progress(issues_without_p0) is False

    def test_classification_history(self):
        """测试分类历史记录"""
        issues = [
            CodeIssue(
                issue_id="issue-1",
                category=IssueCategory.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                title="Security",
                description="Bug"
            ),
            CodeIssue(
                issue_id="issue-2",
                category=IssueCategory.PERFORMANCE,
                severity=ReviewSeverity.MAJOR,
                title="Performance",
                description="Issue"
            )
        ]
        classifier = IssueClassifier()

        classifier.batch_classify(issues)

        assert len(classifier.classification_history) == 2
        assert classifier.classification_history[0]["issue_id"] == "issue-1"
        assert classifier.classification_history[0]["priority"] == "P0"
        assert classifier.classification_history[1]["issue_id"] == "issue-2"
        assert classifier.classification_history[1]["priority"] == "P1"


class TestConvenienceFunctions:
    """便捷函数测试"""

    def test_classify_issue_function(self):
        """测试 classify_issue 函数"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.SECURITY,
            severity=ReviewSeverity.CRITICAL,
            title="Security",
            description="Bug"
        )

        result = classify_issue(issue)

        assert isinstance(result, ClassificationResult)
        assert result.priority == PriorityLevel.P0_CRITICAL

    def test_classify_batch_function(self):
        """测试 classify_batch 函数"""
        issues = [
            CodeIssue(
                issue_id="issue-1",
                category=IssueCategory.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                title="Security",
                description="Bug"
            )
        ]

        result = classify_batch(issues)

        assert isinstance(result, dict)
        assert PriorityLevel.P0_CRITICAL in result
        assert len(result[PriorityLevel.P0_CRITICAL]) == 1

    def test_should_block_development_function(self):
        """测试 should_block_development 函数"""
        issues_with_critical = [
            CodeIssue(
                issue_id="issue-1",
                category=IssueCategory.SECURITY,
                severity=ReviewSeverity.CRITICAL,
                title="Critical",
                description="Bug"
            )
        ]
        issues_without_critical = [
            CodeIssue(
                issue_id="issue-1",
                category=IssueCategory.CODE_STYLE,
                severity=ReviewSeverity.MINOR,
                title="Style",
                description="Issue"
            )
        ]

        assert should_block_development(issues_with_critical) is True
        assert should_block_development(issues_without_critical) is False


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_description(self):
        """测试空描述"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.BEST_PRACTICES,
            severity=ReviewSeverity.INFO,
            title="Issue",
            description=""
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        # 应该使用默认分类
        assert result.priority == PriorityLevel.P2_MINOR

    def test_mixed_case_keywords(self):
        """测试混合大小写关键词"""
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.BEST_PRACTICES,
            severity=ReviewSeverity.INFO,
            title="Style",
            description="This has IMPROVEMENT needed"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        # "improvement" 匹配 P2 关键词
        assert result.priority == PriorityLevel.P2_MINOR

    def test_unknown_category(self):
        """测试未知分类"""
        # 使用一个不在映射中的分类
        # 这会触发关键词检测
        issue = CodeIssue(
            issue_id="issue-1",
            category=IssueCategory.DOCUMENTATION,  # 映射到 P3
            severity=ReviewSeverity.INFO,
            title="Critical bug",
            description="Application crashes"
        )
        classifier = IssueClassifier()

        result = classifier.classify_issue(issue)

        # 应该基于关键词分类为 P0
        assert result.priority == PriorityLevel.P0_CRITICAL
