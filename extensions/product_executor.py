#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
产品管理执行器

专门处理非代码领域的产品管理任务:
- PRD (产品需求文档) 撰写
- RICE/MoSCoW 优先级评估
- 用户故事 (User Story) 映射
- 竞品分析报告
"""

import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.executor import Executor, Task, ExecutionResult, TaskStatus


logger = logging.getLogger(__name__)


class ProductExecutor(Executor):
    """
    产品管理执行器
    
    用于处理非代码的产品规划和需求分析任务，
    体现 SuperAgent 从 "Coding Assistant" 向 "Professional Agent" 的演进。
    """

    def __init__(self, name: str = "ProductExecutor"):
        """初始化产品执行器"""
        super().__init__(name)
        self.supported_types = [
            "prd_generation", 
            "priority_evaluation", 
            "user_story_mapping",
            "market_analysis"
        ]

    def get_supported_types(self) -> List[str]:
        """获取支持的任务类型"""
        return self.supported_types

    def execute(self, task: Task) -> ExecutionResult:
        """
        执行产品管理任务
        
        Args:
            task: 产品任务
                - task_type: prd_generation | priority_evaluation | ...
                - description: 核心目标/背景
                - requirements: 具体包含的模块
                - context: 
                    - target_audience: 目标用户
                    - constraints: 资源/时间约束
                    - metrics: 成功指标
        """
        start_time = time.time()
        logger.info(f"[{self.name}] 开始执行任务: {task.task_type}")

        try:
            # 根据任务类型路由到内部处理逻辑
            if task.task_type == "prd_generation":
                content = self._generate_prd(task)
            elif task.task_type == "priority_evaluation":
                content = self._evaluate_priority(task)
            elif task.task_type == "user_story_mapping":
                content = self._map_user_stories(task)
            else:
                # 默认生成通用分析报告
                content = self._generate_generic_report(task)

            execution_time = time.time() - start_time
            
            return ExecutionResult(
                success=True,
                content=content,
                status=TaskStatus.COMPLETED,
                execution_time=execution_time,
                metadata={
                    "task_type": task.task_type,
                    "generated_at": datetime.now().isoformat(),
                    "framework": "SuperAgent-NonCode-v1"
                }
            )

        except Exception as e:
            logger.error(f"[{self.name}] 任务执行失败: {str(e)}")
            return ExecutionResult(
                success=False,
                content=None,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )

    def _generate_prd(self, task: Task) -> str:
        """生成 PRD 文档 (模拟 LLM 输出)"""
        return f"""# 产品需求文档 (PRD): {task.description}

## 1. 项目背景
{task.description}

## 2. 目标用户
{task.context.get('target_audience', '通用用户')}

## 3. 核心功能
{chr(10).join([f'- {req}' for req in task.requirements])}

## 4. 成功指标 (KPI)
{task.context.get('metrics', '用户活跃度、任务完成率')}

## 5. 风险与约束
{task.context.get('constraints', '无明确约束')}
"""

    def _evaluate_priority(self, task: Task) -> Dict[str, Any]:
        """使用 RICE 模型进行优先级评估"""
        results = []
        for req in task.requirements:
            # 模拟评估得分
            results.append({
                "feature": req,
                "reach": 8,
                "impact": 3,
                "confidence": 0.8,
                "effort": 5,
                "rice_score": (8 * 3 * 0.8) / 5
            })
        
        # 按得分排序
        results.sort(key=lambda x: x['rice_score'], reverse=True)
        return {"prioritized_features": results, "methodology": "RICE Framework"}

    def _map_user_stories(self, task: Task) -> str:
        """生成用户故事地图"""
        stories = []
        for req in task.requirements:
            stories.append(f"作为 [用户], 我想要 [{req}], 以便 [实现业务价值]")
        
        return "\n".join(stories)

    def _generate_generic_report(self, task: Task) -> str:
        """生成通用分析报告"""
        return f"针对 {task.description} 的通用分析报告已生成。"
