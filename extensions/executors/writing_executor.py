#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
写作执行器

实现内容写作功能,验证架构的可扩展性。
这个执行器不依赖Agent系统,是独立实现。
"""

import logging
from typing import List
from datetime import datetime

from core.executor import Executor, Task, ExecutionResult, TaskStatus


logger = logging.getLogger(__name__)


class WritingExecutor(Executor):
    """
    写作执行器

    用于生成各种类型的内容:
    - 文章
    - 博客
    - 文档
    - 营销文案
    - 社交媒体内容

    这是一个独立的实现,不依赖现有的Agent系统,
    用于验证新架构确实支持多领域扩展。
    """

    def __init__(self, name: str = "WritingExecutor"):
        """
        初始化写作执行器

        Args:
            name: 执行器名称
        """
        super().__init__(name)
        self.supported_types = ["writing", "content", "article", "blog", "documentation"]

    def get_supported_types(self) -> List[str]:
        """获取支持的任务类型"""
        return self.supported_types

    def execute(self, task: Task) -> ExecutionResult:
        """
        执行写作任务

        Args:
            task: 写作任务
                - task_type: 内容类型
                - description: 内容主题/要求
                - requirements: 具体要求列表
                - context: 额外上下文
                    - tone: 语气 (professional, casual, friendly)
                    - length: 字数要求
                    - audience: 目标受众
                    - keywords: 关键词列表

        Returns:
            ExecutionResult: 包含生成的内容
        """
        import time
        start_time = time.time()

        try:
            if not self.validate_task(task):
                return ExecutionResult(
                    success=False,
                    content=None,
                    status=TaskStatus.FAILED,
                    error="Invalid task"
                )

            # 提取上下文参数
            tone = task.context.get("tone", "professional")
            length = task.context.get("length", 500)
            audience = task.context.get("audience", "general")
            keywords = task.context.get("keywords", [])

            # 模拟内容生成 (实际应用中会调用LLM)
            logger.info(f"Generating {task.task_type} with tone={tone}, length={length}")

            content = self._generate_content(
                topic=task.description,
                content_type=task.task_type,
                tone=tone,
                length=length,
                audience=audience,
                keywords=keywords,
                requirements=task.requirements
            )

            execution_time = time.time() - start_time

            return ExecutionResult(
                success=True,
                content=content,
                status=TaskStatus.COMPLETED,
                metadata={
                    "word_count": len(content.split()),
                    "tone": tone,
                    "audience": audience,
                    "keywords_included": keywords
                },
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Writing execution failed: {e}", exc_info=True)
            execution_time = time.time() - start_time

            return ExecutionResult(
                success=False,
                content=None,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=execution_time
            )

    def _generate_content(
        self,
        topic: str,
        content_type: str,
        tone: str,
        length: int,
        audience: str,
        keywords: List[str],
        requirements: List[str]
    ) -> str:
        """
        生成内容

        注意: 这是模拟实现。实际应用中会调用LLM API。
        这里我们生成一个模板内容来演示。
        """
        # 根据内容类型选择模板
        if content_type == "article":
            template = self._article_template()
        elif content_type == "blog":
            template = self._blog_template()
        elif content_type == "documentation":
            template = self._documentation_template()
        else:
            template = self._generic_template()

        # 填充模板
        content = template.format(
            topic=topic,
            tone_description=self._get_tone_description(tone),
            audience_description=audience,
            requirements_description=self._format_requirements(requirements),
            keywords_description=self._format_keywords(keywords)
        )

        # 调整长度 (模拟)
        if len(content) < length:
            # 扩展内容
            content += "\n\n" + self._extension_paragraph(topic, tone)

        return content

    def _article_template(self) -> str:
        """文章模板"""
        return """# {topic}

## 引言

本文将探讨{topic}这一重要主题。面向{audience_description}群体,我们希望以{tone_description}的方式分享见解。

## 正文

{requirements_description}

{keywords_description}

## 结论

通过以上讨论,我们可以看到{topic}的重要性。希望本文能为读者提供有价值的参考和启发。

## 参考资料

- 相关文献1
- 相关研究2
"""

    def _blog_template(self) -> str:
        """博客模板"""
        return """# {topic}: {tone_description}的分享

大家好!今天我想和大家聊聊{topic}。

## 为什么这个话题很重要?

{requirements_description}

## 我的经验

{keywords_description}

## 总结

{topic}是一个值得深入探讨的话题。希望这篇分享能对大家有所启发!

欢迎在评论区分享你们的想法和经验!
"""

    def _documentation_template(self) -> str:
        """文档模板"""
        return """# {topic} 文档

## 概述

本文档描述{topic}的相关内容,面向{audience_description}。

## 功能说明

{requirements_description}

## 使用指南

{keywords_description}

## 常见问题

### Q1: 如何开始?

A: 请参考上述功能说明逐步进行。

### Q2: 遇到问题怎么办?

A: 请查看故障排除章节或联系支持团队。

## 总结

{topic}的完整介绍如上。如有疑问,请随时联系。
"""

    def _generic_template(self) -> str:
        """通用模板"""
        return """# {topic}

## 概述

{tone_description}的{topic}介绍。

## 详细内容

{requirements_description}

## 补充信息

{keywords_description}

---

*生成时间: {timestamp}*"""

    def _get_tone_description(self, tone: str) -> str:
        """获取语气描述"""
        tone_map = {
            "professional": "专业",
            "casual": "轻松",
            "friendly": "友好",
            "formal": "正式",
            "humorous": "幽默"
        }
        return tone_map.get(tone, tone)

    def _format_requirements(self, requirements: List[str]) -> str:
        """格式化要求列表"""
        if not requirements:
            return "无特殊要求"
        return "\n".join(f"- {req}" for req in requirements)

    def _format_keywords(self, keywords: List[str]) -> str:
        """格式化关键词列表"""
        if not keywords:
            return "无特定关键词"
        return "关键词: " + ", ".join(keywords)

    def _extension_paragraph(self, topic: str, tone: str) -> str:
        """生成扩展段落"""
        return f"""
## 补充说明

关于{topic}的补充信息。

这里提供更多细节,帮助读者更好地理解{topic}的各个方面。以{tone}的语气,我们希望内容既专业又易懂。
"""

    def __repr__(self) -> str:
        return f"WritingExecutor(name={self.name}, types={self.supported_types})"
