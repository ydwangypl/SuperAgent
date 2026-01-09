#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ralph Wiggum循环

迭代改进代码,直到达到质量标准
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .models import (
    ReviewResult,
    ReviewConfig,
    ReviewStatus,
    CodeIssue,
    ReviewSeverity
)
from .reviewer import CodeReviewer


logger = logging.getLogger(__name__)


class RalphWiggumLoop:
    """Ralph Wiggum迭代改进循环"""

    def __init__(
        self,
        reviewer: CodeReviewer,
        config: Optional[ReviewConfig] = None
    ):
        """初始化Ralph Wiggum循环

        Args:
            reviewer: 代码审查器
            config: 审查配置
        """
        self.reviewer = reviewer
        self.config = config or ReviewConfig()

    async def improve_code(
        self,
        task_id: str,
        files: List[Path],
        initial_code: Dict[str, str],
        llm_callback: Optional[callable] = None
    ) -> ReviewResult:
        """迭代改进代码 (别名方法)"""
        return await self.review_with_loop(task_id, files, initial_code, llm_callback)

    async def review_with_loop(
        self,
        task_id: str,
        files: List[Path],
        code_content: Dict[str, str],
        llm_callback: Optional[callable] = None
    ) -> ReviewResult:
        """迭代改进代码 (Ralph Wiggum 核心入口)

        Args:
            task_id: 任务ID
            files: 文件列表
            code_content: 代码内容
            llm_callback: 改进回调函数 (LLM/Agent)

        Returns:
            ReviewResult: 最终审查结果
        """
        async def internal_callback(current_code: Dict[str, str], improvements: List[Dict]) -> Dict[str, str]:
            if not llm_callback:
                logger.info("未提供LLM回调,跳过改进步骤")
                return current_code
            return await llm_callback(current_code, improvements)

        return await self._run_iteration_loop(task_id, files, code_content, internal_callback)

    async def _run_iteration_loop(
        self,
        task_id: str,
        files: List[Path],
        current_code: Dict[str, str],
        llm_callback: callable
    ) -> ReviewResult:
        """核心迭代循环实现"""
        if not self.config.enable_ralph_wiggum:
            logger.info("Ralph Wiggum循环未启用,执行单次审查")
            return await self.reviewer.review_code(task_id, files, current_code)

        logger.info(f"开始Ralph Wiggum改进循环 (最大迭代: {self.config.max_iterations})")

        iteration = 0
        best_result = None
        best_score = 0.0

        while iteration < self.config.max_iterations:
            iteration += 1
            logger.info(f"第 {iteration} 次迭代...")

            # 审查当前代码
            result = await self.reviewer.review_code(task_id, files, current_code)
            result.iteration_count = iteration

            # 记录最佳结果
            if result.metrics.overall_score > best_score:
                best_score = result.metrics.overall_score
                best_result = result

            # 检查是否达到质量标准
            if self._meets_quality_threshold(result):
                logger.info(f"达到质量标准! 评分: {result.metrics.overall_score:.1f}")
                result.summary += "\n[OK] 代码质量达到标准"
                break

            # 检查是否有严重问题
            if result.has_critical_issues:
                logger.warning(f"存在严重问题,无法继续")
                result.summary += "\n[FAIL] 存在严重问题需要人工处理"
                break

            # 检查是否达到改进阈值
            if iteration > 1:
                previous_score = best_score
                improvement = (result.metrics.overall_score - previous_score) / max(previous_score, 0.01)

                if improvement < self.config.improvement_threshold and improvement >= 0:
                    logger.info(f"改进幅度不足 ({improvement*100:.1f}% < {self.config.improvement_threshold*100:.1f}%)")
                    result.summary += f"\n改进幅度不足,停止迭代 (改进: {improvement*100:.1f}%)"
                    break

            # 生成改进建议
            improvements_needed = self._generate_improvements(result)
            if not improvements_needed:
                logger.info("没有需要改进的地方")
                result.summary += "\n[OK] 代码质量良好,无需改进"
                break

            # 调用改进回调
            logger.info(f"执行 {len(improvements_needed)} 个改进...")
            try:
                improved_code = await llm_callback(current_code, improvements_needed)
                if improved_code == current_code:
                    logger.warning("代码未发生变化,停止迭代")
                    result.summary += "\n代码未发生变化,可能需要人工介入"
                    break
                current_code = improved_code
            except Exception as e:
                logger.error(f"改进失败 ({type(e).__name__}): {e}")
                result.summary += f"\n改进失败 ({type(e).__name__}): {str(e)}"
                result.status = ReviewStatus.FAILED
                break

        if iteration >= self.config.max_iterations:
            logger.info(f"达到最大迭代次数 ({self.config.max_iterations})")
            result.summary += f"\n达到最大迭代次数"

        # 记录最终代码
        final_result = best_result or result
        final_result.improved_code = current_code
        
        return final_result

    def _meets_quality_threshold(self, result: ReviewResult) -> bool:
        """检查是否达到质量标准"""
        if result.metrics.overall_score < self.config.min_overall_score:
            return False
        if result.metrics.critical_count > self.config.max_critical_issues:
            return False
        return True

    def _generate_improvements(self, result: ReviewResult) -> List[Dict[str, Any]]:
        """生成改进建议"""
        improvements = []
        critical_issues = [i for i in result.issues if i.severity == ReviewSeverity.CRITICAL]
        major_issues = [i for i in result.issues if i.severity == ReviewSeverity.MAJOR]
        
        for issue in critical_issues[:5]:
            improvements.append({
                "type": "fix_issue",
                "issue": issue,
                "priority": "critical",
                "description": f"修复严重问题: {issue.title}"
            })

        for issue in major_issues[:3]:
            improvements.append({
                "type": "fix_issue",
                "issue": issue,
                "priority": "major",
                "description": f"修复主要问题: {issue.title}"
            })

        if result.metrics.comment_lines / max(result.metrics.total_lines, 1) < 0.1:
            improvements.append({
                "type": "add_comments",
                "priority": "minor",
                "description": "增加代码注释"
            })

        return improvements
