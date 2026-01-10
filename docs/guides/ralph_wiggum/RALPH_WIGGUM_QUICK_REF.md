# Ralph Wiggum 快速参考卡

**自然语言命令速查**

---

## 🎯 常用命令

### 基础命令

| 命令 | 说明 |
|------|------|
| `使用 Ralph Wiggum 改进 user.py` | 默认3次迭代,70分达标 |
| `使用 Ralph Wiggum 改进 user.py,最多5次` | 指定迭代次数 |
| `使用 Ralph Wiggum 改进 user.py,目标85分` | 指定目标评分 |
| `使用 Ralph Wiggum 改进 user.py,5次,90分` | 完全自定义 |
| `使用 Ralph Wiggum 审查 user.py` | 只审查不改进 |
| `使用 Ralph Wiggum 改进所有py文件` | 批量改进 |

---

## 📊 参数速查

### 迭代次数

| 次数 | 适用场景 |
|------|---------|
| 1次 | 快速检查 |
| 3次 | 默认推荐 ⭐ |
| 5次 | 高质量要求 |
| 7-10次 | 严格模式 |

### 目标评分

| 分数 | 难度 | 适用场景 |
|------|------|---------|
| 60分 | 容易 | 原型开发 |
| 70分 | 中等 | 默认推荐 ⭐ |
| 80分 | 较难 | 生产代码 |
| 85+分 | 很难 | 关键模块 |

---

## 💬 实战示例

### 示例 1: 三次未达标后继续

```
您: 使用 SuperAgent 开发用户登录
   [评分 65/100,未达标]

您: 使用 Ralph Wiggum 改进 auth.py,再试5次

我: [执行改进...]
    迭代1: 65/100
    迭代2: 68/100
    迭代3: 71/100
    迭代4: 73/100 ✅ 达标!

最终: 73/100
```

### 示例 2: 分步达标

```
第1步: 使用 Ralph Wiggum 改进 user.py
      → 72/100 ✅ (目标70)

第2步: 使用 Ralph Wiggum 改进 user.py,目标85
      → 86/100 ✅ (目标85)

第3步: 使用 Ralph Wiggum 改进 user.py,目标90,5次
      → 91/100 ✅ (目标90)
```

### 示例 3: 先审查后改进

```
第1步: 使用 Ralph Wiggum 审查 user.py

      评分: 65/100
      主要问题: 8个

第2步: 使用 Ralph Wiggum 改进 user.py,5次

      最终: 76/100 ✅
```

---

## 🎛️ 命令格式

### 最简格式
```
使用 Ralph Wiggum 改进 <文件>
```

### 完整格式
```
使用 Ralph Wiggum 改进 <文件>,最多<N>次迭代,目标<M>分
```

### 简化格式
```
使用 Ralph Wiggum 改进 <文件>,<N>次,<M>分
```

---

## ⚡ 快速开始

### Windows PowerShell
```powershell
# 设置环境变量
$env:SUPERAGENT_ROOT = "E:\SuperAgent"

# 在 Claude Code 中使用
使用 Ralph Wiggum 改进 user.py
```

### Linux/Mac
```bash
# 设置环境变量
export SUPERAGENT_ROOT="/path/to/SuperAgent"

# 在 Claude Code 中使用
使用 Ralph Wiggum 改进 user.py
```

---

## 📝 典型工作流

```
1. 使用 SuperAgent 开发...
   → 评分 68/100 (未达标)

2. 使用 Ralph Wiggum 改进 main.py,5次
   → 评分 75/100 ✅

3. 使用 Ralph Wiggum 改进 api.py,目标80
   → 评分 82/100 ✅

完成! 🎉
```

---

## 🔍 查看更多

- [RALPH_WIGGUM_USAGE.md](RALPH_WIGGUM_USAGE.md) - 完整使用指南
- [ralph_wiggum_cli.py](ralph_wiggum_cli.py) - 命令行工具
- [review/ralph_wiggum.py](review/ralph_wiggum.py) - 核心实现

---

**立即开始**: `使用 Ralph Wiggum 改进 <您的文件>` 🚀
