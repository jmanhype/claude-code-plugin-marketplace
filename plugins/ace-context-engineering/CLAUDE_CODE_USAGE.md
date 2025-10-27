# ACE Context Engineering - Claude Code Usage Guide

**Plugin Version:** 2.0.0
**Status:** Production-ready with AppWorld integration

---

## Quick Start for Claude Code Users

### What is ACE?

ACE (Agentic Context Engineering) is a plugin that helps Claude Code learn and improve from your coding sessions through:

1. **Bullets** - Reusable patterns and best practices
2. **Retrieval** - Finding relevant guidance for your current task
3. **Reflection** - Learning what worked or didn't work
4. **Curation** - Quality-controlled updates to the playbook
5. **Evolution** - Growing smarter over time

### Installation

The plugin is pre-installed in the marketplace. The playbook is at:
```
plugins/ace-context-engineering/skills/playbook.json
```

---

## Using ACE in Your Claude Code Workflow

### Automatic Integration

ACE works automatically when you:
1. **Complete tasks** - Bullets guide tool usage and best practices
2. **Hit errors** - ACE learns from failures to avoid repeating mistakes
3. **Discover patterns** - New best practices get added to playbook

### Manual Skill Invocation

Reference the skill explicitly when you want Claude Code to:
- Learn from a specific task
- Update guidance based on recent work
- Review and improve existing bullets

**Example prompt:**
```
Using the ace-context-engineering skill, help me implement error retry logic
and capture the pattern for future use
```

---

## Key Features

### 1. Three-Stage Quality-Gated Curator ✨

**What it does:** Ensures only high-quality updates reach your playbook

**Stages:**
1. **Structural Validation** - Checks delta syntax and schema
2. **Quality Assessment** - FAISS semantic deduplication (0.85 threshold)
3. **Final Approval** - Quality score threshold enforcement

**Why it matters:** No duplicate or low-quality bullets pollute your playbook

### 2. FAISS Semantic Deduplication ✨

**What it does:** Uses sentence embeddings to detect semantic duplicates

**Technical details:**
- Model: `all-MiniLM-L6-v2` (384-dimensional embeddings)
- Index: FAISS IndexFlatIP (cosine similarity)
- Threshold: 0.85 (configurable)

**Why it matters:** More accurate than keyword matching, catches paraphrases

### 3. AppWorld Executor Integration ✨ NEW

**What it does:** Enables real task execution with ground-truth metrics

**Capabilities:**
- Execute tasks in AppWorld environment
- Compute TGC (Task Goal Completion) and SGC (Scenario Goal Completion) metrics
- Track which bullets helped vs harmed
- Learn from real execution outcomes

**Status:** Beta (requires AppWorld installation)

### 4. Multi-Epoch Offline Learning

**What it does:** Trains on datasets over multiple epochs

**Features:**
- Iterative improvement across training data
- Grow-and-refine mechanism (periodic deduplication)
- Epoch snapshots for version tracking
- Feedback-based bullet counter updates

---

## Playbook Structure

Your playbook (`skills/playbook.json`) contains:

```json
{
  "metadata": {
    "version": "2.0",
    "total_bullets": 12,
    "active_bullets": 12,
    "last_curated": "2025-10-26T13:08:00Z"
  },
  "bullets": [
    {
      "id": "bullet-2025-10-25-001",
      "title": "Always read files before editing",
      "content": "Use Read tool before Edit to ensure exact matching...",
      "tags": ["tool.read", "tool.edit", "best_practice"],
      "helpful_count": 5,
      "harmful_count": 0,
      "confidence": "high",
      "status": "active"
    }
  ]
}
```

**Key fields:**
- `helpful_count` - Times this bullet helped
- `harmful_count` - Times this bullet was misleading
- `confidence` - high/medium/low
- `tags` - For retrieval filtering

---

## Common Workflows

### 1. Learning from a Successful Task

**When:** You just completed a complex task successfully

**Steps:**
1. Claude Code executes task using retrieved bullets
2. Tracks which bullets were helpful
3. Proposes counter updates (increment `helpful_count`)
4. Three-stage curator validates and merges

**Result:** Successful patterns are reinforced

### 2. Learning from a Failure

**When:** Task failed or produced unexpected results

**Steps:**
1. Reflector analyzes error type
2. Identifies which bullets were harmful or missing
3. Proposes counter updates or new bullets
4. Curator validates before merge

**Result:** Mistakes become learning opportunities

### 3. Discovering New Patterns

**When:** You find a better way to do something

**Steps:**
1. Reflector proposes new bullet with evidence
2. Curator checks for duplicates (FAISS)
3. If unique and high-quality, adds to playbook
4. Available for future tasks

**Result:** Playbook grows with your experience

---

## Running Benchmarks (Advanced)

### Offline Adaptation Demo

Run multi-epoch learning on training data:

```bash
cd plugins/ace-context-engineering/benchmarks
MAX_SAMPLES=5 MAX_EPOCHS=2 python run_offline_adaptation.py
```

**Output:**
- Quality gate statistics (Stage 1/2/3 pass rates)
- Bullet update counts
- Epoch snapshots
- Results JSON

### AppWorld Executor Demo (Requires AppWorld)

Test real task execution with TGC/SGC metrics:

```bash
cd benchmarks
APPWORLD_ROOT=/tmp/appworld \
  /tmp/appworld/venv_appworld/bin/python \
  run_ace_with_appworld.py
```

**Requirements:**
- AppWorld installed at `/tmp/appworld`
- Python 3.11+
- AppWorld dataset downloaded

---

## Configuration

### Playbook Location

Default: `plugins/ace-context-engineering/skills/playbook.json`

To use a custom playbook:
```python
from utils.claude_code_method import ClaudeCodeACE

ace = ClaudeCodeACE(
    playbook_path="path/to/custom_playbook.json",
    use_faiss=True  # Enable FAISS deduplication
)
```

### FAISS Settings

Adjust similarity threshold in `utils/curator_staged.py`:

```python
duplicates = self.deduplicator.find_duplicates(
    bullets,
    threshold=0.85  # Lower = stricter, Higher = more lenient
)
```

### Executor Selection

Use mock executor (default):
```python
ace = ClaudeCodeACE(playbook_path="...")
```

Use AppWorld executor:
```python
from utils.appworld_executor import AppWorldExecutor

executor = AppWorldExecutor(experiment_name="my_experiment")
ace = ClaudeCodeACE(playbook_path="...", executor=executor)
```

---

## Quality Gates Explained

### Stage 1: Structural Validation

**Checks:**
- Delta has required fields (`reasoning`, `task_context`)
- Bullet IDs in counters exist in playbook
- No malformed operations
- Schema compliance

**Pass criteria:** All structural checks pass

### Stage 2: Quality Assessment

**Checks:**
- FAISS duplicate detection (< 0.85 similarity)
- Generalizability (not overly specific)
- Counter validity
- Tag normalization

**Pass criteria:**
- No duplicates found OR duplicate handling strategy applied
- Quality score ≥ 0.6

### Stage 3: Final Approval

**Checks:**
- Quality threshold met
- No human review flags
- Ready for merge

**Pass criteria:**
- Quality score ≥ 0.6
- No blocking issues

**100% pass rate in testing!**

---

## Troubleshooting

### "FAISS not available" Warning

**Solution:** Install FAISS dependencies:
```bash
pip install numpy sentence-transformers faiss-cpu scikit-learn
```

Fallback: TF-IDF will be used automatically (less accurate)

### AppWorld Executor Not Working

**Check:**
1. AppWorld installed: `which appworld`
2. Environment variable: `APPWORLD_ROOT=/tmp/appworld`
3. Python version: `python --version` (need 3.11+)
4. Data downloaded: `ls /tmp/appworld/data/tasks`

### No Bullets Retrieved

**Check:**
1. Playbook has bullets: `jq '.bullets | length' skills/playbook.json`
2. Bullets have relevant tags
3. Retrieval query matches bullet content

**Debug:**
```python
from utils.bullet_retriever import BulletRetriever

retriever = BulletRetriever("skills/playbook.json")
results = retriever.retrieve(query="your task description", top_k=10)
print(f"Retrieved {len(results)} bullets")
```

---

## Performance Metrics

### Curator Quality Gate Statistics

From offline adaptation demo (5 samples × 2 epochs):

| Stage | Passed | Failed | Pass Rate |
|-------|--------|--------|-----------|
| Stage 1: Structural | 10/10 | 0/10 | 100% |
| Stage 2: Quality | 10/10 | 0/10 | 100% |
| Stage 3: Approval | 10/10 | 0/10 | 100% |
| **Final Merge** | **10/10** | **0/10** | **100%** |

### Expected Performance Lift

Based on ACE paper (arXiv:2510.04618v1):
- **+10.6% improvement** on agent tasks (AppWorld benchmark)
- **Grow-and-refine** mechanism prevents playbook bloat
- **Multi-epoch learning** shows continuous improvement

---

## Best Practices

### 1. Tag Consistently

Use hierarchical tags:
- `tool.bash`, `tool.edit`, `tool.read`
- `git.push`, `git.commit`
- `error_handling`, `validation`

### 2. Provide Evidence

High-quality bullets include:
```json
{
  "evidence": [
    {
      "type": "execution",
      "ref": "task-2025-10-25-042",
      "note": "Prevented malformed JSON from being committed"
    }
  ]
}
```

### 3. Review Periodically

Check playbook health:
```bash
# Bullets with low success rate
jq '.bullets[] | select((.harmful_count > .helpful_count)) | {id, title, helpful_count, harmful_count}' \
  skills/playbook.json

# Most helpful bullets
jq '.bullets[] | {id, title, helpful_count} | select(.helpful_count > 3)' \
  skills/playbook.json
```

### 4. Leverage Multi-Epoch Learning

For large projects:
1. Collect training examples (successful + failed tasks)
2. Run offline adaptation (multiple epochs)
3. Use learned playbook for production work
4. Continue online learning during usage

---

## Integration with Claude Code Features

### TodoWrite Integration

Include ACE reflection in your todo list:

```
[pending] Implement feature X
[pending] Run tests
[pending] Reflect and update ACE playbook
```

### Git Workflow

ACE can learn git best practices:
- Pre-commit validation
- Push retry logic
- Commit message patterns
- Branch naming conventions

### Tool Usage Patterns

ACE captures tool-specific best practices:
- Read before Edit (prevents mismatches)
- Parallel tool calls (performance)
- Error handling strategies

---

## Advanced: Custom Executors

Create your own executor for domain-specific evaluation:

```python
class MyCustomExecutor:
    def solve_task(self, instruction, apps, apis, playbook_bullets,
                   ground_truth=None, task_id=None):
        """
        Your custom task execution logic.

        Must return:
        {
            'code': generated_code,
            'final_answer': result,
            'used_bullet_ids': [...],
            'bullet_feedback': {'bullet-id': 'helpful'|'harmful'},
            'success': bool
        }
        """
        # Your implementation here
        pass

# Use with ACE
ace = ClaudeCodeACE(playbook_path="...", executor=MyCustomExecutor())
```

---

## References

- **ACE Paper**: arXiv:2510.04618v1 (License: CC BY 4.0)
- **ace-playbook**: https://github.com/jmanhype/ace-playbook
- **AppWorld**: https://github.com/stonybrooknlp/appworld
- **Plugin Documentation**: `README.md`
- **Implementation Status**: `benchmarks/IMPLEMENTATION_STATUS.md`

---

## Support

**Issues:** [GitHub Issues](https://github.com/jmanhype/claude-code-plugin-marketplace/issues)
**Documentation:** [Plugin README](./README.md)
**Examples:** `examples/` directory

---

**Last Updated:** 2025-10-26
**Plugin Version:** 2.0.0
**Status:** Production-ready (AppWorld executor in beta)
