#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
计划生成器 - 错误处理增强版示例

展示如何在 planning/planner.py 中应用统一的错误处理机制。
"""

import logging
from typing import Dict, Any, Optional

from utils.exceptions import PlanningError, ErrorCodes
from utils.error_handler import handle_errors, ErrorHandler


logger = logging.getLogger(__name__)


class ProjectPlannerWithErrorHandling:
    """
    项目计划器 - 错误处理增强版
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化计划器"""
        self.config = config or {}
        self.error_handler = ErrorHandler(
            max_errors=5,  # 计划生成错误容忍度较低
            reset_interval=300,
            log_errors=True
        )

    @handle_errors(
        error_type=PlanningError,
        fallback=None,
        log=True
    )
    async def generate_plan(
        self,
        requirements: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        生成项目计划 (带错误处理)

        Args:
            requirements: 需求描述
            context: 上下文信息

        Returns:
            生成的计划

        Raises:
            PlanningError: 计划生成失败时抛出
        """
        # 验证输入
        if not requirements or len(requirements.strip()) < 10:
            raise PlanningError(
                message="需求描述太短,请提供更详细的信息",
                error_code=ErrorCodes.INVALID_REQUIREMENTS,
                details={
                    "requirements_length": len(requirements) if requirements else 0,
                    "min_required_length": 10
                }
            )

        try:
            # 原有的计划生成逻辑
            # ... (这里调用原有的计划生成代码)

            # 模拟结果
            plan = {
                "steps": [
                    {"id": 1, "title": "需求分析", "type": "analysis"},
                    {"id": 2, "title": "设计数据模型", "type": "design"},
                    {"id": 3, "title": "实现功能", "type": "implementation"}
                ],
                "total_steps": 3
            }

            logger.info(f"成功生成计划,共 {plan['total_steps']} 个步骤")
            return plan

        except Exception as e:
            self.error_handler.record_error(
                e,
                context={"requirements": requirements[:100]}  # 只记录前100字符
            )

            raise PlanningError(
                message=f"计划生成失败: {str(e)}",
                error_code=ErrorCodes.PLAN_GENERATION_FAILED,
                details={"requirements": requirements[:100]}
            ) from e

    @handle_errors(
        error_type=PlanningError,
        fallback=False,
        log=True
    )
    async def validate_plan(
        self,
        plan: Dict[str, Any]
    ) -> bool:
        """
        验证计划 (带错误处理)

        Args:
            plan: 待验证的计划

        Returns:
            是否验证通过

        Raises:
            PlanningError: 验证失败时抛出
        """
        if not plan or "steps" not in plan:
            raise PlanningError(
                message="计划格式无效",
                error_code=ErrorCodes.PLAN_VALIDATION_FAILED,
                details={"plan_keys": list(plan.keys()) if plan else []}
            )

        try:
            # 原有的验证逻辑
            # ... (这里调用原有的验证代码)

            # 模拟验证
            is_valid = len(plan.get("steps", [])) > 0

            if is_valid:
                logger.info("计划验证通过")
            else:
                logger.warning("计划验证未通过")

            return is_valid

        except Exception as e:
            self.error_handler.record_error(e, context={"plan_steps": len(plan.get("steps", []))})

            raise PlanningError(
                message=f"计划验证失败: {str(e)}",
                error_code=ErrorCodes.PLAN_VALIDATION_FAILED,
                details={"plan": plan}
            ) from e

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        return self.error_handler.get_error_summary()


# 使用示例
async def example_usage():
    """使用示例"""

    planner = ProjectPlannerWithErrorHandling()

    # 示例 1: 正常生成计划
    try:
        plan = await planner.generate_plan("开发一个用户登录系统")
        print(f"生成计划: {plan}")
    except PlanningError as e:
        print(f"错误: {e}")

    # 示例 2: 需求太短
    plan = await planner.generate_plan("登录")  # 返回 None (fallback)
    print(f"短需求结果: {plan}")

    # 示例 3: 验证计划
    try:
        valid = await planner.validate_plan({"steps": []})
        print(f"验证结果: {valid}")
    except PlanningError as e:
        print(f"验证错误: {e}")
