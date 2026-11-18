"""Curve fitting with the Method of Least Squares (data does NOT have to be matched exactly)."""
import math

import numpy as np

from methods.linear_algebra import solve_linear
from utils.errors import NumericalError
from utils.inputs import field, g, get_int, get_list, get_select, get_vector
from utils.results import answer, finish


# ===================================================== PART 1: ALGORITHMS
def least_squares_line(xs, ys):
    n = len(xs)
    if n < 2:
        raise NumericalError("At least 2 data points are needed.")
    sx = sum(xs)
    sy = sum(ys)
    sxy = sum(x * y for x, y in zip(xs, ys))
    sxx = sum(x * x for x in xs)
    denom = n * sxx - sx * sx
    if abs(denom) < 1e-14:
        raise NumericalError("All x-values are the same, so a line cannot be fitted.")
    m = (n * sxy - sx * sy) / denom
    c = (sy - m * sx) / n
    mean_y = sy / n
    rows, sse, sst = [], 0.0, 0.0
    for i in range(n):
        fitted = m * xs[i] + c
        resid = ys[i] - fitted
        sse += resid ** 2
        sst += (ys[i] - mean_y) ** 2
        rows.append([i + 1, xs[i], ys[i], xs[i] * ys[i], xs[i] ** 2, fitted, resid])
    r2 = 1 - sse / sst if sst > 0 else 1.0
    steps = [f"Normal equations: n·Σx² ... gives slope m = (nΣxy - ΣxΣy) / (nΣx² - (Σx)²).",
             f"n = {n}, Σx = {g(sx)}, Σy = {g(sy)}, Σxy = {g(sxy)}, Σx² = {g(sxx)}.",
             f"m = ({n}·{g(sxy)} - {g(sx)}·{g(sy)}) / ({n}·{g(sxx)} - {g(sx)}²) = {g(m)}.",
             f"c = (Σy - mΣx)/n = ({g(sy)} - {g(m)}·{g(sx)})/{n} = {g(c)}.",
             f"Best line: y = {g(m)}x + {g(c)}.  Sum of squared errors SSE = {g(sse)}, R² = {g(r2)}."]
    lo, hi = min(xs), max(xs)
    grid = np.linspace(lo - 0.05 * (hi - lo), hi + 0.05 * (hi - lo), 100)
    return {
        "answers": [answer("Coefficients [m, c]", [m, c]), answer("R²", r2)], "steps": steps, "iterations": n, "converged": None,
        "columns": ["i", "x", "y", "x·y", "x²", "fitted ŷ", "residual y - ŷ"], "rows": rows,
        "metrics": [{"label": "SSE (sum of squared errors)", "value": sse}, {"label": "R²", "value": r2}],
        "plot": {"kind": "curves", "curves": [{"label": f"y = {g(m, 5)}x + {g(c, 5)}", "x": grid, "y": m * grid + c}],
                 "points": {"x": xs, "y": ys}},
    }


def fit_model(xs, ys, model, degree=2):
    n = len(xs)
    notes = []
    X, Y = list(xs), list(ys)
    if model == "polynomial":
        if degree >= n:
            raise NumericalError(f"A degree {degree} polynomial needs at least {degree + 1} data points (you gave {n}).")
        cols = degree + 1
        A = [[x ** k for k in range(cols)] for x in X]
        label = "polynomial"
    elif model == "exponential":
        if min(ys) <= 0:
            raise NumericalError("y = a·e^(bx) needs all y-values to be positive (we take ln y).")
        Y = [math.log(y) for y in ys]
        A = [[1.0, x] for x in X]
        notes.append("Linearised: ln y = ln a + b·x, then a = e^(intercept).")
        label = "exponential"
    elif model == "power":
        if min(xs) <= 0 or min(ys) <= 0:
            raise NumericalError("y = a·x^b needs all x and y values to be positive (we take logarithms).")
        X = [math.log(x) for x in xs]
        Y = [math.log(y) for y in ys]
        A = [[1.0, t] for t in X]
        notes.append("Linearised: ln y = ln a + b·ln x, then a = e^(intercept).")
        label = "power"
    elif model == "logarithmic":
        if min(xs) <= 0:
            raise NumericalError("y = a + b·ln x needs all x-values to be positive.")
        A = [[1.0, math.log(x)] for x in xs]
        label = "logarithmic"
    else:
        raise NumericalError("Unknown model.")
    # normal equations  (AᵀA) c = Aᵀ Y
    m, k = len(A), len(A[0])
    AtA = [[sum(A[r][i] * A[r][j] for r in range(m)) for j in range(k)] for i in range(k)]
    AtY = [sum(A[r][i] * Y[r] for r in range(m)) for i in range(k)]
    coef = solve_linear(AtA, AtY)
    if model == "polynomial":
        params, names = coef, [f"c{i}" for i in range(k)]
        predict = lambda t: sum(c * t ** i for i, c in enumerate(coef))
        eq = " + ".join(f"{g(c, 5)}x^{i}" if i else g(c, 5) for i, c in enumerate(coef))
    elif model == "exponential":
        params, names = [math.exp(coef[0]), coef[1]], ["a", "b"]
        predict = lambda t: params[0] * math.exp(params[1] * t)
        eq = f"{g(params[0], 5)}·e^({g(params[1], 5)}x)"
    elif model == "power":
        params, names = [math.exp(coef[0]), coef[1]], ["a", "b"]
        predict = lambda t: params[0] * t ** params[1]
        eq = f"{g(params[0], 5)}·x^{g(params[1], 5)}"
    else:
        params, names = coef, ["a", "b"]
        predict = lambda t: params[0] + params[1] * math.log(t)
        eq = f"{g(params[0], 5)} + {g(params[1], 5)}·ln(x)"
    rows, sse, sst = [], 0.0, 0.0
    mean_y = sum(ys) / n
    for x, y in zip(xs, ys):
        fit = predict(x)
        sse += (y - fit) ** 2
        sst += (y - mean_y) ** 2
        rows.append([x, y, fit, y - fit])
    r2 = 1 - sse / sst if sst > 0 else 1.0
    lo, hi = min(xs), max(xs)
    grid = np.linspace(lo, hi, 200)
    steps = [f"Chosen model: {label}.", "Build the design matrix A and solve the normal equations (AᵀA)c = Aᵀy with Gaussian elimination.",
             "Fitted parameters: " + ", ".join(f"{nm} = {g(v, 6)}" for nm, v in zip(names, params)) + ".",
             f"Fitted curve: y = {eq}", f"SSE = {g(sse)}, R² = {g(r2)}."]
    return {
        "answers": [answer("Parameters " + str(names).replace("'", ""), params), answer("R²", r2)], "steps": steps, "iterations": n,
        "converged": None, "columns": ["x", "y (data)", "fitted ŷ", "residual"], "rows": rows,
        "notes": notes + ["Exponential/power fits minimise the error in ln y, not in y, so SSE can differ from a direct nonlinear fit."],
        "metrics": [{"label": "SSE", "value": sse}, {"label": "R²", "value": r2}],
        "plot": {"kind": "curves", "curves": [{"label": f"{label} fit: y = {eq}", "x": grid, "y": [predict(float(t)) for t in grid]}],
                 "points": {"x": xs, "y": ys}},
        "_model": (model, degree),
    }


# ===================================================== PART 2: WEBSITE ADAPTERS
def run_line(p):
    xs = get_list(p, "xs", "x values", 2)
    ys = get_vector(p, "ys", "y values", len(xs))
    raw = least_squares_line(xs, ys)
    ref = [float(v) for v in np.polyfit(xs, ys, 1)]
    ref = [ref[0], ref[1]]
    return finish(raw, {"label": "NumPy polyfit", "value": ref, "exact": False})


def run_curve_fit(p):
    xs = get_list(p, "xs", "x values", 2)
    ys = get_vector(p, "ys", "y values", len(xs))
    model = get_select(p, "model", ["polynomial", "exponential", "power", "logarithmic"])
    degree = get_int(p, "degree", "Degree", 1, 10)
    raw = fit_model(xs, ys, model, degree)
    ref = None
    if model == "polynomial":
        ref = [float(c) for c in np.polyfit(xs, ys, degree)[::-1]]
    elif model == "exponential":
        b, ln_a = np.polyfit(xs, np.log(ys), 1)
        ref = [float(np.exp(ln_a)), float(b)]
    elif model == "power":
        b, ln_a = np.polyfit(np.log(xs), np.log(ys), 1)
        ref = [float(np.exp(ln_a)), float(b)]
    else:
        b, a = np.polyfit(np.log(xs), ys, 1)
        ref = [float(a), float(b)]
    return finish(raw, {"label": "NumPy polyfit (same model)", "value": ref, "exact": False})


SPECS = {
    "least_squares": {"name": "Method of Least Squares", "category": "interp", "run": run_line,
                      "formula": r"m=\dfrac{n\sum xy-\sum x\sum y}{n\sum x^2-(\sum x)^2},\quad c=\dfrac{\sum y-m\sum x}{n}",
                      "inputs": [field("xs", "x data", "list", "1, 2, 3, 4", "Comma separated."),
                                 field("ys", "y data", "list", "6, 5, 7, 10")]},
    "curve_fitting": {"name": "Curve Fitting", "category": "interp", "run": run_curve_fit,
                      "formula": r"(A^TA)\,\mathbf{c}=A^T\mathbf{y},\qquad \text{minimise } \sum (y_i-\hat y_i)^2",
                      "inputs": [field("xs", "x data", "list", "0, 1, 2, 3, 4", "Comma separated."),
                                 field("ys", "y data", "list", "1.1, 2.9, 8.2, 20.5, 54.0"),
                                 field("model", "Model", "select", "exponential", "", options=[
                                     {"value": "polynomial", "label": "Polynomial"}, {"value": "exponential", "label": "Exponential  y = a·e^(bx)"},
                                     {"value": "power", "label": "Power  y = a·x^b"}, {"value": "logarithmic", "label": "Logarithmic  y = a + b·ln x"}]),
                                 field("degree", "Polynomial degree (only for Polynomial)", "int", "2", showIf={"model": "polynomial"})]},
}
