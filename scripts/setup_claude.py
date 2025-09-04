#!/usr/bin/env python3
"""
Doctah-MCP Claude Desktop 自动配置脚本
自动检测系统并配置Claude Desktop
"""

import json
import os
import platform
import subprocess
import sys
from pathlib import Path


def get_claude_config_path():
    """获取Claude Desktop配置文件路径"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library/Application Support/Claude/claude_desktop_config.json"
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        return Path(appdata) / "Claude/claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config/Claude/claude_desktop_config.json"
    else:
        raise OSError(f"不支持的操作系统: {system}")


def check_doctah_mcp_installed():
    """检查Doctah-MCP是否已安装"""
    try:
        result = subprocess.run(["pip", "show", "doctah-mcp"], 
                              capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError:
        return False, None


def get_doctah_mcp_command():
    """获取doctah-mcp命令的完整路径"""
    try:
        result = subprocess.run(["which", "doctah-mcp"], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # 如果which命令失败，尝试whereis
        try:
            result = subprocess.run(["whereis", "doctah-mcp"], 
                                  capture_output=True, text=True, check=True)
            # whereis返回 "doctah-mcp: /path/to/doctah-mcp"
            parts = result.stdout.strip().split(": ")
            if len(parts) > 1:
                return parts[1].split()[0]  # 取第一个路径
        except subprocess.CalledProcessError:
            pass
    
    # 如果都失败了，返回默认命令
    return "doctah-mcp"


def create_config(config_path, doctah_mcp_cmd):
    """创建或更新Claude Desktop配置"""
    config = {
        "mcpServers": {
            "doctah-mcp": {
                "command": doctah_mcp_cmd,
                "args": []
            }
        }
    }
    
    # 如果配置文件已存在，尝试合并配置
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
            
            # 合并mcpServers
            if "mcpServers" in existing_config:
                existing_config["mcpServers"]["doctah-mcp"] = config["mcpServers"]["doctah-mcp"]
                config = existing_config
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️  现有配置文件格式有问题，将创建新配置: {e}")
    
    # 创建目录（如果不存在）
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入配置
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    return config


def main():
    """主函数"""
    print("🤖 Doctah-MCP Claude Desktop 自动配置工具")
    print("=" * 50)
    
    # 检查Doctah-MCP是否已安装
    print("🔍 检查Doctah-MCP安装状态...")
    installed, info = check_doctah_mcp_installed()
    
    if not installed:
        print("❌ Doctah-MCP未安装")
        print("请先从源码安装Doctah-MCP:")
        print("   git clone https://github.com/mudrobot/doctah-mcp.git")
        print("   cd doctah-mcp")
        print("   pip install -e .")
        sys.exit(1)
    
    print("✅ Doctah-MCP已安装")
    
    # 获取配置文件路径
    print("\n📁 检测Claude Desktop配置路径...")
    try:
        config_path = get_claude_config_path()
        print(f"   配置路径: {config_path}")
    except OSError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # 获取命令路径
    print("\n🔧 获取doctah-mcp命令路径...")
    doctah_mcp_cmd = get_doctah_mcp_command()
    print(f"   命令路径: {doctah_mcp_cmd}")
    
    # 验证命令是否可用
    try:
        subprocess.run([doctah_mcp_cmd, "--help"], 
                      capture_output=True, check=True, timeout=10)
        print("✅ 命令验证成功")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  命令验证失败，但将继续配置")
    
    # 创建配置
    print(f"\n⚙️  配置Claude Desktop...")
    try:
        config = create_config(config_path, doctah_mcp_cmd)
        print(f"✅ 配置文件已创建/更新: {config_path}")
        
        print("\n📋 当前配置:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 配置失败: {e}")
        sys.exit(1)
    
    # 完成提示
    print("\n🎉 配置完成！")
    print("\n📌 下一步:")
    print("1. 完全退出Claude Desktop应用")
    print("2. 重新启动Claude Desktop")
    print("3. 查找🔨图标，确认MCP服务器已连接")
    print("4. 测试对话: '帮我查询银灰的技能信息'")
    
    print(f"\n💡 如果遇到问题，请查看详细配置指南:")
    print("   CLAUDE_DESKTOP_SETUP.md")


if __name__ == "__main__":
    main() 