"""Collects every method from every module into one catalogue."""
from methods import (approximation, computer_arithmetic, curve_fitting, differentiation, eigenvalues,
                     integration, interpolation, linear_algebra, ode, optimization, root_finding)

CATEGORIES = [
    {"id": "root", "name": "Root Finding", "blurb": "Solve f(x) = 0"},
    {"id": "interp", "name": "Interpolation & Curve Fitting", "blurb": "Curves through or near data"},
    {"id": "integration", "name": "Numerical Integration", "blurb": "Areas under curves"},
    {"id": "diffode", "name": "Differentiation & ODEs", "blurb": "Slopes and changing systems"},
    {"id": "linalg", "name": "Numerical Linear Algebra", "blurb": "Systems, factorizations, conditioning"},
    {"id": "approx", "name": "Best Approximation", "blurb": "Least squares, QR and SVD"},
    {"id": "optim", "name": "Optimization & Eigenvalues", "blurb": "Minima and eigenpairs"},
    {"id": "arith", "name": "Computer Arithmetic & Errors", "blurb": "How computers store numbers"},
]

ORDER = [
    "bisection", "fixed_point", "newton", "secant",
    "lagrange", "hermite", "spline", "poly_approx", "least_squares", "curve_fitting",
    "midpoint", "trapezoid", "simpson", "newton_cotes", "gauss", "legendre",
    "numdiff", "euler", "rk2", "rk4",
    "gauss_elim", "pivoting", "lu", "cholesky", "inverse", "iterative", "conditioning", "cond_number",
    "lls", "gram_schmidt", "qr", "svd",
    "gradient", "cg", "newton_opt", "eigen",
    "float_repr", "rounding", "machine_eps", "error_analysis",
]

_all = {}
for module in (root_finding, interpolation, curve_fitting, integration, differentiation, ode, linear_algebra,
               approximation, optimization, eigenvalues, computer_arithmetic):
    _all.update(module.SPECS)

assert set(ORDER) == set(_all), set(ORDER) ^ set(_all)
METHODS = {k: _all[k] for k in ORDER}


def defaults(method_id):
    return {f["name"]: f["default"] for f in METHODS[method_id]["inputs"]}


def catalog():
    items = []
    for k, s in METHODS.items():
        items.append({"id": k, "name": s["name"], "category": s["category"], "formula": s["formula"], "inputs": s["inputs"]})
    return {"categories": CATEGORIES, "methods": items}
