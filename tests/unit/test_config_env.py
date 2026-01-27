#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置模块环境变量支持测试

v3.3 新增: 环境变量配置覆盖测试
"""

import os
import pytest
from pathlib import Path
from config.settings import (
    load_config,
    load_config_from_env,
    get_env_config_summary,
)


class TestEnvConfig:
    """环境变量配置测试类"""

    def setup_method(self):
        """每个测试前清理环境变量"""
        # 保存原始环境变量
        self._orig_env = {}
        for key in [
            "SUPERAGENT_LOG_LEVEL",
            "SUPERAGENT_REDIS_URL",
            "SUPERAGENT_REDIS_PASSWORD",
            "SUPERAGENT_MEMORY_ENABLED",
            "SUPERAGENT_ORCHESTRATION_PARALLEL",
            "SUPERAGENT_EXPERIENCE_LEVEL",
        ]:
            self._orig_env[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

    def teardown_method(self):
        """每个测试后恢复环境变量"""
        for key in [
            "SUPERAGENT_LOG_LEVEL",
            "SUPERAGENT_REDIS_URL",
            "SUPERAGENT_REDIS_PASSWORD",
            "SUPERAGENT_MEMORY_ENABLED",
            "SUPERAGENT_ORCHESTRATION_PARALLEL",
            "SUPERAGENT_EXPERIENCE_LEVEL",
            "SUPERAGENT_ORCHESTRATION_MAX_TASKS",
        ]:
            os.environ.pop(key, None)

    def test_load_config_from_env_empty(self):
        """测试无环境变量时返回空字典"""
        overrides = load_config_from_env()
        assert overrides == {}

    def test_load_config_from_env_log_level(self):
        """测试日志级别环境变量加载"""
        os.environ["SUPERAGENT_LOG_LEVEL"] = "DEBUG"
        overrides = load_config_from_env()
        assert "logging" in overrides
        assert overrides["logging"]["level"] == "DEBUG"

    def test_load_config_from_env_boolean(self):
        """测试布尔值环境变量解析"""
        os.environ["SUPERAGENT_MEMORY_ENABLED"] = "false"
        overrides = load_config_from_env()
        assert "memory" in overrides
        assert overrides["memory"]["enabled"] is False

        os.environ["SUPERAGENT_MEMORY_ENABLED"] = "true"
        overrides = load_config_from_env()
        assert overrides["memory"]["enabled"] is True

        os.environ["SUPERAGENT_MEMORY_ENABLED"] = "1"
        overrides = load_config_from_env()
        assert overrides["memory"]["enabled"] is True

        os.environ["SUPERAGENT_MEMORY_ENABLED"] = "0"
        overrides = load_config_from_env()
        assert overrides["memory"]["enabled"] is False

    def test_load_config_from_env_integer(self):
        """测试整数值环境变量解析"""
        os.environ["SUPERAGENT_ORCHESTRATION_MAX_TASKS"] = "5"
        overrides = load_config_from_env()
        assert "orchestration" in overrides
        assert overrides["orchestration"]["max_parallel_tasks"] == 5

    def test_load_config_from_env_experience_level(self):
        """测试经验等级环境变量"""
        os.environ["SUPERAGENT_EXPERIENCE_LEVEL"] = "master"
        overrides = load_config_from_env()
        assert "experience_level" in overrides
        assert overrides["experience_level"] == "master"

    def test_load_config_with_env_override(self):
        """测试配置加载时应用环境变量覆盖"""
        os.environ["SUPERAGENT_LOG_LEVEL"] = "WARNING"

        # 使用临时目录
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            config = load_config(project_root=Path(tmpdir))
            assert config.logging.level == "WARNING"

    def test_load_config_env_disabled(self):
        """测试禁用环境变量覆盖"""
        os.environ["SUPERAGENT_LOG_LEVEL"] = "DEBUG"

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            config = load_config(
                project_root=Path(tmpdir),
                allow_env_overrides=False
            )
            # 默认是 INFO，除非配置文件中有其他设置
            assert config.logging.level == "INFO"

    def test_get_env_config_summary_empty(self):
        """测试空环境变量摘要"""
        # 确保清理所有相关环境变量
        for key in list(os.environ.keys()):
            if key.startswith("SUPERAGENT_"):
                del os.environ[key]

        summary = get_env_config_summary()
        # 检查摘要是否表示没有活动配置
        assert "无活动" in summary or summary.strip() == "无活动的环境变量配置"

    def test_get_env_config_summary_with_values(self):
        """测试带值的配置摘要"""
        os.environ["SUPERAGENT_LOG_LEVEL"] = "INFO"
        os.environ["SUPERAGENT_REDIS_PASSWORD"] = "secret123"

        summary = get_env_config_summary()
        assert "SUPERAGENT_LOG_LEVEL" in summary
        # 密码应该被隐藏
        assert "***" in summary or "secret" not in summary

    def test_redis_url_override(self):
        """测试 Redis URL 环境变量覆盖"""
        os.environ["SUPERAGENT_REDIS_URL"] = "redis://localhost:6380/1"
        overrides = load_config_from_env()

        assert "distribution" in overrides
        assert overrides["distribution"]["broker_url"] == "redis://localhost:6380/1"


class TestConfigIntegration:
    """配置集成测试"""

    def test_default_config(self):
        """测试默认配置"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            config = load_config(project_root=Path(tmpdir))

            # 验证默认值
            assert config.experience_level == "novice"
            assert config.memory.enabled is True
            assert config.orchestration.enable_parallel_execution is True
            assert config.token_optimization.enabled is True

    def test_config_with_env_and_file(self):
        """测试环境变量和配置文件同时存在时的优先级"""
        os.environ["SUPERAGENT_LOG_LEVEL"] = "ERROR"

        import tempfile
        import json

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建配置文件
            config_dir = Path(tmpdir) / ".superagent"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"

            config_data = {
                "experience_level": "master",
                "logging": {
                    "level": "DEBUG"
                }
            }
            config_file.write_text(json.dumps(config_data), encoding='utf-8')

            # 加载配置
            config = load_config(project_root=Path(tmpdir))

            # 环境变量应该覆盖文件中的值
            assert config.logging.level == "ERROR"
            # 文件中的值应该保留
            assert config.experience_level == "master"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
