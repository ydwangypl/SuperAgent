#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent v3.0 端到端测试(简化版)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from planning.planner import ProjectPlanner
from orchestration.orchestrator import Orchestrator


async def test_e2e():
    """端到端测试"""
    print("="*70)
    print("  SuperAgent v3.0 End-to-End Test")
    print("="*70)

    # User input
    user_input = "Develop a blog system with article management"
    print(f"\n[1] User Input: {user_input}")

    # Step 1: Generate plan
    print("\n[2] Generating execution plan...")
    planner = ProjectPlanner()
    plan = await planner.create_plan(user_input, {})

    print(f"    - Steps: {len(plan.steps)}")
    print(f"    - Project Type: {plan.analysis.project_type}")
    print(f"    - Estimated Time: {int(plan.estimated_time.total_seconds() / 60)} min")

    # Step 2: Execute plan
    print("\n[3] Executing plan...")
    orchestrator = Orchestrator(Path.cwd())
    result = await orchestrator.execute_plan(plan)

    # Step 3: Show results
    print("\n[4] Results:")
    print(f"    - Status: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"    - Completed: {result.completed_tasks}/{result.total_tasks}")
    print(f"    - Failed: {result.failed_tasks}")
    print(f"    - Duration: {result.duration_seconds}s")
    print(f"    - Success Rate: {result.success_rate * 100:.1f}%")

    if result.success:
        print("\n[OK] End-to-end test PASSED!")
        return 0
    else:
        print("\n[FAIL] End-to-end test FAILED!")
        if result.errors:
            for error in result.errors:
                print(f"    Error: {error}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_e2e())
    sys.exit(exit_code)
