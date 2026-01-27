#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自然语言解析器

将自然语言输入转换为结构化的任务请求。

功能:
- 识别任务类型 (coding, research, review, planning, analysis)
- 提取关键实体 (代码标识符、技术栈)
- 清理和标准化描述文本
"""

import re
from typing import Tuple, List
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TaskType(Enum):
    """任务类型枚举"""
    CODING = "coding"
    RESEARCH = "research"
    REVIEW = "review"
    PLANNING = "planning"
    ANALYSIS = "analysis"


@dataclass
class ParsedRequest:
    """解析后的请求"""
    task_type: TaskType
    description: str
    entities: List[str]
    confidence: float

    def to_dict(self) -> dict:
        return {
            "task_type": self.task_type.value,
            "description": self.description,
            "entities": self.entities,
            "confidence": self.confidence
        }


class NaturalLanguageParser:
    """自然语言解析器

    使用模式匹配和关键词识别来解析用户意图。
    """

    # 任务类型关键词映射 (中英双语支持)
    TASK_PATTERNS = {
        TaskType.CODING: [
            # 中文
            r"创建\s*([^\s]+)",
            r"实现\s*([^\s]+)",
            r"开发\s*([^\s]+)",
            r"编写\s*([^\s]+)",
            r"写\s*([^\s]+)",
            r"添加\s*([^\s]+)",
            r"修改\s*([^\s]+)",
            r"更新\s*([^\s]+)",
            r"重构\s*([^\s]+)",
            r"优化\s*([^\s]+)",
            r"修复\s*([^\s]+)",
            r"新增\s*([^\s]+)",
            r"功能\s*",
            r"模块\s*",
            r"代码\s*",
            # 英文
            r"create\s+",
            r"implement\s+",
            r"develop\s+",
            r"build\s+",
            r"write\s+",
            r"add\s+",
            r"modify\s+",
            r"update\s+",
            r"refactor\s+",
            r"optimize\s+",
            r"fix\s+",
            r"feature\s*",
            r"module\s*",
            r"code\s*",
        ],
        TaskType.RESEARCH: [
            # 中文
            r"研究\s*([^\s]+)",
            r"调研\s*([^\s]+)",
            r"分析\s*([^\s]+)",
            r"调查\s*([^\s]+)",
            r"了解\s*([^\s]+)",
            r"产品研究",
            r"竞品分析",
            r"用户研究",
            r"市场调研",
            r"市场分析",
            r"技术调研",
            r"需求分析",
            # 英文
            r"research\s+",
            r"investigate\s+",
            r"analyze\s+",
            r"survey\s+",
            r"study\s+",
            r"competitor analysis",
            r"market research",
            r"user research",
            r"product research",
        ],
        TaskType.REVIEW: [
            # 中文
            r"审查\s*([^\s]+)",
            r"审核\s*([^\s]+)",
            r"检查\s*([^\s]+)",
            r"代码审查",
            r"代码检查",
            r"质量审查",
            # 英文
            r"review\s+",
            r"audit\s+",
            r"check\s+",
            r"code review",
            r"quality review",
        ],
        TaskType.PLANNING: [
            # 中文
            r"规划\s*([^\s]+)",
            r"计划\s*([^\s]+)",
            r"设计\s*([^\s]+)",
            r"架构\s*([^\s]+)",
            r"制定计划",
            r"项目规划",
            # 英文
            r"plan\s+",
            r"design\s+",
            r"architect\s+",
            r"architecture\s+",
            r"plan the",
        ],
        TaskType.ANALYSIS: [
            # 中文
            r"数据分析",
            r"性能分析",
            r"需求分析",
            r"日志分析",
            # 英文
            r"data analysis",
            r"performance analysis",
            r"log analysis",
        ],
    }

    # 技术栈关键词
    TECH_STACK = [
        'Python', 'JavaScript', 'TypeScript', 'React', 'Vue', 'Vue.js',
        'FastAPI', 'Django', 'Flask', 'Node.js', 'Express',
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis',
        'Docker', 'Kubernetes', 'AWS', 'GCP', 'Azure',
        'REST', 'RESTful', 'GraphQL', 'WebSocket',
        'HTML', 'CSS', 'Tailwind', 'Bootstrap',
        'Pandas', 'NumPy', 'Matplotlib',
    ]

    # 否定模式 (用于降低置信度)
    NEGATION_PATTERNS = [
        r"不需要",
        r"不要",
        r"不想要",
        r"不是要",
        r"不是要",
    ]

    def __init__(self):
        pass

    def parse(self, text: str) -> ParsedRequest:
        """解析自然语言输入

        Args:
            text: 用户输入的自然语言

        Returns:
            ParsedRequest: 解析后的结构化请求
        """
        # 1. 预处理
        text = self._preprocess(text)

        # 2. 检测任务类型
        task_type, confidence = self._detect_task_type(text)

        # 3. 提取实体
        entities = self._extract_entities(text)

        # 4. 清理描述
        description = self._clean_description(text, task_type)

        return ParsedRequest(
            task_type=task_type,
            description=description,
            entities=entities,
            confidence=confidence
        )

    def _preprocess(self, text: str) -> str:
        """预处理文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除首尾空白
        text = text.strip()
        return text

    def _detect_task_type(self, text: str) -> Tuple[TaskType, float]:
        """检测任务类型

        Returns:
            Tuple[TaskType, float]: 任务类型和置信度
        """
        text_lower = text.lower()

        # 检查否定模式
        for pattern in self.NEGATION_PATTERNS:
            if re.search(pattern, text_lower):
                return TaskType.CODING, 0.3  # 降低默认置信度

        best_match = TaskType.CODING  # 默认
        best_confidence = 0.5
        best_match_info = None

        for task_type, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    # 计算置信度
                    match_length = len(match.group(0))
                    text_length = len(text)
                    base_confidence = 0.7
                    length_ratio = match_length / text_length if text_length > 0 else 0

                    # 匹配越长，置信度越高
                    confidence = min(base_confidence + length_ratio * 0.3, 0.95)

                    # 如果有额外捕获组，提高置信度
                    if len(match.groups()) > 0 and match.group(1):
                        confidence = min(confidence + 0.1, 0.95)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = task_type
                        best_match_info = match.group(0) if match else None

        return best_match, best_confidence

    def _extract_entities(self, text: str) -> List[str]:
        """提取关键实体

        Args:
            text: 输入文本

        Returns:
            List[str]: 提取的实体列表
        """
        entities = []

        # 1. 提取代码标识符 (变量名、函数名、类名)
        identifiers = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', text)
        entities.extend(identifiers)

        # 2. 提取技术栈
        for tech in self.TECH_STACK:
            if tech.lower() in text.lower():
                entities.append(tech)

        # 3. 提取文件路径
        file_paths = re.findall(r'[\w/]+\.[a-zA-Z]+', text)
        entities.extend(file_paths)

        # 去重并返回
        return list(set(entities))

    def _clean_description(self, text: str, task_type: TaskType) -> str:
        """清理描述

        移除任务类型相关的动词前缀，保留核心功能描述。

        Args:
            text: 输入文本
            task_type: 检测到的任务类型

        Returns:
            str: 清理后的描述
        """
        result = text

        # 只移除动词前缀，保留捕获的实体 (中英双语)
        verb_prefixes = [
            # 中文
            r"创建\s*", r"实现\s*", r"开发\s*", r"编写\s*", r"写\s*",
            r"添加\s*", r"修改\s*", r"更新\s*", r"重构\s*", r"优化\s*",
            r"修复\s*", r"新增\s*",
            r"研究\s*", r"调研\s*", r"分析\s*", r"调查\s*", r"了解\s*",
            r"审查\s*", r"审核\s*", r"检查\s*",
            r"规划\s*", r"计划\s*", r"设计\s*", r"架构\s*",
            # 英文
            r"create\s+", r"implement\s+", r"develop\s+", r"build\s+", r"write\s+",
            r"add\s+", r"modify\s+", r"update\s+", r"refactor\s+", r"optimize\s+",
            r"fix\s+",
            r"research\s+", r"investigate\s+", r"analyze\s+", r"survey\s+", r"study\s+",
            r"review\s+", r"audit\s+", r"check\s+",
            r"plan\s+", r"design\s+", r"architect\s+",
        ]

        for prefix in verb_prefixes:
            result = re.sub(prefix, '', result, flags=re.IGNORECASE)

        # 移除一些常见的无关词汇 (中英双语)
        result = re.sub(r"我需要\s*", '', result, flags=re.IGNORECASE)
        result = re.sub(r"帮我\s*", '', result, flags=re.IGNORECASE)
        result = re.sub(r"help me\s*", '', result, flags=re.IGNORECASE)
        result = re.sub(r"I need to\s*", '', result, flags=re.IGNORECASE)
        result = re.sub(r"I want to\s*", '', result, flags=re.IGNORECASE)

        # 移除多余空白
        result = re.sub(r'\s+', ' ', result).strip()

        # 如果结果为空，使用原始文本
        if not result:
            result = text

        return result

    def parse_with_alternatives(self, text: str) -> List[Tuple[TaskType, float]]:
        """解析并返回所有可能的类型及其置信度

        Args:
            text: 用户输入的自然语言

        Returns:
            List[Tuple[TaskType, float]]: 按置信度排序的类型列表
        """
        text_lower = text.lower()
        alternatives = []

        for task_type, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    match_length = len(match.group(0))
                    text_length = len(text)
                    confidence = min(0.7 + (match_length / text_length) * 0.3, 0.95)
                    alternatives.append((task_type, confidence))

        # 按置信度排序
        alternatives.sort(key=lambda x: x[1], reverse=True)

        # 如果没有匹配，返回默认
        if not alternatives:
            return [(TaskType.CODING, 0.5)]

        return alternatives


# ============ 测试代码 ============

if __name__ == "__main__":
    parser = NaturalLanguageParser()

    test_cases = [
        "创建一个用户登录模块",
        "我需要做竞品分析，研究竞争对手的产品功能",
        "帮我审查这段代码的质量",
        "规划一下项目架构",
        "分析一下性能瓶颈",
        "实现用户认证功能",
        "修复登录bug",
        "优化数据库查询性能",
    ]

    for text in test_cases:
        result = parser.parse(text)
        print(f"\n输入: {text}")
        print(f"  类型: {result.task_type.value} (置信度: {result.confidence:.2f})")
        print(f"  描述: {result.description}")
        print(f"  实体: {result.entities}")
