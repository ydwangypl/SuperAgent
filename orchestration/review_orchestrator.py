#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码审查编排器 (ReviewOrchestrator)

负责协调代码审查流程，包括文件读取、审查执行、改进建议应用等
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import aiofiles
from .base import BaseOrchestrator
from .models import TaskExecution, TaskStatus, ExecutionPriority, OrchestrationConfig
from .agent_dispatcher import AgentDispatcher
from .mappers import OrchestrationMapper
from common.models import AgentType

try:
    from review import CodeReviewer, RalphWiggumLoop, ReviewConfig, ReviewResult
    REVIEW_AVAILABLE = True
except ImportError:
    REVIEW_AVAILABLE = False
    CodeReviewer = None
    RalphWiggumLoop = None
    ReviewConfig = None
    ReviewResult = None

# Issue Classifier import (P0 v3.2)
try:
    from review.issue_classifier import IssueClassifier, PriorityLevel
    ISSUE_CLASSIFIER_AVAILABLE = True
except ImportError:
    ISSUE_CLASSIFIER_AVAILABLE = False
    IssueClassifier = None
    PriorityLevel = None

logger = logging.getLogger(__name__)


class ReviewOrchestrator(BaseOrchestrator):
    """负责代码审查逻辑的编排器"""

    def __init__(
        self,
        project_root: Path,
        config: Optional[OrchestrationConfig] = None,
        agent_dispatcher: Optional[AgentDispatcher] = None,
        enable_issue_classification: bool = True
    ) -> None:
        super().__init__(project_root, config)
        self.agent_dispatcher = agent_dispatcher
        self.code_reviewer = None
        self.ralph_wiggum_loop = None

        # 初始化 Issue Classifier (P0 v3.2)
        self.issue_classifier = None
        self.issue_classification_enabled = (
            enable_issue_classification and
            ISSUE_CLASSIFIER_AVAILABLE
        )
        if self.issue_classification_enabled:
            self.issue_classifier = IssueClassifier(strict_mode=False)
            logger.info("ReviewOrchestrator: Issue Classifier 已启用")

        if REVIEW_AVAILABLE and self.config.enable_code_review:
            # 使用契约模型进行中转 (Phase 3 优化: 解耦)
            review_req = OrchestrationMapper.to_review_request("internal", [], self.config)

            review_config = ReviewConfig(
                enable_style_check=review_req.enable_style_check,
                enable_security_check=review_req.enable_security_check,
                enable_performance_check=review_req.enable_performance_check,
                enable_best_practices=review_req.enable_best_practices,
                enable_ralph_wiggum=review_req.enable_ralph_wiggum,
                min_overall_score=review_req.min_overall_score,
                max_critical_issues=self.config.max_critical_issues
            )
            self.code_reviewer = CodeReviewer(review_config)
            self.ralph_wiggum_loop = RalphWiggumLoop(self.code_reviewer, review_config)
            logger.info("代码审查编排器已初始化")

    async def run_review(
        self,
        project_id: str,
        executed_tasks: List[TaskExecution]
    ) -> Dict[str, Any]:
        """运行完整的代码审查流程"""
        if not self.code_reviewer:
            return {'status': 'disabled', 'message': '代码审查未启用或不可用'}

        # 1. 准备审查文件
        code_files, files_to_review = await self._prepare_review_files(executed_tasks)
        if not code_files:
            logger.info("没有找到需要审查的代码文件")
            return {'status': 'no_code', 'message': '没有找到需要审查的代码文件'}

        logger.info(f"开始审查 {len(code_files)} 个文件...")

        try:
            # 2. 执行审查 (支持 Ralph Wiggum 循环)
            if self.ralph_wiggum_loop and self.config.enable_ralph_wiggum:
                review_result = await self._run_ralph_wiggum_review(
                    project_id, files_to_review, code_files
                )
            else:
                review_result = await self.code_reviewer.review_code(
                    task_id=project_id,
                    files=files_to_review,
                    code_content=code_files
                )

            # 3. 构建结果摘要
            return self._build_summary(review_result)

        except (RuntimeError, ValueError, TimeoutError) as e:
            logger.error(f"代码审查执行阶段失败: {e}")
            return {'status': 'error', 'error': f"审查执行失败: {str(e)}"}
        except Exception as e:
            logger.exception(f"代码审查遇到非预期异常 ({type(e).__name__}): {e}")
            return {'status': 'error', 'error': f"系统非预期错误 ({type(e).__name__}): {str(e)}"}

    async def _prepare_review_files(
        self,
        executed_tasks: List[TaskExecution]
    ) -> tuple[Dict[str, str], List[Path]]:
        """准备待审查的文件内容和路径"""
        code_files = {}
        files_to_review = []
        read_tasks = []

        for task in executed_tasks:
            if task.status == TaskStatus.COMPLETED and task.result:
                if 'files' in task.result:
                    py_files = [f for f in task.result['files'] if f.endswith('.py')]
                    for file_path in py_files:
                        base_path = task.worktree_path or self.project_root
                        read_tasks.append((file_path, base_path))

        # 去重
        unique_reads = {}
        for rel, base in read_tasks:
            unique_reads[rel] = base

        # 并行读取
        read_results = await asyncio.gather(*[
            self._read_file_safe(rel, base) for rel, base in unique_reads.items()
        ])

        for read_result in read_results:
            if read_result:
                basename, content, full_path = read_result
                code_files[basename] = content
                files_to_review.append(full_path)

        return code_files, files_to_review

    async def _read_file_safe(self, file_rel_path: str, base_dir: Path):
        """安全读取文件内容"""
        full_path = base_dir / file_rel_path
        if not full_path.exists():
            fallback_path = self.project_root / file_rel_path
            if fallback_path.exists():
                full_path = fallback_path
            else:
                return None

        try:
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                return (os.path.basename(file_rel_path), content, full_path)
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"无法读取文件内容 {full_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"读取文件时遇到未知错误 ({type(e).__name__}) {full_path}: {e}")
            return None

    async def _run_ralph_wiggum_review(
        self,
        project_id: str,
        files: List[Path],
        code_content: Dict[str, str]
    ) -> ReviewResult:
        """执行带改进循环的审查"""
        logger.info("启用Ralph Wiggum迭代改进循环...")

        review_result = await self.ralph_wiggum_loop.review_with_loop(
            task_id=project_id,
            files=files,
            code_content=code_content,
            llm_callback=self._improvement_callback
        )

        # 应用改进后的代码到磁盘
        if review_result and review_result.improved_code:
            await self._apply_improvements(review_result.improved_code)

        # 如果循环未产生有效结果，回退到基础审查
        if review_result is None or review_result.metrics.overall_score == 0:
            review_result = await self.code_reviewer.review_code(
                task_id=project_id,
                files=files,
                code_content=code_content
            )

        return review_result

    async def _improvement_callback(
        self,
        current_code: Dict[str, str],
        improvements: List[Dict]
    ) -> Dict[str, str]:
        """改进回调函数 - 应用改进建议"""
        improved_code = current_code.copy()
        improvement_summary = "\n".join([f"- {imp.get('description')}" for imp in improvements])

        repair_tasks = []
        for filename, content in improved_code.items():
            repair_task = TaskExecution(
                task_id=f"repair-{filename}-{datetime.now().strftime('%H%M%S')}",
                step_id="repair",
                status=TaskStatus.PENDING,
                priority=ExecutionPriority.HIGH
            )
            repair_task.inputs = {
                "description": f"根据以下建议修复代码文件 {filename}:\n{improvement_summary}",
                "agent_type": AgentType.CODER.value,
                "file_path": filename,
                "current_content": content,
                "improvements": improvements
            }
            repair_tasks.append(repair_task)

        if not repair_tasks:
            return improved_code

        logger.info(f"正在并行修复 {len(repair_tasks)} 个文件...")

        batch_results = await self.agent_dispatcher.execute_batch(
            repair_tasks,
            max_parallel=self.config.max_parallel_tasks
        )

        for repair_result in batch_results:
            filename = repair_result.inputs.get("file_path")
            if repair_result.status == TaskStatus.COMPLETED and repair_result.result:
                result_data = repair_result.result
                if result_data.get('success') and 'improved_content' in result_data:
                    improved_code[filename] = result_data['improved_content']
                    logger.info(f"文件 {filename} 修复成功")
                else:
                    logger.warning(f"文件 {filename} 修复失败: {result_data.get('error')}")
            else:
                logger.warning(f"修复任务执行失败 ({filename}): {repair_result.error}")

        return improved_code

    async def _apply_improvements(self, improved_code: Dict[str, str]):
        """将改进后的代码写入磁盘"""
        logger.info("应用 Ralph Wiggum 改进后的代码到磁盘...")
        for filename, content in improved_code.items():
            try:
                file_path = self.project_root / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
                logger.info(f"应用改进成功: {filename}")
            except OSError as e:
                logger.error(f"应用改进失败 (IO错误) {filename}: {e}")
            except Exception as e:
                logger.error(f"应用改进遇到未知错误 ({type(e).__name__}) {filename}: {e}")

    def _build_summary(self, review_result: ReviewResult) -> Dict[str, Any]:
        """构建审查摘要 (Phase 3 优化: 使用 Mapper 解耦)"""
        response = OrchestrationMapper.from_review_result(review_result)

        summary = {
            'status': 'completed',
            'overall_score': response.score,
            'total_issues': len(response.issues),
            'summary': response.summary,
            'recommendations': response.recommendations,
            'meets_threshold': response.score >= self.config.min_overall_score,
            'ralph_wiggum_enabled': (
                self.ralph_wiggum_loop is not None and
                self.config.enable_ralph_wiggum
            ),
            # 保持一些内部字段兼容性
            'file_count': review_result.metrics.file_count,
            'total_lines': review_result.metrics.total_lines,
            'critical_count': review_result.metrics.critical_count,
            'major_count': review_result.metrics.major_count,
            'minor_count': review_result.metrics.minor_count,
        }

        logger.info(
            f"代码审查完成: 评分 {summary['overall_score']:.1f}/100, "
            f"发现问题 {summary['total_issues']}个"
        )

        return summary

    # ========== P0 v3.2: Issue Classifier 集成 ==========

    def classify_issues(self, issues: List[Any]) -> Dict[str, Any]:
        """分类代码审查问题

        Args:
            issues: CodeIssue 对象列表

        Returns:
            Dict: 分类结果
        """
        if not self.issue_classification_enabled or not self.issue_classifier:
            return {"enabled": False, "message": "Issue Classifier 未启用"}

        try:
            # 使用批量分类
            grouped_issues = self.issue_classifier.batch_classify(issues)

            # 生成摘要
            summary = self.issue_classifier.get_summary(issues)

            # 检查是否阻塞开发
            should_block = self.issue_classifier.should_block_progress(issues)

            return {
                "enabled": True,
                "grouped_issues": {
                    "P0_CRITICAL": len(grouped_issues.get(PriorityLevel.P0_CRITICAL, [])),
                    "P1_IMPORTANT": len(grouped_issues.get(PriorityLevel.P1_IMPORTANT, [])),
                    "P2_MINOR": len(grouped_issues.get(PriorityLevel.P2_MINOR, [])),
                    "P3_TRIVIAL": len(grouped_issues.get(PriorityLevel.P3_TRIVIAL, []))
                },
                "summary": summary,
                "should_block_development": should_block,
                "classification_history": self.issue_classifier.classification_history
            }
        except Exception as e:
            logger.error(f"问题分类失败: {e}")
            return {
                "enabled": True,
                "error": str(e),
                "grouped_issues": None,
                "should_block_development": False
            }

    def check_blocking_issues(self, issues: List[Any]) -> tuple[bool, List[Any]]:
        """检查是否有阻塞问题

        Args:
            issues: CodeIssue 对象列表

        Returns:
            tuple[bool, List[Any]]: (是否阻塞, P0 问题列表)
        """
        if not self.issue_classification_enabled or not self.issue_classifier:
            return False, []  # 未启用,不阻塞

        try:
            should_block = self.issue_classifier.should_block_progress(issues)

            if not should_block:
                return False, []

            # 提取 P0 问题
            p0_issues = []
            for issue in issues:
                result = self.issue_classifier.classify_issue(issue)
                if result.priority == PriorityLevel.P0_CRITICAL:
                    p0_issues.append({
                        "issue_id": issue.issue_id,
                        "title": issue.title,
                        "category": issue.category.value,
                        "severity": issue.severity.value,
                        "priority": "P0",
                        "reason": result.reason,
                        "suggested_action": result.suggested_action
                    })

            return True, p0_issues
        except Exception as e:
            logger.error(f"检查阻塞问题失败: {e}")
            return False, []

    def get_issue_priority_stats(self, issues: List[Any]) -> Dict[str, int]:
        """获取问题优先级统计

        Args:
            issues: CodeIssue 对象列表

        Returns:
            Dict[str, int]: 优先级统计
        """
        if not self.issue_classification_enabled or not self.issue_classifier:
            return {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "total": len(issues)}

        try:
            grouped = self.issue_classifier.batch_classify(issues)

            return {
                "P0": len(grouped.get(PriorityLevel.P0_CRITICAL, [])),
                "P1": len(grouped.get(PriorityLevel.P1_IMPORTANT, [])),
                "P2": len(grouped.get(PriorityLevel.P2_MINOR, [])),
                "P3": len(grouped.get(PriorityLevel.P3_TRIVIAL, [])),
                "total": len(issues)
            }
        except Exception as e:
            logger.error(f"获取优先级统计失败: {e}")
            return {"P0": 0, "P1": 0, "P2": 0, "P3": 0, "total": len(issues), "error": str(e)}

    def get_classification_summary(self) -> Dict[str, Any]:
        """获取分类摘要

        Returns:
            Dict: 分类摘要
        """
        if not self.issue_classification_enabled or not self.issue_classifier:
            return {"enabled": False}

        return {
            "enabled": True,
            "history_count": len(self.issue_classifier.classification_history),
            "recent_classifications": self.issue_classifier.classification_history[-10:]  # 最近 10 条
        }
