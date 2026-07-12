"""
instagram_upload.py - JETBOX v4 Instagram Infrastructure
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Instagram Graph API OAuth 2.0 entegrasyonu.
Åu an hedef: hesap baÄŸlama ve token yÃ¶netimi.
Post/Reels yÃ¼kleme: FAZA 3'te aktif olacak.

Gerekli kurulum:
  1. Meta Developer Console -> App oluÅŸtur
  2. Instagram Basic Display API veya Instagram Graph API ekle
  3. credentials.json dosyasÄ±na IG_APP_ID ve IG_APP_SECRET ekle
"""

import os
import json
import time
import logging
import threading
import webbrowser
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

logger = logging.getLogger(__name__)

CREDS_FILE    = Path(__file__).parent / "credentials.json"
IG_TOKEN_FILE = Path(__file__).parent / "instagram_token.json"

# OAuth endpoints
IG_AUTH_URL  = "https://api.instagram.com/oauth/authorize"
IG_TOKEN_URL = "https://api.instagram.com/oauth/access_token"
IG_LONG_LIVED_URL = "https://graph.instagram.com/access_token"
IG_GRAPH_URL = "https://graph.instagram.com"

# Scope: account info + media (posts iÃ§in content_publish gerekir, Faza 3'te)
IG_SCOPES = ["user_profile", "user_media"]


# â”€â”€â”€ CREDENTIALS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _load_creds():
    if not CREDS_FILE.exists():
        raise FileNotFoundError(
            f"credentials.json not found at {CREDS_FILE}\n"
            "Add IG_APP_ID and IG_APP_SECRET from Meta Developer Console."
        )
    with open(CREDS_FILE) as f:
        return json.load(f)


def _get_app_id():
    return _load_creds().get("IG_APP_ID", "")


def _get_app_secret():
    return _load_creds().get("IG_APP_SECRET", "")


# â”€â”€â”€ TOKEN MANAGEMENT â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def _save_token(token_data: dict):
    token_data["saved_at"] = int(time.time())
    with open(IG_TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    logger.info("Instagram token saved.")


def _load_token() -> dict | None:
    if not IG_TOKEN_FILE.exists():
        return None
    with open(IG_TOKEN_FILE) as f:
        return json.load(f)


def is_token_valid() -> bool:
    """Long-lived tokens expire in 60 days. We refresh if < 10 days remain."""
    token = _load_token()
    if not token:
        return False
    saved_at = token.get("saved_at", 0)
    expires_in = token.get("expires_in", 0)
    if not expires_in:
        # Short-lived token (1 hr) - needs long-lived exchange
        return False
    elapsed = time.time() - saved_at
    remaining = expires_in - elapsed
    return remaining > (10 * 24 * 3600)  # > 10 days


def get_access_token() -> str | None:
    token = _load_token()
    if token:
        return token.get("access_token")
    return None


def get_ig_user_id() -> str | None:
    token = _load_token()
    if token:
        return token.get("user_id")
    return None


# â”€â”€â”€ OAuth LOCAL CALLBACK SERVER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
_auth_code_holder = {"code": None, "error": None}
_server_ready     = threading.Event()


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = dict(urllib.parse.parse_qsl(parsed.query))
        if "code" in params:
            _auth_code_holder["code"] = params["code"]
            body = b"<html><body style='font-family:monospace;background:#06231D;color:#E3EF26;padding:40px'>" \
                   b"<h2>JETBOX: Instagram Connected</h2><p>You can close this window.</p></body></html>"
            self.send_response(200)
        else:
            _auth_code_holder["error"] = params.get("error_description", "unknown")
            body = b"<html><body style='font-family:monospace;background:#06231D;color:#e05555;padding:40px'>" \
                   b"<h2>Auth Failed</h2><p>Check error in console.</p></body></html>"
            self.send_response(400)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass  # suppress access logs


def _run_callback_server(port: int):
    server = HTTPServer(("localhost", port), _OAuthCallbackHandler)
    _server_ready.set()
    server.handle_request()  # handle ONE request then exit
    server.server_close()


# â”€â”€â”€ OAUTH FLOW â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def authenticate(redirect_port: int = 8891) -> dict:
    """
    Opens browser for Instagram OAuth.
    Returns token dict on success.
    Raises RuntimeError on failure.
    """
    app_id     = _get_app_id()
    app_secret = _get_app_secret()

    if not app_id or not app_secret:
        raise RuntimeError(
            "IG_APP_ID or IG_APP_SECRET missing in credentials.json"
        )

    redirect_uri = f"http://localhost:{redirect_port}/ig_callback"

    # Start callback server in background
    _auth_code_holder["code"] = None
    _auth_code_holder["error"] = None
    _server_ready.clear()
    t = threading.Thread(target=_run_callback_server, args=(redirect_port,), daemon=True)
    t.start()
    _server_ready.wait(timeout=3)

    # Build auth URL
    params = {
        "client_id":     app_id,
        "redirect_uri":  redirect_uri,
        "scope":         ",".join(IG_SCOPES),
        "response_type": "code",
    }
    auth_url = f"{IG_AUTH_URL}?{urllib.parse.urlencode(params)}"
    logger.info(f"Opening browser: {auth_url}")
    webbrowser.open(auth_url)

    # Wait for callback (max 120s)
    timeout = 120
    waited  = 0
    while _auth_code_holder["code"] is None and _auth_code_holder["error"] is None:
        time.sleep(0.5)
        waited += 0.5
        if waited >= timeout:
            raise RuntimeError("OAuth timeout - browser authorization not completed.")

    if _auth_code_holder["error"]:
        raise RuntimeError(f"Instagram OAuth error: {_auth_code_holder['error']}")

    code = _auth_code_holder["code"]

    # Exchange code for short-lived token
    token_data = _exchange_code_for_token(code, app_id, app_secret, redirect_uri)

    # Exchange for long-lived token (60 days)
    long_token = _exchange_for_long_lived_token(
        token_data["access_token"], app_id, app_secret
    )
    long_token["user_id"] = token_data.get("user_id")

    _save_token(long_token)
    return long_token


def _exchange_code_for_token(code, app_id, app_secret, redirect_uri) -> dict:
    data = urllib.parse.urlencode({
        "client_id":     app_id,
        "client_secret": app_secret,
        "grant_type":    "authorization_code",
        "redirect_uri":  redirect_uri,
        "code":          code,
    }).encode()
    req = urllib.request.Request(IG_TOKEN_URL, data=data, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def _exchange_for_long_lived_token(short_token, app_id, app_secret) -> dict:
    params = urllib.parse.urlencode({
        "grant_type":        "ig_exchange_token",
        "client_secret":     app_secret,
        "access_token":      short_token,
    })
    url = f"{IG_LONG_LIVED_URL}?{params}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read())


def refresh_token() -> dict:
    """Refresh long-lived token before it expires."""
    token = get_access_token()
    if not token:
        raise RuntimeError("No Instagram token to refresh. Run authenticate() first.")
    params = urllib.parse.urlencode({
        "grant_type":   "ig_refresh_token",
        "access_token": token,
    })
    url = f"{IG_LONG_LIVED_URL}?{params}"
    with urllib.request.urlopen(url) as resp:
        new_token = json.loads(resp.read())
    token_data = _load_token() or {}
    token_data.update(new_token)
    _save_token(token_data)
    return new_token


# â”€â”€â”€ ACCOUNT INFO â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def get_account_info() -> dict:
    """Returns IG account info for the connected account."""
    access_token = get_access_token()
    if not access_token:
        return {"success": False, "error": "Not authenticated"}
    try:
        params = urllib.parse.urlencode({
            "fields":       "id,username,account_type,media_count",
            "access_token": access_token,
        })
        url = f"{IG_GRAPH_URL}/me?{params}"
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read())
        return {"success": True, **data}
    except Exception as e:
        logger.error(f"IG get_account_info error: {e}")
        return {"success": False, "error": str(e)}


# â”€â”€â”€ STATUS (used by Flask endpoint) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def get_status() -> dict:
    """Returns current Instagram connection status."""
    token = _load_token()
    if not token:
        return {
            "connected":     False,
            "authenticated": False,
            "status":        "NOT_CONNECTED",
            "message":       "Run Instagram OAuth to connect",
        }

    valid = is_token_valid()
    user_id = token.get("user_id")

    if not valid:
        return {
            "connected":     True,
            "authenticated": False,
            "status":        "TOKEN_EXPIRED",
            "user_id":       user_id,
            "message":       "Token expired - re-authenticate",
        }

    return {
        "connected":     True,
        "authenticated": True,
        "status":        "OK",
        "user_id":       user_id,
        "expires_in":    token.get("expires_in"),
        "saved_at":      token.get("saved_at"),
        "message":       "Connected and authenticated",
        "faza":          "FAZA 3 - post/reels upload coming soon",
    }


# â”€â”€â”€ UPLOAD STUBS (FAZA 3) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
def upload_reel(video_path: str, caption: str) -> dict:
    """
    FAZA 3: Upload a Reel to Instagram.
    Requires Instagram Graph API content_publish scope.
    """
    raise NotImplementedError(
        "Instagram Reels upload is scheduled for FAZA 3. "
        "Infrastructure (OAuth, token management) is ready."
    )


def upload_image_post(image_path: str, caption: str) -> dict:
    """FAZA 3: Upload an image post."""
    raise NotImplementedError("Instagram image upload - FAZA 3.")


# â”€â”€â”€ CLI HELPER â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        print("\nJETBOX - Instagram OAuth Setup")
        print("=" * 40)
        try:
            result = authenticate()
            info   = get_account_info()
            print(f"\nâœ“ Connected: @{info.get('username', 'unknown')}")
            print(f"  Account type: {info.get('account_type')}")
            print(f"  Media count:  {info.get('media_count')}")
            print(f"  Token saved to: {IG_TOKEN_FILE}")
        except Exception as e:
            print(f"\nâœ- Error: {e}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--status":
        print(json.dumps(get_status(), indent=2))
    else:
        print("Usage:")
        print("  python instagram_upload.py --setup   # OAuth flow")
        print("  python instagram_upload.py --status  # Check connection")

