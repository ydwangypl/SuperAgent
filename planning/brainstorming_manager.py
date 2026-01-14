"""
脑暴管理器 - P1 Task 2.1

在代码生成前进行设计探索,通过结构化问答:
1. 收集需求细节
2. 探索多种方案
3. 让用户选择最佳方案
4. 生成设计规格文档
"""

from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BrainstormingPhase(Enum):
    """脑暴阶段"""
    REQUIREMENT_GATHERING = "requirement_gathering"  # 需求收集
    SOLUTION_EXPLORATION = "solution_exploration"    # 方案探索
    ALTERNATIVE_COMPARISON = "alternative_comparison"  # 方案对比
    DECISION_MAKING = "decision_making"              # 决策确认


@dataclass
class DesignOption:
    """设计选项"""
    option_id: str
    title: str
    description: str
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    implementation_complexity: str = "medium"  # "low", "medium", "high"
    estimated_time: str = "1-2 days"
    risk_level: str = "medium"  # "low", "medium", "high"


@dataclass
class DesignSpec:
    """设计规格"""
    requirements: Dict[str, str]
    selected_option: DesignOption
    considered_alternatives: List[DesignOption]
    rationale: str  # 为什么选择这个方案
    architecture_notes: str
    acceptance_criteria: List[str] = field(default_factory=list)
    created_at: str = ""


class BrainstormingManager:
    """脑暴管理器 - 协调设计探索流程"""

    def __init__(self):
        self.current_phase = BrainstormingPhase.REQUIREMENT_GATHERING
        self.conversation_history: List[Dict] = []
        self.design_options: List[DesignOption] = []
        self.current_requirements: Dict[str, str] = {}

    def start_brainstorming(self, user_request: str) -> Dict[str, any]:
        """开始脑暴阶段 - 收集需求

        Args:
            user_request: 用户原始请求

        Returns:
            Dict: 包含澄清问题和引导信息
        """
        self.current_phase = BrainstormingPhase.REQUIREMENT_GATHERING

        # 记录到对话历史
        self.conversation_history.append({
            "phase": self.current_phase.value,
            "user_request": user_request,
            "timestamp": self._get_timestamp()
        })

        questions = self._generate_requirement_questions(user_request)

        logger.info(f"开始脑暴阶段: {self.current_phase.value}")

        return {
            "phase": self.current_phase.value,
            "questions": questions,
            "message": "让我们先澄清需求细节",
            "user_request": user_request
        }

    def explore_solutions(self, requirements: Dict[str, str]) -> List[DesignOption]:
        """基于需求探索多种解决方案

        Args:
            requirements: 需求字典

        Returns:
            List[DesignOption]: 设计选项列表 (至少 3 个)
        """
        self.current_phase = BrainstormingPhase.SOLUTION_EXPLORATION
        self.current_requirements = requirements

        # 记录到对话历史
        self.conversation_history.append({
            "phase": self.current_phase.value,
            "requirements": requirements,
            "timestamp": self._get_timestamp()
        })

        # 生成 3-5 个设计选项
        self.design_options = self._generate_design_options(requirements)

        logger.info(f"生成 {len(self.design_options)} 个设计选项")

        return self.design_options

    def compare_alternatives(self) -> Dict:
        """对比不同方案

        Returns:
            Dict: 对比结果
        """
        self.current_phase = BrainstormingPhase.ALTERNATIVE_COMPARISON

        if not self.design_options:
            raise ValueError("没有设计选项可对比,请先调用 explore_solutions()")

        comparison = {
            "options": self.design_options,
            "comparison_matrix": self._create_comparison_matrix(),
            "recommendation": self._recommend_option()
        }

        # 记录到对话历史
        self.conversation_history.append({
            "phase": self.current_phase.value,
            "comparison": comparison,
            "timestamp": self._get_timestamp()
        })

        logger.info(f"方案对比完成,推荐: {comparison['recommendation']['option_id']}")

        return comparison

    def finalize_design(self, selected_option_id: str) -> DesignSpec:
        """确认设计并生成设计规格

        Args:
            selected_option_id: 用户选择的方案 ID

        Returns:
            DesignSpec: 完整的设计规格
        """
        self.current_phase = BrainstormingPhase.DECISION_MAKING

        selected = next(
            (opt for opt in self.design_options if opt.option_id == selected_option_id),
            None
        )

        if not selected:
            available_ids = [opt.option_id for opt in self.design_options]
            raise ValueError(
                f"无效的选项 ID: {selected_option_id}. "
                f"可用选项: {', '.join(available_ids)}"
            )

        design_spec = DesignSpec(
            requirements=self.current_requirements,
            selected_option=selected,
            considered_alternatives=self.design_options,
            rationale=self._generate_rationale(selected),
            architecture_notes=self._generate_architecture_notes(selected),
            acceptance_criteria=self._generate_acceptance_criteria(selected),
            created_at=self._get_timestamp()
        )

        # 记录到对话历史
        self.conversation_history.append({
            "phase": self.current_phase.value,
            "selected_option": selected_option_id,
            "timestamp": self._get_timestamp()
        })

        logger.info(f"设计规格已生成: {selected.title}")

        return design_spec

    def get_current_phase(self) -> BrainstormingPhase:
        """获取当前阶段"""
        return self.current_phase

    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history

    def reset(self):
        """重置脑暴管理器"""
        self.current_phase = BrainstormingPhase.REQUIREMENT_GATHERING
        self.conversation_history = []
        self.design_options = []
        self.current_requirements = {}
        logger.info("脑暴管理器已重置")

    # ========== 私有方法 ==========

    def _generate_requirement_questions(self, request: str) -> List[str]:
        """生成需求澄清问题

        Args:
            request: 用户请求

        Returns:
            List[str]: 澄清问题列表
        """
        # 基于用户请求生成针对性问题
        base_questions = [
            "这个功能的主要用户是谁?",
            "核心功能需求是什么?",
            "有性能或扩展性要求吗?",
            "需要兼容哪些平台或框架?",
            "有特定的设计约束吗?"
        ]

        # 根据请求类型添加额外问题
        request_lower = request.lower()

        if "api" in request_lower or "接口" in request_lower:
            base_questions.extend([
                "API 需要支持哪些操作 (GET/POST/PUT/DELETE)?",
                "需要认证和授权吗?",
                "预期的请求量是多少?"
            ])

        if "数据库" in request_lower or "database" in request_lower:
            base_questions.extend([
                "使用什么数据库类型 (关系型/文档型)?",
                "数据量大概是多少?",
                "需要事务支持吗?"
            ])

        if "ui" in request_lower or "界面" in request_lower:
            base_questions.extend([
                "需要响应式设计吗?",
                "支持哪些浏览器?",
                "有特定的设计风格要求吗?"
            ])

        return base_questions

    def _generate_design_options(self, requirements: Dict[str, str]) -> List[DesignOption]:
        """生成多个设计选项

        Args:
            requirements: 需求字典

        Returns:
            List[DesignOption]: 设计选项列表
        """
        options = []

        # 选项 1: 简单快速方案
        options.append(DesignOption(
            option_id="option-1",
            title="简单快速实现",
            description="使用现有框架和库快速实现核心功能",
            pros=[
                "开发速度快",
                "实现成本低",
                "使用成熟技术,风险低",
                "易于维护"
            ],
            cons=[
                "可能不够灵活",
                "长期扩展性有限",
                "可能受限于框架特性"
            ],
            implementation_complexity="low",
            estimated_time="3-5 days",
            risk_level="low"
        ))

        # 选项 2: 平衡方案
        options.append(DesignOption(
            option_id="option-2",
            title="平衡架构设计",
            description="在简单性和扩展性之间取得平衡",
            pros=[
                "良好的扩展性",
                "合理的性能",
                "架构清晰",
                "未来可优化空间大"
            ],
            cons=[
                "开发时间适中",
                "需要一定架构设计经验",
                "初期投入稍高"
            ],
            implementation_complexity="medium",
            estimated_time="1-2 weeks",
            risk_level="medium"
        ))

        # 选项 3: 高性能方案
        options.append(DesignOption(
            option_id="option-3",
            title="高性能优化方案",
            description="针对性能和并发进行优化",
            pros=[
                "高性能",
                "高并发支持",
                "长期扩展性好",
                "适合大规模场景"
            ],
            cons=[
                "开发周期长",
                "实现复杂度高",
                "维护成本高",
                "可能过度设计"
            ],
            implementation_complexity="high",
            estimated_time="2-3 weeks",
            risk_level="high"
        ))

        return options

    def _create_comparison_matrix(self) -> Dict[str, List[str]]:
        """创建方案对比矩阵

        Returns:
            Dict: 对比矩阵
        """
        if not self.design_options:
            return {}

        return {
            "complexity": [opt.implementation_complexity for opt in self.design_options],
            "time": [opt.estimated_time for opt in self.design_options],
            "risk": [opt.risk_level for opt in self.design_options],
            "pros_count": [len(opt.pros) for opt in self.design_options],
            "cons_count": [len(opt.cons) for opt in self.design_options]
        }

    def _recommend_option(self) -> Dict:
        """推荐最佳方案

        Returns:
            Dict: 推荐结果
        """
        if not self.design_options:
            return {"option_id": None, "reason": "没有可用选项"}

        # 简单策略: 推荐中等复杂度的选项 (通常是 option-2)
        recommended = (self.design_options[1]
                       if len(self.design_options) > 1
                       else self.design_options[0])

        return {
            "option_id": recommended.option_id,
            "title": recommended.title,
            "reason": f"推荐 '{recommended.title}' 因为它在复杂性、时间和风险之间取得了良好平衡"
        }

    def _generate_rationale(self, option: DesignOption) -> str:
        """生成选择理由

        Args:
            option: 选中的选项

        Returns:
            str: 选择理由
        """
        rationale = f"选择 '{option.title}' 的原因:\n\n"

        rationale += "**优点:**\n"
        for pro in option.pros:
            rationale += f"- {pro}\n"

        rationale += "\n**权衡考虑:**\n"
        rationale += f"实现复杂度: {option.implementation_complexity}\n"
        rationale += f"预估时间: {option.estimated_time}\n"
        rationale += f"风险等级: {option.risk_level}\n"

        return rationale

    def _generate_architecture_notes(self, option: DesignOption) -> str:
        """生成架构说明

        Args:
            option: 选中的选项

        Returns:
            str: 架构说明
        """
        notes = f"## 架构设计 ({option.title})\n\n"
        notes += f"### 设计概述\n{option.description}\n\n"
        notes += "### 实现要点\n"

        if option.implementation_complexity == "low":
            notes += "- 使用成熟框架和库\n"
            notes += "- 遵循最佳实践\n"
            notes += "- 保持代码简洁\n"
            notes += "- 优先使用现有解决方案\n"
        elif option.implementation_complexity == "medium":
            notes += "- 采用模块化设计\n"
            notes += "- 定义清晰的接口\n"
            notes += "- 考虑未来扩展性\n"
            notes += "- 实现基本的缓存策略\n"
        else:  # high
            notes += "- 使用高性能架构模式\n"
            notes += "- 实现缓存和优化策略\n"
            notes += "- 支持水平扩展\n"
            notes += "- 实现负载均衡\n"
            notes += "- 使用异步处理\n"

        notes += "\n### 技术栈建议\n"
        notes += "- 根据项目需求选择合适的技术栈\n"
        notes += "- 确保技术选型符合团队能力\n"
        notes += "- 考虑长期维护成本\n"

        return notes

    def _generate_acceptance_criteria(self, option: DesignOption) -> List[str]:
        """生成验收标准

        Args:
            option: 选中的选项

        Returns:
            List[str]: 验收标准列表
        """
        criteria = [
            "所有核心功能正常工作",
            "代码通过单元测试 (覆盖率 > 80%)",
            "代码通过集成测试",
            "代码符合项目规范",
            "性能满足预期要求"
        ]

        if option.risk_level == "high":
            criteria.append("完成压力测试")
            criteria.append("完成安全审计")

        return criteria

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
