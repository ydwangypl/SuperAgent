#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent 全面功能测试套件

测试范围:
1. CLI交互功能测试
2. 对话层功能测试
3. 规划系统功能测试
4. 编排系统功能测试
5. Agent执行功能测试
6. 记忆系统功能测试
7. 代码审查功能测试
8. 错误恢复功能测试
9. 安全功能测试
10. 性能功能测试
"""

import sys
import os
import time
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import traceback
import unittest
from io import StringIO

# 添加项目根目录到路径
SUPERAGENT_ROOT = Path(__file__).parent
sys.path.insert(0, str(SUPERAGENT_ROOT))

# 测试结果记录
test_results = {
    "summary": {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": [],
        "start_time": None,
        "end_time": None,
        "duration": 0
    },
    "modules": {
        "cli": {"total": 0, "passed": 0, "failed": 0, "tests": []},
        "conversation": {"total": 0, "passed": 0, "failed": 0, "tests": []},
        "planning": {"total": 0, "passed": 0, "failed": 0, "tests": []},
        "orchestration": {"total": 0, "passed": 0, "failed": 0, "tests": []},
        "execution": {"total": 0, "passed": 0, "failed": 0, "tests": []},
        "memory": {"total": 0, "passed": 0, "failed": 0, "tests": []},
        "review": {"total": 0, "passed": 0, "failed": 0, "tests": []},
        "error_recovery": {"total": 0, "passed": 0, "failed": 0, "tests": []},
        "security": {"total": 0, "passed": 0, "failed": 0, "tests": []},
        "performance": {"total": 0, "passed": 0, "failed": 0, "tests": []}
    }
}


class TestResult:
    """测试结果记录"""

    def __init__(self, module: str, test_name: str):
        self.module = module
        self.test_name = test_name
        self.start_time = None
        self.end_time = None
        self.duration = 0
        self.status = "pending"  # pending, passed, failed, skipped
        self.error_message = ""
        self.details = {}

    def mark_started(self):
        self.start_time = time.time()
        self.status = "running"

    def mark_passed(self, details: Optional[Dict] = None):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = "passed"
        if details:
            self.details = details

    def mark_failed(self, error_message: str, details: Optional[Dict] = None):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = "failed"
        self.error_message = error_message
        if details:
            self.details = details

    def to_dict(self) -> Dict:
        return {
            "test_name": self.test_name,
            "status": self.status,
            "duration": round(self.duration, 3),
            "error_message": self.error_message,
            "details": self.details
        }


def run_test(module: str, test_name: str, test_func) -> TestResult:
    """运行单个测试"""
    result = TestResult(module, test_name)
    result.mark_started()

    print(f"  [{module.upper()}] 运行: {test_name}...", end=" ")

    try:
        # 运行测试函数
        test_result = test_func()

        # 检查结果
        if test_result is False:
            result.mark_failed("Test returned False")
            print("❌ 失败")
        elif isinstance(test_result, dict) and test_result.get("success") is False:
            result.mark_failed(test_result.get("error", "Unknown error"), test_result)
            print("❌ 失败")
        else:
            details = test_result if isinstance(test_result, dict) else {}
            result.mark_passed(details)
            print("✅ 通过")

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        result.mark_failed(error_msg, {"traceback": traceback.format_exc()})
        print("❌ 失败")
        print(f"    错误: {error_msg}")

    return result


def update_results(result: TestResult):
    """更新测试结果汇总"""
    module_data = test_results["modules"][result.module]
    module_data["total"] += 1
    module_data["tests"].append(result.to_dict())

    if result.status == "passed":
        module_data["passed"] += 1
        test_results["summary"]["passed"] += 1
    elif result.status == "failed":
        module_data["failed"] += 1
        test_results["summary"]["failed"] += 1
        test_results["summary"]["errors"].append({
            "module": result.module,
            "test": result.test_name,
            "error": result.error_message
        })

    test_results["summary"]["total"] += 1


# ============================================================================
# 1. CLI交互功能测试
# ============================================================================

def test_cli_import():
    """测试CLI模块导入"""
    try:
        from cli.main import SuperAgentCLI
        return {"success": True, "class_exists": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_cli_commands():
    """测试CLI命令注册"""
    try:
        from cli.main import SuperAgentCLI
        cli = SuperAgentCLI()

        # 检查关键命令是否存在
        commands = ['do_status', 'do_clear', 'do_pwd', 'do_cd', 'do_plan',
                   'do_execute', 'do_help', 'do_quit']

        missing = [cmd for cmd in commands if not hasattr(cli, cmd)]

        if missing:
            return {"success": False, "error": f"Missing commands: {missing}"}

        return {"success": True, "commands_count": len(commands)}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_cli_prompt():
    """测试CLI提示符"""
    try:
        from cli.main import SuperAgentCLI
        cli = SuperAgentCLI()

        if not hasattr(cli, 'prompt'):
            return {"success": False, "error": "No prompt attribute"}

        if not cli.prompt:
            return {"success": False, "error": "Prompt is empty"}

        return {"success": True, "prompt": cli.prompt}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# 2. 对话层功能测试
# ============================================================================

def test_conversation_manager_import():
    """测试对话管理器导入"""
    try:
        from conversation.manager import ConversationManager
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_conversation_manager_init():
    """测试对话管理器初始化"""
    try:
        from conversation.manager import ConversationManager
        mgr = ConversationManager()

        # 检查关键属性
        if not hasattr(mgr, 'state'):
            return {"success": False, "error": "No state attribute"}

        if not hasattr(mgr, 'intent_recognizer'):
            return {"success": False, "error": "No intent_recognizer"}

        if not hasattr(mgr, 'conversation_history'):
            return {"success": False, "error": "No conversation_history"}

        return {"success": True, "initial_state": mgr.state}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_conversation_process_input():
    """测试对话输入处理"""
    try:
        from conversation.manager import ConversationManager
        mgr = ConversationManager()

        # 测试简单输入
        response = await mgr.process_input("创建一个博客系统")

        if not response:
            return {"success": False, "error": "No response returned"}

        return {"success": True, "response_type": response.type if hasattr(response, 'type') else 'unknown'}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_intent_recognizer_import():
    """测试意图识别器导入"""
    try:
        from conversation.intent_recognizer import IntentRecognizer
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# 3. 规划系统功能测试
# ============================================================================

def test_planner_import():
    """测试规划器导入"""
    try:
        from planning.planner import ProjectPlanner
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_planner_init():
    """测试规划器初始化"""
    try:
        from planning.planner import ProjectPlanner
        planner = ProjectPlanner()

        if not hasattr(planner, 'step_generator'):
            return {"success": False, "error": "No step_generator"}

        if not hasattr(planner, 'dependency_analyzer'):
            return {"success": False, "error": "No dependency_analyzer"}

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_step_generator_import():
    """测试步骤生成器导入"""
    try:
        from planning.step_generator import StepGenerator
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_dependency_analyzer_import():
    """测试依赖分析器导入"""
    try:
        from planning.dependency_analyzer import DependencyAnalyzer
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_planner_create_plan():
    """测试创建执行计划"""
    try:
        from planning.planner import ProjectPlanner
        planner = ProjectPlanner()

        plan = await planner.create_plan(
            user_input="创建一个简单的博客系统",
            context={}
        )

        if not plan:
            return {"success": False, "error": "No plan created"}

        return {"success": True, "has_steps": len(plan.steps) > 0 if hasattr(plan, 'steps') else False}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# 4. 编排系统功能测试
# ============================================================================

def test_orchestrator_import():
    """测试编排器导入"""
    try:
        from orchestration.orchestrator import Orchestrator
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_orchestrator_init():
    """测试编排器初始化"""
    try:
        from orchestration.orchestrator import Orchestrator
        from orchestration.models import OrchestrationConfig

        config = OrchestrationConfig()
        orch = Orchestrator(config)

        if not orch:
            return {"success": False, "error": "Failed to create orchestrator"}

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_task_scheduler_import():
    """测试任务调度器导入"""
    try:
        from orchestration.scheduler import TaskScheduler
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_agent_dispatcher_import():
    """测试Agent分发器导入"""
    try:
        from orchestration.agent_dispatcher import AgentDispatcher
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_review_orchestrator_import():
    """测试审查编排器导入"""
    try:
        from orchestration.review_orchestrator import ReviewOrchestrator
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# 5. Agent执行功能测试
# ============================================================================

def test_base_agent_import():
    """测试基础Agent导入"""
    try:
        from execution.base_agent import BaseAgent
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_coding_agent_import():
    """测试编码Agent导入"""
    try:
        from execution.coding_agent import CodingAgent
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_testing_agent_import():
    """测试测试Agent导入"""
    try:
        from execution.testing_agent import TestingAgent
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_documentation_agent_import():
    """测试文档Agent导入"""
    try:
        from execution.documentation_agent import DocumentationAgent
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_refactoring_agent_import():
    """测试重构Agent导入"""
    try:
        from execution.refactoring_agent import RefactoringAgent
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_agent_output_builder_import():
    """测试Agent输出构建器导入"""
    try:
        from execution.agent_output_builder import AgentOutputBuilder
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# 6. 记忆系统功能测试
# ============================================================================

def test_memory_manager_import():
    """测试记忆管理器导入"""
    try:
        from memory.memory_manager import MemoryManager
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_memory_manager_init():
    """测试记忆管理器初始化"""
    try:
        from memory.memory_manager import MemoryManager
        mgr = MemoryManager()

        if not hasattr(mgr, 'episodic_memory'):
            return {"success": False, "error": "No episodic_memory"}

        if not hasattr(mgr, 'semantic_memory'):
            return {"success": False, "error": "No semantic_memory"}

        if not hasattr(mgr, 'procedural_memory'):
            return {"success": False, "error": "No procedural_memory"}

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_memory_store_and_retrieve():
    """测试记忆存储和检索"""
    try:
        from memory.memory_manager import MemoryManager
        mgr = MemoryManager()

        # 存储记忆
        await mgr.store_episodic(
            content="测试记忆内容",
            metadata={"test": True}
        )

        # 检索记忆
        memories = await mgr.query_episodic("测试", limit=5)

        return {"success": True, "retrieved_count": len(memories)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# 7. 代码审查功能测试
# ============================================================================

def test_code_reviewer_import():
    """测试代码审查器导入"""
    try:
        from review.reviewer import CodeReviewer
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_ralph_wiggum_import():
    """测试Ralph Wiggum循环导入"""
    try:
        from review.ralph_wiggum import RalphWiggumLoop
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# 8. 错误恢复功能测试
# ============================================================================

def test_error_recovery_import():
    """测试错误恢复系统导入"""
    try:
        from orchestration.error_recovery import ErrorRecoverySystem
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_error_recovery_init():
    """测试错误恢复系统初始化"""
    try:
        from orchestration.error_recovery import ErrorRecoverySystem
        recovery = ErrorRecoverySystem()

        if not hasattr(recovery, 'error_history'):
            return {"success": False, "error": "No error_history"}

        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# 9. 安全功能测试
# ============================================================================

def test_security_import():
    """测试安全模块导入"""
    try:
        from common.security import SecurityValidator
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_path_traversal_protection():
    """测试路径穿越防护"""
    try:
        from common.security import SecurityValidator
        validator = SecurityValidator()

        # 测试恶意路径
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
            "C:/Windows/System32"
        ]

        blocked = 0
        for path in malicious_paths:
            try:
                is_safe = validator.validate_path(path)
                if not is_safe:
                    blocked += 1
            except:
                blocked += 1

        if blocked == len(malicious_paths):
            return {"success": True, "blocked_count": blocked}
        else:
            return {"success": False, "error": f"Only blocked {blocked}/{len(malicious_paths)} paths"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# 10. 性能功能测试
# ============================================================================

def test_token_monitor_import():
    """测试Token监控器导入"""
    try:
        from monitoring.token_monitor import TokenMonitor
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_smart_compressor_import():
    """测试智能压缩器导入"""
    try:
        from context.smart_compressor import SmartContextCompressor
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_compression_performance():
    """测试压缩性能"""
    try:
        from context.smart_compressor import SmartContextCompressor
        compressor = SmartContextCompressor()

        # 创建测试上下文
        test_context = {
            "conversation": [
                {"role": "user", "content": "用户消息1"},
                {"role": "assistant", "content": "助手回复1"},
                {"role": "user", "content": "用户消息2"},
                {"role": "assistant", "content": "助手回复2"},
            ] * 10  # 40条消息
        }

        start_time = time.time()
        compressed = await compressor.compress(test_context)
        duration = time.time() - start_time

        return {
            "success": True,
            "original_size": len(str(test_context)),
            "compressed_size": len(str(compressed)),
            "compression_time": round(duration, 3)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================================
# 主测试运行器
# ============================================================================

async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("SuperAgent 全面功能测试".center(80))
    print("="*80 + "\n")

    test_results["summary"]["start_time"] = datetime.now().isoformat()

    # 1. CLI交互功能测试
    print("\n【1/10】CLI交互功能测试")
    print("-" * 80)
    tests = [
        ("cli", "CLI模块导入", test_cli_import),
        ("cli", "CLI命令注册", test_cli_commands),
        ("cli", "CLI提示符", test_cli_prompt),
    ]
    for module, name, func in tests:
        result = run_test(module, name, func)
        update_results(result)

    # 2. 对话层功能测试
    print("\n【2/10】对话层功能测试")
    print("-" * 80)
    tests = [
        ("conversation", "对话管理器导入", test_conversation_manager_import),
        ("conversation", "对话管理器初始化", test_conversation_manager_init),
        ("conversation", "意图识别器导入", test_intent_recognizer_import),
    ]
    for module, name, func in tests:
        result = run_test(module, name, func)
        update_results(result)

    # 异步测试
    print("  [CONVERSATION] 运行: 对话输入处理...", end=" ")
    try:
        result = await test_conversation_process_input()
        if result.get("success"):
            print("✅ 通过")
            test_results["modules"]["conversation"]["tests"].append({
                "test_name": "对话输入处理",
                "status": "passed",
                "duration": 0,
                "details": result
            })
            test_results["modules"]["conversation"]["passed"] += 1
        else:
            print("❌ 失败")
            test_results["modules"]["conversation"]["tests"].append({
                "test_name": "对话输入处理",
                "status": "failed",
                "duration": 0,
                "error_message": result.get("error", "Unknown error")
            })
            test_results["modules"]["conversation"]["failed"] += 1
        test_results["modules"]["conversation"]["total"] += 1
        test_results["summary"]["total"] += 1
        test_results["summary"]["passed"] += 1 if result.get("success") else 0
        test_results["summary"]["failed"] += 0 if result.get("success") else 1
    except Exception as e:
        print(f"❌ 失败: {e}")
        test_results["modules"]["conversation"]["tests"].append({
            "test_name": "对话输入处理",
            "status": "failed",
            "duration": 0,
            "error_message": str(e)
        })
        test_results["modules"]["conversation"]["failed"] += 1
        test_results["modules"]["conversation"]["total"] += 1
        test_results["summary"]["total"] += 1
        test_results["summary"]["failed"] += 1

    # 3. 规划系统功能测试
    print("\n【3/10】规划系统功能测试")
    print("-" * 80)
    tests = [
        ("planning", "规划器导入", test_planner_import),
        ("planning", "规划器初始化", test_planner_init),
        ("planning", "步骤生成器导入", test_step_generator_import),
        ("planning", "依赖分析器导入", test_dependency_analyzer_import),
    ]
    for module, name, func in tests:
        result = run_test(module, name, func)
        update_results(result)

    # 异步测试
    print("  [PLANNING] 运行: 创建执行计划...", end=" ")
    try:
        result = await test_planner_create_plan()
        if result.get("success"):
            print("✅ 通过")
            test_results["modules"]["planning"]["tests"].append({
                "test_name": "创建执行计划",
                "status": "passed",
                "duration": 0,
                "details": result
            })
            test_results["modules"]["planning"]["passed"] += 1
        else:
            print("❌ 失败")
            test_results["modules"]["planning"]["tests"].append({
                "test_name": "创建执行计划",
                "status": "failed",
                "duration": 0,
                "error_message": result.get("error", "Unknown error")
            })
            test_results["modules"]["planning"]["failed"] += 1
        test_results["modules"]["planning"]["total"] += 1
        test_results["summary"]["total"] += 1
        test_results["summary"]["passed"] += 1 if result.get("success") else 0
        test_results["summary"]["failed"] += 0 if result.get("success") else 1
    except Exception as e:
        print(f"❌ 失败: {e}")
        test_results["modules"]["planning"]["tests"].append({
            "test_name": "创建执行计划",
            "status": "failed",
            "duration": 0,
            "error_message": str(e)
        })
        test_results["modules"]["planning"]["failed"] += 1
        test_results["modules"]["planning"]["total"] += 1
        test_results["summary"]["total"] += 1
        test_results["summary"]["failed"] += 1

    # 4. 编排系统功能测试
    print("\n【4/10】编排系统功能测试")
    print("-" * 80)
    tests = [
        ("orchestration", "编排器导入", test_orchestrator_import),
        ("orchestration", "编排器初始化", test_orchestrator_init),
        ("orchestration", "任务调度器导入", test_task_scheduler_import),
        ("orchestration", "Agent分发器导入", test_agent_dispatcher_import),
        ("orchestration", "审查编排器导入", test_review_orchestrator_import),
    ]
    for module, name, func in tests:
        result = run_test(module, name, func)
        update_results(result)

    # 5. Agent执行功能测试
    print("\n【5/10】Agent执行功能测试")
    print("-" * 80)
    tests = [
        ("execution", "基础Agent导入", test_base_agent_import),
        ("execution", "编码Agent导入", test_coding_agent_import),
        ("execution", "测试Agent导入", test_testing_agent_import),
        ("execution", "文档Agent导入", test_documentation_agent_import),
        ("execution", "重构Agent导入", test_refactoring_agent_import),
        ("execution", "Agent输出构建器导入", test_agent_output_builder_import),
    ]
    for module, name, func in tests:
        result = run_test(module, name, func)
        update_results(result)

    # 6. 记忆系统功能测试
    print("\n【6/10】记忆系统功能测试")
    print("-" * 80)
    tests = [
        ("memory", "记忆管理器导入", test_memory_manager_import),
        ("memory", "记忆管理器初始化", test_memory_manager_init),
    ]
    for module, name, func in tests:
        result = run_test(module, name, func)
        update_results(result)

    # 异步测试
    print("  [MEMORY] 运行: 记忆存储和检索...", end=" ")
    try:
        result = await test_memory_store_and_retrieve()
        if result.get("success"):
            print("✅ 通过")
            test_results["modules"]["memory"]["tests"].append({
                "test_name": "记忆存储和检索",
                "status": "passed",
                "duration": 0,
                "details": result
            })
            test_results["modules"]["memory"]["passed"] += 1
        else:
            print("❌ 失败")
            test_results["modules"]["memory"]["tests"].append({
                "test_name": "记忆存储和检索",
                "status": "failed",
                "duration": 0,
                "error_message": result.get("error", "Unknown error")
            })
            test_results["modules"]["memory"]["failed"] += 1
        test_results["modules"]["memory"]["total"] += 1
        test_results["summary"]["total"] += 1
        test_results["summary"]["passed"] += 1 if result.get("success") else 0
        test_results["summary"]["failed"] += 0 if result.get("success") else 1
    except Exception as e:
        print(f"❌ 失败: {e}")
        test_results["modules"]["memory"]["tests"].append({
            "test_name": "记忆存储和检索",
            "status": "failed",
            "duration": 0,
            "error_message": str(e)
        })
        test_results["modules"]["memory"]["failed"] += 1
        test_results["modules"]["memory"]["total"] += 1
        test_results["summary"]["total"] += 1
        test_results["summary"]["failed"] += 1

    # 7. 代码审查功能测试
    print("\n【7/10】代码审查功能测试")
    print("-" * 80)
    tests = [
        ("review", "代码审查器导入", test_code_reviewer_import),
        ("review", "Ralph Wiggum循环导入", test_ralph_wiggum_import),
    ]
    for module, name, func in tests:
        result = run_test(module, name, func)
        update_results(result)

    # 8. 错误恢复功能测试
    print("\n【8/10】错误恢复功能测试")
    print("-" * 80)
    tests = [
        ("error_recovery", "错误恢复系统导入", test_error_recovery_import),
        ("error_recovery", "错误恢复系统初始化", test_error_recovery_init),
    ]
    for module, name, func in tests:
        result = run_test(module, name, func)
        update_results(result)

    # 9. 安全功能测试
    print("\n【9/10】安全功能测试")
    print("-" * 80)
    tests = [
        ("security", "安全模块导入", test_security_import),
        ("security", "路径穿越防护", test_path_traversal_protection),
    ]
    for module, name, func in tests:
        result = run_test(module, name, func)
        update_results(result)

    # 10. 性能功能测试
    print("\n【10/10】性能功能测试")
    print("-" * 80)
    tests = [
        ("performance", "Token监控器导入", test_token_monitor_import),
        ("performance", "智能压缩器导入", test_smart_compressor_import),
    ]
    for module, name, func in tests:
        result = run_test(module, name, func)
        update_results(result)

    # 异步测试
    print("  [PERFORMANCE] 运行: 压缩性能测试...", end=" ")
    try:
        result = await test_compression_performance()
        if result.get("success"):
            print("✅ 通过")
            test_results["modules"]["performance"]["tests"].append({
                "test_name": "压缩性能测试",
                "status": "passed",
                "duration": 0,
                "details": result
            })
            test_results["modules"]["performance"]["passed"] += 1
        else:
            print("❌ 失败")
            test_results["modules"]["performance"]["tests"].append({
                "test_name": "压缩性能测试",
                "status": "failed",
                "duration": 0,
                "error_message": result.get("error", "Unknown error")
            })
            test_results["modules"]["performance"]["failed"] += 1
        test_results["modules"]["performance"]["total"] += 1
        test_results["summary"]["total"] += 1
        test_results["summary"]["passed"] += 1 if result.get("success") else 0
        test_results["summary"]["failed"] += 0 if result.get("success") else 1
    except Exception as e:
        print(f"❌ 失败: {e}")
        test_results["modules"]["performance"]["tests"].append({
            "test_name": "压缩性能测试",
            "status": "failed",
            "duration": 0,
            "error_message": str(e)
        })
        test_results["modules"]["performance"]["failed"] += 1
        test_results["modules"]["performance"]["total"] += 1
        test_results["summary"]["total"] += 1
        test_results["summary"]["failed"] += 1

    test_results["summary"]["end_time"] = datetime.now().isoformat()


def print_summary():
    """打印测试摘要"""
    print("\n" + "="*80)
    print("测试摘要".center(80))
    print("="*80 + "\n")

    summary = test_results["summary"]

    print(f"总测试数: {summary['total']}")
    print(f"通过: {summary['passed']} ✅")
    print(f"失败: {summary['failed']} ❌")
    print(f"通过率: {summary['passed']/summary['total']*100:.1f}%" if summary['total'] > 0 else "通过率: N/A")

    print("\n" + "-"*80)
    print("各模块统计")
    print("-"*80)

    for module_name, module_data in test_results["modules"].items():
        if module_data["total"] > 0:
            pass_rate = module_data["passed"] / module_data["total"] * 100
            print(f"\n{module_name.upper():15} | 总计: {module_data['total']:2} | 通过: {module_data['passed']:2} | 失败: {module_data['failed']:2} | 通过率: {pass_rate:5.1f}%")

    if summary["errors"]:
        print("\n" + "-"*80)
        print("失败详情")
        print("-"*80)
        for error in summary["errors"]:
            print(f"\n[{error['module'].upper()}] {error['test']}")
            print(f"  错误: {error['error']}")

    print("\n" + "="*80)


def save_report():
    """保存测试报告"""
    report_path = SUPERAGENT_ROOT / "test_reports" / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)

    print(f"\n📄 详细报告已保存至: {report_path}")

    # 保存Markdown版本
    md_path = report_path.with_suffix('.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# SuperAgent 全面功能测试报告\n\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        summary = test_results["summary"]
        f.write("## 测试摘要\n\n")
        f.write(f"- 总测试数: {summary['total']}\n")
        f.write(f"- 通过: {summary['passed']} ✅\n")
        f.write(f"- 失败: {summary['failed']} ❌\n")
        f.write(f"- 通过率: {summary['passed']/summary['total']*100:.1f}%\n\n" if summary['total'] > 0 else "- 通过率: N/A\n\n")

        f.write("## 各模块详情\n\n")
        for module_name, module_data in test_results["modules"].items():
            if module_data["total"] > 0:
                f.write(f"### {module_name.upper()}\n\n")
                pass_rate = module_data["passed"] / module_data["total"] * 100
                f.write(f"- 总计: {module_data['total']}\n")
                f.write(f"- 通过: {module_data['passed']}\n")
                f.write(f"- 失败: {module_data['failed']}\n")
                f.write(f"- 通过率: {pass_rate:.1f}%\n\n")

                for test in module_data["tests"]:
                    status_icon = "✅" if test["status"] == "passed" else "❌"
                    f.write(f"- {status_icon} {test['test_name']}")
                    if test["status"] == "failed":
                        f.write(f" - {test['error_message']}")
                    f.write("\n")

                f.write("\n")

        if summary["errors"]:
            f.write("## 失败详情\n\n")
            for error in summary["errors"]:
                f.write(f"### [{error['module'].upper()}] {error['test']}\n\n")
                f.write(f"**错误:** {error['error']}\n\n")

    print(f"📄 Markdown报告已保存至: {md_path}")


async def main():
    """主函数"""
    await run_all_tests()
    print_summary()
    save_report()


if __name__ == "__main__":
    asyncio.run(main())
