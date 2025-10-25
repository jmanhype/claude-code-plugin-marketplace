# User Ratings Interface

## Purpose

Provide lightweight human feedback on bullet effectiveness through simple JSONL format.

---

## Format

Each line in `ratings.jsonl` is a JSON object:

```json
{"type":"user_rating","bullet_id":"yt-thumb-contrast-001","value":1,"note":"Clear CTR uplift"}
{"type":"exec_failure","bullet_id":"yt-prompt-nanoban-002","value":-1,"note":"Produced cluttered text"}
```

---

## Schema

```json
{
  "type": "user_rating | exec_success | exec_failure | validation_pass | validation_fail",
  "bullet_id": "bullet-YYYY-MM-DD-NNN",
  "value": 1 | 0 | -1,
  "note": "Optional explanation",
  "timestamp": "2025-10-25T12:00:00Z"  // optional
}
```

**Values:**
- `1` = Helpful (increment `helpful_count`)
- `0` = Neutral (no change)
- `-1` = Harmful (increment `harmful_count`)

---

## Usage

### 1. Add Ratings

Append to `ratings.jsonl`:

```bash
echo '{"type":"user_rating","bullet_id":"yt-thumb-contrast-001","value":1,"note":"Worked great!"}' \
  >> .claude/context/memory/ratings.jsonl
```

Or use your favorite editor to append lines.

### 2. Validate (Optional)

```bash
# Validate each line individually
while IFS= read -r line; do
  echo "$line" | python scripts/validate_delta.py feedback /dev/stdin
done < ratings.jsonl
```

### 3. Apply to Counters

```bash
python scripts/update_counters.py \
  bullets.json \
  generator_output.json \
  --ratings ratings.jsonl \
  --out bullets_updated.json
```

---

## Examples

### Positive Feedback

```json
{"type":"user_rating","bullet_id":"fin-cohort-define-001","value":1,"note":"Model validated perfectly"}
```

### Negative Feedback

```json
{"type":"exec_failure","bullet_id":"react-safety-001","value":-1,"note":"Checkpoint was too verbose"}
```

### Execution Success

```json
{"type":"exec_success","bullet_id":"yt-thumb-contrast-001","value":1,"note":"Thumbnail got 12% CTR"}
```

---

## Best Practices

1. **Be specific** - Include concrete outcomes in `note` field
2. **Rate what you use** - Only rate bullets you actually applied
3. **Update regularly** - Append ratings after each task
4. **Batch apply** - Accumulate ratings, then run `update_counters.py` periodically

---

## Integration with ACE Cycle

```
Task Execution
     ↓
Generator uses bullets
     ↓
Observe outcome
     ↓
Append rating to ratings.jsonl
     ↓
Run update_counters.py
     ↓
Updated bullets.json with new counters
```

---

## Automation (Optional)

Create a post-task hook:

```bash
# .claude/hooks/post-task.sh
#!/bin/bash
# Auto-append rating if generator output exists

if [[ -f gen_output.json ]]; then
  python scripts/update_counters.py \
    bullets.json \
    gen_output.json \
    --ratings ratings.jsonl \
    --out bullets.json
fi
```

---

**Last Updated**: 2025-10-25
