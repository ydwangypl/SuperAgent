#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码审查器

负责代码质量检查、问题识别、质量评估
"""

import re
import logging
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

# 确保 common 模块在路径中
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from common.exceptions import ReviewError

from .models import (
    ReviewSeverity,
    IssueCategory,
    ReviewStatus,
    CodeIssue,
    QualityMetrics,
    ReviewResult,
    ReviewConfig
)


logger = logging.getLogger(__name__)


class CodeReviewer:
    """代码审查器"""

    def __init__(self, config: Optional[ReviewConfig] = None):
        """初始化代码审查器

        Args:
            config: 审查配置
        """
        self.config = config or ReviewConfig()

    async def review_code(
        self,
        task_id: str,
        files: List[Path],
        code_content: Dict[str, str]
    ) -> ReviewResult:
        """审查代码 (异步版)

        Args:
            task_id: 任务ID
            files: 文件列表
            code_content: 文件内容映射 {filename: content}

        Returns:
            ReviewResult: 审查结果
        """
        import asyncio
        logger.info(f"开始审查任务 {task_id} 的代码")

        result = ReviewResult(
            review_id=f"review-{task_id}",
            task_id=task_id,
            status=ReviewStatus.IN_PROGRESS,
            metrics=QualityMetrics()
        )

        # 统计基本信息
        result.metrics.file_count = len(files)
        for file_path in files:
            # 兼容 Path 对象和字符串键
            content = code_content.get(file_path.name) or code_content.get(str(file_path))
            if content:
                lines = content.split('\n')
                result.metrics.total_lines += len(lines)
                result.metrics.code_lines += len([l for l in lines if l.strip() and not l.strip().startswith('#')])
                result.metrics.comment_lines += len([l for l in lines if l.strip().startswith('#')])
                result.metrics.blank_lines += len([l for l in lines if not l.strip()])

        # 执行各种检查 (使用线程池防止大型项目正则匹配阻塞事件循环)
        issues = []

        # 1. 代码风格检查
        if self.config.enable_style_check:
            style_issues = await asyncio.to_thread(self._check_style, code_content)
            issues.extend(style_issues)

        # 2. 安全检查
        if self.config.enable_security_check:
            security_issues = await asyncio.to_thread(self._check_security, code_content)
            issues.extend(security_issues)

        # 3. 性能检查
        if self.config.enable_performance_check:
            performance_issues = await asyncio.to_thread(self._check_performance, code_content)
            issues.extend(performance_issues)

        # 4. 最佳实践检查
        if self.config.enable_best_practices:
            practice_issues = await asyncio.to_thread(self._check_best_practices, code_content)
            issues.extend(practice_issues)

        result.issues = issues
        result.metrics.issue_count = len(issues)

        # 统计各级别问题
        for issue in issues:
            if issue.severity == ReviewSeverity.CRITICAL:
                result.metrics.critical_count += 1
            elif issue.severity == ReviewSeverity.MAJOR:
                result.metrics.major_count += 1
            elif issue.severity == ReviewSeverity.MINOR:
                result.metrics.minor_count += 1

        # 计算评分
        result.metrics.complexity_score = await asyncio.to_thread(self._calculate_complexity_score, code_content)
        result.metrics.maintainability_score = await asyncio.to_thread(self._calculate_maintainability, result.metrics)

        # 生成总结
        result.summary = self._generate_summary(result)
        result.recommendations = self._generate_recommendations(result)

        # 更新状态
        result.status = ReviewStatus.COMPLETED
        result.completed_at = result.started_at

        logger.info(
            f"审查完成: 发现 {len(issues)} 个问题, "
            f"综合评分: {result.metrics.overall_score:.1f}"
        )

        return result

    def _check_style(self, code_content: Dict[str, str]) -> List[CodeIssue]:
        """检查代码风格

        Args:
            code_content: 代码内容

        Returns:
            List[CodeIssue]: 风格问题列表
        """
        issues = []
        issue_id = 0

        for filename, content in code_content.items():
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                # 检查1: 行长度
                if len(line) > 100:
                    issues.append(CodeIssue(
                        issue_id=f"style-{issue_id}",
                        category=IssueCategory.CODE_STYLE,
                        severity=ReviewSeverity.MINOR,
                        title="行过长",
                        description=f"第{line_num}行长度为{len(line)},超过建议的100字符",
                        file_path=Path(filename),
                        line_number=line_num,
                        code_snippet=line.strip()[:50] + "...",
                        suggestion="将长行拆分为多行"
                    ))
                    issue_id += 1

                # 检查2: 命名规范(简单的snake_case检查)
                if re.search(r'def [A-Z]', line):
                    issues.append(CodeIssue(
                        issue_id=f"style-{issue_id}",
                        category=IssueCategory.CODE_STYLE,
                        severity=ReviewSeverity.MINOR,
                        title="函数命名不符合PEP8",
                        description=f"函数名应使用snake_case,而非PascalCase",
                        file_path=Path(filename),
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="使用snake_case命名函数"
                    ))
                    issue_id += 1

        return issues

    def _check_security(self, code_content: Dict[str, str]) -> List[CodeIssue]:
        """检查安全问题

        Args:
            code_content: 代码内容

        Returns:
            List[CodeIssue]: 安全问题列表
        """
        issues = []
        issue_id = 0

        # 安全模式
        security_patterns = {
            r'eval\(': "使用eval()可能存在代码注入风险",
            r'exec\(': "使用exec()可能存在代码注入风险",
            r'pickle\.loads': "反序列化可能存在安全风险",
            r'shell=True': "subprocess中使用shell=True可能存在命令注入风险",
            r'password.*=.*["\'].*["\']': "硬编码密码",
            r'api_key.*=.*["\'].*["\']': "硬编码API密钥",
        }

        for filename, content in code_content.items():
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                for pattern, message in security_patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append(CodeIssue(
                            issue_id=f"security-{issue_id}",
                            category=IssueCategory.SECURITY,
                            severity=ReviewSeverity.MAJOR,
                            title="潜在的安全问题",
                            description=message,
                            file_path=Path(filename),
                            line_number=line_num,
                            code_snippet=line.strip(),
                            suggestion="请参考安全最佳实践"
                        ))
                        issue_id += 1

        return issues

    def _check_performance(self, code_content: Dict[str, str]) -> List[CodeIssue]:
        """检查性能问题

        Args:
            code_content: 代码内容

        Returns:
            List[CodeIssue]: 性能问题列表
        """
        issues = []
        issue_id = 0

        performance_patterns = {
            r'for .* in .*\.keys\(\)': "使用.keys()进行遍历效率较低",
            r'for .* in range\(len\(.+\)\)': "使用range(len())进行遍历效率较低",
            r'\.\*\*': "使用深拷贝可能影响性能",
            r'list\(.*\.split\(\)\)': "不必要的list()转换",
        }

        for filename, content in code_content.items():
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                for pattern, message in performance_patterns.items():
                    if re.search(pattern, line):
                        issues.append(CodeIssue(
                            issue_id=f"perf-{issue_id}",
                            category=IssueCategory.PERFORMANCE,
                            severity=ReviewSeverity.MINOR,
                            title="性能优化建议",
                            description=message,
                            file_path=Path(filename),
                            line_number=line_num,
                            code_snippet=line.strip(),
                            suggestion="请参考Python性能优化最佳实践"
                        ))
                        issue_id += 1

        return issues

    def _check_best_practices(self, code_content: Dict[str, str]) -> List[CodeIssue]:
        """检查最佳实践

        Args:
            code_content: 代码内容

        Returns:
            List[CodeIssue]: 最佳实践问题列表
        """
        issues = []
        issue_id = 0

        # 最佳实践模式
        practice_patterns = {
            r'except:': "使用裸except可能掩盖异常",
            r'except\s+Exception': "捕获过于宽泛的Exception",
            r'global\s+\w+': "使用全局变量可能导致代码难以维护",
            r'class\s+\w+:\s*pass': "空类定义",
            r'def\s+\w+\(.*\):\s*pass': "空函数定义",
        }

        for filename, content in code_content.items():
            lines = content.split('\n')

            for line_num, line in enumerate(lines, 1):
                for pattern, message in practice_patterns.items():
                    if re.search(pattern, line):
                        issues.append(CodeIssue(
                            issue_id=f"practice-{issue_id}",
                            category=IssueCategory.BEST_PRACTICES,
                            severity=ReviewSeverity.MINOR,
                            title="最佳实践建议",
                            description=message,
                            file_path=Path(filename),
                            line_number=line_num,
                            code_snippet=line.strip(),
                            suggestion="请参考Python最佳实践"
                        ))
                        issue_id += 1

        return issues

    def _calculate_complexity_score(self, code_content: Dict[str, str]) -> float:
        """计算复杂度评分

        Args:
            code_content: 代码内容

        Returns:
            float: 复杂度评分(0-100)
        """
        # 简化的复杂度计算
        # 实际项目中应使用圈复杂度等指标
        total_lines = sum(len(c.split('\n')) for c in code_content.values())

        if total_lines == 0:
            return 100.0

        # 基于代码行数的简化评分
        # 假设100行代码=满分,超过则扣分
        base_score = 100.0
        penalty = max(0, total_lines - 100) * 0.5

        return max(0, base_score - penalty)

    def _calculate_maintainability(self, metrics: QualityMetrics) -> float:
        """计算可维护性评分

        Args:
            metrics: 质量指标

        Returns:
            float: 可维护性评分(0-100)
        """
        # 综合多个因素的可维护性评分
        scores = []

        # 1. 代码注释率(目标20%)
        if metrics.total_lines > 0:
            comment_ratio = metrics.comment_lines / metrics.total_lines
            comment_score = min(100, (comment_ratio / 0.20) * 100)
            scores.append(comment_score)

        # 2. 问题密度
        if metrics.total_lines > 0:
            issue_density = metrics.issue_count / metrics.total_lines
            issue_score = max(0, 100 - issue_density * 1000)
            scores.append(issue_score)

        # 3. 综合评分
        return sum(scores) / len(scores) if scores else 50.0

    def _generate_summary(self, result: ReviewResult) -> str:
        """生成审查总结

        Args:
            result: 审查结果

        Returns:
            str: 审查总结
        """
        lines = [
            f"代码审查完成",
            f"发现 {result.metrics.issue_count} 个问题",
        ]

        if result.metrics.critical_count > 0:
            lines.append(f"  - {result.metrics.critical_count} 个严重问题")
        if result.metrics.major_count > 0:
            lines.append(f"  - {result.metrics.major_count} 个主要问题")
        if result.metrics.minor_count > 0:
            lines.append(f"  - {result.metrics.minor_count} 个轻微问题")

        lines.append(f"综合评分: {result.metrics.overall_score:.1f}/100")

        return "\n".join(lines)

    def _generate_recommendations(self, result: ReviewResult) -> List[str]:
        """生成改进建议

        Args:
            result: 审查结果

        Returns:
            List[str]: 改进建议列表
        """
        recommendations = []

        # 基于评分生成建议
        if result.metrics.overall_score < 70:
            recommendations.append("综合评分较低,建议优先解决严重和主要问题")

        if result.metrics.critical_count > 0:
            recommendations.append(f"存在{result.metrics.critical_count}个严重问题,需要立即修复")

        if result.metrics.comment_lines / max(result.metrics.total_lines, 1) < 0.1:
            recommendations.append("代码注释率偏低,建议增加代码注释")

        if result.metrics.major_count > 5:
            recommendations.append("主要问题较多,建议分批次改进")

        return recommendations