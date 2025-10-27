# ACE Plugin CI/CD Architecture

## Vision: Pure CI/CD ACE System

Instead of running ACE benchmarks locally, run everything in GitHub Actions. This provides:

1. **Reproducibility** - Same environment every time
2. **No Local Setup** - No Python deps, AppWorld installation, or OAuth complexity
3. **Automatic Scheduling** - Run benchmarks on schedule or triggers
4. **Result Tracking** - All results stored in git history
5. **Cost Efficient** - Only runs when needed, uses GitHub runners

## Current ACE Learning Loop

```
┌─────────────┐
│  AppWorld   │ ← Task executes here (requires local setup)
│   Executor  │
└──────┬──────┘
       │ feedback (TGC/SGC)
       ↓
┌─────────────┐
│  Reflector  │ ← Analyzes failures, creates bullets
└──────┬──────┘
       │ new bullets
       ↓
┌─────────────┐
│   Curator   │ ← Validates and merges bullets
└──────┬──────┘
       │ updates
       ↓
┌─────────────┐
│  Playbook   │ ← playbook.json (learned knowledge)
└──────┬──────┘
       │ retrieves bullets
       ↓
┌─────────────┐
│ ACE Code    │ ← Generates code using bullets
│  Generator  │
└──────┬──────┘
       │ code
       ↓
┌─────────────┐
│  AppWorld   │ ← Back to execution
│   Executor  │
└─────────────┘
```

**Problem**: All of this requires local setup (AppWorld, Python, OAuth, etc.)

## New Architecture: CI/CD-Only ACE

```
┌────────────────────────────────────────┐
│       GitHub Actions (Ubuntu)          │
│                                        │
│  ┌──────────────────────────────┐    │
│  │  ACE Benchmark Workflow       │    │
│  │                               │    │
│  │  1. Setup AppWorld            │    │
│  │  2. Load playbook.json        │    │
│  │  3. Run benchmarks            │    │
│  │  4. Collect results           │    │
│  │  5. Update playbook           │    │
│  │  6. Commit changes            │    │
│  └──────────────────────────────┘    │
│                                        │
│  ┌──────────────────────────────┐    │
│  │  Claude Code Skill Invoker    │    │
│  │  (uses ANTHROPIC_API_KEY)     │    │
│  └──────────────────────────────┘    │
│                                        │
└────────────────────────────────────────┘
                  │
                  │ commits results
                  ↓
         ┌────────────────┐
         │   Git Repo     │
         │                │
         │ - playbook.json│ ← Versioned learning
         │ - results/*.md │ ← Benchmark history
         │ - bulletsk/*.json│ ← Individual bullets
         └────────────────┘
```

## Workflow Designs

### 1. Scheduled Benchmark Run

**File**: `.github/workflows/ace-benchmark.yml`

**Purpose**: Run ACE benchmarks automatically

**Triggers**:
- Daily at 2 AM UTC
- Manual via `workflow_dispatch`
- On playbook changes

**Steps**:
```yaml
1. Checkout repository
2. Setup Python 3.11
3. Install AppWorld dependencies
4. Download AppWorld dataset
5. Run ACE benchmarks (5-10 tasks)
6. Generate results report
7. Update playbook.json with new bullets
8. Commit and push results
```

**Benefits**:
- No local setup required
- Automatic learning from failures
- Results tracked in git
- Can run on schedule

### 2. Manual Task Execution

**File**: `.github/workflows/ace-execute-task.yml`

**Purpose**: Test specific AppWorld task on demand

**Trigger**: Manual dispatch with task ID input

**Steps**:
```yaml
1. Checkout repository
2. Setup AppWorld
3. Load specific task
4. Generate code using ACE
5. Execute in AppWorld
6. Report results in PR comment
```

**Benefits**:
- Quick testing of specific tasks
- No local environment needed
- Results posted directly to PRs

### 3. Playbook Learning Workflow

**File**: `.github/workflows/ace-learning.yml`

**Purpose**: Continuous learning from benchmark results

**Triggers**:
- After benchmark workflow completes
- On failure analysis

**Steps**:
```yaml
1. Load latest benchmark results
2. Run Reflector on failures
3. Run Curator to validate bullets
4. Update playbook.json
5. Create PR with bullet changes
```

**Benefits**:
- Automatic knowledge accumulation
- Human review via PR
- Version controlled learning

## Implementation Plan

### Phase 1: Basic Benchmark Workflow

**Goal**: Run ACE benchmarks in CI/CD

**Tasks**:
1. ✅ Create `.github/workflows/ace-benchmark.yml`
2. ✅ Setup AppWorld installation in CI
3. ✅ Configure ANTHROPIC_API_KEY secret
4. ✅ Run 5 test tasks
5. ✅ Commit results to git

**Duration**: 1-2 hours

### Phase 2: Result Tracking

**Goal**: Store and visualize results

**Tasks**:
1. Create `results/` directory structure
2. Generate markdown reports per run
3. Create results dashboard (GitHub Pages)
4. Track TGC/SGC over time

**Duration**: 2-3 hours

### Phase 3: Automatic Learning

**Goal**: Close the learning loop in CI/CD

**Tasks**:
1. Run Reflector on failures
2. Run Curator to merge bullets
3. Auto-commit playbook updates
4. Create PRs for manual review

**Duration**: 3-4 hours

### Phase 4: Advanced Features

**Goal**: Production-ready ACE system

**Tasks**:
1. Parallel task execution
2. Cost tracking and limits
3. Performance benchmarking
4. Multi-model comparison

**Duration**: 1 week

## Workflow Configuration

### ace-benchmark.yml (Draft)

```yaml
name: ACE Benchmark

on:
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'

  workflow_dispatch:
    inputs:
      num_tasks:
        description: 'Number of tasks to run'
        required: false
        default: '5'

      split:
        description: 'Dataset split (train/dev/test_normal)'
        required: false
        default: 'dev'

jobs:
  benchmark:
    runs-on: ubuntu-latest
    timeout-minutes: 120

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for playbook

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install ACE dependencies
        run: |
          cd plugins/ace-context-engineering
          pip install -r requirements.txt

      - name: Setup AppWorld
        run: |
          cd /tmp
          git clone https://github.com/stonybrooknlp/appworld.git
          cd appworld
          pip install -e .

      - name: Download AppWorld data
        run: |
          cd /tmp/appworld
          python -m appworld.apps download
          python -m appworld.data download

      - name: Run ACE Benchmarks
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd plugins/ace-context-engineering
          python -m benchmarks.run_appworld \
            --split ${{ inputs.split || 'dev' }} \
            --max-samples ${{ inputs.num_tasks || '5' }} \
            --playbook skills/playbook.json \
            --output results/run-${{ github.run_number }}.json

      - name: Generate Report
        run: |
          cd plugins/ace-context-engineering
          python -m benchmarks.generate_report \
            --results results/run-${{ github.run_number }}.json \
            --output results/run-${{ github.run_number }}.md

      - name: Update Playbook
        run: |
          cd plugins/ace-context-engineering
          python -m benchmarks.update_playbook \
            --results results/run-${{ github.run_number }}.json \
            --playbook skills/playbook.json

      - name: Commit Results
        run: |
          git config user.name "ACE Bot"
          git config user.email "ace@claude-code-marketplace"
          git add plugins/ace-context-engineering/skills/playbook.json
          git add plugins/ace-context-engineering/results/
          git commit -m "chore: ACE benchmark results run #${{ github.run_number }}

          - Tasks: ${{ inputs.num_tasks || '5' }}
          - Split: ${{ inputs.split || 'dev' }}
          - Workflow: ${{ github.run_id }}

          🤖 Generated with [Claude Code](https://claude.com/claude-code)"
          git push
```

### ace-execute-task.yml (Draft)

```yaml
name: ACE Execute Task

on:
  workflow_dispatch:
    inputs:
      task_id:
        description: 'AppWorld Task ID'
        required: true

      create_pr_comment:
        description: 'Post result as PR comment'
        required: false
        default: 'false'

jobs:
  execute:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Setup AppWorld
        run: |
          # Same as benchmark workflow

      - name: Execute Task
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd plugins/ace-context-engineering
          python -m benchmarks.execute_single_task \
            --task-id "${{ inputs.task_id }}" \
            --playbook skills/playbook.json \
            --output results/task-${{ inputs.task_id }}.json

      - name: Post Result Comment (if requested)
        if: inputs.create_pr_comment == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const result = JSON.parse(
              fs.readFileSync('plugins/ace-context-engineering/results/task-${{ inputs.task_id }}.json')
            );

            const body = `## ACE Task Execution: ${{ inputs.task_id }}

            **Result**: ${result.success ? '✅ Success' : '❌ Failed'}
            **TGC**: ${result.tgc.toFixed(2)}
            **SGC**: ${result.sgc.toFixed(2)}
            **Turns**: ${result.turns}

            ### Bullets Used
            ${result.used_bullet_ids.join(', ')}

            ### Execution History
            ${result.execution_history.map((h, i) =>
              `${i+1}. ${h.result} (TGC: ${h.tgc.toFixed(2)})`
            ).join('\n')}
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

## Benefits of CI/CD-Only Approach

### For Development

✅ **No Local Setup**
- No AppWorld installation
- No Python environment management
- No OAuth complexity

✅ **Consistent Environment**
- Same Ubuntu version
- Same Python version
- Same dependencies

✅ **Easy Collaboration**
- Anyone can trigger workflows
- Results visible to all
- No "works on my machine"

### For ACE Learning

✅ **Automatic Evolution**
- Playbook updates automatically
- Continuous learning from failures
- Version controlled knowledge

✅ **Result History**
- Every run tracked in git
- Easy to see progress over time
- Can replay any historical run

✅ **Cost Efficient**
- Only runs when needed
- No idle local resources
- Parallel execution in cloud

## Migration from Local to CI/CD

### Current Local Setup

```bash
# Local development
cd plugins/ace-context-engineering
source ~/.config/ace_claude_code.env
python -m benchmarks.run_appworld --split dev --max-samples 5
```

**Problems**:
- Requires AppWorld installed locally
- Python environment management
- OAuth token management
- Results not tracked

### New CI/CD Approach

```bash
# Trigger from anywhere
gh workflow run ace-benchmark.yml \
  -f num_tasks=5 \
  -f split=dev

# Watch progress
gh run watch

# View results
gh run view --log
```

**Benefits**:
- No local setup needed
- Results automatically committed
- Can run from phone/tablet
- GitHub handles everything

## Next Steps

1. **Create base workflow** - Start with `ace-benchmark.yml`
2. **Test with 1 task** - Verify AppWorld setup works
3. **Scale to 5 tasks** - Validate results
4. **Add learning loop** - Reflector + Curator
5. **Enable scheduling** - Daily runs

Ready to implement? I can start with the benchmark workflow.
