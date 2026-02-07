#!/usr/bin/env python3
"""Setup script for ChangeLog - Automated Changelog Generator."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="changelog-generator",
    version="1.0.0",
    author="ATLAS (Team Brain)",
    author_email="logan@metaphy.com",
    description="Automated Changelog Generator - Transform git history into professional changelogs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DonkRonk17/ChangeLog",
    py_modules=["changelog"],
    python_requires=">=3.7",
    install_requires=[],  # Zero dependencies
    entry_points={
        "console_scripts": [
            "changelog=changelog:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Documentation",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    keywords="changelog, git, conventional-commits, keep-a-changelog, release-notes",
    project_urls={
        "Bug Reports": "https://github.com/DonkRonk17/ChangeLog/issues",
        "Source": "https://github.com/DonkRonk17/ChangeLog",
    },
)
