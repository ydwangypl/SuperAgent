"""上下文适配器 (SkillContextAdapter)

Gemini 建议 #3 - 实时错误匹配技能注入。
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import re

from .models import SkillCard
from .manager import SkillManager

logger = logging.getLogger(__name__)


class SkillContextAdapter:
    """技能上下文适配器

    职责：
    - 实时匹配错误信息到技能
    - 根据关键词注入技能建议
    - 压缩技能内容以节省 Token
    """

    def __init__(self, skill_manager: SkillManager):
        """初始化适配器

        Args:
            skill_manager: 技能管理器实例
        """
        self.skill_manager = skill_manager

    async def inject_on_error(
        self,
        error_message: str,
        max_skills: int = 3
    ) -> List[str]:
        """错误发生时实时注入相关技能

        Args:
            error_message: 错误信息
            max_skills: 最多返回多少个技能

        Returns:
            技能建议列表（压缩后的字符串）
        """
        # 1. 匹配错误模式
        skills = await self.skill_manager.find_by_error(error_message)

        if not skills:
            logger.debug(f"No skills found for error: {error_message[:50]}...")
            return []

        # 2. 按评分排序
        skills.sort(key=lambda s: s.scores.average, reverse=True)

        # 3. 选取前 N 个
        top_skills = skills[:max_skills]

        # 4. 压缩技能内容
        compressed = []
        for skill in top_skills:
            compressed.append(self._compress_skill(skill))

        logger.info(
            f"Injected {len(compressed)} skills for error: "
            f"{error_message[:30]}..."
        )

        return compressed

    async def inject_by_keyword(
        self,
        description: str,
        max_skills: int = 2
    ) -> List[str]:
        """根据描述关键词注入技能建议

        Args:
            description: 任务描述
            max_skills: 最多返回多少个技能

        Returns:
            技能建议列表
        """
        # 1. 提取关键词
        keywords = self._extract_keywords(description)

        if not keywords:
            return []

        # 2. 查找相关技能
        all_skills = []
        for keyword in keywords:
            skills = await self.skill_manager.find_by_keyword(keyword)
            all_skills.extend(skills)

        if not all_skills:
            return []

        # 3. 去重并排序
        unique_skills = {}
        for skill in all_skills:
            if skill.skill_id not in unique_skills:
                unique_skills[skill.skill_id] = skill

        skills_list = list(unique_skills.values())
        skills_list.sort(key=lambda s: s.scores.average, reverse=True)

        # 4. 选取前 N 个
        top_skills = skills_list[:max_skills]

        # 5. 压缩
        compressed = [
            self._compress_skill(skill)
            for skill in top_skills
        ]

        logger.info(
            f"Injected {len(compressed)} skills for keywords: "
            f"{', '.join(keywords[:3])}"
        )

        return compressed

    async def get_context_injection(
        self,
        context: Dict[str, Any],
        max_skills: int = 3
    ) -> str:
        """获取上下文注入内容

        根据任务上下文自动决定注入策略。

        Args:
            context: 任务上下文
                - description: 任务描述
                - error: 错误信息（可选）
            max_skills: 最多返回多少个技能

        Returns:
            格式化的注入文本
        """
        injections = []

        # 优先处理错误
        error = context.get("error")
        if error:
            error_skills = await self.inject_on_error(error, max_skills)
            if error_skills:
                injections.append("## 相关技能（基于错误匹配）")
                injections.extend(error_skills)

        # 其次处理描述关键词
        description = context.get("description", "")
        if description and len(injections) < max_skills:
            keyword_skills = await self.inject_by_keyword(
                description,
                max_skills - len(injections)
            )
            if keyword_skills:
                injections.append("\n## 相关技能（基于关键词）")
                injections.extend(keyword_skills)

        if not injections:
            return ""

        return "\n\n".join(injections)

    def _compress_skill(self, skill: SkillCard) -> str:
        """压缩技能内容

        保留核心信息，删除冗余细节以节省 Token。

        Args:
            skill: 技能卡

        Returns:
            压缩后的技能文本
        """
        # 简洁格式
        parts = [
            f"### {skill.name}",
            f"**评分**: {skill.scores.average:.1f}/10 "
            f"(重用:{skill.scores.reusability}, 通用:{skill.scores.generality})",
            f"**使用次数**: {skill.usage_count}",
        ]

        # 问题场景（截断）
        if skill.problem_scenario:
            problem = skill.problem_scenario.split("\n")[0][:100]
            parts.append(f"**问题**: {problem}...")

        # 解决方案（截断）
        if skill.solution:
            solution = skill.solution.split("\n")[0][:150]
            parts.append(f"**方案**: {solution}...")

        # 代码示例（如果不太长）
        if skill.code_example and len(skill.code_example) < 200:
            parts.append(f"```{skill.code_example}```")

        return "\n".join(parts)

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词

        Args:
            text: 输入文本

        Returns:
            关键词列表
        """
        # 简单的关键词提取（基于常见的开发术语）
        tech_keywords = [
            "API", "数据库", "认证", "登录", "注册",
            "前端", "后端", "测试", "部署", "Docker",
            "导入", "模块", "依赖", "安装", "配置",
            "数据库", "查询", "模型", "视图", "模板",
            "API", "REST", "GraphQL", "WebSocket",
            "缓存", "Redis", "Memcached",
            "消息队列", "Celery", "RabbitMQ",
            "日志", "监控", "性能",
            "安全", "加密", "权限",
            "ORM", "SQL", "NoSQL",
            "异步", "同步", "并发",
        ]

        # 检查文本中的关键词
        found = []
        text_lower = text.lower()

        for keyword in tech_keywords:
            if keyword.lower() in text_lower:
                found.append(keyword)

        # 如果没找到，尝试提取英文单词
        if not found:
            words = re.findall(r'\b[A-Z][a-z]+\b', text)
            found = words[:3]  # 取前3个

        return found
