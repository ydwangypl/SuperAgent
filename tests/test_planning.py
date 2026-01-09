#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
规划层单元测试
"""

import unittest
import asyncio
from datetime import timedelta

from planning.planner import ProjectPlanner
from planning.step_generator import StepGenerator
from planning.dependency_analyzer import DependencyAnalyzer
from planning.models import (
    Requirements, Step, StepStatus, AgentType,
    DependencyGraph, RequirementAnalysis, RiskReport
)


class TestProjectPlanner(unittest.TestCase):
    """项目规划器测试套件"""

    def setUp(self):
        """测试前准备"""
        self.planner = ProjectPlanner()

    async def test_create_plan_blog(self):
        """测试创建博客系统计划"""
        user_input = "我想开发一个博客系统"
        context = {}

        plan = await self.planner.create_plan(user_input, context)

        self.assertIsNotNone(plan)
        self.assertGreater(len(plan.steps), 0)
        self.assertEqual(plan.analysis.project_type, "blog")
        self.assertIn("博客", plan.requirements.user_input)

    async def test_create_plan_ecommerce(self):
        """测试创建电商网站计划"""
        user_input = "开发一个电商网站"
        context = {}

        plan = await self.planner.create_plan(user_input, context)

        self.assertEqual(plan.analysis.project_type, "ecommerce")
        self.assertTrue(plan.analysis.has_auth)

    async def test_format_plan(self):
        """测试格式化计划"""
        user_input = "开发一个API服务"
        context = {}

        plan = await self.planner.create_plan(user_input, context)
        formatted = self.planner.format_plan(plan)

        self.assertIn("项目执行计划", formatted)
        self.assertIn("需求概述", formatted)
        self.assertIn("执行步骤", formatted)


class TestStepGenerator(unittest.TestCase):
    """步骤生成器测试套件"""

    def setUp(self):
        """测试前准备"""
        self.generator = StepGenerator()

    def test_generate_steps_blog(self):
        """测试生成博客系统步骤"""
        requirements = Requirements(
            user_input="我想开发一个博客系统",
            clarifications={},
            features=["文章管理", "评论功能"]
        )

        analysis = RequirementAnalysis(
            project_type="blog",
            has_product_requirements=True,
            has_database=True,
            has_backend=True,
            has_frontend=True
        )

        steps = self.generator.generate_steps(requirements, analysis)

        self.assertEqual(len(steps), 5)  # 5个标准步骤
        self.assertEqual(steps[0].name, "产品需求分析")
        self.assertEqual(steps[1].name, "数据库设计")
        self.assertEqual(steps[2].name, "后端API开发")
        self.assertEqual(steps[3].name, "前端界面开发")
        self.assertEqual(steps[4].name, "测试用例编写")

    def test_step_dependencies(self):
        """测试步骤依赖关系"""
        requirements = Requirements(
            user_input="开发一个带数据库的博客系统",  # 添加"数据库"关键词以触发数据库需求
            clarifications={},
            features=[]
        )

        analysis = RequirementAnalysis(
            project_type="blog",
            has_product_requirements=True,
            has_database=True,
            has_backend=True,
            has_frontend=True
        )

        steps = self.generator.generate_steps(requirements, analysis)

        # 第一步没有依赖
        self.assertEqual(len(steps[0].dependencies), 0)

        # 第二步依赖第一步
        self.assertIn("step1", steps[1].dependencies)

        # 第三步依赖第二步(后端依赖数据库)
        self.assertIn("step2", steps[2].dependencies)

    def test_step_can_parallel(self):
        """测试步骤并行标识"""
        requirements = Requirements(
            user_input="开发一个博客",
            clarifications={},
            features=[]
        )

        analysis = RequirementAnalysis(
            project_type="blog",
            has_product_requirements=True,
            has_database=True,
            has_backend=True,
            has_frontend=True
        )

        steps = self.generator.generate_steps(requirements, analysis)

        # 前端开发可以并行
        frontend_step = [s for s in steps if s.name == "前端界面开发"][0]
        self.assertTrue(frontend_step.can_parallel)

    def test_step_time_estimation(self):
        """测试时间估算"""
        requirements = Requirements(
            user_input="开发一个博客",
            clarifications={},
            features=[]
        )

        analysis = RequirementAnalysis(
            project_type="blog",
            has_product_requirements=True,
            has_database=True,
            has_backend=True,
            has_frontend=True
        )

        steps = self.generator.generate_steps(requirements, analysis)

        # 总时间应该大于0
        total_seconds = sum(s.estimated_time.total_seconds() for s in steps)
        self.assertGreater(total_seconds, 0)


class TestDependencyAnalyzer(unittest.TestCase):
    """依赖分析器测试套件"""

    def setUp(self):
        """测试前准备"""
        self.analyzer = DependencyAnalyzer()

    def test_build_dependency_graph(self):
        """测试构建依赖图"""
        steps = [
            Step(
                id="step1",
                name="步骤1",
                description="测试",
                agent_type=AgentType.PRODUCT_MANAGEMENT,
                dependencies=[]
            ),
            Step(
                id="step2",
                name="步骤2",
                description="测试",
                agent_type=AgentType.DATABASE_DESIGN,
                dependencies=["step1"]
            )
        ]

        analysis = RequirementAnalysis()
        graph = self.analyzer.analyze_dependencies(steps, analysis)

        self.assertEqual(len(graph.nodes), 2)
        self.assertIn("step1", graph.nodes)
        self.assertIn("step2", graph.nodes)

    def test_get_ready_steps(self):
        """测试获取就绪步骤"""
        steps = [
            Step(
                id="step1",
                name="步骤1",
                description="测试",
                agent_type=AgentType.PRODUCT_MANAGEMENT,
                dependencies=[]
            ),
            Step(
                id="step2",
                name="步骤2",
                description="测试",
                agent_type=AgentType.DATABASE_DESIGN,
                dependencies=["step1"]
            )
        ]

        analysis = RequirementAnalysis()
        graph = self.analyzer.analyze_dependencies(steps, analysis)

        ready = graph.get_ready_steps()
        self.assertIn("step1", ready)
        self.assertNotIn("step2", ready)

    def test_can_execute_parallel(self):
        """测试并行执行判断"""
        graph = DependencyGraph()

        # 添加3个独立步骤
        for i in range(1, 4):
            step = Step(
                id=f"step{i}",
                name=f"步骤{i}",
                description="测试",
                agent_type=AgentType.PRODUCT_MANAGEMENT,
                dependencies=[]
            )
            graph.add_step(step)

        # 应该可以并行
        can_parallel = graph.can_execute_parallel(["step1", "step2", "step3"])
        self.assertTrue(can_parallel)

    def test_get_execution_order(self):
        """测试获取执行顺序"""
        steps = [
            Step(
                id="step1",
                name="步骤1",
                description="测试",
                agent_type=AgentType.PRODUCT_MANAGEMENT,
                dependencies=[]
            ),
            Step(
                id="step2",
                name="步骤2",
                description="测试",
                agent_type=AgentType.DATABASE_DESIGN,
                dependencies=["step1"]
            ),
            Step(
                id="step3",
                name="步骤3",
                description="测试",
                agent_type=AgentType.BACKEND_DEV,
                dependencies=["step2"]
            )
        ]

        analysis = RequirementAnalysis()
        graph = self.analyzer.analyze_dependencies(steps, analysis)

        order = self.analyzer.get_execution_order(graph)

        # 应该有3个执行组(都是串行)
        self.assertEqual(len(order), 3)
        self.assertEqual(order[0], ["step1"])
        self.assertEqual(order[1], ["step2"])
        self.assertEqual(order[2], ["step3"])

    def test_estimate_critical_path(self):
        """测试关键路径估算"""
        steps = [
            Step(
                id="step1",
                name="步骤1",
                description="测试",
                agent_type=AgentType.PRODUCT_MANAGEMENT,
                dependencies=[],
                estimated_time=timedelta(minutes=5)
            ),
            Step(
                id="step2",
                name="步骤2",
                description="测试",
                agent_type=AgentType.DATABASE_DESIGN,
                dependencies=["step1"],
                estimated_time=timedelta(minutes=10)
            )
        ]

        analysis = RequirementAnalysis()
        graph = self.analyzer.analyze_dependencies(steps, analysis)

        critical_time = self.analyzer.estimate_critical_path(steps, graph)

        # 关键路径应该是 5 + 10 = 15分钟
        self.assertEqual(critical_time, 15)


class TestDataModels(unittest.TestCase):
    """数据模型测试套件"""

    def test_requirements_creation(self):
        """测试需求对象创建"""
        req = Requirements(
            user_input="测试输入",
            clarifications={"key": "value"},
            features=["功能1", "功能2"]
        )

        self.assertEqual(req.user_input, "测试输入")
        self.assertEqual(len(req.features), 2)

    def test_step_creation(self):
        """测试步骤对象创建"""
        step = Step(
            id="step1",
            name="测试步骤",
            description="这是一个测试步骤",
            agent_type=AgentType.PRODUCT_MANAGEMENT,
            dependencies=[],
            can_parallel=False,
            estimated_time=timedelta(minutes=10)
        )

        self.assertEqual(step.id, "step1")
        self.assertEqual(step.status, StepStatus.PENDING)
        self.assertEqual(step.estimated_time, timedelta(minutes=10))

    def test_dependency_graph_add_step(self):
        """测试依赖图添加步骤"""
        graph = DependencyGraph()

        step1 = Step(
            id="step1",
            name="步骤1",
            description="测试",
            agent_type=AgentType.PRODUCT_MANAGEMENT,
            dependencies=[]
        )

        step2 = Step(
            id="step2",
            name="步骤2",
            description="测试",
            agent_type=AgentType.DATABASE_DESIGN,
            dependencies=["step1"]
        )

        graph.add_step(step1)
        graph.add_step(step2)

        self.assertEqual(len(graph.nodes), 2)

        # 检查依赖关系
        node2 = graph.nodes["step2"]
        self.assertIn("step1", node2.dependencies)

        node1 = graph.nodes["step1"]
        self.assertIn("step2", node1.dependents)

    def test_risk_report(self):
        """测试风险报告"""
        risk = RiskReport(
            overall_risk="low",
            risks=["风险1"],
            mitigations={"风险1": "缓解措施1"}
        )

        self.assertEqual(risk.overall_risk, "low")
        self.assertEqual(len(risk.risks), 1)
        self.assertEqual(len(risk.mitigations), 1)


if __name__ == '__main__':
    unittest.main()
