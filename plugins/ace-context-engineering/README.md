# ACE Context Engineering Plugin

**Agentic Context Engineering** - Evolve your context through bullets, deltas, and intelligent retrieval.

## Overview

The ACE (Agentic Context Engineering) plugin provides a production-ready system for managing and evolving context in Claude Code. Instead of rewriting entire context files, ACE uses:

- **Bullets** - Atomic, tagged pieces of guidance grounded in evidence
- **Deltas** - Incremental updates (add, edit, merge, deprecate)
- **Retrieval** - TF-IDF + tag-based scoring to find relevant guidance
- **Feedback** - Track what works (helpful_count) and what doesn't (harmful_count)

Based on research: *"Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models"* - Q. Zhang et al., 2025, arXiv:2510.04618, **CC BY 4.0**.

---

## Features

### 🎯 Core Capabilities

- **Smart Retrieval** - TF-IDF cosine similarity + tag overlap + helpfulness scoring
- **Schema Validation** - Complete JSON schemas for bullets, deltas, and outputs
- **Production Scripts** - 5 Python scripts for retrieval, merging, validation, and conflict detection
- **Feedback Integration** - JSONL-based user ratings and automatic counter updates
- **Conflict Detection** - Heuristic detection of contradictory guidance
- **Complete Workflow** - Generator → Reflector → Curator → Merge cycle

### 📦 What's Included

```
ace-context-engineering/
├── skills/
│   ├── ace-skill.md              # ACE skill definition (Generator/Reflector/Curator modes)
│   ├── schemas/
│   │   ├── bullet.schema.json    # Bullet validation schema
│   │   ├── delta.schema.json     # Delta operations schema
│   │   ├── generator_output.schema.json
│   │   ├── reflector_output.schema.json
│   │   ├── curator_output.schema.json
│   │   └── feedback_event.schema.json
│   └── playbook.json             # Seed bullet library (5 bullets)
├── scripts/
│   ├── retrieve_bullets.py       # TF-IDF + tag-based retrieval
│   ├── validate_delta.py         # Multi-schema validation
│   ├── merge_deltas.py           # Deterministic delta merge
│   ├── update_counters.py        # Feedback integration
│   └── detect_conflicts.py       # Contradiction detection
└── docs/
    ├── quickstart.md             # Get started in 5 minutes
    ├── walkthrough.md            # Complete end-to-end example
    └── api.md                    # Script API reference
```

---

## Quick Start

### 1. Install the Plugin

```bash
/plugin marketplace add jmanhype/claude-code-plugin-marketplace
/plugin install ace-context-engineering
```

### 2. Retrieve Bullets

```bash
python scripts/retrieve_bullets.py playbook.json "create YouTube thumbnail" --tags yt.thumbnail --topk 5
```

**Output:**
```json
[
  {
    "id": "yt-thumb-contrast-001",
    "title": "Thumbnails: Max contrast, 3-5 words, 2-3 visual elements",
    "score": 2.18,
    "confidence": 0.8
  }
]
```

### 3. Use in Your Workflow

The retrieved bullets guide your task execution. After completing the task, propose a delta to capture new learnings.

---

## Seed Bullets

The plugin includes 5 production-ready bullets:

| ID | Domain | Description | Confidence |
|----|--------|-------------|-----------|
| `yt-thumb-contrast-001` | YouTube | High-contrast thumbnail design | 0.8 |
| `yt-prompt-nanoban-002` | YouTube | Image generator prompting | 0.6 |
| `fin-cohort-define-001` | Finance | Cohort analysis methodology | 0.9 |
| `fin-ltv-formula-001` | Finance | LTV calculation formula | 0.8 |
| `react-safety-001` | Agents | ReAct safety checkpoints | 0.75 |

---

## Complete ACE Cycle

### Phase 1: Retrieval
Query bullets for your task using tags and TF-IDF scoring.

### Phase 2: Generator
Execute the task using retrieved bullets, producing:
- `final_answer` - The solution
- `used_bullet_ids` - Which bullets were applied
- `observations` - What worked or failed

### Phase 3: Reflector
Analyze generator output and propose deltas:
- New bullets for discovered patterns
- Counter updates (helpful/harmful)
- Edits to improve existing bullets

### Phase 4: Curator
Normalize and deduplicate the proposed delta.

### Phase 5: Merge
Apply the delta to evolve the bullet library.

**Result:** Your context improves with each task.

---

## Scripts Reference

### retrieve_bullets.py

Rank bullets for a query using TF-IDF + tags.

```bash
python scripts/retrieve_bullets.py <bullets.json> <query> [--tags tag1,tag2] [--topk 10]
```

**Scoring Formula:**
```
Score = 2.0 * tag_overlap + cosine(TF-IDF) + 0.1 * log1p(helpful - harmful)
```

### validate_delta.py

Validate JSON against schemas.

```bash
python scripts/validate_delta.py <type> <json_file>
# Types: delta, bullet, gen, reflect, curator, feedback
```

### merge_deltas.py

Apply delta to bullet library.

```bash
python scripts/merge_deltas.py <bullets.json> <delta.json> <output.json>
```

**Operations (in order):**
1. Add new bullets
2. Apply edits
3. Merge bullets (preserving content)
4. Deprecate bullets (tagging + annotation)
5. Update counters

### update_counters.py

Integrate feedback into counters.

```bash
python scripts/update_counters.py <bullets.json> <gen_output.json> [--ratings ratings.jsonl] [--out output.json]
```

### detect_conflicts.py

Find contradictory bullets.

```bash
python scripts/detect_conflicts.py <bullets.json> <conflicts_report.json>
```

Uses polarity analysis (positive vs negative keywords) on bullets with shared tags.

---

## User Feedback

Provide feedback via JSONL format in `ratings.jsonl`:

```json
{"type":"user_rating","bullet_id":"yt-thumb-contrast-001","value":1,"note":"14% CTR!"}
{"type":"exec_failure","bullet_id":"react-safety-001","value":-1,"note":"Too verbose"}
```

**Values:**
- `1` = Helpful (increment helpful_count)
- `-1` = Harmful (increment harmful_count)
- `0` = Neutral

---

## Example Workflow

```bash
# 1. Retrieve bullets
python scripts/retrieve_bullets.py playbook.json "create thumbnail" --tags yt.thumbnail

# 2. (Execute task using retrieved bullets)

# 3. Validate proposed delta
python scripts/validate_delta.py delta my_delta.json

# 4. Merge delta
python scripts/merge_deltas.py playbook.json my_delta.json playbook_updated.json

# 5. Update counters
python scripts/update_counters.py playbook_updated.json gen_output.json --ratings ratings.jsonl

# 6. Check for conflicts
python scripts/detect_conflicts.py playbook_updated.json conflicts.json
```

---

## Bullet Schema

Each bullet includes:

```json
{
  "id": "bullet-YYYY-MM-DD-NNN",
  "title": "Purpose-centric title",
  "content": "Detailed, atomic guidance",
  "tags": ["domain.subdomain", "category"],
  "evidence": [{"type": "execution", "ref": "task-id", "note": "context"}],
  "helpful_count": 0,
  "harmful_count": 0,
  "confidence": 0.5,
  "scope": {
    "domain": "youtube",
    "inputs": ["brief", "assets"],
    "outputs": ["image/png"]
  },
  "prerequisites": [],
  "last_updated": "2025-10-25T12:00:00Z"
}
```

---

## Delta Schema

Incremental updates to the bullet library:

```json
{
  "new_bullets": [...],
  "edits": [{"id": "bullet-id", "set": {"title": "new title"}}],
  "merges": [{"keep_id": "...", "merge_ids": ["..."], "rationale": "..."}],
  "deprecations": [{"id": "...", "reason": "..."}],
  "counters": [{"id": "...", "helpful_delta": 1, "harmful_delta": 0}]
}
```

---

## Advanced Usage

### Custom Retrieval

Extend `retrieve_bullets.py` with semantic embeddings for better recall.

### Domain-Specific Bullets

Create domain packs (e.g., `finance/`, `youtube/`) with specialized bullets.

### Automated Feedback

Integrate with test results or CI/CD to automatically update counters.

---

## Documentation

- **Quick Start** - `docs/quickstart.md` - Get started in 5 minutes
- **Complete Walkthrough** - `docs/walkthrough.md` - End-to-end example with real JSON
- **API Reference** - `docs/api.md` - Detailed script documentation
- **Research Paper** - Zhang et al., 2025, arXiv:2510.04618

---

## Requirements

- Python 3.7+
- `jsonschema` library: `pip install jsonschema`

---

## Contributing

Contributions welcome! Areas for improvement:

- Semantic retrieval (embeddings)
- Web UI for ratings
- A/B testing framework
- Cross-project bullet sharing

---

## License

**CC BY 4.0** - Creative Commons Attribution 4.0 International

Based on research from Zhang et al., 2025, arXiv:2510.04618.

---

## Citation

```bibtex
@article{zhang2025ace,
  title={Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models},
  author={Zhang, Q. and others},
  journal={arXiv preprint arXiv:2510.04618},
  year={2025}
}
```

---

## Support

- **Issues**: https://github.com/jmanhype/claude-code-plugin-marketplace/issues
- **Discussions**: https://github.com/jmanhype/claude-code-plugin-marketplace/discussions
- **Documentation**: https://github.com/jmanhype/claude-code-plugin-marketplace/tree/main/plugins/ace-context-engineering

---

**Made with ❤️ using Claude Code**
