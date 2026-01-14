#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
执行层数据模型

定义Agent执行相关的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from datetime import datetime
from pathlib import Path


class AgentCapability(Enum):
    """Agent能力枚举"""
    CODE_GENERATION = "code_generation"       # 代码生成
    CODE_REFACTORING = "code_refactoring"     # 代码重构
    TEST_GENERATION = "test_generation"       # 测试生成
    DOCUMENTATION = "documentation"           # 文档生成
    DEBUGGING = "debugging"                   # 调试
    CODE_REVIEW = "code_review"               # 代码审查
    ARCHITECTURE = "architecture"             # 架构设计
    OPTIMIZATION = "optimization"             # 性能优化


class AgentStatus(Enum):
    """Agent执行状态"""
    IDLE = "idle"                             # 空闲
    THINKING = "thinking"                     # 思考中
    WORKING = "working"                       # 工作中
    REVIEWING = "reviewing"                   # 审查中
    COMPLETED = "completed"                   # 已完成
    FAILED = "failed"                         # 失败
    BLOCKED = "blocked"                       # 被阻塞


@dataclass
class AgentContext:
    """Agent执行上下文"""
    project_root: Path                        # 项目根目录
    task_id: str                              # 任务ID
    step_id: str                              # 步骤ID

    # 执行环境
    worktree_path: Optional[Path] = None      # Git worktree路径
    environment: Dict[str, str] = field(default_factory=dict)  # 环境变量

    # 相关信息
    dependencies: List[str] = field(default_factory=list)      # 依赖的任务ID
    previous_results: Dict[str, Any] = field(default_factory=dict)  # 前置任务结果

    # 项目上下文
    project_type: Optional[str] = None        # 项目类型
    tech_stack: List[str] = field(default_factory=list)        # 技术栈
    requirements: Dict[str, Any] = field(default_factory=dict)  # 需求信息
    
    # 监控相关 (Phase 3 优化)
    token_monitor: Optional[Any] = None       # Token 监控器


@dataclass
class AgentConfig:
    """Agent配置"""
    # 超时配置
    timeout: int = 3600                       # 超时时间(秒,默认1小时)

    # 重试配置
    max_retries: int = 3                      # 最大重试次数
    retry_delay: int = 5                      # 重试延迟(秒)

    # 输出配置
    output_dir: Optional[Path] = None         # 输出目录
    save_intermediate: bool = False           # 保存中间结果

    # 质量配置
    enable_auto_review: bool = True           # 启用自动审查
    min_quality_score: float = 70.0           # 最低质量评分

    # 特定配置
    custom_config: Dict[str, Any] = field(default_factory=dict)  # 自定义配置


@dataclass
class Artifact:
    """生成的文件或资源"""
    artifact_id: str                           # 工件ID
    artifact_type: str                         # 工件类型(file, code, test, doc等)
    path: Optional[Path] = None               # 文件路径
    content: Optional[str] = None             # 文件内容
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据

    # 质量信息
    quality_score: Optional[float] = None     # 质量评分
    issues: List[str] = field(default_factory=list)  # 问题列表

    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AgentResult:
    """Agent执行结果"""
    agent_id: str                             # Agent ID
    task_id: str                              # 任务ID
    step_id: str                              # 步骤ID
    status: AgentStatus                       # 执行状态

    # 时间信息
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0             # 执行时长(秒)

    # 执行结果
    success: bool = False                     # 是否成功
    message: str = ""                         # 执行消息
    artifacts: List[Artifact] = field(default_factory=list)  # 生成的工件

    # 详细信息
    logs: List[str] = field(default_factory=list)           # 执行日志
    steps: List[Dict[str, Any]] = field(default_factory=list) # 执行步骤 (Phase 3 优化)
    metrics: Dict[str, Any] = field(default_factory=dict)  # 执行指标
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据

    # 错误信息
    error: Optional[str] = None               # 错误消息
    error_details: Optional[Dict[str, Any]] = None  # 错误详情

    @property
    def file_count(self) -> int:
        """生成的文件数量"""
        return len([a for a in self.artifacts if a.artifact_type == "file"])

    @property
    def code_lines(self) -> int:
        """生成的代码行数"""
        total = 0
        for artifact in self.artifacts:
            if artifact.content:
                total += len(artifact.content.split('\n'))
        return total

    @property
    def quality_score(self) -> Optional[float]:
        """平均质量评分"""
        scores = [a.quality_score for a in self.artifacts if a.quality_score is not None]
        return sum(scores) / len(scores) if scores else None


@dataclass
class AgentThought:
    """Agent思考过程"""
    step: int                                  # 思考步骤
    thought: str                              # 思考内容
    action: Optional[str] = None              # 计划采取的行动
    observation: Optional[str] = None         # 观察结果
    timestamp: datetime = field(default_factory=datetime.now)
