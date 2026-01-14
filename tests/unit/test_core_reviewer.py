#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
核心审查器抽象层单元测试
"""

import pytest
import sys
from pathlib import Path
from typing import List

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.reviewer import (
    Reviewer,
    Artifact,
    ReviewResult,
    QualityMetric,
    ReviewStatus,
    ReviewerError,
    ArtifactValidationError,
    ReviewExecutionError
)


class MockCodeReviewer(Reviewer):
    """模拟代码审查器 - 用于测试"""

    def get_supported_types(self) -> List[str]:
        return ["code", "coding"]

    def review(self, artifact: Artifact) -> ReviewResult:
        if not self.validate_artifact(artifact):
            return ReviewResult(
                status=ReviewStatus.REJECTED,
                overall_score=0.0,
                feedback="Invalid artifact"
            )

        # 模拟审查
        metrics = [
            QualityMetric(
                name="style",
                score=85.0,
                description="Code style",
                issues=["Line too long"],
                suggestions=["Break line"]
            ),
            QualityMetric(
                name="correctness",
                score=90.0,
                description="Code correctness"
            )
        ]

        return ReviewResult(
            status=ReviewStatus.APPROVED,
            overall_score=87.5,
            metrics=metrics,
            feedback="Code looks good!",
            approved=True
        )


class MockContentReviewer(Reviewer):
    """模拟内容审查器 - 用于测试"""

    def get_supported_types(self) -> List[str]:
        return ["writing", "content"]

    def review(self, artifact: Artifact) -> ReviewResult:
        if not self.validate_artifact(artifact):
            return ReviewResult(
                status=ReviewStatus.REJECTED,
                overall_score=0.0,
                feedback="Invalid artifact"
            )

        # 模拟审查
        metrics = [
            QualityMetric(
                name="grammar",
                score=80.0,
                description="Grammar check",
                issues=["Some grammar issues"]
            ),
            QualityMetric(
                name="readability",
                score=75.0,
                description="Readability score"
            )
        ]

        return ReviewResult(
            status=ReviewStatus.NEEDS_IMPROVEMENT,
            overall_score=77.5,
            metrics=metrics,
            feedback="Content needs improvement",
            approved=False
        )


class TestQualityMetric:
    """QualityMetric 数据模型测试"""

    def test_metric_creation(self):
        """测试指标创建"""
        metric = QualityMetric(
            name="style",
            score=85.0,
            description="Code style",
            issues=["Issue 1", "Issue 2"],
            suggestions=["Suggestion 1"]
        )

        assert metric.name == "style"
        assert metric.score == 85.0
        assert len(metric.issues) == 2
        assert len(metric.suggestions) == 1

    def test_metric_repr(self):
        """测试指标字符串表示"""
        metric = QualityMetric(name="style", score=85.0)
        repr_str = repr(metric)

        assert "style" in repr_str
        assert "85.0" in repr_str

    def test_is_passing(self):
        """测试通过判断"""
        metric_passing = QualityMetric(name="test", score=75.0)
        metric_failing = QualityMetric(name="test", score=65.0)

        assert metric_passing.is_passing(threshold=70.0) is True
        assert metric_failing.is_passing(threshold=70.0) is False

        # 测试自定义阈值
        assert metric_passing.is_passing(threshold=80.0) is False


class TestArtifact:
    """Artifact 数据模型测试"""

    def test_artifact_creation(self):
        """测试产物创建"""
        artifact = Artifact(
            artifact_type="code",
            content="def hello(): pass",
            metadata={"language": "python", "lines": 1}
        )

        assert artifact.artifact_type == "code"
        assert artifact.content == "def hello(): pass"
        assert artifact.metadata["language"] == "python"

    def test_artifact_repr(self):
        """测试产物字符串表示"""
        artifact = Artifact(
            artifact_type="code",
            content="x" * 100  # 长内容
        )

        repr_str = repr(artifact)
        assert "code" in repr_str
        assert "..." in repr_str  # 应该被截断


class TestReviewResult:
    """ReviewResult 数据模型测试"""

    def test_approved_result(self):
        """测试通过结果"""
        metrics = [
            QualityMetric(name="style", score=85.0),
            QualityMetric(name="correctness", score=90.0)
        ]

        result = ReviewResult(
            status=ReviewStatus.APPROVED,
            overall_score=87.5,
            metrics=metrics,
            feedback="Good!",
            approved=True
        )

        assert result.status == ReviewStatus.APPROVED
        assert result.overall_score == 87.5
        assert result.approved is True
        assert len(result.metrics) == 2

    def test_needs_improvement_result(self):
        """测试需要改进结果"""
        result = ReviewResult(
            status=ReviewStatus.NEEDS_IMPROVEMENT,
            overall_score=65.0,
            feedback="Needs work",
            approved=False
        )

        assert result.status == ReviewStatus.NEEDS_IMPROVEMENT
        assert result.approved is False

    def test_result_repr(self):
        """测试结果字符串表示"""
        approved = ReviewResult(
            status=ReviewStatus.APPROVED,
            overall_score=85.0,
            approved=True
        )
        assert "✅" in repr(approved)

        rejected = ReviewResult(
            status=ReviewStatus.REJECTED,
            overall_score=50.0,
            approved=False
        )
        assert "❌" in repr(rejected)

    def test_get_metric_by_name(self):
        """测试根据名称获取指标"""
        metrics = [
            QualityMetric(name="style", score=85.0),
            QualityMetric(name="correctness", score=90.0)
        ]

        result = ReviewResult(
            status=ReviewStatus.APPROVED,
            overall_score=87.5,
            metrics=metrics
        )

        style_metric = result.get_metric_by_name("style")
        assert style_metric is not None
        assert style_metric.score == 85.0

        missing_metric = result.get_metric_by_name("performance")
        assert missing_metric is None

    def test_has_passing_scores(self):
        """测试所有指标是否通过"""
        # 所有指标都通过
        passing_metrics = [
            QualityMetric(name="style", score=85.0),
            QualityMetric(name="correctness", score=90.0)
        ]

        passing_result = ReviewResult(
            status=ReviewStatus.APPROVED,
            overall_score=87.5,
            metrics=passing_metrics
        )

        assert passing_result.has_passing_scores(threshold=70.0) is True

        # 有一个指标不通过
        failing_metrics = [
            QualityMetric(name="style", score=85.0),
            QualityMetric(name="correctness", score=65.0)  # 不及格
        ]

        failing_result = ReviewResult(
            status=ReviewStatus.NEEDS_IMPROVEMENT,
            overall_score=75.0,
            metrics=failing_metrics
        )

        assert failing_result.has_passing_scores(threshold=70.0) is False

        # 没有指标 - 检查总分
        no_metrics_result = ReviewResult(
            status=ReviewStatus.APPROVED,
            overall_score=75.0
        )

        assert no_metrics_result.has_passing_scores(threshold=70.0) is True


class TestReviewer:
    """Reviewer 抽象类测试"""

    def test_cannot_instantiate_abstract_reviewer(self):
        """测试不能实例化抽象审查器"""
        with pytest.raises(TypeError):
            Reviewer()

    def test_reviewer_name(self):
        """测试审查器名称"""
        reviewer = MockCodeReviewer()
        assert reviewer.name == "MockCodeReviewer"

        custom_reviewer = MockCodeReviewer(name="CustomReviewer")
        assert custom_reviewer.name == "CustomReviewer"

    def test_can_review(self):
        """测试 can_review 方法"""
        reviewer = MockCodeReviewer()

        assert reviewer.can_review("code") is True
        assert reviewer.can_review("coding") is True
        assert reviewer.can_review("writing") is False
        assert reviewer.can_review("design") is False

    def test_get_supported_types(self):
        """测试获取支持的类型"""
        code_reviewer = MockCodeReviewer()
        content_reviewer = MockContentReviewer()

        assert "code" in code_reviewer.get_supported_types()
        assert "writing" in content_reviewer.get_supported_types()

    def test_validate_artifact_valid(self):
        """测试验证有效产物"""
        reviewer = MockCodeReviewer()
        artifact = Artifact(
            artifact_type="code",
            content="def hello(): pass"
        )

        assert reviewer.validate_artifact(artifact) is True

    def test_validate_artifact_invalid_type(self):
        """测试验证无效类型产物"""
        reviewer = MockCodeReviewer()
        artifact = Artifact(
            artifact_type="writing",  # 错误的类型
            content="Some content"
        )

        assert reviewer.validate_artifact(artifact) is False

    def test_validate_artifact_none_content(self):
        """测试验证空内容产物"""
        reviewer = MockCodeReviewer()
        artifact = Artifact(
            artifact_type="code",
            content=None  # 空内容
        )

        assert reviewer.validate_artifact(artifact) is False

    def test_review_success(self):
        """测试成功审查"""
        reviewer = MockCodeReviewer()
        artifact = Artifact(
            artifact_type="code",
            content="def hello(): pass"
        )

        result = reviewer.review(artifact)

        assert result.status == ReviewStatus.APPROVED
        assert result.overall_score == 87.5
        assert result.approved is True
        assert len(result.metrics) == 2

    def test_review_invalid_artifact(self):
        """测试审查无效产物"""
        reviewer = MockCodeReviewer()
        artifact = Artifact(
            artifact_type="writing",  # 错误的类型
            content="Some content"
        )

        result = reviewer.review(artifact)

        assert result.status == ReviewStatus.REJECTED
        assert result.overall_score == 0.0
        assert result.feedback == "Invalid artifact"

    def test_reviewer_repr(self):
        """测试审查器字符串表示"""
        reviewer = MockCodeReviewer(name="TestReviewer")
        repr_str = repr(reviewer)

        assert "MockCodeReviewer" in repr_str
        assert "TestReviewer" in repr_str


class TestReviewerErrors:
    """审查器异常测试"""

    def test_reviewer_error_creation(self):
        """测试审查器异常创建"""
        artifact = Artifact(artifact_type="code", content="test")

        error = ReviewerError(
            message="Test error",
            reviewer_name="TestReviewer",
            artifact=artifact
        )

        assert error.message == "Test error"
        assert error.reviewer_name == "TestReviewer"
        assert error.artifact == artifact
        assert "TestReviewer" in str(error)

    def test_artifact_validation_error(self):
        """测试产物验证异常"""
        artifact = Artifact(artifact_type="code", content="test")

        error = ArtifactValidationError(
            message="Validation failed",
            reviewer_name="TestReviewer",
            artifact=artifact
        )

        assert isinstance(error, ReviewerError)

    def test_review_execution_error(self):
        """测试审查执行异常"""
        artifact = Artifact(artifact_type="code", content="test")

        error = ReviewExecutionError(
            message="Review failed",
            reviewer_name="TestReviewer",
            artifact=artifact
        )

        assert isinstance(error, ReviewerError)


class TestMultipleReviewers:
    """多审查器测试"""

    def test_different_reviewers_different_types(self):
        """测试不同审查器支持不同类型"""
        code_reviewer = MockCodeReviewer()
        content_reviewer = MockContentReviewer()

        # 代码审查器应该审查代码产物
        code_artifact = Artifact(artifact_type="code", content="code")
        assert code_reviewer.can_review(code_artifact.artifact_type)

        # 内容审查器应该审查写作产物
        writing_artifact = Artifact(artifact_type="writing", content="content")
        assert content_reviewer.can_review(writing_artifact.artifact_type)

        # 交叉测试 - 不应该审查
        assert not code_reviewer.can_review(writing_artifact.artifact_type)
        assert not content_reviewer.can_review(code_artifact.artifact_type)

    def test_review_with_different_reviewers(self):
        """测试使用不同审查器审查产物"""
        code_reviewer = MockCodeReviewer()
        content_reviewer = MockContentReviewer()

        code_artifact = Artifact(artifact_type="code", content="def hello(): pass")
        writing_artifact = Artifact(artifact_type="writing", content="Some article content")

        code_result = code_reviewer.review(code_artifact)
        writing_result = content_reviewer.review(writing_artifact)

        assert code_result.approved is True
        assert code_result.status == ReviewStatus.APPROVED

        assert writing_result.approved is False
        assert writing_result.status == ReviewStatus.NEEDS_IMPROVEMENT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
