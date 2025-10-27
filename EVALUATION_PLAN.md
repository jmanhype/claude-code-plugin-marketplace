# ACE Evaluation Plan

## Current Status

✅ **Implemented:**
- Full ACE framework (Generator → Reflector → Curator)
- Bullet retrieval using TF-IDF
- Bullet-driven code generation (not pattern matching)
- Multi-epoch offline adaptation
- Bullet feedback tracking (helpful_count updates)
- Grow-and-refine deduplication
- Tested on 3 synthetic tasks with 100% success

❌ **Missing for Full Evaluation:**
- Real AppWorld dataset (test-normal split with 100+ tasks)
- Baseline methods (GEPA, Dynamic Cheatsheet, Zero-shot)
- Evaluation metrics (TGC, SGC)
- Performance comparison showing +10.6% lift

## Questions on Shadow/Staging/Prod Strategy

**Please clarify what you mean by shadow/staging/prod:**

### Option 1: Evaluation Phases
- **Staging**: Test on small subset (10-20 tasks) to debug
- **Shadow**: Run ACE + baselines in parallel, compare outputs
- **Prod**: Full evaluation on complete test-normal split

### Option 2: Paper's Methodology
- **Offline**: Train on train split, evaluate on test split
- **Online**: Sequential test-time learning on test set
- **Baselines**: Compare ACE vs GEPA vs Cheatsheet vs Zero-shot

### Option 3: Deployment Strategy
- **Shadow**: ACE runs alongside current system, logs don't affect it
- **Staging**: Test in controlled environment first
- **Prod**: Full deployment/evaluation

## Proposed Next Steps

### Step 1: Get Real AppWorld Data
```bash
# AppWorld needs to be installed
pip install appworld
appworld install  # Downloads dataset

# Or use their test data directly if available
```

### Step 2: Implement Baselines
Based on ACE paper Section 4:

**GEPA (General Episodic Propositional Agent)**
- Maintains general episodic memory
- No retrieval mechanism
- Just accumulates all past experiences

**Dynamic Cheatsheet**
- Maintains task-specific tips
- Updates after each task
- No semantic retrieval

**Zero-shot**
- No memory/adaptation
- Fresh prompt each time

### Step 3: Evaluation Harness
Implement TGC/SGC metrics from AppWorld paper:
- **TGC** (Task Goal Completion): Did agent complete the task?
- **SGC** (Scenario Goal Completion): Side effects correct?

### Step 4: Run Experiments
```
For each method (ACE, GEPA, Cheatsheet, Zero-shot):
    For each mode (offline, online):
        Run on test-normal split
        Calculate TGC/SGC
        Save results

Compare:
    ACE vs baselines
    Offline vs online
    Verify +10.6% lift on agents
```

## Implementation Time Estimates

- [ ] Download AppWorld data: 30 min
- [ ] Implement GEPA baseline: 2 hours
- [ ] Implement Dynamic Cheatsheet: 2 hours
- [ ] Evaluation harness with TGC/SGC: 3 hours
- [ ] Run full experiments: 4-8 hours (depending on dataset size)
- [ ] Analysis and reporting: 2 hours

**Total**: ~1-2 days

## Which Strategy Do You Want?

Please clarify:

1. **Shadow/staging/prod means what exactly?**
   - Evaluation phases (small → full dataset)?
   - Paper's offline vs online modes?
   - Something else?

2. **Priorities:**
   - Speed (run on 10 tasks to prove concept)?
   - Rigor (full 100+ task evaluation)?
   - Both (staging → prod)?

3. **Baselines needed:**
   - All three (GEPA, Cheatsheet, Zero-shot)?
   - Just Zero-shot for quick comparison?
   - Match paper exactly?

Once you clarify, I'll implement the evaluation strategy!
