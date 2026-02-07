#!/usr/bin/env python3
"""
ChangeLog - Automated Changelog Generator

Parses git commit history and generates professional CHANGELOG.md files
following the Keep a Changelog (https://keepachangelog.com) and
Conventional Commits (https://conventionalcommits.org) standards.

Supports version tag grouping, date-based grouping, commit categorization,
multiple output formats, and both CLI and Python API usage. Zero external
dependencies - uses Python standard library only.

Author: ATLAS (Team Brain)
For: Logan Smith / Metaphy LLC
Version: 1.0.0
Date: February 7, 2026
License: MIT
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ==============================================================================
# Constants
# ==============================================================================

VERSION = "1.0.0"
TOOL_NAME = "ChangeLog"

# Conventional Commits prefix -> Keep a Changelog category mapping
CONVENTIONAL_COMMITS_MAP = {
    "feat": "Added",
    "feature": "Added",
    "add": "Added",
    "new": "Added",
    "fix": "Fixed",
    "bugfix": "Fixed",
    "hotfix": "Fixed",
    "patch": "Fixed",
    "docs": "Documentation",
    "doc": "Documentation",
    "refactor": "Changed",
    "change": "Changed",
    "update": "Changed",
    "improve": "Changed",
    "enhance": "Changed",
    "deprecate": "Deprecated",
    "deprecated": "Deprecated",
    "remove": "Removed",
    "delete": "Removed",
    "drop": "Removed",
    "security": "Security",
    "vuln": "Security",
    "test": "Testing",
    "tests": "Testing",
    "spec": "Testing",
    "build": "Build",
    "ci": "Build",
    "deploy": "Build",
    "release": "Build",
    "chore": "Other",
    "style": "Other",
    "perf": "Changed",
    "revert": "Changed",
    "merge": "Other",
    "wip": "Other",
}

# Keep a Changelog category order
CATEGORY_ORDER = [
    "Added",
    "Changed",
    "Deprecated",
    "Removed",
    "Fixed",
    "Security",
    "Documentation",
    "Testing",
    "Build",
    "Other",
]

# Default patterns to exclude from changelog
DEFAULT_EXCLUDE_PATTERNS = [
    r"^Merge (branch|pull request|remote)",
    r"^WIP\b",
    r"^wip\b",
    r"^$",
]

# Git log format: hash|author|date|subject|refs
GIT_LOG_FORMAT = "%H|%an|%aI|%s|%D"

# Regex for Conventional Commits: type(scope): description
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)"       # type (feat, fix, etc.)
    r"(?:\((?P<scope>[^)]+)\))?"  # optional scope
    r"(?P<breaking>!)?"           # optional breaking change indicator
    r":\s*"                       # colon + space
    r"(?P<description>.+)$"       # description
)

# Regex for semantic version tags
SEMVER_RE = re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:-(?P<prerelease>[a-zA-Z0-9.]+))?"
    r"(?:\+(?P<build>[a-zA-Z0-9.]+))?$"
)


# ==============================================================================
# Data Classes
# ==============================================================================

@dataclass
class Commit:
    """Represents a single git commit."""
    hash: str
    author: str
    date: str
    message: str
    refs: str = ""
    category: str = "Other"
    scope: str = ""
    description: str = ""
    is_breaking: bool = False

    @property
    def short_hash(self) -> str:
        """Return first 7 characters of commit hash."""
        return self.hash[:7]

    @property
    def date_obj(self) -> datetime:
        """Parse date string to datetime object."""
        try:
            # Handle ISO format with timezone
            date_str = self.date
            if "+" in date_str or date_str.endswith("Z"):
                # Remove timezone offset for simple parsing
                date_str = re.sub(r"[+-]\d{2}:\d{2}$", "", date_str)
                date_str = date_str.replace("Z", "")
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return datetime.now()

    @property
    def date_formatted(self) -> str:
        """Return date in YYYY-MM-DD format."""
        return self.date_obj.strftime("%Y-%m-%d")

    @property
    def month_key(self) -> str:
        """Return YYYY-MM for monthly grouping."""
        return self.date_obj.strftime("%Y-%m")


@dataclass
class VersionGroup:
    """Represents a group of commits for a version or date period."""
    label: str
    date: str = ""
    commits: List[Commit] = field(default_factory=list)
    tag: str = ""

    @property
    def categories(self) -> Dict[str, List[Commit]]:
        """Group commits by category, maintaining order."""
        result = OrderedDict()
        for cat in CATEGORY_ORDER:
            cat_commits = [c for c in self.commits if c.category == cat]
            if cat_commits:
                result[cat] = cat_commits
        return result

    @property
    def commit_count(self) -> int:
        """Total number of commits in this version group."""
        return len(self.commits)


@dataclass
class ChangelogConfig:
    """Configuration for changelog generation."""
    repo_path: str = "."
    output_file: str = "CHANGELOG.md"
    output_format: str = "markdown"
    header: str = "# Changelog"
    description: str = (
        "All notable changes to this project will be documented in this file.\n\n"
        "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),\n"
        "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    )
    unreleased_label: str = "Unreleased"
    group_by: str = "auto"  # "tags", "dates", "auto"
    date_format: str = "%Y-%m-%d"
    exclude_patterns: List[str] = field(default_factory=lambda: list(DEFAULT_EXCLUDE_PATTERNS))
    include_hash: bool = True
    include_author: bool = False
    include_date: bool = False
    limit: int = 0  # 0 = no limit
    since: str = ""
    until: str = ""
    author_filter: str = ""
    reverse: bool = False

    @classmethod
    def from_file(cls, config_path: Path) -> "ChangelogConfig":
        """Load config from JSON file."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            config = cls()
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            return config
        except (FileNotFoundError, json.JSONDecodeError):
            return cls()

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return asdict(self)


# ==============================================================================
# Git Operations
# ==============================================================================

class GitParser:
    """Parse git repository data using subprocess."""

    def __init__(self, repo_path: str = "."):
        """
        Initialize GitParser with repository path.

        Args:
            repo_path: Path to the git repository root.

        Raises:
            FileNotFoundError: If git is not installed.
            ValueError: If path is not a git repository.
        """
        self.repo_path = Path(repo_path).resolve()
        self._validate_git()
        self._validate_repo()

    def _validate_git(self) -> None:
        """Check that git is installed and accessible."""
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                raise FileNotFoundError("git command failed")
        except FileNotFoundError:
            raise FileNotFoundError(
                "Git is not installed or not in PATH.\n"
                "Install git: https://git-scm.com/downloads"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Git command timed out")

    def _validate_repo(self) -> None:
        """Check that the path is a valid git repository."""
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            # Also check if it's inside a git repo
            result = self._run_git(["rev-parse", "--git-dir"], check=False)
            if result.returncode != 0:
                raise ValueError(
                    f"Not a git repository: {self.repo_path}\n"
                    f"Run 'git init' to initialize a repository."
                )

    def _run_git(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """
        Execute a git command in the repository.

        Args:
            args: Git command arguments (without 'git' prefix).
            check: Whether to raise on non-zero exit.

        Returns:
            CompletedProcess with stdout/stderr.
        """
        cmd = ["git"] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.repo_path),
                timeout=60,
                encoding="utf-8",
                errors="replace",
            )
            if check and result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, cmd, result.stdout, result.stderr
                )
            return result
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Git command timed out: {' '.join(cmd)}")

    def get_commits(
        self,
        since: str = "",
        until: str = "",
        author: str = "",
        limit: int = 0,
    ) -> List[Commit]:
        """
        Get commits from the repository.

        Args:
            since: Start date (ISO format or relative like '2 weeks ago').
            until: End date (ISO format or relative).
            author: Filter by author name/email.
            limit: Maximum number of commits (0 = unlimited).

        Returns:
            List of Commit objects, newest first.
        """
        args = ["log", f"--format={GIT_LOG_FORMAT}"]

        if since:
            args.append(f"--since={since}")
        if until:
            args.append(f"--until={until}")
        if author:
            args.append(f"--author={author}")
        if limit > 0:
            args.append(f"-n{limit}")

        result = self._run_git(args, check=False)
        if result.returncode != 0:
            return []

        commits = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 4)
            if len(parts) >= 4:
                commit = Commit(
                    hash=parts[0].strip(),
                    author=parts[1].strip(),
                    date=parts[2].strip(),
                    message=parts[3].strip(),
                    refs=parts[4].strip() if len(parts) > 4 else "",
                )
                commits.append(commit)

        return commits

    def get_tags(self) -> List[Tuple[str, str, str]]:
        """
        Get all tags with their commit hashes and dates.

        Returns:
            List of (tag_name, commit_hash, date) tuples, sorted by date.
        """
        result = self._run_git(
            ["tag", "-l", "--sort=-version:refname",
             "--format=%(refname:short)|%(objectname:short)|%(creatordate:iso)"],
            check=False,
        )
        if result.returncode != 0 or not result.stdout.strip():
            return []

        tags = []
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|", 2)
            if len(parts) >= 2:
                tag_name = parts[0].strip()
                commit_hash = parts[1].strip()
                date = parts[2].strip() if len(parts) > 2 else ""
                tags.append((tag_name, commit_hash, date))

        return tags

    def get_repo_name(self) -> str:
        """Get the repository name from the remote URL or directory name."""
        result = self._run_git(["remote", "get-url", "origin"], check=False)
        if result.returncode == 0 and result.stdout.strip():
            url = result.stdout.strip()
            # Extract repo name from URL
            name = url.rstrip("/").split("/")[-1]
            name = name.replace(".git", "")
            return name
        return self.repo_path.name

    def get_remote_url(self) -> str:
        """Get the remote origin URL."""
        result = self._run_git(["remote", "get-url", "origin"], check=False)
        if result.returncode == 0:
            return result.stdout.strip()
        return ""

    def get_commit_count(self) -> int:
        """Get total number of commits in the repository."""
        result = self._run_git(["rev-list", "--count", "HEAD"], check=False)
        if result.returncode == 0:
            try:
                return int(result.stdout.strip())
            except ValueError:
                pass
        return 0


# ==============================================================================
# Commit Categorization
# ==============================================================================

class CommitCategorizer:
    """Categorize commits using Conventional Commits and keyword matching."""

    def __init__(self, custom_rules: Optional[Dict[str, str]] = None):
        """
        Initialize categorizer.

        Args:
            custom_rules: Optional dict of prefix -> category overrides.
        """
        self.rules = dict(CONVENTIONAL_COMMITS_MAP)
        if custom_rules:
            self.rules.update(custom_rules)

    def categorize(self, commit: Commit) -> Commit:
        """
        Categorize a single commit by analyzing its message.

        Args:
            commit: Commit object to categorize.

        Returns:
            Same commit with category, scope, description, is_breaking set.
        """
        message = commit.message.strip()

        # Try Conventional Commits format first
        match = CONVENTIONAL_RE.match(message)
        if match:
            commit_type = match.group("type").lower()
            commit.scope = match.group("scope") or ""
            commit.description = match.group("description").strip()
            commit.is_breaking = bool(match.group("breaking"))

            if commit_type in self.rules:
                commit.category = self.rules[commit_type]
            else:
                commit.category = "Other"

            return commit

        # Fallback: keyword matching on the full message
        message_lower = message.lower()

        # Check for category keywords in message
        keyword_map = {
            "Added": ["add ", "added ", "new ", "create ", "implement ", "introduce "],
            "Fixed": ["fix ", "fixed ", "resolve ", "resolved ", "repair ", "patch "],
            "Changed": ["update ", "updated ", "change ", "changed ", "modify ",
                        "improve ", "improved ", "enhance ", "enhanced ", "refactor "],
            "Removed": ["remove ", "removed ", "delete ", "deleted ", "drop "],
            "Deprecated": ["deprecate ", "deprecated "],
            "Security": ["security ", "vulnerability ", "cve-"],
            "Documentation": ["readme", "documentation", " docs ", "doc: "],
            "Testing": ["test ", "tests ", "testing ", "spec "],
            "Build": ["build ", "ci ", "deploy ", "release "],
        }

        for category, keywords in keyword_map.items():
            for keyword in keywords:
                if message_lower.startswith(keyword) or (
                    f" {keyword}" in f" {message_lower}"
                    and message_lower.find(keyword) < 20
                ):
                    commit.category = category
                    commit.description = message
                    return commit

        # Default: Other
        commit.category = "Other"
        commit.description = message
        return commit

    def categorize_all(self, commits: List[Commit]) -> List[Commit]:
        """
        Categorize all commits.

        Args:
            commits: List of commits to categorize.

        Returns:
            Same list with categories applied.
        """
        for commit in commits:
            self.categorize(commit)
        return commits


# ==============================================================================
# Version Grouping
# ==============================================================================

class VersionGrouper:
    """Group commits by version tags or date periods."""

    def __init__(self, config: ChangelogConfig):
        """
        Initialize grouper with configuration.

        Args:
            config: Changelog configuration.
        """
        self.config = config

    def group_by_tags(
        self, commits: List[Commit], tags: List[Tuple[str, str, str]]
    ) -> List[VersionGroup]:
        """
        Group commits by version tags.

        Args:
            commits: List of commits (newest first).
            tags: List of (tag_name, commit_hash, date) tuples.

        Returns:
            List of VersionGroup objects.
        """
        if not tags:
            return self._group_as_unreleased(commits)

        # Build tag lookup by commit hash
        tag_hashes = {tag[1]: (tag[0], tag[2]) for tag in tags}

        groups = []
        current_label = self.config.unreleased_label
        current_date = ""
        current_commits = []

        for commit in commits:
            short = commit.short_hash
            if short in tag_hashes:
                # Save current group if it has commits
                if current_commits:
                    groups.append(VersionGroup(
                        label=current_label,
                        date=current_date,
                        commits=list(current_commits),
                        tag=current_label if current_label != self.config.unreleased_label else "",
                    ))
                    current_commits = []

                # Start new group with this tag
                tag_name, tag_date = tag_hashes[short]
                current_label = tag_name
                current_date = self._format_tag_date(tag_date)

            current_commits.append(commit)

        # Don't forget the last group
        if current_commits:
            groups.append(VersionGroup(
                label=current_label,
                date=current_date,
                commits=list(current_commits),
                tag=current_label if current_label != self.config.unreleased_label else "",
            ))

        return groups

    def group_by_dates(self, commits: List[Commit]) -> List[VersionGroup]:
        """
        Group commits by month.

        Args:
            commits: List of commits (newest first).

        Returns:
            List of VersionGroup objects, one per month.
        """
        if not commits:
            return []

        month_groups = OrderedDict()
        for commit in commits:
            key = commit.month_key
            if key not in month_groups:
                month_groups[key] = []
            month_groups[key].append(commit)

        groups = []
        for month_key, month_commits in month_groups.items():
            try:
                dt = datetime.strptime(month_key, "%Y-%m")
                label = dt.strftime("%B %Y")
                date = dt.strftime("%Y-%m-01")
            except ValueError:
                label = month_key
                date = ""

            groups.append(VersionGroup(
                label=label,
                date=date,
                commits=month_commits,
            ))

        return groups

    def group_auto(
        self, commits: List[Commit], tags: List[Tuple[str, str, str]]
    ) -> List[VersionGroup]:
        """
        Automatically choose grouping strategy.

        Uses tags if available with semver format, otherwise dates.

        Args:
            commits: List of commits.
            tags: List of tags.

        Returns:
            List of VersionGroup objects.
        """
        # Check if we have semver-like tags
        semver_tags = [t for t in tags if SEMVER_RE.match(t[0])]
        if semver_tags:
            return self.group_by_tags(commits, semver_tags)
        elif tags:
            return self.group_by_tags(commits, tags)
        else:
            return self.group_by_dates(commits)

    def _group_as_unreleased(self, commits: List[Commit]) -> List[VersionGroup]:
        """Group all commits as unreleased."""
        if not commits:
            return []
        return [VersionGroup(
            label=self.config.unreleased_label,
            date=datetime.now().strftime(self.config.date_format),
            commits=commits,
        )]

    def _format_tag_date(self, date_str: str) -> str:
        """Format a tag date string."""
        if not date_str:
            return ""
        try:
            # Parse various date formats
            for fmt in ["%Y-%m-%d %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"]:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.strftime(self.config.date_format)
                except ValueError:
                    continue
            # Try ISO format
            clean = re.sub(r"[+-]\d{2}:\d{2}$", "", date_str.strip())
            clean = clean.replace("Z", "").strip()
            dt = datetime.fromisoformat(clean)
            return dt.strftime(self.config.date_format)
        except (ValueError, TypeError):
            return date_str.strip()


# ==============================================================================
# Formatters
# ==============================================================================

class MarkdownFormatter:
    """Generate Markdown-formatted changelog."""

    def __init__(self, config: ChangelogConfig):
        """Initialize with config."""
        self.config = config

    def format(self, groups: List[VersionGroup], repo_url: str = "") -> str:
        """
        Format version groups as Markdown.

        Args:
            groups: List of VersionGroup objects.
            repo_url: Optional repository URL for commit links.

        Returns:
            Formatted Markdown string.
        """
        lines = []

        # Header
        lines.append(self.config.header)
        lines.append("")
        lines.append(self.config.description)
        lines.append("")

        # Format GitHub URL for commit links
        github_url = ""
        if repo_url:
            github_url = repo_url.rstrip("/")
            if github_url.endswith(".git"):
                github_url = github_url[:-4]
            # Convert SSH to HTTPS if needed
            if github_url.startswith("git@"):
                github_url = github_url.replace(":", "/").replace("git@", "https://")

        for group in groups:
            # Version header
            date_str = f" - {group.date}" if group.date else ""
            lines.append(f"## [{group.label}]{date_str}")
            lines.append("")

            categories = group.categories
            if not categories:
                lines.append("_No categorized changes._")
                lines.append("")
                continue

            for category, commits in categories.items():
                lines.append(f"### {category}")
                lines.append("")

                for commit in commits:
                    desc = commit.description or commit.message
                    parts = [f"- {desc}"]

                    if self.config.include_hash:
                        if github_url:
                            parts.append(
                                f" ([`{commit.short_hash}`]({github_url}/commit/{commit.hash}))"
                            )
                        else:
                            parts.append(f" (`{commit.short_hash}`)")

                    if self.config.include_author:
                        parts.append(f" - {commit.author}")

                    if commit.scope:
                        parts.insert(1, f" **({commit.scope})**")

                    if commit.is_breaking:
                        parts.insert(0, "- **BREAKING:** ")
                        parts[1] = desc  # Remove the leading dash

                    lines.append("".join(parts))

                lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(f"*Generated by [ChangeLog](https://github.com/DonkRonk17/ChangeLog) v{VERSION}*")
        lines.append("")

        return "\n".join(lines)


class TextFormatter:
    """Generate plain-text formatted changelog."""

    def __init__(self, config: ChangelogConfig):
        """Initialize with config."""
        self.config = config

    def format(self, groups: List[VersionGroup], repo_url: str = "") -> str:
        """
        Format version groups as plain text.

        Args:
            groups: List of VersionGroup objects.
            repo_url: Optional repository URL.

        Returns:
            Formatted plain text string.
        """
        lines = []
        sep = "=" * 70

        lines.append(sep)
        lines.append(self.config.header.replace("# ", "").upper())
        lines.append(sep)
        lines.append("")

        for group in groups:
            date_str = f" ({group.date})" if group.date else ""
            lines.append(f"  {group.label}{date_str}")
            lines.append("-" * 70)

            categories = group.categories
            if not categories:
                lines.append("  No categorized changes.")
                lines.append("")
                continue

            for category, commits in categories.items():
                lines.append(f"  [{category}]")

                for commit in commits:
                    desc = commit.description or commit.message
                    hash_str = f" ({commit.short_hash})" if self.config.include_hash else ""
                    lines.append(f"    * {desc}{hash_str}")

                lines.append("")

        lines.append(sep)
        lines.append(f"Generated by ChangeLog v{VERSION}")
        lines.append(sep)

        return "\n".join(lines)


class JSONFormatter:
    """Generate JSON-formatted changelog."""

    def __init__(self, config: ChangelogConfig):
        """Initialize with config."""
        self.config = config

    def format(self, groups: List[VersionGroup], repo_url: str = "") -> str:
        """
        Format version groups as JSON.

        Args:
            groups: List of VersionGroup objects.
            repo_url: Optional repository URL.

        Returns:
            Formatted JSON string.
        """
        data = {
            "generator": f"ChangeLog v{VERSION}",
            "generated_at": datetime.now().isoformat(),
            "repository": repo_url,
            "versions": [],
        }

        for group in groups:
            version_data = {
                "label": group.label,
                "date": group.date,
                "tag": group.tag,
                "commit_count": group.commit_count,
                "categories": {},
            }

            for category, commits in group.categories.items():
                version_data["categories"][category] = [
                    {
                        "hash": c.hash,
                        "short_hash": c.short_hash,
                        "author": c.author,
                        "date": c.date_formatted,
                        "message": c.message,
                        "description": c.description or c.message,
                        "scope": c.scope,
                        "is_breaking": c.is_breaking,
                    }
                    for c in commits
                ]

            data["versions"].append(version_data)

        return json.dumps(data, indent=2, ensure_ascii=False)


# ==============================================================================
# Main ChangeLog Class (Python API)
# ==============================================================================

class ChangeLog:
    """
    Main interface for changelog generation.

    Provides both programmatic API and powers the CLI.

    Example:
        >>> cl = ChangeLog(repo_path=".")
        >>> output = cl.generate()
        >>> print(output)

        >>> cl = ChangeLog(repo_path="/path/to/repo", config={"include_author": True})
        >>> cl.generate(output_file="CHANGELOG.md")
    """

    def __init__(
        self,
        repo_path: str = ".",
        config: Optional[Dict] = None,
        config_file: Optional[str] = None,
    ):
        """
        Initialize ChangeLog.

        Args:
            repo_path: Path to the git repository.
            config: Optional configuration dictionary.
            config_file: Optional path to .changelogrc JSON file.

        Raises:
            FileNotFoundError: If git is not installed.
            ValueError: If path is not a git repository.
        """
        # Load config
        if config_file:
            self.config = ChangelogConfig.from_file(Path(config_file))
        else:
            self.config = ChangelogConfig()

        # Override with explicit config
        if config:
            for key, value in config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

        self.config.repo_path = repo_path
        self.parser = GitParser(repo_path)
        self.categorizer = CommitCategorizer()
        self.grouper = VersionGrouper(self.config)

    def generate(self, output_file: Optional[str] = None) -> str:
        """
        Generate the changelog.

        Args:
            output_file: Optional file path to write output. If None, returns string.

        Returns:
            Formatted changelog string.
        """
        # Get commits
        commits = self.parser.get_commits(
            since=self.config.since,
            until=self.config.until,
            author=self.config.author_filter,
            limit=self.config.limit,
        )

        # Filter excluded patterns
        commits = self._filter_commits(commits)

        # Categorize
        self.categorizer.categorize_all(commits)

        # Get tags
        tags = self.parser.get_tags()

        # Group
        if self.config.group_by == "tags":
            groups = self.grouper.group_by_tags(commits, tags)
        elif self.config.group_by == "dates":
            groups = self.grouper.group_by_dates(commits)
        else:
            groups = self.grouper.group_auto(commits, tags)

        # Reverse if requested
        if self.config.reverse:
            groups = list(reversed(groups))

        # Format
        repo_url = self.parser.get_remote_url()
        formatter = self._get_formatter()
        output = formatter.format(groups, repo_url)

        # Write to file if requested
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(output, encoding="utf-8")

        return output

    def validate_commits(self) -> Dict:
        """
        Validate commit messages against Conventional Commits.

        Returns:
            Dictionary with validation results.
        """
        commits = self.parser.get_commits(limit=self.config.limit)
        commits = self._filter_commits(commits)

        results = {
            "total": len(commits),
            "conventional": 0,
            "non_conventional": 0,
            "compliance_pct": 0.0,
            "by_type": {},
            "non_conventional_commits": [],
        }

        for commit in commits:
            match = CONVENTIONAL_RE.match(commit.message)
            if match:
                results["conventional"] += 1
                commit_type = match.group("type").lower()
                results["by_type"][commit_type] = results["by_type"].get(commit_type, 0) + 1
            else:
                results["non_conventional"] += 1
                results["non_conventional_commits"].append({
                    "hash": commit.short_hash,
                    "message": commit.message,
                })

        if results["total"] > 0:
            results["compliance_pct"] = round(
                (results["conventional"] / results["total"]) * 100, 1
            )

        return results

    def get_stats(self) -> Dict:
        """
        Get commit statistics for the repository.

        Returns:
            Dictionary with statistics.
        """
        commits = self.parser.get_commits(limit=self.config.limit)
        commits = self._filter_commits(commits)
        self.categorizer.categorize_all(commits)

        # Category breakdown
        category_counts = {}
        for commit in commits:
            category_counts[commit.category] = category_counts.get(commit.category, 0) + 1

        # Author breakdown
        author_counts = {}
        for commit in commits:
            author_counts[commit.author] = author_counts.get(commit.author, 0) + 1

        # Date range
        if commits:
            oldest = commits[-1].date_formatted
            newest = commits[0].date_formatted
        else:
            oldest = newest = "N/A"

        # Tags
        tags = self.parser.get_tags()

        return {
            "repo_name": self.parser.get_repo_name(),
            "total_commits": len(commits),
            "total_tags": len(tags),
            "date_range": {"oldest": oldest, "newest": newest},
            "categories": dict(sorted(category_counts.items(), key=lambda x: -x[1])),
            "authors": dict(sorted(author_counts.items(), key=lambda x: -x[1])),
            "tags": [t[0] for t in tags[:10]],
        }

    def _filter_commits(self, commits: List[Commit]) -> List[Commit]:
        """Filter out commits matching exclude patterns."""
        if not self.config.exclude_patterns:
            return commits

        compiled = [re.compile(p) for p in self.config.exclude_patterns]
        filtered = []
        for commit in commits:
            excluded = False
            for pattern in compiled:
                if pattern.search(commit.message):
                    excluded = True
                    break
            if not excluded:
                filtered.append(commit)
        return filtered

    def _get_formatter(self):
        """Get the appropriate formatter based on config."""
        fmt = self.config.output_format.lower()
        if fmt == "text" or fmt == "txt":
            return TextFormatter(self.config)
        elif fmt == "json":
            return JSONFormatter(self.config)
        else:
            return MarkdownFormatter(self.config)


# ==============================================================================
# CLI Interface
# ==============================================================================

def _print_stats(stats: Dict) -> None:
    """Print statistics in a readable format."""
    print("=" * 60)
    print(f"  CHANGELOG STATISTICS: {stats['repo_name']}")
    print("=" * 60)
    print(f"  Total Commits: {stats['total_commits']}")
    print(f"  Total Tags:    {stats['total_tags']}")
    print(f"  Date Range:    {stats['date_range']['oldest']} to {stats['date_range']['newest']}")
    print()

    if stats["categories"]:
        print("  Categories:")
        for cat, count in stats["categories"].items():
            bar = "#" * min(count, 40)
            print(f"    {cat:15s} {count:4d}  {bar}")
        print()

    if stats["authors"]:
        print("  Top Authors:")
        for author, count in list(stats["authors"].items())[:10]:
            print(f"    {author:30s} {count:4d} commits")
        print()

    if stats["tags"]:
        print("  Recent Tags:")
        for tag in stats["tags"]:
            print(f"    {tag}")
        print()

    print("=" * 60)


def _print_validation(results: Dict) -> None:
    """Print validation results in a readable format."""
    print("=" * 60)
    print("  COMMIT MESSAGE VALIDATION")
    print("=" * 60)
    print(f"  Total Commits:       {results['total']}")
    print(f"  Conventional:        {results['conventional']}")
    print(f"  Non-conventional:    {results['non_conventional']}")
    print(f"  Compliance:          {results['compliance_pct']}%")
    print()

    if results["by_type"]:
        print("  By Type:")
        for commit_type, count in sorted(results["by_type"].items(), key=lambda x: -x[1]):
            print(f"    {commit_type:15s} {count:4d}")
        print()

    if results["non_conventional_commits"]:
        print("  Non-conventional commits (first 10):")
        for item in results["non_conventional_commits"][:10]:
            print(f"    {item['hash']}  {item['message'][:60]}")
        print()

    # Grade
    pct = results["compliance_pct"]
    if pct >= 90:
        grade = "A - Excellent"
    elif pct >= 75:
        grade = "B - Good"
    elif pct >= 50:
        grade = "C - Fair"
    elif pct >= 25:
        grade = "D - Poor"
    else:
        grade = "F - Non-compliant"

    print(f"  Grade: {grade}")
    print("=" * 60)


def main():
    """CLI entry point."""
    # Fix Windows console encoding
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    parser = argparse.ArgumentParser(
        prog="changelog",
        description="ChangeLog - Automated Changelog Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  changelog generate                    Generate CHANGELOG.md from current repo
  changelog generate /path/to/repo      Generate for specific repo
  changelog generate -o CHANGES.md      Custom output filename
  changelog generate --format json      JSON output
  changelog generate --format text      Plain text output
  changelog generate --no-hash          Omit commit hashes
  changelog generate --with-author      Include author names
  changelog generate --since 2026-01-01 Filter by date
  changelog generate --limit 100        Limit to last 100 commits
  changelog preview                     Preview without writing file
  changelog validate                    Check commit message compliance
  changelog stats                       Show commit statistics

For more information: https://github.com/DonkRonk17/ChangeLog
        """,
    )

    parser.add_argument(
        "--version", action="version",
        version=f"%(prog)s {VERSION} (Team Brain)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate changelog")
    gen_parser.add_argument("path", nargs="?", default=".", help="Repository path (default: current directory)")
    gen_parser.add_argument("-o", "--output", default="CHANGELOG.md", help="Output filename (default: CHANGELOG.md)")
    gen_parser.add_argument("--format", choices=["markdown", "text", "json"], default="markdown", help="Output format")
    gen_parser.add_argument("--group-by", choices=["auto", "tags", "dates"], default="auto", help="Grouping strategy")
    gen_parser.add_argument("--no-hash", action="store_true", help="Omit commit hashes")
    gen_parser.add_argument("--with-author", action="store_true", help="Include author names")
    gen_parser.add_argument("--with-date", action="store_true", help="Include commit dates")
    gen_parser.add_argument("--since", default="", help="Start date (e.g., 2026-01-01)")
    gen_parser.add_argument("--until", default="", help="End date")
    gen_parser.add_argument("--author", default="", help="Filter by author")
    gen_parser.add_argument("--limit", type=int, default=0, help="Max commits (0 = unlimited)")
    gen_parser.add_argument("--header", default="# Changelog", help="Changelog header")
    gen_parser.add_argument("--reverse", action="store_true", help="Reverse version order (oldest first)")
    gen_parser.add_argument("--config", default="", help="Path to .changelogrc config file")
    gen_parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of file")

    # Preview command
    prev_parser = subparsers.add_parser("preview", help="Preview changelog (stdout only)")
    prev_parser.add_argument("path", nargs="?", default=".", help="Repository path")
    prev_parser.add_argument("--format", choices=["markdown", "text", "json"], default="markdown", help="Output format")
    prev_parser.add_argument("--limit", type=int, default=50, help="Max commits for preview")

    # Validate command
    val_parser = subparsers.add_parser("validate", help="Validate commit messages")
    val_parser.add_argument("path", nargs="?", default=".", help="Repository path")
    val_parser.add_argument("--limit", type=int, default=0, help="Max commits to check")
    val_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show commit statistics")
    stats_parser.add_argument("path", nargs="?", default=".", help="Repository path")
    stats_parser.add_argument("--limit", type=int, default=0, help="Max commits to analyze")
    stats_parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == "generate":
            config = {}
            if args.config:
                cl = ChangeLog(repo_path=args.path, config_file=args.config)
            else:
                config = {
                    "output_format": args.format,
                    "group_by": args.group_by,
                    "include_hash": not args.no_hash,
                    "include_author": args.with_author,
                    "include_date": args.with_date,
                    "since": args.since,
                    "until": args.until,
                    "author_filter": args.author,
                    "limit": args.limit,
                    "header": args.header,
                    "reverse": args.reverse,
                }
                cl = ChangeLog(repo_path=args.path, config=config)

            if args.stdout:
                output = cl.generate()
                print(output)
            else:
                output = cl.generate(output_file=args.output)
                total_lines = output.count("\n") + 1
                print(f"[OK] Changelog generated: {args.output} ({total_lines} lines)")

        elif args.command == "preview":
            cl = ChangeLog(
                repo_path=args.path,
                config={"output_format": args.format, "limit": args.limit},
            )
            output = cl.generate()
            print(output)

        elif args.command == "validate":
            cl = ChangeLog(repo_path=args.path, config={"limit": args.limit})
            results = cl.validate_commits()
            if hasattr(args, "json") and args.json:
                print(json.dumps(results, indent=2))
            else:
                _print_validation(results)

        elif args.command == "stats":
            cl = ChangeLog(repo_path=args.path, config={"limit": args.limit})
            stats = cl.get_stats()
            if hasattr(args, "json") and args.json:
                print(json.dumps(stats, indent=2))
            else:
                _print_stats(stats)

        return 0

    except FileNotFoundError as e:
        print(f"[X] Error: {e}")
        print("[!] Tip: Make sure git is installed and in your PATH")
        return 1
    except ValueError as e:
        print(f"[X] Error: {e}")
        print("[!] Tip: Run this command from inside a git repository")
        return 1
    except KeyboardInterrupt:
        print("\n[!] Cancelled by user")
        return 130
    except Exception as e:
        print(f"[X] Unexpected error: {e}")
        print("[!] Please report this issue at https://github.com/DonkRonk17/ChangeLog/issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
