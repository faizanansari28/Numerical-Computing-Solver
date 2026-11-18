"""Unconstrained optimization: gradient descent, conjugate gradient, Newton's method."""
import math

import numpy as np
from scipy.optimize import minimize

from methods.linear_algebra import solve_linear
from utils import matrix as mx
from utils.errors import NumericalError
from utils.inputs import field, g, get_expr, get_float, get_int, get_matrix, get_select, get_vector
from utils.results import answer, finish
from utils.symbolic import derivative

VARS = ("x", "y")


class Quadratic:
    """f(x,y) = 1/2 xᵀAx − bᵀx  (only used to draw contour plots)."""
    def __init__(self, A, b):
        self.A, self.b = np.array(A, float), np.array(b, float)

    def vec(self, X, Y):
        P = np.stack([X, Y])
        return 0.5 * np.einsum("i...,ij,j...->...", P, self.A, P) - self.b[0] * X - self.b[1] * Y

    def pretty(self):
        return "½xᵀAx − bᵀx"


def gradient_function(f):
    """Returns (grad(x,y) -> [fx, fy], description). Exact if possible, else central differences."""
    dx, dy = derivative(f, "x"), derivative(f, "y")
    if dx is not None and dy is not None:
        return (lambda x, y: [dx(x, y), dy(x, y)]), f"exact partial derivatives: f_x = {dx.pretty()},  f_y = {dy.pretty()}"
    h = 1e-6
    return (lambda x, y: [(f(x + h, y) - f(x - h, y)) / (2 * h), (f(x, y + h) - f(x, y - h)) / (2 * h)]), "central finite differences"


def hessian_function(f):
    out = []
    for v1 in VARS:
        d1 = derivative(f, v1)
        out.append([derivative(d1, v2) if d1 is not None else None for v2 in VARS])
    if all(e is not None for row in out for e in row):
        return (lambda x, y: [[out[i][j](x, y) for j in range(2)] for i in range(2)]), "exact second derivatives"
    h = 1e-4
    def H(x, y):
        fxx = (f(x + h, y) - 2 * f(x, y) + f(x - h, y)) / h ** 2
        fyy = (f(x, y + h) - 2 * f(x, y) + f(x, y - h)) / h ** 2
        fxy = (f(x + h, y + h) - f(x + h, y - h) - f(x - h, y + h) + f(x - h, y - h)) / (4 * h * h)
        return [[fxx, fxy], [fxy, fyy]]
    return H, "finite-difference Hessian"


# ===================================================== PART 1: ALGORITHMS
def gradient_descent(f, grad, start, alpha, tol, max_iter, line_search):
    x, y = start
    path, rows, steps = [(x, y)], [], []
    converged = False
    for k in range(max_iter + 1):
        gx, gy = grad(x, y)
        gnorm = math.hypot(gx, gy)
        fx = f(x, y)
        rows.append([k, x, y, fx, gnorm, alpha if line_search == "fixed" else None])
        if gnorm < tol:
            converged = True
            break
        if k == max_iter:
            break
        step = alpha
        if line_search == "backtracking":
            step = 1.0
            while step > 1e-12:
                try:
                    if f(x - step * gx, y - step * gy) <= fx - 1e-4 * step * gnorm ** 2:
                        break
                except NumericalError:
                    pass
                step /= 2
        rows[-1][5] = step
        x, y = x - step * gx, y - step * gy
        if not (math.isfinite(x) and math.isfinite(y)) or abs(x) > 1e100 or abs(y) > 1e100:
            raise NumericalError("Gradient descent diverged. Use a smaller step size or the backtracking line search.")
        path.append((x, y))
        if k < 3:
            steps.append(f"Iteration {k + 1}: gradient = ({g(gx)}, {g(gy)}), step {g(step)} → new point ({g(x)}, {g(y)}).")
    steps.insert(0, "Steepest descent: move against the gradient, (x, y) ← (x, y) − α·∇f(x, y). Stop when ‖∇f‖ < tolerance.")
    return {
        "answers": [answer("Minimiser (x, y)", [x, y]), answer("Minimum value f", f(x, y))], "steps": steps, "iterations": len(rows) - 1, "converged": converged,
        "columns": ["k", "x", "y", "f(x, y)", "‖∇f‖", "step α"], "rows": rows, "path": path,
        "plot": {"kind": "contour", "f": f, "path": path},
        "history": [r[4] for r in rows],
    }


def conjugate_gradient(A, b, x0, tol, max_iter):
    n = len(A)
    if len(A) != len(A[0]) or len(b) != n or len(x0) != n:
        raise NumericalError("A must be square and b, x0 must have the same size.")
    if not mx.is_symmetric(A):
        raise NumericalError("The conjugate gradient method needs a SYMMETRIC matrix A.")
    if np.min(np.linalg.eigvalsh(np.array(A, float))) <= 0:
        raise NumericalError("The matrix A must be positive definite (all eigenvalues > 0) so that the quadratic has a minimum.")
    x = x0[:]
    r = mx.vec_sub(b, mx.mat_vec(A, x))
    d = r[:]
    rr = mx.dot(r, r)
    rows, path, history, steps = [], [tuple(x)], [], []
    converged = False
    rows.append([0] + x + [math.sqrt(rr), "", ""])
    history.append(math.sqrt(rr))
    if math.sqrt(rr) < tol:
        converged = True
    for k in range(1, max_iter + 1):
        if converged:
            break
        Ad = mx.mat_vec(A, d)
        alpha = rr / mx.dot(d, Ad)
        x = [xi + alpha * di for xi, di in zip(x, d)]
        r = [ri - alpha * ai for ri, ai in zip(r, Ad)]
        rr_new = mx.dot(r, r)
        beta = rr_new / rr
        d = [ri + beta * di for ri, di in zip(r, d)]
        rows.append([k] + x + [math.sqrt(rr_new), alpha, beta])
        history.append(math.sqrt(rr_new))
        path.append(tuple(x))
        if k <= 2:
            steps.append(f"Iteration {k}: α = rᵀr/(dᵀAd) = {g(alpha)}, new x = [" + ", ".join(g(v, 6) for v in x) + f"], residual = {g(math.sqrt(rr_new))}, β = {g(beta)}.")
        rr = rr_new
        if math.sqrt(rr) < tol:
            converged = True
            break
    steps.insert(0, "CG minimises ½xᵀAx − bᵀx (equivalent to solving Ax = b). Start with residual r = b − Ax and direction d = r.")
    steps.append("Each step: α = rᵀr/(dᵀAd), x ← x + αd, r ← r − αAd, β = r_newᵀr_new/rᵀr, d ← r + βd. The directions are A-conjugate.")
    steps.append(f"In exact arithmetic CG finishes in at most n = {n} iterations; here it used {len(rows) - 1}.")
    plot = ({"kind": "contour", "f": Quadratic(A, b), "path": path} if n == 2 else
            {"kind": "series", "lines": [{"label": "‖r‖", "x": list(range(len(history))), "y": history}], "logy": True, "title": "Residual norm"})
    return {
        "answers": [answer("Minimiser x", x)], "steps": steps, "iterations": len(rows) - 1, "converged": converged,
        "columns": ["k"] + [f"x{i + 1}" for i in range(n)] + ["‖r‖", "α", "β"], "rows": rows,
        "plot": plot, "path": path, "history": history,
        "metrics": [{"label": "Residual ‖b − Ax‖₂", "value": mx.norm2(mx.vec_sub(b, mx.mat_vec(A, x)))}],
    }


def newton_optimization(f, grad, hess, start, tol, max_iter):
    x, y = start
    path, rows, steps = [(x, y)], [], []
    converged, notes = False, []
    for k in range(max_iter + 1):
        gx, gy = grad(x, y)
        gnorm = math.hypot(gx, gy)
        rows.append([k, x, y, f(x, y), gnorm])
        if gnorm < tol:
            converged = True
            break
        if k == max_iter:
            break
        H = hess(x, y)
        if abs(H[0][0] * H[1][1] - H[0][1] * H[1][0]) < 1e-14:
            raise NumericalError("The Hessian is singular at the current point, so the Newton step cannot be computed.")
        step = solve_linear(H, [-gx, -gy])
        if not (H[0][0] > 0 and H[0][0] * H[1][1] - H[0][1] ** 2 > 0) and "indef" not in "".join(notes):
            notes.append("At some iteration the Hessian was not positive definite, so the Newton step may point to a maximum or saddle point.")
        x, y = x + step[0], y + step[1]
        if abs(x) > 1e100 or abs(y) > 1e100:
            raise NumericalError("Newton's method diverged. Try another starting point.")
        path.append((x, y))
        if k < 3:
            steps.append(f"Iteration {k + 1}: solve H·p = −∇f with H = {[[round(v, 4) for v in r] for r in H]}, ∇f = ({g(gx)}, {g(gy)}) → p = ({g(step[0])}, {g(step[1])}).")
    steps.insert(0, "Newton's method for optimisation: solve H(x)·p = −∇f(x) and update x ← x + p, where H is the Hessian (matrix of second derivatives).")
    return {
        "answers": [answer("Critical point (x, y)", [x, y]), answer("Value f", f(x, y))], "steps": steps, "iterations": len(rows) - 1, "converged": converged,
        "columns": ["k", "x", "y", "f(x, y)", "‖∇f‖"], "rows": rows, "notes": notes, "path": path,
        "plot": {"kind": "contour", "f": f, "path": path}, "history": [r[4] for r in rows],
    }


# ===================================================== PART 2: WEBSITE ADAPTERS
def _reference_min(f, start):
    res = minimize(lambda v: f(float(v[0]), float(v[1])), list(start), method="BFGS", tol=1e-12)
    return {"label": "SciPy minimize (BFGS)", "value": [float(res.x[0]), float(res.x[1])], "exact": False}


def _common(p):
    f = get_expr(p, "f", VARS)
    start = (get_float(p, "x0", "Initial x"), get_float(p, "y0", "Initial y"))
    return f, start, get_float(p, "tol", "Tolerance", 1e-15), get_int(p, "max_iter", "Max iterations", 1, 20000)


def run_gradient(p):
    f, start, tol, max_iter = _common(p)
    grad, how = gradient_function(f)
    raw = gradient_descent(f, grad, start, get_float(p, "alpha", "Step size α", 1e-12), tol, max_iter, get_select(p, "line_search", ["fixed", "backtracking"], "fixed"))
    raw["notes"] = [f"Gradient from {how}."] + (["Stopped at the iteration limit before ‖∇f‖ < tol; try more iterations or a larger step."] if not raw["converged"] else [])
    return finish(raw, _reference_min(f, start))


def run_cg(p):
    A = get_matrix(p, "A", "A", square=True)
    b = get_vector(p, "b", "b", len(A))
    x0 = get_vector(p, "x0", "x0", len(A))
    raw = conjugate_gradient(A, b, x0, get_float(p, "tol", "Tolerance", 1e-15), get_int(p, "max_iter", "Max iterations", 1, 5000))
    return finish(raw, {"label": "NumPy linalg.solve", "value": np.linalg.solve(np.array(A, float), np.array(b, float)).tolist(), "exact": False})


def run_newton_opt(p):
    f, start, tol, max_iter = _common(p)
    grad, how = gradient_function(f)
    hess, how2 = hessian_function(f)
    raw = newton_optimization(f, grad, hess, start, tol, max_iter)
    raw["notes"] = raw["notes"] + [f"Gradient: {how}. Hessian: {how2}."]
    return finish(raw, _reference_min(f, start))


FUNC = field("f", "Objective f(x, y)", "expr", "(x-1)**2 + 2*(y+2)**2 + x*y", "Variables x and y.", vars=["x", "y"])
START = [field("x0", "Initial x", "number", "0"), field("y0", "Initial y", "number", "0"), field("tol", "Tolerance on ‖∇f‖", "number", "1e-8"),
         field("max_iter", "Maximum iterations", "int", "500")]

SPECS = {
    "gradient": {"name": "Gradient Descent", "category": "optim", "run": run_gradient,
                 "formula": r"\mathbf{x}_{k+1}=\mathbf{x}_k-\alpha\,\nabla f(\mathbf{x}_k)",
                 "inputs": [FUNC] + START[:2] + [field("alpha", "Step size α", "number", "0.1"),
                            field("line_search", "Step rule", "select", "fixed", "", options=[{"value": "fixed", "label": "Fixed α"}, {"value": "backtracking", "label": "Backtracking line search"}])] + START[2:]},
    "cg": {"name": "Conjugate Gradient Method", "category": "optim", "run": run_cg,
           "formula": r"\alpha_k=\dfrac{r_k^Tr_k}{d_k^TAd_k},\ x_{k+1}=x_k+\alpha_kd_k,\ \beta_k=\dfrac{r_{k+1}^Tr_{k+1}}{r_k^Tr_k}",
           "inputs": [field("A", "Symmetric positive definite matrix A", "matrix", "4, 1\n1, 3"), field("b", "Vector b", "list", "1, 2"),
                      field("x0", "Starting vector", "list", "0, 0"), field("tol", "Tolerance", "number", "1e-10"), field("max_iter", "Maximum iterations", "int", "100")]},
    "newton_opt": {"name": "Newton's Method in Optimization", "category": "optim", "run": run_newton_opt,
                   "formula": r"H(\mathbf{x}_k)\,\mathbf{p}_k=-\nabla f(\mathbf{x}_k),\quad \mathbf{x}_{k+1}=\mathbf{x}_k+\mathbf{p}_k",
                   "inputs": [FUNC] + START},
}
