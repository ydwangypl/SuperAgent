# 贡献指南

感谢您对 SuperAgent 的关注!我们欢迎任何形式的贡献。

---

## 🤝 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议:

1. 检查 [Issues](https://github.com/your-org/SuperAgent/issues) 是否已有相关问题
2. 如果没有,创建新的 Issue
3. 使用清晰的标题和详细的描述
4. 提供复现步骤 (针对 bug) 或使用场景 (针对功能)

### 提交代码

#### 1. Fork 仓库

点击页面右上角的 Fork 按钮

#### 2. 克隆您的 Fork

```bash
git clone https://github.com/YOUR_USERNAME/SuperAgent.git
cd SuperAgent
```

#### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

#### 4. 进行更改

- 遵循现有代码风格
- 添加测试 (新功能或 bug 修复)
- 更新文档 (如有必要)
- 确保所有测试通过

```bash
# 运行测试
pytest tests/

# 代码格式化
black .

# 类型检查
mypy .
```

#### 5. 提交更改

```bash
git add .
git commit -m "描述您的更改"
```

提交消息格式:
```
类型(范围): 简短描述

详细描述

关联 Issue: #123
```

类型:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例:
```
feat(platform): 添加 OpenAI Codex 平台支持

实现了 OpenAI Codex 平台适配器,支持 5 个核心工具:
- read: 文件读取
- write: 文件写入
- edit: 文件编辑
- execute: 命令执行
- search: 文件搜索

关联 Issue: #42
```

#### 6. 推送到您的 Fork

```bash
git push origin feature/your-feature-name
```

#### 7. 创建 Pull Request

1. 访问您 Fork 的页面
2. 点击 "New Pull Request"
3. 提供清晰的标题和描述
4. 引用相关的 Issue (如 `Fixes #123`)
5. 等待代码审查

---

## 📋 开发指南

### 环境设置

#### 1. Python 版本

- Python 3.11 或更高版本

#### 2. 安装依赖

```bash
# 克隆仓库
git clone https://github.com/your-org/SuperAgent.git
cd SuperAgent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 3. 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_platform_adapters.py

# 运行测试并显示覆盖率
pytest --cov=platform_adapters --cov-report=html
```

### 代码风格

我们使用以下工具维护代码质量:

- **Black**: 代码格式化
  ```bash
  black .
  ```

- **isort**: Import 排序
  ```bash
  isort .
  ```

- **flake8**: 代码检查
  ```bash
  flake8 .
  ```

- **mypy**: 类型检查
  ```bash
  mypy .
  ```

### 项目结构

```
SuperAgent/
├── cli/                    # CLI 界面
├── conversation/           # 对话管理
├── execution/              # Agent 执行
│   ├── base_agent.py      # 基础 Agent
│   ├── coding_agent.py    # 代码生成 Agent
│   ├── tdd_validator.py   # TDD 验证器
│   └── systematic_debugger.py  # 调试器
├── orchestration/          # 编排系统
│   ├── registry.py        # 技能注册表
│   ├── skill_checker.py   # 技能检查器
│   └── parallel_executor.py  # 并行执行器
├── planning/               # 规划系统
│   └── planner.py         # 任务规划器
├── platform_adapters/      # 平台适配器 (P2)
│   ├── adapter_base.py    # 适配器基类
│   ├── platform_detector.py  # 平台检测
│   ├── tool_mapper.py     # 工具映射
│   ├── claude_code_adapter.py  # Claude Code 适配器
│   ├── openai_codex_adapter.py  # OpenAI Codex 适配器
│   └── opencode_adapter.py  # OpenCode 适配器
├── utils/                  # 工具函数
├── tests/                  # 测试文件
├── docs/                   # 文档
└── extensions/             # 扩展功能
```

### 开发工作流

#### 1. 功能开发

1. 在 GitHub Issues 中讨论新功能
2. 创建功能分支
3. 实现功能并添加测试
4. 更新文档
5. 提交 Pull Request

#### 2. Bug 修复

1. 在 GitHub Issues 中报告 bug
2. 创建修复分支
3. 复现并修复 bug
4. 添加测试防止回归
5. 提交 Pull Request

#### 3. 文档改进

1. 识别需要改进的文档
2. 创建文档分支
3. 更新文档
4. 提交 Pull Request

---

## 🧪 测试指南

### 编写测试

我们使用 pytest 作为测试框架。

#### 测试文件位置

测试文件应放在 `tests/` 目录下,并命名为 `test_*.py`。

#### 测试示例

```python
import unittest
from platform_adapters import PlatformDetector

class TestPlatformDetector(unittest.TestCase):
    def setUp(self):
        self.detector = PlatformDetector()

    def test_detect_platform(self):
        platform = self.detector.detect_platform()
        self.assertIsNotNone(platform)

if __name__ == '__main__':
    unittest.main()
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_platform_detector.py

# 运行特定测试类
pytest tests/test_platform_detector.py::TestPlatformDetector

# 运行特定测试方法
pytest tests/test_platform_detector.py::TestPlatformDetector::test_detect_platform

# 显示详细输出
pytest -v

# 显示测试覆盖率
pytest --cov=platform_adapters --cov-report=html
```

### 测试覆盖率

我们致力于保持高测试覆盖率:
- 新功能: > 90% 覆盖率
- Bug 修复: 添加测试防止回归

---

## 📖 文档指南

### 文档类型

1. **API 文档**: 使用 docstring 记录所有公共 API
2. **用户指南**: 帮助用户使用 SuperAgent
3. **开发者指南**: 帮助开发者贡献代码
4. **架构文档**: 描述系统架构和设计

### 文档风格

- 使用清晰简洁的语言
- 提供代码示例
- 保持文档与代码同步

---

## 🎯 代码审查

### 审查标准

Pull Request 将根据以下标准审查:

1. **代码质量**
   - 遵循代码风格指南
   - 通过所有测试
   - 无明显性能问题

2. **文档**
   - 更新相关文档
   - 添加清晰的 commit 消息
   - 提供使用示例 (如适用)

3. **测试**
   - 新功能有测试覆盖
   - Bug 修复有回归测试
   - 测试通过率 100%

### 审查流程

1. 自动检查 (CI/CD)
   - 代码格式检查
   - 类型检查
   - 测试运行

2. 人工审查
   - 代码质量审查
   - 架构设计审查
   - 文档完整性审查

3. 反馈和修改
   - 审查者提供反馈
   - 贡献者进行修改
   - 重新审查

4. 合并
   - 审查通过后合并
   - 更新 CHANGELOG
   - 发布版本 (如适用)

---

## 🌟 贡献者指南

### 成为贡献者

任何被合并的贡献都会被记录在贡献者列表中。

### 贡献者行为

- 尊重所有贡献者
- 建设性反馈
- 友好协作
- 遵循行为准则

### 认可

重要贡献将在以下地方获得认可:
- README.md 贡献者部分
- 发布说明中
- 项目网站

---

## ❓ 获取帮助

### 联系方式

- **GitHub Issues**: 技术问题和 bug 报告
- **Discord**: 实时讨论和社区支持
- **Email**: project@example.com

### 资源

- [README.md](README.md) - 项目概述
- [文档](docs/) - 详细文档
- [API 参考](docs/api/) - API 文档

---

## 📜 许可证

通过贡献代码,您同意您的贡献将根据项目的许可证进行许可。

---

## 🙏 致谢

感谢所有为 SuperAgent 做出贡献的人!

您的贡献让 SuperAgent 变得更好!

---

**最后更新**: 2026-01-14
**SuperAgent v3.2+ 开发团队
