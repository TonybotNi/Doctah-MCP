#!/usr/bin/env python3
"""
Doctah-MCP 安装脚本
明日方舟PRTS.wiki智能助手 - MCP服务器
"""

from setuptools import setup, find_packages
import pathlib

# 当前目录
HERE = pathlib.Path(__file__).parent

# README内容
README = (HERE / "README.md").read_text(encoding="utf-8") if (HERE / "README.md").exists() else ""

# 版本信息
VERSION = "1.0.0"

setup(
    name="doctah-mcp",
    version=VERSION,
    description="明日方舟PRTS.wiki智能助手 - MCP服务器",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/mudrobot/doctah-mcp",
    author="Mudrobot",
    author_email="mudrobot@example.com",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Games/Entertainment",
    ],
    keywords="arknights prts wiki mcp ai assistant 明日方舟",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "mcp>=1.0.0",
        "httpx>=0.25.0", 
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "pydantic>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0",
            "isort>=5.10",
            "flake8>=4.0",
            "mypy>=1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "doctah-mcp=doctah_mcp.server:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 