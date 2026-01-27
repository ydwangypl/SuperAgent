#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提示词模板库

提供各种类型的提示词模板，支持写作、编程、分析等场景的结构化提示词生成。
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class PromptTemplate:
    """
    提示词模板

    用于将模糊需求转化为结构化提示词。

    Attributes:
        name: 模板名称
        role: 角色定义
        context_pattern: 上下文模式
        goals_pattern: 目标模式
        constraints_pattern: 约束模式（列表）
        workflow_pattern: 工作流模式
        output_format_pattern: 输出格式模式
    """
    name: str
    role: str
    context_pattern: str
    goals_pattern: str
    constraints_pattern: List[str]
    workflow_pattern: str
    output_format_pattern: str


@dataclass
class PromptField:
    """提示词字段定义"""
    key: str
    label: str
    description: str
    required: bool = False
    default: Any = None
    options: List[str] = None


class PromptTemplateLibrary:
    """
    提示词模板库

    提供多种场景的提示词模板，支持获取和自定义。
    """

    # 模板配置字段
    TEMPLATE_FIELDS: Dict[str, List[PromptField]] = {
        "writing": [
            PromptField("audience", "目标受众", "谁会阅读这个内容？", True),
            PromptField("content_type", "内容类型", "文章/博客/文档/营销文案", True),
            PromptField("style", "写作风格", "专业/轻松/正式/幽默", False, "professional"),
            PromptField("length", "长度要求", "字数限制", False, "1000字"),
        ],
        "coding": [
            PromptField("language", "编程语言", "Python/JavaScript/Go等", True),
            PromptField("feature", "功能描述", "要实现的功能", True),
            PromptField("style_guide", "代码规范", "PEP8/Google Style等", False, "PEP8"),
            PromptField("framework", "使用的框架", "Django/FastAPI/React等", False),
        ],
        "analysis": [
            PromptField("subject", "分析主题", "要分析的主题或数据", True),
            PromptField("analysis_type", "分析类型", "趋势/比较/因果/预测", True),
            PromptField("data_source", "数据来源", "数据从哪里来", False),
            PromptField("stakeholders", "利益相关者", "谁会使用这个分析", False),
        ],
        "general": [
            PromptField("task", "任务描述", "要完成的任务", True),
            PromptField("constraints", "约束条件", "有什么限制", False),
            PromptField("priority", "优先级", "什么是重点", False),
        ]
    }

    def __init__(self):
        """初始化模板库"""
        self.templates = {
            "writing": self._writing_template(),
            "coding": self._coding_template(),
            "analysis": self._analysis_template(),
            "general": self._general_template()
        }
        logger.debug(f"PromptTemplateLibrary initialized with {len(self.templates)} templates")

    def _writing_template(self) -> PromptTemplate:
        """写作模板"""
        return PromptTemplate(
            name="写作",
            role="资深文案/内容创作者，擅长用清晰、吸引人的方式传达信息",
            context_pattern="为{audience}创作{content_type}",
            goals_pattern="创作一篇{length}的{style}风格文章，主题是{topic}。文章应该：\n1. 吸引目标读者的注意力\n2. 提供有价值的信息或见解\n3. 结构清晰，逻辑连贯",
            constraints_pattern=[
                "避免使用生僻词汇，确保通俗易懂",
                "保持段落短小，每段不超过100字",
                "使用生动的例子和数据支持观点",
                "避免过度使用专业术语",
                "字数控制在{length}以内"
            ],
            workflow_pattern="1. 确定核心主题和论点\n2. 了解目标受众的痛点和需求\n3. 收集相关素材和数据\n4. 撰写初稿，梳理结构\n5. 润色修改，优化表达\n6. 检查语法和格式",
            output_format_pattern="""```markdown
# 标题

## 引言
简要介绍主题，吸引读者继续阅读。

## 正文
### 小标题1
内容...

### 小标题2
内容...

### 小标题3
内容...

## 结论
总结主要观点，给出建议或展望。
```"""
        )

    def _coding_template(self) -> PromptTemplate:
        """编程模板"""
        return PromptTemplate(
            name="编程",
            role="资深{language}开发者，注重代码质量、可维护性和性能优化",
            context_pattern="开发{feature}功能，使用{language}语言{framework_suffix}",
            goals_pattern="实现{requirement}，满足以下要求：\n{requirements}",
            constraints_pattern=[
                "遵循{style_guide}代码规范",
                "添加清晰的注释说明关键逻辑",
                "处理边界情况和异常",
                "保持函数短小，单一职责",
                "使用有意义的变量和函数名",
                "包含必要的单元测试"
            ],
            workflow_pattern="1. 分析需求，设计架构\n2. 编写代码，实现核心功能\n3. 处理错误和异常情况\n4. 编写单元测试\n5. 代码审查和优化\n6. 更新文档",
            output_format_pattern="""```python
# 代码实现
def function_name():
    '''函数说明'''
    pass

# 测试用例
def test_function():
    pass
```\n\n**使用说明**\n1. 安装依赖...\n2. 配置环境...\n3. 运行程序..."""
        )

    def _analysis_template(self) -> PromptTemplate:
        """分析模板"""
        return PromptTemplate(
            name="分析",
            role="专业数据分析师，擅长从数据中发现洞察并提供可执行的建议",
            context_pattern="对{subject}进行{type}分析{audience_suffix}",
            goals_pattern="回答以下问题：\n{questions}",
            constraints_pattern=[
                "基于数据支持结论，避免主观臆断",
                "提供可执行的建议和行动计划",
                "说明分析的局限性和假设",
                "使用可视化图表展示关键发现",
                "区分事实和推断"
            ],
            workflow_pattern="1. 明确分析目标和问题\n2. 收集和清洗数据\n3. 探索性数据分析\n4. 深入分析和建模\n5. 得出结论和洞察\n6. 提出建议和行动计划\n7. 撰写分析报告",
            output_format_pattern="""# 分析报告：{主题}

## 执行摘要
简明扼要地总结分析目的、方法和关键发现。

## 分析背景
说明分析的背景和动机。

## 数据概况
描述数据来源、规模和主要特征。

## 关键发现
### 发现1
- 数据支撑
- 业务影响

### 发现2
- 数据支撑
- 业务影响

## 建议
基于发现的可行建议。

## 局限性
说明分析的局限性和后续改进方向。"""
        )

    def _general_template(self) -> PromptTemplate:
        """通用模板"""
        return PromptTemplate(
            name="通用",
            role="AI 助手，擅长理解需求并提供高质量的解决方案",
            context_pattern="帮助用户完成{task}",
            goals_pattern="完成{task}，满足以下要求：\n{requirements}",
            constraints_pattern=[
                "提供清晰、准确的回答",
                "如有必要，给出具体的步骤",
                "使用通俗易懂的语言",
                "考虑用户的实际使用场景",
                "在回答前先确认理解是否正确"
            ],
            workflow_pattern="1. 理解需求，明确任务目标\n2. 分析问题的关键要素\n3. 制定解决方案或回答策略\n4. 执行并提供结果\n5. 验证结果是否满足需求",
            output_format_pattern="根据任务类型自适应：\n- 回答类：直接给出答案+解释\n- 任务类：步骤说明+结果\n- 创意类：提供多个选项"
        )

    def get_template(self, template_type: str) -> PromptTemplate:
        """
        获取指定类型的模板

        Args:
            template_type: 模板类型 (writing/coding/analysis/general)

        Returns:
            PromptTemplate: 提示词模板
        """
        template = self.templates.get(template_type)
        if template:
            return template
        logger.warning(f"Template type '{template_type}' not found, using 'general'")
        return self.templates["general"]

    def get_template_fields(self, template_type: str) -> List[PromptField]:
        """
        获取模板的配置字段

        Args:
            template_type: 模板类型

        Returns:
            List[PromptField]: 字段定义列表
        """
        return self.TEMPLATE_FIELDS.get(template_type, [])

    def format_template(
        self,
        template_type: str,
        replacements: Dict[str, str]
    ) -> str:
        """
        格式化模板

        Args:
            template_type: 模板类型
            replacements: 替换值字典

        Returns:
            str: 格式化后的模板字符串
        """
        template = self.get_template(template_type)

        # 格式化各个部分
        parts = []

        # [Role]
        parts.append("[Role]")
        parts.append(template.role)
        parts.append("")

        # [Context]
        parts.append("[Context]")
        context = template.context_pattern
        for key, value in replacements.items():
            context = context.replace(f"{{{key}}}", str(value))
        parts.append(context)
        parts.append("")

        # [Goals]
        parts.append("[Goals]")
        goals = template.goals_pattern
        for key, value in replacements.items():
            goals = goals.replace(f"{{{key}}}", str(value))
        parts.append(goals)
        parts.append("")

        # [Constraints]
        parts.append("[Constraints]")
        for i, constraint in enumerate(template.constraints_pattern, 1):
            formatted_constraint = constraint
            for key, value in replacements.items():
                formatted_constraint = formatted_constraint.replace(f"{{{key}}}", str(value))
            parts.append(f"{i}. {formatted_constraint}")
        parts.append("")

        # [Workflow]
        parts.append("[Workflow]")
        workflow = template.workflow_pattern
        for key, value in replacements.items():
            workflow = workflow.replace(f"{{{key}}}", str(value))
        parts.append(workflow)
        parts.append("")

        # [Output Format]
        parts.append("[Output Format]")
        output_format = template.output_format_pattern
        for key, value in replacements.items():
            output_format = output_format.replace(f"{{{key}}}", str(value))
        parts.append(output_format)

        return "\n".join(parts)

    def list_templates(self) -> List[str]:
        """列出所有可用的模板类型"""
        return list(self.templates.keys())

    def __repr__(self) -> str:
        return f"PromptTemplateLibrary(templates={list(self.templates.keys())})"


# 便捷函数
def get_template(template_type: str) -> PromptTemplate:
    """获取提示词模板"""
    library = PromptTemplateLibrary()
    return library.get_template(template_type)


def format_template(template_type: str, replacements: Dict[str, str]) -> str:
    """格式化提示词模板"""
    library = PromptTemplateLibrary()
    return library.format_template(template_type, replacements)
