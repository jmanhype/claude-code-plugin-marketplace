# ACE Context Engineering Plugin - Code Archaeology Report

**Date**: 2025-10-27
**Plugin Version**: 2.0.1
**Total Size**: ~6.8 MB

---

## Executive Summary

Comprehensive file and folder analysis of the ACE Context Engineering plugin to identify cleanup opportunities and improve plugin structure.

**Key Findings**:
- 6.6 MB of experimental outputs in `benchmarks/experiments/` (1,710 files)
- Multiple duplicate/obsolete documentation files
- Epoch playbook snapshots in skills folder
- Debug scripts and experimental code in benchmarks
- __pycache__ directories not .gitignored

---

## Directory Structure

```
ace-context-engineering/  (6.8 MB total)
├── plugin.json                     [4 KB]   ✅ KEEP - Required
├── README.md                       [12 KB]  ✅ KEEP - Required
├── CHANGELOG.md                    [4 KB]   ✅ KEEP - Required
├── ARCHITECTURE.md                 [12 KB]  ⚠️  REVIEW - May consolidate
├── IMPLEMENTATION_SUMMARY.md       [16 KB]  ⚠️  REVIEW - May consolidate
├── MIGRATION_V2.md                 [8 KB]   ⚠️  REVIEW - May archive
├── CLAUDE_CODE_USAGE.md            [12 KB]  ⚠️  REVIEW - Duplicate info?
├── CLAUDE_CODE_OS_COMPLIANCE.md    [12 KB]  ⚠️  REVIEW - Duplicate info?
├── SYSTEM_ARCHAEOLOGY.md           [20 KB]  ⚠️  REVIEW - Old archaeology
├── delta_ace_implementation.json   [8 KB]   ⚠️  REVIEW - Still needed?
│
├── .claude/                        ✅ KEEP - Plugin hooks
│   └── hooks/
│       └── logs/                   ⚠️  GITIGNORE - Temporary logs
│           ├── chat.json
│           ├── pre_tool_use.json
│           ├── post_tool_use.json
│           └── stop.json
│
├── schemas/                        [32 KB]  ✅ KEEP - Required schemas
│   ├── bullet.schema.json
│   ├── delta.schema.json
│   ├── curator_output.schema.json
│   ├── reflector_output.schema.json
│   ├── generator_output.schema.json
│   └── feedback_event.schema.json
│
├── examples/                       [4 KB]   ✅ KEEP - Usage examples
│   └── basic_usage.py
│
├── scripts/                        [24 KB]  ✅ KEEP - Utility scripts
│   ├── detect_conflicts.py
│   ├── merge_deltas.py
│   ├── retrieve_bullets.py
│   ├── update_counters.py
│   └── validate_delta.py
│
├── src/                            [88 KB]  ⚠️  UNKNOWN - Not analyzed
│   └── [contents unknown]
│
├── skills/                         [68 KB]  ⚠️  CLEANUP NEEDED
│   ├── playbook.json               [6.6 KB] ✅ KEEP - Active playbook
│   ├── playbook_appworld_seed.json [3.9 KB] ✅ KEEP - Seed template
│   ├── playbook_epoch_1.json       [6.6 KB] ❌ DELETE - Snapshot, use git
│   ├── playbook_epoch_2.json       [4.2 KB] ❌ DELETE - Snapshot, use git
│   ├── playbook_epoch_3.json       [4.2 KB] ❌ DELETE - Snapshot, use git
│   ├── playbook_epoch_4.json       [4.2 KB] ❌ DELETE - Snapshot, use git
│   ├── ace-skill.md                [15 KB]  ✅ KEEP - Skill documentation
│   └── generate-appworld-code/     [5.5 KB] ✅ KEEP - Skill definition
│       └── SKILL.md
│
├── ablation/                       [12 KB]  ⚠️  REVIEW - Research artifacts
│   ├── ablation_study.py           [7.6 KB]
│   └── ablation_results.json       [1.8 KB]
│
└── benchmarks/                     [6.6 MB]  🔥 MAJOR CLEANUP NEEDED
    ├── utils/                      [~150 KB] ✅ KEEP - Core utilities
    │   ├── __init__.py
    │   ├── appworld_executor.py    [10 KB]  ✅ Core executor
    │   ├── claude_code_method.py   [16 KB]  ✅ Core method
    │   ├── reflector.py            [24 KB]  ✅ Core reflector
    │   ├── curator_staged.py       [24 KB]  ✅ Core curator
    │   ├── curator.py              [14 KB]  ⚠️  Duplicate? Review
    │   ├── bullet_retriever.py     [4.9 KB] ✅ Core utility
    │   ├── embeddings_faiss.py     [8.3 KB] ✅ Core utility
    │   ├── embeddings.py           [9.2 KB] ⚠️  Duplicate? Review
    │   ├── ace_code_generator.py   [7.6 KB] ✅ Core utility
    │   ├── base_method.py          [4.1 KB] ✅ Core utility
    │   ├── appworld_loader.py      [5.3 KB] ✅ Core utility
    │   ├── claude_code_react_agent.py       [18 KB] ⚠️ Review usage
    │   ├── claude_code_skill_invoker.py     [9.4 KB] ⚠️ Review usage
    │   ├── reflexion_executor.py   [9.0 KB] ⚠️  Review usage
    │   └── skills_executor.py      [14 KB]  ⚠️  Review usage
    │
    ├── finer/                      ⚠️  UNKNOWN - Package?
    │   └── __pycache__/            ❌ GITIGNORE
    │
    ├── experiments/                [4.5 MB]  🔥 DELETE ENTIRE FOLDER
    │   └── outputs/                [1,710 files]
    │       └── ace_interactive/
    │           └── tasks/          [6 task folders with full AppWorld DBs]
    │               ├── 287e338_1/  [~750 KB each]
    │               ├── 29caf6f_3/
    │               ├── 302c169_3/
    │               ├── afc0fce_3/
    │               ├── e7a10f8_2/
    │               └── c901732_1/
    │                   ├── dbs/            [12-14 .jsonl files]
    │                   ├── logs/
    │                   ├── version/
    │                   ├── evaluation/
    │                   ├── checkpoints/
    │                   └── misc/
    │
    ├── results/                    [~800 KB]  ⚠️  ARCHIVE OLD RESULTS
    │   ├── offline_adaptation_*.json        [33 files]
    │   ├── playbook_initial_*.json          [31 files]
    │   ├── playbook_final_*.json            [31 files]
    │   └── appworld_*.json                  [4 files]
    │
    ├── Python Scripts:             [~100 KB]
    │   ├── evaluate_appworld_interactive.py [8.3 KB] ✅ KEEP - Core eval
    │   ├── evaluate_appworld.py    [12 KB]  ⚠️  Duplicate? Review
    │   ├── run_offline_adaptation.py        [7.2 KB] ✅ KEEP - Core eval
    │   ├── run_ace_with_appworld.py         [3.6 KB] ⚠️  Review usage
    │   ├── test_appworld_executor.py        [1.2 KB] ✅ KEEP - Tests
    │   ├── test_ace_integration.py          [5.0 KB] ✅ KEEP - Tests
    │   ├── test_ace_workflow.py    [3.6 KB] ✅ KEEP - Tests
    │   ├── test_reflector_enhancements.py   [9.9 KB] ✅ KEEP - Tests
    │   ├── test_staged_curator.py  [6.7 KB] ✅ KEEP - Tests
    │   ├── skill_monitor.py        [12 KB]  ❌ DELETE - Debug/experimental
    │   ├── skill_monitor_standalone.py      [10 KB] ❌ DELETE - Debug/experimental
    │   ├── skill_monitor_simple.py [9.6 KB] ❌ DELETE - Debug/experimental
    │   ├── auto_response_generator.py       [6.6 KB] ❌ DELETE - Debug/experimental
    │   └── simple_auto_responder.py         [4.5 KB] ❌ DELETE - Debug/experimental
    │
    └── Markdown Documentation:     [~150 KB] ⚠️  MAJOR CONSOLIDATION NEEDED
        ├── BUGFIX_COMPLETE.md      [8.2 KB] ✅ KEEP - Important history
        ├── MISSION_ACCOMPLISHED.md [9.9 KB] ✅ KEEP - Important history
        ├── ACE_PAPER_ALIGNMENT.md  [12 KB]  ⚠️  Consolidate to main README
        ├── ACE_PAPER_COMPARISON.md [15 KB]  ⚠️  Consolidate to main README
        ├── ENHANCED_REFLECTOR.md   [6.5 KB] ⚠️  Consolidate or archive
        ├── ENHANCED_REFLECTOR_SUMMARY.md    [15 KB] ⚠️  Duplicate content
        ├── REFLECTOR_ENHANCEMENT_README.md  [6.0 KB] ⚠️  Duplicate content
        ├── REFLECTOR_VALIDATION_RESULTS.md  [9.6 KB] ⚠️  Archive to results
        ├── THREE_STAGE_CURATOR_VERIFICATION.md      [5.3 KB] ⚠️ Archive
        ├── INTERACTIVE_PROTOCOL_SUCCESS.md  [10 KB]  ⚠️  Archive
        ├── APPWORLD_EXECUTOR_INTEGRATION.md [7.7 KB] ⚠️  Archive
        ├── APPWORLD_EXECUTION_READY.md      [12 KB]  ⚠️  Archive
        ├── BASELINE_RESULTS.md     [8.9 KB] ⚠️  Move to results/
        ├── ACE_FINAL_REPORT.md     [12 KB]  ⚠️  Consolidate
        ├── ACE_FINAL_RESULTS.md    [4.6 KB] ⚠️  Move to results/
        ├── ACE_SUCCESS_REPORT.md   [4.8 KB] ⚠️  Consolidate
        ├── ACE_STATUS_REPORT.md    [3.2 KB] ⚠️  Consolidate
        ├── EVALUATION_STATUS.md    [13 KB]  ⚠️  Archive
        ├── IMPLEMENTATION_STATUS.md [9.4 KB] ⚠️  Archive
        └── OFFLINE_ADAPTATION_RESULTS.md    [2.4 KB] ⚠️ Move to results/
```

---

## Cleanup Recommendations

### 🔥 HIGH PRIORITY: DELETE (Saves ~5 MB)

1. **benchmarks/experiments/** folder (4.5 MB, 1,710 files)
   - **Reason**: AppWorld task execution outputs, experimental data
   - **Action**: `rm -rf benchmarks/experiments/`
   - **Impact**: Saves 4.5 MB, removes 1,710 files

2. **Epoch playbook snapshots** (19.2 KB)
   - **Files**:
     - `skills/playbook_epoch_1.json`
     - `skills/playbook_epoch_2.json`
     - `skills/playbook_epoch_3.json`
     - `skills/playbook_epoch_4.json`
   - **Reason**: Git history serves this purpose
   - **Action**: `rm skills/playbook_epoch_*.json`

3. **Debug/experimental scripts** (~43 KB)
   - **Files**:
     - `benchmarks/skill_monitor.py`
     - `benchmarks/skill_monitor_standalone.py`
     - `benchmarks/skill_monitor_simple.py`
     - `benchmarks/auto_response_generator.py`
     - `benchmarks/simple_auto_responder.py`
   - **Reason**: Development/debugging tools, not needed for plugin
   - **Action**: `rm benchmarks/*monitor*.py benchmarks/*responder*.py`

### ⚠️  MEDIUM PRIORITY: ARCHIVE OR CONSOLIDATE

4. **Old benchmark results** (~600 KB)
   - **Folder**: `benchmarks/results/`
   - **Files**: 99 JSON files from development iterations
   - **Recommendation**:
     - Keep last 5-10 most recent results
     - Archive older results to separate `archive/` folder or delete
     - Or move to `.gitignore` (don't track in repo)

5. **Duplicate/obsolete documentation** (~100 KB)
   - **Files**:
     - `SYSTEM_ARCHAEOLOGY.md` - Old archaeology, replaced by this report
     - `ENHANCED_REFLECTOR_SUMMARY.md` - Duplicate of ENHANCED_REFLECTOR.md
     - `REFLECTOR_ENHANCEMENT_README.md` - Duplicate content
     - `ACE_PAPER_COMPARISON.md` - Consolidate into main README
     - `ACE_PAPER_ALIGNMENT.md` - Consolidate into main README
     - `EVALUATION_STATUS.md` - Outdated status
     - `IMPLEMENTATION_STATUS.md` - Outdated status
   - **Recommendation**: Consolidate key info into README.md, delete duplicates

6. **Status/verification docs** (~70 KB)
   - **Files**:
     - `THREE_STAGE_CURATOR_VERIFICATION.md`
     - `INTERACTIVE_PROTOCOL_SUCCESS.md`
     - `APPWORLD_EXECUTOR_INTEGRATION.md`
     - `APPWORLD_EXECUTION_READY.md`
     - `ACE_STATUS_REPORT.md`
     - `ACE_SUCCESS_REPORT.md`
   - **Recommendation**: Move to `benchmarks/docs/archive/` or delete
   - **Keep**: BUGFIX_COMPLETE.md, MISSION_ACCOMPLISHED.md (important history)

### 🔍 LOW PRIORITY: REVIEW

7. **Utility duplicates**
   - `benchmarks/utils/curator.py` vs `curator_staged.py` - Keep staged version?
   - `benchmarks/utils/embeddings.py` vs `embeddings_faiss.py` - Keep FAISS version?
   - **Recommendation**: Check usage, remove unused version

8. **Unknown/unanalyzed**
   - `src/` folder (88 KB) - Need to analyze contents
   - `ablation/` folder (12 KB) - Research artifacts, keep or archive?
   - `benchmarks/finer/` - Package import or custom code?

9. **.gitignore improvements**
   - Add `__pycache__/` directories
   - Add `.claude/hooks/logs/`
   - Add `benchmarks/results/` (track results elsewhere)
   - Add `benchmarks/experiments/` if recreated

---

## Proposed .gitignore Additions

```gitignore
# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Claude Code plugin logs
.claude/hooks/logs/

# Benchmark outputs (track results separately)
benchmarks/experiments/
benchmarks/results/
benchmarks/**/*.log

# Temporary files
*.tmp
*.bak
*~
.DS_Store

# Virtual environments
venv/
env/
```

---

## Plugin Structure Best Practices

### ✅ Required Files (Keep)
- `plugin.json` - Plugin manifest
- `README.md` - Main documentation
- `CHANGELOG.md` - Version history
- `.claude/` - Plugin hooks and configuration
- `schemas/` - JSON schemas for validation
- `examples/` - Usage examples
- Core utility files in `benchmarks/utils/`

### ⚠️  Optional Files (Review)
- `ARCHITECTURE.md` - Could consolidate into README
- Implementation guides - Could move to wiki/docs site
- Old verification reports - Archive or delete

### ❌ Should Not Be in Plugin
- Experimental outputs (`benchmarks/experiments/`)
- Debug scripts not needed for plugin operation
- Duplicate documentation
- __pycache__ directories
- Temporary log files

---

## Cleanup Action Plan

### Phase 1: Safe Deletions (Saves ~4.6 MB)
```bash
cd /Users/speed/claude-code-plugin-marketplace/plugins/ace-context-engineering

# Delete experiments folder
rm -rf benchmarks/experiments/

# Delete epoch snapshots
rm skills/playbook_epoch_*.json

# Delete debug scripts
rm benchmarks/skill_monitor*.py
rm benchmarks/*auto_responder*.py

# Delete __pycache__
find . -type d -name __pycache__ -exec rm -rf {} +

# Delete .claude/hooks/logs if present
rm -rf .claude/hooks/logs/*.json
```

### Phase 2: Archive Old Results
```bash
# Create archive folder
mkdir -p archive/old_results

# Move old benchmark results (keep last 10)
ls -t benchmarks/results/*.json | tail -n +11 | xargs -I {} mv {} archive/old_results/
```

### Phase 3: Consolidate Documentation
```bash
# Move status/verification docs to archive
mkdir -p archive/old_docs

mv benchmarks/ENHANCED_REFLECTOR_SUMMARY.md archive/old_docs/
mv benchmarks/REFLECTOR_ENHANCEMENT_README.md archive/old_docs/
mv benchmarks/THREE_STAGE_CURATOR_VERIFICATION.md archive/old_docs/
mv benchmarks/INTERACTIVE_PROTOCOL_SUCCESS.md archive/old_docs/
mv benchmarks/APPWORLD_EXECUTOR_INTEGRATION.md archive/old_docs/
mv benchmarks/APPWORLD_EXECUTION_READY.md archive/old_docs/
mv benchmarks/EVALUATION_STATUS.md archive/old_docs/
mv benchmarks/IMPLEMENTATION_STATUS.md archive/old_docs/
mv SYSTEM_ARCHAEOLOGY.md archive/old_docs/

# Update README.md to consolidate key information from:
# - ACE_PAPER_ALIGNMENT.md
# - ACE_PAPER_COMPARISON.md
# Then move those to archive as well
```

### Phase 4: Update .gitignore
```bash
# Add to .gitignore
cat >> .gitignore << 'EOF'

# Python cache
__pycache__/
*.pyc

# Claude Code plugin logs
.claude/hooks/logs/

# Benchmark outputs
benchmarks/experiments/
benchmarks/results/
*.log

# Archive (local only)
archive/
EOF
```

---

## Expected Impact

### Before Cleanup:
- Total size: ~6.8 MB
- File count: ~2,000+ files
- Documentation: ~30 markdown files with duplicates
- Plugin clarity: Cluttered with development artifacts

### After Cleanup:
- Total size: ~1.2 MB (saves 5.6 MB = 82% reduction)
- File count: ~200 files (removes 1,800 temporary files)
- Documentation: ~10 essential markdown files
- Plugin clarity: Clean, production-ready structure

---

## Files to Definitely Keep

### Core Plugin Files:
- `plugin.json`
- `README.md`
- `CHANGELOG.md`
- `.claude/` (excluding logs)

### Important Documentation:
- `BUGFIX_COMPLETE.md` - Documents critical bug fixes
- `MISSION_ACCOMPLISHED.md` - Final status report
- `ARCHITECTURE.md` - System design

### Core Code:
- `benchmarks/utils/*.py` (after removing duplicates)
- `benchmarks/evaluate_appworld_interactive.py`
- `benchmarks/run_offline_adaptation.py`
- `benchmarks/test_*.py` - All test files
- `schemas/*.json`
- `scripts/*.py`
- `examples/*.py`
- `skills/playbook.json`
- `skills/playbook_appworld_seed.json`
- `skills/ace-skill.md`
- `skills/generate-appworld-code/`

---

## Summary

**Recommended Actions**:
1. ✅ Delete `benchmarks/experiments/` (4.5 MB)
2. ✅ Delete epoch playbook snapshots (19 KB)
3. ✅ Delete debug/monitoring scripts (43 KB)
4. ⚠️  Archive old benchmark results (600 KB)
5. ⚠️  Consolidate duplicate documentation (100 KB)
6. ⚠️  Update .gitignore for future cleanliness
7. 🔍 Review utility duplicates (curator.py, embeddings.py)

**Total Space Savings**: ~5.6 MB (82% reduction)

**Plugin Quality Impact**:
- Cleaner structure
- Easier maintenance
- Faster git operations
- Better user experience
- Production-ready appearance

---

**Date**: 2025-10-27
**Version**: 2.0.1
**Author**: Claude Code
**Purpose**: Code archaeology for ACE Context Engineering plugin cleanup
