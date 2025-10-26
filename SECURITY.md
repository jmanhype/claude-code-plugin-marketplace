# Security Policy

## Overview

This marketplace contains plugins that may execute code, access networks, and (in limited cases) perform real trading. Security is our top priority.

## Threat Model

### In-Scope Threats

1. **Supply-chain attacks**: Malicious code in remote plugin sources
2. **Hook execution risks**: Shell scripts with unintended side effects
3. **Credential leakage**: API keys, secrets exposed in logs or code
4. **Privilege escalation**: Plugins gaining unauthorized access
5. **Trading system abuse**: Unauthorized live trading or excessive risk

### Out-of-Scope (User Responsibility)

- Host OS security and patching
- Physical access to machines running plugins
- Social engineering attacks on plugin maintainers

## Security Measures

### 1. Remote Source Pinning

**Problem**: Plugins referencing `https://raw.githubusercontent.com/.../main/file.sh` can change silently.

**Solution**: All remote sources MUST be pinned to commit SHAs and have integrity hashes.

#### Example (Insecure)

```json
{
  "hooks": [
    {
      "name": "pre_trade",
      "source": "https://raw.githubusercontent.com/user/repo/main/.claude/hooks/pre_trade.sh"
    }
  ]
}
```

#### Example (Secure)

```json
{
  "hooks": [
    {
      "name": "pre_trade",
      "source": "https://raw.githubusercontent.com/user/repo/a1b2c3d4/.claude/hooks/pre_trade.sh",
      "integrity": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  ]
}
```

**How to generate integrity hash**:

```bash
curl -sL <url> | sha256sum | awk '{print $1}'
```

**CI Enforcement**: The `validate.yml` GitHub Actions workflow rejects any plugin with unpinned sources.

### 2. Permissions Model

All plugins MUST declare their required permissions in `plugin.json`:

```json
{
  "permissions": {
    "filesystem": true,   // Read/write local files
    "network": true,      // Make network requests
    "exec": false,        // Execute shell commands
    "env": true,          // Access environment variables
    "trading": "paper"    // Trading mode: "none", "paper", or "live"
  }
}
```

**Permission Levels**:

| Permission | Risk | Use Cases |
|------------|------|-----------|
| `filesystem` | Medium | Logging, config, bullet storage |
| `network` | Medium | Exchange APIs, web scraping |
| `exec` | **High** | Running hooks, shell scripts |
| `env` | Low | Reading API keys, config |
| `trading: live` | **Critical** | Real money trading (requires approval) |

**Default**: Plugins without declared permissions are treated as **untrusted** and may be rejected by loaders.

### 3. Hook Sandboxing

Shell hooks (`pre_run`, `post_run`, etc.) pose the highest execution risk.

#### Recommended Sandboxing Approaches

**Option A: Disable hooks by default**

```python
# In plugin loader
if not user_approved_hooks(plugin_name):
    raise PermissionError(f"Hooks for {plugin_name} not approved")
```

**Option B: Run in restricted environment**

```bash
# Use firejail or similar
firejail --noprofile --net=none --private=./sandbox bash hook.sh
```

**Option C: Dry-run first**

```bash
# Preview hook without execution
bash -n hook.sh && echo "Syntax OK"
cat hook.sh | less  # Manual review
```

**Option D: Log all hook invocations**

```python
import subprocess, logging

def run_hook(hook_path):
    logging.info(f"Running hook: {hook_path}")
    result = subprocess.run(["bash", hook_path], capture_output=True, timeout=30)
    logging.info(f"Hook exit code: {result.returncode}")
    logging.info(f"Hook stdout: {result.stdout}")
    logging.info(f"Hook stderr: {result.stderr}")
    return result
```

### 4. Trading System Security

#### Paper Trading Default

**Rule**: All trading plugins MUST default to `PAPER_TRADING=true`.

**Enforcement**:

```python
# qts/executor.py
if mode == "live" and not kwargs.get("enabled", False):
    raise RuntimeError("Live trading requires explicit approval. Pass enabled=True.")
```

#### Live Trading Approval

Live trading requires:

1. **Manual approval** in writing (email, Slack, ticket)
2. **Permissions manifest** with `"trading": "live"`
3. **Promotion gate passed**: 4-week paper tournament with green metrics
4. **Guarded rollout**: Start with tiny size (1% of paper size), strict caps

#### Secrets Management

**Do NOT**:
- Hardcode API keys in code or configs
- Print secrets to logs
- Store secrets in version control

**Do**:
- Use environment variables (`os.getenv("EXCHANGE_API_KEY")`)
- Use OS keychain (macOS Keychain, Windows Credential Manager)
- Use secret management tools (1Password CLI, Vault, AWS Secrets Manager)

**Example (Secure)**:

```python
import os

api_key = os.getenv("EXCHANGE_API_KEY")
if not api_key:
    raise ValueError("EXCHANGE_API_KEY not found. Set it via: export EXCHANGE_API_KEY=...")
```

### 5. CI/CD Security

The `.github/workflows/validate.yml` workflow enforces:

1. **Schema validation**: All `plugin.json` files must pass schema checks
2. **Pinned sources**: No `/main/` or `/master/` URLs allowed
3. **Integrity checks**: Remote sources must have sha256 hashes
4. **Linting**: Python files must pass basic syntax checks

**To bypass CI** (discouraged): Add `[skip ci]` to commit message (only for docs/README changes).

### 6. Audit Trail

All trading actions are logged as ACE bullets in `logs/bullets/`:

```json
{
  "id": "a1b2c3d4e5f6g7h8",
  "timestamp": "2025-01-15T12:00:00Z",
  "action": {
    "llm_decision": {"decision": "TRADE", ...},
    "risk_check": {"approved": true, "violations": []}
  },
  "result": {
    "execution_result": {"success": true, "fills": [...]}
  }
}
```

**Retention**: Keep bullets for ≥90 days for audit and retrieval.

### 7. Dependency Security

**Python dependencies**:
- Pin versions in `requirements.txt`
- Run `pip-audit` to check for known vulnerabilities
- Use `pipenv` or `poetry` for lockfiles

**Example**:

```bash
pip install pip-audit
pip-audit
```

**GitHub Dependabot**: Enable for automatic dependency updates and security alerts.

## Incident Response

### Reporting Security Issues

**Do NOT** open public GitHub issues for security vulnerabilities.

**Contact**: Email `security@<your-domain>` with:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment

**Response SLA**: We aim to acknowledge within 48 hours and patch within 7 days for critical issues.

### Emergency Actions

If a plugin is compromised:

1. **Immediate**: Disable plugin in marketplace (`marketplace.json`)
2. **Within 1 hour**: Notify all users via email/Slack
3. **Within 24 hours**: Publish patch or remove plugin
4. **Post-mortem**: Root cause analysis and prevention steps

### Trading System Kill Switch

**Trigger**: Any of:
- Unauthorized access detected
- Risk violations spiking
- Latency >2x SLO
- External alert (exchange, monitoring)

**Action**:

```bash
# Emergency flatten all positions
python -m qts.main --kill-switch --flatten-all
```

**Recovery**: Manual approval required to resume trading after kill switch.

## Plugin Review Checklist

Before adding a new plugin to the marketplace:

- [ ] All remote sources pinned to commit SHAs
- [ ] Integrity hashes (`sha256`) added to all remote sources
- [ ] Permissions declared in `plugin.json`
- [ ] No hardcoded secrets in code
- [ ] Hooks reviewed for unsafe commands (`rm -rf`, `curl | bash`, etc.)
- [ ] Trading plugins default to `PAPER_TRADING=true`
- [ ] Trading plugins have `riskConfigPath` in config
- [ ] README includes security notes and permissions
- [ ] CI validation passes (`python tools/validate_plugins.py`)

## Best Practices

1. **Principle of Least Privilege**: Request only the permissions you need
2. **Defense in Depth**: Assume remote sources can be compromised; validate outputs
3. **Fail Safe**: On error, default to NO_TRADE or halt execution
4. **Transparency**: Log all actions; make audit trails accessible
5. **Regular Reviews**: Re-validate plugins quarterly; check for dependency CVEs

## References

- [OWASP Secure Coding Practices](https://owasp.org/www-project-secure-coding-practices-quick-reference-guide/)
- [CWE Top 25 Software Weaknesses](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Last updated**: 2025-01-15
**Version**: 1.0
