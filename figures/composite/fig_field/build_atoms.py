"""Atomic-scale illustration assets for Fig. 2a, rendered in OVITO (Tachyon, ambient occlusion, transparent PNG).

Illustrations, not computed geometries: a stepped fcc(211) metal surface with the step-edge sites marked and N* in
the step hollow, and a truncated-octahedral metal particle on an oxide support.

    render-venv/python build_atoms.py [out_dir]
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "assets")
sys.path.insert(0, os.path.join(HERE, "..", "fig1"))
from build_structures import fcc211, probe_site  # noqa: E402

METAL_LT, METAL_DK = "#B9C0CC", "#5F6675"
SITE, N_COL = "#D9A93A", "#3A55C8"
SUP_O, SUP_M = "#E2D6C2", "#B9A47F"
SEED = 20261021


def rgb(h):
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)])


def camera_dir(elev, azim):
    e, a = math.radians(elev), math.radians(azim)
    return np.array([math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), -math.sin(e)])


def render(P, radii, colors, png, elev, azim, size):
    from ovito.data import DataCollection, Particles, SimulationCell
    from ovito.pipeline import Pipeline, StaticSource
    from ovito.vis import TachyonRenderer, Viewport

    data = DataCollection()
    cell = SimulationCell(pbc=(False, False, False))
    lo, hi = P.min(axis=0) - 5.0, P.max(axis=0) + 5.0
    cell[...] = [[hi[0] - lo[0], 0, 0, lo[0]], [0, hi[1] - lo[1], 0, lo[1]], [0, 0, hi[2] - lo[2], lo[2]]]
    cell.vis.enabled = False
    data.objects.append(cell)
    parts = Particles(count=len(P))
    parts.create_property("Position", data=P)
    parts.create_property("Radius", data=radii)
    parts.create_property("Color", data=np.clip(colors, 0, 1))
    data.objects.append(parts)
    pipe = Pipeline(source=StaticSource(data=data))
    pipe.add_to_scene()
    d = camera_dir(elev, azim)
    vp = Viewport(type=Viewport.Type.Ortho, camera_dir=tuple(d), camera_pos=tuple(P.mean(axis=0) - d * 200.0))
    vp.zoom_all(size=size)
    vp.render_image(size=size, filename=png, background=(1.0, 1.0, 1.0), alpha=True,
                    renderer=TachyonRenderer(ambient_occlusion=True, ambient_occlusion_brightness=0.7,
                                             shadows=False, direct_light_intensity=0.9, antialiasing_samples=24))
    pipe.remove_from_scene()
    print("wrote", png, len(P))


def height_colour(z, lo=METAL_DK, hi=METAL_LT, gamma=0.8):
    t = (z - z.min()) / max(z.max() - z.min(), 1e-9)
    return rgb(lo)[None, :] + (rgb(hi) - rgb(lo))[None, :] * t[:, None] ** gamma


def surface():
    d = 2.65
    P = fcc211(d, along=10, steps=4, layers=3)
    col = height_colour(P[:, 2])
    n_pos, _ = probe_site(P, d)
    top = P[:, 2] > -0.05
    y_edge = P[top][np.argmin(np.abs(P[top][:, 1] - n_pos[1])), 1]
    edge = top & (np.abs(P[:, 1] - y_edge) < 0.3) & (np.abs(P[:, 0] - n_pos[0]) < 1.6 * d)
    col[edge] = rgb(SITE)
    P = np.vstack([P, n_pos])
    col = np.vstack([col, rgb(N_COL)])
    radii = np.r_[np.full(len(P) - 1, 1.24), 0.9]
    render(P, radii, col, os.path.join(OUT, "surface.png"), elev=40, azim=158, size=(1600, 1200))


def nanoparticle(rng):
    d = 2.65
    a = d * math.sqrt(2.0)
    basis = np.array([[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]]) * a
    g = np.array([[i, j, k] for i in range(-6, 7) for j in range(-6, 7) for k in range(-6, 7)]) * a
    C = (g[:, None, :] + basis[None, :, :]).reshape(-1, 3)
    r = 10.0
    C = C[(np.abs(C).sum(axis=1) <= 1.5 * r) & (np.abs(C).max(axis=1) <= r)]
    C = C[C[:, 2] >= -0.35 * r]
    C[:, 2] -= C[:, 2].min()
    col_c = height_colour(np.linalg.norm(C - [0, 0, C[:, 2].mean() * 0.6], axis=1))
    ss = 2.4
    xs = np.arange(-21, 21.1, ss)
    S = np.array([[x, y, -2.1 - k * ss] for x in xs for y in xs for k in range(4)
                  if math.hypot(x, y) < 21.5 - 1.5 * k])
    S += rng.normal(0, 0.1, S.shape)
    is_o = ((np.round(S[:, 0] / ss) + np.round(S[:, 1] / ss) + np.round(S[:, 2] / ss)) % 2 == 0)
    col_s = np.where(is_o[:, None], rgb(SUP_O)[None, :], rgb(SUP_M)[None, :]) + rng.uniform(-0.025, 0.025,
                                                                                               (len(S), 1))
    P = np.vstack([C, S])
    radii = np.r_[np.full(len(C), 1.26), np.where(is_o, 1.32, 0.86)]
    render(P, radii, np.vstack([col_c, col_s]), os.path.join(OUT, "nanoparticle.png"), elev=26, azim=152,
           size=(1600, 1200))


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(SEED)
    if 'nano' not in sys.argv[2:]:
        surface()
    if 'surf' not in sys.argv[2:]:
        nanoparticle(rng)


if __name__ == "__main__":
    main()
