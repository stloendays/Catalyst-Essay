"""V3.6 hybrid harness as a metro-map track (16:9 slide, Chinese).

Claim: the agent makes the choices and records the evidence; every number comes from the fixed core or a registered tool;
a module the agent writes itself is used only after it passes the sandbox checks.
Source: docs/V36_HYBRID_HARNESS.md (sections 2, 4, 5, 8); GPT V3.5 proposal (five layers, interface contracts, registry).
Run: D:/Tools/pur_bridge_env/Scripts/python.exe make_v36_harness.py
"""
import os

from matplotlib.patches import Circle, FancyBboxPatch, PathPatch
from matplotlib.path import Path

import layout
import style
import track

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = ["Microsoft YaHei", "Arial"]
track.SERIF = FONT
INK, LABEL = "#1B1B1B", "#2E3440"
G, GD = style.FE, style.DARK_G          # evidence / decision: green family
B, BD = style.RU, style.DARK_B          # model building / execution: blue family
AMB, AMBD = "#E8AE5E", "#8A5638"        # feedback: warm
RED = "#D9474F"
NAVY, BLUE, GREEN = "#304C86", "#5677B5", "#6E9F60"

W, H = 338.7, 190.5
pg = style.Page(W, H)
cv = pg.canvas(0, 0, W, H)


def txt(x, y, s, size=12, color=INK, weight="normal", ha="center", va="center", **kw):
    return cv.text(x, y, s, fontsize=size, color=color, fontweight=weight, ha=ha, va=va, family=FONT, zorder=7, **kw)


txt(12, 181, "AI 负责选择和证据，数值由固定核心或登记工具计算；AI 新写的模块先过沙箱才能用", 19, weight="bold", ha="left")

# ---------------- main track: five layers
y = 141
tr = track.Track(cv, y=y, sym=13, desc=12, title=14, lw=3.0)
bands = [(10, 66, style.TINT_G, "① 证据", GD), (70, 120, "#DCE7D6", "② 决策", GD), (124, 190, style.TINT_B, "③ 建模", BD),
         (194, 290, "#D9DFEC", "④ 确定性执行与验证", BD), (294, 332, "#F6E7D2", "⑤ 反馈与报告", AMBD)]
for x0, x1, fill, title, tc in bands:
    tr.band(x0, x1, fill, title, tc, below=17, height=40, r=6, alpha=0.85)
for x0, x1, c in ((14, 68, GD), (68, 122, GD), (122, 192, BD), (192, 292, BD), (292, 318, AMBD)):
    tr.seg(x0, x1, c)
for x in (60, 113, 185, 285):
    tr.chevron(x)

tr.station(24, "检索抽取", "文献 → 记录", GD)
tr.station(50, "来源记录", "每个数\n可追溯", GD)
tr.station(84, "备选方案", "≥2 个，\n附计算值", GD)
tr.station(106, "工作流", "rev n", GD)
tr.station(138, "界区", "basis", BD)
tr.station(156, "流程图", "先画后算", BD)
tr.station(176, "model.py", "只做组合\ncomputed_by", BD)
tr.gate(204, "接口契约", RED)
tr.gate(228, "物理门控", RED)
tr.station(252, "设计优化", "连续变量\n程序优化", BD)
tr.station(276, "独立审查", "只看工程", BD)
tr.station(302, "人工检查", "", AMBD)
tr.terminal(320, AMBD, check=True, desc="报告")

# BLOCK -> replan loop under the track, back to the workflow station (new revision, old kept)
yl = 111
for xg in (204, 228):
    p = Path([(xg, y), (xg, y - 12), (xg - 4, yl + 2), (xg - 10, yl)], [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
    cv.add_patch(PathPatch(p, facecolor="none", edgecolor=RED, lw=1.8, capstyle="round", zorder=1))
cv.plot([218, 116], [yl, yl], color=RED, lw=1.8, solid_capstyle="round", zorder=1)
p = Path([(116, yl), (108, yl), (106, yl + 6), (106, y - 2)], [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
cv.add_patch(PathPatch(p, facecolor="none", edgecolor=RED, lw=1.8, capstyle="round", zorder=1))
cv.annotate("", xy=(106, y - 2.2), xytext=(106, y - 6), zorder=3,
            arrowprops=dict(arrowstyle="-|>", lw=0, color=RED, mutation_scale=9, shrinkA=0, shrinkB=0))
txt(161, yl - 3.2, "阻断：按失败类别重新规划，生成 rev n+1，旧版本保留", 12, RED, weight="bold", va="top")
txt(161, yl - 9.6, "通过或警告则继续，警告写进报告", 12, LABEL, va="top")

# ---------------- three tool tiers
tiers = [(84, NAVY, "T0 固定核心", "只填参数，不能改",
          [(120, "单元库", "压缩·冷却·分离"), (160, "物性", "NIST 热力学"), (200, "物理门控", "守恒·平衡"),
           (240, "核算账", "能耗·投资"), (280, "留出拦截", "全程检查")]),
         (62, BLUE, "T1 登记工具", "自主选用，超范围给警告",
          [(120, "文献工具", "检索·OCR·抽取"), (160, "MKM", "微观动力学"), (200, "设计优化", "连续变量"),
           (240, "敏感性", "逐参数"), (280, "IDAES", "参考工厂校核")]),
         (40, GREEN, "T2 沙箱模块", "可以自己写，须先验证",
          [(120, "写模块", "附自带测试"), (160, "通用检查", "有限·单位·非负"), (200, "可用", "带警告"),
           (240, "人工批准", "")])]
for ty, c, name, rule, sts in tiers:
    txt(12, ty + 2.2, name, 14, c, weight="bold", ha="left", va="bottom")
    txt(12, ty + 0.6, rule, 12, LABEL, ha="left", va="top")
    x_end = 292 if ty != 40 else 240
    cv.plot([104, x_end], [ty, ty], color=c, lw=2.2, solid_capstyle="round", zorder=2)
    for x, s, d in sts:
        hollow = s == "IDAES"
        cv.add_patch(Circle((x, ty), 1.6, facecolor="white", edgecolor=c, lw=1.3, ls="--" if hollow else "-", zorder=4))
        txt(x, ty + 3.0, s + ("（待接入）" if hollow else ""), 12, c if not hollow else LABEL, weight="bold", va="bottom")
        if d:
            txt(x, ty - 3.0, d, 12, LABEL, va="top")
# promotion: T2 -> T1
p = Path([(240, 40), (256, 40), (258, 55), (258, 62)], [Path.MOVETO, Path.CURVE4, Path.CURVE4, Path.CURVE4])
cv.add_patch(PathPatch(p, facecolor="none", edgecolor=GREEN, lw=1.8, ls=(0, (3, 2)), capstyle="round", zorder=1))
cv.annotate("", xy=(258, 61.8), xytext=(258, 57), zorder=3,
            arrowprops=dict(arrowstyle="-|>", lw=0, color=GREEN, mutation_scale=9, shrinkA=0, shrinkB=0))
txt(262, 48, "晋升为登记工具", 12, GREEN, weight="bold", ha="left")

# calls from the main track into the tiers (thin dotted)
# the model.py drop is broken around the replan labels so it does not run through them
for x, y0, y1 in ((176, y - 15, 113), (176, 94, 44), (252, y - 15, 66), (24, y - 11, 66)):
    cv.plot([x, x], [y0, y1], color="#8C94A3", lw=0.9, ls=(0, (1.5, 1.8)), zorder=0)
txt(178, 118, "调用", 12, LABEL, ha="left")

# ---------------- governance strip
gy = 13
cv.plot([10, 330], [gy + 7, gy + 7], color="#C9CED8", lw=0.8, zorder=0)
items = ["分阶段工具", "事件日志", "哈希冻结", "费用账本", "留出隔离", "额度路由"]
txt(12, gy, "贯穿全程", 14, INK, weight="bold", ha="left")
for i, s in enumerate(items):
    x = 70 + i * 44
    txt(x, gy, s, 12, LABEL)
    if i:
        cv.plot([x - 22, x - 22], [gy - 3, gy + 3], color="#C9CED8", lw=0.8)

layout.audit(pg.fig)
pg.save(HERE, "V36_harness")
