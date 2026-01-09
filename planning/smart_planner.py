#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智能规划器

增强的规划功能,集成意图识别,自动生成智能执行计划
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import timedelta
from collections import OrderedDict

from planning.models import (
    Requirements, Step, ExecutionPlan, DependencyGraph,
    RequirementAnalysis, RiskReport
)
from common.models import AgentType
from planning.planner import ProjectPlanner
from orchestration.registry import AgentRegistry

# 避免循环导入
if TYPE_CHECKING:
    from conversation import IntentRecognizer, IntentResult


logger = logging.getLogger(__name__)


class SmartPlanner(ProjectPlanner):
    """智能规划器 - 增强版ProjectPlanner"""

    def __init__(self) -> None:
        """初始化智能规划器"""
        super().__init__()

        # 延迟导入避免循环依赖
        from conversation import IntentRecognizer

        # 初始化智能意图识别器
        self.intent_recognizer = IntentRecognizer()

        # 初始化计划缓存: 使用 OrderedDict 实现简单的 LRU 缓存
        self._plan_cache: OrderedDict[str, tuple[ExecutionPlan, float]] = OrderedDict()
        self._cache_ttl = 600  # 10分钟缓存
        self._max_cache_size = 100  # 最大缓存条数

    async def create_smart_plan(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """创建智能执行计划(带缓存)

        Args:
            user_input: 用户输入
            context: 对话上下文(可选)

        Returns:
            ExecutionPlan: 智能生成的执行计划
        """
        # 1. 如果输入为空,返回空计划
        if not user_input.strip():
            logger.warning("规划器收到空输入")
            return ExecutionPlan(
                requirements=Requirements(user_input="", features=[], clarifications={}),
                steps=[],
                dependencies=DependencyGraph(nodes={}),
                analysis=RequirementAnalysis(project_type="unknown"),
                estimated_time=timedelta(0),
                risk_report=RiskReport(overall_risk="low", risks=[])
            )

        context = context or {}

        # 生成缓存键
        cache_key = self._generate_cache_key(user_input, context)

        # 检查并清理过期缓存
        self._clean_expired_cache()

        # 检查缓存
        if cache_key in self._plan_cache:
            cached_plan, timestamp = self._plan_cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"使用缓存的计划: {cache_key[:8]}...")
                # 移动到末尾 (LRU)
                self._plan_cache.move_to_end(cache_key)
                return cached_plan
            else:
                # 过期删除
                del self._plan_cache[cache_key]

        try:
            # 2. 使用智能意图识别 (recognize 已经是异步方法)
            intent_result = await self.intent_recognizer.recognize(user_input)

            # 3. 增强上下文
            enhanced_context = self._enhance_context(
                context,
                intent_result
            )

            # 4. 生成基础计划
            plan = await super().create_plan(user_input, enhanced_context)

            # 5. 智能优化计划
            plan = self._optimize_plan(plan, intent_result)

            # 存入缓存
            self._plan_cache[cache_key] = (plan, time.time())
            
            # 控制缓存大小
            if len(self._plan_cache) > self._max_cache_size:
                self._plan_cache.popitem(last=False)

            return plan
        except (ValueError, json.JSONDecodeError, AttributeError) as e:
            logger.error(f"智能规划参数或数据解析失败: {e}")
            raise RuntimeError(f"规划器数据异常: {str(e)}") from e
        except asyncio.CancelledError:
            logger.warning("智能规划任务被取消")
            raise
        except (OSError, IOError) as e:
            logger.error(f"智能规划过程中发生IO错误: {e}")
            raise RuntimeError(f"系统IO异常: {str(e)}") from e
        except Exception as e:
            logger.error(f"智能规划遇到非预期异常 ({type(e).__name__}): {e}", exc_info=True)
            # 如果失败，尝试生成一个最基础的计划或抛出异常
            raise RuntimeError(f"系统繁忙，无法生成执行计划 ({type(e).__name__}): {str(e)}") from e

    def _clean_expired_cache(self) -> None:
        """清理过期缓存"""
        now = time.time()
        expired_keys = [
            k for k, v in self._plan_cache.items()
            if now - v[1] > self._cache_ttl
        ]
        for k in expired_keys:
            del self._plan_cache[k]
        
        if expired_keys:
            logger.debug(f"已清理 {len(expired_keys)} 条过期计划缓存")

    def _enhance_context(
        self,
        context: Dict[str, Any],
        intent_result: 'IntentResult'
    ) -> Dict[str, Any]:
        """增强上下文信息

        Args:
            context: 原始上下文
            intent_result: 意图识别结果

        Returns:
            Dict[str, Any]: 增强后的上下文
        """
        enhanced = context.copy()

        # 添加识别的Agent类型
        if intent_result.agent_types:
            enhanced["suggested_agents"] = [
                AgentType(agent) for agent in intent_result.agent_types
            ]

        # 添加识别的关键词 (Intent 使用 keywords 而非 extracted_keywords)
        if intent_result.keywords:
            enhanced["keywords"] = list(set(context.get("keywords", []) + intent_result.keywords))

        # 添加置信度
        enhanced["confidence"] = intent_result.confidence

        # 添加主要意图 (Intent 使用 type)
        enhanced["primary_intent"] = intent_result.type.value

        return enhanced

    def _optimize_plan(
        self,
        plan: ExecutionPlan,
        intent_result: 'IntentResult'
    ) -> ExecutionPlan:
        """优化执行计划

        Args:
            plan: 原始计划
            intent_result: 意图识别结果

        Returns:
            ExecutionPlan: 优化后的计划
        """
        # 1. 智能Agent类型分配
        plan = self._optimize_agent_types(plan, intent_result)

        # 2. 智能步骤顺序调整
        plan = self._optimize_step_order(plan, intent_result)

        # 3. 智能时间估算
        plan = self._optimize_time_estimation(plan, intent_result)

        return plan

    def _optimize_agent_types(
        self,
        plan: ExecutionPlan,
        intent_result: 'IntentResult'
    ) -> ExecutionPlan:
        """优化Agent类型分配

        Args:
            plan: 原始计划
            intent_result: 意图识别结果

        Returns:
            ExecutionPlan: 优化后的计划
        """
        # 如果识别到了Agent类型,使用它们
        if intent_result.agent_types:
            # 获取识别的Agent类型
            recognized_agents = list(intent_result.agent_types)

            # 为每个步骤分配最优的Agent类型
            for i, step in enumerate(plan.steps):
                # 如果步骤的Agent类型不在识别列表中
                if step.agent_type not in recognized_agents:
                    # 尝试找到最相关的Agent类型
                    best_agent = self._find_best_agent(step, recognized_agents)
                    if best_agent:
                        step.agent_type = best_agent

        return plan

    def _find_best_agent(
        self,
        step: Step,
        available_agents: List[AgentType]
    ) -> Optional[AgentType]:
        """为步骤找到最佳Agent类型 (Phase 3 重构版：基于 Registry)"""
        if not available_agents:
            return None

        # 按优先级排序可用Agent (从 Registry 获取)
        sorted_agents = sorted(
            available_agents,
            key=lambda x: AgentRegistry.get_priority(x)
        )

        return sorted_agents[0]

    def _optimize_step_order(
        self,
        plan: ExecutionPlan,
        intent_result: 'IntentResult'
    ) -> ExecutionPlan:
        """优化步骤顺序 (基于Agent能力的通用匹配)"""
        if intent_result.suggested_steps:
            # 使用更通用的能力匹配逻辑，而非硬编码名称
            reordered_steps = []
            
            # 建立能力到步骤的模糊匹配
            for suggested_step in intent_result.suggested_steps:
                # 提取建议步骤的核心关键词 (去除序号)
                clean_suggestion = suggested_step.split(". ", 1)[-1] if ". " in suggested_step else suggested_step
                
                # 在现有计划步骤中寻找语义最接近的
                for step in plan.steps:
                    if step not in reordered_steps:
                        # 简单的包含匹配，未来可升级为向量相似度
                        if clean_suggestion[:4] in step.name or clean_suggestion[:4] in step.description:
                            reordered_steps.append(step)

            # 保持未匹配步骤的原始相对顺序
            for step in plan.steps:
                if step not in reordered_steps:
                    reordered_steps.append(step)

            plan.steps = reordered_steps
            
        return plan

    def _optimize_time_estimation(
        self,
        plan: ExecutionPlan,
        intent_result: 'IntentResult'
    ) -> ExecutionPlan:
        """优化时间估算

        Args:
            plan: 原始计划
            intent_result: 意图识别结果

        Returns:
            ExecutionPlan: 优化后的计划
        """
        # 基于置信度调整时间估算
        confidence_multiplier = 1.0

        if intent_result.confidence < 0.5:
            # 低置信度,增加时间估算
            confidence_multiplier = 1.5
        elif intent_result.confidence > 0.8:
            # 高置信度,减少时间估算
            confidence_multiplier = 0.8

        # 调整每个步骤的估算时间
        for step in plan.steps:
            if step.estimated_time:
                step.estimated_time = timedelta(
                    seconds=step.estimated_time.total_seconds() * confidence_multiplier
                )

        # 重新计算总时间
        plan.estimated_time = self._estimate_total_time(plan.steps)

        return plan

    async def generate_plan_from_intent(
        self,
        intent_result: 'IntentResult',
        user_input: str
    ) -> ExecutionPlan:
        """从意图结果直接生成计划

        Args:
            intent_result: 意图识别结果
            user_input: 用户输入

        Returns:
            ExecutionPlan: 生成的执行计划
        """
        # 构建增强上下文
        context = {
            "suggested_agents": [
                AgentType(agent) for agent in intent_result.agent_types
            ],
            "keywords": intent_result.keywords,
            "confidence": intent_result.confidence,
            "primary_intent": intent_result.type.value
        }

        # 生成计划
        plan = await self.create_smart_plan(user_input, context)

        return plan

    async def get_plan_suggestions(
        self,
        user_input: str
    ) -> Dict[str, Any]:
        """获取计划建议 (异步版)

        Args:
            user_input: 用户输入

        Returns:
            Dict[str, Any]: 计划建议
        """
        # 识别意图 (在线程池中执行同步操作)
        intent_result = await asyncio.to_thread(self.intent_recognizer.recognize, user_input)

        # 生成建议
        suggestions = {
            "primary_intent": intent_result.primary_intent,
            "confidence": intent_result.confidence,
            "recommended_agents": [
                {
                    "agent_type": agent.value,
                    "reasoning": self._get_agent_reasoning(agent, intent_result)
                }
                for agent in intent_result.agent_types[:5]  # 最多5个
            ],
            "suggested_steps": intent_result.suggested_steps,
            "estimated_complexity": self._estimate_complexity(intent_result),
            "keywords": intent_result.keywords,
            "reasoning": intent_result.reasoning
        }

        return suggestions

    def _get_agent_reasoning(
        self,
        agent_type: AgentType,
        intent_result: 'IntentResult'
    ) -> str:
        """获取Agent类型推荐理由 (Phase 3 重构版：基于 Registry)"""
        return AgentRegistry.get_description(agent_type)

    def _estimate_complexity(self, intent_result: 'IntentResult') -> str:
        """估算项目复杂度

        Args:
            intent_result: 意图识别结果

        Returns:
            str: 复杂度级别 (low/medium/high)
        """
        # 基于多个因素估算复杂度
        score = 0

        # Agent类型数量
        if len(intent_result.agent_types) >= 4:
            score += 2
        elif len(intent_result.agent_types) >= 2:
            score += 1

        # 关键词数量
        if len(intent_result.keywords) >= 3:
            score += 2
        elif len(intent_result.keywords) >= 1:
            score += 1

        # 输入长度
        if len(intent_result.primary_intent) > 50:
            score += 1

        # 判定复杂度
        if score >= 4:
            return "high"
        elif score >= 2:
            return "medium"
        else:
            return "low"

    def _generate_cache_key(
        self,
        user_input: str,
        context: Dict[str, Any]
    ) -> str:
        """生成缓存键

        Args:
            user_input: 用户输入
            context: 上下文信息

        Returns:
            str: MD5哈希缓存键
        """
        # 将context转换为JSON字符串
        context_str = json.dumps(context, sort_keys=True)

        # 组合输入和上下文
        combined = f"{user_input}|{context_str}"

        # 生成MD5哈希
        return hashlib.md5(combined.encode('utf-8')).hexdigest()

    def clear_cache(self):
        """清除计划缓存"""
        self._plan_cache.clear()
        logger.info("计划生成缓存已清除")

