# ACE Skill Integration Analysis

**Date**: 2025-10-27
**Investigation**: Verify Generator uses Claude Code OS skills
**Result**: ❌ **BOTH Generator AND Reflector bypass the skill system**

## Executive Summary

The ACE system has **NO LLM-powered components**. Both the Generator and Reflector use hardcoded templates and heuristics instead of Claude Code OS skills. This explains the 0% → 0% learning results.

## Critical Findings

### 1. Generator Does NOT Use Skills

**Current Implementation** (`ace_code_generator.py:121`):
```python
# ❌ WRONG: Bypasses skill system entirely
code = skill_invoker.generate_appworld_code(
    instruction=instruction,
    apps=apps,
    strategies=strategies
)
```

**What This Actually Does**:
- Calls `generate_appworld_code()` Python function directly (claude_code_skill_invoker.py:78)
- Uses hardcoded if/else templates for Spotify/Gmail/Venmo (lines 108-335)
- **Never invokes the actual `generate-appworld-code` skill**
- Ignores bullet guidance from Reflector

**Evidence**:
- Added debug logging to `invoke_skill()` - message never appeared
- Test run completed without skill invocation warning
- Code path: ACECodeGenerator → generate_appworld_code() → hardcoded templates

### 2. Reflector Does NOT Use LLM

**Current Implementation** (`reflector.py:374-396`):
```python
# ❌ Rule-based pattern matching
elif error_type == 'logic_error':
    title = f"Verify {app_name or 'app'} API logic and requirements"
    content = f"When implementing {app_name or 'app'} operations: "
    content += '; '.join(missing_patterns)  # String concatenation
```

**What This Actually Does**:
- Uses string templates and pattern concatenation
- No LLM imports (no anthropic, claude, openai, or gpt references)
- Generates generic bullets like "Verify venmo API logic and requirements"

**Code Archaeology Results**:
- ✅ `skills/generate-appworld-code/SKILL.md` EXISTS (233 lines)
- ❌ `skills/reflect-appworld-failure/SKILL.md` MISSING
- ❌ `skills/curate-bullet-proposal/SKILL.md` MISSING

## Impact on Learning

### Broken Learning Loop

```
┌─────────────────────────────────────────────────────────┐
│                    ACE Learning Loop                     │
└─────────────────────────────────────────────────────────┘

Failure → Reflector → Curator → Playbook → Generator → Code
            ↑ BROKEN              ↑           ↓ BROKEN
         (heuristics)         (5→7 bullets)  (hardcoded)
                                              templates
```

**Result**:
- Reflector generates 2 generic bullets using pattern matching
- Bullets added to playbook (5 → 7 bullets)
- **Generator ignores bullets** and uses hardcoded templates
- No performance improvement (0% → 0%)

### Why 0% → 0%

1. **Reflector produces generic guidance**:
   - Before: "Verify general API logic and requirements"
   - Should be: "General tasks require supervisor.complete_task() call. Example: `apis.supervisor.complete_task()`"

2. **Generator ignores bullet guidance**:
   - Uses hardcoded templates from claude_code_skill_invoker.py
   - Bullets are retrieved but never applied
   - Same code generated regardless of learned patterns

3. **No semantic understanding**:
   - No LLM analyzes failure patterns
   - No LLM generates code from bullet guidance
   - System is entirely rule-based

## Architecture Gap

### Current State (Broken)

| Component  | Expected            | Actual              | Status |
|------------|---------------------|---------------------|--------|
| Generator  | Claude Code OS Skill| Hardcoded templates | ❌     |
| Reflector  | LLM semantic analysis| Pattern matching   | ❌     |
| Curator    | LLM quality scoring | Heuristics         | ❌     |

### Required State (ACE Paper)

| Component  | Implementation      | Files Needed       |
|------------|---------------------|--------------------|
| Generator  | invoke_skill("generate-appworld-code") | ✅ EXISTS |
| Reflector  | invoke_skill("reflect-appworld-failure") | ❌ MISSING |
| Curator    | invoke_skill("curate-bullet-proposal") | ❌ MISSING |

## Fix Plan

### Phase 1: Fix Generator (Highest Priority)

**File**: `benchmarks/utils/ace_code_generator.py`

**Change Line 121**:
```python
# Before (WRONG)
code = skill_invoker.generate_appworld_code(
    instruction=instruction,
    apps=apps,
    strategies=strategies
)

# After (CORRECT)
prompt = self._build_skill_prompt(instruction, apps, relevant_bullets)
code = skill_invoker.invoke_skill(
    skill_name="generate-appworld-code",
    prompt=prompt
)
```

**Add Helper Method**:
```python
def _build_skill_prompt(
    self,
    instruction: str,
    apps: List[str],
    bullets: List
) -> str:
    """Build prompt for generate-appworld-code skill."""
    strategies = [f"- {b.title}: {b.content}" for b in bullets]

    return f"""# Task
{instruction}

## Available Apps
{', '.join(apps)}

## Strategies from Playbook
{chr(10).join(strategies) if strategies else "No strategies available"}

Generate Python code to solve this task using the AppWorld API.
"""
```

**Expected Impact**:
- Generator will use actual Claude Code OS skill
- Bullet guidance will be applied semantically
- Code quality should improve immediately

### Phase 2: Create Reflector Skill (Critical)

**Create**: `skills/reflect-appworld-failure/SKILL.md`

**Frontmatter**:
```markdown
---
name: reflect-appworld-failure
description: Analyze AppWorld task failures to extract specific API patterns and generate actionable bullets
allowed-tools: Read
---
```

**Input Format** (JSON):
```json
{
  "task_instruction": "What is the title of the most-liked song in my Spotify playlists",
  "apps": ["spotify"],
  "error_type": "api_misuse",
  "error_messages": ["AttributeError: 'Spotify' object has no attribute 'get_tracks'"],
  "failed_code": "songs = spotify.get_tracks(playlist_id=pid)",
  "missing_patterns": ["Use search_* methods for Spotify, not get_*"],
  "suggested_fixes": ["Use show_playlist_songs() instead"]
}
```

**Output Format** (JSON):
```json
{
  "bullet": {
    "id": "bullet-2025-10-27-...",
    "title": "Spotify: Use show_playlist_songs() not get_tracks()",
    "content": "Spotify API uses show_playlist_songs(access_token, playlist_id) to retrieve tracks. The method get_tracks() does not exist. Example: songs = apis.spotify.show_playlist_songs(access_token=token, playlist_id=playlist['id'])",
    "tags": ["app.spotify", "api_misuse", "method_names", "playlists"],
    "evidence": [...],
    "confidence": "high",
    "scope": "app"
  }
}
```

**Modify**: `benchmarks/utils/reflector.py`

**Replace `_generate_appworld_bullet()` (line 374)**:
```python
def _generate_appworld_bullet(
    self,
    sample: Dict,
    error_analysis: Dict
) -> Optional[Dict]:
    """Generate AppWorld-specific bullet using Claude Code OS skill."""
    from claude_code_skill_invoker import invoke_skill
    import json

    # Build input for skill
    skill_input = {
        "task_instruction": sample.get('instruction', ''),
        "apps": sample.get('apps', []),
        "error_type": error_analysis.get('error_type'),
        "error_messages": error_analysis.get('error_messages', []),
        "failed_code": error_analysis.get('failed_code', ''),
        "missing_patterns": error_analysis.get('missing_patterns', []),
        "suggested_fixes": error_analysis.get('suggested_fixes', [])
    }

    # Invoke skill (uses Claude Code OS for semantic analysis)
    try:
        response = invoke_skill("reflect-appworld-failure", json.dumps(skill_input))
        bullet_data = json.loads(response)
        return bullet_data['bullet']
    except Exception as e:
        print(f"Skill invocation failed: {e}")
        return self._generate_appworld_bullet_fallback(sample, error_analysis)
```

**Expected Impact**:
- Reflector generates specific bullets with concrete examples
- Bullets include working code snippets
- Quality increases: "Verify venmo logic" → "Venmo: Call login() before search_transactions(). Example: token = venmo.login()['access_token']; results = venmo.search_transactions(token, query)"

### Phase 3: Update Skill Invoker (Infrastructure)

**File**: `benchmarks/utils/claude_code_skill_invoker.py`

**Modify `invoke_skill()` (line 29)**:
```python
def invoke_skill(skill_name: str, prompt: str) -> str:
    """
    Invoke a Claude Code Skill and return the response.

    Args:
        skill_name: Name of the skill (e.g., "generate-appworld-code")
        prompt: Input prompt for the skill

    Returns:
        Skill response as string

    Raises:
        RuntimeError: If skill invocation fails
    """
    print(f"\n{'='*80}")
    print(f"🎯 SKILL INVOCATION")
    print(f"{'='*80}")
    print(f"Skill: {skill_name}")
    print(f"Prompt length: {len(prompt)} chars")
    print(f"{'='*80}\n")

    if skill_name == "generate-appworld-code":
        return invoke_generate_appworld_code_skill(prompt)
    elif skill_name == "reflect-appworld-failure":
        return invoke_reflect_appworld_failure_skill(prompt)
    else:
        raise ValueError(f"Unknown skill: {skill_name}")
```

**Add New Function**:
```python
def invoke_reflect_appworld_failure_skill(prompt: str) -> str:
    """
    Analyze AppWorld failures using the reflect-appworld-failure skill.

    This skill uses Claude to semantically analyze error patterns
    and generate specific, actionable bullets.

    Args:
        prompt: JSON string with error analysis

    Returns:
        JSON string with bullet proposal
    """
    # TODO: Actual Claude Code OS skill invocation
    # For now, use fallback implementation

    import json

    # Parse input
    input_data = json.loads(prompt)

    # Call Claude/LLM to analyze error and generate bullet
    # (This would be the actual skill invocation in production)

    # Fallback: Return template
    return json.dumps({
        "bullet": {
            "id": f"bullet-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}",
            "title": "Fallback bullet",
            "content": "Skill invocation not yet implemented",
            "tags": ["fallback"],
            "evidence": [],
            "confidence": "low",
            "scope": "app"
        }
    })
```

## Expected Results After Fixes

### Immediate (Phase 1 Only - Fix Generator)

- Generator uses Claude Code OS skill
- Bullet guidance applied semantically
- Baseline performance may improve 5-10%
- Reflector still generates generic bullets

### Complete (All Phases)

- **Epoch 1**: 0% baseline → 0% (still learning)
- **Epoch 2**: 0% → 15-25% (learned patterns applied)
- Bullets are specific with code examples
- Generator applies bullet guidance correctly
- True ACE learning loop functional

### Bullet Quality Comparison

**Before (Heuristics)**:
```json
{
  "title": "Verify venmo API logic and requirements",
  "content": "When implementing venmo operations: Check task logic and requirements; Missing login() call for venmo"
}
```

**After (LLM)**:
```json
{
  "title": "Venmo: Call login() before search_transactions()",
  "content": "Venmo API requires authentication token for all operations. Always call venmo.login() first to get access_token, then pass it to other methods. Example: response = apis.venmo.login(username='user', password='pass'); token = response['access_token']; results = apis.venmo.search_transactions(access_token=token, query={'friend': 'Alice'})",
  "tags": ["app.venmo", "authentication", "search", "api_order"]
}
```

## Implementation Priority

1. **Phase 1** (Highest): Fix Generator skill invocation (1 hour)
   - Immediate impact: Bullets can be applied
   - Low risk: Fallback still works

2. **Phase 2** (Critical): Create Reflector skill (2-3 hours)
   - High impact: Quality bullets discovered
   - Medium risk: Need skill prompt engineering

3. **Phase 3** (Infrastructure): Skill invoker updates (30 min)
   - Enables both skills to work
   - Low risk: Pure infrastructure

## Testing Plan

### After Phase 1
```bash
MAX_SAMPLES=5 MAX_EPOCHS=2 python run_offline_adaptation.py
```
- Verify skill invocation debug messages appear
- Check that bullets are passed to skill
- Baseline: 0% → 0-5%

### After Phase 2
```bash
MAX_SAMPLES=10 MAX_EPOCHS=2 python run_offline_adaptation.py
```
- Verify specific bullets generated
- Check bullet quality (has code examples)
- Target: 0% → 15-25%

### After Phase 3
```bash
MAX_SAMPLES=20 MAX_EPOCHS=4 python run_offline_adaptation.py
```
- Full learning demonstration
- Target: 0% → 20-30% by Epoch 4

## Conclusion

The current ACE system is **entirely rule-based** with no LLM-powered components. Both Generator and Reflector use hardcoded templates and heuristics, explaining the 0% → 0% learning results.

**Root Cause**: Architecture gap between code and ACE paper design.

**Solution**: Implement proper skill invocation at both ends of the learning loop.

**Priority**: Fix Generator first (Phase 1) to unblock bullet application, then create Reflector skill (Phase 2) to improve bullet quality.
