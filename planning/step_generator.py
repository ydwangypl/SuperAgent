#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
步骤生成器

根据需求分析生成执行步骤
"""

import re
from typing import List, Dict, Any
from datetime import timedelta

from .models import (
    Step, StepStatus, AgentType, RequirementAnalysis, Requirements
)


class StepGenerator:
    """步骤生成器"""

    def __init__(self):
        self.step_counter = 0

    def generate_steps(
        self,
        requirements: Requirements,
        analysis: RequirementAnalysis
    ) -> List[Step]:
        """生成执行步骤

        Args:
            requirements: 需求
            analysis: 需求分析

        Returns:
            List[Step]: 步骤列表
        """
        self.step_counter = 0
        
        # 审计优化: 如果意图中有建议的步骤, 则基于建议步骤生成
        if requirements.intent and requirements.intent.suggested_steps:
            return self._generate_from_suggestions(requirements, analysis)
            
        # 兜底逻辑: 基于特征分析生成硬编码步骤
        return self._generate_from_analysis(requirements, analysis)

    def _generate_from_suggestions(
        self,
        requirements: Requirements,
        analysis: RequirementAnalysis
    ) -> List[Step]:
        """基于意图建议生成步骤"""
        steps = []
        suggestions = requirements.intent.suggested_steps
        agent_types = requirements.intent.agent_types or []
        
        for i, task_name in enumerate(suggestions):
            self.step_counter += 1
            
            # 尝试匹配合适的 Agent 类型
            # 简单的启发式匹配: 如果建议名称包含特定词汇
            agent_type = self._map_task_to_agent(task_name, agent_types)
            
            step = Step(
                id=f"step{self.step_counter}",
                name=task_name,
                description=f"执行任务: {task_name}",
                agent_type=agent_type,
                inputs={
                    "user_input": requirements.user_input,
                    "context": requirements.clarifications
                },
                dependencies=[f"step{i}"] if i > 0 else [],
                can_parallel=False,
                estimated_time=timedelta(minutes=10),
                status=StepStatus.PENDING
            )
            steps.append(step)
            
        return steps

    def _map_task_to_agent(self, task_name: str, recommended_agents: List[AgentType]) -> AgentType:
        """根据任务名称映射 Agent 类型"""
        name_lower = task_name.lower()
        
        if any(kw in name_lower for kw in ["需求", "分析", "prd", "规划"]):
            return AgentType.PRODUCT_MANAGEMENT
        if any(kw in name_lower for kw in ["数据库", "表", "存储", "sql", "schema"]):
            return AgentType.DATABASE_DESIGN
        if any(kw in name_lower for kw in ["前端", "ui", "界面", "页面"]):
            return AgentType.FRONTEND_DEV
        if any(kw in name_lower for kw in ["后端", "接口", "api", "服务端"]):
            return AgentType.BACKEND_DEV
        if any(kw in name_lower for kw in ["测试", "qa", "质量"]):
            return AgentType.QA_ENGINEERING
        if any(kw in name_lower for kw in ["部署", "运维", "docker", "ci"]):
            return AgentType.DEVOPS_ENGINEERING
            
        # 如果有推荐列表, 返回第一个
        if recommended_agents:
            return recommended_agents[0]
            
        return AgentType.BACKEND_DEV  # 默认

    def _generate_from_analysis(
        self,
        requirements: Requirements,
        analysis: RequirementAnalysis
    ) -> List[Step]:
        """原有的基于分析的步骤生成逻辑"""
        steps = []
        
        if analysis.has_product_requirements:
            steps.append(self._create_product_step(requirements))
            
        if analysis.has_database:
            steps.append(self._create_database_step(requirements))
            
        if analysis.has_backend:
            steps.append(self._create_backend_step(requirements))
            
        if analysis.has_frontend:
            steps.append(self._create_frontend_step(requirements))
            
        if analysis.has_backend or analysis.has_frontend:
            steps.append(self._create_testing_step(requirements))
            
        return steps

    def _create_product_step(self, requirements: Requirements) -> Step:
        """创建产品需求分析步骤"""
        self.step_counter += 1
        return Step(
            id=f"step{self.step_counter}",
            name="产品需求分析",
            description="生成PRD文档、用户故事、功能列表",
            agent_type=AgentType.PRODUCT_MANAGEMENT,
            inputs={
                "user_input": requirements.user_input,
                "clarifications": requirements.clarifications
            },
            dependencies=[],  # 第一步没有依赖
            can_parallel=False,
            estimated_time=timedelta(minutes=5),
            status=StepStatus.PENDING
        )

    def _create_database_step(self, requirements: Requirements) -> Step:
        """创建数据库设计步骤"""
        self.step_counter += 1
        return Step(
            id=f"step{self.step_counter}",
            name="数据库设计",
            description="设计数据表结构、关系、索引",
            agent_type=AgentType.DATABASE_DESIGN,
            inputs={
                "user_input": requirements.user_input,
                "features": requirements.features
            },
            dependencies=["step1"],  # 依赖产品需求
            can_parallel=False,
            estimated_time=timedelta(minutes=8),
            status=StepStatus.PENDING
        )

    def _create_backend_step(self, requirements: Requirements) -> Step:
        """创建后端开发步骤"""
        self.step_counter += 1
        return Step(
            id=f"step{self.step_counter}",
            name="后端API开发",
            description="设计和实现RESTful API",
            agent_type=AgentType.BACKEND_DEV,
            inputs={
                "user_input": requirements.user_input,
                "features": requirements.features,
                "has_auth": requirements.clarifications.get("needs_auth", False)
            },
            dependencies=["step2"] if self._needs_database(requirements) else ["step1"],
            can_parallel=False,
            estimated_time=timedelta(minutes=15),
            status=StepStatus.PENDING
        )

    def _create_frontend_step(self, requirements: Requirements) -> Step:
        """创建前端开发步骤"""
        self.step_counter += 1
        return Step(
            id=f"step{self.step_counter}",
            name="前端界面开发",
            description="设计和实现用户界面",
            agent_type=AgentType.FRONTEND_DEV,
            inputs={
                "user_input": requirements.user_input,
                "features": requirements.features
            },
            dependencies=["step3"],  # 依赖后端API
            can_parallel=True,  # 可以与测试并行
            estimated_time=timedelta(minutes=12),
            status=StepStatus.PENDING
        )

    def _create_testing_step(self, requirements: Requirements) -> Step:
        """创建测试步骤"""
        self.step_counter += 1
        return Step(
            id=f"step{self.step_counter}",
            name="测试用例编写",
            description="编写单元测试和集成测试",
            agent_type=AgentType.QA_ENGINEERING,
            inputs={
                "user_input": requirements.user_input,
                "features": requirements.features
            },
            dependencies=["step3", "step4"],  # 依赖后端和前端
            can_parallel=False,
            estimated_time=timedelta(minutes=10),
            status=StepStatus.PENDING
        )

    def _needs_database(self, requirements: Requirements) -> bool:
        """判断是否需要数据库"""
        # 关键词检查
        db_keywords = ["数据库", "database", "mysql", "postgres", "mongodb"]
        for keyword in db_keywords:
            if keyword in requirements.user_input.lower():
                return True

        # 业务对象检查
        business_objects = ["用户", "文章", "商品", "订单", "评论"]
        for obj in business_objects:
            if obj in requirements.user_input:
                return True

        return False
