#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
跨层级数据契约 (Data Contracts)

定义层级间通信的标准数据结构，减少直接的模型依赖。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from common.models import TaskStatus, AgentType

@dataclass
class TaskInput:
    """任务输入契约"""
    task_id: str
    step_id: str
    agent_type: AgentType
    description: str
    project_root: Path
    worktree_path: Optional[Path] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    context_data: Dict[str, Any] = field(default_factory=dict)
    token_monitor: Optional[Any] = None

@dataclass
class TaskOutput:
    """任务输出契约"""
    task_id: str
    success: bool
    status: TaskStatus
    message: str = ""
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReviewRequest:
    """审查请求契约"""
    project_id: str
    files: List[Path]
    enable_style_check: bool = True
    enable_security_check: bool = True
    enable_performance_check: bool = True
    enable_best_practices: bool = True
    enable_ralph_wiggum: bool = True
    max_iterations: int = 3
    min_overall_score: float = 70.0

@dataclass
class ReviewResponse:
    """审查响应契约"""
    success: bool
    score: float
    issues: List[Dict[str, Any]] = field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    improved_code: Optional[Dict[str, str]] = None
