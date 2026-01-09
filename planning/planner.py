#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目规划器

生成完整的项目执行计划
"""

import re
from typing import List, Dict, Any, Optional
from datetime import timedelta

from .models import (
    Requirements, Step, ExecutionPlan, DependencyGraph,
    RequirementAnalysis, RiskReport, AgentType
)
from .step_generator import StepGenerator
from .dependency_analyzer import DependencyAnalyzer


class ProjectPlanner:
    """项目规划器"""

    def __init__(self) -> None:
        self.step_generator = StepGenerator()
        self.dependency_analyzer = DependencyAnalyzer()

        # 预编译通用特征正则表达式
        self._patterns = {
            "ui": re.compile(r"界面|ui|页面|web|frontend|前端|gui|cli|控制台", re.IGNORECASE),
            "backend": re.compile(r"后端|backend|server|服务|api", re.IGNORECASE),
            "database": re.compile(r"数据库|database|sql|存储|save|data", re.IGNORECASE),
            "auth": re.compile(r"登录|注册|用户|auth|permission", re.IGNORECASE),
            "api": re.compile(r"api|接口|rest|grpc|webhook", re.IGNORECASE),
            "logic": re.compile(r"逻辑|处理|计算|算法|business|logic", re.IGNORECASE),
            "ecommerce": re.compile(r"电商|商城|交易|订单|商品|shop|mall", re.IGNORECASE)
        }

        self._feature_patterns = {
            "文章管理": re.compile(r"文章|博客|内容|post|article", re.IGNORECASE),
            "用户系统": re.compile(r"用户|登录|注册|权限|auth|user", re.IGNORECASE),
            "评论功能": re.compile(r"评论|留言|互动|comment", re.IGNORECASE),
            "商品管理": re.compile(r"商品|货物|库存|product|item", re.IGNORECASE),
            "订单处理": re.compile(r"订单|交易|支付|order|payment", re.IGNORECASE),
            "数据处理": re.compile(r"处理|分析|转化|process", re.IGNORECASE),
            "用户交互": re.compile(r"交互|输入|显示|input|display", re.IGNORECASE),
            "系统集成": re.compile(r"集成|打通|对接|integrate", re.IGNORECASE),
            "安全合规": re.compile(r"安全|加密|权限|security", re.IGNORECASE),
            "自动化": re.compile(r"自动|任务|脚本|automation", re.IGNORECASE)
        }

    async def create_plan(
        self,
        user_input: str,
        context: Dict[str, Any],
        intent: Optional[Any] = None
    ) -> ExecutionPlan:
        """创建执行计划

        Args:
            user_input: 用户输入
            context: 对话上下文
            intent: 意图识别结果 (审计优化: 减少重复计算, 直接使用意图数据)

        Returns:
            ExecutionPlan: 执行计划
        """
        # 1. 构建需求对象
        requirements = self._build_requirements(user_input, context, intent)

        # 2. 分析需求
        analysis = self._analyze_requirements(requirements)

        # 3. 生成步骤
        steps = self.step_generator.generate_steps(requirements, analysis)

        # 4. 分析依赖关系
        dependencies = self.dependency_analyzer.analyze_dependencies(steps, analysis)

        # 5. 估算时间
        estimated_time = self._estimate_total_time(steps)

        # 6. 风险评估
        risk_report = self._assess_risks(requirements, analysis, steps)

        # 7. 构建计划
        plan = ExecutionPlan(
            requirements=requirements,
            steps=steps,
            dependencies=dependencies,
            analysis=analysis,
            estimated_time=estimated_time,
            risk_report=risk_report
        )

        return plan

    def _build_requirements(
        self,
        user_input: str,
        context: Dict[str, Any],
        intent: Optional[Any] = None
    ) -> Requirements:
        """构建需求对象

        Args:
            user_input: 用户输入
            context: 上下文
            intent: 意图

        Returns:
            Requirements: 需求对象
        """
        # 提取功能列表
        features = self._extract_features(user_input, intent)

        # 提取约束条件
        constraints = []
        if context.get("constraints"):
            constraints.extend(context["constraints"])

        return Requirements(
            user_input=user_input,
            clarifications=context.get("clarifications", {}),
            intent=intent,
            constraints=constraints,
            features=features
        )

    def _analyze_requirements(self, requirements: Requirements) -> RequirementAnalysis:
        """分析需求 (通用化逻辑)"""
        analysis = RequirementAnalysis()
        text = requirements.user_input.lower()

        # 基于特征检测而非项目类型
        analysis.has_frontend = bool(self._patterns["ui"].search(text))
        analysis.has_backend = bool(self._patterns["backend"].search(text))
        analysis.has_database = bool(self._patterns["database"].search(text))
        analysis.has_auth = bool(self._patterns["auth"].search(text))
        analysis.has_api = bool(self._patterns["api"].search(text))
        analysis.has_ecommerce = bool(self._patterns["ecommerce"].search(text))
        
        # 总是需要产品需求分析
        analysis.has_product_requirements = True

        # 动态判定项目类型
        if analysis.has_ecommerce:
            analysis.project_type = "ecommerce"
        elif analysis.has_frontend and analysis.has_backend:
            analysis.project_type = "fullstack_app"
        elif analysis.has_frontend:
            analysis.project_type = "ui_application"
        elif analysis.has_backend:
            analysis.project_type = "service_application"
        elif "算法" in text or "逻辑" in text:
            analysis.project_type = "logic_library"
        else:
            analysis.project_type = "general_module"

        # 检测技术栈 (简单回退)
        tech_keywords = {
            "Python": ["python", "pip"],
            "JavaScript": ["javascript", "node", "react", "vue"],
            "Rust": ["rust", "cargo"],
            "C++": ["c++", "cmake", "gcc"],
            "Go": ["go", "golang"]
        }
        
        analysis.tech_stack = "未指定"
        for tech, keywords in tech_keywords.items():
            if any(k in text for k in keywords):
                analysis.tech_stack = tech
                break

        # 评估复杂度 (基于特征数量)
        detected_features = [f for f in self._patterns if self._patterns[f].search(text)]
        feature_count = len(detected_features)
        
        if feature_count <= 1:
            analysis.complexity = "low"
        elif feature_count <= 3:
            analysis.complexity = "medium"
        else:
            analysis.complexity = "high"

        return analysis

    def _extract_features(self, user_input: str, intent: Optional[Any] = None) -> List[str]:
        """从用户输入中提取功能列表

        Args:
            user_input: 用户输入
            intent: 意图 (可选)

        Returns:
            List[str]: 功能列表
        """
        features = []

        # 审计优化: 如果有预置意图, 直接提取其关键词作为特征
        if intent and hasattr(intent, 'keywords'):
            features.extend(intent.keywords)

        for feature_name, pattern in self._feature_patterns.items():
            if pattern.search(user_input):
                if feature_name not in features:
                    features.append(feature_name)

        return features

    def _estimate_total_time(self, steps: List[Step]) -> timedelta:
        """估算总时间

        Args:
            steps: 步骤列表

        Returns:
            timedelta: 总时间
        """
        total = timedelta()
        for step in steps:
            total += step.estimated_time
        return total

    def _assess_risks(
        self,
        requirements: Requirements,
        analysis: RequirementAnalysis,
        steps: List[Step]
    ) -> RiskReport:
        """评估风险

        Args:
            requirements: 需求
            analysis: 分析结果
            steps: 步骤

        Returns:
            RiskReport: 风险报告
        """
        risks = []
        mitigations = {}

        # 风险1: 需求不明确
        if not requirements.features:
            risks.append("需求不够具体,可能导致返工")
            mitigations["需求不明确"] = "在开始前生成详细PRD文档"

        # 风险2: 复杂度高
        if analysis.complexity == "high":
            risks.append("项目复杂度高,建议分阶段实施")
            mitigations["复杂度高"] = "采用敏捷开发,分迭代交付"

        # 风险3: 技术栈未确定
        if not analysis.tech_stack or analysis.tech_stack == "未指定":
            risks.append("技术栈未确定,可能影响开发效率")
            mitigations["技术栈未定"] = "根据项目类型推荐合适技术栈"

        # 风险4: 缺少测试
        step_count = len(steps)
        if step_count < 3:
            risks.append("项目规模较小,但仍然需要测试")
            mitigations["缺少测试"] = "添加基础测试用例"

        # 确定整体风险等级
        if len(risks) == 0:
            overall_risk = "low"
        elif len(risks) <= 2:
            overall_risk = "medium"
        else:
            overall_risk = "high"

        return RiskReport(
            overall_risk=overall_risk,
            risks=risks,
            mitigations=mitigations
        )

    def format_plan(self, plan: ExecutionPlan) -> str:
        """格式化计划为可读文本

        Args:
            plan: 执行计划

        Returns:
            str: 格式化的计划文本
        """
        lines = []
        lines.append("="*70)
        lines.append("  项目执行计划")
        lines.append("="*70)

        # 需求概述
        lines.append("\n【需求概述】")
        lines.append(f"  原始需求: {plan.requirements.user_input}")
        lines.append(f"  项目类型: {plan.analysis.project_type}")
        lines.append(f"  技术栈: {plan.analysis.tech_stack or '待确定'}")
        lines.append(f"  复杂度: {plan.analysis.complexity}")

        if plan.requirements.features:
            lines.append(f"  功能列表: {', '.join(plan.requirements.features)}")

        # 执行步骤
        lines.append("\n【执行步骤】")
        for i, step in enumerate(plan.steps, 1):
            deps = f" (依赖: {', '.join(step.dependencies)})" if step.dependencies else ""
            parallel = " [可并行]" if step.can_parallel else ""
            time_str = f"{int(step.estimated_time.total_seconds() / 60)}分钟"

            lines.append(f"\n  步骤{i}: {step.name}{deps}{parallel}")
            lines.append(f"    描述: {step.description}")
            lines.append(f"    负责Agent: {step.agent_type.value}")
            lines.append(f"    预计耗时: {time_str}")

        # 时间估算
        total_minutes = int(plan.estimated_time.total_seconds() / 60)
        lines.append(f"\n【时间估算】")
        lines.append(f"  总预计时间: {total_minutes}分钟 ({total_minutes//60}小时{total_minutes%60}分钟)")

        # 风险评估
        if plan.risk_report.risks:
            lines.append(f"\n【风险评估】")
            lines.append(f"  整体风险: {plan.risk_report.overall_risk}")
            lines.append(f"  风险项:")
            for risk in plan.risk_report.risks:
                lines.append(f"    - {risk}")

            if plan.risk_report.mitigations:
                lines.append(f"  缓解措施:")
                for risk, mitigation in plan.risk_report.mitigations.items():
                    lines.append(f"    {risk}: {mitigation}")

        lines.append("\n" + "="*70)

        return "\n".join(lines)
