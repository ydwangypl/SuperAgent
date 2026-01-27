#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
内容审查器

实现内容质量审查功能,验证架构的可扩展性。
这个审查器不依赖代码审查系统,是独立实现。
"""

import logging
import re
from typing import List
from datetime import datetime

from core.reviewer import Reviewer, Artifact, ReviewResult, QualityMetric, ReviewStatus


logger = logging.getLogger(__name__)


class ContentReviewer(Reviewer):
    """
    内容审查器

    用于审查各种类型的内容质量:
    - 文章质量
    - 可读性
    - SEO优化
    - 语法和拼写
    - 结构完整性

    这是一个独立的实现,不依赖现有的代码审查系统,
    用于验证新架构确实支持多领域扩展。
    """

    def __init__(self, name: str = "ContentReviewer"):
        """
        初始化内容审查器

        Args:
            name: 审查器名称
        """
        super().__init__(name)
        self.supported_types = ["writing", "content", "article", "blog", "documentation"]

        # 审查规则
        self.min_title_length = 10
        self.min_content_length = 100
        self.max_sentence_length = 30  # 单句最大词数
        self.min_paragraph_count = 3

    def get_supported_types(self) -> List[str]:
        """获取支持的产物类型"""
        return self.supported_types

    def review(self, artifact: Artifact) -> ReviewResult:
        """
        审查内容

        Args:
            artifact: 内容产物
                - artifact_type: 内容类型
                - content: 文本内容 (字符串)

        Returns:
            ReviewResult: 审查结果
        """
        import time
        start_time = time.time()

        try:
            if not self.validate_artifact(artifact):
                return ReviewResult(
                    status=ReviewStatus.REJECTED,
                    overall_score=0.0,
                    feedback="Invalid artifact",
                    approved=False
                )

            content = artifact.content

            # 执行各项审查
            metrics = self._perform_reviews(content)

            # 计算总体评分
            overall_score = self._calculate_overall_score(metrics)

            # 确定审查状态
            if overall_score >= 80:
                status = ReviewStatus.APPROVED
                approved = True
                feedback = "内容质量优秀,符合发布标准。"
            elif overall_score >= 60:
                status = ReviewStatus.NEEDS_IMPROVEMENT
                approved = False
                feedback = "内容基本可用,但建议改进。"
            else:
                status = ReviewStatus.REJECTED
                approved = False
                feedback = "内容质量不达标,需要大幅改进。"

            review_time = time.time() - start_time

            return ReviewResult(
                status=status,
                overall_score=overall_score,
                metrics=metrics,
                feedback=feedback,
                approved=approved,
                metadata={
                    "word_count": len(content.split()),
                    "char_count": len(content),
                    "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
                    "sentence_count": len(re.split(r'[.!?]+', content))
                },
                review_time=review_time
            )

        except Exception as e:
            logger.error(f"Content review failed: {e}", exc_info=True)
            review_time = time.time() - start_time

            return ReviewResult(
                status=ReviewStatus.REJECTED,
                overall_score=0.0,
                feedback=f"审查失败: {str(e)}",
                approved=False,
                review_time=review_time
            )

    def _perform_reviews(self, content: str) -> List[QualityMetric]:
        """执行各项审查"""
        metrics = []

        # 1. 长度审查
        metrics.append(self._review_length(content))

        # 2. 可读性审查
        metrics.append(self._review_readability(content))

        # 3. 结构审查
        metrics.append(self._review_structure(content))

        # 4. 语法审查 (简化版)
        metrics.append(self._review_grammar(content))

        # 5. SEO审查
        metrics.append(self._review_seo(content))

        return metrics

    def _review_length(self, content: str) -> QualityMetric:
        """审查内容长度"""
        word_count = len(content.split())
        char_count = len(content)

        issues = []
        suggestions = []

        if word_count < self.min_content_length:
            issues.append(f"内容过短 ({word_count}字),建议至少{self.min_content_length}字")
            score = 50.0
        elif word_count > 5000:
            issues.append(f"内容过长 ({word_count}字),建议分章节")
            score = 70.0
        else:
            score = 100.0
            suggestions.append("内容长度适中")

        return QualityMetric(
            name="length",
            score=score,
            description="内容长度",
            issues=issues,
            suggestions=suggestions
        )

    def _review_readability(self, content: str) -> QualityMetric:
        """审查可读性"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        issues = []
        suggestions = []

        if not sentences:
            return QualityMetric(
                name="readability",
                score=0.0,
                description="可读性",
                issues=["无法识别句子"]
            )

        # 计算平均句长
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

        long_sentences = [s for s in sentences if len(s.split()) > self.max_sentence_length]

        if long_sentences:
            issues.append(f"发现{len(long_sentences)}个过长的句子")
            score = max(50.0, 100.0 - len(long_sentences) * 10)
        else:
            score = 100.0
            suggestions.append("句子长度适中,易读性良好")

        return QualityMetric(
            name="readability",
            score=score,
            description="可读性",
            issues=issues,
            suggestions=suggestions
        )

    def _review_structure(self, content: str) -> QualityMetric:
        """审查内容结构"""
        lines = content.split('\n')
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        issues = []
        suggestions = []

        # 检查是否有标题
        has_title = any(line.strip().startswith('#') for line in lines)

        # 检查段落数量
        if len(paragraphs) < self.min_paragraph_count:
            issues.append(f"段落过少 ({len(paragraphs)}段),建议至少{self.min_paragraph_count}段")
            score = 60.0
        else:
            score = 100.0

        if not has_title:
            issues.append("缺少标题")
            score = max(score, 70.0)  # 至少70分
        else:
            suggestions.append("有标题,结构清晰")

        return QualityMetric(
            name="structure",
            description="内容结构",
            score=score,
            issues=issues,
            suggestions=suggestions
        )

    def _review_grammar(self, content: str) -> QualityMetric:
        """审查语法 (简化版)"""
        issues = []
        suggestions = []

        score = 100.0

        # 简单的语法检查
        # 检查连续空格
        if re.search(r'  +', content):
            issues.append("发现连续空格")
            score -= 5

        # 检查中英文混排的空格 (简化)
        # 这里只做基本检查

        # 检查标点符号 (简化)
        if re.search(r'[,\.]{2,}', content):
            issues.append("发现重复标点符号")
            score -= 10

        # 检查句子以空格开头
        if re.search(r'^\s+\S', content, re.MULTILINE):
            issues.append("句子以空格开头")
            score -= 5

        if score >= 90:
            suggestions.append("语法基本正确")

        return QualityMetric(
            name="grammar",
            description="语法",
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions
        )

    def _review_seo(self, content: str) -> QualityMetric:
        """审查SEO优化"""
        issues = []
        suggestions = []

        score = 100.0

        # 检查是否有标题
        has_heading = any(line.strip().startswith('#') for line in content.split('\n'))

        # 检查内容长度
        word_count = len(content.split())
        if word_count < 300:
            issues.append("内容过短,SEO效果可能不佳")
            score -= 20

        if not has_heading:
            issues.append("缺少标题标签(H1)")
            score -= 15
        else:
            suggestions.append("有标题,有利于SEO")

        # 检查段落结构
        if '\n\n' not in content:
            issues.append("缺少段落分隔,不利于阅读")
            score -= 10

        return QualityMetric(
            name="seo",
            description="SEO优化",
            score=max(0.0, score),
            issues=issues,
            suggestions=suggestions
        )

    def _calculate_overall_score(self, metrics: List[QualityMetric]) -> float:
        """计算总体评分"""
        if not metrics:
            return 0.0

        # 加权平均
        weights = {
            "length": 0.15,
            "readability": 0.25,
            "structure": 0.20,
            "grammar": 0.25,
            "seo": 0.15
        }

        weighted_sum = 0.0
        total_weight = 0.0

        for metric in metrics:
            weight = weights.get(metric.name, 0.2)
            weighted_sum += metric.score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def __repr__(self) -> str:
        return f"ContentReviewer(name={self.name}, types={self.supported_types})"
