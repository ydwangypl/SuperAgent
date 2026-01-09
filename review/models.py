#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代码审查层数据模型

定义代码审查相关的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from pathlib import Path


class ReviewSeverity(Enum):
    """审查问题严重程度"""
    INFO = "info"           # 信息提示
    MINOR = "minor"         # 轻微问题
    MAJOR = "major"         # 主要问题
    CRITICAL = "critical"   # 严重问题
    BLOCKER = "blocker"     # 阻塞问题


class IssueCategory(Enum):
    """问题分类"""
    CODE_STYLE = "code_style"           # 代码风格
    BEST_PRACTICES = "best_practices"   # 最佳实践
    PERFORMANCE = "performance"         # 性能问题
    SECURITY = "security"              # 安全问题
    ERROR_HANDLING = "error_handling"  # 错误处理
    DOCUMENTATION = "documentation"    # 文档问题
    TESTING = "testing"                # 测试问题
    ARCHITECTURE = "architecture"      # 架构问题


class ReviewStatus(Enum):
    """审查状态"""
    PENDING = "pending"       # 待审查
    IN_PROGRESS = "in_progress"  # 审查中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败


@dataclass
class CodeIssue:
    """代码问题"""
    issue_id: str                              # 问题ID
    category: IssueCategory                     # 问题分类
    severity: ReviewSeverity                    # 严重程度
    title: str                                  # 问题标题
    description: str                            # 问题描述
    file_path: Optional[Path] = None           # 文件路径
    line_number: Optional[int] = None          # 行号
    code_snippet: Optional[str] = None         # 代码片段
    suggestion: Optional[str] = None            # 修改建议

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False                      # 是否已解决
    resolution: Optional[str] = None            # 解决方案


@dataclass
class QualityMetrics:
    """代码质量指标"""
    file_count: int = 0                        # 文件数量
    total_lines: int = 0                       # 总行数
    code_lines: int = 0                         # 代码行数
    comment_lines: int = 0                      # 注释行数
    blank_lines: int = 0                        # 空行数

    # 质量评分
    complexity_score: float = 0.0              # 复杂度评分(0-100)
    maintainability_score: float = 0.0         # 可维护性评分(0-100)
    test_coverage: float = 0.0                  # 测试覆盖率(0-100)

    # 问题统计
    issue_count: int = 0                       # 问题总数
    critical_count: int = 0                     # 严重问题数
    major_count: int = 0                        # 主要问题数
    minor_count: int = 0                        # 轻微问题数

    @property
    def overall_score(self) -> float:
        """综合评分"""
        if self.issue_count == 0:
            return 100.0

        # 根据问题严重程度计算
        penalty = (
            self.critical_count * 20 +
            self.major_count * 10 +
            self.minor_count * 2
        )

        score = max(0, 100 - penalty)
        return score


@dataclass
class ReviewResult:
    """审查结果"""
    review_id: str                             # 审查ID
    task_id: str                                # 关联的任务ID
    status: ReviewStatus                        # 审查状态
    metrics: QualityMetrics                     # 质量指标
    issues: List[CodeIssue] = field(default_factory=list)  # 问题列表

    # 时间信息
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # 审查总结
    summary: str = ""                            # 审查总结
    recommendations: List[str] = field(default_factory=list)  # 改进建议

    # Ralph Wiggum循环
    iteration_count: int = 0                    # 迭代次数
    max_iterations: int = 3                     # 最大迭代次数
    improved_code: Optional[Dict[str, str]] = None  # 最终改进后的代码 (文件名 -> 内容)

    @property
    def duration(self) -> float:
        """审查时长(秒)"""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0

    @property
    def has_critical_issues(self) -> bool:
        """是否有严重问题"""
        return any(
            issue.severity in [ReviewSeverity.CRITICAL, ReviewSeverity.BLOCKER]
            for issue in self.issues
        )


@dataclass
class ReviewConfig:
    """审查配置"""
    enable_style_check: bool = True             # 启用风格检查
    enable_security_check: bool = True          # 启用安全检查
    enable_performance_check: bool = True       # 启用性能检查
    enable_best_practices: bool = True          # 启用最佳实践检查

    # Ralph Wiggum配置
    enable_ralph_wiggum: bool = True            # 启用Ralph Wiggum循环
    max_iterations: int = 3                      # 最大迭代次数
    improvement_threshold: float = 0.1           # 改进阈值(10%)

    # 质量阈值
    min_overall_score: float = 70.0             # 最低综合评分
    max_critical_issues: int = 0                # 最大严重问题数

    # 审查规则
    check_patterns: Dict[str, List[str]] = field(default_factory=dict)  # 检查模式
    exclude_patterns: List[str] = field(default_factory=list)  # 排除模式