import os, sys, json, time, tempfile, types
"""Route policy (user 2026-11-15): personal quota first, advisor key as a fallback capped at 40 USD in total, back to the
personal quota 5 h after it ran out. Offline, fake clients."""
d = tempfile.mkdtemp()
os.environ["LLM_POLICY_FILE"] = d + "/p.json"; os.environ["LLM_SPEND_FILE"] = d + "/s.json"
json.dump({"routes": ["api-yes-personal", "advisor-openai"], "advisor_cap_usd": 40, "return_after_s": 5}, open(d + "/p.json", "w"))
sys.path.insert(0, r"D:/论文-AI4S/wt-v34/agent/extraction")
import llm_route as L
assert L.ROUTES == ("api-yes-personal", "advisor-openai") and L.ADVISOR_CAP_USD == 40 and L.RETURN_AFTER_S == 5
mk = lambda route, model: types.SimpleNamespace(_route=route)
L.make_client = mk
r = L.Router("m")
assert r.client._route == "api-yes-personal"
r._next()                                     # personal exhausted -> advisor, time recorded
assert r.client._route == "advisor-openai" and L._spend()["first_exhausted_at"]
r.account(types.SimpleNamespace(input_tokens=2_000_000, output_tokens=1_000_000))   # 10 + 30 = 40 USD
assert abs(L._spend()["advisor_usd"] - 40) < 1e-9
r2 = L.Router("m"); assert r2.client._route == "advisor-openai", "new build starts on the fallback within the pause"
t0 = time.time(); r.before_call()             # cap used: waits until 5 s after exhaustion, then back to personal
assert r.client._route == "api-yes-personal" and time.time() - t0 > 1 and "first_exhausted_at" not in L._spend()
print("route policy: personal -> advisor, shared 40 USD cap, wait and return after the pause: PASS")
