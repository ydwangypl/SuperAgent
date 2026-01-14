@echo off
echo ========================================
echo 重构前检查
echo ========================================
echo.

echo [1/3] 运行所有测试
call scripts\run_all_tests.bat

echo.
echo [2/3] 检查覆盖率
python generate_coverage_report.py

echo.
echo [3/3] 运行性能测试
python tests/test_performance.py

echo.
echo ========================================
echo 重构前检查完成!
echo ========================================
echo.
echo 如果所有测试通过,可以开始重构。
echo.
pause
