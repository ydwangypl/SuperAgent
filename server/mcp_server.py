#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent MCP Server

提供 Model Context Protocol 接口，供 Claude Desktop 直接调用。

使用方式:
    1. 安装依赖: pip install mcp
    2. 配置 Claude Desktop:
       {
         "mcpServers": {
           "superagent": {
             "command": "python",
             "args": ["-m", "server.mcp_server"]
           }
         }
       }

功能:
- execute_task: 执行任务
- run_tests: 运行测试
- review_code: 代码审查
- analyze_requirement: 产品需求分析
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(PROJECT_ROOT))

# 检查 MCP 是否可用
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("Warning: MCP SDK not installed. Install with: pip install mcp")

from adapters.unified_adapter import UnifiedAdapter

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============ MCP Server ============

if MCP_AVAILABLE:
    app = Server("superagent-mcp")

    # 全局适配器
    _adapter: Optional[UnifiedAdapter] = None

    def get_adapter() -> UnifiedAdapter:
        """获取适配器实例"""
        global _adapter
        if _adapter is None:
            _adapter = UnifiedAdapter(project_root=PROJECT_ROOT)
        return _adapter

    # ============ MCP Tools ============

    @app.list_tools()
    async def list_tools() -> List[Tool]:
        """列出可用的工具"""
        return [
            Tool(
                name="execute_task",
                description=(
                    "执行一个任务，支持多种任务类型："
                    "coding(代码开发)、research(研究分析)、review(代码审查)、"
                    "planning(规划)、analysis(分析)"
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "task_type": {
                            "type": "string",
                            "enum": ["coding", "research", "review", "planning", "analysis"],
                            "description": "任务类型"
                        },
                        "description": {
                            "type": "string",
                            "description": "任务描述（自然语言）"
                        },
                        "config": {
                            "type": "object",
                            "description": "可选配置参数"
                        }
                    },
                    "required": ["task_type", "description"]
                }
            ),
            Tool(
                name="run_tests",
                description="运行测试用例，验证代码正确性",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "test_path": {
                            "type": "string",
                            "description": "测试路径（可选，默认运行所有测试）"
                        }
                    }
                }
            ),
            Tool(
                name="review_code",
                description="审查代码质量、安全性、性能等，返回改进建议",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "代码内容"
                        },
                        "language": {
                            "type": "string",
                            "description": "编程语言（默认 python）"
                        }
                    },
                    "required": ["content"]
                }
            ),
            Tool(
                name="analyze_requirement",
                description="分析产品需求，生成需求文档、用户画像、市场分析等",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "requirement": {
                            "type": "string",
                            "description": "产品需求描述"
                        }
                    },
                    "required": ["requirement"]
                }
            ),
            Tool(
                name="plan_project",
                description="规划项目结构、任务分解、时间估算",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "goal": {
                            "type": "string",
                            "description": "项目目标"
                        },
                        "constraints": {
                            "type": "string",
                            "description": "约束条件（可选）"
                        }
                    },
                    "required": ["goal"]
                }
            ),
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """调用工具"""
        try:
            adapter = get_adapter()
            logger.info(f"Calling tool: {name}")

            if name == "execute_task":
                result = await adapter.execute_task(
                    task_type=arguments["task_type"],
                    task_data={"description": arguments["description"]}
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
                )]

            elif name == "run_tests":
                test_path = arguments.get("test_path", "tests")
                result = await adapter.run_tests(test_path=test_path)
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]

            elif name == "review_code":
                result = await adapter.review_code(
                    artifact_data={"content": arguments["content"]},
                    config={"language": arguments.get("language", "python")}
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(result, ensure_ascii=False, indent=2)
                )]

            elif name == "analyze_requirement":
                # 调用 ProductAgent 进行需求分析
                result = await adapter.execute_task(
                    task_type="research",
                    task_data={
                        "description": f"产品需求分析: {arguments['requirement']}",
                        "agent": "ProductAgent"
                    }
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
                )]

            elif name == "plan_project":
                # 调用规划功能
                result = await adapter.execute_task(
                    task_type="planning",
                    task_data={
                        "description": f"项目规划: {arguments['goal']}",
                        "constraints": arguments.get("constraints", "")
                    }
                )
                return [TextContent(
                    type="text",
                    text=json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
                )]

            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]

        except Exception as e:
            logger.error(f"Tool call error: {e}", exc_info=True)
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

    # ============ 启动 ============

    async def main():
        """启动 MCP Server"""
        logger.info("Starting SuperAgent MCP Server...")
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    def run():
        """同步启动入口"""
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logger.info("MCP Server stopped")
        except Exception as e:
            logger.error(f"MCP Server error: {e}", exc_info=True)

else:
    # MCP SDK 不可用时的占位实现
    def list_tools():
        return []

    def call_tool(name, arguments):
        return [TextContent(
            type="text",
            text="Error: MCP SDK not installed. Install with: pip install mcp"
        )]

    def main():
        print("Error: MCP SDK not installed. Install with: pip install mcp")
        print("Then run: python -m server.mcp_server")

    def run():
        main()


# ============ 启动命令 ============

if __name__ == "__main__":
    if not MCP_AVAILABLE:
        print("=" * 60)
        print("  SuperAgent MCP Server")
        print("=" * 60)
        print("  Error: MCP SDK not installed")
        print()
        print("  Install with:")
        print("    pip install mcp")
        print()
        print("  Then configure in Claude Desktop:")
        print("    {")
        print('      "mcpServers": {')
        print('        "superagent": {')
        print('          "command": "python",')
        print('          "args": ["-m", "server.mcp_server"]')
        print("        }")
        print("      }")
        print("    }")
        print("=" * 60)
    else:
        print("=" * 60)
        print("  SuperAgent MCP Server v3.4.0")
        print("=" * 60)
        print("  Configure in Claude Desktop:")
        print("  {")
        print('    "mcpServers": {')
        print('      "superagent": {')
        print('        "command": "python",')
        print('        "args": ["-m", "server.mcp_server"]')
        print("      }")
        print("    }")
        print("  }")
        print("=" * 60)
        run()
