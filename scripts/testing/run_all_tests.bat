@echo off
echo ========================================
echo 运行所有测试
echo ========================================
echo.

echo [1/4] 单元测试
pytest tests/ -v -k "not integration"

echo.
echo [2/4] 集成测试
pytest tests/test_*.py -v -k "integration"

echo.
echo [3/4] 性能测试
python tests/test_performance.py

echo.
echo [4/4] 生成覆盖率报告
python generate_coverage_report.py

echo.
echo ========================================
echo 所有测试完成!
echo ========================================
pause
