"""
Enhanced Network API Builder - Corporate Edition
Enterprise-grade network API builder for corporate environments
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
if readme_file.exists():
    with open(readme_file, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    long_description = "Enterprise-grade network API builder for corporate environments"

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, "r") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    requirements = [
        "requests>=2.28.0",
        "urllib3>=1.26.0", 
        "certifi>=2022.12.7",
        "PyYAML>=6.0",
        "cryptography>=3.4.8",
        "pyOpenSSL>=22.0.0",
        "PySocks>=1.7.1"
    ]

setup(
    name="enhanced-network-api-corporate",
    version="1.0.0",
    description="Enterprise network API builder with corporate SSL and proxy support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Enhanced Network API Team",
    author_email="support@enhanced-network-api.com",
    url="https://github.com/your-username/enhanced-network-api-corporate",
    project_urls={
        "Bug Reports": "https://github.com/your-username/enhanced-network-api-corporate/issues",
        "Source": "https://github.com/your-username/enhanced-network-api-corporate",
        "Documentation": "https://github.com/your-username/enhanced-network-api-corporate/docs",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "enhanced_network_api": [
            "enhanced_network_api_agent.yaml",
            "../api/*.json",
            "../api/*.md"
        ]
    },
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.910"
        ],
        "corporate": [
            "cryptography>=3.4.8",
            "pyOpenSSL>=22.0.0",
            "PySocks>=1.7.1"
        ],
        "airgapped": [
            "cryptography>=3.4.8",
            "pyOpenSSL>=22.0.0"
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Networking",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Security",
        "Environment :: Console",
        "Natural Language :: English"
    ],
    keywords=[
        "networking", "api", "corporate", "ssl", "proxy", 
        "zscaler", "firewall", "fortinet", "meraki", "cisco",
        "enterprise", "air-gapped", "security"
    ],
    entry_points={
        "console_scripts": [
            "enhanced-network-api=enhanced_network_api.enhanced_network_api_agent:main",
            "corporate-ssl-helper=enhanced_network_api.ssl_helper:main",
            "corporate-network-helper=enhanced_network_api.corporate_network_helper:main",
            "certificate-discovery=enhanced_network_api.certificate_discovery:main",
            "corporate-environment-detector=enhanced_network_api.corporate_environment_detector:main",
            "corporate-deployment-packager=enhanced_network_api.corporate_deployment_packager:main",
            "air-gapped-deployment=enhanced_network_api.air_gapped_deployment:main",
            "validate-corporate-compatibility=enhanced_network_api.validate_corporate_network_compatibility:main",
        ]
    },
    zip_safe=False,
    platforms=["any"]
)