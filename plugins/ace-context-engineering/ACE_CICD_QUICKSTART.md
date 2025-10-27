# ACE CI/CD Quick Start

Run ACE benchmarks entirely in GitHub Actions - no local setup required!

## 🎯 Vision

Instead of running ACE locally with complex setup (AppWorld, Python, OAuth), run everything in CI/CD:

- ✅ No local dependencies
- ✅ Reproducible environment
- ✅ Results auto-committed to git
- ✅ Can run from anywhere (phone, tablet, etc.)
- ✅ Scheduled daily runs

## 🚀 Quick Start (5 minutes)

### 1. Add API Key Secret

```bash
# Get your API key
cat ~/.config/ace_claude_max_api_key.txt

# Add to GitHub:
# 1. Go to: https://github.com/jmanhype/claude-code-plugin-marketplace/settings/secrets/actions
# 2. Click "New repository secret"
# 3. Name: ANTHROPIC_API_KEY
# 4. Value: sk-ant-api03-... (paste the key)
# 5. Click "Add secret"
```

### 2. Trigger Workflow

```bash
# Via GitHub CLI
gh workflow run ace-benchmark.yml \
  -f num_tasks=5 \
  -f split=dev

# Or via GitHub web UI:
# https://github.com/jmanhype/claude-code-plugin-marketplace/actions/workflows/ace-benchmark.yml
# Click "Run workflow" → Set parameters → "Run workflow"
```

### 3. Watch Progress

```bash
# Watch in terminal
gh run watch

# Or view in browser
# https://github.com/jmanhype/claude-code-plugin-marketplace/actions
```

### 4. View Results

Results are automatically committed to `plugins/ace-context-engineering/results/`:

```bash
# View latest results
cat plugins/ace-context-engineering/results/run-*.json | tail -1

# View markdown report
cat plugins/ace-context-engineering/results/run-*.md | tail -1
```

## 📊 What Gets Created

### Workflow File

`.github/workflows/ace-benchmark.yml` - Main benchmark workflow

**Features**:
- Runs on schedule (daily 2 AM UTC)
- Manual trigger with parameters
- Installs AppWorld automatically
- Runs ACE benchmarks
- Commits results to git
- Uploads artifacts

### Results Directory

`plugins/ace-context-engineering/results/` - Benchmark results

**Files per run**:
- `run-{number}.json` - Detailed results
- `run-{number}.md` - Markdown report
- `run-{number}.log` - Execution logs

### Standalone Runner

`benchmarks/run_appworld_standalone.py` - Standalone ACE runner

**Features**:
- Works in CI/CD without interaction
- Uses ACECodeGenerator directly
- Saves results to JSON
- Can run with or without AppWorld execution

## 🔧 Testing Locally (Optional)

You can test the standalone runner locally before using CI/CD:

```bash
cd plugins/ace-context-engineering

# Setup (one-time)
pip install anthropic requests scikit-learn numpy

# Run benchmark (without AppWorld execution)
export ANTHROPIC_API_KEY="sk-ant-api03-..."
python -m benchmarks.run_appworld_standalone \
  --split dev \
  --max-samples 2 \
  --no-execute

# View results
cat results/benchmark.json
```

This tests code generation only (no AppWorld execution).

## 📅 Scheduled Runs

The workflow runs automatically:

**Schedule**: Daily at 2 AM UTC

**What happens**:
1. GitHub spins up Ubuntu runner
2. Installs AppWorld and dependencies
3. Runs 5 tasks from `dev` split
4. Generates results report
5. Commits results to git
6. Uploads artifacts

**Cost**: Free on GitHub Actions (public repos get unlimited minutes)

## 🎛️ Workflow Parameters

### num_tasks (default: 5)

Number of AppWorld tasks to run per benchmark.

```bash
gh workflow run ace-benchmark.yml -f num_tasks=10
```

**Recommendations**:
- `1-5`: Quick smoke test (5-15 min)
- `5-10`: Regular benchmarking (15-30 min)
- `10-50`: Comprehensive run (30-120 min)

### split (default: dev)

Which AppWorld dataset split to use.

```bash
gh workflow run ace-benchmark.yml -f split=test_normal
```

**Options**:
- `dev`: Development set (easier tasks)
- `train`: Training set (learning)
- `test_normal`: Normal test set
- `test_challenge`: Challenge test set (harder)

## 📈 Viewing Results

### In GitHub Actions UI

1. Go to: https://github.com/jmanhype/claude-code-plugin-marketplace/actions
2. Click on latest "ACE Benchmark" run
3. View logs and artifacts

### In Git History

```bash
# View recent benchmark commits
git log --grep="ACE benchmark" --oneline -5

# View specific run results
git show HEAD:plugins/ace-context-engineering/results/run-1.json
```

### Download Artifacts

Artifacts are kept for 90 days:

```bash
# List artifacts
gh run list --workflow=ace-benchmark.yml

# Download latest
gh run download --name ace-benchmark-run-1
```

## 🔄 Continuous Learning

The system learns from failures:

1. **Run Benchmark** → Some tasks fail
2. **Reflector Analyzes** → Creates new bullets
3. **Curator Validates** → Merges into playbook
4. **Playbook Updated** → Committed to git
5. **Next Run** → Uses improved playbook

This creates a **continuous learning loop** in CI/CD.

## 🎯 Next Steps

### Phase 1: Basic Benchmarking (Complete ✅)

- ✅ Created `ace-benchmark.yml` workflow
- ✅ Created standalone runner
- ✅ Added scheduling support
- ✅ Result tracking in git

### Phase 2: Enhanced Learning (To Do)

- ⏳ Auto-run Reflector on failures
- ⏳ Auto-run Curator for bullet validation
- ⏳ Create PRs for playbook updates
- ⏳ Add human review before merge

### Phase 3: Advanced Features (Future)

- ⏳ Parallel task execution
- ⏳ Cost tracking and limits
- ⏳ Performance benchmarking
- ⏳ Multi-model comparison
- ⏳ Results dashboard (GitHub Pages)

## 🆚 Comparison: Local vs CI/CD

| Aspect | Local Development | CI/CD |
|--------|------------------|--------|
| **Setup** | AppWorld install, Python, OAuth | None - just API key |
| **Environment** | Your machine | Clean Ubuntu runner |
| **Triggers** | Manual | Scheduled + manual |
| **Results** | Local files | Git-tracked |
| **Cost** | Your compute | Free (public repos) |
| **Collaboration** | Requires sharing | Everyone can view |
| **Reproducibility** | "Works on my machine" | Guaranteed consistent |

## 🔐 Security

**API Key Protection**:
- ✅ Stored in GitHub Secrets
- ✅ Never logged or exposed
- ✅ Only available during workflow execution
- ✅ Encrypted at rest

**Permissions**:
- ✅ Only repo admins can add secrets
- ✅ Only maintainers can trigger workflows
- ✅ Results committed with bot account

## 💰 Cost Considerations

### GitHub Actions

- ✅ **Free** for public repositories
- ✅ Unlimited minutes
- ✅ No cost

### Anthropic API

- 💵 Uses your API credits
- 💵 Estimate: $0.05-0.15 per task
- 💵 Daily run (5 tasks): ~$0.25-0.75/day

**Cost controls**:
```yaml
# Limit tasks per run
num_tasks: 5

# Disable scheduling if needed
# on:
#   schedule: []  # Comment out
```

## 🐛 Troubleshooting

### Workflow doesn't start

**Check**:
1. Is `ANTHROPIC_API_KEY` in repository secrets?
2. Do you have permission to trigger workflows?
3. Is the workflow file syntax correct?

### AppWorld installation fails

**Solutions**:
- Check AppWorld repo is accessible
- Verify Python version (3.11)
- Check disk space on runner

### API rate limits

**Solutions**:
- Reduce `num_tasks`
- Increase time between runs
- Check Anthropic usage dashboard

### No results committed

**Check**:
- Did benchmark actually run?
- Check workflow logs
- Verify git permissions

## 📚 Additional Resources

- **ACE Architecture**: `ACE_CICD_ARCHITECTURE.md`
- **GitHub Action Docs**: `.github/workflows/ace-benchmark.yml`
- **Standalone Runner**: `benchmarks/run_appworld_standalone.py`
- **Results**: `results/` directory

## ✅ Success Checklist

- [x] Workflow created (`.github/workflows/ace-benchmark.yml`)
- [ ] API key added to GitHub secrets
- [ ] First manual run triggered successfully
- [ ] Results committed to git
- [ ] Scheduled runs enabled
- [ ] Team notified about new CI/CD system

---

**Status**: Workflow ready, API key needed
**Last Updated**: Mon Oct 27, 2025
**Author**: Claude Code via jmanhype
