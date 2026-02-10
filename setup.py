#!/usr/bin/env python3
"""Setup script for ChangeLog."""

from pathlib import Path
from setuptools import setup

# Read README for long description
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

setup(
    name='changelog-generator',
    version='1.0.0',
    description='Automated CHANGELOG.md generator from git commit history',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='ATLAS (Team Brain)',
    author_email='metaphy@metaphy.com',
    url='https://github.com/DonkRonk17/ChangeLog',
    py_modules=['changelog'],
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'changelog=changelog:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Version Control :: Git',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='changelog git version-control keepachangelog semantic-versioning',
)
