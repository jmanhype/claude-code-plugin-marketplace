"""
Anthropic OAuth2 client with ngrok-assisted PKCE callback.

Provides:
    - NgrokManager: launches ngrok and discovers the public HTTPS URL
    - PKCETokenProviderWithNgrok: performs OAuth2 authorization-code flow
    - ClaudeOAuth2LLMClient: calls Anthropic-compatible /v1/messages endpoint
"""

from __future__ import annotations

import base64
import hashlib
import http.server
import json
import os
import queue
import secrets
import string
import subprocess
import threading
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import requests


# --------------------------------------------------------------------------------------
# Core response container
# --------------------------------------------------------------------------------------


@dataclass
class LLMResponse:
    text: str
    raw: Optional[Dict[str, Any]] = None


class LLMClient:
    def __init__(self, model: Optional[str] = None) -> None:
        self.model = model

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        raise NotImplementedError


# --------------------------------------------------------------------------------------
# ngrok subprocess management
# --------------------------------------------------------------------------------------


class NgrokManager:
    """
    Start ngrok as a subprocess and expose the HTTPS tunnel URL.

    Requirements:
        * ngrok binary in PATH
        * NGROK_AUTHTOKEN set (for authenticated plans)
    """

    def __init__(self, local_port: int, region: str = "us") -> None:
        self._local_port = local_port
        self._region = region
        self._proc: Optional[subprocess.Popen[str]] = None
        self._public_url: Optional[str] = None

    def start(self, timeout: float = 15.0) -> str:
        if self._proc and self._proc.poll() is None:
            return self._public_url or self._discover_public_url(timeout=timeout)

        self._proc = subprocess.Popen(
            [
                "ngrok",
                "http",
                "--region",
                self._region,
                "--log",
                "stdout",
                str(self._local_port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        return self._discover_public_url(timeout=timeout)

    def _discover_public_url(self, timeout: float = 15.0) -> str:
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
                resp.raise_for_status()
                data = resp.json()
                for tunnel in data.get("tunnels", []):
                    if tunnel.get("proto") == "https":
                        self._public_url = tunnel["public_url"]
                        return self._public_url
            except Exception:
                pass
            time.sleep(0.3)

        raise RuntimeError("Failed to obtain ngrok public URL within timeout")

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._proc = None
        self._public_url = None


# --------------------------------------------------------------------------------------
# OAuth2 + PKCE flow
# --------------------------------------------------------------------------------------


@dataclass
class OAuth2Token:
    access_token: str
    expires_at: float
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"

    @property
    def is_expired(self) -> bool:
        # refresh slightly before expiry to avoid race conditions
        return time.time() >= (self.expires_at - 30)


class OAuth2TokenProvider:
    def get_token(self) -> OAuth2Token:
        raise NotImplementedError


class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    """Single-use handler that captures OAuth2 redirect parameters."""

    queue: "queue.Queue[Dict[str, str]]" = queue.Queue()

    def do_GET(self) -> None:  # noqa: N802 - HTTP verb naming
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = dict(urllib.parse.parse_qsl(parsed.query))
        _CallbackHandler.queue.put(params)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Authentication complete. You may close this tab.")

    def log_message(self, *args: Any, **kwargs: Any) -> None:  # silence default logging
        return


class PKCETokenProviderWithNgrok(OAuth2TokenProvider):
    """
    Perform OAuth2 Authorization Code (PKCE) flow using a localhost callback
    tunneled through ngrok.
    """

    def __init__(
        self,
        *,
        auth_url: str,
        token_url: str,
        client_id: str,
        scope: str,
        redirect_port: int = 8765,
        ngrok_region: str = "us",
        audience: Optional[str] = None,
        token_file: Optional[Path] = None,
        extra_token_params: Optional[Dict[str, str]] = None,
    ) -> None:
        self.auth_url = auth_url
        self.token_url = token_url
        self.client_id = client_id
        self.scope = scope
        self.redirect_port = redirect_port
        self.audience = audience
        self.extra_token_params = extra_token_params or {}

        self._ngrok = NgrokManager(local_port=redirect_port, region=ngrok_region)
        self._cached: Optional[OAuth2Token] = None

        self._token_file = token_file
        if isinstance(token_file, str):
            self._token_file = Path(token_file)
        if self._token_file:
            self._token_file.parent.mkdir(parents=True, exist_ok=True)

    # Utilities -----------------------------------------------------------------

    @staticmethod
    def _random_string(length: int = 64) -> str:
        alphabet = string.ascii_letters + string.digits + "-._~"
        return "".join(secrets.choice(alphabet) for _ in range(length))

    def _load_from_disk(self) -> Optional[OAuth2Token]:
        if not self._token_file or not self._token_file.exists():
            return None
        try:
            data = json.loads(self._token_file.read_text())
            token = OAuth2Token(
                access_token=data["access_token"],
                expires_at=data["expires_at"],
                refresh_token=data.get("refresh_token"),
                token_type=data.get("token_type", "Bearer"),
            )
            if token.is_expired:
                return None
            return token
        except Exception:
            return None

    def _save_to_disk(self, token: OAuth2Token) -> None:
        if not self._token_file:
            return
        payload = {
            "access_token": token.access_token,
            "expires_at": token.expires_at,
            "refresh_token": token.refresh_token,
            "token_type": token.token_type,
        }
        self._token_file.write_text(json.dumps(payload))

    # Public API ----------------------------------------------------------------

    def get_token(self) -> OAuth2Token:
        if self._cached and not self._cached.is_expired:
            return self._cached

        disk_token = self._load_from_disk()
        if disk_token:
            self._cached = disk_token
            return disk_token

        public_callback = self._ngrok.start()
        try:
            token = self._run_interactive_flow(public_callback + "/callback")
        finally:
            self._ngrok.stop()

        self._cached = token
        self._save_to_disk(token)
        return token

    # Internal ------------------------------------------------------------------

    def _run_interactive_flow(self, redirect_uri: str) -> OAuth2Token:
        code_verifier = self._random_string(64)
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        state = self._random_string(32)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": self.scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        if self.audience:
            params["audience"] = self.audience

        auth_uri = f"{self.auth_url}?{urllib.parse.urlencode(params)}"

        # Start local HTTP server to capture redirect
        server = http.server.HTTPServer(("127.0.0.1", self.redirect_port), _CallbackHandler)
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()

        import webbrowser

        webbrowser.open(auth_uri)

        try:
            payload = _CallbackHandler.queue.get(timeout=300)
        finally:
            server.server_close()

        if payload.get("state") != state or "code" not in payload:
            raise RuntimeError("OAuth2 state mismatch or missing authorization code")

        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "code": payload["code"],
            "redirect_uri": redirect_uri,
            "code_verifier": code_verifier,
        }
        data.update(self.extra_token_params)

        response = requests.post(self.token_url, data=data, timeout=30)
        try:
            response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(
                f"Token endpoint error: HTTP {response.status_code} – {response.text[:400]}"
            ) from exc

        token_payload = response.json()
        expires_in = float(token_payload.get("expires_in", 3600))
        return OAuth2Token(
            access_token=token_payload["access_token"],
            expires_at=time.time() + expires_in,
            refresh_token=token_payload.get("refresh_token"),
            token_type=token_payload.get("token_type", "Bearer"),
        )


# --------------------------------------------------------------------------------------
# Anthropic Messages client (Bearer token, OAuth gateway)
# --------------------------------------------------------------------------------------


class ClaudeOAuth2LLMClient(LLMClient):
    """
    Perform POST {base_url}/v1/messages using OAuth2 Bearer token.
    The gateway in front of Anthropic must translate Authorization → x-api-key.
    """

    def __init__(
        self,
        *,
        model: str,
        token_provider: OAuth2TokenProvider,
        base_url: str,
        anthropic_version: str = "2023-06-01",
        default_max_tokens: int = 2048,
        session_factory: Optional[Callable[[], requests.Session]] = None,
    ) -> None:
        super().__init__(model=model)
        self._provider = token_provider
        self._base_url = base_url.rstrip("/")
        self._anthropic_version = anthropic_version
        self._default_max_tokens = default_max_tokens
        self._session_factory = session_factory or requests.Session

    def complete(self, prompt: str, **kwargs: Any) -> LLMResponse:
        session = self._session_factory()
        token = self._provider.get_token()

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "max_tokens": int(kwargs.get("max_tokens", self._default_max_tokens)),
        }

        system_prompt = kwargs.get("system")
        if system_prompt:
            # Anthropic API accepts top-level system string
            payload["system"] = system_prompt

        for key in ("temperature", "top_p", "stop_sequences", "metadata", "tools"):
            if key in kwargs and kwargs[key] is not None:
                payload[key] = kwargs[key]

        headers = {
            "Authorization": f"{token.token_type} {token.access_token}",
            "anthropic-version": self._anthropic_version,
            "content-type": "application/json",
        }
        extra_headers = kwargs.get("extra_headers")
        if isinstance(extra_headers, dict):
            headers.update(extra_headers)

        url = f"{self._base_url}/v1/messages"
        response = session.post(url, headers=headers, json=payload, timeout=60)
        try:
            response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(
                f"Claude call failed: HTTP {response.status_code} – {response.text[:600]}"
            ) from exc

        data = response.json()
        return LLMResponse(text=_extract_claude_text(data), raw=data)


def _extract_claude_text(data: Dict[str, Any]) -> str:
    content = data.get("content") or []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    return text.strip()
        return json.dumps(content)

    if isinstance(content, str):
        return content.strip()

    return ""


# --------------------------------------------------------------------------------------
# Convenience factory
# --------------------------------------------------------------------------------------


def build_oauth_client_from_env() -> ClaudeOAuth2LLMClient:
    """
    Construct ClaudeOAuth2LLMClient using ACE_* environment variables.

    Required env vars:
        ACE_OAUTH_AUTH_URL
        ACE_OAUTH_TOKEN_URL
        ACE_OAUTH_CLIENT_ID
        ACE_OAUTH_SCOPE
        ACE_OAUTH_BASE_URL   (gateway fronting Anthropic)

    Optional:
        ACE_OAUTH_AUDIENCE
        ACE_OAUTH_REDIRECT_PORT (default 8765)
        ACE_OAUTH_NGROK_REGION  (default 'us')
        ACE_OAUTH_MODEL         (default 'claude-3-5-sonnet-20241022')
        ACE_OAUTH_TOKEN_FILE    (default ~/.config/ace_oauth_token.json)
    """

    required_keys = [
        "ACE_OAUTH_AUTH_URL",
        "ACE_OAUTH_TOKEN_URL",
        "ACE_OAUTH_CLIENT_ID",
        "ACE_OAUTH_SCOPE",
        "ACE_OAUTH_BASE_URL",
    ]

    missing = [key for key in required_keys if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing required OAuth environment variables: {', '.join(missing)}")

    redirect_port = int(os.getenv("ACE_OAUTH_REDIRECT_PORT", "8765"))
    ngrok_region = os.getenv("ACE_OAUTH_NGROK_REGION", "us")
    token_file = os.getenv(
        "ACE_OAUTH_TOKEN_FILE",
        os.path.join(Path.home(), ".config", "ace_oauth_token.json"),
    )

    provider = PKCETokenProviderWithNgrok(
        auth_url=os.environ["ACE_OAUTH_AUTH_URL"],
        token_url=os.environ["ACE_OAUTH_TOKEN_URL"],
        client_id=os.environ["ACE_OAUTH_CLIENT_ID"],
        scope=os.environ["ACE_OAUTH_SCOPE"],
        redirect_port=redirect_port,
        ngrok_region=ngrok_region,
        audience=os.getenv("ACE_OAUTH_AUDIENCE"),
        token_file=Path(token_file),
    )

    model = os.getenv("ACE_OAUTH_MODEL", "claude-3-5-sonnet-20241022")
    anthropic_version = os.getenv("ACE_OAUTH_VERSION", "2023-06-01")

    client = ClaudeOAuth2LLMClient(
        model=model,
        token_provider=provider,
        base_url=os.environ["ACE_OAUTH_BASE_URL"],
        anthropic_version=anthropic_version,
    )
    return client

