#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
规划层数据模型

定义规划相关的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING
from datetime import timedelta
import logging

from common.models import StepStatus, AgentType

if TYPE_CHECKING:
    from conversation.models import Intent

logger = logging.getLogger(__name__)


@dataclass
class Requirements:
    """需求定义"""
    user_input: str                        # 用户原始输入
    clarifications: Dict[str, Any] = field(default_factory=dict)         # 澄清后的信息
    intent: Optional['Intent'] = None      # 意图识别结果 (审计优化: 保持意图数据流一致性)
    constraints: List[str] = field(default_factory=list)       # 约束条件
    preferences: Dict[str, Any] = field(default_factory=dict)  # 偏好设置
    features: List[str] = field(default_factory=list)         # 功能列表


@dataclass
class Step:
    """执行步骤"""
    id: str                                # 步骤ID
    name: str                              # 步骤名称
    description: str                       # 步骤描述
    agent_type: AgentType                  # 负责的Agent类型
    inputs: Dict[str, Any] = field(default_factory=dict)      # 输入参数
    dependencies: List[str] = field(default_factory=list)     # 依赖的步骤ID列表
    can_parallel: bool = False             # 是否可并行执行
    estimated_time: timedelta = timedelta(minutes=3)         # 预计耗时 (默认 3 分钟,符合粒度验证要求)
    status: StepStatus = StepStatus.PENDING                    # 状态
    outputs: Dict[str, Any] = field(default_factory=dict)     # 输出结果


@dataclass
class DependencyNode:
    """依赖图节点"""
    step_id: str                           # 步骤ID
    dependencies: Set[str] = field(default_factory=set)       # 依赖的步骤ID集合
    dependents: Set[str] = field(default_factory=set)         # 依赖此步骤的其他步骤


@dataclass
class DependencyGraph:
    """依赖关系图"""
    nodes: Dict[str, DependencyNode] = field(default_factory=dict)  # 所有节点

    def add_step(self, step: Step):
        """添加步骤到依赖图"""
        node = DependencyNode(
            step_id=step.id,
            dependencies=set(step.dependencies)
        )
        self.nodes[step.id] = node

        # 更新其他节点的依赖关系
        for dep_id in step.dependencies:
            if dep_id in self.nodes:
                self.nodes[dep_id].dependents.add(step.id)

    def get_ready_steps(self, completed_steps: Optional[Set[str]] = None) -> List[str]:
        """获取所有就绪的步骤(依赖已满足)

        Args:
            completed_steps: 已完成的步骤ID集合
        """
        completed_steps = completed_steps or set()
        ready = []
        for step_id, node in self.nodes.items():
            if step_id in completed_steps:
                continue
            # 所有依赖都已在已完成列表中
            if all(dep in completed_steps for dep in node.dependencies):
                ready.append(step_id)
        return ready

    def get_parallel_groups(self) -> List[List[str]]:
        """使用分层拓扑排序获取可并行的步骤组

        Returns:
            List[List[str]]: 每一层是可以并行的步骤ID列表
        """
        groups = []
        completed = set()
        remaining = set(self.nodes.keys())
        while remaining:
            ready = self.get_ready_steps(completed)
            if not ready:
                break
            groups.append(ready)
            completed.update(ready)
            remaining.difference_update(ready)
        return groups

    def can_execute_parallel(self, step_ids: List[str]) -> bool:
        """检查一组步骤是否可以并行执行

        Args:
            step_ids: 步骤ID列表

        Returns:
            bool: True表示可以并行执行(互不依赖)
        """
        step_set = set(step_ids)
        for step_id in step_ids:
            if step_id not in self.nodes:
                continue

            node = self.nodes[step_id]
            # 如果该步骤依赖于列表中的任何其他步骤,则不能并行
            if any(dep in step_set for dep in node.dependencies):
                return False

        return True


@dataclass
class RequirementAnalysis:
    """需求分析结果"""
    has_product_requirements: bool = False     # 是否有产品需求
    has_database: bool = False                 # 是否需要数据库
    has_backend: bool = False                  # 是否需要后端
    has_frontend: bool = False                 # 是否需要前端
    has_api: bool = False                      # 是否需要API
    has_auth: bool = False                     # 是否需要认证
    has_testing: bool = True                   # 是否需要测试(默认需要)
    project_type: str = ""                     # 项目类型
    tech_stack: str = ""                       # 技术栈
    complexity: str = "medium"                 # 复杂度(low/medium/high)


@dataclass
class RiskReport:
    """风险评估报告"""
    overall_risk: str = "low"                  # 整体风险等级
    risks: List[str] = field(default_factory=list)  # 风险列表
    mitigations: Dict[str, str] = field(default_factory=dict)  # 缓解措施


@dataclass
class ExecutionPlan:
    """执行计划"""
    requirements: Requirements                # 需求
    steps: List[Step]                          # 执行步骤列表
    dependencies: DependencyGraph              # 依赖关系图
    analysis: RequirementAnalysis              # 需求分析
    estimated_time: timedelta = timedelta(hours=1)  # 总预计时间
    risk_report: RiskReport = field(default_factory=RiskReport)  # 风险评估

    @property
    def description(self) -> str:
        """获取计划描述 (审计优化: 适配编排层调用)"""
        return self.requirements.user_input

    def get_step_by_id(self, step_id: str) -> Optional[Step]:
        """根据ID获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_parallel_groups(self) -> List[List[Step]]:
        """获取可并行的步骤组 (分层执行)"""
        id_groups = self.dependencies.get_parallel_groups()
        step_map = {s.id: s for s in self.steps}

        result = []
        for group in id_groups:
            result.append([step_map[sid] for sid in group if sid in step_map])

        return result
