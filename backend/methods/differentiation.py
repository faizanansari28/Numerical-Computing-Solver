"""Numerical differentiation: approximate f'(x) or f''(x) from function values."""
import numpy as np

from utils.errors import NumericalError
from utils.inputs import field, g, get_expr, get_float, get_int, get_select
from utils.results import answer, finish
from utils.symbolic import derivative

FORMULAS = {
    "forward": ("Forward difference", "(f(x+h) - f(x)) / h", 1),
    "backward": ("Backward difference", "(f(x) - f(x-h)) / h", 1),
    "central": ("Central difference", "(f(x+h) - f(x-h)) / (2h)", 2),
    "five_point": ("Five-point formula", "(f(x-2h) - 8f(x-h) + 8f(x+h) - f(x+2h)) / (12h)", 4),
    "second": ("Central second derivative", "(f(x+h) - 2f(x) + f(x-h)) / h²", 2),
}


# ===================================================== PART 1: ALGORITHMS
def approximate(f, x, h, method):
    if method == "forward":
        return (f(x + h) - f(x)) / h
    if method == "backward":
        return (f(x) - f(x - h)) / h
    if method == "central":
        return (f(x + h) - f(x - h)) / (2 * h)
    if method == "five_point":
        return (f(x - 2 * h) - 8 * f(x - h) + 8 * f(x + h) - f(x + 2 * h)) / (12 * h)
    return (f(x + h) - 2 * f(x) + f(x - h)) / (h * h)


def numerical_derivative(f, x, h, method, exact, shrinks=6):
    if h <= 0:
        raise NumericalError("The step size h must be positive.")
    name, text, order = FORMULAS[method]
    rows, previous = [], None
    hk = h
    for k in range(shrinks + 1):
        approx = approximate(f, x, hk, method)
        err = abs(approx - exact)
        ratio = previous / err if previous and err > 0 else ""
        rows.append([k, hk, approx, exact, err, ratio])
        previous = err
        hk = hk / 2
    value = approximate(f, x, h, method)
    steps = [f"Formula ({name}): {text}.", f"With h = {g(h)}: approximation = {g(value)}.",
             f"Exact value (from the symbolic derivative) = {g(exact)}, so the error is {g(abs(value - exact))}.",
             f"Halving h repeatedly: the error ratio tends to 2^p = {2 ** order} for a method of order O(h^{order}) - see the last column.",
             "Do not make h too small: below about 1e-8 rounding errors take over (subtracting nearly equal numbers)."]
    pad = 1.5 * h if h > 0 else 1
    span = max(3 * h, 1.0)
    grid = np.linspace(x - span, x + span, 300)
    notes = []
    curves = [{"label": f"f(x) = {f.pretty()}", "x": grid, "y": f.vec(grid), "color": "#E8E8F2", "lw": 1.6}]
    if method != "second":
        fx = f(x)
        curves.append({"label": f"tangent with approximate slope {g(value, 5)}", "x": grid, "y": fx + value * (grid - x), "ls": "--"})
        curves.append({"label": f"exact tangent (slope {g(exact, 5)})", "x": grid, "y": fx + exact * (grid - x), "ls": ":", "color": "#F5B85C"})
    return {
        "answers": [answer("Derivative ≈", value)], "steps": steps, "iterations": None, "converged": None,
        "columns": ["k", "step h", "approximation", "exact", "|error|", "previous error / error"], "rows": rows,
        "table_title": "Effect of the step size h", "notes": notes,
        "plot": {"kind": "curves", "curves": curves, "points": {"x": [x], "y": [f(x)], "label": f"x = {g(x)}"}},
        "extra": {"order": order},
    }


# ===================================================== PART 2: WEBSITE ADAPTERS
def run_numdiff(p):
    f = get_expr(p, "f")
    x = get_float(p, "x", "Point x")
    h = get_float(p, "h", "Step size h", 1e-12)
    method = get_select(p, "method", list(FORMULAS), "central")
    d1 = derivative(f)
    d2 = derivative(d1) if d1 else None
    exact_expr = d2 if method == "second" else d1
    if exact_expr is None:
        raise NumericalError("This expression cannot be differentiated exactly, so no exact reference is available.")
    exact = exact_expr(x)
    raw = numerical_derivative(f, x, h, method, exact)
    return finish(raw, {"label": "Exact derivative (symbolic)", "value": exact, "exact": True})


SPECS = {
    "numdiff": {"name": "Numerical Differentiation", "category": "diffode", "run": run_numdiff,
                "formula": r"f'(x)\approx\dfrac{f(x+h)-f(x-h)}{2h},\qquad f''(x)\approx\dfrac{f(x+h)-2f(x)+f(x-h)}{h^2}",
                "inputs": [field("f", "Function f(x)", "expr", "sin(x)"), field("x", "Point x", "number", "1"),
                           field("h", "Step size h", "number", "0.1"),
                           field("method", "Formula", "select", "central", "", options=[
                               {"value": "forward", "label": "Forward difference O(h)"}, {"value": "backward", "label": "Backward difference O(h)"},
                               {"value": "central", "label": "Central difference O(h²)"}, {"value": "five_point", "label": "Five-point O(h⁴)"},
                               {"value": "second", "label": "Second derivative (central) O(h²)"}])]},
}
