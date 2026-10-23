"""Figure editor for code-generated matplotlib figures, in the browser: layers, properties, colours, drag and drop.

Every figure saved through tweak.apply (Page.save does it) leaves a <stem>.tweak_keys.json that says what can be
edited and how to re-render the figure; this server finds them all under --root, shows them, writes the edits to
<stem>.tweaks.json and reruns the figure's own script. The script stays the source and nothing is lost on a rerun.

    python tools/figure_tweak.py [figure] [--root figures [--root other/figures ...]] [--port 8765] [--no-browser]
    tools/figure_tweak.cmd                      (double-click)

`figure` is a stem (FigField), a label from <root>/figure_labels.json ("Fig. 2", "2", "ED3") or omitted. Several
--root folders (other projects' figures) are listed together; the consistency check stays within the current
figure's root.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import threading
import webbrowser
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = (os.sep + ".git" + os.sep, os.sep + "node_modules" + os.sep)


def discover(root):
    """[(stem, label, keys path)] under root, or under each of a list of roots in turn; within a root ordered by its
    figure_labels.json, then by name. A stem already found under an earlier root is skipped."""
    if isinstance(root, (list, tuple)):
        out, seen = [], set()
        for r in root:
            for x in discover(r):
                if x[0] not in seen:
                    seen.add(x[0])
                    out.append(x)
        return out
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


ROLES = [("letter", "分图字母"), ("title", "分图标题"), ("axislabel", "坐标轴标题"), ("ticks", "刻度/类别标签"),
         ("legend", "图例文字"), ("text", "图中标注")]


def consistency(root):
    """Effective font size and weight of every text role in every figure (base size x the author's size factor)."""
    out, missing = {r: [] for r, _ in ROLES}, []
    for stem, lab, kp in discover(root):
        k = json.load(open(kp, encoding="utf-8"))
        tp = os.path.join(os.path.dirname(kp), stem + ".tweaks.json")
        tw = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else {}
        recs = [v for v in k.get("ids", {}).values() if "member" not in v and v.get("role") in out]
        if not any("fontsize" in v for v in k.get("ids", {}).values()):
            missing.append(lab)
        for v in recs:
            t = tw.get(v["key"], {})
            if t.get("visible") is False:
                continue
            out[v["role"]].append(dict(fig=stem, label=lab, key=v["key"], base=v["fontsize"],
                                       size=round(v["fontsize"] * t.get("size", 1.0), 2),
                                       weight=t.get("weight") or v.get("weight", "normal")))
    roles = []
    for r, name in ROLES:
        rows = out[r]
        if not rows:
            continue
        sizes = Counter(round(x["size"], 1) for x in rows)
        weights = Counter(x["weight"] for x in rows)
        mode, wmode = sizes.most_common(1)[0][0], weights.most_common(1)[0][0]
        odd = [x for x in rows if abs(x["size"] - mode) > 0.05 or (r in ("letter", "title") and x["weight"] != wmode)]
        if r == "text":                                # annotations differ on purpose: shown as a distribution only
            odd = []
        roles.append(dict(role=r, name=name, n=len(rows), mode=mode, weight=wmode,
                          sizes=sorted(sizes.items()), odd=odd))
    return dict(roles=roles, missing=missing)


def root_of(st, f):
    """The --root folder that holds figure f (the consistency check compares figures of one project)."""
    roots = st["root"] if isinstance(st["root"], (list, tuple)) else [st["root"]]
    hit = [r for r in roots if os.path.abspath(f.keys_path).startswith(os.path.abspath(r) + os.sep)]
    return max(hit, key=len) if hit else roots[0]


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
            elif self.path.startswith("/consistency"):
                self.send(json.dumps(consistency(root_of(st, f)), ensure_ascii=False))
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
                if self.path == "/unify":             # one size (and weight) for chosen texts across figures
                    figs = {s: Fig(s, p) for s, _, p in discover(root_of(st, st["fig"]))}
                    touched, logs = {}, []
                    for row in req["rows"]:
                        fg = figs.get(row["fig"])
                        if fg is None or not row.get("base"):
                            continue
                        t = touched.setdefault(row["fig"], fg.tweaks())
                        e = t.setdefault(row["key"], {})
                        e["size"] = req["size"] / row["base"]
                        if req.get("weight"):
                            e["weight"] = req["weight"]
                    for stem, t in touched.items():
                        figs[stem].write_tweaks(t)
                        logs.append("%s: %s" % (stem, figs[stem].render().splitlines()[0]))
                    return self.send(json.dumps({"log": "OK\n" + "\n".join(logs)}, ensure_ascii=False))
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
    ap.add_argument("--root", action="append",
                    help="folder searched for *.tweak_keys.json; repeat for several projects "
                         "(default: ../figures next to this tool, else here)")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    root = [os.path.abspath(r) for r in (a.root or [guess if os.path.isdir(guess) else os.getcwd()])]
    missing = [r for r in root if not os.path.isdir(r)]
    if missing:
        print("skipped (folder not found): %s" % "; ".join(missing))
    root = [r for r in root if os.path.isdir(r)]
    figs = discover(root)
    if not figs:
        sys.exit("no *.tweak_keys.json under %s: render a figure through tweak.apply first" % "; ".join(root))
    stem = resolve(figs, a.figure)
    st = {"root": root, "figs": figs, "lock": threading.Lock(),
          "fig": Fig(stem, next(p for s, _, p in figs if s == stem))}
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(st))
    url = "http://127.0.0.1:%d/" % a.port
    print("figure editor at %s  (%d figures under %s)  -- Ctrl+C to stop" % (url, len(figs), "; ".join(root)))
    if not a.no_browser:
        webbrowser.open(url)
    srv.serve_forever()


if __name__ == "__main__":
    main()
