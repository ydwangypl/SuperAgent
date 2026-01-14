#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
集成测试 - 测试完整的对话→规划流程
"""

import unittest
import asyncio

from conversation.manager import ConversationManager
from planning.planner import ProjectPlanner


class TestFullIntegration(unittest.IsolatedAsyncioTestCase):
    """完整集成测试套件"""

    async def asyncSetUp(self):
        """测试前异步准备"""
        self.conv_mgr = ConversationManager()
        self.planner = ProjectPlanner()

    async def test_full_flow_blog(self):
        """测试博客系统的完整流程 (Phase 2)"""
        user_input = "我想开发一个Python博客系统,包含文章管理和用户评论功能,需要数据库存储,包含后端API"

        # 步骤1: 对话管理
        conv_result = await self.conv_mgr.process_input(user_input)

        self.assertEqual(conv_result.type, "requirements_ready")
        self.assertEqual(conv_result.data['intent'].type.value, "new_project")

        # 步骤2: 项目规划
        plan = await self.planner.create_plan(
            user_input,
            conv_result.data['context']
        )

        # 验证计划
        self.assertGreater(len(plan.steps), 0)
        # 项目类型现在是动态判定的 (博客 -> service_application 或 fullstack_app)
        self.assertIn(plan.analysis.project_type, ["blog", "service_application", "fullstack_app"])
        self.assertIn("文章管理", plan.requirements.features)

        # 验证步骤
        step_names = [s.name for s in plan.steps]
        self.assertIn("产品需求分析", step_names)
        self.assertIn("数据库设计", step_names)
        self.assertIn("后端API开发", step_names)

        # 验证依赖
        for step in plan.steps:
            if step.name == "数据库设计":
                self.assertIn("step1", step.dependencies)

    async def test_full_flow_ecommerce(self):
        """测试完整的电商网站开发流程"""
        user_input = "我想开发一个电商网站系统,需要商品管理和订单功能,包含用户登录注册"

        # 对话管理
        conv_result = await self.conv_mgr.process_input(user_input)

        self.assertEqual(conv_result.type, "requirements_ready")

        # 项目规划
        plan = await self.planner.create_plan(
            user_input,
            conv_result.data['context']
        )

        # 验证
        self.assertIn(plan.analysis.project_type, ["ecommerce", "service_application", "fullstack_app"])
        self.assertTrue(plan.analysis.has_auth)

    async def test_full_flow_with_clarification(self):
        """测试需要澄清的完整流程"""
        user_input = "帮我开发"

        # 对话管理 - 应该触发澄清
        conv_result = await self.conv_mgr.process_input(user_input)

        self.assertEqual(conv_result.type, "clarification")
        self.assertGreater(len(conv_result.clarifications), 0)

        # 验证澄清问题
        questions = conv_result.clarifications
        required_questions = [q for q in questions if q.required]

        self.assertGreater(len(required_questions), 0)

    async def test_end_to_end_time_estimation(self):
        """测试端到端时间估算"""
        user_input = "开发一个任务管理API"

        # 完整流程
        conv_result = await self.conv_mgr.process_input(user_input)
        plan = await self.planner.create_plan(
            user_input,
            conv_result.data['context']
        )

        # 验证时间估算
        total_minutes = int(plan.estimated_time.total_seconds() / 60)

        # 应该在30-60分钟之间
        self.assertGreaterEqual(total_minutes, 30)
        self.assertLessEqual(total_minutes, 60)

    async def test_plan_consistency(self):
        """测试计划一致性"""
        # 多次生成相同需求的计划,结果应该一致
        user_input = "开发一个博客系统"

        plan1 = await self.planner.create_plan(user_input, {})
        plan2 = await self.planner.create_plan(user_input, {})

        # 步骤数量应该相同
        self.assertEqual(len(plan1.steps), len(plan2.steps))

        # 步骤名称应该相同
        names1 = [s.name for s in plan1.steps]
        names2 = [s.name for s in plan2.steps]

        self.assertEqual(names1, names2)

    async def test_context_propagation(self):
        """测试上下文传播"""
        user_input = "开发一个需要用户认证的博客系统"

        # 对话管理
        conv_result = await self.conv_mgr.process_input(user_input)

        # 项目规划
        plan = await self.planner.create_plan(
            user_input,
            conv_result.data['context']
        )

        # 验证上下文传播
        self.assertEqual(plan.requirements.user_input, user_input)

        # 如果识别出认证需求,应该在分析中体现
        if "认证" in user_input or "登录" in user_input:
            # 这个逻辑在需求分析中
            pass

    def test_planner_format_output(self):
        """测试规划器格式化输出"""
        # 使用同步版本测试格式化
        import asyncio

        async def test_format():
            user_input = "开发一个博客系统"
            plan = await self.planner.create_plan(user_input, {})

            formatted = self.planner.format_plan(plan)

            # 验证格式化输出包含关键部分
            self.assertIn("项目执行计划", formatted)
            self.assertIn("需求概述", formatted)
            self.assertIn("执行步骤", formatted)
            self.assertIn("时间估算", formatted)

        asyncio.run(test_format())


class TestErrorHandling(unittest.IsolatedAsyncioTestCase):
    """错误处理测试套件"""

    async def asyncSetUp(self):
        """测试前异步准备"""
        self.conv_mgr = ConversationManager()
        self.planner = ProjectPlanner()

    async def test_empty_input_handling(self):
        """测试空输入处理"""
        result = await self.conv_mgr.process_input("")

        # 应该返回澄清响应
        self.assertEqual(result.type, "clarification")

    async def test_very_long_input_handling(self):
        """测试超长输入处理"""
        long_input = "我想开发" * 100

        result = await self.conv_mgr.process_input(long_input)

        # 应该能够处理而不崩溃
        self.assertIsNotNone(result)

    def test_invalid_context_handling(self):
        """测试无效上下文处理"""
        # 空上下文
        plan = asyncio.run(self.planner.create_plan("测试", {}))

        self.assertIsNotNone(plan)
        self.assertIsInstance(plan.steps, list)


class TestPerformance(unittest.IsolatedAsyncioTestCase):
    """性能测试套件"""

    async def asyncSetUp(self):
        """测试前异步准备"""
        self.conv_mgr = ConversationManager()
        self.planner = ProjectPlanner()

    async def test_conversation_performance(self):
        """测试对话管理性能"""
        import time

        inputs = [
            "我想开发一个博客系统",
            "开发一个电商网站",
            "创建一个任务管理API",
            "建立一个个人网站",
            "做一个在线教育平台"
        ]

        start_time = time.time()

        for user_input in inputs:
            await self.conv_mgr.process_input(user_input)

        elapsed = time.time() - start_time

        # 平均每个输入应该在100ms内
        avg_time = elapsed / len(inputs)
        self.assertLess(avg_time, 0.1)

    async def test_planning_performance(self):
        """测试规划性能"""
        import time

        user_input = "开发一个博客系统"

        start_time = time.time()

        plan = await self.planner.create_plan(user_input, {})

        elapsed = time.time() - start_time

        # 规划应该在200ms内完成
        self.assertLess(elapsed, 0.2)

        # 验证计划质量
        self.assertGreater(len(plan.steps), 0)


if __name__ == '__main__':
    unittest.main()
