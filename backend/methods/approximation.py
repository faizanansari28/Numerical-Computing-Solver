"""Best approximation: least squares, Gram-Schmidt, QR factorization (Householder), SVD."""
import math

import numpy as np

from methods.eigenvalues import jacobi_eigen
from methods.linear_algebra import solve_linear
from utils import matrix as mx
from utils.errors import NumericalError
from utils.inputs import field, g, get_matrix, get_select, get_vector
from utils.results import answer, finish


def check_tall(A):
    m, n = len(A), len(A[0])
    if m < n:
        raise NumericalError(f"This method needs at least as many rows as columns (A is {m} x {n}).")


# ===================================================== PART 1: ALGORITHMS
def linear_least_squares(A, b):
    check_tall(A)
    m, n = len(A), len(A[0])
    if len(b) != m:
        raise NumericalError(f"b must have {m} entries (one per row of A).")
    At = mx.transpose(A)
    AtA = mx.mat_mul(At, A)
    Atb = mx.mat_vec(At, b)
    try:
        x = solve_linear(AtA, Atb)
    except NumericalError:
        raise NumericalError("The columns of A are linearly dependent, so AᵀA is singular and the least-squares solution is not unique.")
    fit = mx.mat_vec(A, x)
    r = mx.vec_sub(b, fit)
    orth = mx.norm_inf(mx.mat_vec(At, r))
    steps = ["Minimise ‖b − A x‖₂. The minimiser satisfies the NORMAL EQUATIONS  AᵀA x = Aᵀb.",
             "AᵀA = " + str([[round(v, 5) for v in row] for row in AtA]) + ",  Aᵀb = " + str([round(v, 5) for v in Atb]),
             "Solving the n×n system gives x = [" + ", ".join(g(v, 7) for v in x) + "].",
             f"Residual r = b − Ax has length ‖r‖₂ = {g(mx.norm2(r))}.",
             f"Geometric check: the residual must be orthogonal to every column of A: max |Aᵀr| = {g(orth)}."]
    return {
        "answers": [answer("Least-squares solution x", x)], "steps": steps, "iterations": None, "converged": None,
        "columns": ["i", "b_i", "(Ax)_i", "residual r_i"], "rows": [[i + 1, b[i], fit[i], r[i]] for i in range(m)], "table_title": "Fit and residuals",
        "metrics": [{"label": "‖b − Ax‖₂", "value": mx.norm2(r)}, {"label": "max |Aᵀr| (should be 0)", "value": orth}],
        "plot": {"kind": "curves", "curves": [{"label": "A x (fitted values)", "x": list(range(1, m + 1)), "y": fit}],
                 "points": {"x": list(range(1, m + 1)), "y": b, "label": "b (data)"}, "xlabel": "row i", "ylabel": "value"},
        "notes": ["Forming AᵀA squares the condition number; QR factorization is the more accurate way to solve least-squares problems."],
    }


def gram_schmidt(A, modified=True):
    check_tall(A)
    m, n = len(A), len(A[0])
    cols = [[A[i][j] for i in range(m)] for j in range(n)]
    Q, R, rows, steps = [], mx.zeros(n, n), [], []
    for j in range(n):
        v = cols[j][:]
        for i in range(j):
            R[i][j] = mx.dot(Q[i], v if modified else cols[j])       # modified: use the updated v
            v = [a - R[i][j] * q for a, q in zip(v, Q[i])]
        R[j][j] = mx.norm2(v)
        if R[j][j] < 1e-12:
            raise NumericalError(f"Column {j + 1} is (almost) a combination of the previous columns, so the columns are linearly dependent.")
        Q.append([a / R[j][j] for a in v])
        proj = ", ".join(f"r{i + 1}{j + 1} = {g(R[i][j], 5)}" for i in range(j)) or "none"
        rows.append([j + 1, proj, R[j][j], "[" + ", ".join(g(a, 5) for a in Q[j]) + "]"])
        if j < 3:
            steps.append(f"Column {j + 1}: subtract the projections onto earlier q's ({proj}); length of what is left = {g(R[j][j], 6)}; divide to get q_{j + 1}.")
    Qm = mx.transpose(Q)                                                 # m x n
    QtQ = mx.mat_mul(mx.transpose(Qm), Qm)
    orth = max(abs(QtQ[i][j] - (1.0 if i == j else 0.0)) for i in range(n) for j in range(n))
    recon = mx.frobenius(mx.mat_sub(mx.mat_mul(Qm, R), A))
    steps.insert(0, ("Modified" if modified else "Classical") + " Gram-Schmidt: q_j = (a_j − Σ_(i<j) (q_iᵀ·a_j) q_i) / its length. The lengths and projections form R, so A = Q R.")
    return {
        "answers": [answer("Orthonormal matrix Q", Qm), answer("Upper-triangular R", R)], "steps": steps, "iterations": n, "converged": None,
        "columns": ["j", "projections r_ij", "r_jj = ‖v_j‖", "q_j"], "rows": rows, "table_title": "Gram-Schmidt steps",
        "metrics": [{"label": "max |QᵀQ − I| (orthogonality)", "value": orth}, {"label": "‖A − QR‖ (Frobenius)", "value": recon}],
        "plot": {"kind": "matrices", "items": [("A", A), ("Q", Qm), ("R", R)]},
        "notes": ["Classical Gram-Schmidt loses orthogonality for nearly dependent columns; the modified version is more stable."],
    }


def householder_qr(A):
    m, n = len(A), len(A[0])
    R = mx.copy(A)
    Q = mx.identity(m)
    steps = []
    for k in range(min(n, m - 1)):
        x = [R[i][k] for i in range(k, m)]
        norm_x = mx.norm2(x)
        if norm_x < 1e-14:
            continue
        alpha = -norm_x if x[0] >= 0 else norm_x
        v = x[:]
        v[0] -= alpha
        nv = mx.norm2(v)
        if nv < 1e-14:
            continue
        v = [a / nv for a in v]
        for j in range(n):                                  # R = H R
            s = sum(v[i] * R[k + i][j] for i in range(m - k))
            for i in range(m - k):
                R[k + i][j] -= 2 * v[i] * s
        for r in range(m):                                  # Q = Q H
            s = sum(Q[r][k + i] * v[i] for i in range(m - k))
            for i in range(m - k):
                Q[r][k + i] -= 2 * s * v[i]
        steps.append(f"Reflection {k + 1}: reflect column {k + 1} onto the first axis so that everything below the diagonal becomes 0.")
    for i in range(m):
        for j in range(min(i, n)):
            R[i][j] = 0.0 if abs(R[i][j]) < 1e-13 else R[i][j]
    for j in range(min(m, n)):                      # normalise signs so that diag(R) > 0
        if R[j][j] < 0:
            R[j] = [-v for v in R[j]]
            for r in range(m):
                Q[r][j] = -Q[r][j]
    steps.append("Signs are normalised so that the diagonal of R is positive (this makes the factorization unique).")
    return Q, R, steps


def qr_factorization(A, b=None):
    check_tall(A)
    m, n = len(A), len(A[0])
    Q, R, steps = householder_qr(A)
    err = mx.frobenius(mx.mat_sub(mx.mat_mul(Q, R), A))
    QtQ = mx.mat_mul(mx.transpose(Q), Q)
    orth = max(abs(QtQ[i][j] - (1.0 if i == j else 0.0)) for i in range(m) for j in range(m))
    steps.insert(0, "Householder QR: apply reflections H_k = I − 2vvᵀ that zero the entries below the diagonal, column by column. Then R = H_n…H_1 A and Q = H_1…H_n.")
    out = {
        "answers": [answer("Upper-triangular R", R), answer("Orthogonal matrix Q", Q)], "steps": steps, "iterations": n, "converged": None,
        "columns": ["row"] + [f"R col {j + 1}" for j in range(n)], "rows": [[i + 1] + R[i] for i in range(m)], "table_title": "Upper-triangular factor R",
        "metrics": [{"label": "‖A − QR‖ (Frobenius)", "value": err}, {"label": "max |QᵀQ − I|", "value": orth}],
        "plot": {"kind": "matrices", "items": [("A", A), ("Q", Q), ("R", R)]}, "extra": {},
    }
    if b is not None:
        Qtb = mx.mat_vec(mx.transpose(Q), b)
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            if abs(R[i][i]) < 1e-12:
                raise NumericalError("R has a zero on its diagonal: the columns of A are linearly dependent.")
            x[i] = (Qtb[i] - sum(R[i][j] * x[j] for j in range(i + 1, n))) / R[i][i]
        res = mx.norm2(mx.vec_sub(mx.mat_vec(A, x), b))
        out["steps"].append("Least squares with QR: solve R x = (Qᵀb) using the first n rows (back substitution): x = [" + ", ".join(g(v, 7) for v in x) + "].")
        out["answers"].append(answer("Least-squares solution x (from QR)", x))
        out["metrics"].append({"label": "‖Ax − b‖₂", "value": res})
        out["extra"]["x"] = x
    return out


def svd_manual(A, k=None):
    m, n = len(A), len(A[0])
    AtA = mx.mat_mul(mx.transpose(A), A)
    vals, V = jacobi_eigen(AtA)
    order = sorted(range(n), key=lambda i: -vals[i])
    k_keep = min(m, n)
    sigma = [math.sqrt(max(vals[i], 0.0)) for i in order][:k_keep]
    Vs = [[V[r][i] for i in order[:k_keep]] for r in range(n)]
    tol = max(sigma[0], 1e-300) * 1e-12 * max(m, n)
    rank = sum(1 for s in sigma if s > tol)
    U = mx.zeros(m, rank)
    for j in range(rank):
        col = mx.mat_vec(A, [Vs[r][j] for r in range(n)])
        for i in range(m):
            U[i][j] = col[i] / sigma[j]
    Sigma = mx.zeros(rank, rank)
    for i in range(rank):
        Sigma[i][i] = sigma[i]
    Vr = [[Vs[r][j] for j in range(rank)] for r in range(n)]
    recon = mx.frobenius(mx.mat_sub(mx.mat_mul(mx.mat_mul(U, Sigma), mx.transpose(Vr)), A))
    total = sum(s * s for s in sigma)
    rows, cum = [], 0.0
    for i, s in enumerate(sigma):
        cum += s * s
        tail = math.sqrt(max(total - cum, 0.0))
        rows.append([i + 1, s, s * s / total * 100 if total else 0, cum / total * 100 if total else 0, tail])
    kappa = sigma[0] / sigma[rank - 1] if rank and sigma[rank - 1] > 0 else float("inf")
    steps = ["SVD: A = U Σ Vᵀ. The singular values σ_i are the square roots of the eigenvalues of AᵀA; the columns of V are its eigenvectors.",
             "Eigen-decomposition of AᵀA found with Jacobi rotations; sorted so that σ1 ≥ σ2 ≥ … .",
             "Each column of U is u_i = A v_i / σ_i.",
             "σ = [" + ", ".join(g(s, 6) for s in sigma) + f"],  rank = {rank}.",
             f"Check: ‖A − UΣVᵀ‖ = {g(recon)}.",
             "Eckart-Young: the best rank-k approximation has error sqrt(σ_(k+1)² + …) (last column of the table)."]
    return {
        "answers": [answer("Singular values σ", sigma)], "steps": steps, "iterations": None, "converged": None,
        "columns": ["i", "σ_i", "energy σ_i² (%)", "cumulative energy (%)", "error of best rank-i approx. ‖A − A_i‖_F"], "rows": rows,
        "table_title": "Singular values",
        "metrics": [{"label": "Rank", "value": rank}, {"label": "κ₂(A) = σ_max / σ_min", "value": kappa}, {"label": "‖A − UΣVᵀ‖", "value": recon}],
        "plot": {"kind": "bars", "labels": [f"σ{i + 1}" for i in range(k_keep)], "values": [max(s, 1e-18) for s in sigma], "ylabel": "singular value", "title": "Singular values of A"},
        "notes": ["Computing σ from AᵀA squares the condition number, so very small singular values lose accuracy (production codes avoid this)."],
    }


# ===================================================== PART 2: WEBSITE ADAPTERS
def run_lls(p):
    A = get_matrix(p, "A", "A")
    b = get_vector(p, "b", "b", len(A))
    raw = linear_least_squares(A, b)
    ref = np.linalg.lstsq(np.array(A, float), np.array(b, float), rcond=None)[0]
    return finish(raw, {"label": "NumPy lstsq", "value": ref.tolist(), "exact": False})


def _sign_fix(Q, R):
    Q, R = np.array(Q, float), np.array(R, float)
    s = np.sign(np.diag(R)[: R.shape[1]]) if R.shape[0] >= R.shape[1] else np.sign(np.diag(R))
    s[s == 0] = 1
    k = len(s)
    Q[:, :k] = Q[:, :k] * s
    R[:k, :] = (R[:k, :].T * s).T
    return Q, R


def run_gs(p):
    A = get_matrix(p, "A", "A")
    raw = gram_schmidt(A, get_select(p, "variant", ["modified", "classical"], "modified") == "modified")
    Qr, Rr = np.linalg.qr(np.array(A, float))
    Qr, Rr = _sign_fix(Qr, Rr)
    return finish(raw, {"label": "NumPy linalg.qr (reduced)", "value": Qr.tolist(), "exact": False})


def run_qr(p):
    A = get_matrix(p, "A", "A")
    b = get_vector(p, "b", "b", len(A)) if str(p.get("b", "")).strip() else None
    raw = qr_factorization(A, b)
    if b is not None:
        ref = np.linalg.lstsq(np.array(A, float), np.array(b, float), rcond=None)[0]
        raw["answers"] = [raw["answers"][2]] + raw["answers"][:2]
        return finish(raw, {"label": "NumPy lstsq", "value": ref.tolist(), "exact": False})
    Qr, Rr = np.linalg.qr(np.array(A, float), mode="complete")
    Qr, Rr = _sign_fix(Qr, Rr)
    return finish(raw, {"label": "NumPy linalg.qr, factor R", "value": Rr.tolist(), "exact": False})


def run_svd(p):
    A = get_matrix(p, "A", "A")
    raw = svd_manual(A)
    ref = np.linalg.svd(np.array(A, float), compute_uv=False)
    got = raw["answers"][0]["value"]
    ref = list(ref)[: len(got)]
    return finish(raw, {"label": "NumPy linalg.svd", "value": ref, "exact": False})


SPECS = {
    "lls": {"name": "Linear Least Squares", "category": "approx", "run": run_lls,
            "formula": r"\min_x \|b-Ax\|_2 \;\Longleftrightarrow\; A^TA\,x=A^Tb",
            "inputs": [field("A", "Matrix A (more rows than columns)", "matrix", "1, 1\n1, 2\n1, 3\n1, 4"), field("b", "Vector b", "list", "6, 5, 7, 10")]},
    "gram_schmidt": {"name": "Gram-Schmidt Orthonormalization", "category": "approx", "run": run_gs,
                     "formula": r"q_j=\dfrac{a_j-\sum_{i<j}(q_i^Ta_j)\,q_i}{\left\|a_j-\sum_{i<j}(q_i^Ta_j)\,q_i\right\|}",
                     "inputs": [field("A", "Matrix A (columns are the vectors)", "matrix", "1, 1, 0\n1, 0, 1\n0, 1, 1"),
                                field("variant", "Variant", "select", "modified", "", options=[{"value": "modified", "label": "Modified (stable)"}, {"value": "classical", "label": "Classical"}])]},
    "qr": {"name": "QR Factorization", "category": "approx", "run": run_qr,
           "formula": r"A=QR,\quad Q^TQ=I,\quad Rx=Q^Tb",
           "inputs": [field("A", "Matrix A", "matrix", "1, 1\n1, 2\n1, 3\n1, 4"), field("b", "Vector b (optional - solves least squares)", "list", "6, 5, 7, 10", optional=True)]},
    "svd": {"name": "Singular Value Decomposition", "category": "approx", "run": run_svd,
            "formula": r"A=U\Sigma V^T,\quad \sigma_i=\sqrt{\lambda_i(A^TA)}",
            "inputs": [field("A", "Matrix A", "matrix", "3, 2, 2\n2, 3, -2")]},
}
