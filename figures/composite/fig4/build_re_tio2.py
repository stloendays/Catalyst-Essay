"""Re/TiO2 at 1 and 5 wt% Re, schematic surfaces rendered in OVITO.

Support: stoichiometric rutile TiO2(110), three O-Ti2O2-O trilayers with the bridging-O
rows on top (a = 4.594 A, c = 2.959 A, u = 0.3053). Re: compact hcp clusters
(a = 2.761 A, c = 4.456 A) placed on the surface. The two surfaces carry Re atoms in the
ratio 1 : 5, and the higher loading is drawn as fewer isolated atoms and larger clusters
("Re loading sets dispersion", D01 case file). Cluster sizes are illustrative, not
characterization data.

    render-venv/python build_re_tio2.py [out_dir]
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "renders")
A, C, U = 4.594, 2.959, 0.3053
HALF_X, HALF_Y = 30.0, 16.0            # slab half-widths along [1-10] and [001], A
COL = {"Ti": "#9DACCB", "O": "#DADADA", "Re": "#3E4452"}
RAD = {"Ti": 1.02, "O": 0.86, "Re": 1.30}
LOADINGS = {  # cluster sizes; totals 12 and 60 Re atoms
    "1wt": [1, 1, 1, 1, 2, 2, 4],
    "5wt": [19, 16, 13, 1, 1, 1, 1, 2, 2, 4],
}
VIEW_ELEV, VIEW_AZIM = 38.0, 180.0
SIZE = (1600, 800)


def hex_rgb(h):
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)])


def rutile_110():
    basis = [("Ti", (0, 0, 0)), ("Ti", (.5, .5, .5)),
             ("O", (U, U, 0)), ("O", (1 - U, 1 - U, 0)), ("O", (.5 + U, .5 - U, .5)), ("O", (.5 - U, .5 + U, .5))]
    lat = np.diag([A, A, C])
    ex = np.array([1.0, -1.0, 0.0]) / math.sqrt(2.0)
    ez = np.array([1.0, 1.0, 0.0]) / math.sqrt(2.0)
    ey = np.array([0.0, 0.0, 1.0])
    sym, pos = [], []
    n = 16
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            for k in range(-8, 9):
                for s, f in basis:
                    r = (np.array([i, j, k]) + np.array(f)) @ lat
                    sym.append(s)
                    pos.append([r @ ex, r @ ey, r @ ez])
    sym, P = np.array(sym), np.array(pos)
    d110 = A / math.sqrt(2.0)
    z_top = 0.0                                    # a Ti2O2 plane
    keep = (P[:, 2] <= z_top + 1.4) & (P[:, 2] >= z_top - 2 * d110 - 1.4)
    keep &= (np.abs(P[:, 0]) <= HALF_X) & (np.abs(P[:, 1]) <= HALF_Y)
    return sym[keep], P[keep]


def hcp_cluster(n):
    a, c = 2.761, 4.456
    pts = []
    for i in range(-4, 5):
        for j in range(-4, 5):
            for layer in range(0, 4):
                x = a * (i + 0.5 * j) + (a / 2.0 if layer % 2 else 0.0)
                y = a * (math.sqrt(3.0) / 2.0) * j + (a / (2.0 * math.sqrt(3.0)) if layer % 2 else 0.0)
                pts.append([x, y, layer * c / 2.0])
    pts = np.array(pts)
    d = np.linalg.norm(pts - np.array([0.0, 0.0, -1.6]), axis=1)   # a dome resting on its base layer
    return pts[np.argsort(d, kind="stable")[:n]]


def decorate(sym, P, sizes, rng):
    top_o = P[sym == "O", 2].max()
    placed, out = [], []
    for n in sorted(sizes, reverse=True):
        cl = hcp_cluster(n)
        r_cl = np.max(np.hypot(cl[:, 0], cl[:, 1])) + 1.4
        for _ in range(2000):
            cx, cy = rng.uniform(-HALF_X + r_cl + 2, HALF_X - r_cl - 2), rng.uniform(-HALF_Y + r_cl + 3, HALF_Y - r_cl - 6)
            if all(math.hypot(cx - px, cy - py) > r_cl + pr + 2.5 for px, py, pr in placed):
                break
        th = rng.uniform(0, 2 * math.pi)
        rot = np.array([[math.cos(th), -math.sin(th), 0], [math.sin(th), math.cos(th), 0], [0, 0, 1]])
        out.append(cl @ rot.T + np.array([cx, cy, top_o + 1.9]))
        placed.append((cx, cy, r_cl))
    return np.vstack(out)


def camera(elev=VIEW_ELEV, azim=VIEW_AZIM):
    e, az = math.radians(elev), math.radians(azim)
    d = np.array([math.sin(az) * math.cos(e), math.cos(az) * math.cos(e), -math.sin(e)])
    right = np.cross(d, [0.0, 0.0, 1.0])
    right /= np.linalg.norm(right)
    return d, right, np.cross(right, d)


def frame(P, margin=1.04):
    """Half-height of the ortho view that holds every atom, and the view centre."""
    d, right, up = camera()
    xr, yu = P @ right, P @ up
    half_w = (xr.max() - xr.min()) / 2.0 + 1.5
    half_h = (yu.max() - yu.min()) / 2.0 + 1.5
    centre = ((xr.max() + xr.min()) / 2.0) * right + ((yu.max() + yu.min()) / 2.0) * up + (P @ d).mean() * d
    return max(half_h, half_w * SIZE[1] / SIZE[0]) * margin, centre


def render(sym, P, png, fov, centre):
    from ovito.data import DataCollection, Particles, SimulationCell
    from ovito.pipeline import Pipeline, StaticSource
    from ovito.vis import TachyonRenderer, Viewport

    data = DataCollection()
    cell = SimulationCell(pbc=(False, False, False))
    lo, hi = P.min(axis=0) - 2.0, P.max(axis=0) + 2.0
    cell[...] = [[hi[0] - lo[0], 0, 0, lo[0]], [0, hi[1] - lo[1], 0, lo[1]], [0, 0, hi[2] - lo[2], lo[2]]]
    cell.vis.enabled = False
    data.objects.append(cell)
    parts = Particles(count=len(P))
    parts.create_property("Position", data=P)
    parts.create_property("Radius", data=np.array([RAD[s] for s in sym]))
    zmin, zmax = P[sym != "Re", 2].min(), P[sym != "Re", 2].max()
    cols = []
    for s, z in zip(sym, P[:, 2]):
        c = hex_rgb(COL[s])
        if s != "Re":                                   # deeper atoms slightly darker, so the rows read
            t = (z - zmin) / max(zmax - zmin, 1e-9)
            c = c * (0.78 + 0.22 * t)
        cols.append(c)
    parts.create_property("Color", data=np.array(cols))
    data.objects.append(parts)
    pipe = Pipeline(source=StaticSource(data=data))
    pipe.add_to_scene()
    d = camera()[0]
    vp = Viewport(type=Viewport.Type.Ortho, camera_dir=tuple(d), camera_pos=tuple(centre - d * 120.0), fov=fov)
    vp.render_image(size=SIZE, filename=png, background=(1.0, 1.0, 1.0), alpha=True,
                    renderer=TachyonRenderer(ambient_occlusion=True, ambient_occlusion_brightness=0.8,
                                             shadows=False, direct_light_intensity=1.0, antialiasing_samples=16))
    pipe.remove_from_scene()


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(20260923)
    sym0, P0 = rutile_110()
    counts = {k: sum(v) for k, v in LOADINGS.items()}
    assert counts == {"1wt": 12, "5wt": 60}
    built = {}
    for tag, sizes in LOADINGS.items():
        re = decorate(sym0, P0, sizes, rng)
        built[tag] = (np.concatenate([sym0, np.array(["Re"] * len(re))]), np.vstack([P0, re]))
    fov, centre = frame(built["5wt"][1])                # one camera for both, so they compare directly
    for tag, sizes in LOADINGS.items():
        sym, P = built[tag]
        re = P[len(P0):]
        render(sym, P, os.path.join(OUT, "ReTiO2_%s.png" % tag), fov, centre)
        print("%s: %d support atoms, %d Re in %d species" % (tag, len(P0), len(re), len(sizes)))


if __name__ == "__main__":
    main()
