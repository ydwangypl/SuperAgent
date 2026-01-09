#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent v3.0 CLI主入口

命令行交互界面,支持自然语言编程
"""

import cmd
import sys
import os
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime

# Windows控制台UTF-8支持
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到Python路径
SUPERAGENT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(SUPERAGENT_ROOT))

# 导入对话管理器、规划器和编排器
from conversation.manager import ConversationManager
from planning.planner import ProjectPlanner
from orchestration.orchestrator import Orchestrator
from orchestration.models import OrchestrationConfig

# 导入配置管理
from config import load_config, save_config, SuperAgentConfig


class SuperAgentCLI(cmd.Cmd):
    """SuperAgent命令行界面"""

    # CLI配置
    prompt = "\033[1;32mSuperAgent>\033[0m "
    intro = """
    ╔═══════════════════════════════════════════════════════╗
    ║     SuperAgent v3.0 - 自然语言编程系统               ║
    ║                                                     ║
    ║     "通过对话,让编程变得简单"                       ║
    ╚═══════════════════════════════════════════════════════╝

    💡 提示: 直接用中文描述你想开发的项目即可开始
    📖 帮助: 输入 'help' 查看所有命令
    🚪 退出: 输入 'quit' 或 'exit'
    """

    def __init__(self):
        super().__init__()
        self.project_root = SUPERAGENT_ROOT
        self.current_project = None

        # 初始化对话管理器
        self.conversation_mgr = ConversationManager()

        # 初始化规划器
        self.planner = ProjectPlanner()

        # 初始化编排器
        self.orchestrator = None
        self.current_plan = None
        self.last_result = None

    # ========== 内置命令 ==========

    def do_status(self, args: str):
        """查看当前状态 - status [options]

        选项:
          detail  - 显示详细信息
        """
        if self.current_project:
            print(f"\n当前项目: {self.current_project}")
            print(f"项目路径: {self.project_root}")
        else:
            print("\n当前状态: 未加载项目")
            print(f"工作目录: {self.project_root}")

        print(f"\nSuperAgent版本: 3.0.0-dev")
        print(f"Python版本: {sys.version.split()[0]}")

    def do_doctor(self, args: str):
        """环境自检 - doctor
        检查 Git 环境、配置文件、目录权限、记忆系统及依赖项
        """
        print("\n" + "="*60)
        print("  SuperAgent 环境诊断 (Doctor)")
        print("="*60)
        
        # 1. 检查 Python 版本与核心依赖
        py_version = sys.version_info
        status_py = "✅" if py_version.major >= 3 and py_version.minor >= 10 else "❌"
        print(f"{status_py} Python 版本: {py_version.major}.{py_version.minor}.{py_version.micro} (要求 3.10+)")

        dependencies = ["aiofiles", "pytest", "yaml", "jinja2", "pydantic"]
        missing_deps = []
        for dep in dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(dep)
        
        status_deps = "✅" if not missing_deps else "❌"
        deps_msg = "已全部安装" if not missing_deps else f"缺少: {', '.join(missing_deps)}"
        print(f"{status_deps} 核心依赖: {deps_msg}")

        # 2. 检查 Git 与 Worktree 支持
        import subprocess
        try:
            git_ver = subprocess.check_output(["git", "--version"], stderr=subprocess.STDOUT).decode().strip()
            print(f"✅ Git 环境: {git_ver}")
            
            # 检查是否在 git 仓库中
            result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], 
                                   capture_output=True, text=True)
            if result.returncode == 0 and "true" in result.stdout.lower():
                print("✅ Git 仓库: 已检测到有效仓库")
            else:
                print("⚠️  Git 仓库: 当前目录不是 Git 仓库 (Worktree 功能将受限)")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Git 环境: 未找到 git 命令，Worktree 功能将无法使用")

        # 3. 检查目录权限与记忆系统
        root = Path(self.project_root)
        status_root = "✅" if os.access(root, os.W_OK) else "❌"
        print(f"{status_root} 项目根目录: {root} ({'可写' if os.access(root, os.W_OK) else '不可写'})")

        memory_dir = root / ".superagent" / "memory"
        if memory_dir.exists():
            status_mem = "✅" if os.access(memory_dir, os.W_OK) else "❌"
            print(f"{status_mem} 记忆系统目录: {memory_dir} ({'正常' if os.access(memory_dir, os.W_OK) else '不可写'})")
        else:
            print("⚠️  记忆系统目录: 未创建 (将在首次启动时初始化)")

        # 4. 检查配置文件
        config_path = root / ".superagent" / "config.json"
        if config_path.exists():
            print(f"✅ 配置文件: 已找到 {config_path}")
        else:
            print(f"⚠️  配置文件: 未找到 (提示: 输入 'config init' 可创建默认配置)")

        # 5. 检查 LLM 环境变量
        api_keys = {
            "OPENAI_API_KEY": "OpenAI",
            "ANTHROPIC_API_KEY": "Anthropic",
            "GOOGLE_API_KEY": "Google Gemini",
            "DEEPSEEK_API_KEY": "DeepSeek"
        }
        found_keys = [label for key, label in api_keys.items() if os.environ.get(key)]
        
        if found_keys:
            print(f"✅ LLM 配置: 已检测到 {', '.join(found_keys)}")
        else:
            print("⚠️  LLM 配置: 未检测到 API 密钥环境变量")
            print("   (提示: 请在系统环境变量或 .env 文件中设置 OPENAI_API_KEY 等)")

        print("\n诊断完成！" + "="*50)

    def do_plan(self, args: str):
        """创建项目计划 - plan <需求描述>"""
        if not args.strip():
            print("\n❌ 请提供需求描述")
            print("   用法: plan <需求描述>")
            return

        print(f"\n🚀 正在分析需求: {args[:50]}...")
        
        try:
            # 1. 意图识别
            import asyncio
            intent = asyncio.run(self.conversation_mgr.intent_recognizer.recognize(args))
            print(f"✅ 识别意图: {intent.type.value} (置信度: {intent.confidence:.2f})")

            # 2. 生成计划
            plan = asyncio.run(self.planner.create_plan(args, intent=intent))
            self.current_plan = plan
            
            print(f"✅ 计划生成成功: 共 {len(plan.steps)} 个步骤")
            print("\n" + "="*60)
            print(self.planner.format_plan(plan))
            print("="*60)
            print("\n💡 提示: 输入 'execute' 开始执行此计划")
            
        except Exception as e:
            print(f"❌ 计划生成失败: {e}")

    def do_clear(self, __args: str):
        """清除屏幕 - clear"""
        os.system('clear' if os.name == 'posix' else 'cls')

    def do_pwd(self, __args: str):
        """显示当前工作目录 - pwd"""
        print(f"\n{os.getcwd()}")

    def do_cd(self, args: str):
        """切换目录 (安全增强版) - cd <path>"""
        if not args.strip():
            print("❌ 请指定目录路径")
            return

        from common.security import validate_path, SecurityError
        
        try:
            # 1. 解析目标路径
            target_path = Path(args.strip())
            
            # 2. 安全验证：只允许在项目根目录下切换
            # 如果是绝对路径，验证其是否在 SUPERAGENT_ROOT 下
            # 如果是相对路径，验证解析后的路径是否在 SUPERAGENT_ROOT 下
            validated_path = validate_path(target_path, SUPERAGENT_ROOT)
            
            # 3. 执行切换
            os.chdir(str(validated_path))
            print(f"✓ 已切换到: {os.getcwd()}")
        except SecurityError as e:
            print(f"❌ 安全策略拒绝: {e}")
        except FileNotFoundError:
            print(f"❌ 目录不存在: {args}")
        except PermissionError:
            print(f"❌ 权限不足: 无法进入目录 {args}")
        except NotADirectoryError:
            print(f"❌ 不是一个目录: {args}")
        except OSError as e:
            print(f"❌ 切换失败 (系统错误): {e}")
        except Exception as e:
            print(f"❌ 切换失败 (未知错误): {e}")

    def do_ls(self, args: str):
        """列出目录内容 (安全增强版) - ls [path]"""
        path_str = args.strip() or "."
        
        from common.security import validate_path, SecurityError
        
        try:
            # 1. 安全验证
            target_path = Path(path_str)
            validated_path = validate_path(target_path, SUPERAGENT_ROOT)
            
            # 2. 列出内容
            files = os.listdir(str(validated_path))
            print(f"\n📁 {path_str}/")
            for f in sorted(files):
                f_path = validated_path / f
                icon = "📁" if f_path.is_dir() else "📄"
                print(f"  {icon} {f}")
        except SecurityError as e:
            print(f"❌ 安全策略拒绝: {e}")
        except FileNotFoundError:
            print(f"❌ 路径不存在: {path_str}")
        except PermissionError:
            print(f"❌ 权限不足: 无法读取目录 {path_str}")
        except Exception as e:
            print(f"❌ 列出目录失败: {e}")

    def do_execute(self, args: str):
        """执行当前计划 - execute [options]

        选项:
          force   - 强制重新执行
          plan    - 只显示计划,不执行
        """
        if not self.current_plan:
            print("\n❌ 没有可执行的计划")
            print("   请先输入项目需求生成计划")
            return

        args_list = args.strip().split()
        show_only = "plan" in args_list

        if show_only:
            # 只显示计划
            print("\n" + "="*60)
            print("  当前执行计划")
            print("="*60)
            print(self.planner.format_plan(self.current_plan))
            return

        # 执行计划
        print("\n" + "="*60)
        print("  开始执行项目计划")
        print("="*60)

        try:
            # 初始化编排器
            if not self.orchestrator:
                # 加载全局配置并转换为编排配置
                global_config = load_config(project_root=self.project_root)
                config = OrchestrationConfig(
                    max_parallel_tasks=global_config.orchestration.max_parallel_tasks,
                    enable_parallel_execution=global_config.orchestration.enable_parallel_execution,
                    enable_code_review=global_config.code_review.enabled,
                    min_overall_score=global_config.code_review.min_overall_score,
                    max_critical_issues=global_config.code_review.max_critical_issues,
                    enable_style_check=global_config.code_review.enable_style_check,
                    enable_security_check=global_config.code_review.enable_security_check,
                    enable_performance_check=global_config.code_review.enable_performance_check,
                    enable_best_practices=global_config.code_review.enable_best_practices,
                    enable_ralph_wiggum=global_config.code_review.enable_ralph_wiggum
                )
                self.orchestrator = Orchestrator(self.project_root, config, global_config)

            # 执行
            print(f"\n项目ID: {self.orchestrator.state.project_id}")
            print(f"任务数量: {len(self.current_plan.steps)}")
            print("\n正在执行 (按 Ctrl+C 中断)... ")

            import time
            start_time = time.time()

            try:
                self.last_result = asyncio.run(
                    self.orchestrator.execute_plan(self.current_plan)
                )
            except KeyboardInterrupt:
                print("\n\n⚠️  用户中断执行")
                # 这里可以添加一些清理逻辑
                return

            duration = time.time() - start_time

            # 显示结果
            print("\n" + "="*60)
            print("  执行完成")
            print("="*60)

            print(f"\n状态: {'✅ 成功' if self.last_result.success else '❌ 失败'}")
            print(f"完成: {self.last_result.completed_tasks}/{self.last_result.total_tasks}")
            print(f"失败: {self.last_result.failed_tasks}")
            print(f"耗时: {duration:.2f}秒")
            print(f"成功率: {self.last_result.success_rate * 100:.1f}%")

            if self.last_result.errors:
                print("\n错误信息:")
                for error in self.last_result.errors:
                    print(f"  - {error}")

        except (OSError, ImportError) as e:
            print(f"\n❌ 环境或系统错误: {e}")
        except ValueError as e:
            print(f"\n❌ 参数错误: {e}")
        except Exception as e:
            print(f"❌ 执行失败 (未知错误 - {type(e).__name__}): {e}")
            import traceback
            traceback.print_exc()

    def do_memory(self, args: str):
        """记忆管理命令 - memory <subcommand> [options]

        子命令:
          stats     - 查看记忆统计
          query     - 查询记忆内容
          episodic  - 查看情节记忆
          semantic  - 查看语义记忆
          procedural- 查看程序记忆
          export    - 导出记忆数据
          continuity- 显示 CONTINUITY.md

        示例:
          memory stats              # 查看统计
          memory query error        # 查询包含"error"的记忆
          memory episodic 10        # 查看最近10条情节记忆
          memory semantic arch      # 查询包含"arch"的语义记忆
          memory export backup.json # 导出到文件
        """
        if not self.orchestrator or not self.orchestrator.memory_manager:
            print("\n❌ 记忆系统未初始化")
            print("   请先执行一个计划以启用记忆系统")
            return

        args_list = args.strip().split()
        if not args_list:
            print("\n❌ 请指定子命令")
            print("   使用 'help memory' 查看帮助")
            return

        subcommand = args_list[0]

        try:
            if subcommand == "stats":
                self._memory_stats()
            elif subcommand == "query":
                keyword = args_list[1] if len(args_list) > 1 else ""
                self._memory_query(keyword)
            elif subcommand == "episodic":
                limit = int(args_list[1]) if len(args_list) > 1 and args_list[1].isdigit() else 10
                self._memory_episodic(limit)
            elif subcommand == "semantic":
                category = args_list[1] if len(args_list) > 1 else None
                self._memory_semantic(category)
            elif subcommand == "procedural":
                category = args_list[1] if len(args_list) > 1 else None
                self._memory_procedural(category)
            elif subcommand == "export":
                filename = args_list[1] if len(args_list) > 1 else "memory_export.json"
                self._memory_export(filename)
            elif subcommand == "continuity":
                self._memory_continuity()
            else:
                print(f"\n❌ 未知子命令: {subcommand}")
                print("   使用 'help memory' 查看帮助")
        except ValueError as e:
            print(f"\n❌ 参数格式错误: {e}")
        except (OSError, IOError) as e:
            print(f"\n❌ 文件操作失败: {e}")
        except Exception as e:
            print(f"\n❌ 记忆操作失败 (未知错误 - {type(e).__name__}): {e}")
            import traceback
            traceback.print_exc()

    def _memory_stats(self):
        """显示记忆统计"""
        stats = self.orchestrator.memory_manager.get_statistics()

        print("\n" + "="*60)
        print("  记忆系统统计")
        print("="*60)

        print(f"\n总记忆条目: {stats['total']}")
        print(f"  - 情节记忆: {stats['episodic']} 条")
        print(f"  - 语义记忆: {stats['semantic']} 条")
        print(f"  - 程序记忆: {stats['procedural']} 条")

        if stats.get('categories'):
            print(f"\n分类统计:")
            for category, count in stats['categories'].items():
                print(f"  - {category}: {count} 条")

        if stats.get('tags'):
            print(f"\n热门标签:")
            for tag, count in sorted(stats['tags'].items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  - {tag}: {count} 次")

    def _memory_query(self, keyword: str):
        """查询记忆"""
        print("\n正在查询记忆...")

        result = asyncio.run(
            self.orchestrator.memory_manager.query_relevant_memory(
                task=keyword or "all",
                agent_type=None
            )
        )

        print("\n" + "="*60)
        print("  查询结果")
        print("="*60)

        if result.get('mistakes'):
            print(f"\n错误教训 ({len(result['mistakes'])} 条):")
            for mistake in result['mistakes'][:5]:
                print(f"\n  - {mistake.get('error_type', 'Unknown')}")
                print(f"    上下文: {mistake.get('context', '')}")
                print(f"    经验: {mistake.get('learning', '')}")

        if result.get('best_practices'):
            print(f"\n最佳实践 ({len(result['best_practices'])} 条):")
            for practice in result['best_practices'][:5]:
                print(f"\n  - {practice.get('content', '')[:80]}...")

        if result.get('architecture_decisions'):
            print(f"\n架构决策 ({len(result['architecture_decisions'])} 条):")
            for decision in result['architecture_decisions'][:5]:
                print(f"\n  - {decision.get('category', '')}: {decision.get('content', '')[:60]}...")

        if not any(result.values()):
            print("\n未找到相关记忆")

    def _memory_episodic(self, limit: int):
        """显示情节记忆"""
        memories = asyncio.run(
            self.orchestrator.memory_manager.get_episodic_memories(limit=limit)
        )

        print("\n" + "="*60)
        print(f"  最近 {len(memories)} 条情节记忆")
        print("="*60)

        for i, mem in enumerate(memories, 1):
            print(f"\n{i}. [{mem.get('timestamp', '')}] {mem.get('task_id', '')}")
            print(f"   状态: {mem.get('metadata', {}).get('status', '')}")
            print(f"   事件: {mem.get('event', '')[:100]}...")

    def _memory_semantic(self, category: Optional[str]):
        """显示语义记忆"""
        memories = asyncio.run(
            self.orchestrator.memory_manager.query_semantic_memory(category=category)
        )

        print("\n" + "="*60)
        print(f"  语义记忆 ({category or '全部'} {len(memories)} 条)")
        print("="*60)

        for i, mem in enumerate(memories[:10], 1):
            print(f"\n{i}. [{mem.get('timestamp', '')}] {mem.get('category', '')}")
            tags = ", ".join(mem.get('tags', []))
            if tags:
                print(f"   标签: {tags}")
            print(f"   内容: {mem.get('knowledge', '')[:100]}...")

    def _memory_procedural(self, category: Optional[str]):
        """显示程序记忆"""
        memories = asyncio.run(
            self.orchestrator.memory_manager.get_procedural_memories(category=category)
        )

        print("\n" + "="*60)
        print(f"  程序记忆 ({category or '全部'} {len(memories)} 条)")
        print("="*60)

        for i, mem in enumerate(memories[:10], 1):
            print(f"\n{i}. [{mem.get('timestamp', '')}] {mem.get('category', '')}")
            print(f"   实践: {mem.get('practice', '')[:100]}...")

    def _memory_export(self, filename: str):
        """导出记忆数据"""
        import json

        # 收集所有记忆
        episodic = asyncio.run(self.orchestrator.memory_manager.get_episodic_memories(limit=1000))
        semantic = asyncio.run(self.orchestrator.memory_manager.query_semantic_memory())
        procedural = asyncio.run(self.orchestrator.memory_manager.get_procedural_memories())

        export_data = {
            "export_time": str(datetime.now()),
            "episodic_count": len(episodic),
            "semantic_count": len(semantic),
            "procedural_count": len(procedural),
            "episodic": episodic,
            "semantic": semantic,
            "procedural": procedural
        }

        output_path = self.project_root / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"\n✓ 记忆已导出到: {output_path}")
        print(f"  总计: {len(episodic) + len(semantic) + len(procedural)} 条")

    def _memory_continuity(self):
        """显示 CONTINUITY.md"""
        continuity_file = self.project_root / ".superagent" / "memory" / "CONTINUITY.md"

        if not continuity_file.exists():
            print("\n❌ CONTINUITY.md 文件不存在")
            return

        with open(continuity_file, 'r', encoding='utf-8') as f:
            content = f.read()

        print("\n" + content)

    def do_review(self, args: str):
        """代码审查命令 - review <subcommand> [options]

        子命令:
          status    - 查看审查配置状态
          run       - 手动触发代码审查
          history   - 查看审查历史(如果有的话)

        示例:
          review status           # 查看配置
          review run              # 运行审查
        """
        if not self.orchestrator or not self.orchestrator.code_reviewer:
            print("\n❌ 代码审查系统未启用")
            print("   请在配置中启用代码审查功能")
            return

        args_list = args.strip().split()
        if not args_list:
            print("\n❌ 请指定子命令")
            print("   使用 'help review' 查看帮助")
            return

        subcommand = args_list[0]

        try:
            if subcommand == "status":
                self._review_status()
            elif subcommand == "run":
                print("\n⚠️ 代码审查通常在计划执行后自动运行")
                print("   如需手动审查,请先执行计划")
            elif subcommand == "history":
                if self.last_result and self.last_result.code_review_summary:
                    self._display_review_summary(self.last_result.code_review_summary)
                else:
                    print("\n❌ 没有审查历史")
            else:
                print(f"\n❌ 未知子命令: {subcommand}")
        except ValueError as e:
            print(f"\n❌ 参数错误: {e}")
        except Exception as e:
            print(f"\n❌ 代码审查操作失败 (未知错误 - {type(e).__name__}): {e}")
            import traceback
            traceback.print_exc()

    def _review_status(self):
        """显示审查配置状态"""
        config = self.orchestrator.config

        print("\n" + "="*60)
        print("  代码审查配置")
        print("="*60)

        status = "✅ 已启用" if config.enable_code_review else "❌ 未启用"
        print(f"\n状态: {status}")
        print(f"最低评分: {config.min_overall_score}")
        print(f"最多严重问题: {config.max_critical_issues}")

        print(f"\n检查项:")
        print(f"  风格检查: {'✅' if config.enable_style_check else '❌'}")
        print(f"  安全检查: {'✅' if config.enable_security_check else '❌'}")
        print(f"  性能检查: {'✅' if config.enable_performance_check else '❌'}")
        print(f"  最佳实践: {'✅' if config.enable_best_practices else '❌'}")
        print(f"  Ralph Wiggum: {'✅' if config.enable_ralph_wiggum else '❌'}")

    def _display_review_summary(self, review_summary):
        """显示审查摘要"""
        print("\n" + "="*60)
        print("  代码审查结果")
        print("="*60)

        if review_summary['status'] == 'no_code':
            print(f"\n{review_summary['message']}")
        elif review_summary['status'] == 'error':
            print(f"\n审查失败: {review_summary.get('error', '未知错误')}")
        elif review_summary['status'] == 'completed':
            score = review_summary['overall_score']
            status_icon = "[OK]" if review_summary['meets_threshold'] else "[WARN]"

            print(f"\n{status_icon} 综合评分: {score:.1f}/100")
            print(f"   审查文件: {review_summary['file_count']}个")
            print(f"   代码行数: {review_summary['total_lines']}行")

            print(f"\n   问题统计:")
            print(f"   总计: {review_summary['total_issues']}个")
            print(f"   - 严重: {review_summary['critical_count']}个")
            print(f"   - 主要: {review_summary['major_count']}个")
            print(f"   - 轻微: {review_summary['minor_count']}个")

            if review_summary['recommendations']:
                print(f"\n   改进建议:")
                for rec in review_summary['recommendations']:
                    print(f"   - {rec}")

            print(f"\n   审查总结:")
            for line in review_summary['summary'].split('\n'):
                print(f"   {line}")

            if not review_summary['meets_threshold']:
                print(f"\n   [WARN] 代码质量未达到要求")

    def do_result(self, args: str):
        """查看上次执行结果 - result [options]

        选项:
          detail  - 显示详细信息
          tasks   - 显示任务详情
        """
        if not self.last_result:
            print("\n❌ 没有执行结果")
            print("   请先使用 'execute' 命令执行计划")
            return

        args_list = args.strip().split()
        show_detail = "detail" in args_list
        show_tasks = "tasks" in args_list

        print("\n" + "="*60)
        print("  执行结果摘要")
        print("="*60)

        print(f"\n项目ID: {self.last_result.project_id}")
        print(f"状态: {'✅ 成功' if self.last_result.success else '❌ 失败'}")
        print(f"总任务: {self.last_result.total_tasks}")
        print(f"已完成: {self.last_result.completed_tasks}")
        print(f"失败: {self.last_result.failed_tasks}")
        print(f"跳过: {self.last_result.skipped_tasks}")
        print(f"耗时: {self.last_result.duration_seconds}秒")
        print(f"成功率: {self.last_result.success_rate * 100:.1f}%")

        if show_tasks:
            print("\n" + "-"*60)
            print("  任务执行详情")
            print("-"*60)

            for task in self.last_result.task_executions:
                status_symbol = {
                    "completed": "✅",
                    "failed": "❌",
                    "skipped": "⏭️",
                    "pending": "⏳"
                }.get(task.status.value, "❓")

                duration = ""
                if task.started_at and task.completed_at:
                    duration = f" ({(task.completed_at - task.started_at).total_seconds():.2f}s)"

                print(f"\n{status_symbol} {task.task_id}: {task.status.value.upper()}{duration}")

                if task.assignment:
                    print(f"   Agent: {task.assignment.agent_type}")

                if show_detail and task.result:
                    print(f"   结果: {task.result}")

                if task.error:
                    print(f"   错误: {task.error}")

        if show_detail and self.orchestrator:
            stats = self.orchestrator.get_task_statistics()

            print("\n" + "-"*60)
            print("  Agent统计")
            print("-"*60)

            for agent_type, agent_stats in stats['agent_stats'].items():
                print(f"\n{agent_type}:")
                print(f"  负载: {agent_stats['current_load']}/{agent_stats['max_concurrent']}")
                print(f"  利用率: {agent_stats['utilization']}")
                print(f"  执行次数: {agent_stats['total_executions']}")

            # 显示记忆统计
            if 'memory_stats' in stats:
                memory_stats = stats['memory_stats']
                print("\n" + "-"*60)
                print("  记忆系统统计")
                print("-"*60)
                print(f"\n总记忆: {memory_stats['total']}")
                print(f"  - 情节: {memory_stats['episodic']}")
                print(f"  - 语义: {memory_stats['semantic']}")
                print(f"  - 程序: {memory_stats['procedural']}")

        # 显示代码审查结果
        if self.last_result.code_review_summary:
            print("\n" + "-"*60)
            print("  代码审查结果")
            print("-"*60)

            review = self.last_result.code_review_summary

            if review['status'] == 'no_code':
                print(f"\n{review['message']}")
            elif review['status'] == 'error':
                print(f"\n审查失败: {review.get('error', '未知错误')}")
            elif review['status'] == 'completed':
                # 质量评分
                score = review['overall_score']
                status_icon = "[OK]" if review['meets_threshold'] else "[WARN]"

                print(f"\n{status_icon} 综合评分: {score:.1f}/100")
                print(f"   审查文件: {review['file_count']}个")
                print(f"   代码行数: {review['total_lines']}行")

                # 问题统计
                print(f"\n   问题统计:")
                print(f"   总计: {review['total_issues']}个")
                print(f"   - 严重: {review['critical_count']}个")
                print(f"   - 主要: {review['major_count']}个")
                print(f"   - 轻微: {review['minor_count']}个")

                # 改进建议
                if review['recommendations']:
                    print(f"\n   改进建议:")
                    for rec in review['recommendations']:
                        print(f"   - {rec}")

                # 详细总结
                print(f"\n   审查总结:")
                for line in review['summary'].split('\n'):
                    print(f"   {line}")

                # 质量门禁提示
                if not review['meets_threshold']:
                    print(f"\n   [WARN] 代码质量未达到要求 (需要 >= {self.orchestrator.config.min_overall_score if self.orchestrator else 70:.0f}分)")
            else:
                print(f"\n未知状态: {review['status']}")

    def do_config(self, args: str):
        """配置管理命令 - config <subcommand> [options]

        子命令:
          show     - 显示当前配置
          init     - 初始化配置文件
          edit     - 编辑配置
          export   - 导出配置

        示例:
          config show              # 显示配置
          config init              # 初始化配置
          config export config.json # 导出配置
        """
        args_list = args.strip().split()
        if not args_list:
            print("\n❌ 请指定子命令")
            print("   使用 'help config' 查看帮助")
            return

        subcommand = args_list[0]

        try:
            if subcommand == "show":
                self._config_show()
            elif subcommand == "init":
                self._config_init()
            elif subcommand == "edit":
                self._config_edit()
            elif subcommand == "export":
                filename = args_list[1] if len(args_list) > 1 else "config.json"
                self._config_export(filename)
            else:
                print(f"\n❌ 未知子命令: {subcommand}")
        except (OSError, IOError) as e:
            print(f"\n❌ 配置文件操作失败: {e}")
        except Exception as e:
            print(f"\n❌ 配置操作失败 (未知错误): {e}")
            import traceback
            traceback.print_exc()

    def _config_show(self):
        """显示当前配置"""
        try:
            config = load_config(project_root=self.project_root)

            print("\n" + "="*60)
            print("  SuperAgent v3.0 配置")
            print("="*60)

            print(f"\n项目根目录: {config.project_root}")

            print("\n" + "-"*60)
            print("  记忆系统配置")
            print("-"*60)
            print(f"启用: {config.memory.enabled}")
            print(f"保留天数: {config.memory.retention_days if config.memory.retention_days > 0 else '永久'}")
            print(f"最大情节记忆: {config.memory.max_episodic_memories}")
            print(f"最大语义记忆: {config.memory.max_semantic_memories}")

            print("\n" + "-"*60)
            print("  代码审查配置")
            print("-"*60)
            print(f"启用: {config.code_review.enabled}")
            print(f"最低评分: {config.code_review.min_overall_score}")
            print(f"最多严重问题: {config.code_review.max_critical_issues}")

            print("\n" + "-"*60)
            print("  编排配置")
            print("-"*60)
            print(f"并行执行: {config.orchestration.enable_parallel_execution}")
            print(f"最大并行任务: {config.orchestration.max_parallel_tasks}")
            print(f"Agent超时: {config.orchestration.agent_timeout_seconds}秒")

            print("\n" + "-"*60)
            print("  日志配置")
            print("-"*60)
            print(f"级别: {config.logging.level}")
            print(f"文件输出: {config.logging.file_output}")

        except FileNotFoundError:
            print(f"\n❌ 配置文件不存在")
        except PermissionError:
            print(f"\n❌ 无权读取配置文件")
        except Exception as e:
            print(f"\n❌ 加载配置失败 (未知错误): {e}")

    def _config_init(self):
        """初始化配置文件"""
        from config.settings import get_default_config_path

        config_path = get_default_config_path(self.project_root)

        if config_path.exists():
            print(f"\n⚠️  配置文件已存在: {config_path}")
            print("   使用 'config edit' 编辑现有配置")
            return

        # 创建默认配置
        config = SuperAgentConfig(project_root=self.project_root)

        # 保存配置
        save_config(config, config_path)

        print(f"\n✓ 配置文件已创建: {config_path}")
        print("\n提示:")
        print("  - 使用 'config show' 查看配置")
        print("  - 使用 'config edit' 编辑配置")

    def _config_edit(self):
        """编辑配置提示"""
        print("\n配置编辑:")
        print("  方法1: 使用 'config edit' 命令(交互式)")
        print("  方法2: 直接编辑 .superagent/config.json 文件")
        print("\n配置文件位置: .superagent/config.json")

    def _config_export(self, filename: str):
        """导出配置"""
        import json

        try:
            config = load_config(project_root=self.project_root)
            output_path = self.project_root / filename

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)

            print(f"\n✓ 配置已导出到: {output_path}")
        except PermissionError:
            print(f"\n❌ 权限不足: 无法写入文件 {filename}")
        except OSError as e:
            print(f"\n❌ 导出失败 (系统错误): {e}")
        except Exception as e:
            print(f"\n❌ 导出失败 (未知错误): {e}")

    def do_help(self, args: str):
        """显示帮助信息 - help [command]"""
        if args.strip():
            # 显示特定命令的帮助
            super().do_help(args)
        else:
            # 显示概览帮助
            print("\n" + "="*60)
            print("  SuperAgent v3.0 命令帮助")
            print("="*60)

            print("\n内置命令:")
            print("  status     - 查看当前状态")
            print("  clear      - 清除屏幕")
            print("  pwd        - 显示当前目录")
            print("  cd <path>  - 切换目录")
            print("  ls [path]  - 列出目录内容")
            print("  help       - 显示帮助")
            print("  quit/exit  - 退出程序")

            print("\n项目管理:")
            print("  execute    - 执行当前生成的计划")
            print("  result     - 查看执行结果")
            print("              - result tasks  显示任务详情")
            print("              - result detail 显示详细信息")

            print("\n记忆系统:")
            print("  memory stats       - 查看记忆统计")
            print("  memory query       - 查询记忆内容")
            print("  memory episodic    - 查看情节记忆")
            print("  memory semantic    - 查看语义记忆")
            print("  memory procedural  - 查看程序记忆")
            print("  memory export      - 导出记忆数据")
            print("  memory continuity  - 显示 CONTINUITY.md")

            print("\n代码审查:")
            print("  review status  - 查看审查配置")
            print("  review history - 查看审查历史")

            print("\n配置管理:")
            print("  config show     - 显示当前配置")
            print("  config init     - 初始化配置文件")
            print("  config edit     - 编辑配置")
            print("  config export   - 导出配置")

            print("\n自然语言编程:")
            print("  直接输入你的需求,例如:")
            print("    我想开发一个博客系统")
            print("    帮我创建一个任务管理API")
            print("    开发一个电商网站")

            print("\n典型工作流:")
            print("  1. 输入项目需求 → 生成计划")
            print("  2. execute plan  → 查看计划")
            print("  3. execute       → 执行计划")
            print("  4. result tasks  → 查看结果")
            print("  5. memory stats  → 查看记忆")

            print("\n提示: 输入 'help <命令>' 查看详细帮助")
            print()

    def do_quit(self, __args: str):
        """退出程序 - quit"""
        print("\n感谢使用SuperAgent v3.0!")
        print("文档: docs/")
        print("问题反馈: github.com/superagent/issues")
        return True

    def do_exit(self, __args: str):
        """退出程序 - exit"""
        return self.do_quit(__args)

    # ========== 默认处理 - 自然语言输入 ==========

    def default(self, line: str):
        """处理未识别的命令(作为自然语言输入)"""
        if not line.strip():
            return

        # 显示处理中
        print("\n正在理解您的需求...")

        # 调用对话管理器处理
        try:
            result = asyncio.run(self.conversation_mgr.process_input(line))
            self.display_result(result)
        except KeyboardInterrupt:
            print("\n\n⚠️  已取消")
        except (TimeoutError, asyncio.TimeoutError):
            print("\n❌ 处理超时，请稍后重试")
        except ConnectionError:
            print("\n❌ 网络连接失败，请检查您的连接")
        except Exception as e:
            print(f"\n错误 (未知类型): {e}")
            import traceback
            traceback.print_exc()

    # ========== 辅助方法 ==========

    def display_result(self, result):
        """显示处理结果"""
        if result.type == "clarification":
            print("\n" + "="*60)
            print("  需求澄清")
            print("="*60)

            print(f"\n{result.message}\n")

            for i, q in enumerate(result.clarifications, 1):
                required = "【必须】" if q.required else ""
                print(f"{i}. {q.question} {required}")

                if q.options:
                    for opt in q.options:
                        print(f"   - {opt}")

                if q.reason:
                    print(f"   理由: {q.reason}")
                print()

            print("请回答上述问题,或输入您的完整需求...")

        elif result.type == "requirements_ready":
            print("\n" + "="*60)
            print("  需求已明确")
            print("="*60)

            print(f"\n{result.message}")
            print(f"\n意图: {result.data['intent'].type.value}")
            print(f"置信度: {result.data['intent'].confidence}")

            # 进入规划阶段
            print("\n正在生成项目规划...")
            try:
                plan = asyncio.run(self.planner.create_plan(
                    result.data['user_input'],
                    result.data['context'],
                    intent=result.data.get('intent')
                ))

                # 显示计划
                plan_text = self.planner.format_plan(plan)
                print(plan_text)

                # 保存计划到CLI和对话管理器
                self.current_plan = plan
                self.conversation_mgr.set_context("current_plan", plan)

                print("\n提示:")
                print("  - 输入 'execute' 执行此计划")
                print("  - 输入 'execute plan' 查看计划详情")
                print("  - 输入新的需求将重新生成计划")

            except (TimeoutError, asyncio.TimeoutError):
                print(f"\n❌ 规划超时，请重试")
            except ValueError as e:
                print(f"\n❌ 规划数据错误: {e}")
            except Exception as e:
                print(f"\n规划失败 (未知错误): {e}")
                import traceback
                traceback.print_exc()

        else:
            print(f"\n{result.message}")

            if result.data:
                print(f"\n详细信息:")
                for key, value in result.data.items():
                    print(f"  {key}: {value}")


def main():
    """主入口函数"""
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ SuperAgent v3.0 需要Python 3.8或更高版本")
        print(f"   当前版本: {sys.version}")
        sys.exit(1)

    # 创建并启动CLI
    cli = SuperAgentCLI()

    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\n\n👋 程序已中断")
        sys.exit(0)
    except (OSError, IOError) as e:
        print(f"\n❌ 系统 IO 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生严重未知错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
