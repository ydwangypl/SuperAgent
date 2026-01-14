# -*- coding: utf-8 -*-
"""
P1 功能演示 - 技能管理系统

演示 SkillChecker 的技能验证和管理功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from orchestration.skill_checker import SkillChecker, Skill


def demo_skill_checker():
    """演示技能管理系统"""

    print("=" * 80)
    print("[P1 功能演示 #2] 技能管理系统")
    print("=" * 80)
    print()

    # 创建技能检查器
    checker = SkillChecker()

    # 1. 查看所有技能
    print("[功能 1] 查看所有技能")
    print("-" * 80)
    all_skills = list(Skill)
    print(f"[OK] 技能总数: {len(all_skills)}")
    print(f"  技能列表:")
    for skill in all_skills:
        print(f"    - {skill.value:30} : {skill.name}")
    print()

    # 2. 启用 P0 核心技能
    print("[功能 2] 启用 P0 核心技能")
    print("-" * 80)
    p0_skills = [Skill.TEST_DRIVEN_DEVELOPMENT, Skill.CODE_REVIEW]
    for skill in p0_skills:
        checker.enable_skill(skill)
        print(f"  [OK] 已启用: {skill.value}")

    status = checker.get_skill_status()
    print(f"\n  当前启用技能: {sum(1 for v in status.values() if v)}/{len(status)}")
    for skill_id, enabled in status.items():
        status_str = "[+]" if enabled else "[ ]"
        print(f"    {status_str} {skill_id}")
    print()

    # 3. 检查任务需求 (通过)
    print("[功能 3] 检查任务需求 (通过案例)")
    print("-" * 80)
    task_type = "code_review"
    print(f"  任务类型: {task_type}")

    result = checker.check_task_skills(task_type, auto_fail=False)
    print(f"[OK] 检查结果: {'通过' if result else '失败'}")
    print(f"  说明: 代码审查只需要 TDD 和 Code Review 技能")
    print()

    # 4. 检查任务需求 (失败)
    print("[功能 4] 检查任务需求 (失败案例)")
    print("-" * 80)
    task_type = "feature_development"
    print(f"  任务类型: {task_type}")
    print(f"  需要技能: Brainstorming + TDD")

    result = checker.check_task_skills(task_type, auto_fail=False)
    print(f"[OK] 检查结果: {'通过' if result else '失败'}")

    if not result:
        # 获取历史记录
        history = checker.skill_history[-1]
        print(f"  缺失技能: {', '.join(history['missing_skills'])}")
        print(f"  可用技能: {', '.join(history['available_skills'])}")
    print()

    # 5. 启用所有技能
    print("[功能 5] 启用所有技能")
    print("-" * 80)
    for skill in all_skills:
        checker.enable_skill(skill)

    status = checker.get_skill_status()
    all_enabled = all(status.values())
    print(f"[OK] 所有技能已启用: {all_enabled}")
    print(f"  启用技能数: {sum(1 for v in status.values() if v)}/{len(status)}")
    print()

    # 6. 测试不同任务类型
    print("[功能 6] 不同任务类型的技能需求")
    print("-" * 80)
    task_types = [
        "feature_development",
        "bug_fixing",
        "code_review",
        "refactoring",
        "architecture_design"
    ]

    for task in task_types:
        result = checker.check_task_skills(task, auto_fail=False)
        status_str = "允许" if result else "拒绝"
        required = checker.TASK_SKILL_MAPPING.get(task, set())
        skills_str = ', '.join([s.value for s in required]) if required else "无"
        print(f"  {task:25} -> [{status_str}] 需要: {skills_str}")
    print()

    # 7. 禁用技能测试
    print("[功能 7] 禁用技能测试")
    print("-" * 80)
    checker.disable_skill(Skill.BRAINSTORMING)
    print(f"  禁用技能: {Skill.BRAINSTORMING.value}")

    result = checker.check_task_skills("feature_development", auto_fail=False)
    print(f"  检查 'feature_development': {'通过' if result else '失败'}")

    if not result:
        try:
            checker.check_task_skills("feature_development", auto_fail=True)
        except Exception as e:
            print(f"  异常信息: {str(e)[:80]}...")
    print()

    # 恢复
    checker.enable_skill(Skill.BRAINSTORMING)

    print("=" * 80)
    print("[完成] 技能管理系统演示完成!")
    print("=" * 80)
    print()


if __name__ == "__main__":
    demo_skill_checker()
