"""Drag-and-drop editor for the code-generated figures: move labels, legends and axis titles, resize markers, then
re-render from the script. The adjustments are stored as data in <stem>.tweaks.json next to the figure and re-applied
by figures/composite/tweak.py on every render, so the script stays the source and nothing is lost on a rerun.

    python tools/figure_tweak.py <figure folder or paper figure number 1-6> [--port 8765] [--no-browser]
    tools/figure_tweak.cmd 2          (double-click and type the number)

Opens http://127.0.0.1:<port>/ . Click an item to select it; drag (or arrow keys, 0.1 mm; Shift 0.5 mm) to move a
text or legend; mouse wheel or +/- to resize a marker set (marker positions are data and do not move). "保存并重新出图"
writes the adjustments and reruns the figure script; the page then shows the new render.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PY = r"D:\Tools\pur_bridge_env\Scripts\python.exe"
PAPER_FIGS = {"1": "fig1", "2": "fig_field", "3": "fig4", "4": "fig2", "5": "fig_frontier", "6": "fig3"}   # paper No.
FALLBACK_PY =r"D:\Research\CatalystForge\.venv\Scripts\python.exe"     # e.g. fig_frontier needs yaml


class Fig:
    def __init__(self, folder, python):
        self.dir = os.path.abspath(folder)
        scripts = sorted(glob.glob(os.path.join(self.dir, "make_*.py")))
        if len(scripts) > 1:                     # e.g. fig3 also holds a helper panel script
            scripts = [s for s in scripts if os.path.basename(s).startswith("make_fig")] or scripts
        if len(scripts) != 1:
            sys.exit("expected one make_*.py in %s, found %s" % (self.dir, scripts))
        self.script, self.python = scripts[0], python
        keys = glob.glob(os.path.join(self.dir, "*.tweak_keys.json"))
        if not keys:
            print(self.render())
            keys = glob.glob(os.path.join(self.dir, "*.tweak_keys.json"))
        self.stem = os.path.basename(keys[0])[:-len(".tweak_keys.json")]
        self.lock = threading.Lock()

    def path(self, ext):
        return os.path.join(self.dir, self.stem + ext)

    def tweaks(self):
        p = self.path(".tweaks.json")
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

    def write_tweaks(self, t):
        t = {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in sorted(t.items())
             if abs(v.get("dx_mm", 0)) > 1e-3 or abs(v.get("dy_mm", 0)) > 1e-3 or abs(v.get("scale", 1) - 1) > 1e-3}
        if t:
            json.dump(t, open(self.path(".tweaks.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        elif os.path.exists(self.path(".tweaks.json")):
            os.remove(self.path(".tweaks.json"))

    def render(self):
        r = self._run()
        if r.returncode and "ModuleNotFoundError" in r.stderr and os.path.exists(FALLBACK_PY) \
                and self.python != FALLBACK_PY:
            self.python = FALLBACK_PY
            r = self._run()
        out = (r.stdout + r.stderr).strip().splitlines()
        return ("OK" if r.returncode == 0 else "ERROR %d" % r.returncode) + "\n" + "\n".join(out[-12:])

    def _run(self):
        return subprocess.run([self.python, os.path.basename(self.script)], cwd=self.dir, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")


def make_handler(fig):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, body, ctype="application/json; charset=utf-8", code=200):
            b = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            if self.path == "/":
                html = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "figure_tweak.html"),
                            encoding="utf-8").read()
                self.send(html.replace("__TITLE__", fig.stem), "text/html; charset=utf-8")
            elif self.path.startswith("/svg"):
                self.send(open(fig.path(".svg"), "rb").read(), "image/svg+xml")
            elif self.path.startswith("/keys"):
                self.send(open(fig.path(".tweak_keys.json"), encoding="utf-8").read())
            elif self.path.startswith("/tweaks"):
                self.send(json.dumps(fig.tweaks(), ensure_ascii=False))
            else:
                self.send("not found", "text/plain", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            with fig.lock:
                t = fig.tweaks()
                if self.path == "/save":                  # deltas from the page, added to what is stored
                    for k, d in req.items():
                        cur = t.setdefault(k, {})
                        for ax in ("dx_mm", "dy_mm"):
                            if d.get(ax):
                                cur[ax] = cur.get(ax, 0.0) + d[ax]
                        if d.get("scale", 1) != 1:
                            cur["scale"] = cur.get("scale", 1.0) * d["scale"]
                elif self.path == "/reset":
                    for k in req.get("keys", []):
                        t.pop(k, None)
                elif self.path == "/reset_all":
                    t = {}
                else:
                    return self.send("not found", "text/plain", 404)
                fig.write_tweaks(t)
                log = fig.render()
            self.send(json.dumps({"log": log, "tweaks": fig.tweaks()}, ensure_ascii=False))
    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", nargs="?", help="figure folder, or the paper's figure number 1-6")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--python", default=DEFAULT_PY if os.path.exists(DEFAULT_PY) else sys.executable)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    folder = a.folder or input("要调哪张图？输入正文图号 1-6：").strip()
    if folder in PAPER_FIGS:
        folder = os.path.join(ROOT, "figures", "composite", PAPER_FIGS[folder])
    fig = Fig(folder, a.python)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(fig))
    url = "http://127.0.0.1:%d/" % a.port
    print("editing %s (%s) at %s  -- Ctrl+C to stop" % (fig.stem, os.path.relpath(fig.script, ROOT), url))
    if not a.no_browser:
        webbrowser.open(url)
    srv.serve_forever()


if __name__ == "__main__":
    main()
