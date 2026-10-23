"""Figure editor for code-generated matplotlib figures, in the browser: layers, properties, colours, drag and drop.

Every figure saved through tweak.apply (Page.save does it) leaves a <stem>.tweak_keys.json that says what can be
edited and how to re-render the figure; this server finds them all under --root, shows them, writes the edits to
<stem>.tweaks.json and reruns the figure's own script. The script stays the source and nothing is lost on a rerun.

    python tools/figure_tweak.py [figure] [--root figures] [--port 8765] [--no-browser]
    tools/figure_tweak.cmd                      (double-click)

`figure` is a stem (FigField), a label from <root>/figure_labels.json ("Fig. 2", "2", "ED3") or omitted.
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

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = (os.sep + ".git" + os.sep, os.sep + "node_modules" + os.sep)


def discover(root):
    """stem -> keys-file path, for every figure under root, ordered by figure_labels.json then by name."""
    labels_path = os.path.join(root, "figure_labels.json")
    labels = json.load(open(labels_path, encoding="utf-8")) if os.path.exists(labels_path) else {}
    found = {}
    for p in glob.glob(os.path.join(root, "**", "*.tweak_keys.json"), recursive=True):
        if not any(s in p for s in SKIP):
            found[os.path.basename(p)[:-len(".tweak_keys.json")]] = p
    order = [s for s in labels if s in found] + sorted(s for s in found if s not in labels)
    return [(s, labels.get(s, s), found[s]) for s in order]


def resolve(figs, want):
    if not want:
        return figs[0][0]
    w = want.strip().lower().replace(" ", "")
    for s, lab, _ in figs:
        l2 = lab.lower().replace(" ", "")
        if w in (s.lower(), l2) or l2 in ("fig." + w, "extendeddatafig." + w.replace("ed", "", 1)):
            return s
    sys.exit("unknown figure %r; known: %s" % (want, ", ".join(l for _, l, _ in figs)))


class Fig:
    def __init__(self, stem, keys_path):
        self.stem, self.keys_path = stem, keys_path
        self.dir = os.path.dirname(keys_path)

    def path(self, ext):
        return os.path.join(self.dir, self.stem + ext)

    def meta(self):
        return json.load(open(self.keys_path, encoding="utf-8")).get("meta", {})

    def tweaks(self):
        p = self.path(".tweaks.json")
        return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

    def write_tweaks(self, t):
        clean = {}
        for k, v in sorted(t.items()):
            out = {}
            for kk, vv in (v or {}).items():
                if isinstance(vv, float):
                    vv = round(vv, 3)
                if (kk in ("dx_mm", "dy_mm", "dw_mm", "dh_mm") and abs(vv) < 1e-3) \
                        or (kk in ("size", "scale", "lw") and abs(vv - 1) < 1e-3) \
                        or (kk in ("rename", "colors") and not vv) or (kk == "visible" and vv is True):
                    continue
                out[kk] = vv
            if out:
                clean[k] = out
        p = self.path(".tweaks.json")
        if clean:
            json.dump(clean, open(p, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        elif os.path.exists(p):
            os.remove(p)

    def render(self):
        m = self.meta()
        if not m.get("script"):
            return "ERROR\n%s has no render information; run its script once with the current tweak.py" % self.stem
        r = subprocess.run([m["python"], m["script"]] + m.get("args", []), cwd=m.get("cwd") or self.dir,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = (r.stdout + r.stderr).strip().splitlines()
        return ("OK" if r.returncode == 0 else "ERROR %d" % r.returncode) + "\n" + "\n".join(out[-12:])


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
            f = st["fig"]
            if self.path == "/":
                self.send(open(os.path.join(HERE, "figure_tweak.html"), encoding="utf-8").read(),
                          "text/html; charset=utf-8")
            elif self.path.startswith("/figs"):
                st["figs"] = discover(st["root"])
                self.send(json.dumps({"current": f.stem, "figs": [[s, l] for s, l, _ in st["figs"]]},
                                     ensure_ascii=False))
            elif self.path.startswith("/svg"):
                self.send(open(f.path(".svg"), "rb").read(), "image/svg+xml")
            elif self.path.startswith("/keys"):
                self.send(open(f.keys_path, encoding="utf-8").read())
            elif self.path.startswith("/tweaks"):
                self.send(json.dumps(f.tweaks(), ensure_ascii=False))
            else:
                self.send("not found", "text/plain", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            with st["lock"]:
                if self.path == "/open":
                    hit = [x for x in discover(st["root"]) if x[0] == req["fig"]]
                    if not hit:
                        return self.send(json.dumps({"log": "ERROR\nno such figure"}))
                    st["fig"] = Fig(hit[0][0], hit[0][2])
                    return self.send(json.dumps({"log": "OK"}))
                f = st["fig"]
                t = f.tweaks()
                if self.path == "/save":                  # full settings of the changed items; null removes one
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
    ap.add_argument("figure", nargs="?")
    guess = os.path.join(os.path.dirname(HERE), "figures")
    ap.add_argument("--root", default=guess if os.path.isdir(guess) else os.getcwd(),
                    help="folder searched for *.tweak_keys.json (default: ../figures next to this tool, else here)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    root = os.path.abspath(a.root)
    figs = discover(root)
    if not figs:
        sys.exit("no *.tweak_keys.json under %s: render a figure through tweak.apply first" % root)
    stem = resolve(figs, a.figure)
    st = {"root": root, "figs": figs, "lock": threading.Lock(),
          "fig": Fig(stem, next(p for s, _, p in figs if s == stem))}
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(st))
    url = "http://127.0.0.1:%d/" % a.port
    print("figure editor at %s  (%d figures under %s)  -- Ctrl+C to stop" % (url, len(figs), root))
    if not a.no_browser:
        webbrowser.open(url)
    srv.serve_forever()


if __name__ == "__main__":
    main()
