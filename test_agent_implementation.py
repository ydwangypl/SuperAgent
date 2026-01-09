#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Agent实现测试

验证Agent输出是否符合规范
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from execution.models import AgentContext, AgentConfig
from execution.coding_agent_v2 import CodingAgent
from execution.agent_output_builder import AgentOutputBuilder


async def test_coding_agent_output():
    """测试CodingAgent输出"""
    print("\n" + "="*70)
    print("测试: CodingAgent输出格式")
    print("="*70)

    # 创建Agent
    agent = CodingAgent()

    # 创建上下文
    context = AgentContext(
        project_root=Path("."),
        task_id="task-001",
        step_id="step-1"
    )

    # 测试用例1: 用户管理API
    print("\n📝 测试用例1: 用户管理API")
    print("-" * 70)

    task_input_1 = {
        "description": "开发用户管理API,支持用户注册和登录功能,使用JWT认证",
        "tech_stack": ["Python", "FastAPI", "PostgreSQL", "JWT"]
    }

    result_1 = await agent.execute(context, task_input_1)

    # 验证结果
    print(f"\n✅ 执行状态: {'成功' if result_1.success else '失败'}")
    print(f"   消息: {result_1.message}")
    print(f"   生成工件数: {len(result_1.artifacts)}")

    # 显示工件详情
    for i, artifact in enumerate(result_1.artifacts, 1):
        print(f"\n   工件{i}: {artifact.artifact_type}")
        print(f"   - 路径: {artifact.path}")
        if artifact.content:
            content_lines = artifact.content.split('\n')
            preview = '\n'.join(content_lines[:5])
            print(f"   - 内容预览:\n{preview}\n...")

    # 验证元数据
    print(f"\n📊 元数据:")
    for key, value in result_1.metadata.items():
        if key != "next_steps":
            print(f"   - {key}: {value}")

    # 验证下一步建议
    if "next_steps" in result_1.metadata:
        print(f"\n➡️  下一步建议:")
        for i, step in enumerate(result_1.metadata["next_steps"], 1):
            print(f"   {i}. {step}")

    # 验证思考过程
    print(f"\n🤔 思考过程:")
    for thought in agent.thoughts:
        print(f"   步骤{thought.step}: {thought.thought}")
        print(f"   动作: {thought.action}")

    # 测试用例2: 博客系统
    print("\n\n📝 测试用例2: 博客系统")
    print("-" * 70)

    task_input_2 = {
        "description": "开发博客系统,支持文章发布、评论和搜索功能",
        "tech_stack": ["Python", "FastAPI", "MongoDB", "Redis"]
    }

    result_2 = await agent.execute(context, task_input_2)

    print(f"\n✅ 执行状态: {'成功' if result_2.success else '失败'}")
    print(f"   消息: {result_2.message}")
    print(f"   生成工件数: {len(result_2.artifacts)}")

    # 显示工件详情
    for i, artifact in enumerate(result_2.artifacts, 1):
        print(f"\n   工件{i}: {artifact.artifact_type}")
        print(f"   - 路径: {artifact.path}")

    # 验证元数据
    print(f"\n📊 元数据:")
    print(f"   - 功能需求: {result_2.metadata.get('functional_requirements_count')}个")
    print(f"   - 文件数量: {result_2.metadata.get('file_count')}个")
    print(f"   - 估算代码行数: {result_2.metadata.get('estimated_code_lines')}行")

    return result_1.success and result_2.success


async def test_output_builder():
    """测试AgentOutputBuilder"""
    print("\n" + "="*70)
    print("测试: AgentOutputBuilder功能")
    print("="*70)

    # 测试需求文档生成
    print("\n📝 测试1: 需求文档生成")
    req_artifact = AgentOutputBuilder.create_requirements_artifact(
        feature_name="用户管理API",
        functional_requirements=[
            "用户注册功能",
            "用户登录功能",
            "密码加密存储"
        ],
        non_functional_requirements=[
            "API响应时间 < 200ms",
            "支持1000并发用户"
        ],
        technical_constraints=["使用FastAPI", "数据库使用PostgreSQL"]
    )

    print(f"✅ 工件类型: {req_artifact.artifact_type}")
    print(f"   路径: {req_artifact.path}")
    print(f"   内容长度: {len(req_artifact.content)}字符")
    print("\n内容预览:")
    print(req_artifact.content[:200] + "...")

    # 测试架构文档生成
    print("\n📝 测试2: 架构文档生成")
    arch_artifact = AgentOutputBuilder.create_architecture_artifact(
        feature_name="用户管理API",
        pattern="MVC",
        layers=["API层", "服务层", "数据访问层"],
        dependencies=["FastAPI", "SQLAlchemy", "Pydantic"],
        directory_structure="src/\n├── api/\n└── services/"
    )

    print(f"✅ 工件类型: {arch_artifact.artifact_type}")
    print(f"   路径: {arch_artifact.path}")
    print("\n内容预览:")
    print(arch_artifact.content[:200] + "...")

    # 测试API规范生成
    print("\n📝 测试3: API规范生成")
    api_artifact = AgentOutputBuilder.create_api_spec_artifact(
        feature_name="用户管理API",
        endpoints=[
            {
                "method": "POST",
                "path": "/api/v1/users/register",
                "description": "注册新用户",
                "request": {"email": "user@example.com", "password": "pass"},
                "response": {"user_id": "123", "email": "user@example.com"}
            }
        ]
    )

    print(f"✅ 工件类型: {api_artifact.artifact_type}")
    print(f"   路径: {api_artifact.path}")
    print("\n内容预览:")
    print(api_artifact.content[:300] + "...")

    return True


async def test_output_format_compliance():
    """测试输出格式符合性"""
    print("\n" + "="*70)
    print("测试: 输出格式符合性验证")
    print("="*70)

    agent = CodingAgent()
    context = AgentContext(
        project_root=Path("."),
        task_id="task-test",
        step_id="step-test"
    )

    task_input = {
        "description": "测试功能",
        "tech_stack": ["Python", "FastAPI"]
    }

    result = await agent.execute(context, task_input)

    # 验证清单
    checks = []

    # 1. 成功状态
    checks.append(("success字段", result.success is not None))

    # 2. agent_id
    checks.append(("agent_id字段", result.agent_id == "coding-agent"))

    # 3. task_id
    checks.append(("task_id字段", result.task_id == "task-test"))

    # 4. step_id
    checks.append(("step_id字段", result.step_id == "step-test"))

    # 5. artifacts非空
    checks.append(("artifacts非空", len(result.artifacts) > 0))

    # 6. 每个artifact包含必需字段
    for artifact in result.artifacts:
        checks.append((f"artifact包含artifact_id", artifact.artifact_id is not None))
        checks.append((f"artifact包含artifact_type", artifact.artifact_type is not None))
        checks.append((f"artifact包含path", artifact.path is not None))
        checks.append((f"artifact包含content", artifact.content is not None))

    # 7. metadata非空
    checks.append(("metadata非空", len(result.metadata) > 0))

    # 8. 内容是Markdown格式
    for artifact in result.artifacts:
        if artifact.content:
            checks.append((f"content是Markdown", artifact.content.strip().startswith('#')))

    # 输出验证结果
    print("\n📋 验证结果:")
    print("-" * 70)

    passed = 0
    failed = 0

    for check_name, check_result in checks:
        status = "✅" if check_result else "❌"
        print(f"  {status} {check_name}")
        if check_result:
            passed += 1
        else:
            failed += 1

    print(f"\n📊 统计:")
    print(f"   通过: {passed}/{passed + failed}")
    print(f"   失败: {failed}/{passed + failed}")
    print(f"   通过率: {passed * 100 // (passed + failed)}%")

    return failed == 0


async def main():
    """主测试函数"""
    print("\n" + "🚀" * 35)
    print("SuperAgent v3.0 - Agent实现测试")
    print("🚀" * 35)

    try:
        # 测试1: 输出构建器
        builder_ok = await test_output_builder()

        # 测试2: CodingAgent输出
        agent_ok = await test_coding_agent_output()

        # 测试3: 格式符合性
        compliance_ok = await test_output_format_compliance()

        # 总结
        print("\n" + "="*70)
        print("📊 测试总结")
        print("="*70)

        results = {
            "AgentOutputBuilder": builder_ok,
            "CodingAgent输出": agent_ok,
            "格式符合性": compliance_ok
        }

        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} - {test_name}")

        all_passed = all(results.values())

        if all_passed:
            print("\n🎉 所有测试通过!")
            print("✨ Agent实现符合规范!")
        else:
            print("\n⚠️  部分测试未通过,需要检查实现")

    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 设置Windows控制台UTF-8编码
    if sys.platform == "win32":
        import sys
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

    # 运行测试
    asyncio.run(main())
