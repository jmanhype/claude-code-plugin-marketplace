# Tools Context

## Purpose

This file documents tools, skills, MCP servers, and their usage policies for the Claude Code agent.

---

## Available Tools Overview

### File Operations

- **Read**: Read files (supports offset/limit for large files)
- **Write**: Create or overwrite files
- **Edit**: Make precise string replacements in files
- **Glob**: Find files by pattern (e.g., "**/*.js")
- **Grep**: Search file contents (supports regex, context lines)

### Execution

- **Bash**: Execute shell commands (with timeout support)
- **BashOutput**: Retrieve output from background shells
- **KillShell**: Terminate background shells

### Task Management

- **TodoWrite**: Manage structured task lists
- **Task**: Launch specialized sub-agents for complex work

### Context Management

- **ExitPlanMode**: Signal completion of planning phase
- **SlashCommand**: Execute custom slash commands
- **Skill**: Invoke specialized skills

### Web & Search

- **WebFetch**: Fetch and analyze web content
- **WebSearch**: Search the web for current information

### Specialized

- **NotebookEdit**: Edit Jupyter notebook cells

---

## Tool Usage Policies

### General Principles

1. **Use specialized tools first**: Prefer Read over `cat`, Edit over `sed`, Glob over `find`
2. **Parallel when possible**: Make independent tool calls simultaneously
3. **Sequential when dependent**: Wait for results before making dependent calls
4. **No placeholders**: Never guess parameter values; wait for actual data

### File Operations

#### Read

**When to use:**

- Reading specific files by path
- Inspecting file contents before editing
- Reviewing configuration or documentation

**Best practices:**

- Always read before editing (Edit tool requires prior read)
- Use offset/limit for very large files
- Read multiple files in parallel when independent

**Anti-patterns:**

- Using Bash `cat` instead of Read
- Reading entire file when only need specific section
- Not reading before Edit (will fail)

#### Write

**When to use:**

- Creating new files
- Completely replacing file contents

**Best practices:**

- Prefer Edit over Write for existing files
- Read existing file first if unsure whether it exists
- Don't create unnecessary documentation files (*.md) proactively

**Anti-patterns:**

- Writing when Edit would be more precise
- Creating files without checking if they exist
- Using `echo >` or heredocs in Bash instead of Write

#### Edit

**When to use:**

- Modifying existing files
- Making precise, targeted changes
- Preserving context and formatting

**Best practices:**

- Always Read file first (Edit requires it)
- Match exact indentation from Read output (after line number prefix)
- Provide enough context in old_string to be unique
- Use replace_all for renaming variables across file

**Anti-patterns:**

- Including line numbers in old_string/new_string
- Not reading file first
- Making changes without unique old_string match
- Using sed/awk in Bash instead of Edit

#### Glob

**When to use:**

- Finding files by pattern
- Discovering project structure
- Locating specific file types

**Best practices:**

- Use patterns like "**/*.js" for recursive search
- Combine with Grep for content-based filtering
- Make multiple speculative Glob calls in parallel

**Anti-patterns:**

- Using `find` in Bash instead of Glob
- Not using wildcards for broader matches
- Sequential globs when parallel would work

#### Grep

**When to use:**

- Searching code for patterns
- Finding function/class definitions
- Locating specific strings or regex matches

**Best practices:**

- Use output_mode: "files_with_matches" for file lists
- Use output_mode: "content" with -n for line numbers
- Filter with glob or type parameters
- Use -i for case-insensitive search
- Set multiline: true for cross-line patterns

**Anti-patterns:**

- Using `grep` or `rg` in Bash instead of Grep tool
- Not specifying output_mode appropriately
- Forgetting to escape special regex characters

---

## Bash Tool Policies

### When to Use Bash

✅ **Appropriate uses:**

- Git operations (status, diff, commit, push, pull, fetch)
- Package managers (npm, pip, cargo)
- Build tools (make, cmake, webpack)
- Docker/containerization commands
- System commands that require shell
- Chaining commands with && or ;

❌ **Avoid Bash for:**

- File reading (use Read)
- File editing (use Edit)
- File creation (use Write)
- File search (use Glob)
- Content search (use Grep)
- Communication with user (use direct text output)

### Bash Best Practices

#### Quoting

```bash
# Correct: paths with spaces
cd "/path/with spaces/directory"
python "/path/with spaces/script.py"

# Incorrect: will fail
cd /path/with spaces/directory
```

#### Parallel vs Sequential

```bash
# Parallel (independent commands): make separate Bash calls
# Call 1: git status
# Call 2: git diff

# Sequential (dependent commands): use && in single call
git add . && git commit -m "message" && git push
```

#### Timeouts

- Default: 120000ms (2 minutes)
- Maximum: 600000ms (10 minutes)
- Specify longer timeout for slow operations

#### Background Execution

```bash
# Use run_in_background: true for long-running commands
# Monitor with BashOutput tool
# Don't use for 'sleep' command
# Don't add '&' at end when using this parameter
```

---

## Git Operations

### Git Push Policy

**CRITICAL**: Branch names must start with `claude/` and end with session ID, or push will fail with 403.

```bash
# Correct
git push -u origin claude/feature-name-SESSION123

# Always use -u flag for new branches
# Retry up to 4 times with exponential backoff on network errors:
# 2s, 4s, 8s, 16s
```

### Git Fetch/Pull Policy

```bash
# Prefer specific branches
git fetch origin feature-branch
git pull origin feature-branch

# Retry up to 4 times with exponential backoff on network errors
```

### Git Commit Policy

**Only commit when explicitly requested by user.**

#### Safety Protocol

- ❌ NEVER update git config
- ❌ NEVER run destructive commands (push --force, hard reset) without explicit request
- ❌ NEVER skip hooks (--no-verify) without explicit request
- ❌ NEVER force push to main/master (warn user if requested)
- ⚠️ Avoid `git commit --amend` (only use if explicitly requested or for pre-commit hook fixes)

#### Commit Workflow

1. Run in parallel:
   - `git status` (see untracked files)
   - `git diff` (see staged/unstaged changes)
   - `git log` (understand commit message style)

2. Draft commit message:
   - Summarize nature of changes (feature, fix, refactor, docs, etc.)
   - Focus on "why" not "what"
   - Don't commit secrets (.env, credentials, etc.)
   - End with attribution:
     ```
     🤖 Generated with [Claude Code](https://claude.com/claude-code)

     Co-Authored-By: Claude <noreply@anthropic.com>
     ```

3. Add files and commit:
   - Add relevant untracked files
   - Create commit using heredoc for message
   - Run `git status` after to verify

4. Handle pre-commit hook failures:
   - If hook modifies files, check if safe to amend
   - Verify authorship: `git log -1 --format='%an %ae'`
   - Verify not pushed: git status shows "Your branch is ahead"
   - Only amend if both true; otherwise make new commit

**Example commit with heredoc:**

```bash
git commit -m "$(cat <<'EOF'
feat: Add user authentication feature

Implements JWT-based authentication with refresh tokens.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Git PR Creation

Use `gh` CLI for GitHub operations.

#### PR Workflow

1. Run in parallel:
   - `git status` (see untracked files)
   - `git diff` (see staged/unstaged changes)
   - Check if branch tracks remote and is up to date
   - `git log` and `git diff [base]...HEAD` (understand full commit history)

2. Analyze ALL commits that will be in PR (not just latest)

3. Run in parallel:
   - Create branch if needed
   - Push with -u if needed
   - Create PR with heredoc body:

```bash
gh pr create --title "PR title" --body "$(cat <<'EOF'
## Summary
- Bullet point 1
- Bullet point 2

## Test plan
- [ ] Test item 1
- [ ] Test item 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Task Tool (Sub-agents)

### Available Agent Types

#### general-purpose

- Full tool access
- Complex multi-step tasks
- Research and code search

#### Explore

- **Fast codebase exploration**
- Specialized for finding files and searching code
- Use when exploring codebase structure or answering "how does X work?"

**Thoroughness levels:**

- "quick": Basic searches
- "medium": Moderate exploration
- "very thorough": Comprehensive analysis

**When to use:**

- ✅ Exploring codebase to answer questions
- ✅ Understanding how features work
- ✅ Finding files by patterns or keywords
- ❌ NOT for reading specific known file paths (use Read)
- ❌ NOT for searching specific class definitions (use Glob)

### Task Tool Best Practices

1. **Launch multiple agents in parallel** when possible (single message, multiple Task calls)
2. **Provide detailed task description** (agent is stateless, gets one shot)
3. **Specify what information to return** in final message
4. **Clearly state if writing code or just researching**
5. **Trust agent outputs** (they are generally reliable)
6. **Use proactively** when agent description matches task

---

## TodoWrite Tool

### When to Use

✅ **Use TodoWrite when:**

- Task has 3+ distinct steps
- Task is non-trivial and complex
- User explicitly requests todo list
- User provides multiple tasks
- After receiving new instructions (capture requirements)
- Before starting work (mark in_progress)
- After completing task (mark completed, add follow-ups)

❌ **Don't use TodoWrite when:**

- Single straightforward task
- Trivial task (< 3 simple steps)
- Purely conversational/informational
- Task can be done in one shot

### Task State Management

**States:**

- `pending`: Not started
- `in_progress`: Currently working (EXACTLY ONE at a time)
- `completed`: Finished successfully

**Task descriptions must have TWO forms:**

- `content`: Imperative (e.g., "Run tests")
- `activeForm`: Present continuous (e.g., "Running tests")

**Rules:**

- Update status in real-time
- Mark complete IMMEDIATELY after finishing
- EXACTLY ONE task in_progress at any time
- Complete current before starting next
- Remove tasks that become irrelevant

**Completion requirements:**

✅ **Only mark completed when:**

- Task is FULLY accomplished
- Tests pass (if applicable)
- No unresolved errors
- Implementation is complete

❌ **Keep in_progress if:**

- Tests failing
- Implementation partial
- Errors encountered
- Blocked by dependencies

---

## Web Tools

### WebFetch

**When to use:**

- Fetching specific URL content
- Analyzing documentation pages
- Retrieving information from known URLs

**Best practices:**

- Provide clear prompt for what to extract
- Handle redirects (tool will inform you)
- Prefer MCP web fetch tools if available (start with `mcp__`)

### WebSearch

**When to use:**

- Finding current information beyond knowledge cutoff
- Researching recent events
- Discovering relevant documentation

**Best practices:**

- Account for "Today's date" in queries
- Use domain filtering when appropriate
- Combine with WebFetch to dive deeper

---

## Tool Combinations (Recipes)

### Explore Codebase Pattern

**Task**: Understand how feature X works

```
1. Use Task tool with subagent_type=Explore, thoroughness="medium"
2. Review agent's findings
3. Use Read tool on specific files agent identified
```

### Fix Bugs Pattern

**Task**: Fix errors in code

```
1. Use Grep to find error locations
2. Use Read to understand context
3. Use Edit to make fixes (read first!)
4. Use Bash to run tests
5. Iterate until tests pass
```

### Add Feature Pattern

**Task**: Implement new feature

```
1. Use TodoWrite to plan steps
2. Use Glob/Grep to find relevant files
3. Use Read to understand existing code
4. Use Edit/Write to implement (prefer Edit)
5. Use Bash to test
6. Mark todos as completed
```

### Research Pattern

**Task**: Answer "How does X work?"

```
1. Use Task (Explore) for quick discovery
2. Use Read for detailed examination
3. Combine findings in response
```

---

## Common Pitfalls

### ❌ Anti-patterns

- Using Bash for file operations (use specialized tools)
- Not reading file before Edit
- Making sequential tool calls when parallel would work
- Guessing parameter values instead of waiting
- Over-using Task tool for simple operations
- Not updating TodoWrite in real-time

### ✅ Best Practices

- Match tool to task (specialized > general)
- Parallel by default, sequential when needed
- Read before Edit (always)
- Clear task descriptions for sub-agents
- Real-time todo updates
- Retry with backoff for network operations

---

## Quick Reference

### File Operations Decision Tree

```
Need to...
├─ Read file? → Read tool
├─ Create new file? → Write tool
├─ Modify existing? → Edit tool (read first!)
├─ Find files? → Glob tool
└─ Search content? → Grep tool
```

### Bash Decision Tree

```
Need to...
├─ File operation? → Use specialized tool (NOT Bash)
├─ Git operation? → Bash (with retry logic)
├─ Build/test? → Bash
├─ Package manager? → Bash
└─ System command? → Bash
```

### Task Decision Tree

```
Need to...
├─ Explore codebase? → Task (Explore, specify thoroughness)
├─ Complex multi-step? → Task (general-purpose)
├─ Simple/specific? → Direct tools (NOT Task)
└─ Read known file? → Read (NOT Task)
```

---

## Tool Performance Tips

1. **Batch reads**: Read multiple files in parallel
2. **Cache awareness**: Re-reading same file is fast
3. **Context budget**: Don't over-fetch; use progressive disclosure
4. **Parallel tool calls**: Maximize concurrency for independent operations
5. **Specialized agents**: Use Task tool for complex discovery, not simple reads

---

**Last Updated**: 2025-10-25
