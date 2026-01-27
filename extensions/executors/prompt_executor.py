#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提示词优化执行器

实现提示词优化功能，将模糊需求转化为结构化提示词。
支持直接优化、引导式交互和提示词精炼三种模式。
"""

import logging
import time
from typing import Any, Dict, List, Optional

from core.executor import Executor, Task, ExecutionResult, TaskStatus

from .prompt_templates import PromptTemplateLibrary, PromptTemplate

logger = logging.getLogger(__name__)


class PromptExecutor(Executor):
    """
    提示词优化执行器

    将模糊需求转化为结构化提示词，支持：
    - 直接优化 (prompt_optimize): 输入完整时直接生成结构化提示词
    - 引导式交互 (prompt_generate): 识别缺失信息，返回引导问题
    - 提示词精炼 (prompt_refine): 基于反馈改进现有提示词

    Example:
        >>> executor = PromptExecutor()
        >>> result = executor.execute(Task(
        ...     task_type="prompt_generate",
        ...     description="我想写个小红书文案"
        ... ))
        >>> print(result.content)  # {"status": "need_more_info", "questions": [...]}
    """

    def __init__(self, name: str = "PromptExecutor"):
        """
        初始化提示词执行器

        Args:
            name: 执行器名称
        """
        super().__init__(name)
        self.template_library = PromptTemplateLibrary()

    def get_supported_types(self) -> List[str]:
        """
        获取支持的任务类型

        Returns:
            List[str]: 支持的任务类型列表
        """
        return [
            "prompt_optimize",   # 直接优化
            "prompt_generate",   # 引导式生成
            "prompt_refine",     # 精炼提示词
        ]

    def execute(self, task: Task) -> ExecutionResult:
        """
        执行提示词优化任务

        Args:
            task: 提示词任务
                - task_type: 任务类型 (prompt_optimize/prompt_generate/prompt_refine)
                - description: 任务描述/原始需求
                - context: 额外上下文
                - requirements: 任务要求列表

        Returns:
            ExecutionResult: 执行结果
        """
        start_time = time.time()

        try:
            if not self.validate_task(task):
                return ExecutionResult(
                    success=False,
                    content=None,
                    status=TaskStatus.FAILED,
                    error="Invalid task",
                    execution_time=time.time() - start_time
                )

            task_type = task.task_type

            if task_type == "prompt_optimize":
                return self._direct_optimize(task, start_time)
            elif task_type == "prompt_generate":
                return self._generate_prompt(task, start_time)
            elif task_type == "prompt_refine":
                return self._refine_prompt(task, start_time)
            else:
                return ExecutionResult(
                    success=False,
                    content=None,
                    status=TaskStatus.FAILED,
                    error=f"Unknown task type: {task_type}",
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            logger.error(f"Prompt execution failed: {e}", exc_info=True)
            return ExecutionResult(
                success=False,
                content=None,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )

    def _direct_optimize(self, task: Task, start_time: float) -> ExecutionResult:
        """
        直接优化：输入完整，直接生成结构化提示词

        Args:
            task: 任务
            start_time: 开始时间

        Returns:
            ExecutionResult: 包含结构化提示词
        """
        requirement = task.description
        context = task.context

        # 1. 链式推理分析需求
        thinking = self._chain_of_thought_analyze(requirement, context)

        # 2. 构建替换字典
        replacements = self._build_replacements(requirement, context)

        # 3. 获取模板类型
        template_type = context.get("template_type", self._infer_template_type(requirement))

        # 4. 结构化构建提示词
        structured_prompt = self._build_structured_prompt(
            requirement=requirement,
            role=context.get("role", ""),
            context=context.get("context", ""),
            goals=context.get("goals", ""),
            constraints=context.get("constraints", []),
            workflow=context.get("workflow", []),
            output_format=context.get("output_format", ""),
            template_type=template_type,
            replacements=replacements
        )

        execution_time = time.time() - start_time

        return ExecutionResult(
            success=True,
            content=structured_prompt,
            status=TaskStatus.COMPLETED,
            metadata={
                "thinking": thinking,
                "template_type": template_type,
                "replacements": replacements
            },
            execution_time=execution_time
        )

    def _generate_prompt(self, task: Task, start_time: float) -> ExecutionResult:
        """
        生成提示词：引导式交互

        识别需求中缺失的关键信息，返回引导问题列表。

        Args:
            task: 任务
            start_time: 开始时间

        Returns:
            ExecutionResult: 包含引导问题
        """
        requirement = task.description

        # 1. 快速分析
        thinking = self._quick_thinking(requirement)

        # 2. 识别缺失信息
        missing_info = self._identify_missing_info(requirement)

        # 3. 推断模板类型
        template_type = self._infer_template_type(requirement)
        template_fields = self.template_library.get_template_fields(template_type)

        execution_time = time.time() - start_time

        if missing_info:
            # 返回引导问题
            return ExecutionResult(
                success=True,
                content={
                    "status": "need_more_info",
                    "questions": missing_info,
                    "thinking": thinking,
                    "suggested_template": template_type,
                    "template_fields": [
                        {"key": f.key, "label": f.label, "description": f.description}
                        for f in template_fields
                    ]
                },
                status=TaskStatus.COMPLETED,
                metadata={
                    "thinking": thinking,
                    "template_type": template_type
                },
                execution_time=execution_time
            )
        else:
            # 信息完整，直接优化
            task.context["template_type"] = template_type
            return self._direct_optimize(task, start_time)

    def _refine_prompt(self, task: Task, start_time: float) -> ExecutionResult:
        """
        精炼提示词：基于反馈改进

        Args:
            task: 任务
            start_time: 开始时间

        Returns:
            ExecutionResult: 包含精炼后的提示词
        """
        original_prompt = task.context.get("prompt", "")
        feedback = task.context.get("feedback", "")
        requirements = task.requirements

        # 1. 分析反馈
        thinking = self._refine_thinking(original_prompt, feedback, requirements)

        # 2. 基于反馈精炼
        refined = self._refine_with_feedback(original_prompt, feedback, requirements)

        execution_time = time.time() - start_time

        return ExecutionResult(
            success=True,
            content=refined,
            status=TaskStatus.COMPLETED,
            metadata={
                "thinking": thinking,
                "original_length": len(original_prompt),
                "refined_length": len(refined)
            },
            execution_time=execution_time
        )

    def _build_replacements(self, requirement: str, context: Dict) -> Dict[str, str]:
        """构建模板替换字典"""
        replacements = {
            "topic": requirement,
            "task": requirement,
            "requirement": requirement,
        }

        # 添加上下文中的值
        for key, value in context.items():
            if isinstance(value, str):
                replacements[key] = value
            else:
                replacements[key] = str(value)

        return replacements

    def _infer_template_type(self, requirement: str) -> str:
        """推断模板类型"""
        requirement_lower = requirement.lower()

        # 写作相关关键词
        writing_keywords = ["写", "文章", "文案", "博客", "文档", "内容", "创作", "撰写"]
        if any(kw in requirement for kw in writing_keywords):
            return "writing"

        # 编程相关关键词
        coding_keywords = ["代码", "编程", "开发", "实现", "函数", "类", "程序", "api", "接口"]
        if any(kw in requirement_lower for kw in coding_keywords):
            return "coding"

        # 分析相关关键词
        analysis_keywords = ["分析", "研究", "报告", "调研", "数据", "洞察", "趋势"]
        if any(kw in requirement for kw in analysis_keywords):
            return "analysis"

        return "general"

    def _build_structured_prompt(
        self,
        requirement: str,
        role: str,
        context: str,
        goals: str,
        constraints: List[str],
        workflow: List[str],
        output_format: str,
        template_type: str,
        replacements: Dict[str, str]
    ) -> str:
        """
        构建结构化提示词

        输出格式：
        [Role]
        xxx

        [Context]
        xxx

        [Goals]
        xxx

        [Constraints]
        1. xxx
        2. xxx

        [Workflow]
        1. xxx
        2. xxx

        [Output Format]
        xxx
        """
        template = self.template_library.get_template(template_type)

        prompt_parts = []

        # [Role]
        prompt_parts.append("[Role]")
        prompt_parts.append(role or template.role)
        prompt_parts.append("")

        # [Context]
        prompt_parts.append("[Context]")
        if context:
            prompt_parts.append(context)
        else:
            context_text = template.context_pattern
            for key, value in replacements.items():
                context_text = context_text.replace(f"{{{key}}}", value)
            prompt_parts.append(context_text)
        prompt_parts.append("")

        # [Goals]
        prompt_parts.append("[Goals]")
        if goals:
            prompt_parts.append(goals)
        else:
            goals_text = template.goals_pattern
            for key, value in replacements.items():
                goals_text = goals_text.replace(f"{{{key}}}", value)
            prompt_parts.append(goals_text)
        prompt_parts.append("")

        # [Constraints]
        prompt_parts.append("[Constraints]")
        if constraints:
            for i, c in enumerate(constraints, 1):
                prompt_parts.append(f"{i}. {c}")
        else:
            for i, c in enumerate(template.constraints_pattern, 1):
                formatted_c = c
                for key, value in replacements.items():
                    formatted_c = formatted_c.replace(f"{{{key}}}", value)
                prompt_parts.append(f"{i}. {formatted_c}")
        prompt_parts.append("")

        # [Workflow]
        prompt_parts.append("[Workflow]")
        if workflow:
            for i, w in enumerate(workflow, 1):
                prompt_parts.append(f"{i}. {w}")
        else:
            workflow_text = template.workflow_pattern
            for key, value in replacements.items():
                workflow_text = workflow_text.replace(f"{{{key}}}", value)
            prompt_parts.append(workflow_text)
        prompt_parts.append("")

        # [Output Format]
        prompt_parts.append("[Output Format]")
        if output_format:
            prompt_parts.append(output_format)
        else:
            output_text = template.output_format_pattern
            for key, value in replacements.items():
                output_text = output_text.replace(f"{{{key}}}", value)
            prompt_parts.append(output_text)

        return "\n".join(prompt_parts)

    def _chain_of_thought_analyze(self, requirement: str, context: Dict) -> str:
        """
        链式推理分析需求

        使用 <Thinking> 标签展示分析过程。
        """
        thinking_parts = [
            "<Thinking>",
            f"分析原始需求: {requirement}",
            f"上下文信息: {context}",
        ]

        # 推断模板类型
        template_type = self._infer_template_type(requirement)
        thinking_parts.append(f"推断模板类型: {template_type}")

        # 分析关键要素
        thinking_parts.append(f"关键要素:")
        for key, value in context.items():
            thinking_parts.append(f"  - {key}: {value}")

        thinking_parts.append("</Thinking>")

        return "\n".join(thinking_parts)

    def _quick_thinking(self, requirement: str) -> str:
        """快速分析需求"""
        template_type = self._infer_template_type(requirement)

        return f"""<Thinking>
快速分析需求: {requirement}
推断模板类型: {template_type}
检查信息完整性...
</Thinking>"""

    def _refine_thinking(
        self,
        original_prompt: str,
        feedback: str,
        requirements: List[str]
    ) -> str:
        """精炼分析"""
        return f"""<Thinking>
分析原始提示词: {original_prompt[:100]}...
收到的反馈: {feedback}
额外要求: {requirements}
识别需要改进的方面...
</Thinking>"""

    def _identify_missing_info(self, requirement: str) -> List[Dict[str, str]]:
        """
        识别需求中缺失的关键信息

        Returns:
            List[Dict]: 包含问题信息的列表
        """
        questions = []
        requirement_lower = requirement.lower()

        # 目标受众
        if not any(kw in requirement for kw in ["受众", "读者", "用户", "audience"]):
            questions.append({
                "key": "audience",
                "question": "目标受众是谁？（如：技术从业者/新手/大众）",
                "importance": "high"
            })

        # 目的/目标
        if not any(kw in requirement for kw in ["目的", "目标", "goal", "用途"]):
            questions.append({
                "key": "purpose",
                "question": "你希望通过这个提示词达到什么目的？",
                "importance": "high"
            })

        # 风格/语气
        if not any(kw in requirement for kw in ["风格", "语气", "tone", "style"]):
            questions.append({
                "key": "style",
                "question": "期望的语气风格是什么？（专业/轻松/正式/幽默）",
                "importance": "medium"
            })

        # 字数/长度
        if not any(kw in requirement for kw in ["字数", "长度", "length", "多少"]):
            questions.append({
                "key": "length",
                "question": "有字数或长度限制吗？",
                "importance": "low"
            })

        # 模板特定的问题
        template_type = self._infer_template_type(requirement)

        if template_type == "writing":
            if not any(kw in requirement for kw in ["文章", "文案", "博客", "类型"]):
                questions.append({
                    "key": "content_type",
                    "question": "这是什么类型的内容？（文章/博客/营销文案/社交媒体）",
                    "importance": "high"
                })
        elif template_type == "coding":
            if not any(kw in requirement_lower for kw in ["语言", "language", "python", "javascript"]):
                questions.append({
                    "key": "language",
                    "question": "使用什么编程语言？",
                    "importance": "high"
                })
        elif template_type == "analysis":
            if not any(kw in requirement for kw in ["分析", "数据", "主题"]):
                questions.append({
                    "key": "subject",
                    "question": "分析的主题或数据是什么？",
                    "importance": "high"
                })

        return questions[:4]  # 最多返回4个问题

    def _refine_with_feedback(
        self,
        original_prompt: str,
        feedback: str,
        requirements: List[str]
    ) -> str:
        """
        基于反馈精炼提示词

        在原始提示词基础上添加改进建议。
        """
        refined = original_prompt.rstrip()

        # 添加改进部分
        improvements = ["\n\n[改进建议]", "=" * 40]

        if feedback:
            improvements.append(f"收到的反馈:\n{feedback}")

        if requirements:
            improvements.append("\n需要改进的地方:")
            for i, req in enumerate(requirements, 1):
                improvements.append(f"{i}. {req}")

        improvements.append("\n" + "=" * 40)
        improvements.append("请根据以上反馈优化提示词。")

        refined += "\n".join(improvements)

        return refined

    def preview_template(self, template_type: str, context: Dict = None) -> str:
        """
        预览模板效果

        Args:
            template_type: 模板类型
            context: 上下文信息

        Returns:
            str: 格式化后的模板预览
        """
        template = self.template_library.get_template(template_type)
        context = context or {}

        # 构建替换字典
        replacements = {
            "topic": "示例主题",
            "task": "示例任务",
            "requirement": "示例需求",
        }
        replacements.update(context)

        return self._build_structured_prompt(
            requirement="示例主题",
            role="",
            context="",
            goals="",
            constraints=[],
            workflow=[],
            output_format="",
            template_type=template_type,
            replacements=replacements
        )

    def __repr__(self) -> str:
        return (
            f"PromptExecutor("
            f"name={self.name}, "
            f"templates={self.template_library.list_templates()})"
        )
