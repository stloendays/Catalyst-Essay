"""Model routes for the extraction agent: the local API-YES gateway first, the advisor's OpenAI key once API-YES is
used up or unavailable (user, 2026-10-06).

Both routes use the streamed Responses API with store=false (API-YES forwards only that call intact). Keys are
handed straight to the client and never printed, logged or stored.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

API_YES_URL = "http://127.0.0.1:8788/v1"
API_YES_CONFIG = Path.home() / "AppData" / "Roaming" / "api-yes" / "api-yes.json"
HARNESS_AGENT = r"D:\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1\agent"
ROUTES = ("api-yes", "advisor-openai")
EXHAUSTED_WORDS = ("quota", "credit", "insufficient", "balance", "billing", "exhaust", "余额", "额度", "用完")


def api_yes_key(model: str) -> str | None:
    """The enabled API-YES proxy key whose model list contains `model`, or None if the gateway does not serve it."""
    try:
        proxies = json.loads(API_YES_CONFIG.read_text(encoding="utf-8"))["proxies"]
    except (OSError, ValueError, KeyError):
        return None
    for p in proxies:
        if not p.get("enabled"):
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
    if route == "api-yes":
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


class Router:
    """Hands out the current client and moves to the next route when the current one is exhausted."""

    def __init__(self, model: str, start: str = "api-yes"):
        self.model = model
        self.order = list(ROUTES[ROUTES.index(start):])
        self.client = None
        self._next()

    def _next(self) -> None:
        while self.order:
            route = self.order.pop(0)
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
                return fn(self.client)
            except Exception as e:  # noqa: BLE001 - classified below
                if not is_exhausted(e):
                    raise
                print(f"  route {self.client._route} exhausted ({type(e).__name__}: {str(e)[:160]}); switching",
                      flush=True)
                self._next()
