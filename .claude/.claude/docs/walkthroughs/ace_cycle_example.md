# ACE Cycle Walkthrough - YouTube Thumbnail Generation

This document shows a complete ACE cycle with real JSON examples.

---

## Task

**User Request:** "Create a thumbnail for my video 'Only Claude Skills You'll Ever Need'"

---

## Phase 1: Retrieval

**Query:** "create YouTube thumbnail"
**Tags:** `yt.thumbnail`, `design`

```bash
python scripts/retrieve_bullets.py bullets.json "create YouTube thumbnail" --tags yt.thumbnail --topk 3
```

**Retrieved Bullets:**

```json
[
  {
    "id": "yt-thumb-contrast-001",
    "title": "Thumbnails: Max contrast, 3-5 words, 2-3 visual elements",
    "score": 4.8523,
    "tags": ["yt.thumbnail", "design", "visual.hierarchy"],
    "confidence": 0.8
  },
  {
    "id": "yt-prompt-nanoban-002",
    "title": "Prompting image generator for thumbnails (template)",
    "score": 3.2156,
    "tags": ["yt.thumbnail", "prompting", "image.gen"],
    "confidence": 0.6
  }
]
```

---

## Phase 2: Generator

**Input:**

```json
{
  "mode": "generator",
  "task_input": "Create YouTube thumbnail for 'Only Claude Skills You'll Ever Need'",
  "context_bullets": ["yt-thumb-contrast-001", "yt-prompt-nanoban-002"],
  "tools": ["image_gen", "edit"],
  "constraints": {"max_tokens": 2000}
}
```

**Generator Output:**

```json
{
  "final_answer": "Created two thumbnail concepts:\n1. High-contrast comp: Purple gradient bg, subject left, 'ONLY SKILLS YOU NEED' right in bold white\n2. Alternative: Blue/orange split, emoji accents\nExported 1280×720 PNG files.",
  "answer_confidence": 0.72,
  "used_bullet_ids": ["yt-thumb-contrast-001", "yt-prompt-nanoban-002"],
  "bullet_confidence": {
    "yt-thumb-contrast-001": 0.9,
    "yt-prompt-nanoban-002": 0.5
  },
  "observations": [
    {
      "type": "validation",
      "detail": "Followed 3-5 word rule, 2 visual elements (subject + text)"
    },
    {
      "type": "exec_error",
      "detail": "First prompt produced low contrast; re-prompted with stronger negatives"
    },
    {
      "type": "exec_success",
      "detail": "Second iteration achieved target contrast ratio"
    }
  ],
  "brief_rationale": "Applied yt-thumb-contrast-001 for layout (3-5 words, high contrast). Used yt-prompt-nanoban-002 template but needed to strengthen negative prompts for contrast. Final output meets 16:9 spec."
}
```

---

## Phase 3: Reflector

**Input:**
- Generator output (above)
- Optional: Ground truth (user feedback "Thumbnail got 14% CTR, above our 10% target")

**Reflector Output:**

```json
{
  "proposed_deltas": {
    "new_bullets": [
      {
        "id": "yt-negatives-strong-001",
        "title": "YouTube thumbnails need aggressive negative prompts for contrast",
        "content": "Default negative prompts ('low contrast', 'busy') are insufficient. Use stronger negatives: 'washed out', 'low saturation', 'muddy colors', 'unclear subject'. This prevents flat, low-contrast renders that reduce CTR.",
        "tags": ["yt.thumbnail", "prompting", "image.gen", "contrast"],
        "evidence": [
          {
            "type": "exec_success",
            "ref": "thumbnail-2025-10-25-001",
            "note": "First render was flat; stronger negatives fixed it"
          }
        ],
        "helpful_count": 0,
        "harmful_count": 0,
        "confidence": 0.7,
        "scope": {
          "domain": "youtube",
          "inputs": ["prompt", "style"],
          "outputs": ["image"]
        },
        "prerequisites": ["yt-thumb-contrast-001"],
        "last_updated": "2025-10-25T14:30:00Z",
        "links": ["yt-prompt-nanoban-002"]
      }
    ],
    "edits": [],
    "merges": [],
    "deprecations": [],
    "counters": [
      {
        "id": "yt-thumb-contrast-001",
        "helpful_delta": 2,
        "harmful_delta": 0,
        "reason": "Guided layout successfully; high confidence application"
      },
      {
        "id": "yt-prompt-nanoban-002",
        "helpful_delta": 1,
        "harmful_delta": 0,
        "reason": "Template worked but needed refinement"
      }
    ]
  },
  "justification": "Generator successfully applied yt-thumb-contrast-001 (3-5 words, high contrast) but discovered that yt-prompt-nanoban-002's negative prompts were too weak. Proposing new bullet to capture the stronger negative prompt pattern. Both bullets marked helpful; yt-thumb-contrast-001 highly confident (0.9).",
  "needs_followup": false
}
```

---

## Phase 4: Curator

**Input:** Reflector's proposed_deltas

**Curator Output:**

```json
{
  "clean_delta": {
    "new_bullets": [
      {
        "id": "yt-negatives-strong-001",
        "title": "YouTube thumbnails need aggressive negative prompts for contrast",
        "content": "Default negative prompts ('low contrast', 'busy') are insufficient. Use stronger negatives: 'washed out', 'low saturation', 'muddy colors', 'unclear subject'. This prevents flat, low-contrast renders that reduce CTR.",
        "tags": ["yt.thumbnail", "prompting", "image.gen", "contrast"],
        "evidence": [
          {
            "type": "exec_success",
            "ref": "thumbnail-2025-10-25-001",
            "note": "First render was flat; stronger negatives fixed it"
          }
        ],
        "helpful_count": 0,
        "harmful_count": 0,
        "confidence": 0.7,
        "scope": {
          "domain": "youtube",
          "inputs": ["prompt", "style"],
          "outputs": ["image"]
        },
        "prerequisites": ["yt-thumb-contrast-001"],
        "last_updated": "2025-10-25T14:30:00Z",
        "links": ["yt-prompt-nanoban-002"]
      }
    ],
    "edits": [],
    "merges": [],
    "deprecations": [],
    "counters": [
      {
        "id": "yt-thumb-contrast-001",
        "helpful_delta": 2,
        "harmful_delta": 0,
        "reason": "Guided layout successfully"
      },
      {
        "id": "yt-prompt-nanoban-002",
        "helpful_delta": 1,
        "harmful_delta": 0,
        "reason": "Template worked but needed refinement"
      }
    ]
  },
  "curation_notes": "No deduplication needed. New bullet (yt-negatives-strong-001) is distinct from existing prompting bullets; adds specific negative prompt guidance. No conflicts detected. Counter updates are conservative and evidence-based."
}
```

---

## Phase 5: Validation & Merge

### Validate Delta

```bash
python scripts/validate_delta.py delta clean_delta.json
```

**Output:**
```
✅ Valid delta: clean_delta.json
```

### Merge Delta

```bash
python scripts/merge_deltas.py bullets.json clean_delta.json bullets_updated.json
```

**Output:**
```
📝 Merging delta into 5 bullets...
  ✅ Added 1 new bullets
  ✅ Applied 0 edits
  ✅ Merged 0 bullet groups
  ✅ Deprecated 0 bullets
  ✅ Updated 2 counters
✅ Merged → bullets_updated.json (6 total bullets)
```

---

## Phase 6: Update Counters from Generator

```bash
python scripts/update_counters.py bullets_updated.json gen_output.json --out bullets_final.json
```

**Output:**
```
📝 Updating counters for 6 bullets...
  ✅ Updated 2 bullets from generator output
✅ Counters updated → bullets_final.json
```

---

## Phase 7: User Feedback (Optional)

User adds rating to `ratings.jsonl`:

```json
{"type":"user_rating","bullet_id":"yt-thumb-contrast-001","value":1,"note":"Thumbnail got 14% CTR, above 10% target"}
```

Apply ratings:

```bash
python scripts/update_counters.py bullets_final.json gen_output.json --ratings ratings.jsonl --out bullets.json
```

**Output:**
```
📝 Updating counters for 6 bullets...
  ✅ Updated 2 bullets from generator output
  ✅ Applied 1 ratings from ratings.jsonl
✅ Counters updated → bullets.json
```

---

## Final Bullet State

**yt-thumb-contrast-001:**
- `helpful_count`: 5 → 8 (was 5, +2 from reflector, +1 from user rating)
- `harmful_count`: 0
- `confidence`: 0.8

**yt-prompt-nanoban-002:**
- `helpful_count`: 3 → 4 (+1 from reflector)
- `harmful_count`: 1
- `confidence`: 0.6

**yt-negatives-strong-001 (NEW):**
- `helpful_count`: 0
- `harmful_count`: 0
- `confidence`: 0.7
- Status: Ready for next retrieval

---

## Summary

**Complete ACE cycle demonstrated:**

1. ✅ Retrieved 2 relevant bullets
2. ✅ Generator applied bullets and produced solution
3. ✅ Reflector proposed 1 new bullet + 2 counter updates
4. ✅ Curator validated and cleaned delta
5. ✅ Validated delta against schema
6. ✅ Merged delta (6 total bullets now)
7. ✅ Updated counters from generator output
8. ✅ Applied user rating
9. ✅ Bullet library evolved (5 → 6 bullets)

**Next task** will retrieve yt-negatives-strong-001 alongside existing bullets, benefiting from this learned pattern.

---

**Demonstration complete.** See `bullets.json` for final state.
