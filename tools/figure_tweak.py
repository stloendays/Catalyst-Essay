"""Drag-and-drop editor for the code-generated figures (main Figs. 1-6 and Extended Data Figs. 1-10).

Move or resize a whole chart, move texts, annotation labels, axis titles, legends and the tick or category labels of
an axis, change their wording and size, resize marker sets, then re-render from the script. The adjustments are
stored as data in <stem>.tweaks.json next to the figure and re-applied by figures/composite/tweak.py on every render,
so the script stays the source and nothing is lost on a rerun.

    python tools/figure_tweak.py [2 | ED3 | <figure folder>] [--port 8765] [--no-browser]
    tools/figure_tweak.cmd            (double-click; pick the figure in the page)

Opens http://127.0.0.1:<port>/ ; the figure can be switched in the page.
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
FALLBACK_PY = r"D:\Research\CatalystForge\.venv\Scripts\python.exe"     # e.g. fig_frontier needs yaml
COMP, ED = os.path.join(ROOT, "figures", "composite"), os.path.join(ROOT, "figures", "extended_data")
# paper figure number -> folder, script, arguments, output stem
FIGS = {str(n): (os.path.join(COMP, d), s, [], stem) for n, d, s, stem in (
    (1, "fig1", "make_fig1.py", "Fig1"), (2, "fig_field", "make_fig_field.py", "FigField"),
    (3, "fig4", "make_fig4.py", "Fig4"), (4, "fig2", "make_fig2.py", "Fig2"),
    (5, "fig_frontier", "make_fig_frontier.py", "FigFrontier"), (6, "fig3", "make_fig3.py", "Fig3"))}
for _f in sorted(glob.glob(os.path.join(ED, "EDFig*_*.svg")), key=lambda p: int(os.path.basename(p)[5:].split("_")[0])):
    _stem = os.path.basename(_f)[:-4]
    _n = _stem[5:].split("_")[0]
    FIGS["ED" + _n] = (ED, "render_extended_data.py", [_n], _stem)


def label(fid):
    return ("Extended Data Fig. " + fid[2:]) if fid.startswith("ED") else ("Fig. " + fid)


class Fig:
    def __init__(self, fid, python):
        self.fid = fid
        self.dir, self.script, self.args, self.stem = FIGS[fid]
        self.python = python
        if not os.path.exists(self.path(".tweak_keys.json")):
            print(self.render())

    def path(self, ext):
        return os.path.join(self.dir, self.stem + ext)

    def tweaks(self):
        p = self.path(".tweaks.json")
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

    def write_tweaks(self, t):
        clean = {}
        for k, v in sorted(t.items()):
            v = {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in (v or {}).items()}
            v = {kk: vv for kk, vv in v.items() if not (
                (kk in ("dx_mm", "dy_mm", "dw_mm", "dh_mm") and abs(vv) < 1e-3)
                or (kk in ("size", "scale") and abs(vv - 1) < 1e-3) or (kk == "rename" and not vv))}
            if v:
                clean[k] = v
        p = self.path(".tweaks.json")
        if clean:
            json.dump(clean, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        elif os.path.exists(p):
            os.remove(p)

    def render(self):
        r = self._run()
        if r.returncode and "ModuleNotFoundError" in r.stderr and os.path.exists(FALLBACK_PY) \
                and self.python != FALLBACK_PY:
            self.python = FALLBACK_PY
            r = self._run()
        out = (r.stdout + r.stderr).strip().splitlines()
        return ("OK" if r.returncode == 0 else "ERROR %d" % r.returncode) + "\n" + "\n".join(out[-12:])

    def _run(self):
        return subprocess.run([self.python, self.script] + self.args, cwd=self.dir, capture_output=True,
                              text=True, encoding="utf-8", errors="replace")


class State:
    def __init__(self, fid, python):
        self.python, self.lock, self.fig = python, threading.Lock(), Fig(fid, python)


def make_handler(st):
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
            f = st.fig
            if self.path == "/":
                self.send(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "figure_tweak.html"),
                               encoding="utf-8").read(), "text/html; charset=utf-8")
            elif self.path.startswith("/figs"):
                self.send(json.dumps({"current": f.fid, "stem": f.stem,
                                      "figs": [[k, label(k)] for k in FIGS]}, ensure_ascii=False))
            elif self.path.startswith("/svg"):
                self.send(open(f.path(".svg"), "rb").read(), "image/svg+xml")
            elif self.path.startswith("/keys"):
                self.send(open(f.path(".tweak_keys.json"), encoding="utf-8").read())
            elif self.path.startswith("/tweaks"):
                self.send(json.dumps(f.tweaks(), ensure_ascii=False))
            else:
                self.send("not found", "text/plain", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            with st.lock:
                if self.path == "/open":
                    st.fig = Fig(req["fig"], st.python)
                    return self.send(json.dumps({"log": "OK"}))
                f = st.fig
                t = f.tweaks()
                if self.path == "/save":                  # full overrides of the changed items; null removes one
                    for k, v in req.items():
                        if v:
                            t[k] = v
                        else:
                            t.pop(k, None)
                elif self.path == "/reset_all":
                    t = {}
                elif self.path != "/render":
                    return self.send("not found", "text/plain", 404)
                f.write_tweaks(t)
                log = f.render()
            self.send(json.dumps({"log": log}, ensure_ascii=False))
    return H


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("figure", nargs="?", default="2", help="paper figure number 1-6, ED1-ED10, or a figure folder")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--python", default=DEFAULT_PY if os.path.exists(DEFAULT_PY) else sys.executable)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    fid = a.figure.upper().replace(" ", "")
    if fid not in FIGS:                                   # a folder: match it in the registry
        d = os.path.abspath(a.figure)
        fid = next((k for k, v in FIGS.items() if os.path.abspath(v[0]) == d), None)
        if fid is None:
            sys.exit("unknown figure %r; use 1-6, ED1-ED10 or a folder among %s" % (a.figure, sorted(FIGS)))
    st = State(fid, a.python)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(st))
    url = "http://127.0.0.1:%d/" % a.port
    print("figure editor at %s (%s)  -- Ctrl+C to stop" % (url, label(fid)))
    if not a.no_browser:
        webbrowser.open(url)
    srv.serve_forever()


if __name__ == "__main__":
    main()
