import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from datetime import timedelta
from pathlib import Path
import os
import sys

# 添加项目根目录到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from planning.smart_planner import SmartPlanner
from planning.models import ExecutionPlan, Requirements, DependencyGraph, RequirementAnalysis, RiskReport
from common.models import AgentType

class TestSmartPlanner(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.planner = SmartPlanner()

    async def test_empty_input(self):
        """测试空输入"""
        plan = await self.planner.create_smart_plan("")
        
        self.assertEqual(plan.requirements.user_input, "")
        self.assertEqual(len(plan.steps), 0)
        # RequirementAnalysis 的默认 complexity 是 medium
        self.assertEqual(plan.analysis.complexity, "medium")

    @patch('planning.planner.ProjectPlanner.create_plan', new_callable=AsyncMock)
    @patch('conversation.intent_recognizer.IntentRecognizer.recognize', new_callable=AsyncMock)
    async def test_smart_plan_caching(self, mock_recognize, mock_create_plan):
        """测试计划缓存"""
        planner = SmartPlanner()
        user_input = "创建一个简单的Web应用"
        
        # 模拟 IntentRecognizer
        from conversation.intent_recognizer import Intent, IntentType
        mock_intent = Intent(
            type=IntentType.NEW_PROJECT,
            confidence=0.9,
            agent_types=[AgentType.FRONTEND_DEV]
        )
        mock_recognize.return_value = mock_intent
        
        # 模拟返回的计划
        mock_plan = ExecutionPlan(
            requirements=Requirements(user_input=user_input, features=[], clarifications={}),
            steps=[],
            dependencies=DependencyGraph(nodes={}),
            analysis=RequirementAnalysis(project_type="web"),
            estimated_time=timedelta(hours=1),
            risk_report=RiskReport(overall_risk="low", risks=[])
        )
        mock_create_plan.return_value = mock_plan
        
        # 第一次调用
        plan1 = await planner.create_smart_plan(user_input)
        
        # 第二次调用(应该使用缓存)
        plan2 = await planner.create_smart_plan(user_input)
        
        self.assertEqual(plan1, plan2)
        # create_plan 应该只被调用一次
        self.assertEqual(mock_create_plan.call_count, 1)
        mock_create_plan.assert_called_once()

    @patch('planning.planner.ProjectPlanner.create_plan', new_callable=AsyncMock)
    @patch('conversation.intent_recognizer.IntentRecognizer.recognize', new_callable=AsyncMock)
    async def test_intent_enhancement(self, mock_recognize, mock_create_plan):
        """测试意图增强逻辑"""
        planner = SmartPlanner()
        user_input = "修复一个bug"
        
        # 模拟 IntentRecognizer
        from conversation.intent_recognizer import Intent, IntentType
        mock_intent = Intent(
            type=IntentType.FIX_BUG,
            confidence=0.8,
            agent_types=[AgentType.BACKEND_DEV],
            keywords=["bug", "fix"]
        )
        mock_recognize.return_value = mock_intent
        
        # 模拟 ProjectPlanner
        mock_plan = ExecutionPlan(
            requirements=Requirements(user_input=user_input, features=[], clarifications={}),
            steps=[],
            dependencies=DependencyGraph(nodes={}),
            analysis=RequirementAnalysis(project_type="api"),
            estimated_time=timedelta(hours=1),
            risk_report=RiskReport(overall_risk="low", risks=[])
        )
        mock_create_plan.return_value = mock_plan
        
        plan = await planner.create_smart_plan(user_input)
        
        self.assertEqual(plan.analysis.project_type, "api")

if __name__ == '__main__':
    unittest.main()
