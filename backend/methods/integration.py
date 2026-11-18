"""Numerical integration (quadrature): approximate the integral of f(x) from a to b.

Methods: Midpoint, Trapezoidal, Simpson, Newton-Cotes, Gauss-Legendre, Legendre polynomials.
"""
import math

import numpy as np
from numpy.polynomial import legendre as np_legendre
from scipy.integrate import quad

from utils.errors import NumericalError
from utils.inputs import field, g, get_expr, get_float, get_int, get_select
from utils.results import answer, finish


def check_limits(a, b):
    if a >= b:
        raise NumericalError("The lower limit a must be smaller than the upper limit b.")


# ===================================================== PART 1: ALGORITHMS
def midpoint(f, a, b, n):
    check_limits(a, b)
    h = (b - a) / n
    total = 0.0
    rows, polys, nodes = [], [], []
    for i in range(1, n + 1):
        x_mid = a + (i - 0.5) * h
        fx = f(x_mid)
        total += fx
        rows.append([i, x_mid, fx, h, h * fx])
        left = a + (i - 1) * h
        polys.append(([left, left, left + h, left + h], [0, fx, fx, 0]))
        nodes.append((x_mid, fx))
    result = h * total
    steps = [f"Step size h = (b - a)/n = ({g(b)} - {g(a)})/{n} = {g(h)}.",
             "Evaluate f at the middle of every subinterval: x_i = a + (i - 1/2)h.",
             f"Sum of f(x_i) = {g(total)}.", f"Integral ≈ h · Σ f(x_i) = {g(h)} · {g(total)} = {g(result)}."]
    return pack(f, a, b, result, steps, ["i", "midpoint x_i", "f(x_i)", "width h", "area h·f(x_i)"], rows, polys, nodes, n, "midpoint")


def trapezoid(f, a, b, n):
    check_limits(a, b)
    h = (b - a) / n
    total = f(a) + f(b)
    rows = [[0, a, f(a), 1, f(a)]]
    polys, nodes = [], [(a, f(a))]
    for i in range(1, n + 1):
        x = a + i * h
        fx = f(x)
        weight = 1 if i == n else 2
        if i < n:
            total += 2 * fx
        rows.append([i, x, fx, weight, weight * fx])
        left = a + (i - 1) * h
        polys.append(([left, left, x, x], [0, f(left), fx, 0]))
        nodes.append((x, fx))
    result = (h / 2) * total
    steps = [f"Step size h = (b - a)/n = ({g(b)} - {g(a)})/{n} = {g(h)}.",
             "Weights: the two end points count once, every inner point counts twice.",
             f"Sum = f(a) + f(b) + 2·Σ f(inner) = {g(total)}.", f"Integral ≈ (h/2) · Sum = ({g(h)}/2) · {g(total)} = {g(result)}."]
    return pack(f, a, b, result, steps, ["i", "x_i", "f(x_i)", "Weight", "Contribution (weight · f)"], rows, polys, nodes, n, "trapezoid")


def simpson(f, a, b, n):
    check_limits(a, b)
    if n % 2 != 0:
        raise NumericalError(f"Simpson's rule needs an EVEN number of intervals (you gave n = {n}).")
    h = (b - a) / n
    rows, polys, nodes, total = [], [], [], 0.0
    for i in range(n + 1):
        x = a + i * h
        fx = f(x)
        weight = 1 if i in (0, n) else (4 if i % 2 == 1 else 2)
        total += weight * fx
        rows.append([i, x, fx, weight, weight * fx])
        nodes.append((x, fx))
    for i in range(0, n, 2):                             # parabola through three points
        x0, x1, x2 = a + i * h, a + (i + 1) * h, a + (i + 2) * h
        px = np.linspace(x0, x2, 25)
        py = []
        for t in px:
            py.append(sum(y * np.prod([(t - xx) / (xk - xx) for xx in (x0, x1, x2) if xx != xk])
                          for xk, y in ((x0, f(x0)), (x1, f(x1)), (x2, f(x2)))))
        polys.append((list(px) + [x2, x0], py + [0, 0]))
    result = (h / 3) * total
    steps = [f"Step size h = (b - a)/n = ({g(b)} - {g(a)})/{n} = {g(h)}.",
             "Weights follow the pattern 1, 4, 2, 4, 2, ..., 4, 1 (odd points ×4, even inner points ×2).",
             f"Weighted sum = {g(total)}.", f"Integral ≈ (h/3) · Sum = ({g(h)}/3) · {g(total)} = {g(result)}."]
    return pack(f, a, b, result, steps, ["i", "x_i", "f(x_i)", "Weight", "Contribution (weight · f)"], rows, polys, nodes, n, "simpson")


NC_RULES = {   # closed Newton-Cotes: (name, weights, factor so that I = factor * h * sum(w f))
    1: ("Trapezoidal rule", [1, 1], 1 / 2),
    2: ("Simpson's 1/3 rule", [1, 4, 1], 1 / 3),
    3: ("Simpson's 3/8 rule", [1, 3, 3, 1], 3 / 8),
    4: ("Boole's rule", [7, 32, 12, 32, 7], 2 / 45),
}


def newton_cotes(f, a, b, degree, panels=1):
    check_limits(a, b)
    if degree not in NC_RULES:
        raise NumericalError("Newton-Cotes degree must be 1, 2, 3 or 4.")
    name, weights, factor = NC_RULES[degree]
    H = (b - a) / panels
    h = H / degree
    result, rows, polys, nodes = 0.0, [], [], []
    for p in range(panels):
        left = a + p * H
        xs = [left + k * h for k in range(degree + 1)]
        ys = [f(x) for x in xs]
        piece = factor * h * sum(w * y for w, y in zip(weights, ys))
        result += piece
        for k in range(degree + 1):
            rows.append([p + 1, k, xs[k], ys[k], weights[k], weights[k] * ys[k]])
            nodes.append((xs[k], ys[k]))
        px = np.linspace(xs[0], xs[-1], 40)
        py = [sum(y * np.prod([(t - xx) / (xk - xx) for xx in xs if xx != xk]) for xk, y in zip(xs, ys)) for t in px]
        polys.append((list(px) + [xs[-1], xs[0]], py + [0, 0]))
    steps = [f"{name} uses {degree + 1} equally spaced points per panel with weights {weights} (closed Newton-Cotes, degree {degree}).",
             f"{panels} panel(s) of width {g(H)}; spacing h = {g(h)}.",
             f"On each panel: I ≈ {g(factor, 5)}·h·Σ w_k f(x_k).", f"Total integral ≈ {g(result)}."]
    out = pack(f, a, b, result, steps, ["panel", "k", "x_k", "f(x_k)", "weight w_k", "w_k · f(x_k)"], rows, polys, nodes, panels * degree, "nc")
    out["notes"].append(f"This rule is exact for polynomials up to degree {degree if degree % 2 else degree + 1}.")
    return out


def legendre(n, x):
    """P_n(x) and its derivative using the recurrence (k+1)P_(k+1) = (2k+1)x P_k - k P_(k-1)."""
    p_prev, p = 1.0, x
    if n == 0:
        return 1.0, 0.0
    for k in range(1, n):
        p_prev, p = p, ((2 * k + 1) * x * p - k * p_prev) / (k + 1)
    dp = n * (x * p - p_prev) / (x * x - 1)
    return p, dp


def gauss_nodes_weights(n):
    """Roots of P_n by Newton's method; weights w = 2 / ((1 - x²) P_n'(x)²)."""
    nodes, weights = [], []
    for i in range(1, n + 1):
        x = math.cos(math.pi * (i - 0.25) / (n + 0.5))
        for _ in range(100):
            p, dp = legendre(n, x)
            dx = p / dp
            x -= dx
            if abs(dx) < 1e-15:
                break
        _, dp = legendre(n, x)
        nodes.append(x)
        weights.append(2 / ((1 - x * x) * dp * dp))
    order = sorted(range(n), key=lambda k: nodes[k])
    return [nodes[k] for k in order], [weights[k] for k in order]


def gauss_legendre(f, a, b, n):
    check_limits(a, b)
    if n < 1 or n > 20:
        raise NumericalError("Number of Gauss points must be between 1 and 20.")
    t, w = gauss_nodes_weights(n)
    half, mid = (b - a) / 2, (b + a) / 2
    total, rows, nodes = 0.0, [], []
    for i in range(n):
        x = half * t[i] + mid
        fx = f(x)
        total += w[i] * fx
        rows.append([i + 1, t[i], w[i], x, fx, w[i] * fx])
        nodes.append((x, fx))
    result = half * total
    steps = [f"Use the {n} roots t_i of the Legendre polynomial P_{n}(t) on [-1, 1] and the weights w_i = 2/((1 - t_i²)·P'_{n}(t_i)²).",
             f"Map [-1, 1] to [a, b]: x_i = (b - a)/2 · t_i + (a + b)/2, with (b - a)/2 = {g(half)}.",
             f"Σ w_i f(x_i) = {g(total)}.", f"Integral ≈ (b - a)/2 · Σ w_i f(x_i) = {g(half)} · {g(total)} = {g(result)}.",
             f"An {n}-point Gauss rule is exact for every polynomial up to degree {2 * n - 1}."]
    out = pack(f, a, b, result, steps, ["i", "node t_i", "weight w_i", "x_i", "f(x_i)", "w_i · f(x_i)"], rows, [], nodes, n, "gauss")
    out["notes"].append(f"Only {n} function evaluations were used.")
    return out


def pack(f, a, b, result, steps, columns, rows, polys, nodes, n, kind):
    if len(polys) > 80:                       # too many pieces to draw one by one
        polys = []
    if len(nodes) > 80:
        nodes = []
    return {
        "answers": [answer("Integral ≈", result)], "steps": steps, "iterations": n, "converged": None,
        "columns": columns, "rows": rows, "notes": [], "evaluations": len(nodes),
        "plot": {"kind": "integration", "f": f, "a": a, "b": b, "polys": polys, "nodes": nodes},
    }


def legendre_polynomials(n, x0):
    if n < 0 or n > 12:
        raise NumericalError("Degree n must be between 0 and 12.")
    values = [1.0, x0]
    for k in range(1, n):
        values.append(((2 * k + 1) * x0 * values[k] - k * values[k - 1]) / (k + 1))
    values = values[: n + 1]
    rows = []
    for k in range(n + 1):
        rule = "P_0 = 1" if k == 0 else "P_1 = x" if k == 1 else f"({2 * k - 1}·x·P_{k - 1} - {k - 1}·P_{k - 2})/{k}"
        rows.append([k, rule, values[k]])
    roots = gauss_nodes_weights(n)[0] if n >= 1 else []
    # orthogonality check with Gauss quadrature (exact for these degrees)
    t, w = gauss_nodes_weights(n + 2)
    worst = 0.0
    for i in range(n + 1):
        for j in range(n + 1):
            integral = sum(wk * legendre_value(i, tk) * legendre_value(j, tk) for tk, wk in zip(t, w))
            target = 2 / (2 * i + 1) if i == j else 0.0
            worst = max(worst, abs(integral - target))
    steps = ["Legendre polynomials are generated by the recurrence (k+1)P_(k+1)(x) = (2k+1)x·P_k(x) - k·P_(k-1)(x), with P_0 = 1, P_1 = x.",
             f"At x = {g(x0)} the values are " + ", ".join(f"P_{k} = {g(v, 6)}" for k, v in enumerate(values)) + ".",
             f"P_{n} has {n} real roots in (-1, 1): " + (", ".join(g(r, 6) for r in roots) if roots else "none (constant)") + " - these are the Gauss-Legendre nodes.",
             f"Orthogonality: ∫ P_i P_j dx over [-1, 1] = 0 (i≠j) and 2/(2i+1) (i=j). Largest deviation found numerically: {g(worst)}."]
    grid = np.linspace(-1, 1, 300)
    curves = [{"label": f"P_{k}(x)", "x": grid, "y": [legendre_value(k, float(t_)) for t_ in grid]} for k in range(min(n, 6) + 1)]
    return {
        "answers": [answer(f"P_{n}({g(x0)})", values[n])], "steps": steps, "iterations": n, "converged": None,
        "columns": ["k", "recurrence", f"P_k({g(x0)})"], "rows": rows,
        "metrics": [{"label": "Worst orthogonality error", "value": worst}], "notes": ["Plot shows P_0 ... P_" + str(min(n, 6)) + "."],
        "plot": {"kind": "curves", "curves": curves, "ylabel": "P_k(x)", "title": "Legendre polynomials on [-1, 1]"},
    }


def legendre_value(k, x):
    if k == 0:
        return 1.0
    p_prev, p = 1.0, x
    for j in range(1, k):
        p_prev, p = p, ((2 * j + 1) * x * p - j * p_prev) / (j + 1)
    return p


# ===================================================== PART 2: WEBSITE ADAPTERS
def _setup(p):
    f = get_expr(p, "f")
    a, b = get_float(p, "a", "Lower limit a"), get_float(p, "b", "Upper limit b")
    check_limits(a, b)
    reference = quad(lambda t: f(t), a, b, epsabs=1e-13, epsrel=1e-13, limit=200)[0]
    return f, a, b, {"label": "SciPy quad", "value": reference, "exact": False}


def _with_estimate(raw, rule, f, a, b, n, order):
    finer = rule(f, a, b, 2 * n)["answers"][0]["value"]
    est = abs(raw["answers"][0]["value"] - finer) / (2 ** order - 1)
    raw["metrics"] = [{"label": f"Error estimate from doubling n (|I_n - I_2n|/{2 ** order - 1})", "value": est}]
    raw["notes"].append("Error estimate uses Richardson's idea: compare with the result for twice as many intervals.")
    return raw


def run_midpoint(p):
    f, a, b, ref = _setup(p)
    n = get_int(p, "n", "Number of intervals", 1, 20000)
    return finish(_with_estimate(midpoint(f, a, b, n), midpoint, f, a, b, n, 2), ref)


def run_trapezoid(p):
    f, a, b, ref = _setup(p)
    n = get_int(p, "n", "Number of intervals", 1, 20000)
    return finish(_with_estimate(trapezoid(f, a, b, n), trapezoid, f, a, b, n, 2), ref)


def run_simpson(p):
    f, a, b, ref = _setup(p)
    n = get_int(p, "n", "Number of intervals", 2, 20000)
    return finish(_with_estimate(simpson(f, a, b, n), simpson, f, a, b, n, 4), ref)


def run_newton_cotes(p):
    f, a, b, ref = _setup(p)
    return finish(newton_cotes(f, a, b, get_int(p, "degree", "Degree", 1, 4), get_int(p, "panels", "Panels", 1, 5000)), ref)


def run_gauss(p):
    f, a, b, ref = _setup(p)
    return finish(gauss_legendre(f, a, b, get_int(p, "npts", "Number of Gauss points", 1, 20)), ref)


def run_legendre(p):
    n = get_int(p, "n", "Degree n", 0, 12)
    x0 = get_float(p, "x0", "Evaluate at x", -1, 1)
    raw = legendre_polynomials(n, x0)
    ref = float(np_legendre.legval(x0, [0] * n + [1]))
    return finish(raw, {"label": "NumPy legval", "value": ref, "exact": False})


FUNC = field("f", "Function f(x)", "expr", "x**2", "Example: x^2, sin(x), exp(-x^2), 1/(1+x^2)")
A = field("a", "Lower limit a", "number", "0")
B = field("b", "Upper limit b", "number", "4")

SPECS = {
    "midpoint": {"name": "Midpoint Rule", "category": "integration", "run": run_midpoint,
                 "formula": r"\int_a^b f\,dx \approx h\sum_{i=1}^{n} f\!\left(a+(i-\tfrac12)h\right),\quad h=\tfrac{b-a}{n}",
                 "inputs": [FUNC, A, B, field("n", "Number of intervals n", "int", "4")]},
    "trapezoid": {"name": "Trapezoidal Rule", "category": "integration", "run": run_trapezoid,
                  "formula": r"\int_a^b f\,dx \approx \dfrac{h}{2}\Big[f(x_0)+2\sum_{i=1}^{n-1}f(x_i)+f(x_n)\Big]",
                  "inputs": [FUNC, A, B, field("n", "Number of intervals n", "int", "4")]},
    "simpson": {"name": "Simpson's Rule", "category": "integration", "run": run_simpson,
                "formula": r"\int_a^b f\,dx \approx \dfrac{h}{3}\Big[f_0+4\sum f_{odd}+2\sum f_{even}+f_n\Big]",
                "inputs": [FUNC, A, B, field("n", "Number of intervals n (EVEN)", "int", "4", "Must be even.")]},
    "newton_cotes": {"name": "Newton-Cotes Quadrature", "category": "integration", "run": run_newton_cotes,
                     "formula": r"\int_a^b f\,dx \approx \sum_{k=0}^{m} w_k f(x_k),\quad x_k=a+kh,\ w_k=\int L_k(x)\,dx",
                     "inputs": [FUNC, A, B, field("degree", "Rule degree", "select", "4", "", options=[
                         {"value": "1", "label": "1 - Trapezoidal"}, {"value": "2", "label": "2 - Simpson 1/3"},
                         {"value": "3", "label": "3 - Simpson 3/8"}, {"value": "4", "label": "4 - Boole"}]),
                         field("panels", "Number of panels (composite)", "int", "1", "1 = one single rule on [a, b].")]},
    "gauss": {"name": "Gaussian Quadrature", "category": "integration", "run": run_gauss,
              "formula": r"\int_a^b f\,dx \approx \dfrac{b-a}{2}\sum_{i=1}^{n} w_i\, f\!\left(\tfrac{b-a}{2}t_i+\tfrac{a+b}{2}\right)",
              "inputs": [FUNC, A, B, field("npts", "Number of Gauss points n", "int", "3", "Exact for polynomials up to degree 2n-1.")]},
    "legendre": {"name": "Legendre Polynomials", "category": "integration", "run": run_legendre,
                 "formula": r"(k+1)P_{k+1}(x)=(2k+1)xP_k(x)-kP_{k-1}(x),\quad \int_{-1}^{1}P_mP_n\,dx=\tfrac{2}{2n+1}\delta_{mn}",
                 "inputs": [field("n", "Degree n", "int", "4"), field("x0", "Evaluate at x (between -1 and 1)", "number", "0.5")]},
}
