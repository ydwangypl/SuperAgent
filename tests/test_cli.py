#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI层单元测试
"""

import unittest
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

from cli.main import SuperAgentCLI


class TestSuperAgentCLI(unittest.TestCase):
    """CLI测试套件"""

    def setUp(self):
        """测试前准备"""
        self.cli = SuperAgentCLI()

    def test_cli_initialization(self):
        """测试CLI初始化"""
        self.assertIsNotNone(self.cli)
        self.assertEqual(self.cli.current_project, None)
        self.assertIsNotNone(self.cli.conversation_mgr)
        self.assertIsNotNone(self.cli.planner)

    def test_prompt_format(self):
        """测试提示符格式"""
        self.assertEqual(self.cli.prompt, "\033[1;32mSuperAgent>\033[0m ")

    def test_intro_display(self):
        """测试欢迎信息"""
        intro = self.cli.intro
        self.assertIn("SuperAgent v3.1", intro)
        self.assertIn("自然语言编程系统", intro)

    @patch('sys.stdout', new_callable=StringIO)
    def test_do_status(self, mock_stdout):
        """测试status命令"""
        self.cli.do_status("")
        output = mock_stdout.getvalue()
        self.assertIn("SuperAgent版本", output)
        self.assertIn("Python版本", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_do_help(self, mock_stdout):
        """测试help命令"""
        self.cli.do_help("")
        output = mock_stdout.getvalue()
        self.assertIn("命令帮助", output)
        self.assertIn("内置命令", output)

    def test_do_clear(self):
        """测试clear命令"""
        # 只测试不抛异常
        try:
            self.cli.do_clear("")
        except Exception as e:
            self.fail(f"do_clear raised exception: {e}")

    def test_do_pwd(self):
        """测试pwd命令"""
        import os
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.cli.do_pwd("")
            output = mock_stdout.getvalue()
            self.assertIn(os.getcwd(), output)

    def test_do_cd(self):
        """测试cd命令"""
        import os
        import tempfile
        from pathlib import Path

        # 在项目根目录下创建测试目录, 避免跨驱动器/跨根目录的安全限制
        test_dir = Path("test_cd_dir")
        test_dir.mkdir(exist_ok=True)

        try:
            # 测试cd到测试目录
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                self.cli.do_cd(str(test_dir))
                output = mock_stdout.getvalue()
                self.assertIn("已切换到", output)
                
                # 验证工作目录确实改变了 (由于是相对路径切换, 需要验证 cwd 的结尾)
                cwd = os.getcwd()
                self.assertTrue(cwd.endswith("test_cd_dir"))
                
            # 切回原目录
            os.chdir("..")
        finally:
            # 清理
            if test_dir.exists():
                import shutil
                # 确保我们不在要删除的目录里
                if os.getcwd().endswith("test_cd_dir"):
                    os.chdir("..")
                shutil.rmtree(test_dir)

    def test_do_ls(self):
        """测试ls命令"""
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.cli.do_ls(".")
            output = mock_stdout.getvalue()
            self.assertTrue(len(output) > 0)

    def test_do_quit(self):
        """测试quit命令"""
        result = self.cli.do_quit("")
        self.assertTrue(result)

    def test_do_exit(self):
        """测试exit命令"""
        result = self.cli.do_exit("")
        self.assertTrue(result)

    @patch('sys.stdout', new_callable=StringIO)
    def test_default_empty_input(self, mock_stdout):
        """测试空输入"""
        self.cli.default("")
        # 应该不输出任何内容
        output = mock_stdout.getvalue()
        self.assertEqual(output, "")

    @patch('sys.stdout', new_callable=StringIO)
    def test_default_with_conversation(self, mock_stdout):
        """测试自然语言输入"""
        # Mock对话管理器
        mock_response = MagicMock()
        mock_response.type = "requirements_ready"
        mock_response.message = "需求已明确"
        mock_response.data = {
            'intent': MagicMock(type=MagicMock(value="new_project")),
            'user_input': "test",
            'context': {}
        }

        with patch.object(self.cli.conversation_mgr, 'process_input',
                         return_value=mock_response):
            self.cli.default("测试输入")

        output = mock_stdout.getvalue()
        self.assertIn("正在理解您的需求", output)


if __name__ == '__main__':
    unittest.main()
