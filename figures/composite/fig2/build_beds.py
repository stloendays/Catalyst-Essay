"""Catalyst beds drawn to scale at each case's optimum, rendered in OVITO.

Bed volume V comes from fig2_pressure_envelopes.csv (the case optimum). Each bed is a
cylinder with the converter's L/D = 3 (the vessel costing basis) filled with pellets of
one common, illustrative size, and all three are rendered with the same orthographic
camera and field of view so their sizes in the figure stay proportional.

    render-venv/python build_beds.py [out_dir]
"""
import csv
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "renders")
CASES = {"Fe": "#89AA7B", "Ru": "#7789B7", "Ru_at_Fe_price": "#7789B7"}
L_OVER_D = 3.0
PELLET_D = 0.06          # m, illustrative
ELEV = 16.0              # camera elevation above the horizontal, degrees
SIZE = (1200, 2000)


def hex_rgb(h):
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)])


def optimum_volumes():
    rows = list(csv.DictReader(open(os.path.join(HERE, "fig2_pressure_envelopes.csv"), encoding="utf-8")))
    out = {}
    for case in CASES:
        best = min((r for r in rows if r["case"] == case), key=lambda r: float(r["cost"]))
        out[case] = float(best["V_m3"])
    return out


def packed_cylinder(V, rng):
    """Jittered fcc packing of pellets clipped to a cylinder of volume V and L/D = 3."""
    D = (4.0 * V / (math.pi * L_OVER_D)) ** (1.0 / 3.0)
    L, R, d = L_OVER_D * D, D / 2.0, PELLET_D
    a = d * math.sqrt(2.0)
    nr, nz = int(R / a) + 2, int(L / a) + 2
    base = np.array([[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]])
    g = np.array([[i, j, k] for i in range(-nr, nr + 1) for j in range(-nr, nr + 1) for k in range(0, nz + 1)])
    P = ((g[:, None, :] + base[None, :, :]).reshape(-1, 3)) * a
    th = rng.uniform(0, 2 * math.pi)
    rot = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
    P = P @ rot.T + rng.normal(0.0, 0.05 * d, P.shape)
    keep = (np.hypot(P[:, 0], P[:, 1]) <= R - 0.45 * d) & (P[:, 2] >= 0.5 * d) & (P[:, 2] <= L - 0.5 * d)
    P = P[keep]
    P = P[rng.random(len(P)) > 0.06]            # a few vacancies so the surface is not crystalline
    return P, D, L


def render(P, png, color, fov, height, rng):
    from ovito.data import DataCollection, Particles, SimulationCell
    from ovito.pipeline import Pipeline, StaticSource
    from ovito.vis import TachyonRenderer, Viewport

    data = DataCollection()
    cell = SimulationCell(pbc=(False, False, False))
    lo, hi = P.min(axis=0) - 1.0, P.max(axis=0) + 1.0
    cell[...] = [[hi[0] - lo[0], 0, 0, lo[0]], [0, hi[1] - lo[1], 0, lo[1]], [0, 0, hi[2] - lo[2], lo[2]]]
    cell.vis.enabled = False
    data.objects.append(cell)
    parts = Particles(count=len(P))
    parts.create_property("Position", data=P)
    parts.create_property("Radius", data=np.full(len(P), 0.5 * PELLET_D))
    c = hex_rgb(color)
    shade = rng.uniform(-0.07, 0.07, (len(P), 1))
    parts.create_property("Color", data=np.clip(c + shade * (1.0 - c) + shade * c, 0, 1))
    data.objects.append(parts)
    pipe = Pipeline(source=StaticSource(data=data))
    pipe.add_to_scene()
    e = math.radians(ELEV)
    d = np.array([0.0, math.cos(e), -math.sin(e)])
    centre = np.array([0.0, 0.0, height / 2.0])
    vp = Viewport(type=Viewport.Type.Ortho, camera_dir=tuple(d), camera_pos=tuple(centre - d * 60.0), fov=fov)
    vp.render_image(size=SIZE, filename=png, background=(1.0, 1.0, 1.0), alpha=True,
                    renderer=TachyonRenderer(ambient_occlusion=True, ambient_occlusion_brightness=0.8,
                                             shadows=False, direct_light_intensity=0.95,
                                             antialiasing_samples=12))
    pipe.remove_from_scene()


def main():
    os.makedirs(OUT, exist_ok=True)
    vols = optimum_volumes()
    rng = np.random.default_rng(20260923)
    beds = {m: packed_cylinder(V, rng) for m, V in vols.items()}
    # one field of view for every render: the tallest bed, seen at ELEV, plus a margin
    Dm, Lm = max((b[1], b[2]) for b in beds.values())
    fov = 0.5 * (Lm * math.cos(math.radians(ELEV)) + Dm * math.sin(math.radians(ELEV))) * 1.08
    meta = {"fov_m": fov, "size_px": SIZE, "m_per_px": 2.0 * fov / SIZE[1], "pellet_d_m": PELLET_D,
            "L_over_D": L_OVER_D, "beds": {}}
    for m, (P, D, L) in beds.items():
        png = os.path.join(OUT, "bed_%s.png" % m)
        render(P, png, CASES[m], fov, L, rng)
        meta["beds"][m] = {"V_m3": vols[m], "D_m": D, "L_m": L, "pellets": int(len(P))}
        print("%-15s V %.4f m3  D %.3f m  L %.3f m  %d pellets" % (m, vols[m], D, L, len(P)))
    with open(os.path.join(OUT, "beds.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=1)


if __name__ == "__main__":
    main()
