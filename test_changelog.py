#!/usr/bin/env python3
"""
Comprehensive Test Suite for ChangeLog v1.0

Tests cover:
- GitLogParser: Repository validation, commit parsing, tag parsing
- CommitCategorizer: Conventional commits, keyword detection, edge cases
- VersionGrouper: Version grouping, semantic versioning, unreleased
- ChangelogFormatter: Markdown, JSON, text formats
- OutputWriter: File writing, backup, atomic operations
- Integration: End-to-end changelog generation

Run: python test_changelog.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from changelog import (
    Category,
    ChangeLog,
    ChangelogFormatter,
    Commit,
    CommitCategorizer,
    GitLogParser,
    OutputWriter,
    Tag,
    VersionGroup,
    VersionGrouper
)


# ═══════════════════════════════════════════════════════════════════
# TEST: GIT LOG PARSER
# ═══════════════════════════════════════════════════════════════════

class TestGitLogParser(unittest.TestCase):
    """Test git log parsing functionality."""
    
    def setUp(self):
        """Create temporary git repository for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=self.repo_path, check=True, capture_output=True)
        
        # Create initial commit
        (self.repo_path / 'README.md').write_text('# Test Repo')
        subprocess.run(['git', 'add', 'README.md'], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=self.repo_path, check=True, capture_output=True)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_valid_repo(self):
        """Test: Initialize parser with valid git repository."""
        parser = GitLogParser(self.repo_path)
        self.assertEqual(parser.repo_path, self.repo_path.resolve())
    
    def test_initialization_invalid_repo(self):
        """Test: Initialize parser with invalid repository raises ValueError."""
        invalid_path = Path(self.temp_dir) / 'nonexistent'
        with self.assertRaises(ValueError):
            GitLogParser(invalid_path)
    
    def test_parse_commits_basic(self):
        """Test: Parse commits from repository."""
        parser = GitLogParser(self.repo_path)
        commits = parser.parse_commits()
        
        self.assertGreater(len(commits), 0)
        self.assertIsInstance(commits[0], Commit)
        self.assertEqual(commits[0].message, 'Initial commit')
    
    def test_parse_commits_empty_repo(self):
        """Test: Parse commits from repository with no commits returns empty list."""
        # Create empty git repo
        empty_dir = tempfile.mkdtemp()
        subprocess.run(['git', 'init'], cwd=empty_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=empty_dir, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=empty_dir, check=True, capture_output=True)
        
        parser = GitLogParser(empty_dir)
        
        # Empty repo should raise RuntimeError or return empty list
        # We'll handle this gracefully
        try:
            commits = parser.parse_commits()
            # If no error, should be empty
            self.assertEqual(len(commits), 0)
        except RuntimeError as e:
            # Expected: git log fails on empty repo
            self.assertIn("does not have any commits", str(e))
        
        shutil.rmtree(empty_dir, ignore_errors=True)
    
    def test_parse_tags(self):
        """Test: Parse version tags from repository."""
        # Create tag
        subprocess.run(['git', 'tag', 'v1.0.0'], cwd=self.repo_path, check=True, capture_output=True)
        
        parser = GitLogParser(self.repo_path)
        tags = parser.parse_tags()
        
        self.assertEqual(len(tags), 1)
        self.assertIsInstance(tags[0], Tag)
        self.assertEqual(tags[0].name, 'v1.0.0')
    
    def test_parse_tags_no_tags(self):
        """Test: Parse tags from repository with no tags."""
        parser = GitLogParser(self.repo_path)
        tags = parser.parse_tags()
        
        self.assertEqual(len(tags), 0)


# ═══════════════════════════════════════════════════════════════════
# TEST: COMMIT CATEGORIZER
# ═══════════════════════════════════════════════════════════════════

class TestCommitCategorizer(unittest.TestCase):
    """Test commit categorization functionality."""
    
    def setUp(self):
        """Set up categorizer for testing."""
        self.categorizer = CommitCategorizer()
    
    def test_categorize_feat_conventional(self):
        """Test: Categorize conventional commit 'feat:'."""
        commit = Commit(
            hash='abc123',
            author='Test User',
            email='test@example.com',
            date=datetime.now(),
            message='feat: Add new feature'
        )
        
        categorized = self.categorizer.categorize_commit(commit)
        self.assertEqual(categorized.category, Category.ADDED)
    
    def test_categorize_fix_conventional(self):
        """Test: Categorize conventional commit 'fix:'."""
        commit = Commit(
            hash='def456',
            author='Test User',
            email='test@example.com',
            date=datetime.now(),
            message='fix: Resolve bug in parser'
        )
        
        categorized = self.categorizer.categorize_commit(commit)
        self.assertEqual(categorized.category, Category.FIXED)
    
    def test_categorize_keyword_add(self):
        """Test: Categorize using keyword 'add'."""
        commit = Commit(
            hash='ghi789',
            author='Test User',
            email='test@example.com',
            date=datetime.now(),
            message='Add new configuration option'
        )
        
        categorized = self.categorizer.categorize_commit(commit)
        self.assertEqual(categorized.category, Category.ADDED)
    
    def test_categorize_keyword_remove(self):
        """Test: Categorize using keyword 'delete' (removed)."""
        commit = Commit(
            hash='jkl012',
            author='Test User',
            email='test@example.com',
            date=datetime.now(),
            message='Delete old configuration'
        )
        
        categorized = self.categorizer.categorize_commit(commit)
        self.assertEqual(categorized.category, Category.REMOVED)
    
    def test_categorize_default_changed(self):
        """Test: Default categorization to CHANGED."""
        commit = Commit(
            hash='mno345',
            author='Test User',
            email='test@example.com',
            date=datetime.now(),
            message='Update README documentation'
        )
        
        categorized = self.categorizer.categorize_commit(commit)
        self.assertEqual(categorized.category, Category.CHANGED)
    
    def test_categorize_batch(self):
        """Test: Batch categorization of multiple commits."""
        commits = [
            Commit('a1', 'User', 'e@e.com', datetime.now(), 'feat: Feature 1'),
            Commit('a2', 'User', 'e@e.com', datetime.now(), 'fix: Bug 1'),
            Commit('a3', 'User', 'e@e.com', datetime.now(), 'Update something'),
        ]
        
        categorized = self.categorizer.categorize_batch(commits)
        
        self.assertEqual(len(categorized), 3)
        self.assertEqual(categorized[0].category, Category.ADDED)
        self.assertEqual(categorized[1].category, Category.FIXED)
        self.assertEqual(categorized[2].category, Category.CHANGED)


# ═══════════════════════════════════════════════════════════════════
# TEST: VERSION GROUPER
# ═══════════════════════════════════════════════════════════════════

class TestVersionGrouper(unittest.TestCase):
    """Test version grouping functionality."""
    
    def setUp(self):
        """Set up grouper for testing."""
        self.grouper = VersionGrouper()
    
    def test_group_no_tags_unreleased(self):
        """Test: Group all commits as Unreleased when no tags."""
        from changelog import CategorizedCommit
        
        commits = [
            CategorizedCommit('a1', 'User', 'e@e.com', datetime.now(), 'feat: Feature 1', Category.ADDED),
            CategorizedCommit('a2', 'User', 'e@e.com', datetime.now(), 'fix: Bug 1', Category.FIXED),
        ]
        
        groups = self.grouper.group_by_version(commits, [])
        
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].version, "Unreleased")
        self.assertIsNone(groups[0].date)
    
    def test_group_with_tags(self):
        """Test: Group commits by version tags."""
        from changelog import CategorizedCommit
        
        date1 = datetime(2026, 1, 1)
        date2 = datetime(2026, 2, 1)
        
        commits = [
            CategorizedCommit('a1', 'User', 'e@e.com', date1, 'feat: Feature 1', Category.ADDED),
            CategorizedCommit('a2', 'User', 'e@e.com', date2, 'fix: Bug 1', Category.FIXED),
        ]
        
        tags = [
            Tag('v1.0.0', 'a2', date2)
        ]
        
        groups = self.grouper.group_by_version(commits, tags)
        
        # Should have at least the tagged version
        self.assertGreaterEqual(len(groups), 1)
    
    def test_parse_version_with_v_prefix(self):
        """Test: Parse version with 'v' prefix."""
        version = self.grouper._parse_version('v1.2.3')
        self.assertEqual(version, '1.2.3')
    
    def test_parse_version_without_v_prefix(self):
        """Test: Parse version without 'v' prefix."""
        version = self.grouper._parse_version('1.2.3')
        self.assertEqual(version, '1.2.3')


# ═══════════════════════════════════════════════════════════════════
# TEST: CHANGELOG FORMATTER
# ═══════════════════════════════════════════════════════════════════

class TestChangelogFormatter(unittest.TestCase):
    """Test changelog formatting."""
    
    def setUp(self):
        """Set up formatter for testing."""
        self.formatter = ChangelogFormatter()
    
    def test_format_markdown_basic(self):
        """Test: Format basic changelog as Markdown."""
        from changelog import CategorizedCommit
        
        commits = [
            CategorizedCommit('a1', 'User', 'e@e.com', datetime.now(), 'feat: Feature 1', Category.ADDED)
        ]
        
        group = VersionGroup(
            version="1.0.0",
            date=datetime(2026, 2, 10),
            commits_by_category={Category.ADDED: commits}
        )
        
        markdown = self.formatter.format_markdown([group])
        
        self.assertIn('# Changelog', markdown)
        self.assertIn('## [1.0.0] - 2026-02-10', markdown)
        self.assertIn('### Added', markdown)
        self.assertIn('Feature 1', markdown)
    
    def test_format_json_basic(self):
        """Test: Format basic changelog as JSON."""
        from changelog import CategorizedCommit
        
        commits = [
            CategorizedCommit('a1', 'User', 'e@e.com', datetime.now(), 'feat: Feature 1', Category.ADDED)
        ]
        
        group = VersionGroup(
            version="1.0.0",
            date=datetime(2026, 2, 10),
            commits_by_category={Category.ADDED: commits}
        )
        
        json_output = self.formatter.format_json([group])
        data = json.loads(json_output)
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['version'], '1.0.0')
        self.assertIn('Added', data[0]['changes'])
    
    def test_format_text_basic(self):
        """Test: Format basic changelog as plain text."""
        from changelog import CategorizedCommit
        
        commits = [
            CategorizedCommit('a1', 'User', 'e@e.com', datetime.now(), 'feat: Feature 1', Category.ADDED)
        ]
        
        group = VersionGroup(
            version="1.0.0",
            date=datetime(2026, 2, 10),
            commits_by_category={Category.ADDED: commits}
        )
        
        text = self.formatter.format_text([group])
        
        self.assertIn('CHANGELOG', text)
        self.assertIn('VERSION 1.0.0', text)
        self.assertIn('ADDED:', text)
        self.assertIn('Feature 1', text)
    
    def test_clean_commit_message(self):
        """Test: Clean conventional commit prefixes."""
        cleaned = self.formatter._clean_commit_message('feat: add new feature')
        self.assertEqual(cleaned, 'Add new feature')
        
        cleaned = self.formatter._clean_commit_message('fix: resolve bug')
        self.assertEqual(cleaned, 'Resolve bug')


# ═══════════════════════════════════════════════════════════════════
# TEST: OUTPUT WRITER
# ═══════════════════════════════════════════════════════════════════

class TestOutputWriter(unittest.TestCase):
    """Test file output functionality."""
    
    def setUp(self):
        """Set up temp directory for file tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.writer = OutputWriter()
    
    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_write_changelog_new_file(self):
        """Test: Write changelog to new file."""
        output_path = self.temp_path / 'CHANGELOG.md'
        content = '# Changelog\n\nTest content'
        
        self.writer.write_changelog(content, output_path)
        
        self.assertTrue(output_path.exists())
        self.assertEqual(output_path.read_text(encoding='utf-8'), content)
    
    def test_write_changelog_overwrite_with_backup(self):
        """Test: Overwrite existing file creates backup."""
        output_path = self.temp_path / 'CHANGELOG.md'
        output_path.write_text('Old content')
        
        new_content = '# New Changelog\n\nNew content'
        self.writer.write_changelog(new_content, output_path)
        
        # Check new content
        self.assertEqual(output_path.read_text(encoding='utf-8'), new_content)
        
        # Check backup exists
        backups = list(self.temp_path.glob('CHANGELOG.md.backup.*'))
        self.assertGreater(len(backups), 0)


# ═══════════════════════════════════════════════════════════════════
# TEST: INTEGRATION
# ═══════════════════════════════════════════════════════════════════

class TestIntegration(unittest.TestCase):
    """Test end-to-end changelog generation."""
    
    def setUp(self):
        """Create test git repository."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)
        
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=self.repo_path, check=True, capture_output=True)
        
        # Create commits
        (self.repo_path / 'file1.txt').write_text('Content 1')
        subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'feat: Add feature 1'], cwd=self.repo_path, check=True, capture_output=True)
        
        (self.repo_path / 'file2.txt').write_text('Content 2')
        subprocess.run(['git', 'add', '.'], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'fix: Fix bug 1'], cwd=self.repo_path, check=True, capture_output=True)
    
    def tearDown(self):
        """Clean up test repository."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_changelog_full_pipeline(self):
        """Test: Full pipeline from git repo to CHANGELOG.md."""
        output_path = self.repo_path / 'CHANGELOG.md'
        
        changelog = ChangeLog.generate(
            repo_path=str(self.repo_path),
            output_path=str(output_path),
            format='markdown',
            backup=False
        )
        
        # Verify file created
        self.assertTrue(output_path.exists())
        
        # Verify content structure
        content = output_path.read_text(encoding='utf-8')
        self.assertIn('# Changelog', content)
        self.assertIn('## [Unreleased]', content)
        self.assertIn('### Added', content)
        self.assertIn('### Fixed', content)
        self.assertIn('Add feature 1', content)
        self.assertIn('Fix bug 1', content)


# ═══════════════════════════════════════════════════════════════════
# TEST RUNNER
# ═══════════════════════════════════════════════════════════════════

def run_tests():
    """Run all tests with nice output."""
    print("=" * 70)
    print("TESTING: ChangeLog v1.0.0")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGitLogParser))
    suite.addTests(loader.loadTestsFromTestCase(TestCommitCategorizer))
    suite.addTests(loader.loadTestsFromTestCase(TestVersionGrouper))
    suite.addTests(loader.loadTestsFromTestCase(TestChangelogFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestOutputWriter))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"RESULTS: {result.testsRun} tests")
    print(f"[OK] Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    if result.failures:
        print(f"[X] Failed: {len(result.failures)}")
    if result.errors:
        print(f"[X] Errors: {len(result.errors)}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
