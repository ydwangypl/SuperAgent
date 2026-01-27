"""技能数据模型

定义 SkillCard 和相关数据结构。
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class SkillCategory(Enum):
    """技能分类"""
    ERROR_RESOLUTION = "error_resolution"      # 错误解决方案
    PATTERN = "pattern"                        # 设计模式
    WORKAROUND = "workaround"                  # 变通方案
    BEST_PRACTICE = "best_practice"            # 最佳实践
    CONFIGURATION = "configuration"            # 配置技巧
    PERFORMANCE = "performance"                # 性能优化


class SkillType(Enum):
    """技能类型"""
    PATTERN = "pattern"                        # 模式
    SOLUTION = "solution"                      # 解决方案
    WORKAROUND = "workaround"                  # 变通方案


@dataclass
class SkillQualityScores:
    """技能质量评分"""
    reusability: int = 5       # 1-10 可复用性
    generality: int = 5        # 1-10 通用性
    clarity: int = 5           # 1-10 清晰度
    uniqueness: int = 5        # 1-10 独特性

    @property
    def average(self) -> float:
        return (self.reusability + self.generality +
                self.clarity + self.uniqueness) / 4


@dataclass
class SkillCard:
    """技能卡 - 结构化的可复用知识单元

    遵循 Claudeception YAML Frontmatter + Markdown 格式规范。
    """

    # ========== 核心标识 ==========
    skill_id: str                      # 唯一标识: skill_<timestamp>_<hash>
    name: str                          # 技能名称
    category: str                      # 分类 (SkillCategory.value)
    skill_type: str                    # 类型 (SkillType.value)

    # ========== 质量评分 ==========
    scores: SkillQualityScores         # 质量评分

    # ========== 检索优化 ==========
    error_pattern: Optional[str] = None        # 错误模式正则
    error_tags: List[str] = field(default_factory=list)   # 错误标签
    trigger_keywords: List[str] = field(default_factory=list)  # 触发关键词

    # ========== 内容描述 ==========
    problem_scenario: str = ""         # 问题场景描述
    solution: str = ""                 # 解决方案描述
    implementation_steps: List[str] = field(default_factory=list)  # 实施步骤
    code_example: str = ""             # 代码示例
    alternatives: List[str] = field(default_factory=list)  # 替代方案

    # ========== 元数据 ==========
    source_task_id: Optional[str] = None
    source_agent: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = 0
    last_used_at: Optional[str] = None
    version: str = "1.0"

    def to_markdown(self) -> str:
        """转换为 YAML Frontmatter + Markdown 格式"""
        frontmatter = f"""---
skill_id: {self.skill_id}
name: {self.name}
category: {self.category}
skill_type: {self.skill_type}

# Quality Scores
reusability: {self.scores.reusability}
generality: {self.scores.generality}
clarity: {self.scores.clarity}
uniqueness: {self.scores.uniqueness}
avg_score: {self.scores.average:.1f}

# Retrieval Optimization
error_pattern: {self.error_pattern or 'N/A'}
error_tags: {', '.join(self.error_tags)}
trigger_keywords: {', '.join(self.trigger_keywords)}

# Metadata
source_task: {self.source_task_id or 'N/A'}
source_agent: {self.source_agent or 'N/A'}
created_at: {self.created_at}
usage_count: {self.usage_count}
version: {self.version}
---

# {self.name}

## 问题场景
{self.problem_scenario}

## 解决方案
{self.solution}

## 实施步骤
"""
        for i, step in enumerate(self.implementation_steps, 1):
            frontmatter += f"{i}. {step}\n"

        frontmatter += f"""
## 代码示例
```{self.source_agent or 'python'}
{self.code_example}
```

## 替代方案
"""
        for alt in self.alternatives:
            frontmatter += f"- {alt}\n"

        return frontmatter

    def matches_error(self, error_message: str) -> bool:
        """检查是否匹配错误信息"""
        if not self.error_pattern:
            return False
        import re
        return bool(re.search(self.error_pattern, error_message, re.IGNORECASE))
