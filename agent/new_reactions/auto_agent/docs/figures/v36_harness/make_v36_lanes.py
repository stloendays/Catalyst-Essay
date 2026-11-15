"""One build, who does what: AI lane, program lane, human lane (16:9 slide, plain Chinese).

Claim: the AI chooses and assembles; the program computes and checks; a person approves. A calculation the library lacks
is written by the AI but enters the library only after it passes tests and a person agrees.
Source: docs/V36_HYBRID_HARNESS.md, docs/UO2_LIBRARY.md.
Run: D:/Tools/pur_bridge_env/Scripts/python.exe make_v36_lanes.py
"""
import os

from matplotlib.patches import Circle, FancyBboxPatch, PathPatch
from matplotlib.path import Path

import layout
import style

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = ["Microsoft YaHei", "Arial"]
INK, LABEL, GREY = "#1B1B1B", "#2E3440", "#6F7580"
AI_D, AI_T = "#467238", "#E9F0E4"       # green: AI
PR_D, PR_T = "#304C86", "#E6EAF3"       # blue: program
HU_D, HU_T = "#8A5638", "#F8EEDF"       # warm: person
RED = "#D9474F"

W, H = 338.7, 190.5
CUT = 25   # the drawing starts at y = 30; trim the empty strip below it
pg = style.Page(W, H - CUT)
cv = pg.canvas(0, -CUT, W, H)


def txt(x, y, s, size=12, color=INK, weight="normal", ha="center", va="center"):
    return cv.text(x, y, s, fontsize=size, color=color, fontweight=weight, ha=ha, va=va, family=FONT, zorder=7,
                   linespacing=1.25)


def path(points, color, lw=2.6, ls="-", z=2):
    codes = [Path.MOVETO] + [Path.CURVE4] * (len(points) - 1)
    cv.add_patch(PathPatch(Path(points, codes), facecolor="none", edgecolor=color, lw=lw, ls=ls, capstyle="round", zorder=z))


def head(x, y, dx, dy, color):
    cv.annotate("", xy=(x, y), xytext=(x - dx, y - dy), zorder=3,
                arrowprops=dict(arrowstyle="-|>", lw=0, color=color, mutation_scale=11, shrinkA=0, shrinkB=0))


def stop(x, y, name, note, dark):
    cv.add_patch(Circle((x, y), 2.2, facecolor="white", edgecolor=dark, lw=1.8, zorder=5))
    txt(x, y + 5.0, name, 14, dark, weight="bold", va="bottom")
    if note:
        txt(x, y - 4.6, note, 12, LABEL, va="top")


txt(12, 181, "一次建模里，谁做什么", 20, weight="bold", ha="left")

YA, YP, YH = 150, 112, 51
for (y0, y1), fill, dark, name, role in (((132, 168), AI_T, AI_D, "AI", "选择和拼装"),
                                         ((83, 127), PR_T, PR_D, "程序", "计算和检查"),
                                         ((30, 76), HU_T, HU_D, "人", "把关")):
    cv.add_patch(FancyBboxPatch((10, y0), 318, y1 - y0, boxstyle="round,pad=0,rounding_size=6",
                                facecolor=fill, edgecolor="none", zorder=0))
    txt(17, (y0 + y1) / 2 + 4, name, 18, dark, weight="bold", ha="left")
    txt(17, (y0 + y1) / 2 - 5, role, 12, LABEL, ha="left")

# the run: one line weaving AI -> program -> person
cv.plot([66, 142], [YA, YA], color=AI_D, lw=2.6, solid_capstyle="round", zorder=2)
path([(142, YA), (162, YA), (160, YP), (180, YP)], PR_D)
cv.plot([180, 290], [YP, YP], color=PR_D, lw=2.6, solid_capstyle="round", zorder=2)
path([(290, YP), (306, YP), (314, YH + 12), (314, YH)], HU_D)
stop(66, YA, "查文献", "抽出每个数据\n记下出处", AI_D)
stop(104, YA, "选工艺路线", "至少比较\n两种方案", AI_D)
stop(142, YA, "搭模型", "只用模块库\n里的计算拼装", AI_D)
stop(180, YP, "计算", "物料、能量\n设备、投资", PR_D)
stop(216, YP, "检查", "守恒、热力学\n上下游对得上", PR_D)
stop(252, YP, "优化", "压力、温度\n回收率", PR_D)
stop(290, YP, "复核", "另一个模型挑错\nIDAES 复算", PR_D)
cv.add_patch(Circle((314, YH), 3.0, facecolor=HU_D, edgecolor="white", lw=0.8, zorder=5))
cv.plot([312.6, 313.7, 315.6], [YH + 0.1, YH - 1.2, YH + 1.4], color="white", lw=1.4, solid_capstyle="round", zorder=6)
txt(314, YH - 5.2, "人工审核\n看过才出报告", 12, HU_D, va="top")

# a failing check goes back to the model
path([(216, YP + 2.4), (216, 129.5), (216, 129.5), (200, 129.5)], RED, lw=1.8, z=1)
cv.plot([200, 148], [129.5, 129.5], color=RED, lw=1.8, solid_capstyle="round", zorder=1)
path([(148, 129.5), (143, 129.5), (142, 131), (142, 133.6)], RED, lw=1.8, z=1)
head(142, 134.6, 0, 2.5, RED)
txt(182, 131, "不过关就退回改模型", 12, RED, weight="bold", va="bottom")

# the library sits in the empty left part of the program lane
txt(56, 119, "模块库：事先写好、逐个测过", 13, PR_D, weight="bold", ha="left")
txt(56, 109.5, "压缩机 · 泵 · 换热器 · 冷却 · 闪蒸分水", 12, LABEL, ha="left")
txt(56, 101, "反应器 · 膜分离 · 变压吸附 · 精馏 · 设备投资", 12, LABEL, ha="left")

# a calculation the library lacks, in the person lane: AI writes, tests run, a person agrees, then it joins the library
txt(56, 67, "库里没有的计算（例如一种新的分离设备）", 12, GREY, ha="left")
cv.plot([66, 170], [YH, YH], color=GREY, lw=2.0, ls=(0, (4, 2.5)), zorder=2)
for x, name, note, dark in ((66, "AI 写", "", AI_D), (116, "自动测试", "守恒、单位、极限情况", PR_D), (166, "人同意", "", HU_D)):
    cv.add_patch(Circle((x, YH), 2.0, facecolor="white", edgecolor=dark, lw=1.6, zorder=5))
    txt(x, YH + 4.4, name, 13, dark, weight="bold", va="bottom")
    if note:
        txt(x, YH - 4.2, note, 12, LABEL, va="top")
path([(168, YH), (186, YH), (186, 80), (150, 96)], GREY, lw=2.0, ls=(0, (4, 2.5)))
head(149.5, 96.3, -2.4, 1.1, GREY)
txt(190, 67, "才进模块库", 12, GREY, ha="left")

layout.audit(pg.fig)
pg.save(HERE, "V36_lanes")
