"""Au nanoparticles of 2, 3, 4, 5 and 6 nm on TiO2, to scale, rendered in OVITO.

The rank-preservation control compares Au/TiO2 CO-oxidation catalysts that differ only in
Au particle diameter. Each particle is an fcc Au (a = 4.078 A) truncated octahedron with a
(111) base, flattened where it meets a stoichiometric rutile TiO2(110) support; all five
share one support and one camera, so their sizes compare directly. Particle shapes are
illustrative, not characterization data.

    render-venv/python build_au_tio2.py [out_dir]
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "renders")
A_AU = 4.078
A, C, U = 4.594, 2.959, 0.3053                      # rutile
DIAMETERS = [2.0, 3.0, 4.0, 5.0, 6.0]                # nm
GAP = 26.0                                           # A between particle edges
COL = {"Ti": "#9DACCB", "O": "#DADADA", "Au": "#D6B25A"}
RAD = {"Ti": 1.02, "O": 0.86, "Au": 1.44}
ELEV, AZIM = 22.0, 0.0
SIZE = (3600, 900)


def hex_rgb(h):
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)])


def au_particle(d_nm):
    """fcc Au cut to a truncated octahedron about d wide (atom centres plus radii), [111] along z,
    flat base."""
    R = 10.0 * d_nm / 2.0
    n = int(R / A_AU) + 3
    base = np.array([[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]])
    g = np.array([[i, j, k] for i in range(-n, n + 1) for j in range(-n, n + 1) for k in range(-n, n + 1)])
    P = ((g[:, None, :] + base[None, :, :]).reshape(-1, 3)) * A_AU
    s111, s100 = 1.52 * R, 0.96 * R
    keep = (np.abs(P).sum(axis=1) <= s111) & (np.abs(P).max(axis=1) <= s100)
    P = P[keep]
    e1 = np.array([1.0, -1.0, 0.0]) / math.sqrt(2.0)
    e2 = np.array([1.0, 1.0, -2.0]) / math.sqrt(6.0)
    e3 = np.array([1.0, 1.0, 1.0]) / math.sqrt(3.0)
    Q = np.stack([P @ e1, P @ e2, P @ e3], axis=1)
    layer = A_AU / math.sqrt(3.0)                   # (111) interlayer spacing
    zcut = -0.42 * R
    Q = Q[Q[:, 2] >= zcut - 1e-6]
    Q[:, 2] -= Q[:, 2].min()
    width = Q[:, 0].max() - Q[:, 0].min()
    return Q, width, layer


def rutile_110(x0, x1, y0, y1):
    basis = [("Ti", (0, 0, 0)), ("Ti", (.5, .5, .5)),
             ("O", (U, U, 0)), ("O", (1 - U, 1 - U, 0)), ("O", (.5 + U, .5 - U, .5)), ("O", (.5 - U, .5 + U, .5))]
    lat = np.diag([A, A, C])
    ex = np.array([1.0, -1.0, 0.0]) / math.sqrt(2.0)
    ez = np.array([1.0, 1.0, 0.0]) / math.sqrt(2.0)
    ey = np.array([0.0, 0.0, 1.0])
    # lattice ranges that cover the requested window
    span = max(abs(x0), abs(x1)) / (A / math.sqrt(2.0)) + 4
    n = int(span)
    kk = int(max(abs(y0), abs(y1)) / C) + 2
    sym, pos = [], []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            if abs(i + j) > 4:                       # only the three trilayers nearest the surface plane
                continue
            for k in range(-kk, kk + 1):
                for s, f in basis:
                    r = (np.array([i, j, k]) + np.array(f)) @ lat
                    sym.append(s)
                    pos.append([r @ ex, r @ ey, r @ ez])
    sym, P = np.array(sym), np.array(pos)
    d110 = A / math.sqrt(2.0)
    keep = (P[:, 2] <= 1.4) & (P[:, 2] >= -2 * d110 - 1.4)
    keep &= (P[:, 0] >= x0) & (P[:, 0] <= x1) & (P[:, 1] >= y0) & (P[:, 1] <= y1)
    return sym[keep], P[keep]


def main():
    from ovito.data import DataCollection, Particles, SimulationCell
    from ovito.pipeline import Pipeline, StaticSource
    from ovito.vis import TachyonRenderer, Viewport

    os.makedirs(OUT, exist_ok=True)
    parts, centres, x = [], [], 0.0
    for d in DIAMETERS:
        Q, w, _ = au_particle(d)
        cx = x + w / 2.0
        centres.append(cx)
        parts.append(Q + np.array([cx, 0.0, 0.0]))
        x += w + GAP
    x_end = x - GAP
    sym_s, S = rutile_110(-GAP, x_end + GAP, -38.0, 38.0)
    top_o = S[sym_s == "O", 2].max()
    au = np.vstack([p + np.array([0.0, 0.0, top_o + 2.3]) for p in parts])
    sym = np.concatenate([sym_s, np.array(["Au"] * len(au))])
    P = np.vstack([S, au])

    data = DataCollection()
    cell = SimulationCell(pbc=(False, False, False))
    lo, hi = P.min(axis=0) - 2.0, P.max(axis=0) + 2.0
    cell[...] = [[hi[0] - lo[0], 0, 0, lo[0]], [0, hi[1] - lo[1], 0, lo[1]], [0, 0, hi[2] - lo[2], lo[2]]]
    cell.vis.enabled = False
    data.objects.append(cell)
    pp = Particles(count=len(P))
    pp.create_property("Position", data=P)
    pp.create_property("Radius", data=np.array([RAD[s] for s in sym]))
    zmin, zmax = S[:, 2].min(), S[:, 2].max()
    cols = []
    for s, z in zip(sym, P[:, 2]):
        c = hex_rgb(COL[s])
        if s != "Au":
            c = c * (0.78 + 0.22 * (z - zmin) / max(zmax - zmin, 1e-9))
        cols.append(c)
    pp.create_property("Color", data=np.array(cols))
    data.objects.append(pp)
    pipe = Pipeline(source=StaticSource(data=data))
    pipe.add_to_scene()

    e, az = math.radians(ELEV), math.radians(AZIM)
    dvec = np.array([math.sin(az) * math.cos(e), math.cos(az) * math.cos(e), -math.sin(e)])
    right = np.cross(dvec, [0.0, 0.0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, dvec)
    xr, yu = P @ right, P @ up
    half_w = (xr.max() - xr.min()) / 2.0 + 2.0
    half_h = (yu.max() - yu.min()) / 2.0 + 2.0
    fov = max(half_h, half_w * SIZE[1] / SIZE[0]) * 1.02
    centre = ((xr.max() + xr.min()) / 2.0) * right + ((yu.max() + yu.min()) / 2.0) * up + (P @ dvec).mean() * dvec
    vp = Viewport(type=Viewport.Type.Ortho, camera_dir=tuple(dvec), camera_pos=tuple(centre - dvec * 300.0), fov=fov)
    png = os.path.join(OUT, "Au_TiO2_2to6nm.png")
    vp.render_image(size=SIZE, filename=png, background=(1.0, 1.0, 1.0), alpha=True,
                    renderer=TachyonRenderer(ambient_occlusion=True, ambient_occlusion_brightness=0.8,
                                             shadows=False, direct_light_intensity=1.0, antialiasing_samples=16))
    pipe.remove_from_scene()
    # where each particle centre lands in the image, for labelling
    px_per_A = SIZE[1] / (2.0 * fov)
    cx_img = [SIZE[0] / 2.0 + (np.array([cc, 0.0, 0.0]) @ right - (xr.max() + xr.min()) / 2.0) * px_per_A
              for cc in centres]
    meta = {"diameters_nm": DIAMETERS, "au_atoms": [int(len(p)) for p in parts], "support_atoms": int(len(S)),
            "image_px": SIZE, "centre_x_px": cx_img, "px_per_A": px_per_A}
    with open(os.path.join(OUT, "Au_TiO2_2to6nm.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(meta, fh, indent=1)
    print("Au atoms per particle:", meta["au_atoms"], "support atoms:", len(S))


if __name__ == "__main__":
    main()
