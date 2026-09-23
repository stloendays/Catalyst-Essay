"""Build the canonical Figure 8 assets from the two cleaned Origin panel SVGs.

    python render_composite.py <out_dir> [chrome.exe]

Writes <out_dir>/F08_MeOH_selectivity_recycle_D01v3.{svg,png,pdf}:
  svg  composed by compose_svg.py, physical size 183 mm wide
  png  headless Chrome raster of that same SVG, one CSS px per viewBox unit
  pdf  headless Chrome print of that same SVG at its physical size, fonts embedded

All three come from one source, so they cannot drift apart.
"""
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "F08_MeOH_selectivity_recycle_D01v3"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def chrome(args, exe):
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars"] + args,
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def file_url(path):
    return "file:///" + os.path.abspath(path).replace("\\", "/")


def main():
    out_dir = os.path.abspath(sys.argv[1])
    exe = sys.argv[2] if len(sys.argv) > 2 else CHROME
    svg = os.path.join(out_dir, BASE + ".svg")
    png = os.path.join(out_dir, BASE + ".png")
    pdf = os.path.join(out_dir, BASE + ".pdf")

    subprocess.run([sys.executable, os.path.join(HERE, "compose_svg.py"),
                    os.path.join(HERE, "F08_panel_a.svg"), os.path.join(HERE, "F08_panel_a.png"),
                    os.path.join(HERE, "F08_panel_b.svg"), os.path.join(HERE, "F08_panel_b.png"),
                    svg, "183"], check=True)

    src = open(svg, encoding="utf-8").read()
    ET.fromstring(src.encode("utf-8"))  # must be well-formed XML, or viewers refuse it
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', src).group(1).split()]
    W, H = round(vb[2]), round(vb[3])
    wmm = float(re.search(r'width="([\d.]+)mm"', src).group(1))
    hmm = float(re.search(r'height="([\d.]+)mm"', src).group(1))

    tmp = os.path.join(out_dir, "_render_tmp")
    os.makedirs(tmp, exist_ok=True)
    px_svg = os.path.join(tmp, "px.svg")
    with open(px_svg, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(re.sub(r'width="[\d.]+mm" height="[\d.]+mm"',
                        'width="%dpx" height="%dpx"' % (W, H), src, count=1))
    chrome(["--force-device-scale-factor=1", "--default-background-color=FFFFFFFF",
            "--window-size=%d,%d" % (W, H), "--screenshot=" + png, file_url(px_svg)], exe)

    html = os.path.join(tmp, "print.html")
    with open(html, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('<!doctype html><html><head><meta charset="utf-8"><style>'
                 '@page{size:%.2fmm %.2fmm;margin:0}html,body{margin:0;padding:0;background:#fff}'
                 'svg{display:block;width:%.2fmm;height:%.2fmm}</style></head><body>%s</body></html>'
                 % (wmm, hmm, wmm, hmm, src[src.index("<svg"):]))
    chrome(["--no-pdf-header-footer", "--print-to-pdf-no-header", "--print-to-pdf=" + pdf,
            file_url(html)], exe)

    for p in (px_svg, html):
        os.remove(p)
    os.rmdir(tmp)
    print("wrote %s.{svg,png,pdf}: %.1f x %.1f mm, raster %d x %d px" % (BASE, wmm, hmm, W, H))


if __name__ == "__main__":
    main()
