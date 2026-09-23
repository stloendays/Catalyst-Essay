"""Stepped (211) model surfaces with N* at the step, rendered in OVITO.

The NH3-FINAL-1.1 descriptor is the N formation energy at a step site
("S1 raw step_site"), so each metal is drawn as an fcc(211) step built with
that metal's own nearest-neighbour distance, with N* in the most-coordinated
hollow at the step edge. Illustrations of the site the descriptor refers to,
not relaxed geometries.

    render-venv/python build_structures.py [out_dir] [--views]
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = ARGS[0] if ARGS else os.path.join(HERE, "renders")
TRY_VIEWS = "--views" in sys.argv

NN = {"Ru": 2.65, "Os": 2.68, "Fe": 2.48}          # bulk nearest-neighbour distances, Å
COLOR = {"Ru": "#7789B7", "Os": "#9DACCB", "Fe": "#89AA7B", "N": "#2F4BD6"}
R_METAL, R_N = 1.20, 0.86
D_MN = 1.95                                          # N-metal contact distance, Å
VIEW = (48.0, 160.0)                                 # (elevation, azimuth) degrees
SIZE = (900, 700)


def shade(hex_color, t):
    """Height shading: t=1 (step edge) is the palette colour lifted toward white,
    t=0 (deepest atom) is it pulled toward a dark ink, so the steps read at once."""
    c = np.array(hex_rgb(hex_color))
    light = c + (1.0 - c) * 0.32
    dark = c * 0.60
    return tuple(dark + (light - dark) * (t ** 0.85))


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5))


def fcc211(d, along=6, steps=3, layers=3):
    """fcc(211) slab in a frame where z is the macroscopic surface normal, x runs
    along the close-packed step edge and y crosses the steps."""
    a = d * math.sqrt(2.0)
    nrm = np.array([2.0, 1.0, 1.0]) / math.sqrt(6.0)
    t = np.array([0.0, 1.0, -1.0]) / math.sqrt(2.0)
    u = np.cross(nrm, t)
    basis = np.array([[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]]) * a
    rng = range(-10, 11)
    pts = np.array([np.array([i, j, k]) * a + b for i in rng for j in rng for k in rng for b in basis])
    P = np.stack([pts @ t, pts @ u, pts @ nrm], axis=1)
    terrace = a * math.sqrt(6.0) / 2.0                   # step period of fcc(211) along y
    depth = layers * a / math.sqrt(6.0) * 2.2
    keep = (P[:, 2] <= 1e-6) & (P[:, 2] > -depth)
    keep &= (np.abs(P[:, 0]) <= (along - 1) * d / 2.0 + 1e-6)
    keep &= (np.abs(P[:, 1]) <= steps * terrace / 2.0 + 1e-6)
    return P[keep]


def probe_site(P, d):
    """Lower a probe sphere of radius D_MN onto the surface around the central step
    edge; keep the touching position with the most neighbours at contact."""
    edge = P[P[:, 2] > -0.05]
    y_edge = edge[np.argmin(np.abs(edge[:, 1])), 1]
    best, best_key = None, None
    for x in np.arange(-d, d + 1e-9, 0.04):
        for y in np.arange(y_edge - 1.6 * d, y_edge + 1.6 * d + 1e-9, 0.04):
            rho2 = (P[:, 0] - x) ** 2 + (P[:, 1] - y) ** 2
            near = rho2 < D_MN ** 2
            if not near.any():
                continue
            z = np.max(P[near, 2] + np.sqrt(D_MN ** 2 - rho2[near]))
            p = np.array([x, y, z])
            dist = np.linalg.norm(P - p, axis=1)
            coord = int(np.sum(dist < D_MN + 0.06))
            key = (coord, -abs(x) - 0.5 * abs(y - y_edge))
            if best_key is None or key > best_key:
                best, best_key = p, key
    return best, best_key[0]


def write_xyz(path, P, symbol, n_pos):
    lo, hi = P.min(axis=0) - 8.0, P.max(axis=0) + 8.0
    L = hi - lo
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("%d\n" % (len(P) + 1))
        fh.write('Lattice="%.4f 0 0 0 %.4f 0 0 0 %.4f" Origin="%.4f %.4f %.4f" '
                 'Properties=species:S:1:pos:R:3\n' % (L[0], L[1], L[2], lo[0], lo[1], lo[2]))
        for p in P:
            fh.write("%s %.5f %.5f %.5f\n" % (symbol, *p))
        fh.write("N %.5f %.5f %.5f\n" % tuple(n_pos))


def camera_dir(elev, azim):
    e, a = math.radians(elev), math.radians(azim)
    return np.array([math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), -math.sin(e)])


def render(xyz, png, metal, view=VIEW, size=SIZE, margin=1.10):
    from ovito.io import import_file
    from ovito.vis import TachyonRenderer, Viewport

    pipe = import_file(xyz)
    types = pipe.source.data.particles_.particle_types_
    for t in list(types.types):
        mt = types.make_mutable(t)
        mt.radius, mt.color = ((R_N, hex_rgb(COLOR["N"])) if t.name == "N"
                               else (R_METAL, hex_rgb(COLOR[metal])))
    pipe.source.data.cell.vis.enabled = False

    def height_colour(frame, data):
        # Runs at compute time, so the per-atom colour is what the renderer sees.
        parts = data.particles_
        p = np.asarray(parts.positions)
        n_id = [t.id for t in parts.particle_types.types if t.name == "N"][0]
        is_n = np.asarray(parts.particle_types) == n_id
        zm = p[~is_n, 2]
        tt = np.clip((p[:, 2] - zm.min()) / max(zm.max() - zm.min(), 1e-9), 0.0, 1.0)
        parts.create_property("Color", data=np.array(
            [hex_rgb(COLOR["N"]) if n else shade(COLOR[metal], v) for n, v in zip(is_n, tt)]))

    pipe.modifiers.append(height_colour)
    pipe.add_to_scene()

    pos = np.asarray(pipe.compute().particles.positions)
    d = camera_dir(*view)
    right = np.cross(d, [0.0, 0.0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, d)
    xr, yu = pos @ right, pos @ up
    cx, cy = (xr.min() + xr.max()) / 2.0, (yu.min() + yu.max()) / 2.0
    half_w = (xr.max() - xr.min()) / 2.0 + R_METAL
    half_h = (yu.max() - yu.min()) / 2.0 + R_METAL
    aspect = size[0] / size[1]
    fov = max(half_h, half_w / aspect) * margin
    centre = cx * right + cy * up + (pos @ d).mean() * d
    vp = Viewport(type=Viewport.Type.Ortho, camera_dir=tuple(d),
                  camera_pos=tuple(centre - d * 80.0), fov=fov)
    vp.render_image(size=size, filename=png, background=(1.0, 1.0, 1.0), alpha=True,
                    renderer=TachyonRenderer(ambient_occlusion=True, ambient_occlusion_brightness=0.75,
                                             shadows=False, direct_light_intensity=1.0,
                                             antialiasing_samples=16))
    pipe.remove_from_scene()


def main():
    os.makedirs(OUT, exist_ok=True)
    for m, d in NN.items():
        P = fcc211(d)
        n, coord = probe_site(P, d)
        dists = np.sort(np.linalg.norm(P - n, axis=1))
        xyz = os.path.join(OUT, "%s_211_N.xyz" % m)
        write_xyz(xyz, P, m, n)
        views = [(58.0, 200.0), (48.0, 160.0)] if TRY_VIEWS else [VIEW]
        for v in views:
            tag = "" if not TRY_VIEWS else "_az%d" % int(v[1])
            png = os.path.join(OUT, "%s_211_N%s.png" % (m, tag))
            render(xyz, png, m, view=v)
        print("%s: %d atoms, N at a %d-fold site, nearest contacts %s A (next %.2f)"
              % (m, len(P), coord, "/".join("%.2f" % x for x in dists[:coord]), dists[coord]))


if __name__ == "__main__":
    main()
