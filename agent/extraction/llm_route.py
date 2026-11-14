"""Model routes for the extraction agent: the local API-YES gateway first, the advisor's OpenAI key once API-YES is
used up or unavailable (user, 2026-10-06).

Both routes use the streamed Responses API with store=false (API-YES forwards only that call intact). Keys are
handed straight to the client and never printed, logged or stored.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path

API_YES_URL = "http://127.0.0.1:8788/v1"
API_YES_CONFIG = Path.home() / "AppData" / "Roaming" / "api-yes" / "api-yes.json"
HARNESS_AGENT = os.path.join(os.environ.get("NH3_HARNESS", r"D:\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1"), "agent")
PERSONAL_CREDENTIAL = "69d4b1ee-f6fe-4fe3-ac95-75e3f539fbfa"  # API-YES credential "GPT-个人" (user, 2026-11-13: use gpt-5.6 from it)
XIEXIU_CREDENTIAL = "4626141b-2c5d-4933-8fef-f38fec7160af"   # API-YES credential "邪修gpt" (user, 2026-11-11)
CREDENTIAL_ROUTES = {"api-yes-personal": PERSONAL_CREDENTIAL, "api-yes-xiexiu": XIEXIU_CREDENTIAL}
ALL_ROUTES = ("api-yes-personal", "api-yes-xiexiu", "api-yes", "advisor-openai")
# Route policy file (user 2026-11-15): when present it overrides LLM_ROUTES and sets the fallback limits, so builds started
# by a running launcher pick up a new policy. {"routes": [...], "advisor_cap_usd": 40, "return_after_s": 18000}
POLICY_FILE = Path(os.environ.get("LLM_POLICY_FILE", r"D:\agent_runs\_route_policy.json"))
SPEND_FILE = Path(os.environ.get("LLM_SPEND_FILE", r"D:\agent_runs\_route_spend.json"))
try:
    POLICY = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
except (OSError, ValueError):
    POLICY = {}
# LLM_ROUTES="api-yes-personal" limits every call to the listed routes (user 2026-11-14: test on the personal account quota only)
ROUTES = (tuple(r for r in POLICY.get("routes", []) if r in ALL_ROUTES)
          or tuple(r for r in os.environ.get("LLM_ROUTES", "").split(",") if r in ALL_ROUTES) or ALL_ROUTES)
# Spend on the advisor key across all builds, gpt-5.5 list-price basis like the run ledger (cached input counted at full
# price, so the cap is conservative); the first route is retried return_after_s after it was exhausted.
ADVISOR_CAP_USD = float(POLICY.get("advisor_cap_usd") or os.environ.get("LLM_ADVISOR_CAP_USD") or 0)
RETURN_AFTER_S = float(POLICY.get("return_after_s") or os.environ.get("LLM_RETURN_AFTER_S") or 0)
PRICE_PER_M = (5.0, 30.0)
# LLM_WAIT_ON_LIMIT=1: when the last route reports a usage limit with a reset time, wait for the reset instead of failing
WAIT_ON_LIMIT = os.environ.get("LLM_WAIT_ON_LIMIT") == "1"
MAX_WAIT_S = 6 * 3600
DEFAULT_MODEL = "gpt-5.6-sol"   # served by GPT-个人 (ChatGPT account: list input only); 邪修gpt serves plain "gpt-5.6"
EXHAUSTED_WORDS = ("quota", "credit", "insufficient", "balance", "billing", "exhaust", "not supported", "余额", "额度", "用完")


def api_yes_key(model: str, credential: str | None = None) -> str | None:
    """The enabled API-YES proxy key whose model list contains `model` (optionally only proxies of one credential),
    or None if the gateway does not serve it."""
    try:
        proxies = json.loads(API_YES_CONFIG.read_text(encoding="utf-8"))["proxies"]
    except (OSError, ValueError, KeyError):
        return None
    for p in proxies:
        if not p.get("enabled") or (credential and p.get("credentialId") != credential):
            continue
        req = urllib.request.Request(API_YES_URL + "/models", headers={"Authorization": "Bearer " + p["key"]})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                if model in {m["id"] for m in json.load(r).get("data", [])}:
                    return p["key"]
        except OSError:
            continue
    return None


def make_client(route: str, model: str):
    """An OpenAI client for `route`, or None if that route cannot serve `model` right now."""
    import openai
    if route in CREDENTIAL_ROUTES:
        key = api_yes_key(model, CREDENTIAL_ROUTES[route])
        if key is None:
            return None
        client = openai.OpenAI(api_key=key, base_url=API_YES_URL, timeout=1800)
    elif route == "api-yes":
        key = api_yes_key(model)
        if key is None:
            return None
        client = openai.OpenAI(api_key=key, base_url=API_YES_URL, timeout=1800)
    elif route == "advisor-openai":
        sys.path.insert(0, HARNESS_AGENT)
        from llm_client import resolve_api_key
        key = resolve_api_key()
        if not key:
            return None
        client = openai.OpenAI(api_key=key, timeout=1800)
    else:
        raise ValueError(route)
    client._route = route
    return client


def is_exhausted(err: Exception) -> bool:
    """True when the route is used up or unreachable (switch route), False for errors of the request itself."""
    import openai
    if isinstance(err, (openai.APIConnectionError, openai.RateLimitError, openai.PermissionDeniedError,
                        openai.AuthenticationError)):
        return True
    status = getattr(err, "status_code", None)
    text = str(err).lower()
    return status in (402, 429, 503) or any(w in text for w in EXHAUSTED_WORDS)


def wait_for_reset(err) -> bool:
    """With LLM_WAIT_ON_LIMIT=1: if err is a usage limit carrying a reset time within MAX_WAIT_S, sleep until just after the
    reset and return True (the caller retries the same route); otherwise return False."""
    if not WAIT_ON_LIMIT:
        return False
    import re
    import time
    m = re.search(r"resets_at['\"]?:\s*(\d{9,})", str(err))
    wait = int(m.group(1)) - time.time() + 60 if m else None
    if wait is None or not 0 < wait <= MAX_WAIT_S:
        return False
    print(f"  usage limit reached; waiting {wait / 60:.0f} min for the reset", flush=True)
    time.sleep(wait)
    return True


def _spend() -> dict:
    try:
        return json.loads(SPEND_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _spend_write(d: dict) -> None:
    SPEND_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SPEND_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(d, indent=1), encoding="utf-8")
    os.replace(tmp, SPEND_FILE)


class Router:
    """Hands out the current client and moves to the next route when the current one is exhausted. With a policy
    (advisor_cap_usd, return_after_s) the advisor key is a capped fallback and the first route is retried after a pause;
    the exhaustion time and the advisor spend are shared by all builds through SPEND_FILE."""

    def __init__(self, model: str, start: str = ROUTES[0]):
        self.model = model
        self.first = start
        self.order = list(ROUTES[ROUTES.index(start):])
        self.client = None
        since = _spend().get("first_exhausted_at")
        if RETURN_AFTER_S and since and time.time() - since < RETURN_AFTER_S and len(self.order) > 1:
            print(f"  route {start} exhausted {(time.time() - since) / 60:.0f} min ago; starting on the fallback", flush=True)
            self.order.pop(0)
        self._next()

    def _first_exhausted(self) -> None:
        d = _spend()
        if not (d.get("first_exhausted_at") and time.time() - d["first_exhausted_at"] < max(RETURN_AFTER_S, 1)):
            d["first_exhausted_at"] = time.time()
            _spend_write(d)

    def before_call(self) -> None:
        """Return to the first route once return_after_s has passed; wait for that point when the advisor cap is used up."""
        if not self.client or self.client._route == self.first or not RETURN_AFTER_S:
            return
        since = _spend().get("first_exhausted_at") or 0
        capped = self.client._route == "advisor-openai" and ADVISOR_CAP_USD and _spend().get("advisor_usd", 0) >= ADVISOR_CAP_USD
        if capped and time.time() - since < RETURN_AFTER_S:
            wait = since + RETURN_AFTER_S - time.time() + 30
            print(f"  advisor cap {ADVISOR_CAP_USD:.0f} USD reached; waiting {wait / 60:.0f} min for {self.first}", flush=True)
            time.sleep(wait)
        if time.time() - since >= RETURN_AFTER_S:
            client = make_client(self.first, self.model)
            if client is not None:
                self.order.insert(0, self.client._route)
                self.client = client
                d = _spend()
                d.pop("first_exhausted_at", None)
                _spend_write(d)
                print(f"  route: back to {self.first}", flush=True)

    def account(self, usage) -> None:
        """Add one response's tokens to the shared advisor spend (list-price basis)."""
        if not self.client or self.client._route != "advisor-openai" or usage is None:
            return
        tin = getattr(usage, "input_tokens", None) or getattr(usage, "prompt_tokens", 0) or 0
        tout = getattr(usage, "output_tokens", None) or getattr(usage, "completion_tokens", 0) or 0
        d = _spend()
        d["advisor_usd"] = round(d.get("advisor_usd", 0) + (tin * PRICE_PER_M[0] + tout * PRICE_PER_M[1]) / 1e6, 4)
        _spend_write(d)

    def _next(self) -> None:
        if self.client is not None and self.client._route == self.first:
            self._first_exhausted()
        while self.order:
            route = self.order.pop(0)
            if route == "advisor-openai" and ADVISOR_CAP_USD and _spend().get("advisor_usd", 0) >= ADVISOR_CAP_USD \
                    and not RETURN_AFTER_S:
                print(f"  route advisor-openai skipped: cap {ADVISOR_CAP_USD:.0f} USD used", flush=True)
                continue
            client = make_client(route, self.model)
            if client is not None:
                self.client = client
                print(f"  route: {route}", flush=True)
                return
            print(f"  route {route} unavailable for {self.model}", flush=True)
        raise SystemExit(f"no route serves {self.model}: API-YES and the advisor key are both unavailable")

    def call(self, fn):
        """fn(client) -> result; retried on the next route when the current route is exhausted."""
        while True:
            try:
                self.before_call()
                result = fn(self.client)
                self.account(getattr(result, "usage", None))
                return result
            except Exception as e:  # noqa: BLE001 - classified below
                if not is_exhausted(e):
                    raise
                if not self.order and wait_for_reset(e):
                    continue
                print(f"  route {self.client._route} exhausted ({type(e).__name__}: {str(e)[:160]}); switching",
                      flush=True)
                self._next()
