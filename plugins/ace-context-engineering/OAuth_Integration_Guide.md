# ACE OAuth Integration Guide

## Overview

The ACE (Autonomous Coding Engine) context engineering system has been upgraded from CLI-based skill invocation to a robust OAuth2-backed architecture. This upgrade provides secure, reliable API access to Claude through an OAuth gateway while maintaining backward compatibility through fallback mechanisms.

## Architecture Components

### 1. OAuth Client Stack (`anthropic_oauth_client.py`)

The OAuth implementation consists of three main components:

#### NgrokManager
- Manages ngrok subprocess for secure HTTPS tunneling
- Exposes localhost OAuth callback endpoint to the internet
- Requirements:
  - `ngrok` binary in PATH
  - `NGROK_AUTHTOKEN` environment variable set

#### PKCETokenProviderWithNgrok
- Implements OAuth2 Authorization Code flow with PKCE
- Handles:
  - Interactive browser-based authentication
  - Token caching and persistence
  - Automatic token refresh (when expired)
- Security features:
  - PKCE (Proof Key for Code Exchange) for enhanced security
  - State parameter validation
  - Token expiration handling

#### ClaudeOAuth2LLMClient
- Anthropic Messages API client using OAuth Bearer tokens
- Gateway expectation: Translates `Authorization: Bearer` → `x-api-key`
- Features:
  - Configurable anthropic-version header
  - System prompt support
  - Tool/function calling support
  - Session management

### 2. Skill Invocation System (`claude_code_skill_invoker.py`)

#### Key Features
- **Lazy client initialization**: OAuth client created once, reused across invocations
- **Retry logic**: Configurable retry for timeout failures (2 retries for `curate-delta`)
- **JSON enforcement**: Two-phase approach for skills requiring JSON responses
- **Skill context loading**: Reads SKILL.md files for instructions
- **Fallback implementations**: Template-based code generation if OAuth fails

#### Skill Configuration
```python
max_tokens_by_skill = {
    "generate-appworld-code": 2048,
    "curate-delta": 1024,
    "reflect-appworld-failure": 768,
    # default: 1024
}
```

### 3. ACE Code Generator Hardening (`ace_code_generator.py`)

#### Structured Prompt Payload
```json
{
    "instruction": "task description",
    "apps": ["spotify", "venmo"],
    "strategies": ["learned patterns"],
    "bullets": [
        {
            "id": "bullet_id",
            "title": "pattern name",
            "content": "detailed pattern",
            "tags": ["app.spotify"],
            "confidence": 0.85
        }
    ],
    "environment": {
        "mode": "appworld_offline",
        "credentials": {
            "username": "user@example.com",
            "password": "password"
        },
        "requirements": [
            "Return ONLY executable Python code.",
            "Do not request user permission.",
            "Always call apis.supervisor.complete_task().",
            "Handle errors with try/except."
        ]
    }
}
```

#### Code Validation Pipeline
1. **Initial generation**: Send structured prompt to skill
2. **Code extraction**: Handle markdown fences, JSON wrappers
3. **Validation checks**:
   - Minimum code length (20 chars)
   - Contains `apis.` calls
   - Contains `complete_task` call
4. **Reinforcement**: If non-code response, retry with stricter directives
5. **Bullet usage validation**: Track which learned patterns were applied

### 4. AppWorld Loader Enhancement (`appworld_loader.py`)

- **App detection**: Recognizes Spotify tasks explicitly
- **Supported apps**: spotify, venmo, gmail, slack, contacts, calendar, phone, messaging, email, notes, reminders
- **Fallback**: Returns `['general']` if no specific app detected

## Environment Configuration

### Required OAuth Variables
```bash
# OAuth Gateway Configuration
export ACE_OAUTH_AUTH_URL="https://your-gateway.com/oauth/authorize"
export ACE_OAUTH_TOKEN_URL="https://your-gateway.com/oauth/token"
export ACE_OAUTH_CLIENT_ID="your-client-id"
export ACE_OAUTH_SCOPE="anthropic:messages:write"
export ACE_OAUTH_BASE_URL="https://your-gateway.com"  # Gateway fronting Anthropic

# ngrok Configuration
export NGROK_AUTHTOKEN="your-ngrok-token"
```

### Optional OAuth Variables
```bash
# Optional OAuth Settings
export ACE_OAUTH_AUDIENCE="https://api.anthropic.com"  # If required by gateway
export ACE_OAUTH_REDIRECT_PORT="8765"                  # Default: 8765
export ACE_OAUTH_NGROK_REGION="us"                     # Default: us
export ACE_OAUTH_MODEL="claude-3-5-sonnet-20241022"    # Default model
export ACE_OAUTH_TOKEN_FILE="~/.config/ace_oauth_token.json"  # Token cache location
export ACE_OAUTH_VERSION="2023-06-01"                  # Anthropic API version
```

## OAuth Gateway Requirements

Your OAuth gateway must:

1. **Support OAuth2 Authorization Code flow with PKCE**
   - Handle `code_challenge` and `code_challenge_method=S256`
   - Validate `code_verifier` during token exchange

2. **Translate authentication headers**
   - Convert `Authorization: Bearer <token>` → `x-api-key: <anthropic-key>`
   - Forward requests to Anthropic's API

3. **Support Anthropic Messages API**
   - Endpoint: `/v1/messages`
   - Headers: `anthropic-version`, `content-type: application/json`

## Migration Path

### From CLI to OAuth

1. **Phase 1: Environment Setup**
   ```bash
   # Install ngrok
   brew install ngrok  # macOS
   # or download from https://ngrok.com/download

   # Set up ngrok authentication
   ngrok config add-authtoken YOUR_NGROK_TOKEN
   ```

2. **Phase 2: Gateway Configuration**
   - Deploy or configure your OAuth gateway
   - Ensure it meets the requirements above
   - Test with curl:
   ```bash
   # Test token endpoint
   curl -X POST https://your-gateway.com/oauth/token \
     -d "grant_type=authorization_code" \
     -d "client_id=your-client-id" \
     -d "code=test-code"
   ```

3. **Phase 3: ACE Configuration**
   ```bash
   # Export all required OAuth variables
   source oauth_config.env

   # Test the setup
   MAX_SAMPLES=1 MAX_EPOCHS=1 python -u \
     plugins/ace-context-engineering/benchmarks/run_offline_adaptation.py
   ```

### Fallback Behavior

If OAuth environment is not configured:
1. System logs missing variables
2. Falls back to template-based implementation
3. Returns functional (but non-LLM) code

Example fallback log:
```
Missing required OAuth environment variables: ACE_OAUTH_AUTH_URL, ACE_OAUTH_TOKEN_URL
Falling back to template implementation
```

## Testing OAuth Integration

### 1. Unit Test
```python
from anthropic_oauth_client import build_oauth_client_from_env

# This will trigger the OAuth flow
client = build_oauth_client_from_env()

# Test a simple completion
response = client.complete(
    "Hello, Claude!",
    system="You are a helpful assistant.",
    max_tokens=100
)
print(response.text)
```

### 2. Skill Test
```python
from claude_code_skill_invoker import invoke_skill

# Test generate-appworld-code skill
code = invoke_skill(
    "generate-appworld-code",
    '{"instruction": "Find my most played song on Spotify", "apps": ["spotify"]}'
)
print(code)
```

### 3. End-to-End Test
```bash
# Run single sample through full pipeline
MAX_SAMPLES=1 MAX_EPOCHS=1 python -u \
  plugins/ace-context-engineering/benchmarks/run_offline_adaptation.py
```

## Security Considerations

1. **Token Storage**
   - Tokens cached in `~/.config/ace_oauth_token.json` by default
   - File permissions should be 600 (user read/write only)
   - Consider using OS keychain for production

2. **ngrok Security**
   - Uses authenticated tunnels (requires NGROK_AUTHTOKEN)
   - Callback only accepts expected OAuth parameters
   - Server closes after single callback

3. **PKCE Protection**
   - 64-character random code verifier
   - SHA256 challenge prevents code interception attacks
   - State parameter prevents CSRF attacks

## Troubleshooting

### Common Issues

1. **ngrok not found**
   ```
   RuntimeError: Failed to obtain ngrok public URL within timeout
   ```
   Solution: Install ngrok and ensure it's in PATH

2. **Missing OAuth variables**
   ```
   RuntimeError: Missing required OAuth environment variables: ACE_OAUTH_AUTH_URL, ...
   ```
   Solution: Export all required ACE_OAUTH_* variables

3. **Token endpoint error**
   ```
   RuntimeError: Token endpoint error: HTTP 401 – Unauthorized
   ```
   Solution: Verify client_id and gateway configuration

4. **JSON enforcement failure**
   ```
   RuntimeError: Skill curate-delta did not return valid JSON after reinforcement
   ```
   Solution: Check skill SKILL.md instructions for JSON format requirements

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Optimizations

1. **Client caching**: Single OAuth client instance reused across invocations
2. **Token persistence**: Avoids repeated OAuth flows
3. **Selective retries**: Only retry on timeout errors
4. **Lazy initialization**: OAuth client created only when needed

## Future Enhancements

1. **Refresh token support**: Automatic token refresh before expiration
2. **Multi-gateway support**: Route different skills through different gateways
3. **Metrics collection**: Track API usage, latency, success rates
4. **Circuit breaker**: Automatic fallback after N consecutive failures
5. **Batch processing**: Send multiple skill invocations in parallel

## Conclusion

The OAuth integration provides a production-ready, secure path for ACE to interact with Claude's API while maintaining the flexibility and reliability needed for autonomous code generation. The system gracefully handles failures, provides clear debugging information, and maintains backward compatibility through intelligent fallbacks.