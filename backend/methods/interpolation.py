"""Interpolation: build a curve that passes EXACTLY through given data points.

Methods: Lagrange, Hermite, Natural Cubic Spline, Polynomial Approximation (Newton divided differences).
"""
import numpy as np
from scipy.interpolate import CubicHermiteSpline, CubicSpline, lagrange as scipy_lagrange

from utils.errors import NumericalError
from utils.inputs import field, g, get_expr, get_float, get_int, get_list, get_vector
from utils.results import answer, finish


# ===================================================== PART 1: ALGORITHMS
def check_points(xs, ys):
    if len(xs) != len(ys):
        raise NumericalError(f"You gave {len(xs)} x-values but {len(ys)} y-values. They must match.")
    if len(xs) < 2:
        raise NumericalError("At least 2 data points are needed.")
    if len(set(xs)) != len(xs):
        raise NumericalError("Two data points have the same x-value. An interpolating function needs distinct x-values.")


def sort_points(xs, ys, extra=None):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [[xs[i] for i in order], [ys[i] for i in order]]
    if extra is not None:
        out.append([extra[i] for i in order])
    return out


def lagrange_value(xs, ys, x):
    """Returns P(x) and the list of basis values L_k(x)."""
    n = len(xs)
    basis = []
    total = 0.0
    for k in range(n):
        L = 1.0
        for j in range(n):
            if j != k:
                L = L * (x - xs[j]) / (xs[k] - xs[j])
        basis.append(L)
        total += ys[k] * L
    return total, basis


def lagrange(xs, ys, xe):
    check_points(xs, ys)
    value, basis = lagrange_value(xs, ys, xe)
    rows = [[k, xs[k], ys[k], basis[k], ys[k] * basis[k]] for k in range(len(xs))]
    steps = [f"P(x) = Σ y_k · L_k(x), where L_k(x) = Π_(j≠k) (x - x_j)/(x_k - x_j). Degree = {len(xs) - 1}.",
             f"At x = {g(xe)} the basis values are " + ", ".join(f"L_{k} = {g(b)}" for k, b in enumerate(basis)) + ".",
             f"Sum of y_k · L_k = {g(value)}.",
             f"Check: the basis values add up to {g(sum(basis))} (they must always sum to 1)."]
    lo, hi = min(xs), max(xs)
    grid = np.linspace(lo - 0.05 * (hi - lo), hi + 0.05 * (hi - lo), 300)
    curve = [lagrange_value(xs, ys, float(t))[0] for t in grid]
    notes = []
    if xe < lo or xe > hi:
        notes.append("x lies outside the data range: this is EXTRAPOLATION and can be very inaccurate.")
    return {
        "answers": [answer(f"P({g(xe)})", value)], "steps": steps, "iterations": len(xs), "converged": None,
        "columns": ["k", "x_k", "y_k", f"L_k({g(xe)})", "y_k · L_k"], "rows": rows, "notes": notes,
        "plot": {"kind": "curves", "curves": [{"label": f"Lagrange polynomial (degree {len(xs) - 1})", "x": grid, "y": curve}],
                 "points": {"x": xs, "y": ys}, "highlight": (xe, value, f"P({g(xe)}) = {g(value)}")},
    }


def divided_differences(z, values):
    """Newton divided-difference table. Returns the table (list of columns)."""
    n = len(z)
    table = [list(values)]
    for level in range(1, n):
        prev = table[-1]
        col = []
        for i in range(n - level):
            col.append((prev[i + 1] - prev[i]) / (z[i + level] - z[i]))
        table.append(col)
    return table


def newton_form_value(z, coeffs, x):
    result = coeffs[-1]
    for k in range(len(coeffs) - 2, -1, -1):      # Horner-like evaluation
        result = result * (x - z[k]) + coeffs[k]
    return result


def hermite(xs, ys, dys, xe):
    check_points(xs, ys)
    if len(dys) != len(xs):
        raise NumericalError("You need one derivative value for every data point.")
    n = len(xs)
    z, q0 = [], []
    for i in range(n):
        z += [xs[i], xs[i]]
        q0 += [ys[i], ys[i]]
    m = 2 * n
    table = [q0]
    for level in range(1, m):
        col = []
        for i in range(m - level):
            if z[i + level] == z[i]:
                col.append(dys[i // 2])            # repeated node -> use the derivative
            else:
                col.append((table[-1][i + 1] - table[-1][i]) / (z[i + level] - z[i]))
        table.append(col)
    coeffs = [table[k][0] for k in range(m)]
    value = newton_form_value(z, coeffs, xe)
    rows = []
    for i in range(m):
        rows.append([z[i]] + [table[k][i] if i < len(table[k]) else "" for k in range(min(m, 4))])
    steps = ["Every node is listed twice (z_0 = z_1 = x_0, ...). For repeated nodes the first divided difference is the given derivative f'(x_i).",
             "Hermite polynomial: H(x) = f[z0] + f[z0,z1](x-z0) + f[z0,z1,z2](x-z0)(x-z1) + ...",
             "Top-edge divided differences (the coefficients): " + ", ".join(g(c, 6) for c in coeffs) + ".",
             f"Evaluating the polynomial at x = {g(xe)} gives H({g(xe)}) = {g(value)}."]
    lo, hi = min(xs), max(xs)
    grid = np.linspace(lo, hi, 300)
    curve = [newton_form_value(z, coeffs, float(t)) for t in grid]
    return {
        "answers": [answer(f"H({g(xe)})", value)], "steps": steps, "iterations": m, "converged": None,
        "columns": ["z", "f[z]", "f[z,z]", "2nd diff", "3rd diff"], "rows": rows,
        "table_title": "Divided-difference table (first 4 columns)",
        "notes": [f"The Hermite polynomial has degree {m - 1} and matches both values AND slopes at every node."],
        "plot": {"kind": "curves", "curves": [{"label": f"Hermite polynomial (degree {m - 1})", "x": grid, "y": curve}],
                 "points": {"x": xs, "y": ys}, "highlight": (xe, value, f"H({g(xe)}) = {g(value)}")},
        "extra": {"coeffs": coeffs},
    }


def solve_tridiagonal(lower, diag, upper, rhs):
    """Thomas algorithm for a tridiagonal system."""
    n = len(diag)
    d = diag[:]
    r = rhs[:]
    for i in range(1, n):
        factor = lower[i] / d[i - 1]
        d[i] = d[i] - factor * upper[i - 1]
        r[i] = r[i] - factor * r[i - 1]
    x = [0.0] * n
    x[n - 1] = r[n - 1] / d[n - 1]
    for i in range(n - 2, -1, -1):
        x[i] = (r[i] - upper[i] * x[i + 1]) / d[i]
    return x


def spline_second_derivatives(xs, ys):
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    M = [0.0] * n                                   # natural spline: M_0 = M_(n-1) = 0
    if n > 2:
        lower, diag, upper, rhs = [0.0], [], [], []
        for i in range(1, n - 1):
            lower.append(h[i - 1])
            diag.append(2 * (h[i - 1] + h[i]))
            upper.append(h[i])
            rhs.append(6 * ((ys[i + 1] - ys[i]) / h[i] - (ys[i] - ys[i - 1]) / h[i - 1]))
        inner = solve_tridiagonal(lower, diag, upper[:-1] + [0.0], rhs)
        for i in range(1, n - 1):
            M[i] = inner[i - 1]
    return M, h


def spline_value(xs, ys, M, h, x):
    i = 0
    while i < len(xs) - 2 and x > xs[i + 1]:
        i += 1
    a, b = xs[i + 1] - x, x - xs[i]
    return (M[i] * a ** 3 + M[i + 1] * b ** 3) / (6 * h[i]) + (ys[i] / h[i] - M[i] * h[i] / 6) * a + (ys[i + 1] / h[i] - M[i + 1] * h[i] / 6) * b


def cubic_spline(xs, ys, xe):
    check_points(xs, ys)
    M, h = spline_second_derivatives(xs, ys)
    value = spline_value(xs, ys, M, h, xe)
    rows = []
    for i in range(len(xs) - 1):
        a_i = ys[i]
        b_i = (ys[i + 1] - ys[i]) / h[i] - h[i] * (2 * M[i] + M[i + 1]) / 6
        c_i = M[i] / 2
        d_i = (M[i + 1] - M[i]) / (6 * h[i])
        rows.append([i, f"[{g(xs[i])}, {g(xs[i + 1])}]", a_i, b_i, c_i, d_i])
    steps = ["On each interval the spline is a cubic S_i(x) = a_i + b_i(x-x_i) + c_i(x-x_i)² + d_i(x-x_i)³.",
             "Conditions: S passes through all points, and S, S', S'' are continuous at interior knots. Natural ends: S''(x_0) = S''(x_n) = 0.",
             "Unknowns M_i = S''(x_i) satisfy a tridiagonal system: h_(i-1)M_(i-1) + 2(h_(i-1)+h_i)M_i + h_i M_(i+1) = 6[(y_(i+1)-y_i)/h_i - (y_i-y_(i-1))/h_(i-1)].",
             "Solved M = [" + ", ".join(g(m, 6) for m in M) + "] (second derivatives at the knots).",
             f"x = {g(xe)} lies in one interval, and evaluating that cubic gives S({g(xe)}) = {g(value)}."]
    lo, hi = min(xs), max(xs)
    grid = np.linspace(lo, hi, 300)
    curve = [spline_value(xs, ys, M, h, float(t)) for t in grid]
    notes = []
    if xe < lo or xe > hi:
        notes.append("x lies outside the data range: the spline is extended using the end cubic (extrapolation).")
    return {
        "answers": [answer(f"S({g(xe)})", value)], "steps": steps, "iterations": len(xs) - 1, "converged": None,
        "columns": ["i", "interval", "a_i", "b_i", "c_i", "d_i"], "rows": rows, "table_title": "Cubic pieces S_i(x)",
        "notes": notes,
        "plot": {"kind": "curves", "curves": [{"label": "Natural cubic spline", "x": grid, "y": curve}],
                 "points": {"x": xs, "y": ys}, "highlight": (xe, value, f"S({g(xe)}) = {g(value)}")},
    }


def poly_approximation(f, a, b, degree, xe):
    if a >= b:
        raise NumericalError("The left end a must be smaller than the right end b.")
    n = degree + 1
    h = (b - a) / degree
    z = [a + i * h for i in range(n)]
    values = [f(t) for t in z]
    table = divided_differences(z, values)
    coeffs = [table[k][0] for k in range(n)]
    value = newton_form_value(z, coeffs, xe)
    grid = np.linspace(a, b, 400)
    approx = [newton_form_value(z, coeffs, float(t)) for t in grid]
    exact = f.vec(grid)
    max_err = float(np.max(np.abs(exact - np.array(approx))))
    rows = [[i, z[i]] + [table[k][i] if i < len(table[k]) else "" for k in range(min(n, 4))] for i in range(n)]
    steps = [f"Take {n} equally spaced nodes on [{g(a)}, {g(b)}] with spacing h = {g(h)}, and evaluate f at each node.",
             "Build Newton's divided differences f[z0], f[z0,z1], f[z0,z1,z2], ... (the table below).",
             "P(x) = f[z0] + f[z0,z1](x-z0) + f[z0,z1,z2](x-z0)(x-z1) + ...",
             f"P({g(xe)}) = {g(value)}   (true f({g(xe)}) = {g(f(xe))}).",
             f"Largest error of P over [a, b] (checked on 400 points): {g(max_err)}."]
    notes = [f"Error formula: f(x) - P(x) = f^({n})(ξ)/{n}! · Π (x - z_i). More nodes does NOT always help (Runge phenomenon) - compare degree {degree} with a smaller degree."]
    return {
        "answers": [answer(f"P({g(xe)})", value)], "steps": steps, "iterations": n, "converged": None,
        "columns": ["i", "z_i", "f[z]", "1st diff", "2nd diff", "3rd diff"], "rows": rows,
        "table_title": "Divided-difference table (first 4 columns)", "notes": notes,
        "metrics": [{"label": "Max |f - P| on [a, b]", "value": max_err}],
        "plot": {"kind": "curves", "curves": [{"label": f"f(x) = {f.pretty()}", "x": grid, "y": exact, "color": "#E8E8F2", "lw": 1.6},
                                              {"label": f"Polynomial P (degree {degree})", "x": grid, "y": approx, "ls": "--"}],
                 "points": {"x": z, "y": values, "label": "nodes"}, "highlight": (xe, value, f"P({g(xe)})")},
    }


# ===================================================== PART 2: WEBSITE ADAPTERS
def _data(p, with_deriv=False):
    xs = get_list(p, "xs", "x values", 2)
    ys = get_vector(p, "ys", "y values", len(xs))
    xe = get_float(p, "xe", "Evaluation point x")
    return xs, ys, xe


def run_lagrange(p):
    xs, ys, xe = _data(p)
    check_points(xs, ys)
    xs, ys = sort_points(xs, ys)
    raw = lagrange(xs, ys, xe)
    ref = float(scipy_lagrange(xs, ys)(xe))
    return finish(raw, {"label": "SciPy lagrange", "value": ref, "exact": False})


def run_hermite(p):
    xs, ys, xe = _data(p)
    dys = get_vector(p, "dys", "slopes f'(x)", len(xs))
    check_points(xs, ys)
    xs, ys, dys = sort_points(xs, ys, dys)
    raw = hermite(xs, ys, dys, xe)
    ref = float(CubicHermiteSpline(xs, ys, dys)(xe)) if len(xs) == 2 else None
    # independent check for any size: solve the Hermite conditions with NumPy
    degree = 2 * len(xs) - 1
    A = [[t ** k for k in range(degree + 1)] for t in xs] + [[k * t ** (k - 1) if k else 0.0 for k in range(degree + 1)] for t in xs]
    try:
        coef = np.linalg.solve(np.array(A, float), np.array(ys + dys, float))
        ref = float(sum(c * xe ** k for k, c in enumerate(coef)))
    except np.linalg.LinAlgError:
        pass
    return finish(raw, {"label": "NumPy linear-system check", "value": ref, "exact": False} if ref is not None else None)


def run_spline(p):
    xs, ys, xe = _data(p)
    check_points(xs, ys)
    xs, ys = sort_points(xs, ys)
    raw = cubic_spline(xs, ys, xe)
    ref = float(CubicSpline(xs, ys, bc_type="natural", extrapolate=True)(xe))
    return finish(raw, {"label": "SciPy CubicSpline (natural)", "value": ref, "exact": False})


def run_poly_approx(p):
    f = get_expr(p, "f")
    a, b = get_float(p, "a", "a"), get_float(p, "b", "b")
    degree = get_int(p, "degree", "Degree", 1, 20)
    xe = get_float(p, "xe", "Evaluation point x")
    raw = poly_approximation(f, a, b, degree, xe)
    return finish(raw, {"label": "Exact f(x)", "value": f(xe), "exact": True})


XS = field("xs", "x data points", "list", "0, 1, 2, 3, 4", "Separated by commas.")
YS = field("ys", "y data points", "list", "0, 0.8415, 0.9093, 0.1411, -0.7568", "Same count as x.")
XE = field("xe", "Evaluate at x", "number", "2.5")

SPECS = {
    "lagrange": {"name": "Lagrange Interpolation", "category": "interp", "run": run_lagrange,
                 "formula": r"P(x)=\sum_{k=0}^{n} y_k L_k(x),\quad L_k(x)=\prod_{j\neq k}\dfrac{x-x_j}{x_k-x_j}",
                 "inputs": [XS, YS, XE]},
    "hermite": {"name": "Hermite Interpolation", "category": "interp", "run": run_hermite,
                "formula": r"H(x)=f[z_0]+\sum_{k=1}^{2n+1} f[z_0,\dots,z_k]\prod_{i<k}(x-z_i),\quad z_{2i}=z_{2i+1}=x_i",
                "inputs": [XS, YS, field("dys", "Slopes f'(x) at each point", "list", "1, 0.5403, -0.4161, -0.99, -0.6536", "One derivative per point."), XE]},
    "spline": {"name": "Cubic Spline Interpolation", "category": "interp", "run": run_spline,
               "formula": r"S_i(x)=a_i+b_i(x-x_i)+c_i(x-x_i)^2+d_i(x-x_i)^3,\quad S''(x_0)=S''(x_n)=0",
               "inputs": [XS, YS, XE]},
    "poly_approx": {"name": "Polynomial Approximation", "category": "interp", "run": run_poly_approx,
                    "formula": r"P_n(x)=f[z_0]+f[z_0,z_1](x-z_0)+\cdots+f[z_0,\dots,z_n]\prod_{i<n}(x-z_i)",
                    "inputs": [field("f", "Function f(x) to approximate", "expr", "exp(x)"), field("a", "Left end a", "number", "0"),
                               field("b", "Right end b", "number", "2"), field("degree", "Polynomial degree n", "int", "3"),
                               field("xe", "Evaluate at x", "number", "1.5")]},
}
