# ACE Interactive Protocol Architecture

## Overview

The ACE (Agentic Context Engineering) system uses an interactive protocol where a Skill Monitor generates code, and the ClaudeCodeReActAgent executes that code in real AppWorld environments.

## Key Components

### 1. Skill Monitor (`skill_monitor_standalone.py`)

**Role**: Code Generation Service ONLY

**What it does**:
- Monitors `/tmp/appworld_requests/` for request files
- Reads task instructions, app list, and playbook bullets
- Generates AppWorld Python code using app-specific patterns
- Writes response files containing **ONLY** the generated code

**What it does NOT do**:
- Does NOT execute code
- Does NOT simulate execution
- Does NOT provide TGC/SGC scores
- Does NOT generate error analysis

**Response format**:
```json
{
  "code": "# Generated Python code here",
  "reasoning": "Generated code using 5 playbook strategies",
  "timestamp": 1234567890.123
}
```

### 2. ClaudeCodeReActAgent (`utils/claude_code_react_agent.py`)

**Role**: Code Execution and Evaluation

**What it does**:
1. Writes request files to `/tmp/appworld_requests/`
2. Waits for Skill Monitor to generate code
3. Reads the generated code from response file
4. **Executes code in real AppWorld environment**
5. Gets **real TGC/SGC scores** from AppWorld test tracker
6. Provides execution feedback for next iteration

**Key methods**:
- `generate_code_interactive()` - Communicates with Skill Monitor (lines 120-224)
- `_execute_in_appworld()` - Executes code in AppWorld (lines 238-287)
- `solve_task()` - Main ReAct loop with execution (lines 289-410)

**Execution flow**:
```python
for turn in range(1, max_turns + 1):
    # Step 1: Generate code via interactive protocol
    code = self.generate_code_interactive(...)  # Asks Skill Monitor

    # Step 2: Execute code in REAL AppWorld
    result, success, tgc, sgc = self._execute_in_appworld(task_id, code)

    # Step 3: Store REAL execution results
    execution_history.append({
        'turn': turn,
        'result': result,
        'success': success,
        'tgc': tgc,  # Real score from AppWorld tests!
        'sgc': sgc   # Real score from AppWorld tests!
    })
```

### 3. AppWorldExecutor (`utils/appworld_executor.py`)

**Role**: ACE Integration Layer

**What it does**:
- Wraps ClaudeCodeReActAgent for ACE compatibility
- Analyzes real execution errors for bullet generation
- Provides rich error analysis from actual failures

**Key method**:
```python
def _analyze_execution_errors(execution_history, code_history, ...):
    """
    Analyzes REAL execution results to extract patterns:
    - API errors from real failures
    - Missing authentication from real attempts
    - Test failures from real AppWorld tests

    Returns structured error analysis for reflector.
    """
```

## Interactive Protocol Flow

```
┌─────────────────────────────────────────────────────────────┐
│  ACE Offline Adaptation (run_offline_adaptation.py)        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AppWorldExecutor                                           │
│  - Manages task execution                                   │
│  - Analyzes errors for bullet generation                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  ClaudeCodeReActAgent                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ReAct Loop (max 3 turns):                            │  │
│  │                                                       │  │
│  │  1. Write request file                               │  │
│  │     ├─ instruction                                   │  │
│  │     ├─ apps                                          │  │
│  │     ├─ bullets (from playbook)                       │  │
│  │     └─ execution_history (from previous turns)       │  │
│  │                                                       │  │
│  │  2. Wait for response ──────────┐                   │  │
│  │                                   │                   │  │
│  │  3. Read generated code ◄────────┤                   │  │
│  │                                   │                   │  │
│  │  4. EXECUTE in AppWorld          │                   │  │
│  │     ├─ world.execute(code)       │                   │  │
│  │     ├─ world.evaluate()          │                   │  │
│  │     └─ Get real TGC/SGC          │                   │  │
│  │                                   │                   │  │
│  │  5. If failed & turns left:      │                   │  │
│  │     └─ Loop with feedback        │                   │  │
│  │                                   │                   │  │
│  └───────────────────────────────────┴───────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  Skill Monitor (skill_monitor_standalone.py)               │
│  - Monitors /tmp/appworld_requests/                        │
│  - Generates code using app patterns                       │
│  - Writes response with CODE ONLY                          │
│  - Does NOT execute or simulate                            │
└─────────────────────────────────────────────────────────────┘
```

## Evidence of Real Execution

From `/tmp/offline_adaptation_enhanced_full.log`:

```
🚀 EXECUTING CODE IN APPWORLD
======================================================================

📊 EXECUTION RESULT:
  TGC: 0.25, SGC: 0.25 (2/8 tests passed)
  Success: ❌
  TGC: 0.25
  SGC: 0.25
```

The key evidence is **(2/8 tests passed)** - this message comes from the real AppWorld test tracker (`world.evaluate()`), not simulation.

## Common Misconception

**WRONG**: "The skill monitor simulates execution and returns fake TGC scores"

**CORRECT**:
- The skill monitor only generates code
- The ClaudeCodeReActAgent executes that code in real AppWorld
- Real TGC/SGC scores come from actual test execution
- The skill monitor's old `simulate_execution()` function was vestigial code that has been removed

## File Locations

```
plugins/ace-context-engineering/benchmarks/
├── skill_monitor_standalone.py          # Code generation service
├── utils/
│   ├── claude_code_react_agent.py      # Real execution in AppWorld
│   └── appworld_executor.py            # ACE integration
└── run_offline_adaptation.py           # Main evaluation script
```

## Summary

**The system IS running with real AppWorld execution!**

- Skill Monitor: Generates code (no execution)
- ClaudeCodeReActAgent: Executes code in AppWorld (real TGC scores)
- AppWorldExecutor: Analyzes real errors for bullet generation

The 30×2 offline adaptation uses real execution with real test results, not simulation.
