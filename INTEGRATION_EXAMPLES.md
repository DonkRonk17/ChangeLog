# ChangeLog - Integration Examples

## 🎯 INTEGRATION PHILOSOPHY

ChangeLog is designed to work seamlessly with other Team Brain tools. This document provides **copy-paste-ready code examples** for common integration patterns.

---

## 📚 TABLE OF CONTENTS

1. [Pattern 1: ChangeLog + GitFlow](#pattern-1-changelog--gitflow)
2. [Pattern 2: ChangeLog + SynapseLink](#pattern-2-changelog--synapselink)
3. [Pattern 3: ChangeLog + CodeMetrics](#pattern-3-changelog--codemetrics)
4. [Pattern 4: ChangeLog + ToolRegistry](#pattern-4-changelog--toolregistry)
5. [Pattern 5: ChangeLog + SessionDocGen](#pattern-5-changelog--sessiondocgen)
6. [Pattern 6: ChangeLog + AgentHealth](#pattern-6-changelog--agenthealth)
7. [Pattern 7: ChangeLog + ConfigManager](#pattern-7-changelog--configmanager)
8. [Pattern 8: ChangeLog + QuickBackup](#pattern-8-changelog--quickbackup)
9. [Pattern 9: Multi-Tool Build Workflow](#pattern-9-multi-tool-build-workflow)
10. [Pattern 10: Full Portfolio Analysis](#pattern-10-full-portfolio-analysis)

---

## Pattern 1: ChangeLog + GitFlow

**Use Case:** Generate changelog after GitFlow release operations.

**Why:** Automate changelog generation as part of the release workflow.

**Code:**

```python
import subprocess
from changelog import ChangeLog

# After creating a release with GitFlow
def post_release_changelog(repo_path: str, version: str):
    """Generate changelog after a GitFlow release."""
    cl = ChangeLog(repo_path=repo_path)
    
    # Generate full changelog
    output = cl.generate(output_file="CHANGELOG.md")
    
    # Commit the changelog
    subprocess.run(["git", "add", "CHANGELOG.md"], cwd=repo_path)
    subprocess.run(
        ["git", "commit", "-m", f"docs: update changelog for {version}"],
        cwd=repo_path,
    )
    
    print(f"[OK] Changelog updated for {version}")

# Usage
post_release_changelog(".", "v1.2.0")
```

**Result:** Changelog auto-generated and committed with each release.

---

## Pattern 2: ChangeLog + SynapseLink

**Use Case:** Notify Team Brain when a changelog is generated.

**Why:** Keep team informed of project documentation updates.

**Code:**

```python
import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects")

from changelog import ChangeLog

# Generate changelog
cl = ChangeLog(repo_path=".")
stats = cl.get_stats()
validation = cl.validate_commits()
cl.generate(output_file="CHANGELOG.md")

# Prepare Synapse notification
repo_name = stats['repo_name']
commit_count = stats['total_commits']
compliance = validation['compliance_pct']
top_category = max(stats['categories'], key=stats['categories'].get) if stats['categories'] else "N/A"

message = (
    f"Changelog generated for {repo_name}\n"
    f"Commits: {commit_count}\n"
    f"Top category: {top_category}\n"
    f"Commit compliance: {compliance}%\n"
)

print(message)
# Send via SynapseLink if available
try:
    from SynapseLink.synapselink import quick_send
    quick_send("TEAM", f"Changelog: {repo_name}", message)
except ImportError:
    print("SynapseLink not available, skipping notification")
```

**Result:** Team notified of changelog generation with key metrics.

---

## Pattern 3: ChangeLog + CodeMetrics

**Use Case:** Combine changelog stats with code health metrics.

**Why:** Comprehensive project health dashboard.

**Code:**

```python
import json
import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects")

from changelog import ChangeLog

# Get changelog metrics
cl = ChangeLog(repo_path=".")
cl_stats = cl.get_stats()
cl_validation = cl.validate_commits()

# Get code metrics (if CodeMetrics available)
try:
    from CodeMetrics.codemetrics import CodeMetrics
    cm = CodeMetrics()
    cm_report = cm.analyze(".")
    
    # Combined health report
    health = {
        "code": {
            "total_lines": cm_report.get("total_lines", 0),
            "health_grade": cm_report.get("grade", "N/A"),
        },
        "commits": {
            "total": cl_stats['total_commits'],
            "compliance": cl_validation['compliance_pct'],
            "top_categories": dict(list(cl_stats['categories'].items())[:5]),
        },
    }
    print(json.dumps(health, indent=2))
except ImportError:
    # CodeMetrics not available, just show changelog stats
    print(json.dumps({"commits": cl_stats}, indent=2))
```

**Result:** Unified code and commit health metrics.

---

## Pattern 4: ChangeLog + ToolRegistry

**Use Case:** Ensure ChangeLog is registered in the tool ecosystem.

**Why:** Tool discovery and ecosystem awareness.

**Code:**

```python
import sys
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects")

# Check if ChangeLog is registered
try:
    from ToolRegistry.toolregistry import ToolRegistry
    
    registry = ToolRegistry()
    
    # Check registration
    if not registry.get_tool("ChangeLog"):
        registry.register_tool(
            name="ChangeLog",
            version="1.0.0",
            description="Automated Changelog Generator",
            path="C:/Users/logan/OneDrive/Documents/AutoProjects/ChangeLog",
            category="documentation",
            tags=["changelog", "git", "documentation", "conventional-commits"],
        )
        print("[OK] ChangeLog registered in ToolRegistry")
    else:
        print("[OK] ChangeLog already registered")
except ImportError:
    print("ToolRegistry not available")
```

**Result:** ChangeLog discoverable in the Team Brain ecosystem.

---

## Pattern 5: ChangeLog + SessionDocGen

**Use Case:** Include changelog metrics in session documentation.

**Why:** Track project progress across sessions.

**Code:**

```python
from changelog import ChangeLog

# Get project stats for session doc
def get_changelog_summary(repo_path: str) -> dict:
    """Get changelog summary for session documentation."""
    cl = ChangeLog(repo_path=repo_path)
    stats = cl.get_stats()
    validation = cl.validate_commits()
    
    return {
        "repo": stats['repo_name'],
        "total_commits": stats['total_commits'],
        "commit_compliance": f"{validation['compliance_pct']}%",
        "categories": stats['categories'],
        "date_range": stats['date_range'],
    }

# Usage in session doc generation
summary = get_changelog_summary(".")
print(f"## Project: {summary['repo']}")
print(f"- Commits: {summary['total_commits']}")
print(f"- Compliance: {summary['commit_compliance']}")
```

**Result:** Session docs enriched with commit analytics.

---

## Pattern 6: ChangeLog + AgentHealth

**Use Case:** Track changelog generation as an agent health metric.

**Why:** Ensure documentation keeps pace with development.

**Code:**

```python
import os
from pathlib import Path
from changelog import ChangeLog

def check_changelog_health(project_dir: str) -> dict:
    """Check if project's changelog is up to date."""
    changelog_path = Path(project_dir) / "CHANGELOG.md"
    
    result = {
        "has_changelog": changelog_path.exists(),
        "commits_since_last_update": 0,
        "needs_update": False,
    }
    
    if not changelog_path.exists():
        result["needs_update"] = True
        try:
            cl = ChangeLog(repo_path=project_dir)
            stats = cl.get_stats()
            result["commits_since_last_update"] = stats["total_commits"]
        except Exception:
            pass
    else:
        # Check if changelog is outdated
        changelog_mtime = os.path.getmtime(changelog_path)
        git_dir = Path(project_dir) / ".git"
        if git_dir.exists():
            head_mtime = os.path.getmtime(git_dir / "refs" / "heads")
            if head_mtime > changelog_mtime:
                result["needs_update"] = True
    
    return result

# Usage
health = check_changelog_health(".")
if health["needs_update"]:
    print("[!] Changelog needs update")
else:
    print("[OK] Changelog is current")
```

**Result:** Automated staleness detection for changelogs.

---

## Pattern 7: ChangeLog + ConfigManager

**Use Case:** Centralize changelog configuration.

**Why:** Consistent changelog settings across all projects.

**Code:**

```python
import json
from pathlib import Path
from changelog import ChangeLog

# Create a shared .changelogrc template
def create_team_config(project_dir: str):
    """Create standard Team Brain changelog config."""
    config = {
        "output_file": "CHANGELOG.md",
        "output_format": "markdown",
        "header": "# Changelog",
        "include_hash": True,
        "include_author": False,
        "exclude_patterns": [
            "^Merge (branch|pull request)",
            "^WIP\\b",
            "^wip\\b"
        ],
    }
    
    config_path = Path(project_dir) / ".changelogrc"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"[OK] Created .changelogrc in {project_dir}")

# Usage
create_team_config(".")

# Generate using team config
cl = ChangeLog(repo_path=".", config_file=".changelogrc")
cl.generate(output_file="CHANGELOG.md")
```

**Result:** Consistent changelog configuration across Team Brain.

---

## Pattern 8: ChangeLog + QuickBackup

**Use Case:** Backup changelog before regeneration.

**Why:** Preserve manual edits and historical versions.

**Code:**

```python
import shutil
from datetime import datetime
from pathlib import Path
from changelog import ChangeLog

def safe_regenerate(repo_path: str):
    """Regenerate changelog with backup of existing."""
    changelog_path = Path(repo_path) / "CHANGELOG.md"
    
    # Backup existing changelog
    if changelog_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = changelog_path.with_suffix(f".{timestamp}.md.bak")
        shutil.copy2(changelog_path, backup_path)
        print(f"[OK] Backup: {backup_path.name}")
    
    # Regenerate
    cl = ChangeLog(repo_path=repo_path)
    cl.generate(output_file=str(changelog_path))
    print("[OK] Changelog regenerated")

# Usage
safe_regenerate(".")
```

**Result:** Safe changelog regeneration with automatic backup.

---

## Pattern 9: Multi-Tool Build Workflow

**Use Case:** Complete tool build workflow using ChangeLog.

**Why:** Demonstrate production-grade integration.

**Code:**

```python
import json
from pathlib import Path
from changelog import ChangeLog

def build_phase_9_changelog(tool_dir: str, tool_name: str):
    """Phase 9 of Build Protocol - Changelog generation."""
    print(f"\n=== Phase 9: Changelog for {tool_name} ===")
    
    cl = ChangeLog(repo_path=tool_dir)
    
    # 1. Generate changelog
    output = cl.generate(output_file=str(Path(tool_dir) / "CHANGELOG.md"))
    lines = output.count('\n') + 1
    print(f"[OK] CHANGELOG.md: {lines} lines")
    
    # 2. Validate commits
    validation = cl.validate_commits()
    print(f"[OK] Compliance: {validation['compliance_pct']}%")
    
    # 3. Get stats for BUILD_REPORT
    stats = cl.get_stats()
    
    # 4. Build report data
    report_data = {
        "changelog_lines": lines,
        "total_commits": stats['total_commits'],
        "commit_compliance": validation['compliance_pct'],
        "categories": stats['categories'],
        "authors": stats['authors'],
    }
    
    print(f"[OK] Stats collected for BUILD_REPORT")
    return report_data

# Usage
report = build_phase_9_changelog(".", "MyTool")
print(json.dumps(report, indent=2))
```

**Result:** Complete Phase 9 changelog workflow with metrics.

---

## Pattern 10: Full Portfolio Analysis

**Use Case:** Analyze commit quality across the entire portfolio.

**Why:** Portfolio-wide quality assessment and improvement tracking.

**Code:**

```python
import json
import os
from pathlib import Path
from changelog import ChangeLog

def portfolio_analysis(base_dir: str):
    """Analyze all git repos in a directory."""
    base = Path(base_dir)
    results = []
    
    for item in sorted(base.iterdir()):
        if item.is_dir() and (item / ".git").exists():
            try:
                cl = ChangeLog(repo_path=str(item))
                stats = cl.get_stats()
                validation = cl.validate_commits()
                
                results.append({
                    "tool": item.name,
                    "commits": stats['total_commits'],
                    "compliance": validation['compliance_pct'],
                    "has_changelog": (item / "CHANGELOG.md").exists(),
                    "top_category": max(stats['categories'], key=stats['categories'].get)
                        if stats['categories'] else "N/A",
                })
            except Exception as e:
                results.append({
                    "tool": item.name,
                    "error": str(e),
                })
    
    # Summary
    total = len([r for r in results if 'commits' in r])
    avg_compliance = sum(r.get('compliance', 0) for r in results) / max(total, 1)
    with_changelog = sum(1 for r in results if r.get('has_changelog', False))
    
    print(f"\nPortfolio Analysis: {total} repositories")
    print(f"Average compliance: {avg_compliance:.1f}%")
    print(f"With CHANGELOG.md: {with_changelog}/{total}")
    print(f"\nTop 10 by compliance:")
    
    sorted_results = sorted(
        [r for r in results if 'compliance' in r],
        key=lambda x: x['compliance'],
        reverse=True,
    )
    for r in sorted_results[:10]:
        status = "[OK]" if r.get('has_changelog') else "[  ]"
        print(f"  {status} {r['tool']:30s} {r['compliance']:5.1f}% ({r['commits']} commits)")
    
    return results

# Usage
results = portfolio_analysis("C:/Users/logan/OneDrive/Documents/AutoProjects")
```

**Result:** Complete portfolio-wide commit quality analysis.

---

## 📊 RECOMMENDED INTEGRATION PRIORITY

**Week 1 (Essential):**
1. GitFlow - Post-release changelog generation
2. Build Protocol - Phase 9 integration
3. SynapseLink - Team notifications

**Week 2 (Productivity):**
4. CodeMetrics - Combined health reports
5. ConfigManager - Shared .changelogrc
6. SessionDocGen - Session enrichment

**Week 3 (Advanced):**
7. Portfolio analysis script
8. CI/CD pipeline integration
9. Automated staleness detection

---

## 🔧 TROUBLESHOOTING INTEGRATIONS

**Import Errors:**
```python
# Ensure AutoProjects is in Python path
import sys
from pathlib import Path
sys.path.append(str(Path.home() / "OneDrive/Documents/AutoProjects"))

# Or use ChangeLog directory specifically
sys.path.append("C:/Users/logan/OneDrive/Documents/AutoProjects/ChangeLog")
from changelog import ChangeLog
```

**Git Path Issues:**
```python
# Always use absolute paths for repo_path
from pathlib import Path
repo = str(Path("/path/to/repo").resolve())
cl = ChangeLog(repo_path=repo)
```

---

**Last Updated:** February 7, 2026
**Maintained By:** ATLAS (Team Brain)
