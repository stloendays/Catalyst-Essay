"""Metro-map tracks: the preferred way to draw a workflow / decision contract (no box-and-arrow).

One line carries the object through the procedure. Parameters are stations on the line (symbol above,
short descriptor below), decisions are small solid nodes with the *passing* condition above, and each
failing verdict leaves the line as a smooth curve that carries its failing condition and ends in a
labelled terminal. Soft rounded bands behind the line group stages (they are backgrounds, not boxes:
no outline). The line colour can change per section to encode what it is carrying.

Reference implementation: QSQ Fig. 1b (D:/Research/QoI-paper-20260927/figures/composite/fig1/make_fig1.py).

    import track
    tr = track.Track(cv, y=27.0)                 # cv: millimetre canvas from style.Page.canvas
    tr.band(33, 78, "#E4ECDE", "Axis 1 - QoI Stability Qualification", "#5E7A52")
    tr.seg(15, 86, "#5E7A52"); tr.chevron(27)
    tr.station(45, r"$\\mathit{\\rho} + \\mathit{\\delta}_\\mathit{k}$", "5 pre-specified\\nperturbations", "#5E7A52")
    tr.gate(86, r"$\\mathit{f}_\\mathrm{m} < \\mathit{\\tau}$", "#5E7A52")
    tr.branch(86, 97, 7, "#EB6969", r"$\\mathit{f}_\\mathrm{m} \\geq \\mathit{\\tau}$", "non-evaluable", "...")
    tr.terminal(170, "#89AA7B", check=True)

Wrap variables in \\mathit{}: the house rc sets mathtext.default = regular. Text colours are dark
ink; a light line (e.g. a grey branch) takes a darker text_color (no light-grey text).
"""
from matplotlib.patches import Circle, FancyBboxPatch, PathPatch
from matplotlib.path import Path

SERIF, MATH = "Times New Roman", "stix"
INK, SYMBOL, LABEL = "#1B1B1B", "#1F2A44", "#2E3440"


class Track:
    def __init__(self, ax, y, sym=9.0, desc=6.0, title=7.2, lw=2.2):
        self.ax, self.y, self.sym, self.desc, self.title_size, self.lw = ax, y, sym, desc, title, lw

    def text(self, x, y, s, size, color=INK, weight="normal", ha="center", va="center", **kw):
        return self.ax.text(x, y, s, fontsize=size, color=color, fontweight=weight, ha=ha, va=va, family=SERIF,
                            math_fontfamily=MATH, zorder=6, **kw)

    def title(self, x, s, color=INK, dy=16.8):
        self.text(x, self.y + dy, s, self.title_size, color, weight="bold", va="bottom")

    def seg(self, x0, x1, color):
        self.ax.plot([x0, x1], [self.y, self.y], color=color, lw=self.lw, solid_capstyle="round", zorder=2)

    def chevron(self, x, color="white"):
        """A small direction mark drawn on the line."""
        self.ax.annotate("", xy=(x + 1.6, self.y), xytext=(x, self.y), zorder=3,
                         arrowprops=dict(arrowstyle="-|>", lw=0, color=color, mutation_scale=6, shrinkA=0, shrinkB=0))

    def band(self, x0, x1, fill, title=None, title_color=INK, below=12.5, height=25.5, r=6.0, alpha=0.75):
        self.ax.add_patch(FancyBboxPatch((x0, self.y - below), x1 - x0, height,
                                         boxstyle="round,pad=0,rounding_size=%.1f" % r,
                                         facecolor=fill, edgecolor="none", alpha=alpha, zorder=0))
        if title:
            self.title((x0 + x1) / 2, title, title_color)

    def station(self, x, sym, desc, ring, r=1.35):
        self.ax.add_patch(Circle((x, self.y), r, facecolor="white", edgecolor=ring, lw=1.1, zorder=4))
        self.text(x, self.y + 4.6, sym, self.sym, SYMBOL, va="bottom")
        if desc:
            self.text(x, self.y - 3.4, desc, self.desc, LABEL, va="top", linespacing=1.15)

    def gate(self, x, cond, color=INK):
        self.ax.add_patch(Circle((x, self.y), 0.95, facecolor=color, edgecolor="white", lw=0.6, zorder=5))
        self.text(x, self.y + 4.6, cond, self.sym - 0.8, color, va="bottom")

    def branch(self, x0, x1, y1, color, cond, verdict, note, text_color=None):
        tc = text_color or color
        p = Path([(x0, self.y), (x0 + 0.55 * (x1 - x0), self.y), (x1 - 0.2 * (x1 - x0), y1), (x1, y1)],
                 [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
        self.ax.add_patch(PathPatch(p, facecolor="none", edgecolor=color, lw=1.5, capstyle="round", zorder=1))
        self.ax.add_patch(Circle((x1, y1), 1.25, facecolor=color, edgecolor="white", lw=0.6, zorder=5))
        self.text(x0 + 0.62 * (x1 - x0) - 1.0, (self.y + y1) / 2 - 0.4, cond, self.sym - 1.4, tc, ha="right")
        self.text(x1 + 2.4, y1 + 0.9, verdict, self.desc + 0.6, tc, weight="bold", ha="left", va="bottom")
        self.text(x1 + 2.4, y1 - 0.4, note, self.desc - 0.4, LABEL, ha="left", va="top")

    def terminal(self, x, color, check=True, r=2.1, desc=None):
        self.ax.add_patch(Circle((x, self.y), r, facecolor=color, edgecolor="white", lw=0.8, zorder=5))
        if check:
            self.ax.plot([x - 0.45 * r, x - 0.1 * r, x + 0.48 * r], [self.y + 0.02 * r, self.y - 0.36 * r, self.y + 0.4 * r],
                         color="white", lw=1.1, solid_capstyle="round", solid_joinstyle="round", zorder=6)
        if desc:
            self.text(x, self.y - 3.6, desc, self.desc, LABEL, va="top", linespacing=1.15)
