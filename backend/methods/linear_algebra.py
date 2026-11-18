"""Numerical linear algebra: solve A x = b and study matrices.

Methods: Gaussian elimination, pivoting strategies, LU (Doolittle), Cholesky, matrix inverse (Gauss-Jordan),
iterative methods (Jacobi / Gauss-Seidel), matrix conditioning, condition number.
"""
import math

import numpy as np

from utils import matrix as mx
from utils.errors import NumericalError
from utils.inputs import field, g, get_float, get_int, get_matrix, get_select, get_vector
from utils.results import answer, finish


def check_system(A, b=None):
    n = len(A)
    if any(len(row) != n for row in A):
        raise NumericalError(f"Matrix A must be square (it is {len(A)} x {len(A[0])}).")
    if b is not None and len(b) != n:
        raise NumericalError(f"Vector b must have {n} entries (it has {len(b)}).")


def solve_linear(A, b):
    """Short helper used by other modules: Gaussian elimination with partial pivoting."""
    n = len(A)
    M = [A[i][:] + [b[i]] for i in range(n)]
    for k in range(n):
        p = max(range(k, n), key=lambda i: abs(M[i][k]))
        if abs(M[p][k]) < 1e-13 * max(1.0, max(abs(v) for row in A for v in row)):
            raise NumericalError("The matrix is singular (or nearly singular): there is no unique solution.")
        M[k], M[p] = M[p], M[k]
        for i in range(k + 1, n):
            m = M[i][k] / M[k][k]
            for j in range(k, n + 1):
                M[i][j] -= m * M[k][j]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]
    return x


def residual(A, x, b):
    return mx.norm_inf(mx.vec_sub(mx.mat_vec(A, x), b))


# ===================================================== PART 1: ALGORITHMS
def eliminate(A, b, pivoting="partial"):
    n = len(A)
    check_system(A, b)
    M = [A[i][:] + [b[i]] for i in range(n)]
    order = list(range(n))                     # remembers column swaps (complete pivoting)
    scale = max(1e-300, max(abs(v) for row in A for v in row))
    stages, steps, swaps, max_mult, det_sign = [], [], 0, 0.0, 1
    pivots = []
    for k in range(n):
        p_row, p_col = k, k
        if pivoting == "partial":
            p_row = max(range(k, n), key=lambda i: abs(M[i][k]))
        elif pivoting == "complete":
            best = max(((i, j) for i in range(k, n) for j in range(k, n)), key=lambda ij: abs(M[ij[0]][ij[1]]))
            p_row, p_col = best
        pivot = M[p_row][p_col]
        if pivot == 0 or (pivoting != "none" and abs(pivot) < 1e-13 * scale):
            if pivoting == "none":
                raise NumericalError(f"Zero pivot at step {k + 1}: elimination without pivoting breaks down. Use partial pivoting.")
            raise NumericalError("The matrix is singular (or nearly singular): there is no unique solution.")
        swap_text = "no swap"
        if p_row != k:
            M[k], M[p_row] = M[p_row], M[k]
            swaps += 1
            det_sign = -det_sign
            swap_text = f"swap row {k + 1} ↔ row {p_row + 1}"
        if p_col != k:
            for row in M:
                row[k], row[p_col] = row[p_col], row[k]
            order[k], order[p_col] = order[p_col], order[k]
            det_sign = -det_sign
            swap_text += f"; swap column {k + 1} ↔ column {p_col + 1}"
        pivots.append(M[k][k])
        mults = []
        for i in range(k + 1, n):
            m = M[i][k] / M[k][k]
            mults.append(f"m{i + 1}{k + 1} = {g(m, 6)}")
            max_mult = max(max_mult, abs(m))
            for j in range(k, n + 1):
                M[i][j] -= m * M[k][j]
        stages.append([k + 1, M[k][k], swap_text, ", ".join(mults) if mults else "-"])
        if k < 2:
            steps.append(f"Step {k + 1}: pivot = {g(M[k][k])} ({swap_text}); eliminate column {k + 1} below the pivot" + (f" using {', '.join(mults)}." if mults else "."))
    y = [0.0] * n
    back = []
    for i in range(n - 1, -1, -1):
        s = sum(M[i][j] * y[j] for j in range(i + 1, n))
        y[i] = (M[i][n] - s) / M[i][i]
        back.append([i + 1, f"({g(M[i][n])} - {g(s)}) / {g(M[i][i])}", y[i]])
    x = [0.0] * n
    for j in range(n):
        x[order[j]] = y[j]
    det = det_sign
    for v in pivots:
        det *= v
    return {"x": x, "U": [row[:n] for row in M], "stages": stages, "back": back[::-1], "steps": steps,
            "swaps": swaps, "max_mult": max_mult, "det": det}


def gaussian_elimination(A, b, pivoting="partial"):
    res = eliminate(A, b, pivoting)
    x = res["x"]
    steps = [f"Build the augmented matrix [A | b] and use {pivoting} pivoting."] + res["steps"] + [
        "Back substitution (from the last row upwards) gives x = [" + ", ".join(g(v, 8) for v in x) + "].",
        f"Determinant of A = product of pivots (with sign for swaps) = {g(res['det'])}."]
    return {
        "answers": [answer("Solution x", x)], "steps": steps, "iterations": len(A), "converged": None,
        "tables": [{"title": "Forward elimination", "columns": ["step k", "pivot", "row/column swap", "multipliers"], "rows": res["stages"]},
                   {"title": "Back substitution", "columns": ["i", "x_i = (c_i - Σ u_ij x_j) / u_ii", "x_i"], "rows": res["back"]}],
        "metrics": [{"label": "Residual ‖Ax − b‖∞", "value": residual(A, x, b)}, {"label": "Determinant det(A)", "value": res["det"]},
                    {"label": "Largest multiplier |m|", "value": res["max_mult"]}],
        "plot": {"kind": "matrices", "items": [("A", A), ("U (after elimination)", res["U"])]},
        "notes": ["Large multipliers magnify rounding errors - this is why pivoting matters."],
    }


def pivoting_comparison(A, b):
    check_system(A, b)
    rows, answers_x, steps = [], None, []
    exact = np.linalg.solve(np.array(A, float), np.array(b, float))
    for name in ("none", "partial", "complete"):
        try:
            res = eliminate(A, b, name)
            err = float(np.max(np.abs(np.array(res["x"]) - exact)))
            rows.append([name, res["swaps"], res["max_mult"], residual(A, res["x"], b), err, "[" + ", ".join(g(v, 6) for v in res["x"]) + "]"])
            if name == "partial":
                answers_x = res["x"]
            steps.append(f"{name.capitalize()} pivoting: largest multiplier {g(res['max_mult'], 4)}, error vs NumPy {g(err, 4)}.")
        except NumericalError as e:
            rows.append([name, "-", "-", "-", "-", f"FAILED: {e}"])
            steps.append(f"{name.capitalize()} pivoting FAILED: {e}")
    if answers_x is None:
        raise NumericalError("The matrix is singular, so no pivoting strategy can solve it.")
    steps.append("Partial pivoting picks the largest |entry| in the column, complete pivoting the largest in the whole remaining block.")
    return {
        "answers": [answer("Solution x (partial pivoting)", answers_x)], "steps": steps, "iterations": 3, "converged": None,
        "columns": ["strategy", "row swaps", "largest |m|", "residual", "max error vs NumPy", "solution"], "rows": rows,
        "notes": ["Compare the 'largest |m|' and 'error' columns: tiny pivots create huge multipliers and wrong answers."],
        "plot": {"kind": "bars", "labels": [r[0] for r in rows if r[4] != "-"], "values": [max(r[4], 1e-18) for r in rows if r[4] != "-"],
                 "logy": True, "ylabel": "max error vs NumPy", "title": "Accuracy of each pivoting strategy"},
    }


def lu_doolittle(A, b):
    n = len(A)
    check_system(A, b)
    L, U = mx.identity(n), mx.zeros(n, n)
    for i in range(n):
        for k in range(i, n):
            U[i][k] = A[i][k] - sum(L[i][j] * U[j][k] for j in range(i))
        if abs(U[i][i]) < 1e-14:
            raise NumericalError(f"Zero pivot U[{i + 1}][{i + 1}]: LU factorization without row exchanges fails for this matrix. Reorder the rows (pivoting) first.")
        for k in range(i + 1, n):
            L[k][i] = (A[k][i] - sum(L[k][j] * U[j][i] for j in range(i))) / U[i][i]
    y, fwd = [0.0] * n, []
    for i in range(n):
        s = sum(L[i][j] * y[j] for j in range(i))
        y[i] = b[i] - s
        fwd.append([i + 1, f"{g(b[i])} - {g(s)}", y[i]])
    x, back = [0.0] * n, []
    for i in range(n - 1, -1, -1):
        s = sum(U[i][j] * x[j] for j in range(i + 1, n))
        x[i] = (y[i] - s) / U[i][i]
        back.append([i + 1, f"({g(y[i])} - {g(s)}) / {g(U[i][i])}", x[i]])
    det = math.prod(U[i][i] for i in range(n))
    err = mx.frobenius(mx.mat_sub(mx.mat_mul(L, U), A))
    steps = ["Doolittle: A = L·U with L lower-triangular (1s on the diagonal) and U upper-triangular.",
             "Row i of U: u_ik = a_ik - Σ_(j<i) l_ij u_jk.   Column i of L: l_ki = (a_ki - Σ_(j<i) l_kj u_ji) / u_ii.",
             "Solve L y = b by forward substitution, then U x = y by back substitution.",
             "y = [" + ", ".join(g(v, 6) for v in y) + "],  x = [" + ", ".join(g(v, 6) for v in x) + "].",
             f"det(A) = product of the diagonal of U = {g(det)}."]
    return {
        "answers": [answer("Solution x", x)], "steps": steps, "iterations": n, "converged": None,
        "tables": [{"title": "Forward substitution  L y = b", "columns": ["i", "y_i = b_i - Σ l_ij y_j", "y_i"], "rows": fwd},
                   {"title": "Back substitution  U x = y", "columns": ["i", "x_i = (y_i - Σ u_ij x_j) / u_ii", "x_i"], "rows": back[::-1]}],
        "metrics": [{"label": "‖L·U − A‖ (Frobenius)", "value": err}, {"label": "Residual ‖Ax − b‖∞", "value": residual(A, x, b)},
                    {"label": "det(A)", "value": det}],
        "plot": {"kind": "matrices", "items": [("A", A), ("L", L), ("U", U)]},
        "notes": ["Once A = LU is known, many different right-hand sides b can be solved cheaply."],
    }


def cholesky(A, b):
    n = len(A)
    check_system(A, b)
    if not mx.is_symmetric(A):
        raise NumericalError("Cholesky factorization needs a SYMMETRIC matrix (A = Aᵀ). This matrix is not symmetric.")
    L = mx.zeros(n, n)
    for i in range(n):
        for j in range(i + 1):
            s = sum(L[i][k] * L[j][k] for k in range(j))
            if i == j:
                value = A[i][i] - s
                if value <= 1e-14:
                    raise NumericalError(f"The matrix is not positive definite (a diagonal term became {g(value)} ≤ 0), so Cholesky factorization is impossible.")
                L[i][i] = math.sqrt(value)
            else:
                L[i][j] = (A[i][j] - s) / L[j][j]
    y = [0.0] * n
    for i in range(n):
        y[i] = (b[i] - sum(L[i][j] * y[j] for j in range(i))) / L[i][i]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (y[i] - sum(L[j][i] * x[j] for j in range(i + 1, n))) / L[i][i]
    det = math.prod(L[i][i] for i in range(n)) ** 2
    Lt = mx.transpose(L)
    steps = ["Cholesky: A = L·Lᵀ with L lower-triangular and positive diagonal (needs A symmetric positive definite).",
             "Diagonal: l_ii = sqrt(a_ii - Σ_(k<i) l_ik²).   Below it: l_ij = (a_ij - Σ_(k<j) l_ik l_jk) / l_jj.",
             "Solve L y = b (forward substitution), then Lᵀ x = y (back substitution).",
             "x = [" + ", ".join(g(v, 6) for v in x) + "].", f"det(A) = (Π l_ii)² = {g(det)}."]
    return {
        "answers": [answer("Solution x", x)], "steps": steps, "iterations": n, "converged": None,
        "tables": [{"title": "Factor L", "columns": ["row"] + [f"col {j + 1}" for j in range(n)], "rows": [[i + 1] + L[i] for i in range(n)]},
                   {"title": "Solutions of L y = b and Lᵀ x = y", "columns": ["i", "y_i", "x_i"], "rows": [[i + 1, y[i], x[i]] for i in range(n)]}],
        "metrics": [{"label": "‖L·Lᵀ − A‖ (Frobenius)", "value": mx.frobenius(mx.mat_sub(mx.mat_mul(L, Lt), A))},
                    {"label": "Residual ‖Ax − b‖∞", "value": residual(A, x, b)}, {"label": "det(A)", "value": det}],
        "plot": {"kind": "matrices", "items": [("A", A), ("L", L), ("Lᵀ", Lt)]},
        "notes": ["Cholesky needs about half the work of LU and is very stable for symmetric positive definite matrices."],
    }


def invert(A):
    """Gauss-Jordan elimination on [A | I]; returns the inverse."""
    n = len(A)
    M = [A[i][:] + mx.identity(n)[i] for i in range(n)]
    scale = max(1e-300, max(abs(v) for row in A for v in row))
    for k in range(n):
        p = max(range(k, n), key=lambda i: abs(M[i][k]))
        if abs(M[p][k]) < 1e-13 * scale:
            raise NumericalError("The matrix is singular (determinant ≈ 0), so it has no inverse.")
        M[k], M[p] = M[p], M[k]
        pivot = M[k][k]
        M[k] = [v / pivot for v in M[k]]
        for i in range(n):
            if i != k:
                m = M[i][k]
                M[i] = [M[i][j] - m * M[k][j] for j in range(2 * n)]
    return [row[n:] for row in M]


def matrix_inverse(A):
    n = len(A)
    check_system(A)
    inv = invert(A)
    check = mx.mat_mul(A, inv)
    err = max(abs(check[i][j] - (1.0 if i == j else 0.0)) for i in range(n) for j in range(n))
    det = float(np.linalg.det(np.array(A, float)))
    steps = ["Gauss-Jordan: write [A | I] and apply row operations until the left block becomes I; the right block is then A⁻¹.",
             "For each column: choose the pivot (largest entry), divide its row by the pivot, and clear the column in ALL other rows.",
             "A⁻¹ = " + str([[round(v, 6) for v in row] for row in inv]),
             f"Check: A·A⁻¹ should equal I. Largest deviation = {g(err)}."]
    return {
        "answers": [answer("Inverse A⁻¹", inv)], "steps": steps, "iterations": n, "converged": None,
        "columns": ["row"] + [f"col {j + 1}" for j in range(n)], "rows": [[i + 1] + inv[i] for i in range(n)], "table_title": "A⁻¹",
        "metrics": [{"label": "max |A·A⁻¹ − I|", "value": err}, {"label": "det(A) (NumPy)", "value": det}],
        "plot": {"kind": "matrices", "items": [("A", A), ("A⁻¹", inv), ("A·A⁻¹", check)]},
        "notes": ["In practice we rarely compute A⁻¹: solving A x = b directly is faster and more accurate."],
    }


def iterative(A, b, x0, method="jacobi", tol=1e-8, max_iter=200):
    n = len(A)
    check_system(A, b)
    if len(x0) != n:
        raise NumericalError(f"The starting vector must have {n} entries.")
    for i in range(n):
        if A[i][i] == 0:
            raise NumericalError(f"Diagonal entry a[{i + 1}][{i + 1}] is zero. Reorder the equations so the diagonal has no zeros.")
    dominant = all(abs(A[i][i]) > sum(abs(A[i][j]) for j in range(n) if j != i) for i in range(n))
    x = x0[:]
    rows, history, steps = [], [], []
    converged = False
    for k in range(1, max_iter + 1):
        old = x[:]
        new = x[:]
        for i in range(n):
            source = old if method == "jacobi" else new      # Gauss-Seidel uses the newest values immediately
            s = sum(A[i][j] * source[j] for j in range(n) if j != i)
            new[i] = (b[i] - s) / A[i][i]
        change = mx.norm_inf(mx.vec_sub(new, old))
        rows.append([k] + new + [change])
        history.append(change)
        x = new
        if k <= 2:
            steps.append(f"Iteration {k}: x = [" + ", ".join(g(v, 6) for v in x) + f"], change = {g(change)}.")
        if change < tol:
            converged = True
            break
        if change > 1e100 or math.isinf(change):
            raise NumericalError("The iteration is diverging. The matrix is probably not diagonally dominant - try reordering the equations or use a direct method.")
    D = np.diag(np.diag(np.array(A, float)))
    Lo, Up = np.tril(np.array(A, float), -1), np.triu(np.array(A, float), 1)
    T = -np.linalg.solve(D, Lo + Up) if method == "jacobi" else -np.linalg.solve(D + Lo, Up)
    rho = float(max(abs(np.linalg.eigvals(T))))
    steps.insert(0, "Jacobi: x_i(new) = (b_i - Σ_(j≠i) a_ij x_j(old)) / a_ii.  " if method == "jacobi" else
                 "Gauss-Seidel: same formula, but uses the NEWEST values x_j(new) as soon as they are available.")
    notes = [("The matrix is strictly diagonally dominant, which guarantees convergence." if dominant
              else "The matrix is NOT strictly diagonally dominant - convergence is not guaranteed."),
             f"Spectral radius of the iteration matrix (NumPy check) ρ = {g(rho, 5)}: " + ("< 1, so the method converges." if rho < 1 else "≥ 1, so the method will not converge.")]
    return {
        "answers": [answer("Solution x", x)], "steps": steps, "iterations": len(rows), "converged": converged,
        "columns": ["k"] + [f"x{i + 1}" for i in range(n)] + ["‖Δx‖∞"], "rows": rows, "notes": notes,
        "metrics": [{"label": "Spectral radius ρ(T)", "value": rho}, {"label": "Residual ‖Ax − b‖∞", "value": residual(A, x, b)}],
        "plot": {"kind": "series", "lines": [{"label": "‖xₖ − xₖ₋₁‖∞", "x": list(range(1, len(history) + 1)), "y": history}],
                 "logy": True, "title": f"{'Jacobi' if method == 'jacobi' else 'Gauss-Seidel'} convergence"},
        "history": history,
    }


def matrix_norm(A, kind):
    if kind == "1":
        return max(sum(abs(A[i][j]) for i in range(len(A))) for j in range(len(A[0])))
    if kind == "inf":
        return max(sum(abs(v) for v in row) for row in A)
    return mx.frobenius(A)


def condition_number(A, kind="inf"):
    check_system(A)
    inv = invert(A)
    na, ni = matrix_norm(A, kind), matrix_norm(inv, kind)
    kappa = na * ni
    sym = {"1": "‖·‖₁", "inf": "‖·‖∞", "fro": "‖·‖_F"}[kind]
    lost = math.log10(kappa) if kappa > 0 else 0
    steps = [f"κ(A) = ‖A‖ · ‖A⁻¹‖ using the {sym} norm.", f"‖A‖ = {g(na)}.", "A⁻¹ computed by Gauss-Jordan elimination.",
             f"‖A⁻¹‖ = {g(ni)}.", f"κ(A) = {g(na)} · {g(ni)} = {g(kappa)}.",
             f"Rule of thumb: you can lose about log10(κ) = {g(lost, 4)} decimal digits of accuracy when solving Ax = b."]
    return {
        "answers": [answer("Condition number κ(A)", kappa)], "steps": steps, "iterations": None, "converged": None,
        "columns": ["quantity", "value"], "rows": [["‖A‖", na], ["‖A⁻¹‖", ni], ["κ(A) = ‖A‖·‖A⁻¹‖", kappa], ["digits that may be lost ≈ log10 κ", lost]],
        "table_title": "Condition number", "metrics": [{"label": "log10 κ(A)", "value": lost}],
        "notes": ["κ close to 1 = well-conditioned. κ very large = ill-conditioned (tiny input changes cause huge output changes)."],
        "plot": {"kind": "matrices", "items": [("A", A), ("A⁻¹", inv)]},
    }


def conditioning_experiment(A, b, eps):
    check_system(A, b)
    x = solve_linear(A, b)
    scale = mx.norm_inf(b) or 1.0
    db = [eps * scale * (1 if i % 2 == 0 else -1) for i in range(len(b))]
    x2 = solve_linear(A, [bi + di for bi, di in zip(b, db)])
    dx = mx.vec_sub(x2, x)
    rel_b = mx.norm_inf(db) / mx.norm_inf(b) if mx.norm_inf(b) else 0.0
    rel_x = mx.norm_inf(dx) / mx.norm_inf(x) if mx.norm_inf(x) else 0.0
    amp = rel_x / rel_b if rel_b else 0.0
    kappa = matrix_norm(A, "inf") * matrix_norm(invert(A), "inf")
    steps = ["Solve A x = b, then change b a tiny bit to b + δb and solve again.",
             f"δb = ±{g(eps * scale)} (alternating signs): relative change in b = {g(rel_b)}.",
             f"Relative change in the solution x = {g(rel_x)}.",
             f"Amplification = (relative change in x) / (relative change in b) = {g(amp, 5)}.",
             f"Theory: amplification ≤ κ∞(A) = {g(kappa, 5)}."]
    rows = [[i + 1, x[i], x2[i], dx[i]] for i in range(len(x))]
    return {
        "answers": [answer("Error amplification factor", amp)], "steps": steps, "iterations": None, "converged": None,
        "columns": ["i", "x_i (original)", "x_i (perturbed b)", "change"], "rows": rows,
        "metrics": [{"label": "κ∞(A) (upper bound for amplification)", "value": kappa}, {"label": "Relative change in b", "value": rel_b},
                    {"label": "Relative change in x", "value": rel_x}],
        "notes": ["A large amplification means the system is ILL-CONDITIONED: rounding errors in the data are magnified in the answer."],
        "plot": {"kind": "bars", "labels": ["relative change in b", "relative change in x"], "values": [max(rel_b, 1e-18), max(rel_x, 1e-18)],
                 "logy": True, "title": f"Input vs output change (amplification ≈ {g(amp, 4)})"},
        "status_message": "Experiment finished.",
    }


# ===================================================== PART 2: WEBSITE ADAPTERS
def _system(p):
    A = get_matrix(p, "A", "A", square=True)
    b = get_vector(p, "b", "b", len(A))
    return A, b


def _ref_solve(A, b):
    try:
        return {"label": "NumPy linalg.solve", "value": [float(v) for v in np.linalg.solve(np.array(A, float), np.array(b, float))], "exact": False}
    except np.linalg.LinAlgError:
        raise NumericalError("The matrix is singular, so the system has no unique solution.")


def _cond_note(raw, A):
    c = float(np.linalg.cond(np.array(A, float), np.inf))
    raw["metrics"] = raw.get("metrics", []) + [{"label": "κ∞(A) (NumPy)", "value": c}]
    if c > 1e8:
        raw["notes"] = raw.get("notes", []) + ["Warning: A is badly conditioned, so the digits of x may be unreliable."]
    return raw


def run_gauss(p):
    A, b = _system(p)
    piv = get_select(p, "pivoting", ["none", "partial", "complete"], "partial")
    return finish(_cond_note(gaussian_elimination(A, b, piv), A), _ref_solve(A, b))


def run_pivoting(p):
    A, b = _system(p)
    return finish(pivoting_comparison(A, b), _ref_solve(A, b))


def run_lu(p):
    A, b = _system(p)
    return finish(_cond_note(lu_doolittle(A, b), A), _ref_solve(A, b))


def run_cholesky(p):
    A, b = _system(p)
    raw = cholesky(A, b)
    ref_L = np.linalg.cholesky(np.array(A, float))
    raw["metrics"].append({"label": "max |L − NumPy cholesky|", "value": float(np.max(np.abs(ref_L - np.array(raw["plot"]["items"][1][1]))))})
    return finish(_cond_note(raw, A), _ref_solve(A, b))


def run_inverse(p):
    A = get_matrix(p, "A", "A", square=True)
    raw = matrix_inverse(A)
    ref = np.linalg.inv(np.array(A, float))
    return finish(raw, {"label": "NumPy linalg.inv", "value": ref.tolist(), "exact": False})


def run_iterative(p):
    A, b = _system(p)
    x0 = get_vector(p, "x0", "x0", len(A))
    method = get_select(p, "method", ["jacobi", "gauss_seidel"], "jacobi")
    raw = iterative(A, b, x0, method, get_float(p, "tol", "Tolerance", 1e-15), get_int(p, "max_iter", "Max iterations", 1, 5000))
    return finish(raw, _ref_solve(A, b))


def run_cond_number(p):
    A = get_matrix(p, "A", "A", square=True)
    kind = get_select(p, "norm", ["1", "inf", "fro"], "inf")
    raw = condition_number(A, kind)
    ref = float(np.linalg.cond(np.array(A, float), {"1": 1, "inf": np.inf, "fro": "fro"}[kind]))
    return finish(raw, {"label": "NumPy linalg.cond", "value": ref, "exact": False})


def run_conditioning(p):
    A, b = _system(p)
    return finish(conditioning_experiment(A, b, get_float(p, "eps", "Relative perturbation", 1e-15)))


MAT = field("A", "Matrix A", "matrix", "4, 12, -16\n12, 37, -43\n-16, -43, 98", "One row per line, numbers separated by commas.")
VEC = field("b", "Vector b", "list", "-20, -43, 192", "Same number of entries as rows of A.")
NORM = field("norm", "Matrix norm", "select", "inf", "", options=[{"value": "inf", "label": "∞-norm (max row sum)"}, {"value": "1", "label": "1-norm (max column sum)"}, {"value": "fro", "label": "Frobenius norm"}])
ILL = "1, 1\n1, 1.0001"

SPECS = {
    "gauss_elim": {"name": "Gaussian Elimination", "category": "linalg", "run": run_gauss,
                   "formula": r"m_{ik}=\dfrac{a_{ik}}{a_{kk}},\quad R_i\leftarrow R_i-m_{ik}R_k,\quad x_i=\dfrac{c_i-\sum_{j>i}u_{ij}x_j}{u_{ii}}",
                   "inputs": [field("A", "Matrix A", "matrix", "2, 1, -1\n-3, -1, 2\n-2, 1, 2", "One row per line, numbers separated by commas."), field("b", "Vector b", "list", "8, -11, -3", "Same number of entries as rows of A."), field("pivoting", "Pivoting", "select", "partial", "", options=[
                       {"value": "none", "label": "None"}, {"value": "partial", "label": "Partial"}, {"value": "complete", "label": "Complete"}])]},
    "pivoting": {"name": "Pivoting Strategies", "category": "linalg", "run": run_pivoting,
                 "formula": r"\text{partial: } |a_{pk}|=\max_{i\ge k}|a_{ik}|\qquad \text{complete: } |a_{pq}|=\max_{i,j\ge k}|a_{ij}|",
                 "inputs": [field("A", "Matrix A", "matrix", "1e-20, 1\n1, 1", "Default shows why pivoting is needed."), field("b", "Vector b", "list", "1, 2")]},
    "lu": {"name": "LU Factorization", "category": "linalg", "run": run_lu,
           "formula": r"A=LU,\quad Ly=b,\quad Ux=y",
           "inputs": [MAT, VEC]},
    "cholesky": {"name": "Cholesky Factorization", "category": "linalg", "run": run_cholesky,
                 "formula": r"A=LL^T,\quad l_{ii}=\sqrt{a_{ii}-\sum_{k<i}l_{ik}^2}",
                 "inputs": [MAT, VEC]},
    "inverse": {"name": "Matrix Inversion", "category": "linalg", "run": run_inverse,
                "formula": r"[A\,|\,I]\ \xrightarrow{\text{row operations}}\ [I\,|\,A^{-1}]",
                "inputs": [field("A", "Matrix A", "matrix", "2, -1, 0\n-1, 2, -1\n0, -1, 2")]},
    "iterative": {"name": "Iterative Methods", "category": "linalg", "run": run_iterative,
                  "formula": r"x_i^{(k+1)}=\dfrac{1}{a_{ii}}\Big(b_i-\sum_{j\neq i}a_{ij}x_j\Big)",
                  "inputs": [field("A", "Matrix A", "matrix", "10, -1, 2\n-1, 11, -1\n2, -1, 10"), field("b", "Vector b", "list", "14, 18, 30"),
                             field("x0", "Starting vector x0", "list", "0, 0, 0"),
                             field("method", "Method", "select", "gauss_seidel", "", options=[{"value": "jacobi", "label": "Jacobi"}, {"value": "gauss_seidel", "label": "Gauss-Seidel"}]),
                             field("tol", "Tolerance", "number", "1e-8"), field("max_iter", "Maximum iterations", "int", "200")]},
    "conditioning": {"name": "Matrix Conditioning", "category": "linalg", "run": run_conditioning,
                     "formula": r"\dfrac{\|\delta x\|}{\|x\|}\le \kappa(A)\,\dfrac{\|\delta b\|}{\|b\|}",
                     "inputs": [field("A", "Matrix A", "matrix", ILL), field("b", "Vector b", "list", "2, 2.0001"),
                                field("eps", "Relative perturbation of b", "number", "1e-4", "How much to disturb b.")]},
    "cond_number": {"name": "Condition Number", "category": "linalg", "run": run_cond_number,
                    "formula": r"\kappa(A)=\|A\|\,\|A^{-1}\|",
                    "inputs": [field("A", "Matrix A", "matrix", ILL), NORM]},
}
