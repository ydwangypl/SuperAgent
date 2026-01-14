@echo off
echo ========================================
echo 重构后验证
echo ========================================
echo.

echo [1/4] 运行所有测试
call scripts\run_all_tests.bat

echo.
echo [2/4] 性能对比
echo 重构前基准 vs 当前性能
python tests/test_performance.py

echo.
echo [3/4] 覆盖率检查
python generate_coverage_report.py

echo.
echo [4/4] 集成测试
python run_all_integration_tests.py

echo.
echo ========================================
echo 重构后验证完成!
echo ========================================
pause
