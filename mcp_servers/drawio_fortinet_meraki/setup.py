#!/usr/bin/env python3
"""
Setup script for DrawIO Fortinet/Meraki MCP Server
"""

from setuptools import setup, find_packages
import os

# Read requirements
with open("requirements.txt", "r") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="drawio-fortinet-meraki-mcp",
    version="1.0.0",
    description="MCP Server for DrawIO integration with FortiManager and Meraki APIs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Enhanced Network API Team",
    author_email="team@enhanced-network-api.com",
    url="https://github.com/enhanced-network-api/drawio-fortinet-meraki-mcp",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Networking",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="mcp drawio fortinet meraki network topology diagram",
    entry_points={
        "console_scripts": [
            "drawio-fortinet-meraki-mcp=mcp_server:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/enhanced-network-api/drawio-fortinet-meraki-mcp/issues",
        "Source": "https://github.com/enhanced-network-api/drawio-fortinet-meraki-mcp",
        "Documentation": "https://github.com/enhanced-network-api/drawio-fortinet-meraki-mcp/wiki",
    },
)
