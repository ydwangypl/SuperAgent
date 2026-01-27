"""记忆自动晋升器 (EpisodicToProceduralPromoter)

Gemini 建议 #4 - 从情节记忆中自动提取程序性技能。
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import re
from datetime import datetime
from collections import Counter

from .models import SkillCard, SkillCategory, SkillType, SkillQualityScores
from .extractor import SkillExtractor
from .manager import SkillManager

logger = logging.getLogger(__name__)


class EpisodicToProceduralPromoter:
    """情节记忆到程序性技能的自动晋升器

    职责：
    - 从情节记忆中识别重复模式
    - 自动提取程序性技能
    - 晋升为技能卡
    """

    def __init__(
        self,
        skill_manager: SkillManager,
        skill_extractor: SkillExtractor,
        min_occurrences: int = 3
    ):
        """初始化晋升器

        Args:
            skill_manager: 技能管理器
            skill_extractor: 技能提取器
            min_occurrences: 最少出现次数才晋升
        """
        self.skill_manager = skill_manager
        self.skill_extractor = skill_extractor
        self.min_occurrences = min_occurrences

    async def promote_from_memories(
        self,
        episodic_memories: List[Dict[str, Any]]
    ) -> List[SkillCard]:
        """从情节记忆中晋升技能

        Args:
            episodic_memories: 情节记忆列表
                每个记忆包含:
                - content: 记忆内容
                - metadata: 元数据 (task_type, success, error, etc.)
                - timestamp: 时间戳

        Returns:
            晋升的技能卡列表
        """
        # 1. 识别重复模式
        patterns = self._identify_repeating_patterns(episodic_memories)

        if not patterns:
            logger.info("No repeating patterns found in memories")
            return []

        # 2. 对每个模式尝试晋升为技能
        promoted_skills = []

        for pattern_name, pattern_data in patterns.items():
            if pattern_data["count"] < self.min_occurrences:
                logger.debug(
                    f"Pattern '{pattern_name}' occurs only "
                    f"{pattern_data['count']} times (< {self.min_occurrences})"
                )
                continue

            # 检查是否已存在相似技能
            existing = await self._find_similar_skill(pattern_name)
            if existing:
                logger.debug(
                    f"Similar skill already exists: {existing.skill_id}"
                )
                # 更新使用次数
                existing.usage_count += pattern_data["count"]
                continue

            # 尝试提取技能
            skill = await self._promote_pattern_to_skill(
                pattern_name,
                pattern_data
            )

            if skill:
                promoted_skills.append(skill)
                logger.info(
                    f"Promoted pattern '{pattern_name}' to skill: {skill.skill_id}"
                )

        return promoted_skills

    def _identify_repeating_patterns(
        self,
        memories: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """识别重复模式

        Args:
            memories: 情节记忆列表

        Returns:
            模式字典:
            {
                "pattern_name": {
                    "count": int,
                    "examples": List[Dict],
                    "contexts": List[Dict]
                }
            }
        """
        patterns = {}

        for memory in memories:
            # 提取模式签名
            pattern_name = self._extract_pattern_signature(memory)

            if not pattern_name:
                continue

            if pattern_name not in patterns:
                patterns[pattern_name] = {
                    "count": 0,
                    "examples": [],
                    "contexts": []
                }

            patterns[pattern_name]["count"] += 1
            patterns[pattern_name]["examples"].append(memory.get("content", ""))
            patterns[pattern_name]["contexts"].append(memory.get("metadata", {}))

        return patterns

    def _extract_pattern_signature(self, memory: Dict[str, Any]) -> Optional[str]:
        """提取模式签名

        Args:
            memory: 单个记忆

        Returns:
            模式签名 (None if not a repeating pattern)
        """
        content = memory.get("content", "")
        metadata = memory.get("metadata", {})

        # 策略1: 基于错误类型
        error = metadata.get("error")
        if error:
            # 提取错误类型
            error_match = re.search(r'(\w+Error)', error)
            if error_match:
                return f"error_{error_match.group(1)}"

        # 策略2: 基于任务类型 + 关键词
        task_type = metadata.get("task_type", "")
        if task_type in ["coding", "implementation"]:
            # 提取常见编程模式
            patterns = [
                (r"import\s+\w+", "import_pattern"),
                (r"def\s+\w+\(", "function_definition"),
                (r"class\s+\w+", "class_definition"),
                (r"async\s+def", "async_function"),
                (r"@\w+", "decorator_usage"),
                (r"with\s+\w+\s+as", "context_manager"),
            ]

            content_lower = content.lower()
            for pattern, signature in patterns:
                if re.search(pattern, content):
                    return signature

        # 策略3: 基于解决方案关键词
        success_keywords = ["解决", "修复", "fix", "resolve", "solved"]
        if any(kw in content.lower() for kw in success_keywords):
            # 提取问题类型
            problem_match = re.search(r'(\w+)\s*(问题|错误|error|issue)', content)
            if problem_match:
                return f"solution_{problem_match.group(1)}"

        return None

    async def _promote_pattern_to_skill(
        self,
        pattern_name: str,
        pattern_data: Dict[str, Any]
    ) -> Optional[SkillCard]:
        """将模式晋升为技能

        Args:
            pattern_name: 模式名称
            pattern_data: 模式数据

        Returns:
            技能卡 (None if extraction fails)
        """
        # 构建虚拟任务用于提取
        examples = pattern_data["examples"][:3]  # 取前3个例子

        # 合并示例内容
        combined_content = "\n\n".join(examples)

        # 构建虚拟任务和结果
        virtual_task = {
            "type": "pattern_promotion",
            "description": f"自动晋升模式: {pattern_name}",
            "pattern_name": pattern_name
        }

        virtual_result = {
            "success": True,
            "output": combined_content,
            "examples_count": len(examples)
        }

        virtual_context = {
            "promotion": True,
            "pattern_count": pattern_data["count"],
            "source": "episodic_memory"
        }

        # 使用 SkillExtractor 评估
        gate_result = await self.skill_extractor.evaluate(
            task=virtual_task,
            result=virtual_result,
            context=virtual_context
        )

        if not gate_result.passed:
            logger.debug(
                f"Pattern '{pattern_name}' did not pass quality gate: "
                f"{gate_result.reason}"
            )
            return None

        # 创建技能卡
        skill_id = self.skill_extractor.generate_skill_id(virtual_task)

        # 提取问题场景（从第一个例子）
        problem_scenario = self._extract_problem_scenario(pattern_data)

        # 提取解决方案（综合所有例子）
        solution = self._extract_solution(pattern_data)

        # 提取代码示例（如果有）
        code_example = self._extract_code_example(pattern_data)

        skill = SkillCard(
            skill_id=skill_id,
            name=f"自动晋升: {pattern_name.replace('_', ' ').title()}",
            category=gate_result.category,
            skill_type=gate_result.skill_type,
            scores=gate_result.scores,
            problem_scenario=problem_scenario,
            solution=solution,
            code_example=code_example,
            source_task_id="auto_promotion",
            source_agent="EpisodicToProceduralPromoter",
            usage_count=pattern_data["count"]  # 初始使用次数 = 出现次数
        )

        return skill

    def _extract_problem_scenario(
        self,
        pattern_data: Dict[str, Any]
    ) -> str:
        """提取问题场景"""
        # 从第一个例子中提取问题
        first_example = pattern_data["examples"][0]

        # 尝试提取错误信息
        error_match = re.search(r'(\w+Error:[^。\n]+)', first_example)
        if error_match:
            return error_match.group(1)

        # 否则返回前100字符
        return first_example[:100] + "..."

    def _extract_solution(
        self,
        pattern_data: Dict[str, Any]
    ) -> str:
        """提取解决方案"""
        examples = pattern_data["examples"]

        # 提取所有解决方案关键词后的内容
        solutions = []
        for example in examples:
            # 匹配 "解决:" "fix:" "方案:" 等后的内容
            matches = re.findall(
                r'(?:解决|修复|fix|resolve|方案)[：:]\s*([^\n]+)',
                example,
                re.IGNORECASE
            )
            solutions.extend(matches)

        if solutions:
            # 统计最常见的解决方案
            counter = Counter(solutions)
            most_common = counter.most_common(1)[0][0]
            return most_common

        # 否则返回第一个例子的相关部分
        return examples[0][:150] + "..."

    def _extract_code_example(
        self,
        pattern_data: Dict[str, Any]
    ) -> str:
        """提取代码示例"""
        examples = pattern_data["examples"]

        for example in examples:
            # 提取代码块
            code_match = re.search(r'```(\w+)?\n(.*?)```', example, re.DOTALL)
            if code_match:
                code = code_match.group(2).strip()
                # 限制长度
                if len(code) < 500:
                    return code

        # 提取单行代码
        for example in examples:
            # 匹配 def, class, import 等开头的行
            lines = example.split('\n')
            for line in lines:
                line = line.strip()
                if any(line.startswith(kw) for kw in ['def ', 'class ', 'import ', 'from ']):
                    return line

        return ""

    async def _find_similar_skill(
        self,
        pattern_name: str
    ) -> Optional[SkillCard]:
        """查找相似的已存在技能

        Args:
            pattern_name: 模式名称

        Returns:
            相似技能 (None if not found)
        """
        # 尝试按关键词查找
        keywords = pattern_name.replace('_', ' ').split()

        for keyword in keywords:
            skills = await self.skill_manager.find_by_keyword(keyword)
            if skills:
                # 返回评分最高的
                return max(skills, key=lambda s: s.scores.average)

        return None

    async def auto_promote_from_memory_manager(
        self,
        memory_manager
    ) -> List[SkillCard]:
        """从 MemoryManager 自动晋升

        这是便捷方法，直接从 MemoryManager 获取情节记忆。

        Args:
            memory_manager: MemoryManager 实例

        Returns:
            晋升的技能卡列表
        """
        # 获取所有情节记忆
        episodic_memories = await memory_manager.get_episodic_memories()

        if not episodic_memories:
            logger.info("No episodic memories found")
            return []

        # 转换为标准格式
        formatted_memories = []
        for memory in episodic_memories:
            formatted_memories.append({
                "content": memory.get("content", ""),
                "metadata": memory.get("metadata", {}),
                "timestamp": memory.get("timestamp", datetime.now().isoformat())
            })

        # 晋升
        return await self.promote_from_memories(formatted_memories)
