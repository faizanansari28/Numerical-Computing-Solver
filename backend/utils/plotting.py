"""Matplotlib plots in the NUMERIQ dark theme.

Every numerical method returns a small "plot spec" dictionary, for example
    {"kind": "root", "f": <Expr>, "xs": [...], "root": 1.52}
and render(spec) turns it into a base64 PNG that the website shows in an <img>.
"""
import base64
import io

import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

BG = "#0C0C14"
PURPLE = "#8055FF"
BLUE = "#627BFF"
WHITE = "#E8E8F2"
GREY = "#A1A1AA"
GOLD = "#F5B85C"
GRID = "#23232F"
CMAP = LinearSegmentedColormap.from_list("numiq", ["#4B35B8", "#0C0C14", "#3556D6"])


def _new(width=8.4, height=4.7):
    fig = Figure(figsize=(width, height), dpi=130, facecolor=BG)
    ax = fig.add_subplot(111)
    _style(ax)
    return fig, ax


def _style(ax):
    ax.set_facecolor(BG)
    for side in ax.spines.values():
        side.set_color(GRID)
    ax.tick_params(colors=GREY, labelsize=8)
    ax.xaxis.label.set_color(GREY)
    ax.yaxis.label.set_color(GREY)
    ax.title.set_color(WHITE)
    ax.grid(True, color=GRID, linewidth=0.6, alpha=0.9)


def _legend(ax):
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        leg = ax.legend(loc="best", fontsize=8, facecolor="#12121C", edgecolor=GRID)
        for t in leg.get_texts():
            t.set_color(WHITE)


def _to_png(fig):
    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=BG)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _range(xs, pad=0.25, min_width=1.0):
    lo, hi = float(min(xs)), float(max(xs))
    width = max(hi - lo, min_width)
    return lo - pad * width, hi + pad * width


# ---------------------------------------------------------------- plot kinds
def _root(spec):
    fig, ax = _new()
    f, xs, root = spec["f"], spec["xs"], spec["root"]
    lo, hi = _range(list(xs) + [root])
    grid = np.linspace(lo, hi, 500)
    ax.plot(grid, f.vec(grid), color=PURPLE, lw=2, label=f"f(x) = {f.pretty()}")
    ax.axhline(0, color=GREY, lw=1)
    for k, (a, b) in enumerate(spec.get("brackets", [])[:6]):
        ax.axvspan(a, b, color=BLUE, alpha=0.10 if k else 0.18)
    for (p, q) in spec.get("lines", [])[:12]:
        ax.plot([p[0], q[0]], [p[1], q[1]], color=BLUE, lw=1, ls="--")
    pts = list(xs)
    ys = f.vec(np.array(pts))
    ax.scatter(pts, ys, s=22, color=WHITE, zorder=4, label="iterates")
    for i, (px, py) in enumerate(zip(pts[:8], ys[:8])):
        ax.annotate(str(i), (px, py), textcoords="offset points", xytext=(4, 6), color=GREY, fontsize=7)
    ax.scatter([root], [0], marker="*", s=170, color=GOLD, zorder=5, label=f"root ≈ {root:.6g}")
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    _legend(ax)
    return fig


def _fixedpoint(spec):
    fig, ax = _new()
    g, xs = spec["g"], spec["xs"]
    lo, hi = _range(xs, pad=0.4)
    grid = np.linspace(lo, hi, 400)
    ax.plot(grid, g.vec(grid), color=PURPLE, lw=2, label=f"y = g(x) = {g.pretty()}")
    ax.plot(grid, grid, color=GREY, lw=1.2, label="y = x")
    px, py = [xs[0]], [0.0]
    for x_old, x_new in zip(xs[:-1], xs[1:]):
        px += [x_old, x_new]
        py += [x_new, x_new]
    ax.plot(px[:60], py[:60], color=BLUE, lw=1.1, label="cobweb path")
    ax.scatter([xs[-1]], [xs[-1]], marker="*", s=170, color=GOLD, zorder=5, label=f"fixed point ≈ {xs[-1]:.6g}")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    _legend(ax)
    return fig


def _integration(spec):
    fig, ax = _new()
    f, a, b = spec["f"], spec["a"], spec["b"]
    pad = 0.08 * (b - a)
    grid = np.linspace(a - pad, b + pad, 500)
    ax.plot(grid, f.vec(grid), color=WHITE, lw=2, label=f"f(x) = {f.pretty()}", zorder=3)
    ax.axhline(0, color=GREY, lw=0.8)
    polys = spec.get("polys", [])
    if not polys:
        g2 = np.linspace(a, b, 300)
        ax.fill_between(g2, 0, f.vec(g2), color=PURPLE, alpha=0.22, label="area")
    for k, (px, py) in enumerate(polys):
        ax.fill(px, py, color=PURPLE, alpha=0.28, zorder=2, label="approximation" if k == 0 else None)
        ax.plot(px, py, color=BLUE, lw=0.9, zorder=2)
    nodes = spec.get("nodes", [])
    if nodes:
        nx, ny = zip(*nodes)
        ax.scatter(nx, ny, s=26, color=GOLD, zorder=5, label="nodes used")
        for x_, y_ in nodes:
            ax.plot([x_, x_], [0, y_], color=GOLD, lw=0.6, alpha=0.5)
    ax.set_xlabel("x")
    ax.set_ylabel("f(x)")
    _legend(ax)
    return fig


def _curves(spec):
    fig, ax = _new()
    colors = [PURPLE, BLUE, GOLD, "#5EEAD4", "#F472B6", WHITE]
    for k, c in enumerate(spec["curves"]):
        ax.plot(c["x"], c["y"], color=c.get("color", colors[k % len(colors)]), lw=c.get("lw", 2),
                ls=c.get("ls", "-"), label=c["label"])
    pts = spec.get("points")
    if pts:
        ax.scatter(pts["x"], pts["y"], s=46, color=GOLD, zorder=5, edgecolor=BG, label=pts.get("label", "data points"))
    hl = spec.get("highlight")
    if hl:
        ax.scatter([hl[0]], [hl[1]], marker="*", s=190, color=WHITE, zorder=6, label=hl[2])
    ax.set_xlabel(spec.get("xlabel", "x"))
    ax.set_ylabel(spec.get("ylabel", "y"))
    if spec.get("title"):
        ax.set_title(spec["title"], fontsize=10)
    _legend(ax)
    return fig


def _series(spec):
    fig, ax = _new()
    colors = [PURPLE, BLUE, GOLD, "#5EEAD4", "#F472B6", WHITE]
    for k, s in enumerate(spec["lines"]):
        y = np.array(s["y"], dtype=float)
        y = np.where(y > 0, y, np.nan) if spec.get("logy") else y
        ax.plot(s["x"], y, color=colors[k % len(colors)], lw=2, marker="o", ms=3.5, label=s["label"])
    if spec.get("logy"):
        ax.set_yscale("log")
    if spec.get("logx"):
        ax.set_xscale("log")
    ax.set_xlabel(spec.get("xlabel", "iteration"))
    ax.set_ylabel(spec.get("ylabel", "error"))
    if spec.get("title"):
        ax.set_title(spec["title"], fontsize=10)
    _legend(ax)
    return fig


def _contour(spec):
    fig, ax = _new(7.2, 5.2)
    f, path = spec["f"], np.array(spec["path"], dtype=float)
    lo_x, hi_x = _range(path[:, 0], 0.35, 2.0)
    lo_y, hi_y = _range(path[:, 1], 0.35, 2.0)
    gx, gy = np.meshgrid(np.linspace(lo_x, hi_x, 160), np.linspace(lo_y, hi_y, 160))
    z = f.vec(gx.ravel(), gy.ravel()).reshape(gx.shape)
    ax.contourf(gx, gy, z, levels=24, cmap=CMAP, alpha=0.9)
    ax.contour(gx, gy, z, levels=24, colors=GREY, linewidths=0.3, alpha=0.5)
    ax.plot(path[:, 0], path[:, 1], color=WHITE, lw=1.6, marker="o", ms=3, label="iterates")
    ax.scatter([path[0, 0]], [path[0, 1]], color=BLUE, s=60, zorder=5, label="start")
    ax.scatter([path[-1, 0]], [path[-1, 1]], marker="*", color=GOLD, s=200, zorder=6, label="end")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(False)
    _legend(ax)
    return fig


def _matrices(spec):
    items = spec["items"]
    fig = Figure(figsize=(3.4 * len(items) + 0.6, 3.9), dpi=130, facecolor=BG)
    for k, (title, mat) in enumerate(items):
        ax = fig.add_subplot(1, len(items), k + 1)
        m = np.array(mat, dtype=float)
        _style(ax)
        ax.grid(False)
        top = max(float(np.max(np.abs(m))), 1e-12)
        ax.imshow(m, cmap=CMAP, norm=TwoSlopeNorm(0, -top, top), aspect="equal")
        size = 9 if max(m.shape) <= 4 else 7 if max(m.shape) <= 7 else 5
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                ax.text(j, i, f"{m[i, j]:.3g}", ha="center", va="center", color=WHITE, fontsize=size)
        ax.set_title(title, fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
    return fig


def _bars(spec):
    fig, ax = _new()
    labels, values = spec["labels"], [float(v) for v in spec["values"]]
    colors = [PURPLE if i % 2 == 0 else BLUE for i in range(len(values))]
    ax.bar(labels, values, color=colors, edgecolor=BG)
    if spec.get("logy"):
        ax.set_yscale("log")
    ax.set_ylabel(spec.get("ylabel", ""))
    if spec.get("title"):
        ax.set_title(spec["title"], fontsize=10)
    ax.grid(axis="x", visible=False)
    return fig


def _bits(spec):
    sign, expo, mant = spec["sign"], spec["exponent"], spec["mantissa"]
    n = 1 + len(expo) + len(mant)
    fig = Figure(figsize=(10, 2.3), dpi=130, facecolor=BG)
    ax = fig.add_subplot(111)
    ax.set_facecolor(BG)
    ax.axis("off")
    groups = [(sign, PURPLE, "sign"), (expo, BLUE, "exponent"), (mant, "#4A4A5C", "mantissa (fraction)")]
    pos = 0
    for text, color, name in groups:
        for ch in text:
            ax.add_patch(Rectangle((pos + 0.05, 0.1), 0.9, 0.8, color=color, alpha=0.9 if ch == "1" else 0.35))
            ax.text(pos + 0.5, 0.5, ch, ha="center", va="center", color=WHITE, fontsize=6)
            pos += 1
        ax.text(pos - len(text) / 2, -0.15, name, ha="center", va="top", color=GREY, fontsize=8)
    ax.set_xlim(0, n)
    ax.set_ylim(-0.6, 1.1)
    return fig


KINDS = {
    "root": _root, "fixedpoint": _fixedpoint, "integration": _integration, "curves": _curves,
    "series": _series, "contour": _contour, "matrices": _matrices, "bars": _bars, "bits": _bits,
}


def render(spec):
    """plot spec -> base64 PNG string (or None if there is nothing to draw)."""
    if not spec:
        return None
    return _to_png(KINDS[spec["kind"]](spec))
