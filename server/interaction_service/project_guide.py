#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
项目引导器

实现大型项目的分阶段对话引导：
- 阶段 1: 需求收集
- 阶段 2: 产品研究
- 阶段 3: 架构设计
- 阶段 4: 代码开发
- 阶段 5: 测试验收
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from server.interaction_service import NaturalLanguageParser, AgentDispatcher
from pathlib import Path


class ProjectPhase(Enum):
    """项目阶段"""
    INIT = "init"                    # 初始阶段
    REQUIREMENT = "requirement"      # 需求收集
    RESEARCH = "research"            # 产品研究
    DESIGN = "design"                # 架构设计
    DEVELOPMENT = "development"      # 代码开发
    TESTING = "testing"              # 测试验收
    COMPLETE = "complete"            # 完成


@dataclass
class PhaseQuestion:
    """阶段问题"""
    question: str
    examples: List[str]
    required: bool = True


# 阶段配置
PHASE_CONFIG = {
    ProjectPhase.INIT: PhaseQuestion(
        question="请描述您想要开发的项目是什么？",
        examples=[
            "我想开发一个电商网站",
            "我需要一个项目管理工具",
            "我要做一个社交媒体应用"
        ]
    ),
    ProjectPhase.REQUIREMENT: PhaseQuestion(
        question="这个项目需要哪些核心功能？请尽量详细描述。",
        examples=[
            "用户注册登录、商品展示、购物车、订单管理",
            "任务创建、分配、跟踪、团队协作"
        ]
    ),
    ProjectPhase.RESEARCH: PhaseQuestion(
        question="是否需要我先进行竞品分析和用户研究？",
        examples=["是，需要研究竞品", "不需要，直接开始开发"]
    ),
    ProjectPhase.DESIGN: PhaseQuestion(
        question="对技术架构有什么要求吗？",
        examples=[
            "使用 React + Node.js + PostgreSQL",
            "全用 Python 技术栈",
            "没有特殊要求，你来决定"
        ]
    ),
    ProjectPhase.DEVELOPMENT: PhaseQuestion(
        question="准备好开始开发了吗？",
        examples=["准备好了", "我还想再考虑一下"]
    ),
    ProjectPhase.TESTING: PhaseQuestion(
        question="开发完成后需要我自动运行测试吗？",
        examples=["需要", "不需要"]
    ),
}


class ProjectGuide:
    """项目引导器

    引导用户完成大型项目的全流程。
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.parser = NaturalLanguageParser()
        self.dispatcher = AgentDispatcher(project_root=project_root or Path("."))
        self.current_phase = ProjectPhase.INIT
        self.project_info: Dict[str, Any] = {}
        self.is_research_done = False

    def get_welcome_message(self) -> str:
        """获取欢迎消息"""
        return """
## 🎯 欢迎使用 SuperAgent 项目引导器！

我可以帮您从需求到代码落地全程完成项目开发。

**项目流程**：
1. 📝 需求收集 - 了解您的项目需求
2. 🔍 产品研究 - 竞品分析和用户调研
3. 🎨 架构设计 - 技术选型和系统设计
4. 💻 代码开发 - 生成完整代码
5. ✅ 测试验收 - 自动化测试

---

**请先告诉我，您想要开发什么项目？**
        """

    def get_current_question(self) -> str:
        """获取当前阶段的问题"""
        phase_info = PHASE_CONFIG.get(self.current_phase)
        if not phase_info:
            return "项目已完成所有阶段！"

        question = f"\n**【{self._get_phase_name()}】**\n\n{phase_info.question}\n\n"

        if phase_info.examples:
            question += "示例：\n"
            for ex in phase_info.examples[:3]:
                question += f"- {ex}\n"

        return question

    def _get_phase_name(self) -> str:
        """获取阶段名称"""
        names = {
            ProjectPhase.INIT: "项目初始化",
            ProjectPhase.REQUIREMENT: "需求收集",
            ProjectPhase.RESEARCH: "产品研究",
            ProjectPhase.DESIGN: "架构设计",
            ProjectPhase.DEVELOPMENT: "代码开发",
            ProjectPhase.TESTING: "测试验收",
            ProjectPhase.COMPLETE: "完成",
        }
        return names.get(self.current_phase, "未知阶段")

    def handle_input(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入，返回响应和下一步动作"""
        result = {
            "message": "",
            "action": None,  # "continue", "research", "develop", "test", "complete"
            "phase": self.current_phase.value,
            "project_info": self.project_info,
        }

        # 解析用户意图
        parsed = self.parser.parse(user_input)

        # 根据当前阶段处理
        if self.current_phase == ProjectPhase.INIT:
            self.project_info["description"] = parsed.description
            result["message"] = f"好的，我来帮您开发：**{parsed.description}**\n\n"
            self._advance_phase()
            result["message"] += self.get_current_question()

        elif self.current_phase == ProjectPhase.REQUIREMENT:
            self.project_info["requirements"] = parsed.description
            self.project_info["entities"] = parsed.entities
            result["message"] = f"已记录需求：**{parsed.description}**\n\n"

            # 检查是否需要研究
            if "研究" in user_input or "analysis" in user_input.lower():
                result["action"] = "research"
                result["message"] += "好的，我将先进行产品研究..."
            else:
                self._advance_phase()
                result["message"] += self.get_current_question()

        elif self.current_phase == ProjectPhase.RESEARCH:
            if self.is_research_done:
                result["message"] = "研究已完成！\n\n"
            else:
                # 执行产品研究
                result["action"] = "research"
                result["message"] = "正在执行产品研究...\n"
                self.is_research_done = True

            self._advance_phase()
            result["message"] += self.get_current_question()

        elif self.current_phase == ProjectPhase.DESIGN:
            self.project_info["design"] = parsed.description
            result["message"] = f"已记录设计要求：**{parsed.description}**\n\n"
            self._advance_phase()
            result["message"] += self.get_current_question()

        elif self.current_phase == ProjectPhase.DEVELOPMENT:
            result["action"] = "develop"
            result["message"] = "开始代码开发...\n\n"
            self._advance_phase()
            result["message"] += self.get_current_question()

        elif self.current_phase == ProjectPhase.TESTING:
            self.project_info["testing"] = parsed.description
            result["action"] = "test"
            result["message"] = "执行测试...\n"
            self._advance_phase()
            result["message"] += self._get_completion_message()

        elif self.current_phase == ProjectPhase.COMPLETE:
            result["action"] = "complete"
            result["message"] = self._get_completion_message()

        return result

    def _advance_phase(self):
        """推进到下一阶段"""
        phases = list(ProjectPhase)
        current_idx = phases.index(self.current_phase)
        if current_idx < len(phases) - 1:
            self.current_phase = phases[current_idx + 1]

    def _get_completion_message(self) -> str:
        """获取完成消息"""
        return f"""
## 🎉 项目开发完成！

**项目摘要**：
- 描述：{self.project_info.get('description', 'N/A')}
- 需求：{self.project_info.get('requirements', 'N/A')}
- 设计：{self.project_info.get('design', 'N/A')}

---

如需继续开发新功能，请告诉我！"""

    async def execute_research(self) -> Dict[str, Any]:
        """执行产品研究"""
        if not self.project_info.get("description"):
            return {"error": "没有项目描述"}

        return await self.dispatcher.dispatch_async(
            task_type="research",
            description=self.project_info["description"]
        )

    async def execute_development(self) -> Dict[str, Any]:
        """执行代码开发"""
        if not self.project_info.get("requirements"):
            return {"error": "没有需求描述"}

        return await self.dispatcher.dispatch_async(
            task_type="coding",
            description=self.project_info["requirements"]
        )

    async def execute_testing(self) -> Dict[str, Any]:
        """执行测试"""
        from adapters.unified_adapter import UnifiedAdapter
        adapter = UnifiedAdapter(project_root=Path("."))
        return await adapter.run_tests()


# ============ 使用示例 ============

async def demo():
    """演示项目引导器"""
    guide = ProjectGuide()

    print("=" * 60)
    print("  SuperAgent 项目引导器演示")
    print("=" * 60)

    # 1. 欢迎
    print(guide.get_welcome_message())

    # 2. 阶段 1: 项目初始化
    print("\n👤 用户: 我想开发一个在线教育平台")
    result = guide.handle_input("我想开发一个在线教育平台")
    print(f"\n🤖 Agent: {result['message']}")
    print(f"   当前阶段: {result['phase']}")

    # 3. 阶段 2: 需求收集
    print("\n👤 用户: 需要用户注册登录、课程管理、视频播放、支付功能")
    result = guide.handle_input("需要用户注册登录、课程管理、视频播放、支付功能")
    print(f"\n🤖 Agent: {result['message']}")
    print(f"   当前阶段: {result['phase']}")
    print(f"   下一步动作: {result['action']}")

    # 4. 跳过研究，直接进入设计
    print("\n👤 用户: 不需要研究，直接开始")
    result = guide.handle_input("不需要研究，直接开始")
    print(f"\n🤖 Agent: {result['message']}")
    print(f"   当前阶段: {result['phase']}")

    # 5. 架构设计
    print("\n👤 用户: 使用 React 前端，Node.js 后端，MongoDB 数据库")
    result = guide.handle_input("使用 React 前端，Node.js 后端，MongoDB 数据库")
    print(f"\n🤖 Agent: {result['message']}")
    print(f"   当前阶段: {result['phase']}")

    # 6. 开始开发
    print("\n👤 用户: 准备好了，开始开发")
    result = guide.handle_input("准备好了，开始开发")
    print(f"\n🤖 Agent: {result['message']}")
    print(f"   下一步动作: {result['action']}")

    print("\n" + "=" * 60)
    print("  演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
