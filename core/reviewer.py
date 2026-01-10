#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码审查器抽象基类

定义了所有审查器必须实现的接口,使得 SuperAgent
可以支持多种类型的内容审查,而不仅限于代码审查。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


class ReviewStatus(Enum):
    """审查状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    NEEDS_IMPROVEMENT = "needs_improvement"
    REJECTED = "rejected"


@dataclass
class QualityMetric:
    """
    质量指标数据模型

    通用的质量度量,可以用于代码质量、内容质量等。

    Attributes:
        name: 指标名称 (如 "style", "correctness", "readability")
        score: 分数 (0-100)
        description: 指标描述
        issues: 发现的问题列表
        suggestions: 改进建议列表
    """

    name: str
    score: float
    description: str = ""
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"QualityMetric({self.name}={self.score:.1f})"

    def is_passing(self, threshold: float = 70.0) -> bool:
        """
        判断是否通过阈值

        Args:
            threshold: 通过阈值

        Returns:
            bool: 是否通过
        """
        return self.score >= threshold


@dataclass
class Artifact:
    """
    产物数据模型

    通用的产物表示,可以是代码、文档、设计图等。

    Attributes:
        artifact_type: 产物类型 (如 "code", "writing", "design")
        content: 产物内容
        metadata: 额外的元数据
    """

    artifact_type: str
    content: Any
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        content_preview = str(self.content)[:50] if self.content else ""
        return f"Artifact(type={self.artifact_type}, content={content_preview}...)"


@dataclass
class ReviewResult:
    """
    审查结果数据模型

    通用的审查结果表示。

    Attributes:
        status: 审查状态
        overall_score: 总体分数 (0-100)
        metrics: 质量指标列表
        feedback: 反馈意见
        approved: 是否通过
        metadata: 额外的元数据
        review_time: 审查耗时 (秒)
    """

    status: ReviewStatus
    overall_score: float
    metrics: List[QualityMetric] = field(default_factory=list)
    feedback: str = ""
    approved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    review_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def __repr__(self) -> str:
        status_icon = "✅" if self.approved else "❌"
        return f"{status_icon} ReviewResult(score={self.overall_score:.1f}, status={self.status.value})"

    def get_metric_by_name(self, name: str) -> Optional[QualityMetric]:
        """
        根据名称获取质量指标

        Args:
            name: 指标名称

        Returns:
            Optional[QualityMetric]: 质量指标,如果不存在返回 None
        """
        for metric in self.metrics:
            if metric.name == name:
                return metric
        return None

    def has_passing_scores(self, threshold: float = 70.0) -> bool:
        """
        检查所有指标是否都通过阈值

        Args:
            threshold: 通过阈值

        Returns:
            bool: 是否所有指标都通过
        """
        if not self.metrics:
            return self.overall_score >= threshold

        return all(metric.is_passing(threshold) for metric in self.metrics)


class Reviewer(ABC):
    """
    代码审查器抽象基类

    所有审查器必须继承此类并实现 review() 方法。

    设计理念:
    - 依赖倒置: 高层模块依赖此抽象,而非具体实现
    - 开闭原则: 可以添加新的审查器而无需修改现有代码
    - 单一职责: 每个审查器只负责一种类型的审查
    """

    def __init__(self, name: Optional[str] = None):
        """
        初始化审查器

        Args:
            name: 审查器名称 (默认使用类名)
        """
        self.name = name or self.__class__.__name__

    @abstractmethod
    def review(self, artifact: Artifact) -> ReviewResult:
        """
        审查产物

        Args:
            artifact: 要审查的产物

        Returns:
            ReviewResult: 审查结果

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement review()")

    def can_review(self, artifact_type: str) -> bool:
        """
        判断是否能审查指定类型的产物

        默认实现: 检查 artifact_type 是否在 get_supported_types() 返回的列表中

        Args:
            artifact_type: 产物类型

        Returns:
            bool: 是否能审查
        """
        return artifact_type in self.get_supported_types()

    def get_supported_types(self) -> List[str]:
        """
        获取支持的产物类型列表

        子类应该重写此方法以返回支持的产物类型。

        Returns:
            List[str]: 支持的产物类型列表
        """
        return []

    def validate_artifact(self, artifact: Artifact) -> bool:
        """
        验证产物是否有效

        默认实现: 检查产物类型是否支持

        Args:
            artifact: 要验证的产物

        Returns:
            bool: 产物是否有效
        """
        if not self.can_review(artifact.artifact_type):
            return False

        if artifact.content is None:
            return False

        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


class ReviewerError(Exception):
    """审查器异常基类"""

    def __init__(self, message: str, reviewer_name: str, artifact: Artifact):
        self.message = message
        self.reviewer_name = reviewer_name
        self.artifact = artifact
        super().__init__(f"[{reviewer_name}] {message}")


class ArtifactValidationError(ReviewerError):
    """产物验证失败异常"""

    pass


class ReviewExecutionError(ReviewerError):
    """审查执行失败异常"""

    pass
