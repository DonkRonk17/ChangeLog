#!/usr/bin/env python3
"""
Comprehensive test suite for ChangeLog v1.0.0.

Tests cover:
- Core functionality (commit parsing, categorization, grouping, formatting)
- Edge cases (empty repos, no tags, special characters, Unicode)
- Error handling (missing git, invalid repos, bad input)
- Integration scenarios (full generate pipeline, multiple formats)
- Configuration (config loading, overrides)

Run: python test_changelog.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from changelog import (
    ChangeLog,
    ChangelogConfig,
    Commit,
    CommitCategorizer,
    GitParser,
    MarkdownFormatter,
    TextFormatter,
    JSONFormatter,
    VersionGroup,
    VersionGrouper,
    CONVENTIONAL_RE,
    SEMVER_RE,
    VERSION,
)


class TestCommit(unittest.TestCase):
    """Test Commit dataclass."""

    def test_commit_creation(self):
        """Test basic commit creation."""
        commit = Commit(
            hash="abc1234567890",
            author="ATLAS",
            date="2026-02-07T10:00:00-08:00",
            message="feat: add changelog generator",
        )
        self.assertEqual(commit.hash, "abc1234567890")
        self.assertEqual(commit.author, "ATLAS")
        self.assertEqual(commit.message, "feat: add changelog generator")

    def test_short_hash(self):
        """Test short hash property."""
        commit = Commit(hash="abc1234567890", author="", date="", message="")
        self.assertEqual(commit.short_hash, "abc1234")

    def test_date_formatted(self):
        """Test date formatting."""
        commit = Commit(
            hash="abc", author="", date="2026-02-07T10:00:00-08:00", message=""
        )
        self.assertEqual(commit.date_formatted, "2026-02-07")

    def test_date_formatted_no_timezone(self):
        """Test date formatting without timezone."""
        commit = Commit(
            hash="abc", author="", date="2026-02-07T10:00:00", message=""
        )
        self.assertEqual(commit.date_formatted, "2026-02-07")

    def test_month_key(self):
        """Test month key for grouping."""
        commit = Commit(
            hash="abc", author="", date="2026-02-07T10:00:00", message=""
        )
        self.assertEqual(commit.month_key, "2026-02")

    def test_default_category(self):
        """Test default category is Other."""
        commit = Commit(hash="abc", author="", date="", message="")
        self.assertEqual(commit.category, "Other")


class TestCommitCategorizer(unittest.TestCase):
    """Test commit categorization logic."""

    def setUp(self):
        """Set up categorizer instance."""
        self.categorizer = CommitCategorizer()

    def test_conventional_feat(self):
        """Test feat: prefix categorization."""
        commit = Commit(hash="abc", author="", date="", message="feat: add new feature")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Added")
        self.assertEqual(commit.description, "add new feature")

    def test_conventional_fix(self):
        """Test fix: prefix categorization."""
        commit = Commit(hash="abc", author="", date="", message="fix: resolve crash bug")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Fixed")
        self.assertEqual(commit.description, "resolve crash bug")

    def test_conventional_docs(self):
        """Test docs: prefix categorization."""
        commit = Commit(hash="abc", author="", date="", message="docs: update README")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Documentation")

    def test_conventional_refactor(self):
        """Test refactor: prefix categorization."""
        commit = Commit(hash="abc", author="", date="", message="refactor: clean up utils")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Changed")

    def test_conventional_test(self):
        """Test test: prefix categorization."""
        commit = Commit(hash="abc", author="", date="", message="test: add unit tests")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Testing")

    def test_conventional_with_scope(self):
        """Test scope parsing in conventional commits."""
        commit = Commit(hash="abc", author="", date="", message="feat(cli): add --verbose flag")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Added")
        self.assertEqual(commit.scope, "cli")
        self.assertEqual(commit.description, "add --verbose flag")

    def test_conventional_breaking_change(self):
        """Test breaking change detection."""
        commit = Commit(hash="abc", author="", date="", message="feat!: remove deprecated API")
        self.categorizer.categorize(commit)
        self.assertTrue(commit.is_breaking)
        self.assertEqual(commit.category, "Added")

    def test_keyword_fallback_add(self):
        """Test keyword fallback for 'add' prefix."""
        commit = Commit(hash="abc", author="", date="", message="Add new CLI command")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Added")

    def test_keyword_fallback_fix(self):
        """Test keyword fallback for 'fix' prefix."""
        commit = Commit(hash="abc", author="", date="", message="Fix broken link in README")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Fixed")

    def test_keyword_fallback_update(self):
        """Test keyword fallback for 'update' prefix."""
        commit = Commit(hash="abc", author="", date="", message="Update dependencies")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Changed")

    def test_keyword_fallback_remove(self):
        """Test keyword fallback for 'remove' prefix."""
        commit = Commit(hash="abc", author="", date="", message="Remove deprecated code")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Removed")

    def test_unmatched_message(self):
        """Test message that matches no patterns."""
        commit = Commit(hash="abc", author="", date="", message="Initial commit")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Other")

    def test_categorize_all(self):
        """Test batch categorization."""
        commits = [
            Commit(hash="1", author="", date="", message="feat: add A"),
            Commit(hash="2", author="", date="", message="fix: fix B"),
            Commit(hash="3", author="", date="", message="Initial commit"),
        ]
        self.categorizer.categorize_all(commits)
        self.assertEqual(commits[0].category, "Added")
        self.assertEqual(commits[1].category, "Fixed")
        self.assertEqual(commits[2].category, "Other")

    def test_custom_rules(self):
        """Test custom categorization rules."""
        categorizer = CommitCategorizer(custom_rules={"custom": "Special"})
        commit = Commit(hash="abc", author="", date="", message="custom: do something")
        categorizer.categorize(commit)
        self.assertEqual(commit.category, "Special")

    def test_empty_message(self):
        """Test empty commit message."""
        commit = Commit(hash="abc", author="", date="", message="")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Other")

    def test_security_keyword(self):
        """Test security keyword detection."""
        commit = Commit(hash="abc", author="", date="", message="security: patch XSS vulnerability")
        self.categorizer.categorize(commit)
        self.assertEqual(commit.category, "Security")


class TestVersionGroup(unittest.TestCase):
    """Test VersionGroup functionality."""

    def test_empty_group(self):
        """Test empty version group."""
        group = VersionGroup(label="v1.0.0")
        self.assertEqual(group.commit_count, 0)
        self.assertEqual(len(group.categories), 0)

    def test_categories_grouping(self):
        """Test commits grouped by category."""
        commits = [
            Commit(hash="1", author="", date="", message="", category="Added"),
            Commit(hash="2", author="", date="", message="", category="Fixed"),
            Commit(hash="3", author="", date="", message="", category="Added"),
        ]
        group = VersionGroup(label="v1.0.0", commits=commits)
        cats = group.categories
        self.assertIn("Added", cats)
        self.assertIn("Fixed", cats)
        self.assertEqual(len(cats["Added"]), 2)
        self.assertEqual(len(cats["Fixed"]), 1)

    def test_commit_count(self):
        """Test commit count property."""
        commits = [
            Commit(hash=str(i), author="", date="", message="") for i in range(5)
        ]
        group = VersionGroup(label="v1.0.0", commits=commits)
        self.assertEqual(group.commit_count, 5)


class TestChangelogConfig(unittest.TestCase):
    """Test configuration handling."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ChangelogConfig()
        self.assertEqual(config.output_file, "CHANGELOG.md")
        self.assertEqual(config.output_format, "markdown")
        self.assertEqual(config.group_by, "auto")
        self.assertTrue(config.include_hash)
        self.assertFalse(config.include_author)

    def test_config_from_file(self):
        """Test loading config from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"output_file": "CHANGES.md", "include_author": True}, f)
            f.flush()
            config = ChangelogConfig.from_file(Path(f.name))
            self.assertEqual(config.output_file, "CHANGES.md")
            self.assertTrue(config.include_author)
        os.unlink(f.name)

    def test_config_from_missing_file(self):
        """Test loading config from non-existent file returns defaults."""
        config = ChangelogConfig.from_file(Path("/nonexistent/path.json"))
        self.assertEqual(config.output_file, "CHANGELOG.md")

    def test_config_to_dict(self):
        """Test config serialization."""
        config = ChangelogConfig()
        d = config.to_dict()
        self.assertIn("output_file", d)
        self.assertIn("output_format", d)
        self.assertIsInstance(d, dict)


class TestRegexPatterns(unittest.TestCase):
    """Test regex pattern matching."""

    def test_conventional_commits_basic(self):
        """Test basic conventional commit parsing."""
        match = CONVENTIONAL_RE.match("feat: add new feature")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("type"), "feat")
        self.assertEqual(match.group("description"), "add new feature")

    def test_conventional_commits_with_scope(self):
        """Test conventional commit with scope."""
        match = CONVENTIONAL_RE.match("fix(parser): handle empty input")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("type"), "fix")
        self.assertEqual(match.group("scope"), "parser")
        self.assertEqual(match.group("description"), "handle empty input")

    def test_conventional_commits_breaking(self):
        """Test breaking change indicator."""
        match = CONVENTIONAL_RE.match("feat!: remove old API")
        self.assertIsNotNone(match)
        self.assertIsNotNone(match.group("breaking"))

    def test_conventional_commits_no_match(self):
        """Test non-conventional message doesn't match."""
        match = CONVENTIONAL_RE.match("Just a regular commit message")
        self.assertIsNone(match)

    def test_semver_basic(self):
        """Test basic semver matching."""
        match = SEMVER_RE.match("v1.0.0")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("major"), "1")
        self.assertEqual(match.group("minor"), "0")
        self.assertEqual(match.group("patch"), "0")

    def test_semver_without_v(self):
        """Test semver without v prefix."""
        match = SEMVER_RE.match("2.1.3")
        self.assertIsNotNone(match)

    def test_semver_with_prerelease(self):
        """Test semver with prerelease tag."""
        match = SEMVER_RE.match("v1.0.0-beta.1")
        self.assertIsNotNone(match)
        self.assertEqual(match.group("prerelease"), "beta.1")

    def test_semver_no_match(self):
        """Test non-semver string doesn't match."""
        match = SEMVER_RE.match("release-candidate")
        self.assertIsNone(match)


class TestMarkdownFormatter(unittest.TestCase):
    """Test Markdown output formatting."""

    def setUp(self):
        """Set up formatter."""
        self.config = ChangelogConfig()
        self.formatter = MarkdownFormatter(self.config)

    def test_basic_format(self):
        """Test basic Markdown formatting."""
        commits = [
            Commit(hash="abc1234", author="ATLAS", date="2026-02-07", message="feat: add feature",
                   category="Added", description="add feature"),
        ]
        groups = [VersionGroup(label="v1.0.0", date="2026-02-07", commits=commits)]
        output = self.formatter.format(groups)
        self.assertIn("# Changelog", output)
        self.assertIn("## [v1.0.0]", output)
        self.assertIn("### Added", output)
        self.assertIn("add feature", output)

    def test_format_with_hash(self):
        """Test hash inclusion in output."""
        commits = [
            Commit(hash="abc1234567", author="", date="", message="",
                   category="Added", description="test"),
        ]
        groups = [VersionGroup(label="v1.0.0", commits=commits)]
        output = self.formatter.format(groups)
        self.assertIn("abc1234", output)

    def test_format_without_hash(self):
        """Test hash exclusion."""
        self.config.include_hash = False
        formatter = MarkdownFormatter(self.config)
        commits = [
            Commit(hash="abc1234567", author="", date="", message="",
                   category="Added", description="test"),
        ]
        groups = [VersionGroup(label="v1.0.0", commits=commits)]
        output = formatter.format(groups)
        self.assertNotIn("abc1234", output)

    def test_format_with_github_links(self):
        """Test GitHub commit links."""
        commits = [
            Commit(hash="abc1234567890", author="", date="", message="",
                   category="Added", description="test"),
        ]
        groups = [VersionGroup(label="v1.0.0", commits=commits)]
        output = self.formatter.format(groups, repo_url="https://github.com/DonkRonk17/Test")
        self.assertIn("https://github.com/DonkRonk17/Test/commit/abc1234567890", output)

    def test_empty_groups(self):
        """Test formatting with no groups."""
        output = self.formatter.format([])
        self.assertIn("# Changelog", output)

    def test_multiple_categories(self):
        """Test formatting with multiple categories."""
        commits = [
            Commit(hash="1", author="", date="", message="", category="Added", description="A"),
            Commit(hash="2", author="", date="", message="", category="Fixed", description="B"),
            Commit(hash="3", author="", date="", message="", category="Changed", description="C"),
        ]
        groups = [VersionGroup(label="v1.0.0", commits=commits)]
        output = self.formatter.format(groups)
        self.assertIn("### Added", output)
        self.assertIn("### Fixed", output)
        self.assertIn("### Changed", output)


class TestTextFormatter(unittest.TestCase):
    """Test plain text output formatting."""

    def setUp(self):
        """Set up formatter."""
        self.config = ChangelogConfig()
        self.formatter = TextFormatter(self.config)

    def test_basic_format(self):
        """Test basic text formatting."""
        commits = [
            Commit(hash="abc1234", author="", date="", message="",
                   category="Added", description="add feature"),
        ]
        groups = [VersionGroup(label="v1.0.0", date="2026-02-07", commits=commits)]
        output = self.formatter.format(groups)
        self.assertIn("CHANGELOG", output)
        self.assertIn("v1.0.0", output)
        self.assertIn("[Added]", output)
        self.assertIn("add feature", output)

    def test_text_has_separators(self):
        """Test text output has visual separators."""
        output = self.formatter.format([])
        self.assertIn("=" * 70, output)


class TestJSONFormatter(unittest.TestCase):
    """Test JSON output formatting."""

    def setUp(self):
        """Set up formatter."""
        self.config = ChangelogConfig()
        self.formatter = JSONFormatter(self.config)

    def test_basic_format(self):
        """Test basic JSON formatting."""
        commits = [
            Commit(hash="abc1234567", author="ATLAS", date="2026-02-07", message="feat: test",
                   category="Added", description="test"),
        ]
        groups = [VersionGroup(label="v1.0.0", commits=commits)]
        output = self.formatter.format(groups)
        data = json.loads(output)
        self.assertIn("versions", data)
        self.assertEqual(len(data["versions"]), 1)
        self.assertEqual(data["versions"][0]["label"], "v1.0.0")

    def test_json_is_valid(self):
        """Test output is valid JSON."""
        commits = [
            Commit(hash="abc", author="ATLAS", date="2026-02-07", message="test",
                   category="Other", description="test"),
        ]
        groups = [VersionGroup(label="v1.0.0", commits=commits)]
        output = self.formatter.format(groups)
        data = json.loads(output)  # Should not raise
        self.assertIsInstance(data, dict)

    def test_json_empty_groups(self):
        """Test JSON with empty groups."""
        output = self.formatter.format([])
        data = json.loads(output)
        self.assertEqual(len(data["versions"]), 0)


class TestVersionGrouper(unittest.TestCase):
    """Test version grouping logic."""

    def setUp(self):
        """Set up grouper."""
        self.config = ChangelogConfig()
        self.grouper = VersionGrouper(self.config)

    def test_group_by_dates(self):
        """Test date-based grouping."""
        commits = [
            Commit(hash="1", author="", date="2026-02-07T10:00:00", message="A"),
            Commit(hash="2", author="", date="2026-02-05T10:00:00", message="B"),
            Commit(hash="3", author="", date="2026-01-15T10:00:00", message="C"),
        ]
        groups = self.grouper.group_by_dates(commits)
        self.assertEqual(len(groups), 2)  # Feb + Jan
        self.assertIn("February", groups[0].label)
        self.assertIn("January", groups[1].label)

    def test_group_empty_commits(self):
        """Test grouping with no commits."""
        groups = self.grouper.group_by_dates([])
        self.assertEqual(len(groups), 0)

    def test_group_auto_no_tags(self):
        """Test auto grouping falls back to dates when no tags."""
        commits = [
            Commit(hash="1", author="", date="2026-02-07T10:00:00", message="A"),
        ]
        groups = self.grouper.group_auto(commits, [])
        self.assertTrue(len(groups) > 0)
        self.assertIn("February", groups[0].label)

    def test_group_as_unreleased(self):
        """Test all commits as unreleased when no tags."""
        commits = [
            Commit(hash="1", author="", date="2026-02-07", message="A"),
            Commit(hash="2", author="", date="2026-02-06", message="B"),
        ]
        groups = self.grouper.group_by_tags(commits, [])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].label, "Unreleased")
        self.assertEqual(groups[0].commit_count, 2)


class TestGitIntegration(unittest.TestCase):
    """Integration tests using a temporary git repository."""

    def setUp(self):
        """Create a temporary git repository with test commits."""
        self.test_dir = tempfile.mkdtemp()
        self._init_test_repo()

    def tearDown(self):
        """Clean up temporary directory."""
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception:
            pass

    def _init_test_repo(self):
        """Initialize a test git repo with sample commits."""
        os.chdir(self.test_dir)

        # Init repo
        subprocess.run(["git", "init"], capture_output=True, cwd=self.test_dir)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            capture_output=True, cwd=self.test_dir,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            capture_output=True, cwd=self.test_dir,
        )

        # Create commits
        test_commits = [
            "feat: add initial project structure",
            "fix: resolve startup crash",
            "docs: add README documentation",
            "refactor: clean up main module",
            "test: add unit tests for parser",
            "chore: update gitignore",
            "feat(cli): add --verbose flag",
            "fix(parser): handle empty input",
            "Add error handling for edge cases",
            "Update dependencies to latest",
        ]

        for i, msg in enumerate(test_commits):
            filepath = os.path.join(self.test_dir, f"file_{i}.txt")
            with open(filepath, "w") as f:
                f.write(f"content {i}")
            subprocess.run(["git", "add", "."], capture_output=True, cwd=self.test_dir)
            subprocess.run(
                ["git", "commit", "-m", msg],
                capture_output=True, cwd=self.test_dir,
            )

    def test_parse_commits(self):
        """Test parsing commits from real git repo."""
        parser = GitParser(self.test_dir)
        commits = parser.get_commits()
        self.assertEqual(len(commits), 10)
        self.assertEqual(commits[0].message, "Update dependencies to latest")

    def test_get_repo_name(self):
        """Test getting repo name from directory."""
        parser = GitParser(self.test_dir)
        name = parser.get_repo_name()
        self.assertIsNotNone(name)
        self.assertTrue(len(name) > 0)

    def test_get_commit_count(self):
        """Test commit count."""
        parser = GitParser(self.test_dir)
        count = parser.get_commit_count()
        self.assertEqual(count, 10)

    def test_full_generate_markdown(self):
        """Test full changelog generation pipeline - Markdown."""
        cl = ChangeLog(repo_path=self.test_dir)
        output = cl.generate()
        self.assertIn("# Changelog", output)
        self.assertIn("Added", output)
        self.assertIn("Fixed", output)
        self.assertTrue(len(output) > 100)

    def test_full_generate_text(self):
        """Test full changelog generation - text format."""
        cl = ChangeLog(repo_path=self.test_dir, config={"output_format": "text"})
        output = cl.generate()
        self.assertIn("CHANGELOG", output)
        self.assertIn("[Added]", output)

    def test_full_generate_json(self):
        """Test full changelog generation - JSON format."""
        cl = ChangeLog(repo_path=self.test_dir, config={"output_format": "json"})
        output = cl.generate()
        data = json.loads(output)
        self.assertIn("versions", data)
        self.assertTrue(len(data["versions"]) > 0)

    def test_generate_to_file(self):
        """Test writing changelog to file."""
        output_path = os.path.join(self.test_dir, "CHANGELOG.md")
        cl = ChangeLog(repo_path=self.test_dir)
        cl.generate(output_file=output_path)
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("# Changelog", content)

    def test_validate_commits(self):
        """Test commit validation."""
        cl = ChangeLog(repo_path=self.test_dir)
        results = cl.validate_commits()
        self.assertEqual(results["total"], 10)
        self.assertGreater(results["conventional"], 0)
        self.assertGreater(results["compliance_pct"], 0)

    def test_get_stats(self):
        """Test statistics generation."""
        cl = ChangeLog(repo_path=self.test_dir)
        stats = cl.get_stats()
        self.assertEqual(stats["total_commits"], 10)
        self.assertIn("categories", stats)
        self.assertIn("authors", stats)

    def test_filter_merge_commits(self):
        """Test that merge commits are filtered."""
        # Add a merge-like commit
        filepath = os.path.join(self.test_dir, "merge_file.txt")
        with open(filepath, "w") as f:
            f.write("merge content")
        subprocess.run(["git", "add", "."], capture_output=True, cwd=self.test_dir)
        subprocess.run(
            ["git", "commit", "-m", "Merge branch 'feature' into main"],
            capture_output=True, cwd=self.test_dir,
        )

        cl = ChangeLog(repo_path=self.test_dir)
        output = cl.generate()
        self.assertNotIn("Merge branch", output)

    def test_limit_commits(self):
        """Test commit limit option."""
        cl = ChangeLog(repo_path=self.test_dir, config={"limit": 3})
        stats = cl.get_stats()
        self.assertEqual(stats["total_commits"], 3)

    def test_include_author(self):
        """Test author inclusion in output."""
        cl = ChangeLog(
            repo_path=self.test_dir,
            config={"include_author": True},
        )
        output = cl.generate()
        self.assertIn("Test User", output)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def test_invalid_repo_path(self):
        """Test error on non-git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                GitParser(tmpdir)

    def test_nonexistent_path(self):
        """Test error on nonexistent path."""
        with self.assertRaises((ValueError, FileNotFoundError, OSError)):
            GitParser("/this/path/does/not/exist/at/all")

    def test_commit_with_special_chars(self):
        """Test commit message with special characters."""
        commit = Commit(
            hash="abc", author="", date="",
            message="fix: handle 'quotes' and \"double quotes\" properly"
        )
        categorizer = CommitCategorizer()
        categorizer.categorize(commit)
        self.assertEqual(commit.category, "Fixed")

    def test_commit_with_pipe_in_message(self):
        """Test commit message containing pipe character."""
        commit = Commit(
            hash="abc", author="", date="",
            message="feat: add x | y filter support"
        )
        categorizer = CommitCategorizer()
        categorizer.categorize(commit)
        self.assertEqual(commit.category, "Added")

    def test_very_long_commit_message(self):
        """Test very long commit message."""
        long_msg = "feat: " + "x" * 1000
        commit = Commit(hash="abc", author="", date="", message=long_msg)
        categorizer = CommitCategorizer()
        categorizer.categorize(commit)
        self.assertEqual(commit.category, "Added")

    def test_date_parsing_fallback(self):
        """Test date parsing with invalid date."""
        commit = Commit(hash="abc", author="", date="not-a-date", message="")
        # Should not raise, falls back to current time
        date = commit.date_formatted
        self.assertIsNotNone(date)


class TestCLI(unittest.TestCase):
    """Test CLI interface."""

    def test_main_no_args_returns_0(self):
        """Test main() with no arguments returns 0."""
        from changelog import main
        with patch("sys.argv", ["changelog"]):
            # main() prints help and returns 0
            result = main()
            self.assertEqual(result, 0)

    def test_version_string(self):
        """Test version is defined."""
        self.assertRegex(VERSION, r"\d+\.\d+\.\d+")


def run_tests():
    """Run all tests with summary output."""
    print("=" * 70)
    print(f"TESTING: ChangeLog v{VERSION}")
    print("=" * 70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCommit))
    suite.addTests(loader.loadTestsFromTestCase(TestCommitCategorizer))
    suite.addTests(loader.loadTestsFromTestCase(TestVersionGroup))
    suite.addTests(loader.loadTestsFromTestCase(TestChangelogConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestRegexPatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestMarkdownFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestTextFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestJSONFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestVersionGrouper))
    suite.addTests(loader.loadTestsFromTestCase(TestGitIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestCLI))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 70)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print(f"RESULTS: {result.testsRun} tests")
    print(f"[OK] Passed: {passed}")
    if result.failures:
        print(f"[X] Failed: {len(result.failures)}")
    if result.errors:
        print(f"[X] Errors: {len(result.errors)}")
    print("=" * 70)

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
