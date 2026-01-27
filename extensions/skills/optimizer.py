"""技能索引优化器 (SkillIndexOptimizer)

性能优化模块 - 提升大规模技能库的检索效率。
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from pathlib import Path
import logging
import pickle
from datetime import datetime, timedelta

from .models import SkillCard

logger = logging.getLogger(__name__)


class SkillIndexOptimizer:
    """技能索引优化器

    职责:
    - 缓存热门技能
    - 增量索引更新
    - 批量查询优化
    """

    def __init__(self, skills_dir: Path, cache_ttl: int = 3600):
        """初始化优化器

        Args:
            skills_dir: 技能目录
            cache_ttl: 缓存生存时间(秒)，默认1小时
        """
        self.skills_dir = Path(skills_dir)
        self.cache_ttl = cache_ttl

        # 缓存路径
        self.top_skills_cache_file = self.skills_dir / "top_skills_cache.pkl"
        self.keyword_index_cache_file = self.skills_dir / "keyword_index_cache.pkl"

        # 内存缓存
        self._top_skills_cache: Optional[List[Tuple[str, float]]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._keyword_index: Dict[str, Set[str]] = {}  # keyword -> skill_ids

    def is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self._cache_timestamp is None:
            return False

        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < self.cache_ttl

    async def get_top_skills(
        self,
        skills: Dict[str, SkillCard],
        limit: int = 50,
        force_refresh: bool = False
    ) -> List[SkillCard]:
        """获取热门技能(按使用次数排序)

        Args:
            skills: 技能字典
            limit: 返回数量限制
            force_refresh: 强制刷新缓存

        Returns:
            热门技能列表
        """
        # 检查缓存
        if not force_refresh and self.is_cache_valid() and self._top_skills_cache:
            logger.debug("Using cached top skills")
            top_ids = [sid for sid, _ in self._top_skills_cache[:limit]]
            return [skills[sid] for sid in top_ids if sid in skills]

        # 计算热门技能
        skill_scores = [
            (skill_id, skill.usage_count * skill.scores.average)
            for skill_id, skill in skills.items()
        ]

        # 按分数排序
        skill_scores.sort(key=lambda x: x[1], reverse=True)

        # 更新缓存
        self._top_skills_cache = skill_scores
        self._cache_timestamp = datetime.now()

        # 异步保存缓存
        top_ids = [sid for sid, _ in skill_scores[:limit]]
        return [skills[sid] for sid in top_ids if sid in skills]

    async def build_keyword_index(
        self,
        skills: Dict[str, SkillCard]
    ) -> Dict[str, Set[str]]:
        """构建关键词倒排索引

        Args:
            skills: 技能字典

        Returns:
            关键词 -> 技能ID集合 的映射
        """
        keyword_index: Dict[str, Set[str]] = {}

        for skill_id, skill in skills.items():
            # 从 trigger_keywords 提取
            for keyword in skill.trigger_keywords:
                if keyword not in keyword_index:
                    keyword_index[keyword] = set()
                keyword_index[keyword].add(skill_id)

            # 从 problem_scene 提取
            words = self._extract_words(skill.problem_scenario)
            for word in words:
                if len(word) < 2:  # 跳过单字符
                    continue
                if word not in keyword_index:
                    keyword_index[word] = set()
                keyword_index[word].add(skill_id)

            # 从 solution 提取
            words = self._extract_words(skill.solution)
            for word in words:
                if len(word) < 2:
                    continue
                if word not in keyword_index:
                    keyword_index[word] = set()
                keyword_index[word].add(skill_id)

        self._keyword_index = keyword_index
        logger.info(f"Built keyword index with {len(keyword_index)} keywords")

        return keyword_index

    def _extract_words(self, text: str) -> List[str]:
        """从文本中提取单词"""
        import re
        # 简单分词(按空格、标点符号)
        words = re.findall(r'\b\w+\b', text.lower())
        return words

    async def find_by_keywords_optimized(
        self,
        keywords: List[str],
        limit: int = 10
    ) -> Set[str]:
        """使用关键词索引快速查找

        Args:
            keywords: 关键词列表
            limit: 最多返回多少个技能ID

        Returns:
            技能ID集合
        """
        if not self._keyword_index:
            logger.warning("Keyword index not built, using empty result")
            return set()

        # 收集匹配的技能ID
        matched_skill_ids: Set[str] = set()

        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self._keyword_index:
                matched_skill_ids.update(self._keyword_index[keyword_lower])

        # 按匹配关键词数量排序(可选)
        return matched_skill_ids

    async def save_cache(self) -> None:
        """保存缓存到磁盘"""
        try:
            # 保存热门技能缓存
            if self._top_skills_cache:
                with open(self.top_skills_cache_file, 'wb') as f:
                    pickle.dump({
                        'data': self._top_skills_cache,
                        'timestamp': self._cache_timestamp.isoformat()
                    }, f)

            # 保存关键词索引
            if self._keyword_index:
                # 转换 set 为 list 以便序列化
                serializable_index = {
                    k: list(v) for k, v in self._keyword_index.items()
                }
                with open(self.keyword_index_cache_file, 'wb') as f:
                    pickle.dump(serializable_index, f)

            logger.debug("Skill index cache saved")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    async def load_cache(self) -> bool:
        """从磁盘加载缓存

        Returns:
            是否加载成功
        """
        try:
            # 加载热门技能缓存
            if self.top_skills_cache_file.exists():
                with open(self.top_skills_cache_file, 'rb') as f:
                    data = pickle.load(f)
                    self._top_skills_cache = data['data']
                    self._cache_timestamp = datetime.fromisoformat(data['timestamp'])

            # 加载关键词索引
            if self.keyword_index_cache_file.exists():
                with open(self.keyword_index_cache_file, 'rb') as f:
                    serializable_index = pickle.load(f)
                    # 转换回 set
                    self._keyword_index = {
                        k: set(v) for k, v in serializable_index.items()
                    }

            logger.info("Skill index cache loaded")
            return True
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return False

    async def optimize_skill_search(
        self,
        skills: Dict[str, SkillCard],
        query: str,
        limit: int = 10
    ) -> List[SkillCard]:
        """优化的技能搜索

        综合使用:
        1. 热门技能缓存(如果查询为空)
        2. 关键词索引
        3. 全文搜索(后备)

        Args:
            skills: 技能字典
            query: 查询字符串
            limit: 返回数量限制

        Returns:
            匹配的技能列表
        """
        if not query or query.strip() == "":
            # 返回热门技能
            return await self.get_top_skills(skills, limit)

        # 使用关键词索引
        keywords = query.lower().split()
        matched_ids = await self.find_by_keywords_optimized(keywords, limit * 2)

        if matched_ids:
            # 按相关性排序(简单实现:按匹配关键词数量)
            results = []
            for skill_id in matched_ids:
                if skill_id in skills:
                    results.append(skills[skill_id])
                    if len(results) >= limit:
                        break
            return results

        # 后备:全文搜索
        return self._fallback_search(skills, query, limit)

    def _fallback_search(
        self,
        skills: Dict[str, SkillCard],
        query: str,
        limit: int
    ) -> List[SkillCard]:
        """后备全文搜索"""
        query_lower = query.lower()
        results = []

        for skill in skills.values():
            # 搜索名称、问题场景、解决方案
            if (query_lower in skill.name.lower() or
                query_lower in skill.problem_scenario.lower() or
                query_lower in skill.solution.lower()):
                results.append(skill)
                if len(results) >= limit:
                    break

        return results

    async def get_statistics(
        self,
        skills: Dict[str, SkillCard]
    ) -> Dict[str, Any]:
        """获取技能库统计信息

        Args:
            skills: 技能字典

        Returns:
            统计信息字典
        """
        total_skills = len(skills)

        # 按类别统计
        category_stats: Dict[str, int] = {}
        for skill in skills.values():
            cat = skill.category
            category_stats[cat] = category_stats.get(cat, 0) + 1

        # 按评分统计
        high_quality = sum(1 for s in skills.values() if s.scores.average >= 8.0)
        medium_quality = sum(1 for s in skills.values() if 6.0 <= s.scores.average < 8.0)
        low_quality = sum(1 for s in skills.values() if s.scores.average < 6.0)

        # 使用次数统计
        total_usage = sum(s.usage_count for s in skills.values())
        avg_usage = total_usage / total_skills if total_skills > 0 else 0

        return {
            "total_skills": total_skills,
            "category_distribution": category_stats,
            "quality_distribution": {
                "high": high_quality,
                "medium": medium_quality,
                "low": low_quality
            },
            "usage_stats": {
                "total_usage": total_usage,
                "average_usage": avg_usage
            },
            "index_stats": {
                "keyword_index_size": len(self._keyword_index),
                "cache_valid": self.is_cache_valid(),
                "cache_age_seconds": (datetime.now() - self._cache_timestamp).total_seconds()
                if self._cache_timestamp else 0
            }
        }
