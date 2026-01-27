#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reviewer适配器

连接新的Reviewer抽象层和现有的代码审查系统。
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import uuid

from core.reviewer import Reviewer, Artifact, ReviewResult, QualityMetric, ReviewStatus
from review.reviewer import CodeReviewer
from review.ralph_wiggum import RalphWiggumLoop
from review.models import ReviewConfig


# 默认超时配置（秒）
DEFAULT_REVIEW_TIMEOUT = 600  # 10 minutes

# 审查器名称
DEFAULT_REVIEWER_NAME = "CodeReviewerAdapter"

logger = logging.getLogger(__name__)


class CodeReviewerAdapter(Reviewer):
    """
    基于现有CodeReviewer的Reviewer实现

    这个Reviewer将新的Reviewer接口适配到现有的代码审查系统。

    示例:
        reviewer = CodeReviewerAdapter(project_root, config)
        artifact = Artifact(artifact_type="code", content="...")
        result = await reviewer.review(artifact)
    """

    def __init__(
        self,
        project_root: Path,
        config: Optional[ReviewConfig] = None,
        name: Optional[str] = None
    ):
        """
        初始化代码审查器适配器

        Args:
            project_root: 项目根目录
            config: 审查配置
            name: 审查器名称
        """
        super().__init__(name)
        self.project_root = project_root
        self.config = config or ReviewConfig()

        # 初始化底层审查器
        self._reviewer = CodeReviewer(self.config)

        # 初始化Ralph Wiggum循环
        if self.config.enable_ralph_wiggum:
            self._ralph_wiggum = RalphWiggumLoop(self._reviewer, self.config)
        else:
            self._ralph_wiggum = None

    def get_supported_types(self) -> List[str]:
        """获取支持的产物类型"""
        return ["code", "coding", "python", "javascript", "typescript"]

    def review(self, artifact: Artifact) -> ReviewResult:
        """
        审查产物 - 同步接口

        Args:
            artifact: 要审查的产物

        Returns:
            ReviewResult: 审查结果
        """
        if not self.validate_artifact(artifact):
            return ReviewResult(
                status=ReviewStatus.REJECTED,
                overall_score=0.0,
                feedback="Invalid artifact",
                approved=False
            )

        # 运行异步审查 - 修复异步/同步反模式
        try:
            # 获取或创建事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                # 已在事件循环中，使用 run_until_complete
                result = loop.run_until_complete(self._review_async(artifact))
            else:
                # 不在事件循环中，直接运行
                result = loop.run_until_complete(self._review_async(artifact))

        except asyncio.TimeoutError:
            logger.error(f"Reviewer {self.name} timed out after {DEFAULT_REVIEW_TIMEOUT}s")
            return ReviewResult(
                status=ReviewStatus.REJECTED,
                overall_score=0.0,
                feedback=f"Review timed out after {DEFAULT_REVIEW_TIMEOUT}s",
                approved=False
            )
        except Exception as e:
            logger.error(f"Reviewer {self.name} failed: {e}", exc_info=True)
            return ReviewResult(
                status=ReviewStatus.REJECTED,
                overall_score=0.0,
                feedback=f"Review failed: {str(e)}",
                approved=False
            )

        return result

    async def _review_async(self, artifact: Artifact) -> ReviewResult:
        """
        异步审查产物

        Args:
            artifact: 要审查的产物

        Returns:
            ReviewResult: 审查结果
        """
        start_time = datetime.now()

        try:
            # 准备审查数据
            if isinstance(artifact.content, str):
                # 单个文件内容
                code_content = {"file.py": artifact.content}
                files = []
            elif isinstance(artifact.content, dict):
                # 文件路径到内容的映射
                code_content = artifact.content
                files = [Path(f) for f in artifact.content.keys()]
            elif isinstance(artifact.content, list):
                # 文件路径列表
                files = [Path(f) for f in artifact.content]
                code_content = {}
                for file_path in files:
                    if file_path.exists():
                        code_content[file_path.name] = file_path.read_text()
            else:
                raise ValueError(f"Unsupported artifact content type: {type(artifact.content)}")

            # 生成审查ID
            review_id = f"review-{uuid.uuid4().hex[:8]}"

            # 执行审查
            if self._ralph_wiggum:
                # 使用Ralph Wiggum循环
                logger.info(f"Reviewer {self.name} using Ralph Wiggum loop")
                result = await self._ralph_wiggum.review_with_loop(
                    task_id=review_id,
                    files=files,
                    code_content=code_content,
                    llm_callback=None  # 暂不使用改进回调
                )
            else:
                # 单次审查
                logger.info(f"Reviewer {self.name} performing single review")
                result = await self._reviewer.review_code(
                    task_id=review_id,
                    files=files,
                    code_content=code_content
                )

            # 转换结果
            review_time = (datetime.now() - start_time).total_seconds()

            return self._convert_review_result(result, review_time)

        except Exception as e:
            logger.error(f"Error in _review_async: {e}", exc_info=True)
            review_time = (datetime.now() - start_time).total_seconds()

            return ReviewResult(
                status=ReviewStatus.REJECTED,
                overall_score=0.0,
                feedback=f"Review error: {str(e)}",
                approved=False,
                review_time=review_time
            )

    def _convert_review_result(
        self,
        review_result,
        review_time: float
    ) -> ReviewResult:
        """转换审查结果格式"""
        # 提取指标 - 使用实际存在的字段
        metrics = [
            QualityMetric(
                name="overall",
                score=review_result.metrics.overall_score,
                description="Overall score"
            ),
            QualityMetric(
                name="complexity",
                score=review_result.metrics.complexity_score,
                description="Code complexity"
            ),
            QualityMetric(
                name="maintainability",
                score=review_result.metrics.maintainability_score,
                description="Code maintainability"
            )
        ]

        # 确定状态
        overall_score = review_result.metrics.overall_score
        if overall_score >= 80:
            status = ReviewStatus.APPROVED
            approved = True
        elif overall_score >= 60:
            status = ReviewStatus.NEEDS_IMPROVEMENT
            approved = False
        else:
            status = ReviewStatus.REJECTED
            approved = False

        return ReviewResult(
            status=status,
            overall_score=overall_score,
            metrics=metrics,
            feedback=review_result.summary,
            approved=approved,
            metadata={
                "issue_count": review_result.metrics.issue_count,
                "critical_count": review_result.metrics.critical_count,
                "major_count": review_result.metrics.major_count,
                "minor_count": review_result.metrics.minor_count,
                "recommendations": review_result.recommendations
            },
            review_time=review_time
        )


class ReviewerAdapter:
    """
    Reviewer适配器 - 管理Reviewer实例

    这个类作为高级接口,简化Reviewer的使用。

    示例:
        adapter = ReviewerAdapter(project_root)
        result = await adapter.review("code", {"content": "..."})
    """

    def __init__(self, project_root: Path):
        """
        初始化适配器

        Args:
            project_root: 项目根目录
        """
        self.project_root = project_root
        self._reviewers: Dict[str, CodeReviewerAdapter] = {}

    def get_reviewer(
        self,
        artifact_type: str,
        config: Optional[ReviewConfig] = None
    ) -> CodeReviewerAdapter:
        """
        获取适合处理该产物类型的审查器

        Args:
            artifact_type: 产物类型
            config: 审查配置

        Returns:
            CodeReviewerAdapter: 审查器实例
        """
        # 检查是否已有缓存的审查器
        cache_key = f"{artifact_type}_{id(config)}"
        if cache_key in self._reviewers:
            return self._reviewers[cache_key]

        # 创建新的审查器
        reviewer = CodeReviewerAdapter(
            project_root=self.project_root,
            config=config,
            name=f"{artifact_type}_reviewer"
        )

        # 缓存审查器
        self._reviewers[cache_key] = reviewer

        return reviewer

    def _create_artifact(
        self,
        artifact_type: str,
        artifact_data: Dict[str, Any]
    ) -> Artifact:
        """创建 Artifact 对象 - 公共方法消除重复"""
        return Artifact(
            artifact_type=artifact_type,
            content=artifact_data.get("content"),
            metadata=artifact_data.get("metadata", {})
        )

    def _convert_result_to_dict(self, result: ReviewResult) -> Dict[str, Any]:
        """转换审查结果为字典格式 - 公共方法消除重复"""
        return {
            "status": result.status.value,
            "overall_score": result.overall_score,
            "metrics": [
                {
                    "name": m.name,
                    "score": m.score,
                    "description": m.description,
                    "issues": m.issues,
                    "suggestions": m.suggestions
                }
                for m in result.metrics
            ],
            "feedback": result.feedback,
            "approved": result.approved,
            "metadata": result.metadata,
            "review_time": result.review_time
        }

    async def review(
        self,
        artifact_type: str,
        artifact_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        审查产物 (异步接口)

        Args:
            artifact_type: 产物类型
            artifact_data: 产物数据
            config: 审查配置

        Returns:
            审查结果字典
        """
        # 转换配置
        review_config = None
        if config:
            review_config = ReviewConfig(**config)

        reviewer = self.get_reviewer(artifact_type, review_config)

        # 创建Artifact对象
        artifact = self._create_artifact(artifact_type, artifact_data)

        # 执行审查
        result = await reviewer._review_async(artifact)

        # 转换为字典格式
        return self._convert_result_to_dict(result)

    def review_sync(
        self,
        artifact_type: str,
        artifact_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        审查产物 (同步接口)

        Args:
            artifact_type: 产物类型
            artifact_data: 产物数据
            config: 审查配置

        Returns:
            审查结果字典
        """
        # 转换配置
        review_config = None
        if config:
            review_config = ReviewConfig(**config)

        reviewer = self.get_reviewer(artifact_type, review_config)

        # 创建Artifact对象
        artifact = self._create_artifact(artifact_type, artifact_data)

        # 执行审查
        result = reviewer.review(artifact)

        # 转换为字典格式
        return self._convert_result_to_dict(result)
