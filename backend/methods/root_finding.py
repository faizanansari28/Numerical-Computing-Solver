"""Root finding: solve f(x) = 0.

Methods: Bisection, Fixed-Point Iteration, Newton-Raphson, Secant.
Part 1 of this file = the algorithms (plain Python, easy to read).
Part 2 (bottom)     = adapters that connect the algorithms to the website.
"""
import math

from scipy.optimize import brentq, fsolve

from utils.errors import NumericalError
from utils.inputs import field, g, get_expr, get_float, get_int
from utils.results import answer, finish
from utils.symbolic import derivative, numeric_derivative


# ===================================================== PART 1: ALGORITHMS
def bisection(f, a, b, tol=1e-6, max_iter=100):
    if a >= b:
        raise NumericalError("The left end a must be smaller than the right end b.")
    fa = f(a)
    fb = f(b)
    if fa * fb > 0:
        raise NumericalError(
            f"f(a) = {g(fa)} and f(b) = {g(fb)} have the same sign, so [a, b] is not guaranteed to contain a root "
            f"(Intermediate Value Theorem). Choose a and b where f changes sign.")
    rows, xs, brackets, steps = [], [], [], []
    converged = False
    c = a
    for i in range(1, max_iter + 1):
        c = (a + b) / 2
        fc = f(c)
        half_width = (b - a) / 2
        rows.append([i, a, b, c, fc, half_width])
        xs.append(c)
        brackets.append((a, b))
        if i <= 4:
            keep = "[a, c]" if fa * fc < 0 else "[c, b]"
            steps.append(f"Iteration {i}: c = (a + b)/2 = ({g(a)} + {g(b)})/2 = {g(c)}, f(c) = {g(fc)}. "
                         f"The sign change is in {keep}, so the interval is halved.")
        if fc == 0 or half_width < tol:
            converged = True
            break
        if fa * fc < 0:
            b, fb = c, fc
        else:
            a, fa = c, fc
    need = math.ceil(math.log2((rows[0][2] - rows[0][1]) / tol)) if tol > 0 else 0
    steps.append(f"The interval shrinks by half every step, so about log2((b-a)/tol) = {need} iterations are needed for tol = {g(tol)}.")
    return {
        "answers": [answer("Root", c)], "steps": steps, "iterations": len(rows), "converged": converged,
        "columns": ["i", "a", "b", "c = (a+b)/2", "f(c)", "(b-a)/2"], "rows": rows,
        "plot": {"kind": "root", "f": f, "xs": xs, "root": c, "brackets": brackets},
        "iterates": xs, "notes": [f"Theory predicts at most {need} iterations; the method used {len(rows)}."],
    }


def fixed_point(gfun, x0, tol=1e-6, max_iter=100):
    x = x0
    rows, xs, steps = [], [x0], []
    converged = False
    for i in range(1, max_iter + 1):
        x_new = gfun(x)
        change = abs(x_new - x)
        rows.append([i, x, x_new, change])
        xs.append(x_new)
        if i <= 4:
            steps.append(f"Iteration {i}: x_{i} = g(x_{i-1}) = g({g(x)}) = {g(x_new)}, change = {g(change)}.")
        if abs(x_new) > 1e12:
            raise NumericalError("The iteration is diverging (values are exploding). Try a different rearrangement g(x) or another starting value.")
        x = x_new
        if change < tol:
            converged = True
            break
    slope = numeric_derivative(gfun, x) if converged else None
    notes = []
    if slope is not None:
        verdict = "converges (|g'| < 1)" if abs(slope) < 1 else "may NOT converge (|g'| >= 1)"
        notes.append(f"Near the fixed point |g'(x*)| ≈ {g(abs(slope), 4)}, so the iteration {verdict}.")
    return {
        "answers": [answer("Fixed point x*", x)], "steps": steps, "iterations": len(rows), "converged": converged,
        "columns": ["i", "x_(i-1)", "x_i = g(x_(i-1))", "|x_i - x_(i-1)|"], "rows": rows,
        "plot": {"kind": "fixedpoint", "g": gfun, "xs": xs}, "iterates": xs[1:], "notes": notes,
        "metrics": [{"label": "|g'(x*)|", "value": abs(slope)}] if slope is not None else [],
    }


def newton(f, df, x0, tol=1e-8, max_iter=50):
    x = x0
    rows, xs, lines, steps = [], [x0], [], []
    converged = False
    for i in range(1, max_iter + 1):
        fx = f(x)
        dfx = df(x)
        if abs(dfx) < 1e-14:
            raise NumericalError(f"f'(x) is (almost) zero at x = {g(x)}, so the Newton step would divide by zero. Choose a different starting value.")
        x_new = x - fx / dfx
        change = abs(x_new - x)
        rows.append([i - 1, x, fx, dfx, x_new, change])
        lines.append(((x, fx), (x_new, 0.0)))
        xs.append(x_new)
        if i <= 4:
            steps.append(f"Iteration {i}: x_{i} = x_{i-1} - f/f' = {g(x)} - ({g(fx)})/({g(dfx)}) = {g(x_new)}.")
        x = x_new
        if change < tol:
            converged = True
            break
    return {
        "answers": [answer("Root", x)], "steps": steps, "iterations": len(rows), "converged": converged,
        "columns": ["n", "x_n", "f(x_n)", "f'(x_n)", "x_(n+1)", "|x_(n+1) - x_n|"], "rows": rows,
        "plot": {"kind": "root", "f": f, "xs": xs, "root": x, "lines": lines}, "iterates": xs[1:],
    }


def secant(f, x0, x1, tol=1e-8, max_iter=50):
    if x0 == x1:
        raise NumericalError("The two starting values x0 and x1 must be different.")
    rows, xs, lines, steps = [], [x0, x1], [], []
    converged = False
    f0, f1 = f(x0), f(x1)
    for i in range(1, max_iter + 1):
        if abs(f1 - f0) < 1e-14:
            raise NumericalError(f"f(x_n) and f(x_(n-1)) are equal ({g(f1)}), so the secant line is horizontal and the denominator is zero. Choose different starting values.")
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        change = abs(x2 - x1)
        rows.append([i, x0, x1, f0, f1, x2, change])
        lines.append(((x0, f0), (x2, 0.0)))
        xs.append(x2)
        if i <= 4:
            steps.append(f"Iteration {i}: x = x1 - f(x1)(x1 - x0)/(f(x1) - f(x0)) = {g(x1)} - ({g(f1)})({g(x1 - x0)})/({g(f1 - f0)}) = {g(x2)}.")
        x0, f0 = x1, f1
        x1, f1 = x2, f(x2)
        if change < tol:
            converged = True
            break
    return {
        "answers": [answer("Root", x1)], "steps": steps, "iterations": len(rows), "converged": converged,
        "columns": ["i", "x_(i-1)", "x_i", "f(x_(i-1))", "f(x_i)", "x_(i+1)", "|x_(i+1) - x_i|"], "rows": rows,
        "plot": {"kind": "root", "f": f, "xs": xs, "root": x1, "lines": lines}, "iterates": xs[2:],
    }


# ===================================================== PART 2: WEBSITE ADAPTERS
def reference_root(f, guess):
    """Independent check with SciPy: brentq if a sign change is found near the guess, else fsolve."""
    try:
        for w in (0.01, 0.1, 0.5, 1, 2, 5, 10, 50):
            lo, hi = guess - w, guess + w
            try:
                if f(lo) * f(hi) < 0:
                    return brentq(f, lo, hi, xtol=1e-14), "SciPy brentq"
            except NumericalError:
                continue
        return float(fsolve(lambda v: f(float(v[0])), guess, xtol=1e-14)[0]), "SciPy fsolve"
    except NumericalError:
        return None, None


def order_note(xs, root):
    errors = [abs(x - root) for x in xs]
    errors = [e for e in errors if e > 1e-13]
    if len(errors) >= 3:
        p = math.log(errors[-1] / errors[-2]) / math.log(errors[-2] / errors[-3])
        return [f"Estimated order of convergence ≈ {p:.2f} (1 = linear, 1.618 = superlinear, 2 = quadratic)."]
    return []


def _finish_root(raw, f, guess, with_order=False):
    root, label = reference_root(f, guess)
    ref = {"label": label, "value": root, "exact": False} if root is not None else None
    if with_order and root is not None:
        raw["notes"] = raw.get("notes", []) + order_note(raw["iterates"], root)
    return finish(raw, ref)


def run_bisection(p):
    f = get_expr(p, "f")
    a, b = get_float(p, "a", "a"), get_float(p, "b", "b")
    tol = get_float(p, "tol", "Tolerance", 1e-15)
    return _finish_root(bisection(f, a, b, tol, get_int(p, "max_iter", "Max iterations", 1, 1000)), f, (a + b) / 2)


def run_fixed_point(p):
    gf = get_expr(p, "g")
    x0 = get_float(p, "x0", "Initial guess")
    raw = fixed_point(gf, x0, get_float(p, "tol", "Tolerance", 1e-15), get_int(p, "max_iter", "Max iterations", 1, 1000))
    root = raw["answers"][0]["value"]
    return _finish_root(raw, lambda v: v - gf(v), root, with_order=True)


def run_newton(p):
    f = get_expr(p, "f")
    x0 = get_float(p, "x0", "Initial guess")
    text = str(p.get("df", "")).strip()
    note = ""
    if text:
        d = get_expr(p, "df")
        note = "Derivative supplied by you."
    else:
        d = derivative(f)
        note = f"Derivative computed symbolically: f'(x) = {d.pretty()}" if d else ""
        if d is None:
            d = lambda v: numeric_derivative(f, v)
            note = "Derivative approximated with a central difference (this expression cannot be differentiated symbolically)."
    raw = newton(f, d, x0, get_float(p, "tol", "Tolerance", 1e-15), get_int(p, "max_iter", "Max iterations", 1, 500))
    raw["notes"] = [note]
    return _finish_root(raw, f, raw["answers"][0]["value"], with_order=True)


def run_secant(p):
    f = get_expr(p, "f")
    raw = secant(f, get_float(p, "x0", "x0"), get_float(p, "x1", "x1"), get_float(p, "tol", "Tolerance", 1e-15),
                 get_int(p, "max_iter", "Max iterations", 1, 500))
    return _finish_root(raw, f, raw["answers"][0]["value"], with_order=True)


TOL = field("tol", "Tolerance", "number", "1e-8", "Stop when the step/interval is smaller than this.")
MAXIT = field("max_iter", "Maximum iterations", "int", "50", "Safety limit.")

SPECS = {
    "bisection": {
        "name": "Bisection Method", "category": "root", "run": run_bisection,
        "formula": r"c = \dfrac{a+b}{2},\quad f(a)f(c)<0 \Rightarrow b=c,\ \text{else } a=c",
        "inputs": [field("f", "Function f(x)", "expr", "x**3 - x - 2", "Example: x^3 - x - 2, cos(x) - x, exp(x) - 3"),
                   field("a", "Left end a", "number", "1"), field("b", "Right end b", "number", "2", "f(a) and f(b) must have opposite signs."),
                   TOL, field("max_iter", "Maximum iterations", "int", "100")],
    },
    "fixed_point": {
        "name": "Fixed-Point Iteration", "category": "root", "run": run_fixed_point,
        "formula": r"x_{n+1} = g(x_n),\qquad |g'(x^*)|<1 \Rightarrow \text{convergence}",
        "inputs": [field("g", "Iteration function g(x)", "expr", "(x+2)**(1/3)", "Rearrange f(x)=0 into x = g(x). For x^3 - x - 2 = 0 use g(x) = (x+2)^(1/3)."),
                   field("x0", "Initial guess x0", "number", "1.5"), TOL, field("max_iter", "Maximum iterations", "int", "100")],
    },
    "newton": {
        "name": "Newton-Raphson Method", "category": "root", "run": run_newton,
        "formula": r"x_{n+1} = x_n - \dfrac{f(x_n)}{f'(x_n)}",
        "inputs": [field("f", "Function f(x)", "expr", "x**3 - x - 2"),
                   field("df", "Derivative f'(x) (optional)", "expr", "", "Leave empty and NUMERIQ differentiates f(x) for you.", optional=True),
                   field("x0", "Initial guess x0", "number", "1.5"), TOL, MAXIT],
    },
    "secant": {
        "name": "Secant Method", "category": "root", "run": run_secant,
        "formula": r"x_{n+1} = x_n - f(x_n)\,\dfrac{x_n - x_{n-1}}{f(x_n)-f(x_{n-1})}",
        "inputs": [field("f", "Function f(x)", "expr", "x**3 - x - 2"),
                   field("x0", "First guess x0", "number", "1"), field("x1", "Second guess x1", "number", "2"), TOL, MAXIT],
    },
}
