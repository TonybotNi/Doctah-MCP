<div align="center">

<img src="./assets/images/doctah-mcp-logo.png" alt="Doctah-MCP Logo" width="150" height="150">

# Doctah-MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

**🌍 Language / 语言选择:**
[🇺🇸 English](README.md) | [🇨🇳 中文](README_zh.md)

</div>

> 🎯 让 AI 助手能够搜索和访问明日方舟游戏资料的 MCP 服务器

Doctah-MCP 通过 Model Context Protocol (MCP) 为 AI 模型提供明日方舟 PRTS.wiki 资料的程序化访问接口。它让 AI 模型能够搜索干员、敌人信息并获取详细内容。

## ✨ 核心功能

* 🎯 **干员搜索**: 查询干员详细信息，包括技能、天赋、基本属性等
* ⚔️ **敌人查询**: 获取敌人数据和等级信息
* 📋 **列表搜索**: 模糊搜索查找相关干员或敌人
* 🔍 **内容验证**: 智能区分干员和敌人页面，确保查询准确性
* 🤖 **AI 友好**: 结构化 Markdown 输出，便于 AI 理解

## 🚀 快速开始

### 通过源码安装

```bash
git clone https://github.com/TonybotNi/Doctah-MCP.git
cd doctah-mcp
pip install -e .
```

**验证安装：**
```bash
# 测试全局命令是否可用
doctah-mcp --help

# 或者测试 Python 模块方式
python -m doctah_mcp.server --help
```

### 开发环境安装

```bash
# 克隆仓库
git clone https://github.com/TonybotNi/Doctah-MCP.git
cd doctah-mcp

# 安装开发依赖
pip install -e ".[dev]"
```

### 🔌 MCP 集成配置

选择以下配置方法之一添加到你的 MCP 客户端配置文件中：

**方法1：使用全局命令（推荐）**
```json
{
    "mcpServers": {
        "doctah-mcp": {
            "command": "doctah-mcp",
            // 或使用完整路径: "/full/path/to/doctah-mcp"
            "args": []
        }
    }
}
```
> 💡 如果找不到 `doctah-mcp` 命令，请使用方法3，用完整的 python 路径

**方法2：使用 Python 模块**
```json
{
    "mcpServers": {
        "doctah-mcp": {
            "command": "python",
            "args": ["-m", "doctah_mcp.server"]
        }
    }
}
```

**方法3：指定完整路径（最可靠）**
```json
{
    "mcpServers": {
        "doctah-mcp": {
            "command": "/full/path/to/python",
            "args": ["-m", "doctah_mcp.server"],
            "cwd": "/path/to/doctah-mcp-folder"
        }
    }
}
```

> 💡 **说明**: `cwd` 是工作目录，只在方法3中需要，指向你下载的 doctah-mcp 项目文件夹

## 💡 可用工具

服务器提供四个主要工具：

### 1. 搜索干员信息

根据干员名称查询详细信息：

```python
result = await call_tool("search_operator_mcp", {
    "name": "银灰",
    "sections": "技能,天赋"
})
```

### 2. 搜索敌人信息

根据敌人名称获取数据：

```python
result = await call_tool("search_enemy_mcp", {
    "name": "源石虫",
    "sections": "级别0,级别1"
})
```

### 3. 列出干员

查找匹配的干员列表：

```python
result = await call_tool("list_operators_mcp", {
    "name": "医疗"
})
```

### 4. 列出敌人

查找匹配的敌人列表：

```python
result = await call_tool("list_enemies_mcp", {
    "name": "无人机"
})
```

## 📁 客户端配置

### Claude Desktop

配置文件位置：
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**推荐配置（最简单）：**
```json
{
  "mcpServers": {
    "doctah-mcp": {
      "command": "doctah-mcp",
      "args": []
    }
  }
}
```

**备用配置（如果上面不工作）：**
```json
{
  "mcpServers": {
    "doctah-mcp": {
      "command": "/full/path/to/python",
      "args": ["-m", "doctah_mcp.server"],
      "cwd": "/path/to/doctah-mcp-folder"
    }
  }
}
```

### Cherry Studio

1. 打开 Cherry Studio → Settings → MCP Servers → Add
2. 类型选择：STDIO
3. **简单配置**：
   - **Command**: `doctah-mcp`
   - **Args**: `[]`
4. **备用配置**（如果上面不工作）：
   - **Command**: `/full/path/to/python`
   - **Args**: `["-m", "doctah_mcp.server"]`
   - **Cwd**: `/path/to/doctah-mcp-folder`

## ⚙️ 配置

通过环境变量进行配置：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| LOG_LEVEL | 日志级别 | INFO |

## 🧪 测试

运行测试套件：

```bash
python -m pytest
```

## 📄 许可证

基于 MIT 许可证发布。详见 [LICENSE](LICENSE) 文件。

## 📖 详细配置指南

需要更详细的配置说明和故障排除？查看：
- [Claude Desktop 详细配置](docs/setup/claude_desktop.md)
- [Cherry Studio 详细配置](docs/setup/cherry_studio.md)

---

<div align="center">

Made with ❤️ for Arknights community

## GitHub Star History

[![Star History Chart](https://api.star-history.com/svg?repos=tonybotni/doctah-mcp&type=Date)](https://star-history.com/#tonybotni/doctah-mcp&Date)

</div> 