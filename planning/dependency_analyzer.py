#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
依赖分析器

分析步骤之间的依赖关系
"""

import logging
from typing import List, Dict, Set

from .models import Step, DependencyGraph, RequirementAnalysis

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """依赖分析器"""

    def __init__(self):
        pass

    def analyze_dependencies(
        self,
        steps: List[Step],
        analysis: RequirementAnalysis
    ) -> DependencyGraph:
        """分析步骤依赖关系

        Args:
            steps: 步骤列表
            analysis: 需求分析

        Returns:
            DependencyGraph: 依赖关系图
        """
        graph = DependencyGraph()

        # 添加所有步骤到图中
        for step in steps:
            graph.add_step(step)

        # 应用预定义的依赖规则
        self._apply_dependency_rules(graph, analysis)

        return graph

    def _apply_dependency_rules(
        self,
        graph: DependencyGraph,
        analysis: RequirementAnalysis
    ):
        """应用依赖规则

        规则:
        1. 产品设计必须最前
        2. 数据库设计在后端API之前
        3. 前端开发依赖API设计
        4. 测试在功能开发之后
        """

        # 这些规则已经在生成步骤时应用
        # 这里可以添加额外的智能分析

        # 检测循环依赖
        if len(graph.nodes) > 1 and self._has_circular_dependency(graph):
            logger.warning("检测到潜在的循环依赖，正在尝试优化...")
            # 可以在这里添加自动解除循环依赖的逻辑，或者抛出异常
            # raise ValueError("检测到循环依赖，无法生成执行计划")

        # 优化: 识别可以并行的步骤
        self._identify_parallel_opportunities(graph)

    def _has_circular_dependency(self, graph: DependencyGraph) -> bool:
        """检测是否有循环依赖"""
        visited = set()
        rec_stack = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = graph.nodes.get(node_id)
            if not node:
                return False

            for dep_id in node.dependencies:
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for node_id in graph.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    return True

        return False

    def _identify_parallel_opportunities(self, graph: DependencyGraph):
        """识别并标记可并行的步骤"""
        groups = graph.get_parallel_groups()
        
        # 凡是属于同一层且层内有多个步骤的, 都可以初步认为是可并行的
        # 注意: 这里的 can_parallel 标记主要用于编排参考
        for group in groups:
            if len(group) > 1:
                # 理论上这些步骤可以并行
                pass

    def get_execution_order(self, graph: DependencyGraph) -> List[List[str]]:
        """获取执行顺序

        返回步骤组列表,每一组的步骤可以并行执行

        Returns:
            List[List[str]]: 每个元素是一组可并行执行的步骤ID
        """
        order = []
        remaining = set(graph.nodes.keys())

        while remaining:
            # 找出所有依赖已满足的步骤
            ready = []
            for step_id in remaining:
                node = graph.nodes[step_id]
                # 所有依赖都不在remaining中(已执行)
                if all(dep not in remaining for dep in node.dependencies):
                    ready.append(step_id)

            if not ready:
                # 无法继续,有循环依赖
                raise ValueError("无法计算执行顺序: 检测到循环依赖")

            order.append(ready)
            # 移除已执行的步骤
            for step_id in ready:
                remaining.remove(step_id)

        return order

    def estimate_critical_path(
        self,
        steps: List[Step],
        graph: DependencyGraph
    ) -> int:
        """估算关键路径长度(分钟) - 使用记忆化优化"""
        step_map = {s.id: s for s in steps}
        memo = {}

        def get_path_time(step_id: str) -> int:
            """获取到该步骤为止的最长路径时间"""
            if step_id in memo:
                return memo[step_id]
                
            step = step_map.get(step_id)
            if not step:
                return 0

            # 基础时间
            base_time = int(step.estimated_time.total_seconds() / 60)

            # 递归计算所有前置依赖路径的最长时间
            dep_times = []
            for dep_id in graph.nodes[step_id].dependencies:
                dep_times.append(get_path_time(dep_id))

            # 当前步骤时间 + 依赖路径的最长时间
            result = base_time + (max(dep_times) if dep_times else 0)
            memo[step_id] = result
            return result

        if not graph.nodes:
            return 0
            
        # 计算所有步骤的路径时间,返回最大值
        return max(get_path_time(step_id) for step_id in graph.nodes.keys())
