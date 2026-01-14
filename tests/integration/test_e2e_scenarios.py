import asyncio
import pytest
from pathlib import Path
from cli.main import SuperAgentCLI
from orchestration.orchestrator import Orchestrator

@pytest.mark.asyncio
async def test_e2e_planning_flow():
    """测试完整的从规划到准备执行的端到端流程"""
    project_root = Path("E:/SuperAgent").resolve()
    cli = SuperAgentCLI()
    
    # 1. 模拟用户输入 'plan'
    # 注意: do_plan 是同步方法，但内部可能调用异步逻辑
    # 在测试环境中，我们直接调用逻辑组件
    print("\n--- 模拟端到端规划流程 ---")
    
    # 模拟意图识别和计划生成
    requirement = "在 common/utils.py 中添加一个计算 MD5 的函数"
    intent = await cli.conversation_mgr.intent_recognizer.recognize(requirement)
    assert intent.type.value in ["add_feature", "coding", "general"]
    
    plan = await cli.planner.create_plan(requirement, context={})
    assert len(plan.steps) > 0
    print(f"✅ 计划生成成功，共 {len(plan.steps)} 步")

    # 2. 模拟编排器初始化与任务分发
    orchestrator = Orchestrator(project_root)
    assert orchestrator.project_root == project_root
    
    # 3. 模拟安全验证
    safe_path = orchestrator.project_root / "common" / "utils.py"
    # 这里我们只是验证路径是否合法，不真正写入文件
    from common.security import SecurityValidator
    validated_path = SecurityValidator.validate_path(Path("common/utils.py"), project_root)
    assert validated_path.name == "utils.py"
    
    print("✅ 端到端核心路径验证通过")

if __name__ == "__main__":
    asyncio.run(test_e2e_planning_flow())
