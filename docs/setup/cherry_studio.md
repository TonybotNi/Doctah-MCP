<div align="center">

<img src="../../assets/images/doctah-mcp-logo.png" alt="Doctah-MCP Logo" width="150" height="150">

# 🍒 Cherry Studio 集成指南

让 Cherry Studio 直接调用 Doctah-MCP。

</div>

## 📋 前提条件

- 已安装 Cherry Studio（最新版）
- 已安装 Python 3.8+
- 已从源码安装 Doctah-MCP

```bash
git clone https://github.com/mudrobot/doctah-mcp.git
cd doctah-mcp
pip install -e .
```

## ⚙️ 添加 MCP Server

1. 打开 Cherry Studio → Settings（设置）
2. 找到 MCP Servers（MCP 服务器） → Add（添加）
3. 选择 Type = STDIO（标准输入输出）

### 推荐配置（最简单）：
- **Command**: `doctah-mcp`
- **Args**: `[]`

### 备用配置（如果上面不工作）：
- **Command**: `/full/path/to/python`
- **Args**: `["-m", "doctah_mcp.server"]`
- **Cwd**: `/path/to/doctah-mcp-folder`

4. 保存并启用

> 💡 **关于 Cwd**: 这是工作目录，只在备用配置中需要，指向你下载的 doctah-mcp 项目文件夹

## ✅ 验证

- 聊天界面看到扳手图标（🔧）表示工具可用
- 测试查询：
  - "查询银灰的技能信息"
  - "搜索所有医疗职业的干员"

## 🧯 故障排除

- **无法启动**: 使用 Python 完整路径
- **无响应**: 确认 Cwd 指向项目根目录；重启 Cherry Studio
- **网络异常**: `curl -I https://prts.wiki` 测试连通性

---

有问题欢迎在 Issues 反馈：https://github.com/mudrobot/doctah-mcp/issues 