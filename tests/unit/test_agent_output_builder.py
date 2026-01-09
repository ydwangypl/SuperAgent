import unittest
from pathlib import Path
import os
import sys
from datetime import datetime

# 添加项目根目录到 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from execution.agent_output_builder import AgentOutputBuilder
from execution.models import Artifact
from common.security import SecurityError

class TestAgentOutputBuilder(unittest.TestCase):
    def setUp(self):
        self.project_root = Path(os.path.abspath(os.path.dirname(__file__))).parent.parent
        self.test_base_dir = self.project_root / "temp_test_artifacts"
        if not self.test_base_dir.exists():
            self.test_base_dir.mkdir(parents=True)

    def tearDown(self):
        # 清理测试目录
        import shutil
        if self.test_base_dir.exists():
            shutil.rmtree(self.test_base_dir)

    def test_create_artifact_path_validation(self):
        """测试工件创建时的路径校验"""
        # 正常路径
        artifact = AgentOutputBuilder.create_artifact(
            artifact_type="code",
            path="src/main.py",
            content="print('hello')",
            base_dir=self.test_base_dir
        )
        self.assertEqual(artifact.artifact_type, "code")
        # AgentOutputBuilder.create_artifact 现在返回绝对路径
        expected_path = (self.test_base_dir / "src/main.py").resolve()
        self.assertEqual(Path(artifact.path).resolve(), expected_path)

        # 尝试路径穿越 (非法路径)
        with self.assertRaises(SecurityError):
            AgentOutputBuilder.create_artifact(
                artifact_type="code",
                path="../outside.py",
                content="malicious",
                base_dir=self.test_base_dir
            )

    def test_create_test_artifact(self):
        """测试测试工件生成"""
        test_cases = [{
            "target": "login_func",
            "target_type": "function",
            "scenarios": ["成功登录", "密码错误"]
        }]
        code_structure = {
            "files": ["auth.py"],
            "functions": [{"name": "login_func", "file": "auth.py"}]
        }
        
        artifact = AgentOutputBuilder.create_test_artifact(
            target_name="Auth",
            test_cases=test_cases,
            code_structure=code_structure,
            base_dir=self.test_base_dir
        )
        
        self.assertEqual(artifact.artifact_type, "test_requirements")
        self.assertIn("Auth", artifact.content)
        self.assertIn("login_func", artifact.content)
        self.assertIn("成功登录", artifact.content)
        
        expected_path = (self.test_base_dir / "docs/test_requirements_auth.md").resolve()
        self.assertEqual(Path(artifact.path).resolve(), expected_path)

    def test_create_documentation_artifact(self):
        """测试文档工件生成"""
        artifact = AgentOutputBuilder.create_documentation_artifact(
            doc_type="api",
            title="User API",
            content="Detailed API info",
            base_dir=self.test_base_dir
        )
        
        self.assertEqual(artifact.artifact_type, "documentation")
        self.assertIn("# User API", artifact.content)
        self.assertIn("SuperAgent v3.0", artifact.content)
        
        expected_path = (self.test_base_dir / "docs/api.md").resolve()
        self.assertEqual(Path(artifact.path).resolve(), expected_path)

    def test_create_refactored_code_artifact(self):
        """测试重构代码工件生成"""
        artifact = AgentOutputBuilder.create_refactored_code_artifact(
            file_path="app/utils.py",
            content="def new_func(): pass",
            changes_count=2,
            base_dir=self.test_base_dir
        )
        
        self.assertEqual(artifact.artifact_type, "refactored_code")
        self.assertEqual(artifact.metadata['changes_count'], 2)
        
        expected_path = (self.test_base_dir / "app/utils.py").resolve()
        self.assertEqual(Path(artifact.path).resolve(), expected_path)

if __name__ == '__main__':
    unittest.main()
