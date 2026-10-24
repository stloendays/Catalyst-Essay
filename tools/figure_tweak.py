"""Figure editor for code-generated matplotlib figures, in the browser: layers, properties, colours, drag and drop.

Every figure saved through tweak.apply (Page.save does it) leaves a <stem>.tweak_keys.json that says what can be
edited and how to re-render the figure; this server finds them all under --root, shows them, writes the edits to
<stem>.tweaks.json and reruns the figure's own script. The script stays the source and nothing is lost on a rerun.

    python tools/figure_tweak.py [figure] [--root figures [--root other/figures ...]] [--port 8765] [--no-browser]
    python tools/figure_tweak.py --overlay D:/data/fig_origin.svg      (an external figure: annotate on top of it)
    tools/figure_tweak.cmd                      (double-click)

`figure` is a stem (FigField), a label from <root>/figure_labels.json ("Fig. 2", "2", "ED3") or omitted. Several
--root folders (other projects' figures) are listed together; the consistency check stays within the current
figure's root.
"""
import argparse
import base64
import glob
import json
import os
import re
import subprocess
import sys
import threading
import webbrowser
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = (os.sep + ".git" + os.sep, os.sep + "node_modules" + os.sep)


def stem_of(keys_path):
    return os.path.basename(keys_path)[:-len(".tweak_keys.json")]


def discover(root):
    """[(id, label, keys path)] under root, or under each of a list of roots in turn; within a root ordered by its
    figure_labels.json, then by name. The id is the stem (FigField), or the path below the root (nc/fig7/Fig7) when
    two figures share a stem; figure_labels.json may name a figure by either. An id already found under an earlier
    root is skipped."""
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
    paths = sorted(p for p in glob.glob(os.path.join(root, "**", "*.tweak_keys.json"), recursive=True)
                   if not any(s in p for s in SKIP))
    n = Counter(stem_of(p) for p in paths)
    found, label = {}, {}
    for p in paths:
        rel = os.path.relpath(p, root)[:-len(".tweak_keys.json")].replace(os.sep, "/")
        fid = stem_of(p) if n[stem_of(p)] == 1 else rel
        found[fid] = p
        label[fid] = labels.get(rel) or labels.get(fid) or fid
    by_label = {k: i for i, k in enumerate(labels)}
    rank = {f: min(by_label.get(os.path.relpath(p, root)[:-len(".tweak_keys.json")].replace(os.sep, "/"), 1e9),
                   by_label.get(f, 1e9)) for f, p in found.items()}
    order = sorted(found, key=lambda f: (rank[f], f))
    return [(f, label[f], found[f]) for f in order]


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
    def __init__(self, fid, keys_path):
        self.id, self.stem, self.keys_path = fid, stem_of(keys_path), keys_path
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

    def svg_text(self):
        """The SVG the editor shows: the figure's own render, or an external figure's source as is."""
        m = self.meta()
        if m.get("overlay"):
            return overlay_source_svg(os.path.join(self.dir, m["source"]))
        return open(self.path(".svg"), encoding="utf-8").read()

    def render(self):
        m = self.meta()
        if m.get("overlay"):
            return render_overlay(self)
        if not m.get("script"):
            return "ERROR\n%s has no render information; run its script once with the current tweak.py" % self.stem
        r = subprocess.run([m["python"], m["script"]] + m.get("args", []), cwd=m.get("cwd") or self.dir,
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))   # no console flash under pythonw
        out = (r.stdout + r.stderr).strip().splitlines()
        return ("OK" if r.returncode == 0 else "ERROR %d" % r.returncode) + "\n" + "\n".join(out[-12:])


# ---- external figures (Origin, R, any SVG or PNG): an annotation layer on top, exported as <stem>_annotated.* --------

UNIT_MM = {"mm": 1.0, "cm": 10.0, "in": 25.4, "pt": 25.4 / 72, "pc": 25.4 / 6, "px": 25.4 / 96, "": 25.4 / 96}
PAPER_PALETTE = {"INK": "#1b1b1b", "RU": "#5677b5", "DARK_B": "#304c86", "OS": "#97abd4", "PALE_B": "#c8d3ea",
                 "FE": "#6e9f60", "DARK_G": "#467238", "RED": "#d9474f", "AMB": "#e0913a", "MID": "#5f646c"}
CHROME = next((p for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe") if os.path.exists(p)), None)


def _length_mm(s):
    m = re.match(r"\s*([\d.]+)\s*([a-z]*)", s or "")
    return float(m.group(1)) * UNIT_MM.get(m.group(2), 25.4 / 96) if m else None


def overlay_source_svg(src):
    """The external figure as SVG with a viewBox (a PNG is wrapped in one, embedded)."""
    if src.lower().endswith(".svg"):
        txt = open(src, encoding="utf-8").read()
        root = re.search(r"<svg\b[^>]*>", txt).group(0)
        if "viewBox" not in root:
            w, h = (re.search(r'\b%s="([^"]+)"' % a, root).group(1) for a in ("width", "height"))
            vb = 'viewBox="0 0 %s %s"' % (re.match(r"[\d.]+", w).group(0), re.match(r"[\d.]+", h).group(0))
            txt = txt.replace(root, root[:-1] + " " + vb + ">", 1)
        return txt
    from PIL import Image
    im = Image.open(src)
    dpi = (im.info.get("dpi") or (300, 300))[0] or 300
    w_mm, h_mm = im.width / dpi * 25.4, im.height / dpi * 25.4
    data = base64.b64encode(open(src, "rb").read()).decode()
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="%.3fmm" '
            'height="%.3fmm" viewBox="0 0 %d %d"><image x="0" y="0" width="%d" height="%d" '
            'xlink:href="data:image/png;base64,%s"/></svg>' % (w_mm, h_mm, im.width, im.height, im.width, im.height, data))


def register_overlay(src):
    """Write <stem>.tweak_keys.json next to an external figure, so the editor lists and edits it."""
    src = os.path.abspath(src)
    if not os.path.isfile(src) or not src.lower().endswith((".svg", ".png")):
        raise ValueError("需要一个 .svg 或 .png 文件：%s" % src)
    stem = os.path.splitext(os.path.basename(src))[0]
    kp = os.path.join(os.path.dirname(src), stem + ".tweak_keys.json")
    if os.path.exists(kp) and not json.load(open(kp, encoding="utf-8")).get("meta", {}).get("overlay"):
        raise ValueError("%s 已是脚本出的图，直接在列表里打开它" % stem)
    txt = overlay_source_svg(src)
    root = re.search(r"<svg\b[^>]*>", txt).group(0)
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', root).group(1).replace(",", " ").split()]
    w = re.search(r'\bwidth="([^"]+)"', root)
    w_mm = _length_mm(w.group(1)) if w and not w.group(1).endswith("%") else vb[2] * 25.4 / 96
    unit = w_mm / vb[2]
    cols = Counter(c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", txt[:2_000_000]))
    meta = dict(stem=stem, overlay=True, source=os.path.basename(src), unit_mm=unit,
                size_mm=[round(vb[2] * unit, 2), round(vb[3] * unit, 2)],
                palette=[c for c, _ in cols.most_common(14)], style_palette=PAPER_PALETTE)
    json.dump(dict(meta=meta, ids={}), open(kp, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    return kp


def render_overlay(f):
    """<stem>_annotated.svg = the source plus the saved annotation layer, and its PNG (600 dpi) and PDF."""
    m = f.meta()
    frag_p = f.path(".overlay.svgfrag")
    frag = open(frag_p, encoding="utf-8").read() if os.path.exists(frag_p) else ""
    txt = overlay_source_svg(os.path.join(f.dir, m["source"]))
    i = txt.rstrip().rfind("</svg>")
    out_svg = f.path("_annotated.svg")
    open(out_svg, "w", encoding="utf-8").write(txt[:i] + '<g id="annotations">\n' + frag + "\n</g>\n" + txt[i:])
    logs = ["wrote %s" % os.path.basename(out_svg)]
    if not CHROME:
        return "OK\n" + logs[0] + "\n(no Chrome/Edge found: PNG and PDF not written)"
    w_mm, h_mm = m["size_mm"]
    html = f.path("_annotated.export.html")
    open(html, "w", encoding="utf-8").write(
        "<!doctype html><meta charset='utf-8'><style>@page{size:%.2fmm %.2fmm;margin:0}html,body{margin:0;"
        "background:#fff}img{display:block;width:%.2fmm;height:%.2fmm}</style><img src='%s'>"
        % (w_mm, h_mm, w_mm, h_mm, os.path.basename(out_svg)))
    css = lambda mm: max(1, round(mm * 96 / 25.4))
    url = "file:///" + html.replace("\\", "/")
    try:
        for ext, flags in (("pdf", ["--print-to-pdf=%s" % f.path("_annotated.pdf"), "--no-pdf-header-footer"]),
                           ("png", ["--screenshot=%s" % f.path("_annotated.png"),
                                    "--window-size=%d,%d" % (css(w_mm), css(h_mm)),
                                    "--force-device-scale-factor=%.4f" % (600 / 96)])):
            out = f.path("_annotated." + ext)
            if os.path.exists(out):
                os.remove(out)
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--default-background-color=FFFFFFFF"] + flags + [url], capture_output=True, timeout=300,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            logs.append(("wrote %s" if os.path.exists(out) else "FAILED %s") % os.path.basename(out))
    finally:
        if os.path.exists(html):
            os.remove(html)
    return ("OK" if all(not l.startswith("FAILED") for l in logs) else "ERROR") + "\n" + "\n".join(logs)


ROLES = [("letter", "分图字母"), ("title", "分图标题"), ("axislabel", "坐标轴标题"), ("ticks", "刻度/类别标签"),
         ("legend", "图例文字"), ("text", "图中标注")]


def consistency(root):
    """Effective font size and weight of every text role in every figure (base size x the author's size factor)."""
    out, missing = {r: [] for r, _ in ROLES}, []
    for fid, lab, kp in discover(root):
        k = json.load(open(kp, encoding="utf-8"))
        tp = os.path.join(os.path.dirname(kp), stem_of(kp) + ".tweaks.json")
        tw = json.load(open(tp, encoding="utf-8")) if os.path.exists(tp) else {}
        recs = [v for v in k.get("ids", {}).values() if "member" not in v and v.get("role") in out]
        if not any("fontsize" in v for v in k.get("ids", {}).values()):
            missing.append(lab)
        for v in recs:
            t = tw.get(v["key"], {})
            if t.get("visible") is False:
                continue
            out[v["role"]].append(dict(fig=fid, label=lab, key=v["key"], base=v["fontsize"],
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
                self.send(json.dumps({"current": f.id, "figs": [[s, l] for s, l, _ in st["figs"]]},
                                     ensure_ascii=False))
            elif self.path.startswith("/svg"):
                self.send(f.svg_text(), "image/svg+xml; charset=utf-8")
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
                if self.path == "/overlay":            # register an external SVG/PNG and open it
                    try:
                        kp = register_overlay(req["path"])
                    except Exception as e:                  # noqa: BLE001 -- shown to the author as is
                        return self.send(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
                    d = os.path.dirname(kp)
                    roots = st["root"] if isinstance(st["root"], list) else [st["root"]]
                    if not any(os.path.abspath(kp).startswith(os.path.abspath(r) + os.sep) for r in roots):
                        st["root"] = roots + [d]
                    hit = [x for x in discover(st["root"]) if os.path.abspath(x[2]) == os.path.abspath(kp)]
                    st["fig"] = Fig(hit[0][0], hit[0][2])
                    return self.send(json.dumps({"ok": True}))
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
                frag = req.pop("__overlay_svg", None)
                if frag is not None or self.path == "/reset_all":
                    if f.meta().get("overlay"):             # the external figure's annotation layer, as drawn
                        open(f.path(".overlay.svgfrag"), "w", encoding="utf-8").write(frag or "")
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
    ap.add_argument("--overlay", action="append", default=[],
                    help="an external SVG or PNG (Origin, R, ...) to annotate; listed with the other figures")
    a = ap.parse_args()
    for src in a.overlay:
        kp = register_overlay(src)
        a.root = (a.root or []) + [os.path.dirname(kp)]
        a.figure = a.figure or os.path.splitext(os.path.basename(src))[0]
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
