"""
系统化调试器 - P1 Task 2.2

在遇到错误时进行科学化的问题解决,通过 4 阶段流程:
1. 观察现象 (ErrorObservation) - 收集错误信息和上下文
2. 提出假设 (Hypothesis) - 生成 3-5 个可能原因
3. 验证假设 (Verification) - 测试假设是否成立
4. 确认根因 (RootCause) - 找到根本原因并修复
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DebuggingPhase(Enum):
    """调试阶段"""
    ERROR_OBSERVATION = "error_observation"    # 观察现象
    HYPOTHESIS_GENERATION = "hypothesis_generation"  # 提出假设
    VERIFICATION = "verification"              # 验证假设
    ROOT_CAUSE_CONFIRMATION = "root_cause_confirmation"  # 确认根因


@dataclass
class ErrorObservation:
    """错误观察数据"""
    error_type: str                          # 错误类型 (例如: "SyntaxError", "ValueError")
    error_message: str                       # 错误消息
    stack_trace: List[str]                   # 堆栈跟踪
    occurred_at: str                         # 发生时间
    code_context: Dict[str, str] = field(default_factory=dict)  # 代码上下文
    related_files: List[str] = field(default_factory=list)      # 相关文件
    reproduction_steps: List[str] = field(default_factory=list)  # 复现步骤
    additional_info: Dict[str, Any] = field(default_factory=dict)  # 额外信息


@dataclass
class Hypothesis:
    """假设数据类"""
    hypothesis_id: str                       # 假设 ID (例如: "hypothesis-1")
    title: str                               # 假设标题
    description: str                         # 详细描述
    likelihood: str                          # 可能性等级 ("low", "medium", "high")
    suggested_tests: List[str] = field(default_factory=list)  # 建议的验证测试
    evidence: List[str] = field(default_factory=list)         # 支持证据
    refutations: List[str] = field(default_factory=list)      # 反驳证据


@dataclass
class VerificationResult:
    """验证结果"""
    hypothesis_id: str                       # 被验证的假设 ID
    is_valid: bool                           # 假设是否成立
    test_results: List[str] = field(default_factory=list)     # 测试结果
    confidence: float = 0.0                  # 置信度 (0.0-1.0)
    notes: str = ""                          # 备注


@dataclass
class RootCause:
    """根因分析结果"""
    root_cause_id: str                       # 根因 ID
    description: str                         # 根因描述
    confirmed_hypothesis_id: str             # 确认的假设 ID
    fix_suggestions: List[str] = field(default_factory=list)  # 修复建议
    prevention_strategies: List[str] = field(default_factory=list)  # 防止策略
    related_issues: List[str] = field(default_factory=list)  # 相关问题


@dataclass
class DebuggingReport:
    """调试报告"""
    observation: ErrorObservation            # 错误观察
    hypotheses: List[Hypothesis]             # 生成的假设
    verifications: List[VerificationResult]  # 验证结果
    root_cause: Optional[RootCause]          # 根因分析
    phase: DebuggingPhase                    # 当前阶段
    created_at: str = ""                     # 创建时间
    completed_at: str = ""                   # 完成时间


class SystematicDebugger:
    """系统化调试器 - 协调 4 阶段调试流程"""

    def __init__(self):
        self.current_phase = DebuggingPhase.ERROR_OBSERVATION
        self.debugging_history: List[Dict] = []
        self.current_report: Optional[DebuggingReport] = None

    def start_debugging(self, error_info: Dict[str, Any]) -> ErrorObservation:
        """开始调试 - 阶段 1: 观察现象

        Args:
            error_info: 错误信息字典,包含:
                - error_type: 错误类型
                - error_message: 错误消息
                - stack_trace: 堆栈跟踪
                - code_context: 代码上下文 (可选)

        Returns:
            ErrorObservation: 错误观察对象
        """
        self.current_phase = DebuggingPhase.ERROR_OBSERVATION

        # 创建错误观察
        observation = ErrorObservation(
            error_type=error_info.get("error_type", "UnknownError"),
            error_message=error_info.get("error_message", ""),
            stack_trace=error_info.get("stack_trace", []),
            occurred_at=self._get_timestamp(),
            code_context=error_info.get("code_context", {}),
            related_files=self._extract_related_files(error_info),
            reproduction_steps=self._generate_reproduction_steps(error_info),
            additional_info=error_info.get("additional_info", {})
        )

        # 记录到历史
        self.debugging_history.append({
            "phase": self.current_phase.value,
            "observation": observation,
            "timestamp": self._get_timestamp()
        })

        # 初始化调试报告
        self.current_report = DebuggingReport(
            observation=observation,
            hypotheses=[],
            verifications=[],
            root_cause=None,
            phase=self.current_phase,
            created_at=self._get_timestamp()
        )

        logger.info(f"开始调试阶段: {self.current_phase.value}")
        logger.info(f"错误类型: {observation.error_type}")

        return observation

    def generate_hypotheses(self, observation: ErrorObservation) -> List[Hypothesis]:
        """生成假设 - 阶段 2: 提出可能原因

        Args:
            observation: 错误观察对象

        Returns:
            List[Hypothesis]: 假设列表 (3-5 个)
        """
        self.current_phase = DebuggingPhase.HYPOTHESIS_GENERATION

        # 生成 3-5 个假设
        hypotheses = self._generate_hypotheses_internal(observation)

        # 更新调试报告
        if self.current_report:
            self.current_report.hypotheses = hypotheses
            self.current_report.phase = self.current_phase

        # 记录到历史
        self.debugging_history.append({
            "phase": self.current_phase.value,
            "hypotheses_count": len(hypotheses),
            "timestamp": self._get_timestamp()
        })

        logger.info(f"生成 {len(hypotheses)} 个假设")

        return hypotheses

    def verify_hypothesis(self, hypothesis: Hypothesis, test_results: List[str]) -> VerificationResult:
        """验证假设 - 阶段 3: 测试假设是否成立

        Args:
            hypothesis: 待验证的假设
            test_results: 测试结果列表

        Returns:
            VerificationResult: 验证结果
        """
        self.current_phase = DebuggingPhase.VERIFICATION

        # 分析测试结果
        verification = self._analyze_verification(hypothesis, test_results)

        # 更新调试报告
        if self.current_report:
            self.current_report.verifications.append(verification)

        # 记录到历史
        self.debugging_history.append({
            "phase": self.current_phase.value,
            "hypothesis_id": hypothesis.hypothesis_id,
            "is_valid": verification.is_valid,
            "confidence": verification.confidence,
            "timestamp": self._get_timestamp()
        })

        logger.info(f"验证假设 {hypothesis.hypothesis_id}: {'成立' if verification.is_valid else '不成立'}")

        return verification

    def confirm_root_cause(self, confirmed_hypothesis_id: str) -> RootCause:
        """确认根因 - 阶段 4: 找到根本原因

        Args:
            confirmed_hypothesis_id: 确认的假设 ID

        Returns:
            RootCause: 根因分析结果
        """
        self.current_phase = DebuggingPhase.ROOT_CAUSE_CONFIRMATION

        # 查找确认的假设
        confirmed_hypothesis = None
        if self.current_report and self.current_report.hypotheses:
            confirmed_hypothesis = next(
                (h for h in self.current_report.hypotheses
                 if h.hypothesis_id == confirmed_hypothesis_id),
                None
            )

        if not confirmed_hypothesis:
            available_ids = [h.hypothesis_id for h in self.current_report.hypotheses] if self.current_report else []
            raise ValueError(
                f"无效的假设 ID: {confirmed_hypothesis_id}. "
                f"可用假设: {', '.join(available_ids)}"
            )

        # 生成根因分析
        root_cause = RootCause(
            root_cause_id=f"root-cause-{confirmed_hypothesis_id}",
            description=f"根因: {confirmed_hypothesis.description}",
            confirmed_hypothesis_id=confirmed_hypothesis_id,
            fix_suggestions=self._generate_fix_suggestions(confirmed_hypothesis),
            prevention_strategies=self._generate_prevention_strategies(confirmed_hypothesis),
            related_issues=self._identify_related_issues(confirmed_hypothesis)
        )

        # 更新调试报告
        if self.current_report:
            self.current_report.root_cause = root_cause
            self.current_report.phase = self.current_phase
            self.current_report.completed_at = self._get_timestamp()

        # 记录到历史
        self.debugging_history.append({
            "phase": self.current_phase.value,
            "root_cause_id": root_cause.root_cause_id,
            "timestamp": self._get_timestamp()
        })

        logger.info(f"根因确认: {root_cause.root_cause_id}")

        return root_cause

    def get_current_phase(self) -> DebuggingPhase:
        """获取当前阶段"""
        return self.current_phase

    def get_debugging_report(self) -> Optional[DebuggingReport]:
        """获取完整调试报告"""
        return self.current_report

    def get_debugging_history(self) -> List[Dict]:
        """获取调试历史"""
        return self.debugging_history

    def reset(self):
        """重置调试器"""
        self.current_phase = DebuggingPhase.ERROR_OBSERVATION
        self.debugging_history = []
        self.current_report = None
        logger.info("调试器已重置")

    # ========== 私有方法 ==========

    def _extract_related_files(self, error_info: Dict[str, Any]) -> List[str]:
        """从错误信息中提取相关文件

        Args:
            error_info: 错误信息

        Returns:
            List[str]: 相关文件路径列表
        """
        related_files = []

        # 从堆栈跟踪提取文件
        stack_trace = error_info.get("stack_trace", [])
        for frame in stack_trace:
            if "File " in frame or "文件 " in frame:
                # 提取文件路径
                parts = frame.split('"')
                if len(parts) > 1:
                    file_path = parts[1]
                    if file_path not in related_files:
                        related_files.append(file_path)

        # 从代码上下文提取文件
        code_context = error_info.get("code_context", {})
        if "file_path" in code_context:
            file_path = code_context["file_path"]
            if file_path not in related_files:
                related_files.append(file_path)

        return related_files

    def _generate_reproduction_steps(self, error_info: Dict[str, Any]) -> List[str]:
        """生成复现步骤

        Args:
            error_info: 错误信息

        Returns:
            List[str]: 复现步骤列表
        """
        steps = []

        # 基于错误类型生成默认步骤
        error_type = error_info.get("error_type", "")
        error_message = error_info.get("error_message", "")

        if "Import" in error_type or "导入" in error_type:
            steps.append("1. 运行导入模块的代码")
            steps.append("2. 检查模块路径是否正确")
            steps.append("3. 验证依赖是否已安装")

        elif "Syntax" in error_type or "语法" in error_type:
            steps.append("1. 打开出错的代码文件")
            steps.append("2. 检查语法错误位置")
            steps.append("3. 验证代码语法正确性")

        elif "Value" in error_type or "TypeError" in error_type:
            steps.append("1. 运行出错的函数")
            steps.append("2. 检查输入参数类型")
            steps.append("3. 验证参数值范围")

        elif "Attribute" in error_type or "属性" in error_type:
            steps.append("1. 访问对象属性")
            steps.append("2. 检查对象类型")
            steps.append("3. 验证属性是否存在")

        else:
            # 通用步骤
            steps.append("1. 重现错误场景")
            steps.append(f"2. 检查错误信息: {error_message}")
            steps.append("3. 分析相关代码逻辑")

        return steps

    def _generate_hypotheses_internal(self, observation: ErrorObservation) -> List[Hypothesis]:
        """生成多个假设

        Args:
            observation: 错误观察

        Returns:
            List[Hypothesis]: 假设列表
        """
        hypotheses = []

        error_type = observation.error_type
        error_msg = observation.error_message.lower()

        # 假设 1: 基于错误类型的通用假设
        if "import" in error_type.lower() or "导入" in error_type:
            hypotheses.append(Hypothesis(
                hypothesis_id="hypothesis-1",
                title="模块导入失败",
                description=f"模块可能未安装或路径不正确",
                likelihood="high",
                suggested_tests=[
                    "检查模块是否已安装 (pip list)",
                    "验证模块路径是否在 sys.path 中",
                    "尝试手动导入模块"
                ],
                evidence=[f"错误类型: {error_type}"],
                refutations=[]
            ))

            hypotheses.append(Hypothesis(
                hypothesis_id="hypothesis-2",
                title="依赖版本冲突",
                description="所需模块的版本可能与当前环境不兼容",
                likelihood="medium",
                suggested_tests=[
                    "检查模块版本",
                    "查看依赖要求文件 (requirements.txt)",
                    "尝试升级或降级模块版本"
                ],
                evidence=["导入错误通常与版本有关"],
                refutations=[]
            ))

        elif "syntax" in error_type.lower() or "语法" in error_type:
            hypotheses.append(Hypothesis(
                hypothesis_id="hypothesis-1",
                title="代码语法错误",
                description="代码中存在语法错误,如缺少括号、冒号等",
                likelihood="high",
                suggested_tests=[
                    "使用语法检查工具 (pylint, flake8)",
                    "检查错误行附近的代码",
                    "验证缩进是否正确"
                ],
                evidence=[f"错误类型: {error_type}"],
                refutations=[]
            ))

            hypotheses.append(Hypothesis(
                hypothesis_id="hypothesis-2",
                title="编码问题",
                description="文件编码可能导致语法解析错误",
                likelihood="low",
                suggested_tests=[
                    "检查文件编码 (UTF-8, GBK 等)",
                    "尝试重新保存文件为正确编码"
                ],
                evidence=[],
                refutations=[]
            ))

        else:
            # 其他错误类型的通用假设
            hypotheses.append(Hypothesis(
                hypothesis_id="hypothesis-1",
                title="参数传递错误",
                description="函数调用时传递的参数类型或数量不正确",
                likelihood="high",
                suggested_tests=[
                    "检查函数签名",
                    "验证参数类型",
                    "打印参数值进行调试"
                ],
                evidence=[f"错误类型: {error_type}"],
                refutations=[]
            ))

            hypotheses.append(Hypothesis(
                hypothesis_id="hypothesis-2",
                title="状态异常",
                description="对象或变量的状态不符合预期",
                likelihood="medium",
                suggested_tests=[
                    "检查对象状态",
                    "验证变量值",
                    "添加断点调试"
                ],
                evidence=[],
                refutations=[]
            ))

        # 假设 2: 环境相关
        hypotheses.append(Hypothesis(
            hypothesis_id=f"hypothesis-{len(hypotheses) + 1}",
            title="环境配置问题",
            description="运行环境可能缺少必要配置或资源",
            likelihood="low",
            suggested_tests=[
                "检查环境变量",
                "验证配置文件",
                "确认资源文件存在"
            ],
            evidence=[],
            refutations=[]
        ))

        return hypotheses

    def _analyze_verification(self, hypothesis: Hypothesis, test_results: List[str]) -> VerificationResult:
        """分析验证结果

        Args:
            hypothesis: 假设
            test_results: 测试结果

        Returns:
            VerificationResult: 验证结果
        """
        # 简单分析: 如果所有测试都通过,假设成立
        all_passed = all("通过" in result or "成功" in result or "passed" in result.lower()
                        for result in test_results)

        # 计算置信度
        passed_count = sum(1 for result in test_results
                          if "通过" in result or "成功" in result or "passed" in result.lower())
        confidence = passed_count / len(test_results) if test_results else 0.0

        return VerificationResult(
            hypothesis_id=hypothesis.hypothesis_id,
            is_valid=all_passed and confidence > 0.5,
            test_results=test_results,
            confidence=confidence,
            notes=f"通过 {passed_count}/{len(test_results)} 个测试"
        )

    def _generate_fix_suggestions(self, hypothesis: Hypothesis) -> List[str]:
        """生成修复建议

        Args:
            hypothesis: 确认的假设

        Returns:
            List[str]: 修复建议列表
        """
        suggestions = []

        title_lower = hypothesis.title.lower()

        if "import" in title_lower or "导入" in title_lower:
            suggestions.append("安装缺失的模块: pip install <module_name>")
            suggestions.append("检查 Python 路径配置")
            suggestions.append("验证虚拟环境是否激活")

        elif "语法" in title_lower or "syntax" in title_lower:
            suggestions.append("修复语法错误 (缺少括号、冒号等)")
            suggestions.append("检查代码缩进")
            suggestions.append("使用 IDE 的语法检查功能")

        elif "参数" in title_lower:
            suggestions.append("修正参数类型和数量")
            suggestions.append("添加参数验证逻辑")
            suggestions.append("更新函数文档说明")

        else:
            suggestions.append("根据错误信息修复代码")
            suggestions.append("添加异常处理逻辑")
            suggestions.append("编写单元测试防止回归")

        return suggestions

    def _generate_prevention_strategies(self, hypothesis: Hypothesis) -> List[str]:
        """生成防止策略

        Args:
            hypothesis: 确认的假设

        Returns:
            List[str]: 防止策略列表
        """
        strategies = []

        strategies.append("添加单元测试覆盖此场景")
        strategies.append("实施代码审查流程")
        strategies.append("使用静态分析工具")

        if "import" in hypothesis.title.lower() or "导入" in hypothesis.title.lower():
            strategies.append("使用 requirements.txt 管理依赖")
            strategies.append("设置 CI/CD 环境检查")

        elif "语法" in hypothesis.title.lower() or "syntax" in hypothesis.title.lower():
            strategies.append("配置 IDE 语法检查")
            strategies.append("使用 linter 工具")

        strategies.append("编写清晰的错误处理文档")
        strategies.append("实施日志记录最佳实践")

        return strategies

    def _identify_related_issues(self, hypothesis: Hypothesis) -> List[str]:
        """识别相关问题

        Args:
            hypothesis: 确认的假设

        Returns:
            List[str]: 相关问题列表
        """
        issues = []

        title_lower = hypothesis.title.lower()

        if "import" in title_lower or "导入" in title_lower:
            issues.append("其他模块可能也存在类似导入问题")
            issues.append("依赖版本可能影响其他功能")

        elif "参数" in title_lower:
            issues.append("其他函数调用可能存在类似问题")
            issues.append("类型检查可能需要在多处添加")

        issues.append("类似代码模式可能导致相同错误")
        issues.append("相关测试用例可能需要更新")

        return issues

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
