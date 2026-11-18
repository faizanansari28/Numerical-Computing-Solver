"""Eigenvalue approximation: power method, inverse power method, shifted inverse power method.
Also contains a small Jacobi eigenvalue routine for symmetric matrices (used by the SVD)."""
import math

import numpy as np

from methods.linear_algebra import check_system, solve_linear
from utils import matrix as mx
from utils.errors import NumericalError
from utils.inputs import field, g, get_float, get_int, get_matrix, get_select, get_vector
from utils.results import answer, finish


# ===================================================== PART 1: ALGORITHMS
def power_method(A, x0, variant="power", shift=0.0, tol=1e-10, max_iter=500):
    n = len(A)
    check_system(A)
    if len(x0) != n or mx.norm_inf(x0) == 0:
        raise NumericalError(f"The starting vector must be non-zero and have {n} entries.")
    B = [row[:] for row in A]
    if variant != "power":
        for i in range(n):
            B[i][i] -= shift                        # (A - μI)
    x = [v / mx.norm_inf(x0) for v in x0]
    lam_old, rows, history = None, [], []
    converged = False
    lam = 0.0
    for k in range(1, max_iter + 1):
        y = mx.mat_vec(A, x) if variant == "power" else solve_linear(B, x)      # y = A x   or   y = (A - μI)^-1 x
        big = max(y, key=abs)
        if big == 0:
            raise NumericalError("The iteration collapsed to the zero vector (the start vector may be an eigenvector for eigenvalue 0).")
        x = [v / big for v in y]                                                # normalise so the largest entry is 1
        Ax = mx.mat_vec(A, x)
        lam = mx.dot(x, Ax) / mx.dot(x, x)                                      # Rayleigh quotient
        change = abs(lam - lam_old) if lam_old is not None else float("nan")
        rows.append([k] + x + [lam, change])
        history.append(change if lam_old is not None else 1.0)
        if lam_old is not None and change < tol:
            converged = True
            break
        lam_old = lam
    steps = {"power": "Power method: repeat y = A x, then scale x = y / (largest entry of y). x tends to the dominant eigenvector.",
             "inverse": "Inverse power method: repeat solve A y = x, then scale. It finds the eigenvalue of SMALLEST magnitude.",
             "shifted": f"Shifted inverse power method: solve (A - {g(shift)}I) y = x each step. It finds the eigenvalue CLOSEST to the shift {g(shift)}."}[variant]
    steps = [steps, "Eigenvalue estimate = Rayleigh quotient λ = xᵀAx / xᵀx.", f"After {len(rows)} iterations λ ≈ {g(lam, 10)}, eigenvector ≈ [" + ", ".join(g(v, 6) for v in x) + "]."]
    return {
        "answers": [answer("Eigenvalue λ", lam), answer("Eigenvector x (largest entry = 1)", x)], "steps": steps,
        "iterations": len(rows), "converged": converged,
        "columns": ["k"] + [f"x{i + 1}" for i in range(n)] + ["λ (Rayleigh)", "|Δλ|"], "rows": rows,
        "metrics": [{"label": "Residual ‖Ax − λx‖∞", "value": mx.norm_inf([a - lam * b for a, b in zip(mx.mat_vec(A, x), x)])}],
        "plot": {"kind": "series", "lines": [{"label": "|Δλ|", "x": list(range(2, len(rows) + 1)), "y": [r[-1] for r in rows[1:]]}],
                 "logy": True, "title": "Convergence of the eigenvalue estimate"},
        "history": history,
    }


def jacobi_eigen(S, tol=1e-14, max_sweeps=60):
    """Eigen-decomposition of a symmetric matrix by Jacobi rotations. Returns (values, vectors-as-columns)."""
    n = len(S)
    A = [row[:] for row in S]
    V = mx.identity(n)
    for _ in range(max_sweeps):
        off = sum(A[i][j] ** 2 for i in range(n) for j in range(n) if i != j)
        if off < tol:
            break
        for p in range(n - 1):
            for q in range(p + 1, n):
                if abs(A[p][q]) < 1e-300:
                    continue
                theta = (A[q][q] - A[p][p]) / (2 * A[p][q])
                t = (1 if theta >= 0 else -1) / (abs(theta) + math.sqrt(theta * theta + 1))
                c = 1 / math.sqrt(t * t + 1)
                s = t * c
                for k in range(n):                      # rotate columns p, q
                    akp, akq = A[k][p], A[k][q]
                    A[k][p], A[k][q] = c * akp - s * akq, s * akp + c * akq
                for k in range(n):                      # rotate rows p, q
                    apk, aqk = A[p][k], A[q][k]
                    A[p][k], A[q][k] = c * apk - s * aqk, s * apk + c * aqk
                for k in range(n):
                    vkp, vkq = V[k][p], V[k][q]
                    V[k][p], V[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    return [A[i][i] for i in range(n)], V


# ===================================================== PART 2: WEBSITE ADAPTERS
def run_power(p):
    A = get_matrix(p, "A", "A", square=True)
    x0 = get_vector(p, "x0", "Starting vector", len(A))
    variant = get_select(p, "variant", ["power", "inverse", "shifted"], "power")
    shift = get_float(p, "shift", "Shift μ") if variant == "shifted" else 0.0
    raw = power_method(A, x0, variant, shift, get_float(p, "tol", "Tolerance", 1e-15), get_int(p, "max_iter", "Max iterations", 1, 5000))
    vals, vecs = np.linalg.eig(np.array(A, float))
    target = {"power": lambda v: -abs(v), "inverse": lambda v: abs(v), "shifted": lambda v: abs(v - shift)}[variant]
    idx = min(range(len(vals)), key=lambda i: target(vals[i]))
    ref = vals[idx]
    srt = sorted(vals, key=lambda v: -abs(v))
    if abs(ref.imag) > 1e-9:
        raw["notes"] = ["The target eigenvalue is complex - the real iteration cannot converge to it."]
        raw["converged"] = False
        return finish(raw)
    if variant == "power" and len(srt) > 1 and abs(srt[0]) > 0:
        raw["notes"] = [f"Convergence speed depends on |λ2/λ1| = {g(abs(srt[1]) / abs(srt[0]), 4)} (smaller = faster)."]
    return finish(raw, {"label": "NumPy linalg.eig", "value": float(ref.real), "exact": False})


SPECS = {
    "eigen": {"name": "Eigenvalue Approximation", "category": "optim", "run": run_power,
              "formula": r"x_{k+1}=\dfrac{Ax_k}{\|Ax_k\|_\infty},\qquad \lambda\approx\dfrac{x^TAx}{x^Tx}",
              "inputs": [field("A", "Matrix A", "matrix", "4, 1\n2, 3", "Square matrix."), field("x0", "Starting vector", "list", "1, 1"),
                         field("variant", "Method", "select", "power", "", options=[
                             {"value": "power", "label": "Power method (largest |λ|)"}, {"value": "inverse", "label": "Inverse power (smallest |λ|)"},
                             {"value": "shifted", "label": "Shifted inverse power (λ nearest μ)"}]),
                         field("shift", "Shift μ (shifted method only)", "number", "2.5", showIf={"variant": "shifted"}),
                         field("tol", "Tolerance", "number", "1e-10"), field("max_iter", "Maximum iterations", "int", "200")]},
}
