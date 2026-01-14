#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模型转换器 (Mappers)

负责编排层模型与跨层契约模型之间的转换。
"""

from typing import Dict, Any, List
from pathlib import Path
from .models import TaskExecution, ExecutionContext, OrchestrationConfig
from execution.models import AgentContext, AgentResult
from common.schemas import ReviewRequest, ReviewResponse


class OrchestrationMapper:
    """编排层转换器"""

    @staticmethod
    def to_review_request(
        project_id: str,
        files: List[Path],
        config: OrchestrationConfig
    ) -> ReviewRequest:
        """转换为审查请求契约"""
        return ReviewRequest(
            project_id=project_id,
            files=files,
            enable_style_check=config.enable_style_check,
            enable_security_check=config.enable_security_check,
            enable_performance_check=config.enable_performance_check,
            enable_best_practices=config.enable_best_practices,
            enable_ralph_wiggum=config.enable_ralph_wiggum,
            max_iterations=config.max_iterations,
            min_overall_score=config.min_overall_score
        )

    @staticmethod
    def to_agent_context(
        task_execution: TaskExecution,
        global_context: ExecutionContext
    ) -> AgentContext:
        """转换为 Agent 执行上下文"""
        worktree_path = task_execution.worktree_path or global_context.worktree_path

        return AgentContext(
            project_root=global_context.project_root,
            task_id=task_execution.task_id,
            step_id=task_execution.step_id,
            worktree_path=worktree_path,
            token_monitor=global_context.token_monitor,
            dependencies=task_execution.dependencies,
            # 可以在这里添加更多从 global_context 或 task_execution 映射的字段
        )

    @staticmethod
    def from_review_result(review_result: Any) -> ReviewResponse:
        """从审查结果转换为响应契约 (使用 Any 避免直接依赖)"""
        return ReviewResponse(
            success=review_result.status.value == "completed",
            score=review_result.metrics.overall_score,
            issues=[
                {
                    "category": i.category.value,
                    "severity": i.severity.value,
                    "title": i.title,
                    "description": i.description,
                    "file_path": str(i.file_path) if i.file_path else None,
                    "line_number": i.line_number,
                    "suggestion": i.suggestion
                }
                for i in review_result.issues
            ],
            summary=review_result.summary,
            recommendations=review_result.recommendations,
            improved_code=review_result.improved_code
        )

    @staticmethod
    def from_agent_result(agent_result: AgentResult) -> Dict[str, Any]:
        """将 Agent 结果转换为 TaskExecution 可接受的字典格式"""
        return {
            "task_id": agent_result.task_id,
            "step_id": agent_result.step_id,
            "agent_id": agent_result.agent_id,
            "status": agent_result.status.value,
            "success": agent_result.success,
            "message": agent_result.message,
            "artifacts": [
                {
                    "artifact_id": a.artifact_id,
                    "artifact_type": a.artifact_type,
                    "path": str(a.path) if a.path else None,
                    "content_length": len(a.content) if a.content else 0,
                    "quality_score": a.quality_score,
                    "metadata": a.metadata
                }
                for a in agent_result.artifacts
            ],
            "logs": agent_result.logs,
            "metrics": agent_result.metrics,
            "error": agent_result.error,
            "files": [
                str(a.path)
                for a in agent_result.artifacts
                if a.path
            ]
        }
