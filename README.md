# 📋 ChangeLog - Automated Changelog Generator

> **Transform your git history into professional changelogs with one command.**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/DonkRonk17/ChangeLog)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.7+-yellow.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-72%20passing-brightgreen.svg)](test_changelog.py)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-orange.svg)](requirements.txt)

---

## 📖 Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
  - [CLI Usage](#cli-usage)
  - [Python API](#python-api)
- [Commands](#-commands)
  - [generate](#generate)
  - [preview](#preview)
  - [validate](#validate)
  - [stats](#stats)
- [Configuration](#-configuration)
- [Output Formats](#-output-formats)
- [Commit Categorization](#-commit-categorization)
- [How It Works](#-how-it-works)
- [Real-World Results](#-real-world-results)
- [Advanced Features](#-advanced-features)
- [Use Cases](#-use-cases)
- [Integration](#-integration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)
- [Credits](#-credits)

---

## 🚨 The Problem

Every professional GitHub repository needs a changelog. But creating and maintaining one manually is:

- **Tedious** - Manually copying commit messages, formatting them, categorizing changes
- **Inconsistent** - Different projects use different formats, making portfolios look unprofessional
- **Forgotten** - Changelogs fall out of date because nobody remembers to update them
- **Time-consuming** - What should take 30 seconds takes 15-30 minutes per release

**Real impact:** 80+ tools in the Team Brain ecosystem, NONE had professional changelogs.

---

## ✅ The Solution

ChangeLog parses your git history and generates a professional, categorized CHANGELOG.md in seconds:

```bash
# One command. That's it.
python changelog.py generate

# Output: CHANGELOG.md with categorized changes, version groups, and commit links
```

**Result:** Professional changelog in <2 seconds, following industry standards.

---

## ✨ Features

- 🔍 **Smart Categorization** - Automatically categorizes commits (Added, Fixed, Changed, etc.)
- 📐 **Conventional Commits** - Full support for `feat:`, `fix:`, `docs:` prefixes
- 🏷️ **Version Grouping** - Groups by semver tags or dates automatically
- 📝 **Multiple Formats** - Markdown, plain text, and JSON output
- 🔗 **GitHub Links** - Auto-generates commit links from remote URL
- ✅ **Commit Validation** - Check compliance with Conventional Commits spec
- 📊 **Statistics** - Category breakdowns, author stats, compliance scores
- ⚙️ **Configurable** - JSON config files, CLI flags, or Python API
- 🐍 **Python API** - Use programmatically from any Python script
- 🚫 **Zero Dependencies** - Pure Python standard library (no pip install needed)
- 🖥️ **Cross-Platform** - Works on Windows, Linux, and macOS
- 🎯 **ASCII-Safe** - No Unicode characters in code output (Windows compatible)

---

## 🚀 Quick Start

### Method 1: Direct Use (Recommended)

```bash
# Navigate to any git repository
cd /path/to/your/project

# Generate changelog
python /path/to/changelog.py generate

# That's it! Check CHANGELOG.md
```

### Method 2: Copy to Project

```bash
# Copy changelog.py to your project
cp /path/to/changelog.py ./

# Run it
python changelog.py generate
```

### Method 3: From Source

```bash
git clone https://github.com/DonkRonk17/ChangeLog.git
cd ChangeLog
python changelog.py generate /path/to/your/repo
```

**First run output:**
```
[OK] Changelog generated: CHANGELOG.md (87 lines)
```

---

## 📦 Installation

### Prerequisites

- **Python 3.7+** (standard library only - no pip install needed)
- **Git** installed and in PATH

### Install

```bash
# Clone the repository
git clone https://github.com/DonkRonk17/ChangeLog.git

# Or install as a package
cd ChangeLog
pip install -e .
```

### Verify Installation

```bash
python changelog.py --version
# Output: changelog 1.0.0 (Team Brain)
```

---

## 📖 Usage

### CLI Usage

```bash
# Generate changelog for current directory
python changelog.py generate

# Generate for a specific repository
python changelog.py generate /path/to/repo

# Custom output filename
python changelog.py generate -o CHANGES.md

# JSON format
python changelog.py generate --format json

# Preview without writing file
python changelog.py preview

# Include author names
python changelog.py generate --with-author

# Filter by date range
python changelog.py generate --since 2026-01-01 --until 2026-02-01

# Limit to last 50 commits
python changelog.py generate --limit 50

# Print to stdout instead of file
python changelog.py generate --stdout
```

### Python API

```python
from changelog import ChangeLog

# Basic usage
cl = ChangeLog(repo_path="/path/to/repo")
output = cl.generate()
print(output)

# Write to file
cl.generate(output_file="CHANGELOG.md")

# With configuration
cl = ChangeLog(
    repo_path=".",
    config={
        "output_format": "markdown",
        "include_author": True,
        "include_hash": True,
        "limit": 100,
    }
)
output = cl.generate()

# Validate commit messages
results = cl.validate_commits()
print(f"Compliance: {results['compliance_pct']}%")

# Get statistics
stats = cl.get_stats()
print(f"Total commits: {stats['total_commits']}")
print(f"Categories: {stats['categories']}")
```

---

## 🔧 Commands

### generate

Generate a changelog from git history.

```bash
python changelog.py generate [path] [options]
```

**Options:**

| Flag | Description | Default |
|------|-------------|---------|
| `-o, --output` | Output filename | `CHANGELOG.md` |
| `--format` | Output format (`markdown`, `text`, `json`) | `markdown` |
| `--group-by` | Grouping strategy (`auto`, `tags`, `dates`) | `auto` |
| `--no-hash` | Omit commit hashes | `False` |
| `--with-author` | Include author names | `False` |
| `--with-date` | Include commit dates | `False` |
| `--since` | Start date filter | (none) |
| `--until` | End date filter | (none) |
| `--author` | Filter by author name | (none) |
| `--limit` | Maximum commits (0=unlimited) | `0` |
| `--header` | Custom header text | `# Changelog` |
| `--reverse` | Reverse version order | `False` |
| `--config` | Path to config file | (none) |
| `--stdout` | Print to stdout | `False` |

### preview

Preview changelog output without writing to file.

```bash
python changelog.py preview [path] [--format markdown|text|json] [--limit 50]
```

### validate

Check commit message compliance with Conventional Commits.

```bash
python changelog.py validate [path] [--limit 100] [--json]
```

**Output example:**
```
==============================================================
  COMMIT MESSAGE VALIDATION
==============================================================
  Total Commits:       142
  Conventional:        98
  Non-conventional:    44
  Compliance:          69.0%

  By Type:
    feat              42
    fix               28
    docs              15
    refactor          8
    test              5

  Grade: C - Fair
==============================================================
```

### stats

Show commit statistics and category breakdowns.

```bash
python changelog.py stats [path] [--limit 0] [--json]
```

**Output example:**
```
============================================================
  CHANGELOG STATISTICS: MyProject
============================================================
  Total Commits: 142
  Total Tags:    5
  Date Range:    2026-01-15 to 2026-02-07

  Categories:
    Added              42  ##########################################
    Fixed              28  ############################
    Changed            22  ######################
    Documentation      15  ###############
    Other              18  ##################
    Testing            12  ############
    Build               5  #####

  Top Authors:
    Logan Smith                        87 commits
    ATLAS                              32 commits
    CLIO                               23 commits

  Recent Tags:
    v1.2.0
    v1.1.0
    v1.0.0

============================================================
```

---

## ⚙️ Configuration

### Config File (`.changelogrc`)

Create a `.changelogrc` file in your project root:

```json
{
  "output_file": "CHANGELOG.md",
  "output_format": "markdown",
  "header": "# Changelog",
  "description": "All notable changes documented here.",
  "unreleased_label": "Unreleased",
  "group_by": "auto",
  "date_format": "%Y-%m-%d",
  "include_hash": true,
  "include_author": false,
  "include_date": false,
  "exclude_patterns": [
    "^Merge (branch|pull request)",
    "^WIP\\b",
    "^wip\\b"
  ],
  "limit": 0,
  "reverse": false
}
```

### Using Config File

```bash
python changelog.py generate --config .changelogrc
```

### Python API Config

```python
cl = ChangeLog(
    repo_path=".",
    config_file=".changelogrc"  # Load from file
)

# Or pass config dict directly
cl = ChangeLog(
    repo_path=".",
    config={"include_author": True, "limit": 50}
)
```

---

## 📄 Output Formats

### Markdown (Default)

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [v1.2.0] - 2026-02-07

### Added

- Add dark mode support (`abc1234`)
- Implement user preferences API (`def5678`)

### Fixed

- Resolve login timeout issue (`ghi9012`)

### Changed

- Improve database query performance (`jkl3456`)

---

*Generated by ChangeLog v1.0.0*
```

### Plain Text

```
======================================================================
CHANGELOG
======================================================================

  v1.2.0 (2026-02-07)
----------------------------------------------------------------------
  [Added]
    * Add dark mode support (abc1234)
    * Implement user preferences API (def5678)

  [Fixed]
    * Resolve login timeout issue (ghi9012)

======================================================================
Generated by ChangeLog v1.0.0
======================================================================
```

### JSON

```json
{
  "generator": "ChangeLog v1.0.0",
  "generated_at": "2026-02-07T10:30:00",
  "versions": [
    {
      "label": "v1.2.0",
      "date": "2026-02-07",
      "commit_count": 4,
      "categories": {
        "Added": [
          {
            "hash": "abc1234...",
            "description": "Add dark mode support"
          }
        ]
      }
    }
  ]
}
```

---

## 🏷️ Commit Categorization

ChangeLog uses a two-tier categorization strategy:

### Tier 1: Conventional Commits (Preferred)

If your commits follow the [Conventional Commits](https://conventionalcommits.org) format:

| Prefix | Category | Example |
|--------|----------|---------|
| `feat:` | Added | `feat: add search functionality` |
| `fix:` | Fixed | `fix: resolve null pointer error` |
| `docs:` | Documentation | `docs: update API reference` |
| `refactor:` | Changed | `refactor: extract validation logic` |
| `test:` | Testing | `test: add integration tests` |
| `build:` | Build | `build: update CI pipeline` |
| `security:` | Security | `security: patch XSS vulnerability` |
| `deprecate:` | Deprecated | `deprecate: mark old API as deprecated` |
| `remove:` | Removed | `remove: drop legacy endpoints` |
| `chore:` | Other | `chore: update dependencies` |

### Tier 2: Keyword Fallback

For non-conventional commits, ChangeLog analyzes the message:

| Keywords | Category |
|----------|----------|
| add, new, create, implement | Added |
| fix, resolve, repair, patch | Fixed |
| update, modify, improve, enhance | Changed |
| remove, delete, drop | Removed |
| security, vulnerability | Security |
| readme, documentation | Documentation |
| test, spec, coverage | Testing |
| build, ci, deploy | Build |
| *(no match)* | Other |

---

## 🔬 How It Works

```
1. GitParser reads git log and tag data via subprocess
2. CommitCategorizer classifies each commit using regex patterns
3. VersionGrouper groups commits by semver tags (or dates if no tags)
4. Formatter renders the grouped data as Markdown/Text/JSON
5. Output written to file or stdout
```

**Architecture:**
- `GitParser` - Executes git commands, parses output into Commit objects
- `CommitCategorizer` - Classifies commits using Conventional Commits + keyword fallback
- `VersionGrouper` - Groups commits by version tags or date periods
- `MarkdownFormatter` / `TextFormatter` / `JSONFormatter` - Render output
- `ChangeLog` - Orchestrates the pipeline, provides Python API
- `main()` - CLI entry point with argparse

---

## 📊 Real-World Results

### Before ChangeLog
- 80+ Team Brain tools with **zero** changelogs
- New contributors had no way to see project history at a glance
- Release notes were written manually (or not at all)

### After ChangeLog
- Professional changelogs generated in **<2 seconds** per project
- Consistent format across the entire portfolio
- Commit compliance validation helps improve commit message quality
- Statistics reveal project health at a glance

---

## 🔥 Advanced Features

### Exclude Patterns

Filter out noise (merge commits, WIP, etc.):

```bash
# Default excludes: Merge commits, WIP
python changelog.py generate

# Custom excludes in .changelogrc
{
  "exclude_patterns": [
    "^Merge",
    "^WIP",
    "^Revert",
    "^Auto-generated"
  ]
}
```

### Date Filtering

```bash
# Commits since January 2026
python changelog.py generate --since 2026-01-01

# Commits in a specific range
python changelog.py generate --since 2026-01-01 --until 2026-02-01
```

### Author Filtering

```bash
# Only commits by a specific author
python changelog.py generate --author "Logan Smith"
```

### Breaking Changes

Conventional Commits with `!` are flagged:
```
feat!: remove deprecated login API
```
Renders as:
```markdown
- **BREAKING:** remove deprecated login API (`abc1234`)
```

### Scoped Commits

```
feat(cli): add --verbose flag
fix(parser): handle empty input
```
Renders as:
```markdown
- add --verbose flag **(cli)** (`abc1234`)
- handle empty input **(parser)** (`def5678`)
```

---

## 🎯 Use Cases

### 1. Single Project Changelog

```bash
cd my-project
python /path/to/changelog.py generate
```

### 2. Portfolio-Wide Changelogs

```bash
for dir in AutoProjects/*/; do
  if [ -d "$dir/.git" ]; then
    python changelog.py generate "$dir"
  fi
done
```

### 3. Release Notes

```bash
# Only changes since last release
python changelog.py generate --since v1.0.0 --stdout > RELEASE_NOTES.md
```

### 4. Commit Quality Check

```bash
python changelog.py validate
# Grade: C - Fair (69.0% compliance)
# Tip: Use feat:/fix:/docs: prefixes to improve!
```

### 5. Team Productivity Analysis

```bash
python changelog.py stats --json > stats.json
# Analyze commit patterns, author contributions, category breakdowns
```

---

## 🔗 Integration

### With Team Brain Tools

```python
from changelog import ChangeLog

# Generate changelog for any Team Brain tool
cl = ChangeLog(repo_path="C:/Users/logan/OneDrive/Documents/AutoProjects/TimeSync")
output = cl.generate(output_file="CHANGELOG.md")
```

### With CI/CD

```yaml
# GitHub Actions example
- name: Generate Changelog
  run: python changelog.py generate --stdout > CHANGELOG.md

- name: Commit Changelog
  run: |
    git add CHANGELOG.md
    git commit -m "docs: update changelog"
```

See [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) for full integration documentation.

---

## 🔧 Troubleshooting

### "Git is not installed or not in PATH"

```bash
# Install git
# Windows: https://git-scm.com/download/win
# Linux: sudo apt install git
# macOS: brew install git

# Verify
git --version
```

### "Not a git repository"

```bash
# Make sure you're in a git repo
git status

# Or specify the path
python changelog.py generate /path/to/git/repo
```

### Empty changelog generated

- Check that the repository has commits: `git log --oneline`
- Check exclude patterns aren't filtering everything
- Try `--limit 0` to include all commits

### Unicode errors on Windows

ChangeLog uses ASCII-safe output by default. If you see encoding errors:
```bash
# Set UTF-8 console
chcp 65001
python changelog.py generate
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Use Conventional Commits: `git commit -m "feat: add my feature"`
4. Run tests: `python test_changelog.py`
5. Submit a pull request

### Code Standards

- Type hints on all functions
- Docstrings for all public methods
- No Unicode emojis in Python code (ASCII-safe)
- All tests must pass (72/72)

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 📝 Credits

**Built by:** ATLAS (Team Brain)
**For:** Logan Smith / Metaphy LLC
**Part of:** Beacon HQ / Team Brain Ecosystem
**Date:** February 7, 2026
**Tool #:** 82 in the AutoProjects collection

**Standards:**
- [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
- [Conventional Commits](https://conventionalcommits.org/en/v1.0.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

**Special Thanks:**
- Logan Smith for the vision of professional-grade tooling
- The Team Brain collective for building 80+ tools that need changelogs
- The Keep a Changelog and Conventional Commits communities

---

**For the Maximum Benefit of Life.**
**One World. One Family. One Love.**
