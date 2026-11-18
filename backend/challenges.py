"""The Universal Challenge: one problem per category, several applicable methods, one fair comparison.

Every method here is the SAME hand-written algorithm used on the Solver page.
Reference answers are exact (known closed form) or computed independently with SciPy/NumPy.
"""
import math
import time

import numpy as np
from scipy.integrate import quad
from scipy.optimize import brentq

from methods import curve_fitting, integration as ig, interpolation as ip, linear_algebra as la, ode, optimization as opt, root_finding as rf
from utils import matrix as mx
from utils.errors import NumericalError
from utils.inputs import field, get_float, get_int
from utils.plotting import render
from utils.results import to_plain
from utils.safe_expr import Expr
from utils.symbolic import derivative


def _err(value, ref):
    return float(np.linalg.norm(np.array(value, float).ravel() - np.array(ref, float).ravel()))


def _res(value, iterations=None, evaluations=None, converged=True, curve=None, extra=None, note=""):
    return {"value": value, "iterations": iterations, "evaluations": evaluations, "converged": converged, "curve": curve, "extra": extra or [], "note": note}


# ------------------------------------------------------------------ 1. ROOT FINDING
F_ROOT = Expr("x**3 - x - 2")
DF_ROOT = derivative(F_ROOT)
G_ROOT = Expr("(x+2)**(1/3)")
ROOT_REF = brentq(lambda t: F_ROOT(t), 1, 2, xtol=1e-15)


def _root_curve(iterates):
    return {"x": list(range(1, len(iterates) + 1)), "y": [abs(v - ROOT_REF) for v in iterates]}


def root_runners():
    def bis(k):
        r = rf.bisection(F_ROOT, 1, 2, k["tol"], 500)
        return _res(r["answers"][0]["value"], r["iterations"], r["iterations"] + 2, r["converged"], _root_curve(r["iterates"]), note="Always converges, but only linearly.")

    def newt(k):
        r = rf.newton(F_ROOT, DF_ROOT, 1.5, k["tol"], 100)
        return _res(r["answers"][0]["value"], r["iterations"], 2 * r["iterations"], r["converged"], _root_curve(r["iterates"]), note="Quadratic convergence; needs f'(x).")

    def sec(k):
        r = rf.secant(F_ROOT, 1, 2, k["tol"], 100)
        return _res(r["answers"][0]["value"], r["iterations"], r["iterations"] + 2, r["converged"], _root_curve(r["iterates"]), note="Superlinear (order ≈ 1.618) without derivatives.")

    def fix(k):
        r = rf.fixed_point(G_ROOT, 1.5, k["tol"], 500)
        return _res(r["answers"][0]["value"], r["iterations"], r["iterations"], r["converged"], _root_curve(r["iterates"]), note="g(x) = (x+2)^(1/3); linear convergence since |g'| ≈ 0.14.")
    return {"bisection": bis, "newton": newt, "secant": sec, "fixed_point": fix}


# ------------------------------------------------------------------ 2. INTEGRATION
F_INT = Expr("sin(x)")
INT_REF = 2.0


def integration_runners():
    def with_curve(rule, evals_of, sizes):          # built lazily so that it is not counted in the timing
        return lambda: {"x": [evals_of(n) for n in sizes], "y": [max(abs(rule(n) - INT_REF), 1e-17) for n in sizes]}

    sizes = [2, 4, 8, 16, 32, 64]

    def mid(k):
        rule = lambda n: ig.midpoint(F_INT, 0, math.pi, n)["answers"][0]["value"]
        return _res(rule(k["n"]), None, k["n"], True, with_curve(rule, lambda n: n, sizes), note="Order 2 (error ∝ h²).")

    def trap(k):
        rule = lambda n: ig.trapezoid(F_INT, 0, math.pi, n)["answers"][0]["value"]
        return _res(rule(k["n"]), None, k["n"] + 1, True, with_curve(rule, lambda n: n + 1, sizes), note="Order 2 (error ∝ h²).")

    def simp(k):
        rule = lambda n: ig.simpson(F_INT, 0, math.pi, n)["answers"][0]["value"]
        return _res(rule(k["n"]), None, k["n"] + 1, True, with_curve(rule, lambda n: n + 1, sizes), note="Order 4 (error ∝ h⁴).")

    def nc(k):
        rule = lambda n: ig.newton_cotes(F_INT, 0, math.pi, 4, max(n // 4, 1))["answers"][0]["value"]
        return _res(rule(k["n"]), None, max(k["n"] // 4, 1) * 4 + 1, True, with_curve(rule, lambda n: max(n // 4, 1) * 4 + 1, [4, 8, 16, 32, 64]), note="Boole's rule (degree 4), composite.")

    def gauss(k):
        rule = lambda m: ig.gauss_legendre(F_INT, 0, math.pi, m)["answers"][0]["value"]
        return _res(rule(k["gauss_points"]), None, k["gauss_points"], True, with_curve(rule, lambda m: m, [1, 2, 3, 4, 5, 6, 7, 8]), note="Exact for polynomials of degree 2n−1; extremely efficient for smooth f.")
    return {"midpoint": mid, "trapezoid": trap, "simpson": simp, "newton_cotes": nc, "gauss": gauss}


# ------------------------------------------------------------------ 3. INTERPOLATION
XS = [0.0, 1.0, 2.0, 3.0, 4.0]
YS = [math.sin(v) for v in XS]
DYS = [math.cos(v) for v in XS]
GRID = np.linspace(0, 4, 400)


def _interp_result(raw, xe, name_note):
    curve = raw["plot"]["curves"][0]
    max_err = float(np.max(np.abs(np.array(curve["y"], float) - np.sin(np.array(curve["x"], float)))))
    return _res(raw["answers"][0]["value"], None, len(XS), True, None, [{"label": "Max |error| on [0, 4]", "value": max_err}], name_note), curve


def interp_runners(knobs_xe):
    store = {}

    def lag(k):
        raw = ip.lagrange(XS, YS, k["xe"])
        out, c = _interp_result(raw, k["xe"], "Degree-4 polynomial through all 5 points.")
        store["lagrange"] = c
        return out

    def newt(k):
        table = ip.divided_differences(XS, YS)
        coeffs = [table[i][0] for i in range(len(XS))]
        value = ip.newton_form_value(XS, coeffs, k["xe"])
        curve = {"label": "Newton divided differences", "x": GRID, "y": [ip.newton_form_value(XS, coeffs, float(t)) for t in GRID]}
        store["newton"] = curve
        max_err = float(np.max(np.abs(np.array(curve["y"]) - np.sin(GRID))))
        return _res(value, None, len(XS), True, None, [{"label": "Max |error| on [0, 4]", "value": max_err}], "Same polynomial as Lagrange, written in Newton form (the interpolating polynomial is unique).")

    def spl(k):
        raw = ip.cubic_spline(XS, YS, k["xe"])
        out, c = _interp_result(raw, k["xe"], "Piecewise cubic, smooth (C²), no wild oscillation.")
        store["spline"] = c
        return out

    def her(k):
        raw = ip.hermite(XS, YS, DYS, k["xe"])
        out, c = _interp_result(raw, k["xe"], "Uses the slopes too: degree-9 polynomial.")
        store["hermite"] = c
        return out

    def lsq(k):
        raw = curve_fitting.fit_model(XS, YS, "polynomial", 2)
        coef = raw["answers"][0]["value"]
        poly = lambda t: sum(c * t ** i for i, c in enumerate(coef))
        curve = {"label": "Least-squares parabola", "x": GRID, "y": [poly(float(t)) for t in GRID]}
        store["lsq"] = curve
        max_err = float(np.max(np.abs(np.array(curve["y"]) - np.sin(GRID))))
        return _res(poly(k["xe"]), None, len(XS), True, None, [{"label": "Max |error| on [0, 4]", "value": max_err}], "Does NOT pass through the points - it smooths them (fitting, not interpolation).")
    return {"lagrange": lag, "newton": newt, "spline": spl, "hermite": her, "lsq": lsq}, store


# ------------------------------------------------------------------ 4. ODE
F_ODE = Expr("y - t**2 + 1", ("t", "y"))
EXACT_ODE = Expr("(t+1)**2 - 0.5*exp(t)", ("t",))
ODE_REF = EXACT_ODE(2.0)


def ode_runners():
    def make(method, evals_per_step, note):
        def run(k):
            def final_error(h):
                n = int(round(2 / h))
                raw = ode.solve_ode(F_ODE, 0.0, 0.5, h, n, method, "heun", lambda t: EXACT_ODE(t))
                return raw["answers"][0]["value"], raw["errors"][-1], n
            value, e, n = final_error(k["h"])
            hs = [0.4, 0.2, 0.1, 0.05, 0.025]

            def curve():
                errs = [max(final_error(h)[1], 1e-17) for h in hs]
                return {"x": hs, "y": errs}
            return _res(value, n, evals_per_step * n, True, curve, [], note)
        return run
    return {"euler": make("euler", 1, "Order 1: halving h halves the error."), "rk2": make("rk2", 2, "Order 2 (Heun)."), "rk4": make("rk4", 4, "Order 4: halving h divides the error by 16.")}


# ------------------------------------------------------------------ 5. LINEAR SYSTEM
A_LIN = [[10.0, -1.0, 2.0], [-1.0, 11.0, -1.0], [2.0, -1.0, 10.0]]
B_LIN = [14.0, 18.0, 30.0]
X_LIN = [1.0, 2.0, 3.0]


def linear_runners():
    def direct(fn, note):
        def run(k):
            x = fn()
            return _res(x, 1, None, True, None, [{"label": "Residual ‖Ax − b‖∞", "value": la.residual(A_LIN, x, B_LIN)}], note)
        return run

    def iterative(method, note):
        def run(k):
            r = la.iterative(A_LIN, B_LIN, [0.0, 0.0, 0.0], method, k["tol"], 1000)
            return _res(r["answers"][0]["value"], r["iterations"], None, r["converged"], {"x": list(range(1, len(r["history"]) + 1)), "y": r["history"]},
                        [{"label": "Residual ‖Ax − b‖∞", "value": la.residual(A_LIN, r["answers"][0]["value"], B_LIN)}], note)
        return run
    return {
        "gauss_none": direct(lambda: la.eliminate(A_LIN, B_LIN, "none")["x"], "Fine here because the diagonal is large."),
        "gauss_partial": direct(lambda: la.eliminate(A_LIN, B_LIN, "partial")["x"], "Safest general-purpose direct method."),
        "lu": direct(lambda: la.lu_doolittle(A_LIN, B_LIN)["answers"][0]["value"], "Reusable factorization."),
        "cholesky": direct(lambda: la.cholesky(A_LIN, B_LIN)["answers"][0]["value"], "A is symmetric positive definite, so Cholesky applies (half the work of LU)."),
        "inverse": direct(lambda: mx.mat_vec(la.invert(A_LIN), B_LIN), "x = A⁻¹b: works, but is more work and less accurate than solving directly."),
        "jacobi": iterative("jacobi", "Converges because A is diagonally dominant."),
        "gauss_seidel": iterative("gauss_seidel", "Usually about twice as fast as Jacobi."),
    }


# ------------------------------------------------------------------ 6. OPTIMIZATION
A_OPT = [[4.0, 1.0], [1.0, 3.0]]
B_OPT = [1.0, 2.0]
F_OPT = Expr("2*x**2 + x*y + 1.5*y**2 - x - 2*y", ("x", "y"))   # = 1/2 xᵀAx − bᵀx
OPT_REF = list(np.linalg.solve(np.array(A_OPT), np.array(B_OPT)))


def optimization_runners():
    grad, _ = opt.gradient_function(F_OPT)
    hess, _ = opt.hessian_function(F_OPT)

    def curve(h):
        return {"x": list(range(len(h))), "y": [max(v, 1e-17) for v in h]}

    def gd(k):
        r = opt.gradient_descent(F_OPT, grad, (0.0, 0.0), k["alpha"], k["tol"], 2000, "fixed")
        return _res(r["answers"][0]["value"], r["iterations"], r["iterations"] + 1, r["converged"], curve(r["history"]), note="Linear convergence; speed depends on step size and conditioning.")

    def gdb(k):
        r = opt.gradient_descent(F_OPT, grad, (0.0, 0.0), 1.0, k["tol"], 2000, "backtracking")
        return _res(r["answers"][0]["value"], r["iterations"], r["iterations"] + 1, r["converged"], curve(r["history"]), note="Automatic step size (Armijo backtracking).")

    def cg(k):
        r = opt.conjugate_gradient(A_OPT, B_OPT, [0.0, 0.0], k["tol"], 100)
        return _res(r["answers"][0]["value"], r["iterations"], r["iterations"], r["converged"], curve(r["history"]), note="Finishes in at most n = 2 steps for a 2-variable quadratic.")

    def newt(k):
        r = opt.newton_optimization(F_OPT, grad, hess, (0.0, 0.0), k["tol"], 100)
        return _res(r["answers"][0]["value"], r["iterations"], r["iterations"] + 1, r["converged"], curve(r["history"]), note="One step for a quadratic, because the second-order model is exact.")
    return {"gradient": gd, "gradient_bt": gdb, "cg": cg, "newton": newt}


# ------------------------------------------------------------------ DEFINITIONS
def _knob(name, label, ftype, default, help=""):
    return field(name, label, ftype, default, help)


CHALLENGES = {
    "root": {
        "title": "Root-Finding Challenge", "icon": "root",
        "statement": r"\text{Find the real root of } f(x)=x^3-x-2 \text{ in } [1,2]",
        "context": "Four methods attack the same equation. Fixed-point iteration uses the rearrangement g(x) = (x + 2)^(1/3).",
        "reference": {"label": "SciPy brentq (xtol 1e-15)", "value": ROOT_REF},
        "knobs": [_knob("tol", "Tolerance", "number", "1e-10", "Stopping tolerance for every method.")],
        "methods": {"bisection": "Bisection", "newton": "Newton-Raphson", "secant": "Secant", "fixed_point": "Fixed-Point Iteration"},
        "plot": {"xlabel": "iteration", "ylabel": "absolute error |xₖ − x*|", "logy": True, "title": "Convergence behaviour"},
    },
    "integration": {
        "title": "Integration Challenge", "icon": "integral",
        "statement": r"\text{Compute } \int_0^{\pi}\sin x\,dx \quad (\text{exact value } 2)",
        "context": "Composite rules use n subintervals; Gaussian quadrature uses n points. Compare accuracy per function evaluation.",
        "reference": {"label": "Exact value", "value": INT_REF, "exact": True},
        "knobs": [_knob("n", "Subintervals n (multiple of 4)", "int", "8", "For midpoint, trapezoid, Simpson and Boole."), _knob("gauss_points", "Gauss points", "int", "4")],
        "methods": {"midpoint": "Midpoint", "trapezoid": "Trapezoidal", "simpson": "Simpson's", "newton_cotes": "Newton-Cotes (Boole)", "gauss": "Gauss-Legendre"},
        "plot": {"xlabel": "function evaluations", "ylabel": "absolute error", "logy": True, "logx": True, "title": "Accuracy vs. work"},
    },
    "interpolation": {
        "title": "Interpolation Challenge", "icon": "curve",
        "statement": r"\text{Estimate } \sin(x) \text{ at a point from the data } x=0,1,2,3,4",
        "context": "The data are samples of sin x. Hermite also receives the slopes cos x. The least-squares parabola is included to show fitting vs interpolation.",
        "reference": {"label": "Exact sin(x)", "value": None, "exact": True},
        "knobs": [_knob("xe", "Evaluate at x", "number", "2.5")],
        "methods": {"lagrange": "Lagrange", "newton": "Newton divided differences", "spline": "Natural cubic spline", "hermite": "Hermite", "lsq": "Least-squares parabola"},
        "plot": {"kind": "curves"},
    },
    "ode": {
        "title": "ODE Challenge", "icon": "wave",
        "statement": r"y'=y-t^2+1,\quad y(0)=0.5,\quad t\in[0,2]\quad (\text{exact } y=(t+1)^2-\tfrac12e^t)",
        "context": "Three one-step methods on the same problem. The graph shows how the final error shrinks as the step size h shrinks.",
        "reference": {"label": "Exact y(2)", "value": ODE_REF, "exact": True},
        "knobs": [_knob("h", "Step size h", "number", "0.2", "t runs from 0 to 2, so n = 2/h steps.")],
        "methods": {"euler": "Euler", "rk2": "RK2 (Heun)", "rk4": "RK4"},
        "plot": {"xlabel": "step size h", "ylabel": "error in y(2)", "logy": True, "logx": True, "title": "Error vs step size (slope = order)"},
    },
    "linear": {
        "title": "Linear-System Challenge", "icon": "matrix",
        "statement": r"A\mathbf{x}=\mathbf{b},\ A=\begin{pmatrix}10&-1&2\\-1&11&-1\\2&-1&10\end{pmatrix},\ \mathbf{b}=\begin{pmatrix}14\\18\\30\end{pmatrix},\ \mathbf{x}^*=(1,2,3)",
        "context": "A is symmetric, positive definite and diagonally dominant, so direct, factorization and iterative methods all apply.",
        "reference": {"label": "Exact solution (1, 2, 3)", "value": X_LIN, "exact": True},
        "knobs": [_knob("tol", "Tolerance (iterative methods)", "number", "1e-10")],
        "methods": {"gauss_none": "Gaussian elimination", "gauss_partial": "Gaussian + partial pivoting", "lu": "LU (Doolittle)", "cholesky": "Cholesky", "inverse": "Matrix inverse", "jacobi": "Jacobi", "gauss_seidel": "Gauss-Seidel"},
        "plot": {"kind": "bars"},
    },
    "optimization": {
        "title": "Optimization Challenge", "icon": "valley",
        "statement": r"\min_{x,y} f=2x^2+xy+\tfrac32y^2-x-2y,\quad \text{start }(0,0)\quad (\text{minimiser solves } A\mathbf{x}=\mathbf{b})",
        "context": "A strictly convex quadratic with Hessian A = [[4,1],[1,3]]. Compare gradient descent, CG and Newton by how fast the gradient vanishes.",
        "reference": {"label": "Exact minimiser A⁻¹b", "value": OPT_REF, "exact": True},
        "knobs": [_knob("tol", "Tolerance on ‖∇f‖", "number", "1e-8"), _knob("alpha", "Step size α (fixed-step GD)", "number", "0.2")],
        "methods": {"gradient": "Gradient descent (fixed α)", "gradient_bt": "Gradient descent (backtracking)", "cg": "Conjugate gradient", "newton": "Newton's method"},
        "plot": {"xlabel": "iteration", "ylabel": "gradient norm ‖∇f‖", "logy": True, "title": "How fast does the gradient vanish?"},
    },
}


def public_definitions():
    out = []
    for cid, c in CHALLENGES.items():
        out.append({"id": cid, "title": c["title"], "icon": c["icon"], "statement": c["statement"], "context": c["context"],
                    "knobs": c["knobs"], "methods": [{"id": k, "name": v} for k, v in c["methods"].items()],
                    "reference_label": c["reference"]["label"]})
    return out


def _timed(fn, knobs, repeats=15):
    best = float("inf")
    for _ in range(repeats):
        t = time.perf_counter()
        fn(knobs)
        best = min(best, time.perf_counter() - t)
    return best * 1000.0


def run_challenge(cid, method_ids, raw_knobs):
    if cid not in CHALLENGES:
        raise NumericalError("Unknown challenge.")
    c = CHALLENGES[cid]
    if not method_ids:
        method_ids = list(c["methods"])
    unknown = [m for m in method_ids if m not in c["methods"]]
    if unknown:
        raise NumericalError(f"'{unknown[0]}' cannot be applied to this challenge.")
    knobs = {}
    for kf in c["knobs"]:
        if kf["type"] == "int":
            knobs[kf["name"]] = get_int({kf["name"]: raw_knobs.get(kf["name"], kf["default"])}, kf["name"], kf["label"], 1, 5000)
        else:
            knobs[kf["name"]] = get_float({kf["name"]: raw_knobs.get(kf["name"], kf["default"])}, kf["name"], kf["label"], 1e-15 if "tol" in kf["name"] else None)
    if cid == "integration":
        if knobs["n"] % 4 != 0:
            raise NumericalError("Subintervals n must be a multiple of 4 (needed for Simpson and Boole).")
        knobs["gauss_points"] = min(knobs["gauss_points"], 20)
    if cid == "ode":
        h = knobs["h"]
        if h <= 0 or h > 1 or abs(2 / h - round(2 / h)) > 1e-9:
            raise NumericalError("Choose h so that 2/h is a whole number (for example 0.5, 0.25, 0.2, 0.1, 0.05).")
    if cid == "optimization" and knobs["alpha"] <= 0:
        raise NumericalError("The step size must be positive.")

    store = {}
    runners = {"root": root_runners, "integration": integration_runners, "ode": ode_runners, "linear": linear_runners, "optimization": optimization_runners}
    if cid == "interpolation":
        runners_map, store = interp_runners(knobs["xe"])
        reference = math.sin(knobs["xe"])
    else:
        runners_map = runners[cid]()
        reference = c["reference"]["value"]

    results = []
    for mid in method_ids:
        fn = runners_map[mid]
        try:
            r = fn(knobs)
        except NumericalError as e:
            results.append({"id": mid, "name": c["methods"][mid], "failed": True, "message": str(e)})
            continue
        r.update(id=mid, name=c["methods"][mid], abs_error=_err(r["value"], reference), time_ms=_timed(fn, knobs))
        if callable(r["curve"]):
            r["curve"] = r["curve"]()
        if cid == "ode" and r["curve"]:
            ys = r["curve"]["y"]
            r["extra"] = [{"label": "Observed order (h = 0.05 → 0.025)", "value": math.log2(ys[-2] / ys[-1]) if ys[-1] > 1e-16 else None}]
        results.append(r)
    ok = [r for r in results if not r.get("failed")]
    ranking = [r["id"] for r in sorted(ok, key=lambda r: (r["abs_error"], r["time_ms"]))]
    fastest = min(ok, key=lambda r: r["time_ms"])["id"] if ok else None
    fewest = min((r for r in ok if r.get("evaluations") or r.get("iterations")), key=lambda r: r.get("evaluations") or r.get("iterations"), default=None)

    pspec = c["plot"]
    plot = None
    if cid == "interpolation":
        exact_curve = {"label": "exact sin(x)", "x": GRID, "y": np.sin(GRID), "color": "#E8E8F2", "lw": 1.4, "ls": ":"}
        plot = {"kind": "curves", "curves": [exact_curve] + [dict(store[r["id"]]) for r in ok if r["id"] in store],
                "points": {"x": XS, "y": YS}, "highlight": (knobs["xe"], reference, f"sin({knobs['xe']:g}) exact"), "title": "Interpolants vs the true function"}
    elif cid == "linear":
        plot = {"kind": "bars", "labels": [r["name"].replace(" ", "\n", 1) for r in ok], "values": [max(r["abs_error"], 1e-17) for r in ok], "logy": True,
                "ylabel": "‖x − x*‖₂", "title": "Accuracy of each method (lower is better)"}
    else:
        lines = [{"label": r["name"], "x": r["curve"]["x"], "y": r["curve"]["y"]} for r in ok if r.get("curve")]
        plot = {"kind": "series", "lines": lines, **{k: v for k, v in pspec.items()}}
    if cid == "linear":                       # also show iterative convergence in the extra payload for the UI
        pass
    image = render(plot) if plot and (plot.get("lines") != [] if plot["kind"] == "series" else True) else None
    for r in results:
        if r.get("curve") is not None:
            r["curve"] = {"x": list(r["curve"]["x"]), "y": list(r["curve"]["y"])}
    return to_plain({
        "challenge": cid, "title": c["title"], "reference": {"label": c["reference"]["label"] if cid != "interpolation" else f"Exact sin({knobs['xe']:g})", "value": reference},
        "results": results, "ranking": ranking, "fastest": fastest,
        "fewest_work": fewest["id"] if fewest else None, "plot": image, "knobs": knobs,
    })
