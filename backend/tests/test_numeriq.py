"""Run with:  python tests/test_numeriq.py     (from the backend folder)

1. Every method runs with its default inputs and agrees with SciPy/NumPy.
2. Every Python snippet on the 'Explore' page is executed and its printed numbers are compared with the backend.
3. Extra random tests and edge cases.
"""
import math
import os
import random
import re
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import app as flask_app  # noqa: E402
import challenges  # noqa: E402
import content  # noqa: E402
import registry  # noqa: E402

client = flask_app.app.test_client()
failures = []


def check(name, ok, detail=""):
    if not ok:
        failures.append(f"{name} {detail}")
        print("FAIL", name, detail)


def flatten(v):
    if isinstance(v, (list, tuple)):
        out = []
        for a in v:
            out += flatten(a)
        return out
    return [float(v)]


def solve(method, params):
    r = client.post("/api/solve", json={"method": method, "params": params})
    return r.status_code, r.json


# ---------------------------------------------------------------- 1 + 2
print("== defaults + learning snippets ==")
NUM = re.compile(r"-?\d+\.?\d*(?:[eE][-+]?\d+)?")
for mid in registry.METHODS:
    r = client.get(f"/api/learn/{mid}")
    check(f"learn {mid}", r.status_code == 200, str(r.json))
    if r.status_code != 200:
        continue
    d = r.json
    res = d["result"]
    ea = res["error_analysis"]
    # backend agrees with its independent reference
    if ea["absolute_error"] is not None and mid not in ("poly_approx", "midpoint", "trapezoid", "numdiff", "euler", "rk2", "rk4", "rounding", "error_analysis"):
        scale = max(1.0, max(abs(x) for x in flatten(ea["reference_value"])))
        check(f"reference {mid}", ea["absolute_error"] < 1e-6 * scale, f"abs err {ea['absolute_error']}")
    if d["content"].get("exact"):
        ex = res["exact_answer"]
        tol = 1e-8 if mid not in ("pivoting",) else 1e-6
        if mid not in ("midpoint", "trapezoid", "euler", "rk2", "rk4", "numdiff", "poly_approx", "lagrange", "hermite", "spline", "curve_fitting", "rounding", "error_analysis"):
            check(f"exact {mid}", ex["absolute_error"] < tol * max(1, abs(flatten(ex["value"])[0])), f"{ex['absolute_error']}")
    # run the snippet
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "snippet.py")
        open(path, "w").write(d["content"]["code"])
        run = subprocess.run([sys.executable, "-I", path], capture_output=True, text=True, timeout=30, cwd=tmp)
    check(f"snippet runs {mid}", run.returncode == 0, run.stderr[-300:])
    if run.returncode != 0:
        continue
    printed = [float(x) for x in NUM.findall(run.stdout)]
    wanted = flatten(res["answers"][0]["value"])
    for w in wanted:
        hit = any(abs(p - w) <= 1e-5 * max(1.0, abs(w)) for p in printed)
        # snippet results are allowed to differ slightly for iterative methods (same algorithm, same stop rule) -> keep tolerance
        check(f"snippet matches backend {mid}", hit, f"backend {w} not in printed {printed[:12]}")
    for rel in d["content"]["related"]:
        check(f"related id {mid}->{rel}", rel in registry.METHODS)
print(f"{len(registry.METHODS)} methods checked")

# ---------------------------------------------------------------- 3 random tests
print("== random tests ==")
random.seed(7)
for t in range(30):
    n = random.randint(2, 6)
    M = np.random.RandomState(t).randn(n, n)
    A = M @ M.T + n * np.eye(n)                      # symmetric positive definite
    xt = np.random.RandomState(t + 100).randn(n)
    b = A @ xt
    P = {"A": "\n".join(",".join(repr(float(v)) for v in row) for row in A), "b": ",".join(repr(float(v)) for v in b)}
    for m in ("gauss_elim", "lu", "cholesky"):
        code, r = solve(m, dict(P))
        check(f"random {m} n={n}", code == 200 and np.allclose(r["answers"][0]["value"], xt, atol=1e-8), str(r)[:120])
    code, r = solve("iterative", {**P, "x0": ",".join(["0"] * n), "method": "gauss_seidel", "tol": "1e-12", "max_iter": "2000"})
    check(f"random gauss-seidel n={n}", code == 200 and np.allclose(r["answers"][0]["value"], xt, atol=1e-6), str(r)[:120])
    code, r = solve("inverse", {"A": P["A"]})
    check(f"random inverse n={n}", code == 200 and np.allclose(r["answers"][0]["value"], np.linalg.inv(A), atol=1e-8))
    code, r = solve("cond_number", {"A": P["A"], "norm": "1"})
    check(f"random cond n={n}", code == 200 and abs(r["answers"][0]["value"] / np.linalg.cond(A, 1) - 1) < 1e-8)
    # QR / least squares with tall matrix
    m_rows = n + random.randint(1, 4)
    T = np.random.RandomState(t + 7).randn(m_rows, n)
    bt = np.random.RandomState(t + 8).randn(m_rows)
    TP = {"A": "\n".join(",".join(repr(float(v)) for v in row) for row in T), "b": ",".join(repr(float(v)) for v in bt)}
    ref = np.linalg.lstsq(T, bt, rcond=None)[0]
    for m in ("lls", "qr"):
        code, r = solve(m, TP)
        check(f"random {m}", code == 200 and np.allclose(r["answers"][0]["value"], ref, atol=1e-8), str(r)[:100])
    code, r = solve("svd", {"A": TP["A"]})
    check("random svd", code == 200 and np.allclose(r["answers"][0]["value"], np.linalg.svd(T, compute_uv=False), atol=1e-8))
    code, r = solve("gram_schmidt", {"A": TP["A"], "variant": "modified"})
    Q = np.array(r["answers"][0]["value"])
    check("random gram-schmidt orthonormal", code == 200 and np.allclose(Q.T @ Q, np.eye(n), atol=1e-8))

# integration vs quad on several functions
for f, a, b in [("sin(x)", 0, math.pi), ("exp(-x^2)", -1, 2), ("1/(1+x^2)", 0, 5), ("x^3 - 2x", -1, 3), ("log(x)", 1, 4), ("sqrt(x)", 0, 2)]:
    for m, extra in (("simpson", {"n": "200"}), ("gauss", {"npts": "16"}), ("newton_cotes", {"degree": "4", "panels": "20"}), ("trapezoid", {"n": "4000"}), ("midpoint", {"n": "4000"})):
        code, r = solve(m, {"f": f, "a": str(a), "b": str(b), **extra})
        tol = 5e-3 if f == "sqrt(x)" else 1e-5
        check(f"integral {m} {f}", code == 200 and r["error_analysis"]["absolute_error"] < tol, str(r["error_analysis"]["absolute_error"]) if code == 200 else str(r))
# Gauss nodes against NumPy
from methods.integration import gauss_nodes_weights  # noqa: E402
for n in range(1, 13):
    t, w = gauss_nodes_weights(n)
    rt, rw = np.polynomial.legendre.leggauss(n)
    check(f"gauss nodes n={n}", np.allclose(t, rt, atol=1e-13) and np.allclose(w, rw, atol=1e-13))
# exactness of Gauss n=3 for degree 5
code, r = solve("gauss", {"f": "x^5 + 3x^2", "a": "0", "b": "2", "npts": "3"})
check("gauss exact degree 5", abs(r["answers"][0]["value"] - (64 / 6 + 8)) < 1e-12)
# Simpson exact for cubic
code, r = solve("simpson", {"f": "x^3", "a": "0", "b": "2", "n": "2"})
check("simpson exact cubic", abs(r["answers"][0]["value"] - 4) < 1e-12)
# root finders on several functions
for f, a, b, x0 in [("cos(x) - x", 0, 1, 0.5), ("exp(x) - 3", 0, 2, 1), ("x^2 - 2", 1, 2, 1.5), ("x^3 - 6x^2 + 11x - 6.1", 2.5, 3.5, 3)]:
    for m, p in (("bisection", {"f": f, "a": a, "b": b, "tol": "1e-10", "max_iter": 100}), ("newton", {"f": f, "x0": x0, "tol": "1e-12", "max_iter": 50}), ("secant", {"f": f, "x0": a, "x1": b, "tol": "1e-12", "max_iter": 50})):
        code, r = solve(m, {k: str(v) for k, v in p.items()})
        check(f"root {m} {f}", code == 200 and r["error_analysis"]["absolute_error"] < 1e-8, str(r)[:150])
# ODE orders
from methods import ode  # noqa: E402
from utils.safe_expr import Expr  # noqa: E402
F, EX = Expr("y - t**2 + 1", ("t", "y")), Expr("(t+1)**2 - 0.5*exp(t)", ("t",))
for method, order in (("euler", 1), ("rk2", 2), ("rk4", 4)):
    e1 = ode.solve_ode(F, 0, 0.5, 0.1, 20, method, "heun", lambda t: EX(t))["errors"][-1]
    e2 = ode.solve_ode(F, 0, 0.5, 0.05, 40, method, "heun", lambda t: EX(t))["errors"][-1]
    check(f"ode order {method}", abs(math.log2(e1 / e2) - order) < 0.15, f"{math.log2(e1 / e2)}")
code, r = solve("rk2", {"f": "y", "t0": "0", "y0": "1", "h": "0.1", "n": "10", "variant": "midpoint", "exact": "exp(t)"})
check("rk2 midpoint", code == 200 and r["error_analysis"]["absolute_error"] < 5e-3)
# optimisation, eigen
code, r = solve("gradient", {"f": "(x-3)^2 + (y+1)^2", "x0": "0", "y0": "0", "alpha": "0.3", "line_search": "fixed", "tol": "1e-10", "max_iter": "500"})
check("gradient", code == 200 and np.allclose(r["answers"][0]["value"], [3, -1], atol=1e-7))
code, r = solve("newton_opt", {"f": "x^4 + y^2 - 2x*y", "x0": "1", "y0": "1", "tol": "1e-10", "max_iter": "50"})
check("newton_opt quartic", code == 200 and abs(r["answers"][0]["value"][0] - 2 ** -0.5) < 1e-6, str(r)[:150])
for variant, shift, target in (("power", "0", 5), ("inverse", "0", 2), ("shifted", "4.2", 5)):
    code, r = solve("eigen", {"A": "4,1\n2,3", "x0": "1,0", "variant": variant, "shift": shift, "tol": "1e-12", "max_iter": "500"})
    check(f"eigen {variant}", code == 200 and abs(r["answers"][0]["value"] - target) < 1e-8, str(r)[:150])
# floating point facts
code, r = solve("machine_eps", {"precision": "double"})
check("machine eps double", r["answers"][0]["value"] == 2.0 ** -52)
code, r = solve("machine_eps", {"precision": "single"})
check("machine eps single", abs(r["answers"][0]["value"] - 2.0 ** -23) < 1e-20)
code, r = solve("float_repr", {"x": "-6.5", "precision": "double"})
check("float -6.5", code == 200 and r["tables"][0]["rows"][0][1] == "1" and r["tables"][0]["rows"][1][1] == "10000000001")

# ---------------------------------------------------------------- 4 edge cases / validation
print("== edge cases ==")
bad = [
    ("bisection", {"f": "x^2 + 1", "a": "0", "b": "1", "tol": "1e-6", "max_iter": "50"}, "same sign"),
    ("bisection", {"f": "x", "a": "2", "b": "1", "tol": "1e-6", "max_iter": "50"}, "smaller"),
    ("bisection", {"f": "x +", "a": "0", "b": "1", "tol": "1e-6", "max_iter": "50"}, "understand"),
    ("bisection", {"f": "__import__('os')", "a": "0", "b": "1", "tol": "1e-6", "max_iter": "50"}, "not allowed"),
    ("bisection", {"f": "x.real", "a": "0", "b": "1", "tol": "1e-6", "max_iter": "50"}, "not allowed"),
    ("bisection", {"f": "y - 1", "a": "0", "b": "2", "tol": "1e-6", "max_iter": "50"}, "Unknown symbol"),
    ("newton", {"f": "x^2 - 1", "x0": "0", "tol": "1e-8", "max_iter": "20"}, "zero"),
    ("secant", {"f": "x^2 + 1", "x0": "1", "x1": "1", "tol": "1e-8", "max_iter": "20"}, "different"),
    ("simpson", {"f": "x^2", "a": "0", "b": "1", "n": "3"}, "EVEN"),
    ("simpson", {"f": "x^2", "a": "1", "b": "0", "n": "4"}, "smaller"),
    ("trapezoid", {"f": "log(x)", "a": "-1", "b": "1", "n": "4"}, "not defined"),
    ("lagrange", {"xs": "1,1,2", "ys": "1,2,3", "xe": "1.5"}, "same x"),
    ("lagrange", {"xs": "1,2,3", "ys": "1,2", "xe": "1.5"}, "must have"),
    ("gauss_elim", {"A": "1,2\n2,4", "b": "1,2", "pivoting": "partial"}, "singular"),
    ("gauss_elim", {"A": "1,2,3\n4,5,6", "b": "1,2", "pivoting": "partial"}, "square"),
    ("lu", {"A": "0,1\n1,0", "b": "1,2"}, "Zero pivot"),
    ("cholesky", {"A": "1,2\n2,1", "b": "1,1"}, "not positive definite"),
    ("cholesky", {"A": "1,2\n0,1", "b": "1,1"}, "SYMMETRIC"),
    ("inverse", {"A": "1,2\n2,4"}, "singular"),
    ("iterative", {"A": "1,2\n3,1", "b": "1,1", "x0": "0,0", "method": "jacobi", "tol": "1e-8", "max_iter": "500"}, "diverging"),
    ("iterative", {"A": "0,1\n1,0", "b": "1,1", "x0": "0,0", "method": "jacobi", "tol": "1e-8", "max_iter": "50"}, "zero"),
    ("cg", {"A": "1,2\n2,1", "b": "1,1", "x0": "0,0", "tol": "1e-8", "max_iter": "50"}, "positive definite"),
    ("ode", None, None),
    ("euler", {"f": "y*y", "t0": "0", "y0": "2", "h": "0.5", "n": "30", "exact": ""}, "blows up"),
    ("gradient", {"f": "x^2 + y^2", "x0": "1", "y0": "1", "alpha": "5", "line_search": "fixed", "tol": "1e-8", "max_iter": "500"}, "diverged"),
    ("gram_schmidt", {"A": "1,2\n2,4\n3,6", "variant": "modified"}, "dependent"),
    ("qr", {"A": "1,2,3\n4,5,6", "b": ""}, "at least as many rows"),
    ("float_repr", {"x": "1e400", "precision": "double"}, None),
    ("legendre", {"n": "20", "x0": "0.5"}, "between"),
    ("bisection", {"f": "x", "a": "", "b": "1", "tol": "1e-6", "max_iter": "50"}, "Please enter"),
    ("bisection", {"f": "x", "a": "abc", "b": "1", "tol": "1e-6", "max_iter": "50"}, "number"),
    ("not_a_method", {}, "Unknown"),
]
for m, p, text in bad:
    if p is None:
        continue
    code, r = solve(m, p)
    check(f"edge {m} {text}", code == 400 and (text is None or text.lower() in r.get("error", "").lower()), f"{code} {r.get('error')}")
# no server crash with unusual JSON
r = client.post("/api/solve", data="not json", content_type="application/json")
check("bad json handled", r.status_code in (400, 500) and r.json is not None)

# ---------------------------------------------------------------- 5 challenges
print("== challenges ==")
for cid in challenges.CHALLENGES:
    r = client.post(f"/api/challenge/{cid}", json={})
    check(f"challenge {cid}", r.status_code == 200 and r.json["plot"], str(r.json)[:100])
    for res in r.json["results"]:
        check(f"challenge {cid} {res['id']} accurate", not res.get("failed") and res["abs_error"] < 0.5, str(res.get("abs_error")))
r = client.post("/api/challenge/root", json={"methods": ["simpson"]})
check("challenge refuses wrong method", r.status_code == 400)
r = client.post("/api/challenge/integration", json={"knobs": {"n": "6"}})
check("challenge validates knobs", r.status_code == 400)

print()
print("ALL TESTS PASSED" if not failures else f"{len(failures)} FAILURES:\n" + "\n".join(failures))
sys.exit(1 if failures else 0)
