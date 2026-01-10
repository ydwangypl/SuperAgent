#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
编排层数据模型

定义任务编排、执行状态、Agent调度相关的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from datetime import datetime
from pathlib import Path


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"           # 待执行
    READY = "ready"               # 就绪(依赖已满足)
    ASSIGNED = "assigned"         # 已分配给Agent
    RUNNING = "running"           # 执行中
    WAITING = "waiting"           # 等待中(等待依赖)
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消
    SKIPPED = "skipped"           # 已跳过


class ExecutionPriority(Enum):
    """执行优先级"""
    CRITICAL = "critical"         # 关键任务
    HIGH = "high"                 # 高优先级
    NORMAL = "normal"             # 普通优先级
    LOW = "low"                   # 低优先级


@dataclass
class ExecutionContext:
    """执行上下文"""
    project_root: Path                          # 项目根目录
    worktree_path: Optional[Path] = None        # Git worktree路径
    environment: Dict[str, str] = field(default_factory=dict)  # 环境变量
    dependencies: Dict[str, Any] = field(default_factory=dict)  # 依赖项
    metadata: Dict[str, Any] = field(default_factory=dict)      # 元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典"""
        return {
            "project_root": str(self.project_root),
            "worktree_path": str(self.worktree_path) if self.worktree_path else None,
            "environment": self.environment,
            "dependencies": self.dependencies,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionContext':
        """从字典重建对象"""
        if not data:
            return None
        
        # 转换路径
        project_root = Path(data["project_root"])
        worktree_path = Path(data["worktree_path"]) if data.get("worktree_path") else None
        
        return cls(
            project_root=project_root,
            worktree_path=worktree_path,
            environment=data.get("environment", {}),
            dependencies=data.get("dependencies", {}),
            metadata=data.get("metadata", {})
        )


@dataclass
class AgentAssignment:
    """Agent分配信息"""
    agent_type: str                              # Agent类型
    agent_id: str                                # Agent实例ID
    assigned_at: datetime                       # 分配时间
    worktree_path: Optional[Path] = None        # 分配的worktree路径
    estimated_duration: Optional[int] = None    # 预计耗时(分钟)

    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典"""
        return {
            "agent_type": self.agent_type,
            "agent_id": self.agent_id,
            "assigned_at": self.assigned_at.isoformat(),
            "worktree_path": str(self.worktree_path) if self.worktree_path else None,
            "estimated_duration": self.estimated_duration
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentAssignment':
        """从字典重建对象"""
        if not data:
            return None
            
        return cls(
            agent_type=data["agent_type"],
            agent_id=data["agent_id"],
            assigned_at=datetime.fromisoformat(data["assigned_at"]),
            worktree_path=Path(data["worktree_path"]) if data.get("worktree_path") else None,
            estimated_duration=data.get("estimated_duration")
        )


@dataclass
class TaskExecution:
    """任务执行记录"""
    task_id: str                                 # 任务ID
    step_id: str                                 # 步骤ID
    status: TaskStatus                          # 执行状态
    priority: ExecutionPriority = ExecutionPriority.NORMAL  # 优先级
    worktree_path: Optional[Path] = None        # 任务专用的 worktree 路径 (审计优化: 解决并行任务竞态)

    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Agent分配
    assignment: Optional[AgentAssignment] = None

    # 执行结果
    result: Optional[Dict[str, Any]] = None
    inputs: Dict[str, Any] = field(default_factory=dict)     # 任务输入数据
    outputs: Dict[str, Any] = field(default_factory=dict)    # 任务输出数据
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)

    # 依赖关系
    dependencies: List[str] = field(default_factory=list)    # 依赖的任务ID
    dependents: List[str] = field(default_factory=list)      # 依赖此任务的其他任务

    # 重试信息
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """转换为可序列化的字典"""
        return {
            "task_id": self.task_id,
            "step_id": self.step_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "worktree_path": str(self.worktree_path) if self.worktree_path else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "assignment": self.assignment.to_dict() if self.assignment else None,
            "result": self.result,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "error": self.error,
            "logs": self.logs,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskExecution':
        """从字典重建对象"""
        if not data:
            return None
            
        return cls(
            task_id=data["task_id"],
            step_id=data["step_id"],
            status=TaskStatus(data["status"]),
            priority=ExecutionPriority(data["priority"]),
            worktree_path=Path(data["worktree_path"]) if data.get("worktree_path") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            assignment=AgentAssignment.from_dict(data["assignment"]) if data.get("assignment") else None,
            result=data.get("result"),
            inputs=data.get("inputs", {}),
            outputs=data.get("outputs", {}),
            error=data.get("error"),
            logs=data.get("logs", []),
            dependencies=data.get("dependencies", []),
            dependents=data.get("dependents", []),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3)
        )


@dataclass
class WorktreeConfig:
    """Git Worktree配置"""
    main_branch: str = "main"                   # 主分支名称
    worktree_base: str = ".worktrees"           # worktree基础目录
    naming_pattern: str = "task-{task_id}"      # 命名模式

    # 配置选项
    auto_cleanup: bool = True                   # 自动清理
    force_prune: bool = False                   # 强制prune
    track_branches: bool = True                 # 跟踪分支


@dataclass
class OrchestrationState:
    """编排状态快照"""
    project_id: str                             # 项目ID
    total_tasks: int                            # 总任务数
    completed_tasks: int = 0                    # 已完成任务数
    failed_tasks: int = 0                       # 失败任务数
    running_tasks: int = 0                      # 运行中任务数
    pending_tasks: int = 0                      # 待执行任务数

    # 状态
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Worktree信息
    active_worktrees: List[str] = field(default_factory=list)

    # 性能指标
    total_duration: Optional[int] = None        # 总耗时(秒)
    average_task_duration: Optional[float] = None  # 平均任务耗时(秒)


@dataclass
class AgentResource:
    """Agent资源信息 (Phase 3 优化版)"""
    agent_type: str                             # Agent类型
    max_concurrent: int                         # 最大并发数
    current_load: int = 0                       # 当前负载
    available_instances: int = 0                # 可用实例数 (保留兼容性)

    # 性能统计
    total_executions: int = 0                   # 总执行次数
    successful_executions: int = 0              # 成功执行次数
    failed_executions: int = 0                  # 失败执行次数
    average_duration: Optional[float] = None    # 平均执行时长(秒)


@dataclass
class GitAutoCommitConfig:
    """Git 自动提交配置"""
    enabled: bool = True                        # 是否启用自动提交
    commit_message_template: str = "feat: {task_id} {description}"  # Commit message 模板
    auto_push: bool = False                     # 是否自动推送到远程
    auto_commit_tasks_json: bool = True         # 是否自动提交 tasks.json 更新


@dataclass
class SingleTaskConfig:
    """单任务焦点模式配置"""
    enabled: bool = True                        # 是否启用单任务焦点模式
    max_parallel_tasks: int = 1                 # 最大并行任务数(单任务模式通常为1)
    max_files_per_task: int = 5                 # 每个任务最多修改的文件数
    max_file_size_kb: int = 100                 # 单个文件最大大小(KB)
    force_incremental: bool = True              # 强制增量执行(一次只执行一个任务)
    enable_auto_split: bool = True              # 启用自动任务拆分


@dataclass
class OrchestrationConfig:
    """编排配置"""
    # 并发配置
    max_parallel_tasks: int = 3                 # 最大并行任务数
    max_concurrent_per_agent: int = 2           # 每个Agent最大并发数

    # 重试配置
    max_retries: int = 3                        # 最大重试次数
    retry_delay: int = 5                        # 重试延迟(秒)

    # 超时配置
    task_timeout: int = 3600                    # 任务超时(秒,默认1小时)
    total_timeout: int = 7200                   # 总超时(秒,默认2小时)

    # Worktree配置
    worktree: WorktreeConfig = field(default_factory=WorktreeConfig)

    # 资源配置
    agent_resources: Dict[str, AgentResource] = field(default_factory=dict)

    # 策略配置
    enable_parallel_execution: bool = True      # 启用并行执行
    enable_auto_retry: bool = True              # 启用自动重试
    enable_early_failure: bool = True           # 启用快速失败(有任务失败时停止)

    # 代码审查配置
    enable_code_review: bool = True             # 启用代码审查
    enable_style_check: bool = True             # 启用代码风格检查
    enable_security_check: bool = True          # 启用安全检查
    enable_performance_check: bool = True       # 启用性能检查
    enable_best_practices: bool = True          # 启用最佳实践检查
    enable_ralph_wiggum: bool = True            # ✅ 启用 Ralph Wiggum 迭代改进
    min_overall_score: float = 70.0             # 最低综合评分要求
    max_critical_issues: int = 0                # 最大严重问题数(0为不允许)

    # Git 自动提交配置
    git_auto_commit: GitAutoCommitConfig = field(default_factory=GitAutoCommitConfig)

    # 单任务焦点模式配置
    single_task_mode: SingleTaskConfig = field(default_factory=SingleTaskConfig)


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool                               # 是否成功
    project_id: str                             # 项目ID
    total_tasks: int                            # 总任务数
    completed_tasks: int                        # 完成任务数
    failed_tasks: int                           # 失败任务数
    skipped_tasks: int = 0                      # 跳过任务数

    # 时间信息
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime = field(default_factory=datetime.now)

    # 详细信息
    task_executions: List[TaskExecution] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)  # 生成的文件和资源

    # 代码审查结果
    code_review_summary: Optional[Dict[str, Any]] = None     # 代码审查摘要

    # 错误信息
    errors: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> int:
        """计算执行时长(秒)"""
        return int((self.completed_at - self.started_at).total_seconds())

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_tasks == 0:
            return 0.0
        return self.completed_tasks / self.total_tasks
