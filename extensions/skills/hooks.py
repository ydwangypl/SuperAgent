"""技能提取 Hook

集成到 SuperAgent 生命周期钩子系统。
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from extensions.hooks.hook_types import HookContext, HookResult, BaseHook
from extensions.hooks.lifecycle_hooks import LifecycleHookType

from .extractor import SkillExtractor, QualityGateResult
from .manager import SkillManager
from .models import SkillCard

logger = logging.getLogger(__name__)


class SkillExtractionHook(BaseHook):
    """技能提取 Hook

    在 POST_TASK 阶段触发，评估任务结果并提取技能。
    """

    def __init__(
        self,
        project_root,
        skill_manager: SkillManager,
        enabled: bool = True
    ):
        """初始化技能提取 Hook

        Args:
            project_root: 项目根目录
            skill_manager: 技能管理器实例
            enabled: 是否启用
        """
        super().__init__(
            name="skill-extraction",
            hook_type=LifecycleHookType.POST_TASK,
            priority=50  # 中等优先级
        )
        self.project_root = project_root
        self.skill_manager = skill_manager
        self.extractor = SkillExtractor()
        self.enabled = enabled

    @property
    def description(self) -> str:
        return "从任务执行结果中提取可复用技能"

    async def execute(self, context: HookContext) -> HookResult:
        """执行技能提取

        Args:
            context: 钩子上下文

        Returns:
            HookResult: 钩子执行结果
        """
        if not self.enabled:
            return HookResult(should_continue=True)

        try:
            # 1. 检查是否应该执行
            if not self._should_extract(context):
                return HookResult(should_continue=True)

            # 2. 构建任务信息
            task_info = self._build_task_info(context)

            # 3. 质量门禁评估
            gate_result = await self.extractor.evaluate(
                task=task_info["task"],
                result=task_info["result"],
                context=task_info["context"]
            )

            if not gate_result.passed:
                logger.debug(
                    f"Skill extraction skipped: {gate_result.reason}"
                )
                return HookResult(should_continue=True)

            # 4. 生成技能卡
            skill = await self._create_skill_card(
                task_info, gate_result, context
            )

            # 5. 保存技能
            success = await self.skill_manager.save_skill(skill)

            if success:
                logger.info(f"Skill extracted: {skill.name}")
                return HookResult(
                    should_continue=True,
                    suggestion=f"已提取技能: {skill.name} "
                               f"(评分: {skill.scores.average:.1f})"
                )
            else:
                return HookResult(
                    should_continue=True,
                    suggestion="技能提取失败"
                )

        except Exception as e:
            logger.error(f"Skill extraction hook error: {e}")
            return HookResult(
                should_continue=True,
                suggestion=f"技能提取错误: {str(e)}"
            )

    def _should_extract(self, context: HookContext) -> bool:
        """检查是否应该提取技能"""
        # 只在任务完成或失败时提取
        if not context.current_task:
            return False

        # 跳过某些任务类型
        skip_types = ["clarification", "clarify"]
        task_type = getattr(context.current_task, 'type', '')
        if task_type.lower() in skip_types:
            return False

        return True

    def _build_task_info(
        self,
        context: HookContext
    ) -> Dict[str, Any]:
        """构建任务信息"""
        task = context.current_task

        # 尝试从 context 获取执行结果
        result = context.metadata.get("execution_result", None)
        if result is None:
            # 从 execution_history 获取
            history = context.execution_history or []
            if history:
                result = history[-1].get("result", None)

        return {
            "task": {
                "type": getattr(task, 'type', 'unknown'),
                "description": getattr(task, 'description', ''),
                "id": getattr(task, 'id', None)
            },
            "result": result or {},
            "context": {
                "step": context.phase,
                "metadata": context.metadata
            }
        }

    async def _create_skill_card(
        self,
        task_info: Dict[str, Any],
        gate_result: QualityGateResult,
        context: HookContext
    ) -> SkillCard:
        """创建技能卡"""
        task = task_info["task"]
        result = task_info["result"]

        # 生成技能 ID
        skill_id = self.extractor.generate_skill_id(task)

        # 构建触发关键词
        trigger_keywords = self._extract_trigger_keywords(task, result)

        return SkillCard(
            skill_id=skill_id,
            name=f"{task.get('type', 'Task')} 技能",
            category=gate_result.category or "pattern",
            skill_type=gate_result.skill_type or "solution",
            scores=gate_result.scores,
            error_pattern=None,  # 可从错误信息中提取
            error_tags=self._extract_error_tags(result),
            trigger_keywords=trigger_keywords,
            problem_scenario=self._extract_problem(task, result),
            solution=self._extract_solution(result),
            implementation_steps=self._extract_steps(result),
            code_example=self._extract_code(result),
            alternatives=[],
            source_task_id=task.get("id"),
            source_agent="SuperAgent"
        )

    def _extract_trigger_keywords(
        self,
        task: Dict[str, Any],
        result: Any
    ) -> list:
        """提取触发关键词"""
        keywords = []
        text = f"{task.get('description', '')} {str(result)}"

        # 提取技术关键词
        import re
        tech_pattern = r'\b(python|javascript|typescript|react|fastapi|django|node)\b'
        keywords.extend(re.findall(tech_pattern, text.lower()))

        return list(set(keywords))

    def _extract_error_tags(self, result: Any) -> list:
        """提取错误标签"""
        tags = []
        result_str = str(result).lower()

        if "timeout" in result_str:
            tags.append("timeout")
        if "permission" in result_str:
            tags.append("permission")
        if "import" in result_str:
            tags.append("import")
        if "syntax" in result_str:
            tags.append("syntax")

        return tags

    def _extract_problem(
        self,
        task: Dict[str, Any],
        result: Any
    ) -> str:
        """提取问题场景"""
        return f"任务: {task.get('description', 'Unknown')}"

    def _extract_solution(self, result: Any) -> str:
        """提取解决方案"""
        result_str = str(result)

        # 尝试提取关键解决方案信息
        if len(result_str) > 500:
            return result_str[:500] + "..."
        return result_str

    def _extract_steps(self, result: Any) -> list:
        """提取实施步骤"""
        return ["步骤1: 执行任务", "步骤2: 验证结果"]

    def _extract_code(self, result: Any) -> str:
        """提取代码示例"""
        result_str = str(result)

        # 尝试提取代码块
        import re
        code_blocks = re.findall(r'```[\s\S]*?```', result_str)

        if code_blocks:
            # 返回第一个代码块，去掉 ``` 标记
            code = code_blocks[0]
            return code.replace('```python', '').replace('```', '').strip()

        return ""
