<div align="center">

<img src="../../assets/images/doctah-mcp-logo.png" alt="Doctah-MCP Logo" width="150" height="150">

# 🤖 Claude Desktop 配置指南

让 Claude 使用 Doctah-MCP 查询明日方舟资料。

</div>

## 📋 前提条件

- 已安装 Claude Desktop
- 已安装 Python 3.8+
- Doctah-MCP 已从源码安装

## 🔧 安装

```bash
# 从源码安装
git clone https://github.com/mudrobot/doctah-mcp.git
cd doctah-mcp
pip install -e .

# 验证安装
python -m doctah_mcp.server --help
```

## 📁 配置文件位置

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

## ⚙️ 配置方法

### 方法1：全局命令（推荐，最简单）

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

### 方法2：Python 模块方式

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

### 方法3：完整路径（最可靠，需要指定工作目录）

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

> 💡 **关于 cwd**: 这是"当前工作目录"，只在方法3中需要。它应该指向你克隆的 doctah-mcp 项目文件夹的路径。

## �� 查找 Python 路径

- **Windows**: `where python`
- **macOS/Linux**: `which python3` 或 `which python`

## 🔄 重启 Claude Desktop

保存配置文件后，完全退出并重新启动 Claude Desktop。

## ✅ 验证

看到🔨图标表示已连接。试试：
- "查询银灰的技能信息"
- "找到所有医疗职业的干员"

## 🧯 故障排除

- **连接失败**: 检查 JSON 格式与路径是否正确，重新启动 Claude
- **命令不可用**: 使用完整 Python 路径
- **网络问题**: `curl -I https://prts.wiki` 测试连通性

---

更多问题可在 Issues 反馈：https://github.com/mudrobot/doctah-mcp/issues 