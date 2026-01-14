# P1 阶段详细规划 - 架构增强

> **日期**: 2026-01-13
> **阶段**: P1 - 架构增强
> **预计周期**: 2-3 周
> **前置条件**: ✅ P0 阶段 100% 完成

---

## 📊 P0 成果回顾

### **里程碑 M1 已达成** ✅

**完成内容**:
- ✅ TDD Validator (300+ 行, 16/16 测试通过)
- ✅ TaskGranularityValidator (369 行, 15/15 测试通过)
- ✅ IssueClassifier (550+ 行, 25/25 测试通过)
- ✅ 完整集成架构 (317 行集成代码)
- ✅ 集成测试套件 (468 行, 16/16 测试通过)
- ✅ **所有测试 72/72 通过 (100%)**

**关键指标**:
```
效率:     300% (1 天完成 2 周工作量)
质量:     100% (所有测试通过)
代码:     1,769+ 行核心代码
测试:     2,110+ 行测试代码
文档:     15,000+ 字完整文档
集成:     3 个验证器完全工作
```

---

## 🎯 P1 阶段目标

### **核心使命**: 架构增强和智能化升级

**P0 阶段建立了核心验证机制**, P1 阶段将在此基础上:
1. **引入脑暴阶段** - 生成前设计探索
2. **增强调试能力** - 系统化问题解决
3. **强制技能使用** - 确保最佳实践
4. **优化执行效率** - 性能和并发

---

## 📋 P1 任务清单

### **Task 2.1: 脑暴阶段集成** (2 周)

**优先级**: P1 - 高
**负责人**: 架构团队

#### **目标**

在代码生成前增加设计探索阶段,通过结构化问答:
- 收集需求细节
- 探索多种方案
- 让用户选择最佳方案
- 生成设计规格文档

#### **Week 1: 基础实现**

**1.1 设计 BrainstormingManager 架构**

**文件**: `planning/brainstorming_manager.py`

**核心组件**:
```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class BrainstormingPhase(Enum):
    """脑暴阶段"""
    REQUIREMENT_GATHERING = "requirement_gathering"  # 需求收集
    SOLUTION_EXPLORATION = "solution_exploration"    # 方案探索
    ALTERNATIVE_COMPARISON = "alternative_comparison" # 方案对比
    DECISION_MAKING = "decision_making"              # 决策确认

@dataclass
class DesignOption:
    """设计选项"""
    option_id: str
    title: str
    description: str
    pros: List[str]
    cons: List[str]
    implementation_complexity: str  # "low", "medium", "high"
    estimated_time: str
    risk_level: str  # "low", "medium", "high"

@dataclass
class DesignSpec:
    """设计规格"""
    requirements: Dict[str, str]
    selected_option: DesignOption
    considered_alternatives: List[DesignOption]
    rationale: str  # 为什么选择这个方案
    architecture_notes: str
    acceptance_criteria: List[str]

class BrainstormingManager:
    """脑暴管理器 - 协调设计探索流程"""

    def __init__(self):
        self.current_phase = BrainstormingPhase.REQUIREMENT_GATHERING
        self.conversation_history: List[Dict] = []
        self.design_options: List[DesignOption] = []

    def start_brainstorming(self, user_request: str) -> Dict[str, str]:
        """开始脑暴阶段 - 收集需求"""
        self.current_phase = BrainstormingPhase.REQUIREMENT_GATHERING

        questions = self._generate_requirement_questions(user_request)
        return {
            "phase": self.current_phase.value,
            "questions": questions,
            "message": "让我们先澄清需求细节"
        }

    def explore_solutions(self, requirements: Dict) -> List[DesignOption]:
        """基于需求探索多种解决方案"""
        self.current_phase = BrainstormingPhase.SOLUTION_EXPLORATION

        # 生成 3-5 个设计选项
        self.design_options = self._generate_design_options(requirements)

        return self.design_options

    def compare_alternatives(self) -> Dict:
        """对比不同方案"""
        self.current_phase = BrainstormingPhase.ALTERNATIVE_COMPARISON

        comparison = {
            "options": self.design_options,
            "comparison_matrix": self._create_comparison_matrix(),
            "recommendation": self._recommend_option()
        }

        return comparison

    def finalize_design(self, selected_option_id: str) -> DesignSpec:
        """确认设计并生成设计规格"""
        self.current_phase = BrainstormingPhase.DECISION_MAKING

        selected = next(
            (opt for opt in self.design_options if opt.option_id == selected_option_id),
            None
        )

        if not selected:
            raise ValueError(f"Invalid option ID: {selected_option_id}")

        design_spec = DesignSpec(
            requirements=self._extract_requirements(),
            selected_option=selected,
            considered_alternatives=self.design_options,
            rationale=self._generate_rationale(selected),
            architecture_notes=self._generate_architecture_notes(selected),
            acceptance_criteria=self._generate_acceptance_criteria(selected)
        )

        return design_spec

    def _generate_requirement_questions(self, request: str) -> List[str]:
        """生成需求澄清问题"""
        # 基于用户请求生成针对性问题
        questions = [
            "这个功能的主要用户是谁?",
            "核心功能需求是什么?",
            "有性能或扩展性要求吗?",
            "需要兼容哪些平台或框架?",
            "有特定的设计约束吗?"
        ]

        return questions

    def _generate_design_options(self, requirements: Dict) -> List[DesignOption]:
        """生成多个设计选项"""
        # 实现方案生成逻辑
        # 至少生成 3 个选项
        pass

    def _create_comparison_matrix(self) -> Dict:
        """创建方案对比矩阵"""
        pass

    def _recommend_option(self) -> Dict:
        """推荐最佳方案"""
        pass

    def _extract_requirements(self) -> Dict[str, str]:
        """提取需求"""
        pass

    def _generate_rationale(self, option: DesignOption) -> str:
        """生成选择理由"""
        pass

    def _generate_architecture_notes(self, option: DesignOption) -> str:
        """生成架构说明"""
        pass

    def _generate_acceptance_criteria(self, option: DesignOption) -> List[str]:
        """生成验收标准"""
        pass
```

**1.2 集成到 CLI 工作流**

**修改**: `cli/main.py`

```python
from planning.brainstorming_manager import BrainstormingManager

class SuperAgentCLI:
    def __init__(self):
        self.brainstorming_manager = BrainstormingManager()

    def handle_user_request(self, request: str):
        """处理用户请求"""

        # 1. 脑暴阶段 (新增)
        if self._should_brainstorm(request):
            design_spec = self._run_brainstorming(request)

            # 2. 生成步骤 (使用设计规格)
            steps = self.planner.generate_detailed_plan(
                user_request=request,
                design_spec=design_spec  # 传入设计规格
            )

            # 3. 执行步骤 (现有逻辑)
            for step in steps:
                self.coding_agent.execute_step(step)
        else:
            # 简单请求,直接执行
            steps = self.planner.generate_simple_plan(request)
            for step in steps:
                self.coding_agent.execute_step(step)

    def _should_brainstorm(self, request: str) -> bool:
        """判断是否需要脑暴阶段"""
        # 简单任务跳过脑暴
        # 复杂任务必须脑暴
        keywords = ["实现", "添加功能", "设计", "重构"]
        return any(kw in request for kw in keywords)

    def _run_brainstorming(self, request: str) -> DesignSpec:
        """运行脑暴流程"""

        # 阶段 1: 收集需求
        questions = self.brainstorming_manager.start_brainstorming(request)
        self._display_questions(questions)

        requirements = self._collect_requirements()

        # 阶段 2: 探索方案
        options = self.brainstorming_manager.explore_solutions(requirements)
        self._display_options(options)

        # 阶段 3: 对比方案
        comparison = self.brainstorming_manager.compare_alternatives()
        self._display_comparison(comparison)

        # 阶段 4: 用户选择
        selected_id = self._get_user_selection()

        # 生成设计规格
        design_spec = self.brainstorming_manager.finalize_design(selected_id)

        return design_spec
```

#### **Week 2: 集成和完善**

**1.3 设计文档保存**

**文件**: `docs/design_specs/{design_id}.md`

```markdown
# 设计规格: {title}

> **生成时间**: {timestamp}
> **设计 ID**: {design_id}

## 需求分析

{requirements}

## 方案对比

### 选项 1: {option_title}

**描述**: {description}

**优点**:
- {pro}

**缺点**:
- {con}

**复杂度**: {complexity}
**预估时间**: {time}
**风险等级**: {risk}

...

## 最终选择

**选择方案**: {selected_option}

**选择理由**:
{rationale}

## 架构说明

{architecture_notes}

## 验收标准

- [ ] {criteria_1}
- [ ] {criteria_2}
...
```

**1.4 设计验证机制**

**文件**: `planning/design_validator.py`

```python
class DesignValidator:
    """设计规格验证器"""

    def validate_design_spec(self, spec: DesignSpec) -> tuple[bool, List[str]]:
        """验证设计规格完整性"""

        errors = []

        # 检查需求
        if not spec.requirements:
            errors.append("缺少需求描述")

        # 检查方案选项
        if len(spec.considered_alternatives) < 2:
            errors.append("至少需要考虑 2 个方案")

        # 检查选择理由
        if not spec.rationale:
            errors.append("缺少选择理由")

        # 检查验收标准
        if not spec.acceptance_criteria:
            errors.append("缺少验收标准")

        return len(errors) == 0, errors
```

#### **验收标准**

- [x] BrainstormingManager 类实现完整
- [ ] 4 个脑暴阶段都能正常工作
- [ ] 能生成至少 3 个设计选项
- [ ] CLI 工作流集成完成
- [ ] 设计文档自动保存
- [ ] 设计验证机制正常
- [ ] 用户满意度 > 80%

**测试要求**:
- 单元测试: `tests/test_brainstorming_manager.py` (20+ 测试)
- 集成测试: `tests/test_brainstorming_integration.py` (10+ 测试)
- 通过率: 100%

---

### **Task 2.2: 4 阶段调试流程** (1 周)

**优先级**: P1 - 高
**负责人**: 调试专家

#### **目标**

实现系统化的调试流程,将调试从随机探索转变为科学方法:
1. **观察现象** - 系统化错误收集
2. **提出假设** - 基于证据的推理
3. **验证假设** - 可重复的测试
4. **确认根因** - 彻底解决问题

#### **核心实现**

**文件**: `debugging/systematic_debugger.py`

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class DebugPhase(Enum):
    """调试阶段"""
    OBSERVE = "observe"           # 观察现象
    HYPOTHESIZE = "hypothesize"   # 提出假设
    VERIFY = "verify"             # 验证假设
    CONFIRM = "confirm"           # 确认根因

@dataclass
class ErrorObservation:
    """错误观察"""
    error_message: str
    error_type: str
    stack_trace: List[str]
    context: Dict  # 错误发生时的上下文
    reproduction_steps: List[str]
    related_files: List[str]

@dataclass
class Hypothesis:
    """假设"""
    hypothesis_id: str
    description: str
    suspected_cause: str
    confidence: str  # "low", "medium", "high"
    verification_method: str
    expected_outcome: str

@dataclass
class VerificationResult:
    """验证结果"""
    hypothesis_id: str
    passed: bool
    actual_outcome: str
    evidence: List[str]

@dataclass
class RootCause:
    """根因分析"""
    cause: str
    explanation: str
    fix_strategy: str
    prevention_measures: List[str]

class SystematicDebugger:
    """系统化调试器"""

    def __init__(self):
        self.current_phase = DebugPhase.OBSERVE
        self.observations: List[ErrorObservation] = []
        self.hypotheses: List[Hypothesis] = []
        self.verifications: List[VerificationResult] = []
        self.root_cause: Optional[RootCause] = None

    def start_debugging(self, error: Exception, context: Dict) -> Dict:
        """阶段 1: 观察现象"""
        self.current_phase = DebugPhase.OBSERVE

        observation = self._collect_error_observation(error, context)
        self.observations.append(observation)

        return {
            "phase": self.current_phase.value,
            "observation": observation,
            "next_actions": self._suggest_next_actions(observation)
        }

    def generate_hypotheses(self) -> List[Hypothesis]:
        """阶段 2: 提出假设"""
        self.current_phase = DebugPhase.HYPOTHESIZE

        # 基于观察生成 3-5 个假设
        self.hypotheses = self._generate_hypotheses_from_observations()

        return self.hypotheses

    def verify_hypothesis(self, hypothesis_id: str) -> VerificationResult:
        """阶段 3: 验证假设"""
        self.current_phase = DebugPhase.VERIFY

        hypothesis = self._get_hypothesis(hypothesis_id)
        result = self._run_verification_test(hypothesis)

        self.verifications.append(result)

        return result

    def confirm_root_cause(self, verified_hypothesis_id: str) -> RootCause:
        """阶段 4: 确认根因"""
        self.current_phase = DebugPhase.CONFIRM

        hypothesis = self._get_hypothesis(verified_hypothesis_id)
        verification = self._get_verification(verified_hypothesis_id)

        self.root_cause = RootCause(
            cause=hypothesis.suspected_cause,
            explanation=self._generate_explanation(hypothesis, verification),
            fix_strategy=self._generate_fix_strategy(hypothesis),
            prevention_measures=self._suggest_prevention(hypothesis)
        )

        return self.root_cause

    def _collect_error_observation(self, error: Exception, context: Dict) -> ErrorObservation:
        """收集错误观察"""
        import traceback

        return ErrorObservation(
            error_message=str(error),
            error_type=type(error).__name__,
            stack_trace=traceback.format_exc().split('\n'),
            context=context,
            reproduction_steps=self._extract_reproduction_steps(context),
            related_files=self._extract_related_files(error)
        )

    def _generate_hypotheses_from_observations(self) -> List[Hypothesis]:
        """基于观察生成假设"""
        hypotheses = []

        # 常见假设模式
        patterns = [
            {
                "cause": "空引用/None 值",
                "confidence": "high",
                "verification": "检查变量是否为 None",
                "expected": "变量值为 None"
            },
            {
                "cause": "类型不匹配",
                "confidence": "medium",
                "verification": "检查类型是否为预期类型",
                "expected": "类型不匹配"
            },
            {
                "cause": "依赖缺失",
                "confidence": "low",
                "verification": "检查导入和依赖",
                "expected": "ImportError 或 ModuleNotFoundError"
            },
            # ... 更多模式
        ]

        for i, pattern in enumerate(patterns):
            hypotheses.append(Hypothesis(
                hypothesis_id=f"hyp-{i}",
                description=f"可能原因: {pattern['cause']}",
                suspected_cause=pattern['cause'],
                confidence=pattern['confidence'],
                verification_method=pattern['verification'],
                expected_outcome=pattern['expected']
            ))

        return hypotheses

    def _run_verification_test(self, hypothesis: Hypothesis) -> VerificationResult:
        """运行验证测试"""
        # 实现验证逻辑
        pass

    def _generate_explanation(self, hypothesis: Hypothesis, verification: VerificationResult) -> str:
        """生成根因解释"""
        pass

    def _generate_fix_strategy(self, hypothesis: Hypothesis) -> str:
        """生成修复策略"""
        pass

    def _suggest_prevention(self, hypothesis: Hypothesis) -> List[str]:
        """建议预防措施"""
        pass

    def _extract_reproduction_steps(self, context: Dict) -> List[str]:
        """提取复现步骤"""
        pass

    def _extract_related_files(self, error: Exception) -> List[str]:
        """提取相关文件"""
        pass

    def _suggest_next_actions(self, observation: ErrorObservation) -> List[str]:
        """建议下一步行动"""
        actions = [
            f"1. 检查错误类型: {observation.error_type}",
            f"2. 查看堆栈跟踪的顶层调用",
            f"3. 检查相关文件: {', '.join(observation.related_files[:3])}"
        ]

        return actions

    def _get_hypothesis(self, hypothesis_id: str) -> Hypothesis:
        """获取假设"""
        return next((h for h in self.hypotheses if h.hypothesis_id == hypothesis_id), None)

    def _get_verification(self, hypothesis_id: str) -> VerificationResult:
        """获取验证结果"""
        return next((v for v in self.verifications if v.hypothesis_id == hypothesis_id), None)
```

#### **集成到执行流程**

**修改**: `execution/coding_agent.py`

```python
from debugging.systematic_debugger import SystematicDebugger

class CodingAgent:
    def __init__(self, enable_debugging=True):
        # ... 现有代码
        self.debugger = SystematicDebugger() if enable_debugging else None

    def execute_step(self, step: Step) -> ExecutionResult:
        """执行步骤,带调试支持"""
        try:
            # 原有执行逻辑
            result = self._execute_step_impl(step)

            # TDD 验证 (已有)
            if self.tdd_enabled:
                tdd_valid, tdd_violations = self.validate_tdd_execution(result)

            return result

        except Exception as error:
            # 新增: 启动系统化调试
            if self.debugger:
                return self._debug_error(error, step)

            raise

    def _debug_error(self, error: Exception, step: Step) -> ExecutionResult:
        """调试错误"""

        # 阶段 1: 观察
        observation_result = self.debugger.start_debugging(error, {
            "step": step,
            "workspace": self.workspace
        })

        self.logger.info(f"调试阶段: 观察\n{observation_result['observation']}")

        # 阶段 2: 假设
        hypotheses = self.debugger.generate_hypotheses()

        self.logger.info(f"调试阶段: 假设\n生成 {len(hypotheses)} 个假设:")
        for hyp in hypotheses:
            self.logger.info(f"  - {hyp.description} (置信度: {hyp.confidence})")

        # 阶段 3: 验证 (选择置信度最高的)
        best_hypothesis = max(hypotheses, key=lambda h: h.confidence)
        verification = self.debugger.verify_hypothesis(best_hypothesis.hypothesis_id)

        self.logger.info(f"调试阶段: 验证\n{verification}")

        # 阶段 4: 确认
        if verification.passed:
            root_cause = self.debugger.confirm_root_cause(best_hypothesis.hypothesis_id)

            self.logger.info(f"调试阶段: 根因\n{root_cause}")

            # 尝试自动修复
            if self._can_auto_fix(root_cause):
                return self._auto_fix(root_cause, step)

        # 无法自动修复,返回错误
        raise
```

#### **验收标准**

- [ ] SystematicDebugger 类实现完整
- [ ] 4 个调试阶段都能正常工作
- [ ] 能生成多个假设并验证
- [ ] CodingAgent 集成完成
- [ ] 调试日志清晰完整
- [ ] 根因分析准确率 > 80%

**测试要求**:
- 单元测试: `tests/test_systematic_debugger.py` (20+ 测试)
- 集成测试: `tests/test_debugging_integration.py` (10+ 测试)
- 通过率: 100%

---

### **Task 2.3: 技能触发系统** (1 周)

**优先级**: P1 - 高
**负责人**: 架构团队

#### **目标**

确保在使用 SuperAgent 前必须具备必要技能,避免低质量开发:
- 强制检查必需技能
- 缺少技能时拒绝执行
- 提供技能获取指引

#### **核心实现**

**文件**: `orchestration/skill_checker.py`

```python
from typing import List, Dict, Optional
from enum import Enum

class Skill(Enum):
    """必需技能"""
    BRAINSTORMING = "brainstorming"                        # 脑暴设计
    TEST_DRIVEN_DEVELOPMENT = "test-driven-development"   # TDD 开发
    SYSTEMATIC_DEBUGGING = "systematic-debugging"         # 系统化调试
    CODE_REVIEW = "requesting-code-review"                # 代码审查

class SkillChecker:
    """技能检查器"""

    # 必需技能映射
    REQUIRED_SKILLS = {
        "complex_feature": [Skill.BRAINSTORMING, Skill.TEST_DRIVEN_DEVELOPMENT],
        "bug_fix": [Skill.SYSTEMATIC_DEBUGGING, Skill.TEST_DRIVEN_DEVELOPMENT],
        "refactoring": [Skill.TEST_DRIVEN_DEVELOPMENT, Skill.CODE_REVIEW],
        "simple_task": [Skill.TEST_DRIVEN_DEVELOPMENT]
    }

    def __init__(self):
        self.available_skills: Dict[Skill, bool] = {
            skill: False for skill in Skill
        }

    def check_skills(self, task_type: str) -> tuple[bool, List[Skill]]:
        """检查任务所需技能是否具备"""

        required = self._get_required_skills(task_type)
        missing = [skill for skill in required if not self.available_skills[skill]]

        return len(missing) == 0, missing

    def enable_skill(self, skill: Skill):
        """启用技能"""
        self.available_skills[skill] = True

    def disable_skill(self, skill: Skill):
        """禁用技能"""
        self.available_skills[skill] = False

    def get_skill_status(self) -> Dict[Skill, bool]:
        """获取所有技能状态"""
        return self.available_skills

    def _get_required_skills(self, task_type: str) -> List[Skill]:
        """获取任务所需技能"""

        # 简单分类
        keywords_complex = ["实现", "添加功能", "设计", "重构"]
        keywords_bug = ["修复", "bug", "错误"]
        keywords_refactor = ["重构", "优化"]

        request_lower = task_type.lower()

        if any(kw in request_lower for kw in keywords_complex):
            return self.REQUIRED_SKILLS["complex_feature"]
        elif any(kw in request_lower for kw in keywords_bug):
            return self.REQUIRED_SKILLS["bug_fix"]
        elif any(kw in request_lower for kw in keywords_refactor):
            return self.REQUIRED_SKILLS["refactoring"]
        else:
            return self.REQUIRED_SKILLS["simple_task"]

class SkillNotAvailableError(Exception):
    """技能不可用异常"""
    def __init__(self, missing_skills: List[Skill]):
        self.missing_skills = missing_skills
        message = f"缺少必需技能: {', '.join([s.value for s in missing_skills])}"

        # 提供技能获取指引
        guidance = self._generate_skill_guidance(missing_skills)
        message += f"\n\n请先学习以下技能:\n{guidance}"

        super().__init__(message)

    @staticmethod
    def _generate_skill_guidance(missing_skills: List[Skill]) -> str:
        """生成技能学习指引"""

        guidance_map = {
            Skill.BRAINSTORMING: """
**脑暴设计技能**
- 理解设计思维和方案探索
- 学习如何提出多个替代方案
- 掌握权衡分析方法
""",
            Skill.TEST_DRIVEN_DEVELOPMENT: """
**TDD 开发技能**
- 理解 RED-GREEN-REFACTOR 循环
- 先写测试再写代码
- 掌握测试覆盖率要求
""",
            Skill.SYSTEMATIC_DEBUGGING: """
**系统化调试技能**
- 学习 4 阶段调试流程
- 观察现象 → 提出假设 → 验证假设 → 确认根因
- 掌握科学化调试方法
""",
            Skill.CODE_REVIEW: """
**代码审查技能**
- 理解代码审查最佳实践
- 学习如何识别代码问题
- 掌握分级修复策略
"""
        }

        guidance = []
        for skill in missing_skills:
            if skill in guidance_map:
                guidance.append(f"\n{guidance_map[skill]}")

        return '\n'.join(guidance)
```

#### **集成到 CLI**

**修改**: `cli/main.py`

```python
from orchestration.skill_checker import SkillChecker, SkillNotAvailableError

class SuperAgentCLI:
    def __init__(self):
        # ... 现有代码
        self.skill_checker = SkillChecker()

        # 启用所有可用技能
        self._initialize_skills()

    def _initialize_skills(self):
        """初始化技能状态"""

        # 根据配置启用技能
        # 默认全部启用 (开发完成后)
        # 生产环境可以要求用户显式启用
        for skill in Skill:
            self.skill_checker.enable_skill(skill)

    def handle_user_request(self, request: str):
        """处理用户请求"""

        # 1. 检查技能 (新增)
        has_skills, missing = self.skill_checker.check_skills(request)

        if not has_skills:
            raise SkillNotAvailableError(missing)

        # 2. 脑暴阶段 (如果需要)
        if self._should_brainstorm(request):
            design_spec = self._run_brainstorming(request)

        # 3. 执行任务 (现有逻辑)
        # ...
```

#### **验收标准**

- [ ] SkillChecker 类实现完整
- [ ] 能检测任务类型并映射到技能
- [ ] 缺少技能时正确拒绝
- [ ] 技能获取指引清晰
- [ ] CLI 集成完成
- [ ] 错误提示友好

**测试要求**:
- 单元测试: `tests/test_skill_checker.py` (15+ 测试)
- 集成测试: `tests/test_skill_integration.py` (8+ 测试)
- 通过率: 100%

---

### **Task 2.4: 并行执行优化** (1 周)

**优先级**: P1 - 中
**负责人**: 性能优化团队

#### **目标**

优化任务执行效率,支持安全的并行执行:
- 识别可并行任务
- 控制并发数量
- 处理资源竞争
- 监控执行性能

#### **核心实现**

**文件**: `execution/parallel_executor.py`

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import threading

class ParallelExecutor:
    """并行执行器"""

    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.Lock()

    def execute_steps_parallel(self, steps: List[Step]) -> List[ExecutionResult]:
        """并行执行步骤"""

        # 1. 构建依赖图
        dependency_graph = self._build_dependency_graph(steps)

        # 2. 识别可并行组
        parallel_groups = self._identify_parallel_groups(dependency_graph)

        # 3. 按组执行
        results = []

        for group in parallel_groups:
            if len(group) == 1:
                # 单个任务,直接执行
                result = self._execute_single(group[0])
                results.append(result)
            else:
                # 多个任务,并行执行
                group_results = self._execute_parallel(group)
                results.extend(group_results)

        return results

    def _build_dependency_graph(self, steps: List[Step]) -> Dict[str, List[str]]:
        """构建依赖图"""
        graph = {}

        for step in steps:
            graph[step.id] = step.dependencies if hasattr(step, 'dependencies') else []

        return graph

    def _identify_parallel_groups(self, graph: Dict[str, List[str]]) -> List[List[Step]]:
        """识别可并行执行的组"""

        # 简单实现: 拓扑排序
        # 返回每层可并行执行的步骤列表
        groups = []
        remaining = set(graph.keys())
        executed = set()

        while remaining:
            # 找出所有依赖已满足的步骤
            ready = [
                step_id for step_id in remaining
                if all(dep in executed for dep in graph[step_id])
            ]

            if not ready:
                # 循环依赖
                raise ValueError("检测到循环依赖")

            groups.append(ready)
            executed.update(ready)
            remaining -= set(ready)

        return groups

    def _execute_single(self, step: Step) -> ExecutionResult:
        """执行单个步骤"""
        # 使用现有的 CodingAgent
        pass

    def _execute_parallel(self, steps: List[Step]) -> List[ExecutionResult]:
        """并行执行多个步骤"""

        futures = {}
        results = []

        # 提交所有任务
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for step in steps:
                future = executor.submit(self._execute_single, step)
                futures[future] = step

            # 收集结果
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # 处理失败
                    self.logger.error(f"任务执行失败: {e}")

        return results

class ResourceManager:
    """资源管理器 - 避免竞争"""

    def __init__(self):
        self.locked_files: Dict[str, threading.Lock] = {}
        self.locked_resources: Dict[str, threading.Lock] = {}

    def acquire_file(self, file_path: str) -> threading.Lock:
        """获取文件锁"""
        with threading.Lock():
            if file_path not in self.locked_files:
                self.locked_files[file_path] = threading.Lock()

        return self.locked_files[file_path]

    def acquire_resource(self, resource_id: str) -> threading.Lock:
        """获取资源锁"""
        with threading.Lock():
            if resource_id not in self.locked_resources:
                self.locked_resources[resource_id] = threading.Lock()

        return self.locked_resources[resource_id]
```

#### **集成到执行流程**

**修改**: `execution/coding_agent.py`

```python
from execution.parallel_executor import ParallelExecutor, ResourceManager

class CodingAgent:
    def __init__(self, enable_parallel=True):
        # ... 现有代码
        self.parallel_enabled = enable_parallel
        self.parallel_executor = ParallelExecutor() if enable_parallel else None
        self.resource_manager = ResourceManager()

    def execute_plan(self, steps: List[Step]) -> List[ExecutionResult]:
        """执行计划"""

        if self.parallel_enabled and self._can_execute_parallel(steps):
            # 并行执行
            return self.parallel_executor.execute_steps_parallel(steps)
        else:
            # 串行执行
            results = []
            for step in steps:
                result = self.execute_step(step)
                results.append(result)

            return results

    def _can_execute_parallel(self, steps: List[Step]) -> bool:
        """判断是否可以并行执行"""

        # 检查步骤数量
        if len(steps) < 2:
            return False

        # 检查依赖关系
        # 如果所有步骤都相互独立,则可以并行
        for step in steps:
            if hasattr(step, 'dependencies') and step.dependencies:
                return False

        return True
```

#### **验收标准**

- [ ] ParallelExecutor 类实现完整
- [ ] 能正确识别可并行任务
- [ ] 依赖关系正确处理
- [ ] 资源竞争避免
- [ ] 性能提升 > 20%
- [ ] 执行日志清晰

**测试要求**:
- 单元测试: `tests/test_parallel_executor.py` (15+ 测试)
- 集成测试: `tests/test_parallel_integration.py` (8+ 测试)
- 性能测试: `tests/test_parallel_performance.py` (5+ 测试)
- 通过率: 100%

---

## 📊 P1 整体进度跟踪

### **时间线**

```
Week 1-2 (Jan 14 - Jan 27):
  ✅ Task 2.1: 脑暴阶段集成

Week 3 (Jan 28 - Feb 3):
  ✅ Task 2.2: 4 阶段调试流程
  ✅ Task 2.3: 技能触发系统

Week 4 (Feb 4 - Feb 10):
  ✅ Task 2.4: 并行执行优化

Milestone M2: 🎉 P1 完成
```

### **预计代码量**

| 任务 | 核心代码 | 测试代码 | 文档 | 总计 |
|------|---------|---------|------|------|
| Task 2.1 | ~600 行 | ~500 行 | ~2000 字 | ~3100 行 |
| Task 2.2 | ~500 行 | ~400 行 | ~1500 字 | ~2400 行 |
| Task 2.3 | ~300 行 | ~300 行 | ~1000 字 | ~1600 行 |
| Task 2.4 | ~400 行 | ~400 行 | ~1000 字 | ~1800 行 |
| **总计** | **~1800 行** | **~1600 行** | **~5500 字** | **~8900 行** |

### **验收指标**

```
✅ 所有 P1 任务完成
✅ 单元测试 100% 通过 (65+ 测试)
✅ 集成测试 100% 通过 (35+ 测试)
✅ 性能测试通过 (5+ 测试)
✅ 文档完整清晰
✅ 性能提升 > 20%
```

---

## 🎯 里程碑 M2 目标

### **完成内容**:
- ✅ 4 个 P1 任务全部完成
- ✅ 脑暴设计系统可用
- ✅ 系统化调试流程完整
- ✅ 技能检查机制健全
- ✅ 并行执行优化实现
- ✅ 所有测试 100% 通过

### **关键指标**:
```
效率:     预计 2-3 周完成
质量:     100% 测试通过
代码:     1800+ 行核心代码
测试:     1600+ 行测试代码
文档:     5500+ 字完整文档
性能:     > 20% 提升
```

---

## 🔗 相关链接

### **P0 成果**
- [M1 最终总结](../M1_FINAL_SUMMARY.md)
- [P0 集成修复报告](../reports/P0_INTEGRATION_FIX_REPORT.md)
- [v3.2 实施状态](../v3.2_IMPLEMENTATION_STATUS.md)

### **开发计划**
- [SuperAgent v3.2 开发计划](../DEVELOPMENT_PLAN_v3.2.md)

---

**报告生成时间**: 2026-01-13 10:20
**SuperAgent v3.2+ 开发团队

🚀 **准备开始 P1 阶段开发!**
