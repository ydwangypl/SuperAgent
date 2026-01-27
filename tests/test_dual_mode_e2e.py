#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SuperAgent v3.3 双轨质量保障端到端测试
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.')))

print('=' * 70)
print('SuperAgent v3.3 Dual-Mode QA - End-to-End Test')
print('=' * 70)

# TEST 1: pytest_utils
print('\n[TEST 1] pytest_utils module')
print('-' * 50)

from core.pytest_utils import build_pytest_command, parse_pytest_output

cmd1 = build_pytest_command()
assert cmd1 == ['pytest', '-v', '--tb=short', '--disable-warnings']
print('  OK: Default command correct')

cmd2 = build_pytest_command(test_path='tests/unit', verbose=False)
assert cmd2 == ['pytest', 'tests/unit', '-q', '--tb=line', '--disable-warnings']
print('  OK: Custom path command correct')

sample = '\n2 passed, 1 failed, 1 error in 0.05s\n'
result = parse_pytest_output(sample)
assert result['passed'] == 2
assert result['failed'] == 1
assert result['errors'] == 1
assert result['success'] == False
print('  OK: Output parsing (failure scenario)')

success_out = '\n5 passed in 0.12s\n'
success_result = parse_pytest_output(success_out)
assert success_result['success'] == True
print('  OK: Output parsing (success scenario)')

print('  PASS: pytest_utils module')

# TEST 2: TestRunner (Option A)
print('\n[TEST 2] TestRunner - Option A (main workflow integration)')
print('-' * 50)

from core.test_runner import TestRunner, TestResult

runner = TestRunner(project_root=Path('.'), timeout=60)
print(f'  OK: TestRunner init (timeout={runner._timeout}s)')

sync_result = runner.run_pytest_sync(test_path='tests/test_dual_mode_qa.py', verbose=True)
assert isinstance(sync_result, TestResult)
assert sync_result.total_tests >= 0
print(f'  OK: run_pytest_sync returns TestResult (passed={sync_result.passed})')

result_dict = sync_result.to_dict()
assert 'success' in result_dict
print('  OK: to_dict() works correctly')

runner.set_timeout(120)
assert runner._timeout == 120
print('  OK: set_timeout() works')

print('  PASS: TestRunner')

# TEST 3: TestAdapter (Option B)
print('\n[TEST 3] TestAdapter - Option B (independent API)')
print('-' * 50)

from adapters.test_adapter import TestAdapter

adapter = TestAdapter(project_root=Path('.'), timeout=60)
print(f'  OK: TestAdapter init (timeout={adapter._timeout}s)')

sync_result = adapter.run_tests_sync(test_path='tests/test_dual_mode_qa.py')
# P1: 统一使用 TestResult dataclass 格式
assert isinstance(sync_result, TestResult)
assert hasattr(sync_result, 'success')
assert hasattr(sync_result, 'passed')
print(f'  OK: run_tests_sync returns TestResult (passed={sync_result.passed})')

adapter.set_timeout(120)
assert adapter._timeout == 120
print('  OK: set_timeout() works')

print('  PASS: TestAdapter')

# TEST 4: UnifiedAdapter
print('\n[TEST 4] UnifiedAdapter - Full integration')
print('-' * 50)

from adapters.unified_adapter import UnifiedAdapter

unified = UnifiedAdapter(project_root=Path('.'))
print('  OK: UnifiedAdapter init')

assert hasattr(unified, 'tester')
assert isinstance(unified.tester, TestAdapter)
print('  OK: tester attribute correct')

assert hasattr(unified, 'run_tests')
assert hasattr(unified, 'run_tests_sync')
print('  OK: Test methods exposed')

assert hasattr(unified, 'execute_and_review_and_test')
assert hasattr(unified, 'execute_and_review_and_test_sync')
print('  OK: Full workflow methods exposed')

result = unified.run_tests_sync(test_path='tests/test_dual_mode_qa.py')
# P1: 统一使用 TestResult dataclass 格式
assert isinstance(result, TestResult)
assert result.success == True
assert result.passed >= 21
print(f'  OK: run_tests_sync executes (passed={result.passed})')

print('  PASS: UnifiedAdapter')

# TEST 5: Configuration
print('\n[TEST 5] Configuration integration')
print('-' * 50)

from orchestration.models import TestingConfig, OrchestrationConfig

config = TestingConfig()
assert config.enabled == True
assert config.timeout == 300
print(f'  OK: TestingConfig defaults (enabled={config.enabled}, timeout={config.timeout})')

custom = TestingConfig(enabled=False, test_path='tests/unit', timeout=600)
assert custom.enabled == False
assert custom.timeout == 600
print('  OK: TestingConfig custom values')

orch = OrchestrationConfig()
assert hasattr(orch, 'testing')
assert isinstance(orch.testing, TestingConfig)
print('  OK: OrchestrationConfig.testing integration')

print('  PASS: Configuration')

# TEST 6: Module exports
print('\n[TEST 6] Module exports')
print('-' * 50)

from adapters import TestAdapter as TA1
from adapters.test_adapter import TestAdapter as TA2
assert TA1 is TA2
print('  OK: TestAdapter exports consistent')

from core.test_runner import TestRunner as TR1
from core.test_runner import TestResult
print('  OK: core.test_runner exports correct')

print('  PASS: Module exports')

# TEST 7: Full workflow execution
print('\n[TEST 7] Full workflow execution')
print('-' * 50)

print('\n  [7.1] Option B: Independent test execution')
test_result = unified.run_tests_sync(test_path='tests/test_dual_mode_qa.py')
# P1: 统一使用 TestResult dataclass 格式
assert isinstance(test_result, TestResult)
assert test_result.success == True
print(f'      OK: Independent execution (passed={test_result.passed})')

print('\n  [7.2] Option B: Quick tests (sync)')
quick = adapter.run_tests_sync(config={'verbose': False})
# P1: 统一使用 TestResult dataclass 格式
assert isinstance(quick, TestResult)
print(f'      OK: Quick tests (passed={quick.passed})')

print('\n  [7.3] Option A: TestRunner execution')
runner_result = runner.run_pytest_sync(test_path='tests/test_dual_mode_qa.py', verbose=False)
assert runner_result.success == True
assert runner_result.passed >= 21
print(f'      OK: TestRunner execution (passed={runner_result.passed})')

print('  PASS: Full workflow')

# TEST 8: Error handling
print('\n[TEST 8] Error handling')
print('-' * 50)

error = adapter.run_tests_sync(test_path='tests/nonexistent.py')
# P1: 统一使用 TestResult dataclass 格式
assert isinstance(error, TestResult)
assert hasattr(error, 'success')
assert hasattr(error, 'total_tests')
print('  OK: Non-existent file handled correctly')

print('  PASS: Error handling')

# TEST 9: Async methods
print('\n[TEST 9] Async methods (Option B)')
print('-' * 50)

async def test_async():
    # Test run_tests async
    async_result = await adapter.run_tests(test_path='tests/test_dual_mode_qa.py')
    # P1: 统一使用 TestResult dataclass 格式
    assert isinstance(async_result, TestResult)
    assert async_result.passed >= 21
    print('      OK: async run_tests executes correctly')

    # Test run_quick_tests async
    quick_async = await adapter.run_quick_tests()
    assert isinstance(quick_async, TestResult)
    print('      OK: async run_quick_tests executes correctly')

    return True

asyncio.run(test_async())
print('  PASS: Async methods')

print('\n' + '=' * 70)
print('ALL 9 END-TO-END TESTS PASSED!')
print('=' * 70)
print('''
Summary:
  [TEST 1] pytest_utils module        - PASS
  [TEST 2] TestRunner (Option A)      - PASS
  [TEST 3] TestAdapter (Option B)     - PASS
  [TEST 4] UnifiedAdapter             - PASS
  [TEST 5] Configuration              - PASS
  [TEST 6] Module exports             - PASS
  [TEST 7] Full workflow execution    - PASS
  [TEST 8] Error handling             - PASS
  [TEST 9] Async methods              - PASS

Architecture:
  Option A (Main Workflow):  TestRunner  -> Auto test in Orchestrator
  Option B (Independent API): TestAdapter -> UnifiedAdapter.run_tests()
''')
