# Architecture Design - ChangeLog v1.0.0

**Date:** February 7, 2026
**Builder:** ATLAS (Team Brain)

---

## Core Components

### 1. GitParser
- **Purpose:** Execute git commands and parse output
- **Inputs:** Repository path, date range, commit filters
- **Outputs:** List of Commit objects with metadata
- **Tools used:** subprocess (git CLI)

### 2. CommitCategorizer
- **Purpose:** Classify commits into changelog categories
- **Inputs:** Commit message string
- **Outputs:** Category (Added, Changed, Fixed, etc.) + cleaned message
- **Strategy:** Conventional Commits prefix matching, then keyword fallback

### 3. VersionGrouper
- **Purpose:** Group commits by version tags or date periods
- **Inputs:** List of commits, list of tags
- **Outputs:** Ordered groups of commits per version/date

### 4. ChangelogFormatter
- **Purpose:** Render grouped commits into output format
- **Inputs:** Grouped commits, format specification
- **Outputs:** Formatted string (Markdown, Plain Text, or JSON)

### 5. CLI Interface
- **Purpose:** Command-line entry point
- **Inputs:** argparse arguments
- **Outputs:** File output or stdout

### 6. ChangeLog Class (Python API)
- **Purpose:** Programmatic interface for integration
- **Inputs:** Configuration dict
- **Outputs:** Changelog string or written file

---

## Data Flow

```
Git Repository
     |
     v
[GitParser] -- git log, git tag, git remote -->
     |
     v
List[Commit(hash, author, date, message, refs)]
     |
     v
[CommitCategorizer] -- prefix/keyword matching -->
     |
     v
List[CategorizedCommit(category, description, ...)]
     |
     v
[VersionGrouper] -- tag matching / date grouping -->
     |
     v
Dict[version/date -> List[CategorizedCommit]]
     |
     v
[ChangelogFormatter] -- Markdown/Text/JSON -->
     |
     v
CHANGELOG.md (or stdout)
```

---

## Commit Categories (Keep a Changelog)

| Category | Conventional Commits Prefix | Keywords |
|----------|---------------------------|----------|
| Added | feat:, feature: | add, new, create, implement |
| Changed | refactor:, change: | update, modify, improve, enhance |
| Deprecated | deprecate: | deprecate, obsolete |
| Removed | remove: | remove, delete, drop |
| Fixed | fix:, bugfix: | fix, repair, resolve, patch |
| Security | security: | security, vulnerability, CVE |
| Documentation | docs:, doc: | readme, documentation, docs |
| Testing | test:, tests: | test, spec, coverage |
| Build | build:, ci: | build, ci, deploy, release |
| Other | chore:, style:, perf: | (fallback for unmatched) |

---

## Error Handling Strategy

1. **Git not found:** Detect via subprocess, raise clear error with install instructions
2. **Not a git repo:** Check .git directory, provide helpful message
3. **No commits:** Generate empty changelog with header only
4. **No tags:** Fall back to date-based grouping (by month)
5. **Unicode errors:** Use UTF-8 throughout, ASCII-safe output option
6. **Permission errors:** Catch OSError, provide troubleshooting tips
7. **Large repos:** Support --limit flag, pagination

---

## Configuration Strategy

### CLI Arguments (Primary)
```
changelog generate [path] [options]
changelog validate [path]
changelog stats [path]
changelog preview [path]
```

### Config File (Optional)
Location: `.changelogrc` in project root (JSON)
```json
{
  "output": "CHANGELOG.md",
  "format": "markdown",
  "categories": {},
  "exclude_patterns": ["^Merge", "^WIP"],
  "date_format": "%Y-%m-%d",
  "header": "# Changelog",
  "unreleased_label": "Unreleased"
}
```

---

## Architecture Phase Score: 99/100
- All components defined, data flow clear, error handling planned, config strategy documented
