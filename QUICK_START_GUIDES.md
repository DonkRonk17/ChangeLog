# ChangeLog - Quick Start Guides

## 📖 ABOUT THESE GUIDES

Each Team Brain agent has a **5-minute quick-start guide** tailored to their role and workflows.

**Choose your guide:**
- [Forge (Orchestrator)](#-forge-quick-start)
- [Atlas (Executor)](#-atlas-quick-start)
- [Clio (Linux Agent)](#-clio-quick-start)
- [Nexus (Multi-Platform)](#-nexus-quick-start)
- [Bolt (Free Executor)](#-bolt-quick-start)

---

## 🔥 FORGE QUICK START

**Role:** Orchestrator / Reviewer
**Time:** 5 minutes
**Goal:** Use ChangeLog to review tool quality and generate missing changelogs

### Step 1: Installation Check
```bash
python C:\Users\logan\OneDrive\Documents\AutoProjects\ChangeLog\changelog.py --version
# Expected: changelog 1.0.0 (Team Brain)
```

### Step 2: First Use - Review a Tool
```bash
# Navigate to any Team Brain tool
cd C:\Users\logan\OneDrive\Documents\AutoProjects\TimeSync

# Check commit quality
python ..\ChangeLog\changelog.py validate
# Shows compliance grade (A-F)

# View statistics
python ..\ChangeLog\changelog.py stats
# Shows category breakdown, author stats
```

### Step 3: Generate Missing Changelog
```bash
# Generate changelog for a tool that doesn't have one
python ..\ChangeLog\changelog.py generate
# Creates CHANGELOG.md
```

### Step 4: Python API for Reviews
```python
from changelog import ChangeLog

# During tool review
cl = ChangeLog(repo_path="C:/path/to/tool")
validation = cl.validate_commits()

if validation['compliance_pct'] < 50:
    print(f"Low compliance: {validation['compliance_pct']}%")
    print("Recommend conventional commits")
```

### Common Forge Commands
```bash
# Validate any tool's commits
python changelog.py validate /path/to/tool

# Generate changelog for review
python changelog.py preview /path/to/tool

# Get JSON stats for reporting
python changelog.py stats /path/to/tool --json
```

### Next Steps for Forge
1. Add changelog validation to tool review checklist
2. Run batch validation across portfolio
3. Track commit compliance improvement over time

---

## ⚡ ATLAS QUICK START

**Role:** Executor / Builder
**Time:** 5 minutes
**Goal:** Generate changelogs as part of the Build Protocol Phase 9

### Step 1: Installation Check
```bash
python -c "from changelog import ChangeLog; print('OK')"
# Expected: OK
```

### Step 2: First Use - Generate Changelog
```bash
# During tool build, in the tool directory
cd C:\Users\logan\OneDrive\Documents\AutoProjects\MyNewTool

# Generate changelog
python ..\ChangeLog\changelog.py generate

# Expected: [OK] Changelog generated: CHANGELOG.md (XX lines)
```

### Step 3: Integration with Build Workflows
```python
# Add to Phase 9: Deployment
from changelog import ChangeLog

# Generate changelog
cl = ChangeLog(repo_path=".")
cl.generate(output_file="CHANGELOG.md")

# Get metrics for BUILD_REPORT.md
stats = cl.get_stats()
validation = cl.validate_commits()
print(f"Commits: {stats['total_commits']}")
print(f"Compliance: {validation['compliance_pct']}%")
```

### Step 4: Common Atlas Commands
```bash
# Generate changelog for current tool
python changelog.py generate

# Include author names
python changelog.py generate --with-author

# Preview before committing
python changelog.py preview

# Validate commit quality
python changelog.py validate
```

### Next Steps for Atlas
1. Add `changelog generate` to Phase 9 checklist
2. Include changelog stats in BUILD_REPORT.md
3. Use conventional commits for better categorization

---

## 🐧 CLIO QUICK START

**Role:** Linux / Ubuntu Agent
**Time:** 5 minutes
**Goal:** Generate changelogs in Linux/WSL environment

### Step 1: Linux Installation
```bash
# Clone from GitHub
git clone https://github.com/DonkRonk17/ChangeLog.git
cd ChangeLog

# Verify
python3 changelog.py --version
# Expected: changelog 1.0.0 (Team Brain)
```

### Step 2: First Use - Generate Changelog
```bash
# Navigate to any project
cd ~/projects/my-tool

# Generate changelog
python3 /path/to/changelog.py generate

# Or add alias
echo 'alias changelog="python3 /path/to/changelog.py"' >> ~/.bashrc
source ~/.bashrc
changelog generate
```

### Step 3: Batch Generation
```bash
# Generate changelogs for all repos in a directory
for dir in ~/projects/*/; do
    if [ -d "$dir/.git" ]; then
        echo "Processing: $(basename $dir)"
        python3 changelog.py generate "$dir"
    fi
done
```

### Step 4: Common Clio Commands
```bash
# Generate for current repo
changelog generate

# JSON output for processing
changelog stats --json | jq '.categories'

# Validate commit messages
changelog validate

# Filter by date
changelog generate --since "1 month ago"
```

### Next Steps for Clio
1. Set up bash alias for quick access
2. Run batch generation across all tools
3. Add to deployment scripts

---

## 🌐 NEXUS QUICK START

**Role:** Multi-Platform Agent
**Time:** 5 minutes
**Goal:** Generate changelogs across different platforms

### Step 1: Platform Detection
```python
import platform
from changelog import ChangeLog

print(f"Platform: {platform.system()}")
cl = ChangeLog(repo_path=".")
# Works on Windows, Linux, macOS identically
```

### Step 2: First Use - Cross-Platform
```python
from changelog import ChangeLog
from pathlib import Path

# Cross-platform path handling (built-in)
repo_path = Path.home() / "projects" / "my-tool"
cl = ChangeLog(repo_path=str(repo_path))
output = cl.generate()
print(output[:200])
```

### Step 3: Platform-Specific Considerations

**Windows:**
- Paths use backslashes but pathlib handles conversion
- Console encoding: Set `chcp 65001` for UTF-8 if needed
- PowerShell batch: Use `Get-ChildItem` for directory iteration

**Linux:**
- Standard Python 3 usage
- Git paths use forward slashes
- Bash batch: Use `for dir in */` pattern

**macOS:**
- Same as Linux usage
- Homebrew git: `brew install git`

### Step 4: Common Nexus Commands
```bash
# Cross-platform (works everywhere)
python changelog.py generate
python changelog.py validate
python changelog.py stats --json
```

### Next Steps for Nexus
1. Test on all platforms
2. Create platform-specific batch scripts
3. Report any cross-platform issues

---

## 🆓 BOLT QUICK START

**Role:** Free Executor (Cline + Grok)
**Time:** 5 minutes
**Goal:** Batch changelog generation without API costs

### Step 1: Verify Free Access
```bash
# No API key required!
python changelog.py --version
# changelog 1.0.0 (Team Brain)
```

### Step 2: First Use - Batch Mode
```bash
# Generate changelogs for ALL tools (no API costs!)
cd C:\Users\logan\OneDrive\Documents\AutoProjects

# PowerShell batch
Get-ChildItem -Directory | ForEach-Object {
    if (Test-Path "$($_.FullName)\.git") {
        Write-Host "Processing: $($_.Name)"
        python ChangeLog\changelog.py generate $_.FullName -o "$($_.FullName)\CHANGELOG.md"
    }
}
```

### Step 3: Cost-Free Analysis
```bash
# Validate all repos (free!)
Get-ChildItem -Directory | ForEach-Object {
    if (Test-Path "$($_.FullName)\.git") {
        Write-Host "`n=== $($_.Name) ==="
        python ChangeLog\changelog.py validate $_.FullName
    }
}
```

### Step 4: Common Bolt Commands
```bash
# Batch generate (save API calls!)
python changelog.py generate /path/to/repo1
python changelog.py generate /path/to/repo2

# JSON output for data collection
python changelog.py stats --json > stats.json
```

### Next Steps for Bolt
1. Run batch generation across all 80+ tools
2. Collect compliance stats for team report
3. Report issues via Synapse

---

## 📚 ADDITIONAL RESOURCES

**For All Agents:**
- Full Documentation: [README.md](README.md)
- Examples: [EXAMPLES.md](EXAMPLES.md)
- Integration Plan: [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md)
- Cheat Sheet: [CHEAT_SHEET.txt](CHEAT_SHEET.txt)

**Standards:**
- [Keep a Changelog](https://keepachangelog.com)
- [Conventional Commits](https://conventionalcommits.org)

**Support:**
- GitHub Issues: https://github.com/DonkRonk17/ChangeLog/issues
- Synapse: Post in THE_SYNAPSE/active/
- Direct: Message ATLAS

---

**Last Updated:** February 7, 2026
**Maintained By:** ATLAS (Team Brain)
