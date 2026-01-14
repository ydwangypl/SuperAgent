#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目规划器

生成完整的项目执行计划
"""

import re
import logging
from typing import List, Dict, Any, Optional
from datetime import timedelta

from .models import (
    Requirements, Step, ExecutionPlan,
    RequirementAnalysis, RiskReport
)
from .step_generator import StepGenerator
from .dependency_analyzer import DependencyAnalyzer
from planning.task_granularity_validator import TaskGranularityValidator

logger = logging.getLogger(__name__)

GRANULARITY_AVAILABLE = True


class ProjectPlanner:
    """项目规划器"""

    def __init__(self, enable_granularity_validation: bool = True) -> None:
        self.step_generator = StepGenerator()
        self.dependency_analyzer = DependencyAnalyzer()

        # 初始化任务粒度验证器 (P0 v3.2)
        self.granularity_validator = None
        self.granularity_enabled = enable_granularity_validation and GRANULARITY_AVAILABLE
        if self.granularity_enabled:
            self.granularity_validator = TaskGranularityValidator()

        # 预编译特征识别正则表达式 (通用化升级)
        self._patterns = {
            "ui": re.compile(r"界面|ui|页面|web|frontend|前端|gui|cli|控制台|display", re.IGNORECASE),
            "backend": re.compile(r"后端|backend|server|服务|api|core|logic", re.IGNORECASE),
            "database": re.compile(r"数据库|database|sql|存储|save|data|persistence", re.IGNORECASE),
            "security": re.compile(
                r"安全|权限|auth|security|permission|加密|登录|注册|login|register|signup",
                re.IGNORECASE
            ),
            "api": re.compile(r"api|接口|rest|grpc|webhook|communication", re.IGNORECASE),
            "integration": re.compile(r"集成|对接|integrate|connect|plugin", re.IGNORECASE),
            "automation": re.compile(r"自动|脚本|script|automation|workflow", re.IGNORECASE)
        }

        # 核心功能模式 (更具抽象性)
        self._feature_patterns = {
            "核心逻辑": re.compile(r"逻辑|处理|核心|core|logic|engine", re.IGNORECASE),
            "用户交互": re.compile(r"交互|用户|ui|user|interaction", re.IGNORECASE),
            "数据管理": re.compile(r"数据|管理|记录|储存|data|management", re.IGNORECASE),
            "安全保障": re.compile(r"安全|权限|加密|security|protection|登录|注册", re.IGNORECASE),
            "外部集成": re.compile(r"对接|集成|外部|external|integration", re.IGNORECASE),
            "流程自动": re.compile(r"自动|任务|流程|automation|workflow", re.IGNORECASE),
            "文章管理": re.compile(r"文章|内容|内容管理|cms|blog|article|content", re.IGNORECASE),
            "评论功能": re.compile(r"评论|留言|comment|feedback", re.IGNORECASE),
            "订单功能": re.compile(r"订单|交易|支付|order|transaction|payment", re.IGNORECASE),
            "商品管理": re.compile(r"商品|库存|product|catalog|inventory", re.IGNORECASE)
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
        analysis.has_auth = bool(self._patterns["security"].search(text))
        analysis.has_api = bool(self._patterns["api"].search(text))
        analysis.has_ecommerce = "电商" in text or "shopping" in text or "shop" in text

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
        lines.append("=" * 70)
        lines.append("  项目执行计划")
        lines.append("=" * 70)

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
        lines.append("\n【时间估算】")
        lines.append(f"  总预计时间: {total_minutes}分钟 ({total_minutes // 60}小时{total_minutes % 60}分钟)")

        # 风险评估
        if plan.risk_report.risks:
            lines.append("\n【风险评估】")
            lines.append(f"  整体风险: {plan.risk_report.overall_risk}")
            lines.append("  风险项:")
            for risk in plan.risk_report.risks:
                lines.append(f"    - {risk}")

            if plan.risk_report.mitigations:
                lines.append("  缓解措施:")
                for risk, mitigation in plan.risk_report.mitigations.items():
                    lines.append(f"    {risk}: {mitigation}")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)

    # ========== P0 v3.2: 任务粒度验证集成 ==========

    def validate_step_granularity(self, step: Step) -> tuple[bool, List[str]]:
        """验证单个步骤的粒度

        Args:
            step: 待验证的步骤

        Returns:
            tuple[bool, List[str]]: (是否通过, 违规列表)
        """
        if not self.granularity_enabled or not self.granularity_validator:
            return True, []  # 粒度验证未启用,直接通过

        try:
            # 使用实际的 TaskGranularityValidator API
            is_valid = self.granularity_validator.validate_task(step)
            violations = self.granularity_validator.get_violations()

            return is_valid, violations
        except Exception as e:
            logger.error(f"步骤粒度验证失败: {e}")
            return False, [f"验证异常: {str(e)}"]

    def validate_all_steps(self, steps: List[Step]) -> Dict[str, Any]:
        """验证所有步骤的粒度

        Args:
            steps: 步骤列表

        Returns:
            Dict: 验证结果摘要
        """
        if not self.granularity_enabled or not self.granularity_validator:
            return {"enabled": False, "all_valid": True}

        try:
            # 使用实际的 TaskGranularityValidator API
            result = self.granularity_validator.validate_task_list(steps)

            return {
                "enabled": True,
                **result
            }
        except Exception as e:
            logger.error(f"批量验证失败: {e}")
            return {
                "enabled": True,
                "total_steps": len(steps),
                "valid_steps": 0,
                "invalid_steps": len(steps),
                "all_valid": False,
                "error": str(e)
            }

    def auto_split_oversized_steps(self, steps: List[Step]) -> List[Step]:
        """自动拆分过大的步骤

        Args:
            steps: 原始步骤列表

        Returns:
            List[Step]: 处理后的步骤列表
        """
        if not self.granularity_enabled or not self.granularity_validator:
            return steps  # 粒度验证未启用,直接返回

        processed_steps = []
        for step in steps:
            # 总是尝试拆分 - auto_split_task 会自动判断是否需要拆分
            try:
                # 使用实际的 TaskGranularityValidator API
                split_result = self.granularity_validator.auto_split_task(step)

                if split_result.success and len(split_result.subtasks) > 1:
                    # 成功拆分为多个子任务
                    logger.info(f"步骤 '{step.name}' 已拆分为 {len(split_result.subtasks)} 个子步骤")
                    processed_steps.extend(split_result.subtasks)
                else:
                    # 无法拆分或无需拆分,保留原步骤
                    processed_steps.append(step)
            except Exception as e:
                logger.error(f"自动拆分失败: {e}")
                # 拆分失败,保留原步骤
                processed_steps.append(step)

        return processed_steps

    def get_granularity_summary(self) -> Dict[str, Any]:
        """获取粒度验证摘要

        Returns:
            Dict: 粒度验证摘要
        """
        if not self.granularity_enabled or not self.granularity_validator:
            return {"enabled": False}

        return {
            "enabled": True,
            "violations": self.granularity_validator.get_violations(),
            "has_violations": self.granularity_validator.has_violations()
        }
