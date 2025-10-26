"""Setup file for Code Safety Monitor package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme = Path(__file__).parent / "README.md"
long_description = readme.read_text() if readme.exists() else ""

setup(
    name="code-safety-monitor",
    version="1.0.0",
    description="DSPy-powered AI safety monitor for detecting backdoors in code",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="jmanhype",
    author_email="",
    url="https://github.com/jmanhype/multi-agent-system",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "dspy>=3.0.3",
        "control-arena>=8.0.0",
        "inspect-ai>=0.3.137",
        "openai>=1.0.0",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ],
        "viz": [
            "plotly>=5.0.0",
            "kaleido>=0.2.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "code-safety-monitor=code_safety_monitor.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Security",
    ],
    keywords="ai-safety backdoor-detection dspy gepa ai-control security",
)
