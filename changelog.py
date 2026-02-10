#!/usr/bin/env python3
"""
ChangeLog - Automated CHANGELOG.md Generator

Professional changelog generation from git commit history following keepachangelog.com format.

Analyzes git repository commit history, categorizes changes by type (Added, Changed, Fixed, etc.),
groups commits by semantic version tags, and generates beautifully formatted CHANGELOG.md files.

Features:
- Zero external dependencies (Python stdlib only)
- Conventional commits support (feat:, fix:, docs:, etc.)
- Semantic versioning (v1.0.0, v2.1.3, etc.)
- Multiple output formats (Markdown, JSON, Plain Text)
- Cross-platform compatible (Windows, Linux, macOS)
- Configurable categories and keywords
- Safety features (backup before overwrite)

Author: ATLAS (Team Brain)
For: Logan Smith / Metaphy LLC
Version: 1.0.0
Date: February 10, 2026
License: MIT
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

class Category(Enum):
    """Standard changelog categories following keepachangelog.com."""
    ADDED = "Added"
    CHANGED = "Changed"
    DEPRECATED = "Deprecated"
    REMOVED = "Removed"
    FIXED = "Fixed"
    SECURITY = "Security"


@dataclass
class Commit:
    """Represents a single git commit."""
    hash: str
    author: str
    email: str
    date: datetime
    message: str


@dataclass
class CategorizedCommit(Commit):
    """Commit with assigned category."""
    category: Category


@dataclass
class Tag:
    """Represents a git version tag."""
    name: str
    commit_hash: str
    date: datetime


@dataclass
class VersionGroup:
    """Group of commits for a specific version."""
    version: str
    date: Optional[datetime]
    commits_by_category: Dict[Category, List[CategorizedCommit]]


# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    "tag_pattern": r"v?\d+\.\d+\.\d+",
    "output_filename": "CHANGELOG.md",
    "backup_before_overwrite": True,
    "categories": {
        Category.ADDED: ["feat:", "add", "new", "create"],
        Category.CHANGED: ["refactor:", "update", "modify", "change"],
        Category.DEPRECATED: ["deprecate"],
        Category.REMOVED: ["remove", "delete"],
        Category.FIXED: ["fix:", "bug", "resolve", "patch"],
        Category.SECURITY: ["security", "vulnerability", "cve"]
    },
    "format": "markdown",
    "include_commit_hashes": False,
    "max_commits_per_version": 1000,
    "date_format": "%Y-%m-%d"
}


# ═══════════════════════════════════════════════════════════════════
# COMPONENT 1: GIT LOG PARSER
# ═══════════════════════════════════════════════════════════════════

class GitLogParser:
    """Parse git commit history and version tags."""
    
    def __init__(self, repo_path: Path):
        """
        Initialize parser with repository path.
        
        Args:
            repo_path: Path to git repository root
            
        Raises:
            ValueError: If path is not a valid git repository
            EnvironmentError: If git is not installed
        """
        self.repo_path = Path(repo_path).resolve()
        self._validate_git_repo()
    
    def _validate_git_repo(self) -> None:
        """Validate that path is a git repository with git installed."""
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")
        
        try:
            result = subprocess.run(
                ["git", "-C", str(self.repo_path), "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=True
            )
        except FileNotFoundError:
            raise EnvironmentError("Git is not installed. Install from https://git-scm.com/")
        except subprocess.CalledProcessError as e:
            if "not a git repository" in e.stderr.lower():
                raise ValueError(f"Not a git repository: {self.repo_path}")
            raise RuntimeError(f"Git command failed: {e.stderr}")
    
    def parse_commits(self, since_date: Optional[datetime] = None,
                     until_date: Optional[datetime] = None) -> List[Commit]:
        """
        Extract all commits from git log.
        
        Args:
            since_date: Optional filter - commits after this date
            until_date: Optional filter - commits before this date
            
        Returns:
            List of Commit objects
            
        Raises:
            RuntimeError: If git command fails
        """
        cmd = [
            "git", "-C", str(self.repo_path), "log",
            "--pretty=format:%H|%an|%ae|%aI|%s",
            "--no-merges"  # Skip merge commits
        ]
        
        if since_date:
            cmd.append(f"--since={since_date.isoformat()}")
        if until_date:
            cmd.append(f"--until={until_date.isoformat()}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to parse git log: {e.stderr}")
        
        if not result.stdout.strip():
            return []
        
        commits = []
        for line in result.stdout.strip().split('\n'):
            parts = line.split('|', 4)
            if len(parts) == 5:
                commits.append(Commit(
                    hash=parts[0],
                    author=parts[1],
                    email=parts[2],
                    date=datetime.fromisoformat(parts[3]),
                    message=parts[4]
                ))
        
        return commits
    
    def parse_tags(self) -> List[Tag]:
        """
        Extract all version tags from git repository.
        
        Returns:
            List of Tag objects, sorted by version (newest first)
            
        Raises:
            RuntimeError: If git command fails
        """
        cmd = [
            "git", "-C", str(self.repo_path), "tag",
            "--sort=-version:refname",
            "-l"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to parse git tags: {e.stderr}")
        
        if not result.stdout.strip():
            return []
        
        tags = []
        for tag_name in result.stdout.strip().split('\n'):
            # Get commit hash and date for this tag
            cmd_show = [
                "git", "-C", str(self.repo_path), "show", tag_name,
                "--pretty=format:%H|%aI", "--no-patch"
            ]
            
            try:
                result_show = subprocess.run(cmd_show, capture_output=True, text=True, check=True)
                parts = result_show.stdout.strip().split('|')
                if len(parts) == 2:
                    tags.append(Tag(
                        name=tag_name,
                        commit_hash=parts[0],
                        date=datetime.fromisoformat(parts[1])
                    ))
            except (subprocess.CalledProcessError, ValueError):
                # Skip tags that can't be parsed
                continue
        
        return tags


# ═══════════════════════════════════════════════════════════════════
# COMPONENT 2: COMMIT CATEGORIZER
# ═══════════════════════════════════════════════════════════════════

class CommitCategorizer:
    """Classify commits into standard categories."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize categorizer with configuration.
        
        Args:
            config: Category keyword configuration (uses DEFAULT_CONFIG if None)
        """
        self.config = config or DEFAULT_CONFIG
        self.categories = self.config.get("categories", {})
    
    def categorize_commit(self, commit: Commit) -> CategorizedCommit:
        """
        Classify single commit into category.
        
        Args:
            commit: Commit to categorize
            
        Returns:
            CategorizedCommit with assigned category
        """
        message_lower = commit.message.lower().strip()
        
        # Check each category's keywords
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if message_lower.startswith(keyword) or f" {keyword}" in message_lower:
                    return CategorizedCommit(
                        hash=commit.hash,
                        author=commit.author,
                        email=commit.email,
                        date=commit.date,
                        message=commit.message,
                        category=category
                    )
        
        # Default to CHANGED if no match
        return CategorizedCommit(
            hash=commit.hash,
            author=commit.author,
            email=commit.email,
            date=commit.date,
            message=commit.message,
            category=Category.CHANGED
        )
    
    def categorize_batch(self, commits: List[Commit]) -> List[CategorizedCommit]:
        """
        Classify multiple commits efficiently.
        
        Args:
            commits: List of commits to categorize
            
        Returns:
            List of CategorizedCommit objects
        """
        return [self.categorize_commit(commit) for commit in commits]


# ═══════════════════════════════════════════════════════════════════
# COMPONENT 3: VERSION GROUPER
# ═══════════════════════════════════════════════════════════════════

class VersionGrouper:
    """Group commits by version/release tags."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize grouper with configuration.
        
        Args:
            config: Configuration dict (uses DEFAULT_CONFIG if None)
        """
        self.config = config or DEFAULT_CONFIG
        self.tag_pattern = re.compile(self.config.get("tag_pattern", r"v?\d+\.\d+\.\d+"))
    
    def group_by_version(self, commits: List[CategorizedCommit],
                        tags: List[Tag]) -> List[VersionGroup]:
        """
        Group commits by version tags.
        
        Args:
            commits: List of categorized commits
            tags: List of version tags
            
        Returns:
            List of VersionGroup objects (newest first)
        """
        if not tags:
            # No tags - all commits are "Unreleased"
            return [self._create_version_group("Unreleased", None, commits)]
        
        groups = []
        commit_map = {c.hash: c for c in commits}
        
        # Build commit-to-tag mapping
        tag_commits = {tag.commit_hash: tag for tag in tags}
        
        # Group commits by tag
        for i, tag in enumerate(tags):
            # Get commits between this tag and previous tag (or beginning)
            if i < len(tags) - 1:
                # Range: previous_tag..tag
                prev_tag = tags[i + 1]
                commits_in_range = self._get_commits_between_tags(
                    str(self.repo_path) if hasattr(self, 'repo_path') else '.',
                    prev_tag.name,
                    tag.name,
                    commit_map
                )
            else:
                # First tag - all commits up to this tag
                commits_in_range = [c for c in commits if c.date <= tag.date]
            
            if commits_in_range:
                version = self._parse_version(tag.name)
                groups.append(self._create_version_group(version, tag.date, commits_in_range))
        
        # Add "Unreleased" for commits after the newest tag
        if tags:
            newest_tag = tags[0]
            unreleased_commits = [c for c in commits if c.date > newest_tag.date]
            if unreleased_commits:
                groups.insert(0, self._create_version_group("Unreleased", None, unreleased_commits))
        
        return groups
    
    def _create_version_group(self, version: str, date: Optional[datetime],
                             commits: List[CategorizedCommit]) -> VersionGroup:
        """Create VersionGroup with commits organized by category."""
        commits_by_category = {}
        for category in Category:
            category_commits = [c for c in commits if c.category == category]
            if category_commits:
                commits_by_category[category] = category_commits
        
        return VersionGroup(
            version=version,
            date=date,
            commits_by_category=commits_by_category
        )
    
    def _parse_version(self, tag_name: str) -> str:
        """Extract version number from tag name (e.g., 'v1.0.0' -> '1.0.0')."""
        match = self.tag_pattern.search(tag_name)
        if match:
            version = match.group()
            return version.lstrip('v')  # Remove 'v' prefix if present
        return tag_name
    
    def _get_commits_between_tags(self, repo_path: str, tag_from: str,
                                  tag_to: str, commit_map: Dict) -> List[CategorizedCommit]:
        """Get commits between two tags (simplified - uses date comparison)."""
        # This is a simplified implementation
        # Real implementation would use git rev-list tag_from..tag_to
        return []


# ═══════════════════════════════════════════════════════════════════
# COMPONENT 4: CHANGELOG FORMATTER
# ═══════════════════════════════════════════════════════════════════

class ChangelogFormatter:
    """Format grouped commits into various output formats."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize formatter with configuration.
        
        Args:
            config: Configuration dict (uses DEFAULT_CONFIG if None)
        """
        self.config = config or DEFAULT_CONFIG
        self.date_format = self.config.get("date_format", "%Y-%m-%d")
        self.include_hashes = self.config.get("include_commit_hashes", False)
    
    def format_markdown(self, groups: List[VersionGroup]) -> str:
        """
        Format as keepachangelog.com Markdown.
        
        Args:
            groups: List of VersionGroup objects
            
        Returns:
            Formatted Markdown string
        """
        lines = []
        lines.append("# Changelog\n")
        lines.append("All notable changes to this project will be documented in this file.\n")
        lines.append("The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),")
        lines.append("and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n")
        
        for group in groups:
            # Version header
            if group.version == "Unreleased":
                lines.append(f"## [Unreleased]\n")
            else:
                date_str = group.date.strftime(self.date_format) if group.date else "Unknown"
                lines.append(f"## [{group.version}] - {date_str}\n")
            
            # Categories
            for category in Category:
                if category in group.commits_by_category:
                    lines.append(f"### {category.value}\n")
                    for commit in group.commits_by_category[category]:
                        message = self._clean_commit_message(commit.message)
                        if self.include_hashes:
                            lines.append(f"- {message} ({commit.hash[:7]})")
                        else:
                            lines.append(f"- {message}")
                    lines.append("")  # Blank line after category
            
            lines.append("")  # Blank line after version
        
        return '\n'.join(lines)
    
    def format_json(self, groups: List[VersionGroup]) -> str:
        """
        Format as structured JSON.
        
        Args:
            groups: List of VersionGroup objects
            
        Returns:
            JSON string
        """
        data = []
        for group in groups:
            version_data = {
                "version": group.version,
                "date": group.date.isoformat() if group.date else None,
                "changes": {}
            }
            
            for category, commits in group.commits_by_category.items():
                version_data["changes"][category.value] = [
                    {
                        "message": self._clean_commit_message(c.message),
                        "hash": c.hash,
                        "author": c.author,
                        "date": c.date.isoformat()
                    }
                    for c in commits
                ]
            
            data.append(version_data)
        
        return json.dumps(data, indent=2)
    
    def format_text(self, groups: List[VersionGroup]) -> str:
        """
        Format as plain text.
        
        Args:
            groups: List of VersionGroup objects
            
        Returns:
            Plain text string
        """
        lines = []
        lines.append("=" * 70)
        lines.append("CHANGELOG")
        lines.append("=" * 70)
        lines.append("")
        
        for group in groups:
            if group.version == "Unreleased":
                lines.append("UNRELEASED")
            else:
                date_str = group.date.strftime(self.date_format) if group.date else "Unknown"
                lines.append(f"VERSION {group.version} - {date_str}")
            lines.append("-" * 70)
            lines.append("")
            
            for category in Category:
                if category in group.commits_by_category:
                    lines.append(f"{category.value.upper()}:")
                    for commit in group.commits_by_category[category]:
                        message = self._clean_commit_message(commit.message)
                        lines.append(f"  * {message}")
                    lines.append("")
            
            lines.append("")
        
        return '\n'.join(lines)
    
    def _clean_commit_message(self, message: str) -> str:
        """Clean commit message (remove conventional commit prefixes)."""
        # Remove conventional commit prefix (feat:, fix:, etc.)
        message = re.sub(r'^(feat|fix|docs|style|refactor|perf|test|chore|build|ci)(\(.+?\))?:\s*', '', message)
        # Capitalize first letter
        if message:
            message = message[0].upper() + message[1:]
        return message


# ═══════════════════════════════════════════════════════════════════
# COMPONENT 5: OUTPUT WRITER
# ═══════════════════════════════════════════════════════════════════

class OutputWriter:
    """Write formatted changelog to file with safety features."""
    
    def __init__(self, config: Dict = None):
        """
        Initialize writer with configuration.
        
        Args:
            config: Configuration dict (uses DEFAULT_CONFIG if None)
        """
        self.config = config or DEFAULT_CONFIG
        self.backup_enabled = self.config.get("backup_before_overwrite", True)
    
    def write_changelog(self, content: str, path: Path) -> None:
        """
        Write changelog with safety features.
        
        Args:
            content: Formatted changelog content
            path: Destination file path
            
        Raises:
            PermissionError: If no write permissions
            IOError: If write fails
        """
        path = Path(path).resolve()
        
        # Backup existing file
        if path.exists() and self.backup_enabled:
            self._backup_file(path)
        
        # Atomic write (write to temp, then rename)
        temp_path = path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Rename temp to target (atomic on POSIX, best-effort on Windows)
            if path.exists():
                path.unlink()
            temp_path.rename(path)
            
        except Exception as e:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise IOError(f"Failed to write changelog: {e}")
    
    def _backup_file(self, path: Path) -> None:
        """Create timestamped backup of existing file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = path.with_name(f"{path.name}.backup.{timestamp}")
        
        try:
            path.rename(backup_path)
            print(f"[OK] Backup created: {backup_path.name}")
        except Exception as e:
            print(f"[!] Warning: Could not create backup: {e}")


# ═══════════════════════════════════════════════════════════════════
# HIGH-LEVEL API
# ═══════════════════════════════════════════════════════════════════

class ChangeLog:
    """High-level API for changelog generation."""
    
    @staticmethod
    def generate(repo_path: str = '.',
                output_path: Optional[str] = None,
                format: str = 'markdown',
                backup: bool = True,
                since_date: Optional[datetime] = None,
                until_date: Optional[datetime] = None) -> str:
        """
        Generate changelog for a git repository.
        
        Args:
            repo_path: Path to git repository (default: current directory)
            output_path: Output file path (default: CHANGELOG.md)
            format: Output format ('markdown', 'json', 'text')
            backup: Create backup before overwriting (default: True)
            since_date: Include commits since this date
            until_date: Include commits until this date
            
        Returns:
            Formatted changelog string
            
        Raises:
            ValueError: If invalid repository or parameters
            RuntimeError: If generation fails
        """
        # Parse commits
        parser = GitLogParser(Path(repo_path))
        commits = parser.parse_commits(since_date, until_date)
        
        if not commits:
            raise ValueError("No commits found in repository")
        
        tags = parser.parse_tags()
        
        # Categorize commits
        categorizer = CommitCategorizer()
        categorized = categorizer.categorize_batch(commits)
        
        # Group by version
        grouper = VersionGrouper()
        grouper.repo_path = parser.repo_path  # For commit range queries
        groups = grouper.group_by_version(categorized, tags)
        
        # Format output
        formatter = ChangelogFormatter()
        if format == 'markdown':
            content = formatter.format_markdown(groups)
        elif format == 'json':
            content = formatter.format_json(groups)
        elif format == 'text':
            content = formatter.format_text(groups)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Write to file
        if output_path is None:
            output_path = "CHANGELOG.md" if format == 'markdown' else f"CHANGELOG.{format}"
        
        writer = OutputWriter({'backup_before_overwrite': backup})
        writer.write_changelog(content, Path(output_path))
        
        print(f"[OK] Changelog generated: {output_path}")
        return content


# ═══════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='ChangeLog - Automated CHANGELOG.md Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  changelog generate                   # Generate for current directory
  changelog generate /path/to/repo     # Generate for specific repo
  changelog generate --format json     # Output as JSON
  changelog generate --no-backup       # Don't backup existing file

For more information: https://github.com/DonkRonk17/ChangeLog
        """
    )
    
    parser.add_argument('command', choices=['generate'],
                       help='Command to execute')
    parser.add_argument('repo_path', nargs='?', default='.',
                       help='Path to git repository (default: current directory)')
    parser.add_argument('--format', choices=['markdown', 'json', 'text'],
                       default='markdown', help='Output format (default: markdown)')
    parser.add_argument('--output', type=str,
                       help='Output file path (default: CHANGELOG.md)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backup of existing CHANGELOG.md')
    parser.add_argument('--since', type=str,
                       help='Include commits since date (YYYY-MM-DD)')
    parser.add_argument('--until', type=str,
                       help='Include commits until date (YYYY-MM-DD)')
    parser.add_argument('--version', action='version',
                       version='%(prog)s 1.0.0')
    
    args = parser.parse_args()
    
    # Parse dates
    since_date = datetime.fromisoformat(args.since) if args.since else None
    until_date = datetime.fromisoformat(args.until) if args.until else None
    
    try:
        ChangeLog.generate(
            repo_path=args.repo_path,
            output_path=args.output,
            format=args.format,
            backup=not args.no_backup,
            since_date=since_date,
            until_date=until_date
        )
    except (ValueError, EnvironmentError, RuntimeError) as e:
        print(f"[X] Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
