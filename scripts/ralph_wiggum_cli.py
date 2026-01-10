#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ralph Wiggum 独立调用接口

允许用户通过自然语言单独调用 Ralph Wiggum 进行代码改进
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

# 添加 SuperAgent 到路径
sys.path.insert(0, str(Path(__file__).parent))

from review import CodeReviewer, RalphWiggumLoop, ReviewConfig, ReviewResult
from common.models import ReviewSeverity


class RalphWiggumStandalone:
    """Ralph Wiggum 独立调用接口"""

    def __init__(
        self,
        project_root: Path,
        min_score: float = 70.0,
        max_iterations: int = 3
    ):
        """初始化 Ralph Wiggum

        Args:
            project_root: 项目根目录
            min_score: 最低质量评分要求
            max_iterations: 最大迭代次数
        """
        self.project_root = project_root

        # 创建配置
        self.config = ReviewConfig(
            enable_style_check=True,
            enable_security_check=True,
            enable_performance_check=True,
            enable_best_practices=True,
            enable_ralph_wiggum=True,
            min_overall_score=min_score,
            ralph_wiggum_max_iterations=max_iterations
        )

        # 初始化审查器和循环
        self.code_reviewer = CodeReviewer(self.config)
        self.ralph_wiggum_loop = RalphWiggumLoop(self.code_reviewer, self.config)

    async def improve_file(
        self,
        file_path: str,
        max_iterations: Optional[int] = None
    ) -> ReviewResult:
        """改进单个文件

        Args:
            file_path: 文件路径 (相对或绝对路径)
            max_iterations: 最大迭代次数 (可选,覆盖默认值)

        Returns:
            ReviewResult: 审查结果
        """
        # 解析文件路径
        file_path = self._resolve_path(file_path)

        # 读取代码
        code_content = {file_path.name: file_path.read_text(encoding='utf-8')}

        # 更新迭代次数
        if max_iterations:
            self.config.ralph_wiggum_max_iterations = max_iterations

        # 执行改进循环
        print(f"\n{'='*60}")
        print(f"Ralph Wiggum 代码改进")
        print(f"{'='*60}")
        print(f"文件: {file_path}")
        print(f"目标评分: {self.config.min_overall_score}")
        print(f"最大迭代: {self.config.ralph_wiggum_max_iterations}")
        print(f"{'='*60}\n")

        result = await self.ralph_wiggum_loop.review_with_loop(
            task_id=f"improve-{file_path.name}",
            files=[file_path],
            code_content=code_content,
            llm_callback=self._generate_improvements
        )

        return result

    async def improve_files(
        self,
        file_patterns: List[str],
        max_iterations: Optional[int] = None
    ) -> Dict[str, ReviewResult]:
        """改进多个文件

        Args:
            file_patterns: 文件路径列表 (支持 glob 模式)
            max_iterations: 最大迭代次数

        Returns:
            Dict[str, ReviewResult]: 每个文件的审查结果
        """
        results = {}

        for pattern in file_patterns:
            # 解析 glob 模式
            files = list(self.project_root.glob(pattern))

            if not files:
                print(f"[WARNING] 未找到文件: {pattern}")
                continue

            for file_path in files:
                if file_path.is_file():
                    try:
                        result = await self.improve_file(
                            str(file_path),
                            max_iterations
                        )
                        results[str(file_path)] = result
                    except Exception as e:
                        print(f"[ERROR] 处理 {file_path} 失败: {e}")

        return results

    async def _generate_improvements(
        self,
        current_code: Dict[str, str],
        improvements: List[Dict]
    ) -> Dict[str, str]:
        """生成改进代码 (回调函数)

        注意: 这是一个占位实现。在实际使用中,这个函数应该调用
        Claude Code 或其他 LLM 来实际改进代码。

        Args:
            current_code: 当前代码
            improvements: 改进建议列表

        Returns:
            改进后的代码
        """
        print(f"\n需要 {len(improvements)} 个改进:")

        for i, improvement in enumerate(improvements, 1):
            print(f"  {i}. [{improvement.get('priority', 'unknown')}] {improprovement['description']}")

        print("\n[提示] 在实际使用中,这里会调用 Claude Code 来改进代码")
        print("[提示] 当前返回原始代码,请手动应用改进建议\n")

        # 在实际集成中,这里应该调用 Claude Code
        # 现在返回原代码作为占位
        return current_code

    def _resolve_path(self, file_path: str) -> Path:
        """解析文件路径"""
        path = Path(file_path)

        if not path.is_absolute():
            path = self.project_root / path

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")

        return path


def print_result(result: ReviewResult):
    """打印审查结果"""
    print(f"\n{'='*60}")
    print(f"审查结果")
    print(f"{'='*60}")
    print(f"状态: {result.status.value}")
    print(f"迭代次数: {result.iteration_count}")
    print(f"\n评分:")
    print(f"  总体: {result.metrics.overall_score:.1f}/100")
    print(f"  风格: {result.metrics.style_score:.1f}/100")
    print(f"  安全: {result.metrics.security_score:.1f}/100")
    print(f"  性能: {result.metrics.performance_score:.1f}/100")
    print(f"  最佳实践: {result.metrics.best_practices_score:.1f}/100")

    print(f"\n问题:")
    print(f"  总计: {result.metrics.issue_count}")
    print(f"  严重: {result.metrics.critical_count}")
    print(f"  主要: {result.metrics.major_count}")
    print(f"  次要: {result.metrics.minor_count}")

    if result.issues:
        print(f"\n主要问题:")
        for issue in result.issues[:5]:
            print(f"  - [{issue.severity.value}] {issue.title}")
            print(f"    位置: {issue.location}")
            if issue.suggestion:
                print(f"    建议: {issue.suggestion}")

    print(f"\n摘要:")
    print(f"  {result.summary}")

    if result.iteration_count > 1:
        if result.metrics.overall_score >= 70:
            print(f"  [SUCCESS] 经过 {result.iteration_count} 次迭代,代码已达标!")
        else:
            print(f"  [WARNING] 经过 {result.iteration_count} 次迭代仍未完全达标")
            print(f"  [TIP] 您可以增加迭代次数或手动改进代码")

    print(f"{'='*60}\n")


async def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Ralph Wiggum 代码改进工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 改进单个文件 (默认3次迭代)
  python ralph_wiggum_cli.py improve user.py

  # 指定迭代次数
  python ralph_wiggum_cli.py improve user.py --iterations 5

  # 指定目标评分
  python ralph_wiggum_cli.py improve user.py --min-score 85

  # 改进多个文件
  python ralph_wiggum_cli.py improve "**/*.py"

  # 完全自定义
  python ralph_wiggum_cli.py improve user.py --iterations 5 --min-score 90
        """
    )

    parser.add_argument(
        'command',
        choices=['improve'],
        help='命令: improve (改进代码)'
    )

    parser.add_argument(
        'files',
        nargs='+',
        help='文件路径 (支持 glob 模式)'
    )

    parser.add_argument(
        '--iterations',
        type=int,
        default=3,
        help='最大迭代次数 (默认: 3)'
    )

    parser.add_argument(
        '--min-score',
        type=float,
        default=70.0,
        help='最低质量评分 (默认: 70.0)'
    )

    parser.add_argument(
        '--project-root',
        type=str,
        default='.',
        help='项目根目录 (默认: 当前目录)'
    )

    args = parser.parse_args()

    # 初始化
    rw = RalphWiggumStandalone(
        project_root=Path(args.project_root),
        min_score=args.min_score,
        max_iterations=args.iterations
    )

    # 执行改进
    if len(args.files) == 1 and not '*' in args.files[0]:
        # 单个文件
        result = await rw.improve_file(args.files[0], args.iterations)
        print_result(result)
    else:
        # 多个文件
        results = await rw.improve_files(args.files, args.iterations)

        for file_path, result in results.items():
            print(f"\n文件: {file_path}")
            print_result(result)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INFO] 用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        sys.exit(1)
