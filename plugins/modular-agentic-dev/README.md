# Modular Agentic Development

**Structured framework for session-based, agent-driven development with modular prompts, audit checkpoints, subagent roles, and simulation harnesses.**

Inspired by Mitchell Hashimoto's Ghostty workflow and extended for full end-to-end code generation and review cycles.

## 🎯 Philosophy

The Modular Agentic Development plugin embodies four core principles:

1. **✳️ Sessions are modular and auditable** - Each AI session is self-contained with complete audit trails
2. **✳️ Final human audit is sacred** - Human developers review and approve all critical changes
3. **✳️ Simulations and tests guide the AI** - Test-driven development with simulation harnesses
4. **✳️ Clean data => clean code** - Normalized, well-structured data leads to better outputs

## 📦 What's Included

### Session Lifecycle Commands

- **`/session-plan`** - Initialize a new development session with structured planning
- **`/session-scaffold`** - Generate project structure from session plan
- **`/session-simulate`** - Run simulations and test harness against current code
- **`/session-cleanup`** - Clean and normalize session outputs
- **`/session-finalize`** - Finalize session with human review checkpoint

### Specialized Agents

- **`planner`** - High-level task decomposition and strategic planning
- **`coder`** - Clean, efficient code implementation
- **`reviewer`** - Code quality and architecture review
- **`tester`** - Comprehensive testing and QA
- **`researcher`** - Deep research and information gathering

### Automated Hooks

- **`pre_prompt_validator`** - Validate and normalize prompts before processing
- **`post_diff_tester`** - Run tests after code generation
- **`session_logger`** - Maintain complete audit trail of all interactions

### Workflows

- **`agentic-development`** - Complete development lifecycle workflow
- **`session-lifecycle`** - Session management with checkpoints and audits

## 🚀 Quick Start

### Installation

```bash
# Add marketplace
/plugin marketplace add https://github.com/jmanhype/claude-code-plugins

# Install plugin
/plugin install modular-agentic-dev
```

### Basic Usage

1. **Start a New Session**
   ```
   /session-plan "Build a user authentication system"
   ```
   Creates session directory, initializes metadata, generates task breakdown

2. **Scaffold the Structure**
   ```
   /session-scaffold
   ```
   Generates directory structure and boilerplate from plan

3. **Implement with Agents**
   ```
   /task --subagent_type=coder "Implement JWT authentication"
   ```
   Use specialized agents for focused tasks

4. **Run Simulations**
   ```
   /session-simulate
   ```
   Execute test harness and validate behavior

5. **Review and Finalize**
   ```
   /session-finalize
   ```
   Human review checkpoint before committing changes

## 🔧 Configuration

Optional environment variables:

```bash
# Session configuration
export SESSION_DIR=".claude/sessions"        # Session log directory
export AUDIT_LEVEL="standard"                # Audit verbosity (minimal/standard/full)
export SIMULATION_MODE="true"                # Enable simulation harness

# Quality gates
export MATURITY_THRESHOLD="80"               # Minimum maturity score for finalization
export REQUIRE_TESTS="true"                  # Enforce test coverage
```

## 📊 Session Structure

Each session creates a structured workspace:

```
.claude/sessions/<session-id>/
├── _meta/
│   ├── session.yaml          # Session metadata
│   ├── spec-map.yaml          # Specification tracking
│   └── maturity.md            # Quality checklist
├── transcripts/
│   ├── planning.md            # Planning phase transcript
│   ├── implementation.md      # Implementation transcript
│   └── review.md              # Review phase transcript
├── artifacts/
│   ├── generated/             # AI-generated code
│   └── approved/              # Human-approved code
└── simulations/
    ├── test-vectors.json      # Test inputs
    └── results.json           # Simulation results
```

## 🧠 Agent Roles Explained

### Planner
- **Purpose**: Strategic decomposition of complex tasks
- **When to use**: Start of new features, architectural decisions
- **Output**: Task breakdown, dependency graph, implementation sequence

### Coder
- **Purpose**: Clean, efficient code implementation
- **When to use**: After planning, for focused implementation tasks
- **Output**: Production-ready code with inline documentation

### Reviewer
- **Purpose**: Code quality and architectural review
- **When to use**: After implementation, before finalization
- **Output**: Quality assessment, improvement suggestions, approval

### Tester
- **Purpose**: Comprehensive testing and validation
- **When to use**: Throughout development, especially before review
- **Output**: Test suites, coverage reports, bug findings

### Researcher
- **Purpose**: Deep research and information gathering
- **When to use**: When exploring new libraries, patterns, or domains
- **Output**: Research summary, recommendations, best practices

## 🎬 Example Workflows

### Feature Development

```bash
# 1. Plan the feature
/session-plan "Add OAuth2 social login"

# 2. Research best practices
/task --subagent_type=researcher "Research OAuth2 best practices for Express.js"

# 3. Scaffold structure
/session-scaffold

# 4. Implement
/task --subagent_type=coder "Implement Google OAuth2 provider"

# 5. Test
/session-simulate

# 6. Review
/task --subagent_type=reviewer "Review OAuth2 implementation"

# 7. Finalize
/session-finalize
```

### Bug Fix

```bash
# 1. Start session
/session-plan "Fix memory leak in WebSocket handler"

# 2. Research the issue
/task --subagent_type=researcher "Analyze WebSocket memory patterns"

# 3. Implement fix
/task --subagent_type=coder "Fix WebSocket memory leak"

# 4. Test thoroughly
/task --subagent_type=tester "Create test suite for WebSocket lifecycle"
/session-simulate

# 5. Finalize
/session-finalize
```

### Refactoring

```bash
# 1. Plan refactoring
/session-plan "Refactor authentication module for testability"

# 2. Code review first
/task --subagent_type=reviewer "Review current authentication implementation"

# 3. Implement refactoring
/task --subagent_type=coder "Refactor auth module with dependency injection"

# 4. Ensure tests pass
/session-simulate

# 5. Final review
/task --subagent_type=reviewer "Verify refactoring maintains behavior"
/session-finalize
```

## 🛡️ Quality Gates

The plugin enforces quality through automated checks:

### Pre-Finalization Checklist

- ✅ All tests passing
- ✅ Code coverage meets threshold
- ✅ No critical security issues
- ✅ Documentation complete
- ✅ Maturity score ≥ threshold
- ✅ Human review completed

### Maturity Scoring

Each session tracks maturity across dimensions:

```yaml
maturity:
  code_quality: 85/100      # Code structure, patterns, readability
  test_coverage: 90/100     # Test completeness and quality
  documentation: 75/100     # Inline docs, READMEs, comments
  security: 95/100          # Security best practices
  performance: 80/100       # Performance considerations
  maintainability: 85/100   # Long-term maintainability
  overall: 85/100           # Weighted average
```

## 🔍 Audit Trail

Every session maintains a complete audit trail:

### What's Logged

- All prompts and responses
- Agent invocations and results
- Code generations and modifications
- Test results and simulations
- Human review decisions
- Configuration changes

### Accessing Audit Logs

```bash
# View current session log
cat .claude/sessions/<session-id>/transcripts/implementation.md

# Check maturity score
cat .claude/sessions/<session-id>/_meta/maturity.md

# Review test results
cat .claude/sessions/<session-id>/simulations/results.json
```

## 🎯 Advanced Features

### Custom Simulation Harnesses

Create custom simulation scenarios:

```bash
# Define test vectors
echo '[
  {"input": "user@example.com", "expected": "valid"},
  {"input": "invalid-email", "expected": "error"}
]' > .claude/sessions/<session-id>/simulations/test-vectors.json

# Run simulations
/session-simulate
```

### Integration with External Tools

The plugin integrates with:

- **Conductor** - State management and coordination
- **JIDO** - Workflow orchestration
- **Custom MCP Servers** - Your own tool integrations

### Extending the Plugin

Add custom commands by creating markdown files:

```markdown
<!-- my-custom-command.md -->
# My Custom Command

## Purpose
Describe what this command does

## Usage
/my-custom-command [args]

## Implementation
Script to execute: ./scripts/my-command.sh
```

## 🤝 Best Practices

### Do's ✅

- Always start with `/session-plan`
- Use specialized agents for focused tasks
- Run simulations before finalizing
- Maintain clean session boundaries
- Review maturity scores regularly
- Keep audit trails for compliance

### Don'ts ❌

- Don't skip planning phase
- Don't finalize without human review
- Don't mix multiple concerns in one session
- Don't ignore test failures
- Don't bypass quality gates

## 📚 Resources

- **Full Documentation**: [Agentic Development Workflow](https://github.com/jmanhype/multi-agent-system/blob/main/.claude/workflows/agentic-development.md)
- **Session Lifecycle**: [Session Management](https://github.com/jmanhype/multi-agent-system/blob/main/.claude/workflows/session-lifecycle.md)
- **Source Repository**: [multi-agent-system](https://github.com/jmanhype/multi-agent-system)

## 🐛 Troubleshooting

### Session won't finalize

Check maturity score:
```bash
cat .claude/sessions/<session-id>/_meta/maturity.md
```

Ensure all quality gates pass:
```bash
/task --subagent_type=tester "Verify all quality gates"
```

### Simulations failing

Review test vectors:
```bash
cat .claude/sessions/<session-id>/simulations/test-vectors.json
```

Check simulation results:
```bash
cat .claude/sessions/<session-id>/simulations/results.json
```

### Hooks not executing

Verify hook permissions:
```bash
chmod +x .claude/hooks/*.sh
```

Check hook logs:
```bash
tail -f .claude/hooks/logs/*.log
```

## 📄 License

MIT License - see [LICENSE](https://github.com/jmanhype/multi-agent-system/blob/main/LICENSE)

## 🙏 Credits

Inspired by Mitchell Hashimoto's Ghostty development workflow and the principles of agentic engineering.

Built with 🧊 by [@jmanhype](https://github.com/jmanhype)
