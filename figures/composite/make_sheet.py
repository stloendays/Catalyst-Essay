"""Compose the individual figure SVGs into sheets, then render PDF and PNG.

Each figure stays a nested <svg> with its own coordinate system, so a sheet is
still vector and still carries live text -- a composition, not a screenshot.
Figures may be scaled down individually; a sheet does not owe anything
submission size. The individual per-figure SVG/PDF/PNG files, written by each
make_figN.py, remain the submission artifacts.

Two sheets are built: the five manuscript figures in reading order, and the
supplementary figures.

Things this has to get right:

  * every child's ids must be namespaced. Matplotlib writes <defs> full of
    glyph paths and clip paths referenced by xlink:href and url(), and the
    names repeat across files. Without a per-child prefix the later figures
    render with the earlier ones' glyphs and clips.
  * the parent must declare xmlns:xlink, or the href references do not resolve
    and the sheet silently loses its text.
  * Chrome's --window-size is CSS pixels at 96 dpi, not device pixels (see the
    comment at the render step).

    D:/Tools/pur_bridge_env/Scripts/python.exe make_sheet.py
"""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PT_MM = 25.4 / 72.0

GAP, PAD, TOP = 9.0, 8.0, 17.0      # between figures, around the sheet, header
CAP = 4.6                           # caption strip above each figure

# stem -> (title, columns). Each column is a list of (file, caption, scale).
# Columns are balanced by total height, and the order inside the main sheet
# follows the manuscript: 1 and 2 down the left, 3 to 5 down the right.
SHEETS = {
    "Sheet_main_figures": (
        "Laboratory catalyst leaders are often not the plant-level optimum: main figures 1\u20136",
        [[("fig1/Fig1.svg", "Figure 1   The most active ammonia catalyst is not the cheapest to run", 0.72),
          ("fig4/Fig4.svg", "Figure 3   Selectivity, recycle and purge reshape the methanol ranking", 0.72),
          ("fig_frontier/FigFrontier.svg", "Figure 5   Supported Ru/C matches fused iron, downstream", 0.72)],
         [("fig_field/FigField.svg", "Figure 2   Laboratory leaders are often not the plant-cost leaders", 0.72),
          ("fig2/Fig2.svg", "Figure 4   Ru matches iron only at a 99% lower price", 0.72),
          ("fig3/Fig3.svg", "Figure 6   Backward design separates targets from reachable properties", 0.72)]]),
}


def read_svg(path):
    """Return (width_mm, height_mm, viewbox, body) for a matplotlib SVG."""
    s = open(path, encoding="utf-8").read()
    m = re.search(r"<svg\b[^>]*>", s)
    head = m.group(0)
    w = float(re.search(r'width="([0-9.]+)pt"', head).group(1))
    h = float(re.search(r'height="([0-9.]+)pt"', head).group(1))
    vb = re.search(r'viewBox="([^"]+)"', head).group(1)
    body = s[m.end():s.rindex("</svg>")]
    return w * PT_MM, h * PT_MM, vb, body


def namespace(body, tag):
    """Prefix every id in the child, and every reference to one."""
    ids = set(re.findall(r'\bid="([^"]+)"', body))
    for oid in sorted(ids, key=len, reverse=True):
        new = "%s-%s" % (tag, oid)
        body = body.replace('id="%s"' % oid, 'id="%s"' % new)
        body = body.replace("url(#%s)" % oid, "url(#%s)" % new)
        body = body.replace('xlink:href="#%s"' % oid, 'xlink:href="#%s"' % new)
        body = body.replace('href="#%s"' % oid, 'href="#%s"' % new)
    return body


def compose(title, columns):
    cols = []
    for spec in columns:
        items, y = [], 0.0
        for path, caption, scale in spec:
            w, h, vb, body = read_svg(os.path.join(HERE, path))
            items.append(dict(path=path, caption=caption, vb=vb, body=body,
                              w=w * scale, h=h * scale, y=y))
            y += CAP + h * scale + GAP
        cols.append(dict(items=items, w=max(i["w"] for i in items), h=y - GAP))

    x = PAD
    for col in cols:
        col["x"] = x
        x += col["w"] + GAP + 3.0
    sheet_w = x - GAP - 3.0 + PAD
    sheet_h = TOP + max(c["h"] for c in cols) + PAD

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        'width="%.2fmm" height="%.2fmm" viewBox="0 0 %.2f %.2f">'
        % (sheet_w, sheet_h, sheet_w, sheet_h),
        '<rect x="0" y="0" width="%.2f" height="%.2f" fill="#ffffff"/>'
        % (sheet_w, sheet_h),
        '<text x="%.2f" y="7.0" font-family="Arial" font-size="5.0" '
        'font-weight="700" fill="#1B1B1B">%s</text>' % (PAD, title),
        '<text x="%.2f" y="11.6" font-family="Arial" font-size="3.0" '
        'fill="#6B6F76">Each figure is the same vector artwork as its own SVG '
        'and PDF; figures are scaled individually on this sheet only.</text>'
        % PAD,
    ]
    n = 0
    for col in cols:
        for it in col["items"]:
            yy = TOP + it["y"]
            parts.append('<text x="%.2f" y="%.2f" font-family="Arial" '
                         'font-size="3.4" font-weight="700" fill="#1B1B1B">%s'
                         '</text>' % (col["x"], yy + 3.0, it["caption"]))
            parts.append('<svg x="%.2f" y="%.2f" width="%.2f" height="%.2f" '
                         'viewBox="%s" preserveAspectRatio="xMinYMin meet">'
                         % (col["x"], yy + CAP, it["w"], it["h"], it["vb"]))
            parts.append(namespace(it["body"], "f%d" % n))
            parts.append("</svg>")
            n += 1
    parts.append("</svg>")
    return "\n".join(parts), sheet_w, sheet_h, n


def render(stem, svg, sheet_w, sheet_h):
    html = os.path.join(HERE, "_%s_tmp.html" % stem)
    open(html, "w", encoding="utf-8").write(
        "<!doctype html><meta charset='utf-8'><style>"
        "@page{size:%.2fmm %.2fmm;margin:0}"
        "html,body{margin:0;padding:0;background:#fff}svg{display:block}"
        "</style>%s" % (sheet_w, sheet_h, svg))
    url = "file:///" + html.replace("\\", "/")
    # --window-size is CSS pixels at 96 dpi, not device pixels. Sizing it from
    # the target dpi makes the window far larger than the sheet, and the sheet
    # renders into a corner of it at about a third of the intended scale.
    css = lambda mm: max(1, round(mm * 96.0 / 25.4))
    jobs = [
        (["--print-to-pdf=%s" % os.path.join(HERE, stem + ".pdf"),
          "--no-pdf-header-footer"], "pdf"),
        (["--screenshot=%s" % os.path.join(HERE, stem + ".png"),
          "--window-size=%d,%d" % (css(sheet_w), css(sheet_h)),
          "--force-device-scale-factor=3"], "png"),          # ~288 dpi
    ]
    try:
        for flags, ext in jobs:
            out = os.path.join(HERE, "%s.%s" % (stem, ext))
            if os.path.exists(out):
                os.remove(out)
            r = subprocess.run(
                [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                 "--default-background-color=FFFFFFFF"] + flags + [url],
                check=False, capture_output=True, timeout=300)
            # Chrome can exit 0 without writing anything, so trust the file.
            if os.path.exists(out):
                print("  %-3s ok   %.0f kB" % (ext, os.path.getsize(out) / 1024))
            else:
                print("  %-3s FAILED  %s"
                      % (ext, r.stderr.decode("utf-8", "ignore")[-300:]))
    finally:
        if os.path.exists(html):
            os.remove(html)


def main():
    for stem, (title, columns) in SHEETS.items():
        svg, w, h, n = compose(title, columns)
        open(os.path.join(HERE, stem + ".svg"), "w", encoding="utf-8").write(svg)
        print("wrote %s.svg   %.1f x %.1f mm, %d figures" % (stem, w, h, n))
        render(stem, svg, w, h)


if __name__ == "__main__":
    main()
