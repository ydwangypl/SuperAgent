"""技能管理器 (SkillManager)

管理技能卡的存储、索引和检索。
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .models import SkillCard, SkillCategory
from .optimizer import SkillIndexOptimizer

logger = logging.getLogger(__name__)


class SkillManager:
    """技能管理器

    职责：
    - 技能卡的持久化存储
    - 双重索引 (general + error_pattern)
    - 技能检索和建议生成
    - 性能优化
    """

    def __init__(self, project_root: Path, enable_optimization: bool = True):
        """初始化技能管理器

        Args:
            project_root: 项目根目录
            enable_optimization: 是否启用性能优化
        """
        self.project_root = Path(project_root)
        self.skills_dir = self.project_root / ".superagent" / "skills"
        self.index_file = self.skills_dir / "skills_index.json"
        self.error_index_file = self.skills_dir / "error_patterns.json"

        self._skills: Dict[str, SkillCard] = {}
        self._error_index: Dict[str, List[str]] = {}  # error_pattern -> skill_ids

        # 性能优化器
        self.enable_optimization = enable_optimization
        self.optimizer = SkillIndexOptimizer(self.skills_dir) if enable_optimization else None

    async def initialize(self) -> None:
        """初始化 (加载现有技能)"""
        self.skills_dir.mkdir(parents=True, exist_ok=True)

        # 加载全局索引
        if self.index_file.exists():
            await self._load_index()

        # 加载错误模式索引
        if self.error_index_file.exists():
            await self._load_error_index()

        # 加载优化缓存
        if self.optimizer:
            await self.optimizer.load_cache()
            # 构建关键词索引
            await self.optimizer.build_keyword_index(self._skills)

        logger.info(f"SkillManager initialized with {len(self._skills)} skills")

    async def _load_index(self) -> None:
        """加载全局索引"""
        try:
            data = json.loads(self.index_file.read_text(encoding='utf-8'))
            for skill_data in data.get("skills", []):
                skill = SkillCard(**skill_data)
                self._skills[skill.skill_id] = skill
        except Exception as e:
            logger.error(f"Failed to load skill index: {e}")

    async def _load_error_index(self) -> None:
        """加载错误模式索引"""
        try:
            self._error_index = json.loads(self.error_index_file.read_text(encoding='utf-8'))
        except Exception as e:
            logger.error(f"Failed to load error index: {e}")

    async def save_skill(self, skill: SkillCard) -> bool:
        """保存技能卡

        Args:
            skill: 技能卡实例

        Returns:
            是否保存成功
        """
        try:
            # 1. 保存技能文件
            skill_file = self.skills_dir / f"{skill.skill_id}.md"
            skill_file.write_text(skill.to_markdown(), encoding='utf-8')

            # 2. 更新内存索引
            self._skills[skill.skill_id] = skill

            # 3. 更新错误模式索引
            if skill.error_pattern:
                if skill.error_pattern not in self._error_index:
                    self._error_index[skill.error_pattern] = []
                if skill.skill_id not in self._error_index[skill.error_pattern]:
                    self._error_index[skill.error_pattern].append(skill.skill_id)

            # 4. 持久化索引
            await self._save_indexes()

            logger.info(f"Skill saved: {skill.skill_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save skill {skill.skill_id}: {e}")
            return False

    async def _save_indexes(self) -> None:
        """保存索引文件"""
        # 保存全局索引
        index_data = {
            "updated_at": datetime.now().isoformat(),
            "count": len(self._skills),
            "skills": [
                {
                    "skill_id": s.skill_id,
                    "name": s.name,
                    "category": s.category,
                    "scores": {
                        "reusability": s.scores.reusability,
                        "generality": s.scores.generality,
                        "clarity": s.scores.clarity,
                        "uniqueness": s.scores.uniqueness,
                        "average": s.scores.average
                    },
                    "trigger_keywords": s.trigger_keywords,
                    "created_at": s.created_at
                }
                for s in self._skills.values()
            ]
        }
        self.index_file.write_text(
            json.dumps(index_data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        # 保存错误模式索引
        self.error_index_file.write_text(
            json.dumps(self._error_index, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    async def find_by_error(self, error_message: str) -> List[SkillCard]:
        """根据错误信息查找相关技能

        Args:
            error_message: 错误信息

        Returns:
            匹配的技能卡列表
        """
        import re
        matched_skills = []

        for pattern, skill_ids in self._error_index.items():
            try:
                if re.search(pattern, error_message, re.IGNORECASE):
                    for skill_id in skill_ids:
                        if skill_id in self._skills:
                            matched_skills.append(self._skills[skill_id])
            except re.error:
                continue

        return matched_skills

    async def find_by_keyword(self, keyword: str) -> List[SkillCard]:
        """根据关键词查找技能 (使用优化索引)

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的技能卡列表
        """
        # 如果启用优化且有索引，使用快速查找
        if self.optimizer and self.optimizer._keyword_index:
            skill_ids = await self.optimizer.find_by_keywords_optimized([keyword])
            return [self._skills[sid] for sid in skill_ids if sid in self._skills]

        # 后备: 原有逻辑
        keyword_lower = keyword.lower()
        matched = []

        for skill in self._skills.values():
            # 检查多个字段
            search_fields = [
                skill.name,
                skill.category,
                skill.problem_scenario,
                skill.solution,
                " ".join(skill.trigger_keywords),
                " ".join(skill.error_tags)
            ]

            if any(keyword_lower in field.lower() for field in search_fields):
                matched.append(skill)

        return matched

    async def get_suggestions(self, context: Dict[str, Any]) -> List[str]:
        """根据上下文生成技能建议

        Args:
            context: 当前上下文

        Returns:
            建议列表
        """
        suggestions = []

        # 检查是否有相关错误技能
        if "error" in context:
            error_skills = await self.find_by_error(str(context["error"]))
            for skill in error_skills[:3]:  # 最多3个
                suggestions.append(
                    f"[技能] {skill.name}: {skill.problem_scenario[:100]}..."
                )

        # 检查关键词匹配
        if "description" in context:
            keyword_skills = await self.find_by_keyword(context["description"])
            for skill in keyword_skills[:2]:  # 最多2个
                suggestions.append(
                    f"[相关] {skill.name}: {skill.solution[:100]}..."
                )

        return suggestions

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息 (包含性能优化统计)"""
        by_category = {}
        for skill in self._skills.values():
            cat = skill.category
            by_category[cat] = by_category.get(cat, 0) + 1

        avg_score = 0
        if self._skills:
            avg_score = sum(
                s.scores.average for s in self._skills.values()
            ) / len(self._skills)

        stats = {
            "total_skills": len(self._skills),
            "by_category": by_category,
            "average_score": round(avg_score, 2),
            "error_patterns_count": len(self._error_index)
        }

        # 添加性能优化统计 (同步方法)
        if self.optimizer:
            # 获取缓存状态信息(不需要await)
            cache_valid = self.optimizer.is_cache_valid()
            cache_age = 0
            if self.optimizer._cache_timestamp:
                from datetime import datetime
                cache_age = (datetime.now() - self.optimizer._cache_timestamp).total_seconds()

            stats["optimization"] = {
                "keyword_index_size": len(self.optimizer._keyword_index),
                "cache_valid": cache_valid,
                "cache_age_seconds": cache_age
            }

        return stats

    async def get_top_skills(self, limit: int = 50) -> List[SkillCard]:
        """获取热门技能 (使用优化缓存)

        Args:
            limit: 返回数量限制

        Returns:
            热门技能列表
        """
        if self.optimizer:
            return await self.optimizer.get_top_skills(self._skills, limit)

        # 后备: 手动计算
        scored = list(self._skills.values())
        scored.sort(key=lambda s: s.usage_count * s.scores.average, reverse=True)
        return scored[:limit]

    # 🆕 负反馈机制（占位符，阶段 2 完整实现）

    async def record_skill_feedback(
        self,
        skill_id: str,
        task_success: bool,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """记录技能应用反馈（Gemini #5）

        阶段 2 完整实现，当前占位符
        """
        logger.info(f"Feedback recorded: {skill_id} - success={task_success}")
        return True
