"""Initial value problems y' = f(t, y), y(t0) = y0.

Methods: Euler, Runge-Kutta 2 (Heun or midpoint), Runge-Kutta 4.
"""
import numpy as np
from scipy.integrate import solve_ivp

from utils.errors import NumericalError
from utils.inputs import field, g, get_expr, get_float, get_int, get_select
from utils.results import answer, finish


# ===================================================== PART 1: ALGORITHMS
def check_blowup(y):
    if abs(y) > 1e100:
        raise NumericalError("The numerical solution blows up (it grows without bound). Try a smaller step size h - the exact solution may also not exist on the whole interval.")


def euler(f, t0, y0, h, n):
    ts, ys, rows = [t0], [y0], []
    t, y = t0, y0
    for i in range(n):
        k1 = f(t, y)
        y_next = y + h * k1
        check_blowup(y_next)
        rows.append([i, t, y, k1, y_next])
        t, y = t + h, y_next
        ts.append(t)
        ys.append(y)
    steps = ["Euler: follow the tangent line for one step:  y_(i+1) = y_i + h·f(t_i, y_i).",
             f"First step: y_1 = {g(ys[0])} + {g(h)}·f({g(ts[0])}, {g(ys[0])}) = {g(ys[1])}."]
    return ts, ys, ["i", "t_i", "y_i", "k1 = f(t_i, y_i)", "y_(i+1)"], rows, steps, 1


def rk2(f, t0, y0, h, n, variant="heun"):
    ts, ys, rows = [t0], [y0], []
    t, y = t0, y0
    for i in range(n):
        k1 = f(t, y)
        if variant == "heun":
            k2 = f(t + h, y + h * k1)
            y_next = y + h / 2 * (k1 + k2)
        else:                                           # midpoint method
            k2 = f(t + h / 2, y + h / 2 * k1)
            y_next = y + h * k2
        check_blowup(y_next)
        rows.append([i, t, y, k1, k2, y_next])
        t, y = t + h, y_next
        ts.append(t)
        ys.append(y)
    if variant == "heun":
        steps = ["RK2 (Heun): k1 = f(t, y), k2 = f(t + h, y + h·k1), y_(i+1) = y_i + (h/2)(k1 + k2)."]
    else:
        steps = ["RK2 (midpoint): k1 = f(t, y), k2 = f(t + h/2, y + (h/2)·k1), y_(i+1) = y_i + h·k2."]
    steps.append(f"First step: k1 = {g(rows[0][3])}, k2 = {g(rows[0][4])}, y_1 = {g(ys[1])}.")
    return ts, ys, ["i", "t_i", "y_i", "k1", "k2", "y_(i+1)"], rows, steps, 2


def rk4(f, t0, y0, h, n):
    ts, ys, rows = [t0], [y0], []
    t, y = t0, y0
    for i in range(n):
        k1 = f(t, y)
        k2 = f(t + h / 2, y + h / 2 * k1)
        k3 = f(t + h / 2, y + h / 2 * k2)
        k4 = f(t + h, y + h * k3)
        y_next = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
        check_blowup(y_next)
        rows.append([i, t, y, k1, k2, k3, k4, y_next])
        t, y = t + h, y_next
        ts.append(t)
        ys.append(y)
    steps = ["RK4: k1 = f(t, y);  k2 = f(t + h/2, y + h/2·k1);  k3 = f(t + h/2, y + h/2·k2);  k4 = f(t + h, y + h·k3).",
             "y_(i+1) = y_i + (h/6)(k1 + 2k2 + 2k3 + k4)  - a weighted average of four slopes.",
             f"First step: k1..k4 = {', '.join(g(v) for v in rows[0][3:7])}, so y_1 = {g(ys[1])}."]
    return ts, ys, ["i", "t_i", "y_i", "k1", "k2", "k3", "k4", "y_(i+1)"], rows, steps, 4


def solve_ode(f, t0, y0, h, n, method, variant="heun", exact=None):
    if h <= 0:
        raise NumericalError("The step size h must be positive.")
    try:
        if method == "euler":
            ts, ys, cols, rows, steps, order = euler(f, t0, y0, h, n)
        elif method == "rk2":
            ts, ys, cols, rows, steps, order = rk2(f, t0, y0, h, n, variant)
        else:
            ts, ys, cols, rows, steps, order = rk4(f, t0, y0, h, n)
    except OverflowError:
        raise NumericalError("The solution blows up (overflow). Try a smaller step size h.")
    if any(abs(v) > 1e150 for v in ys):
        raise NumericalError("The numerical solution blows up. Try a smaller step size h.")
    t_end = ts[-1]
    # reference: exact formula if given, otherwise SciPy's accurate solver
    if exact is not None:
        ref = [exact(t) for t in ts]
        ref_label = "exact solution"
    else:
        sol = solve_ivp(lambda t, y: [f(t, y[0])], (t0, t_end), [y0], t_eval=ts, rtol=1e-12, atol=1e-13, method="DOP853")
        ref = list(sol.y[0])
        ref_label = "SciPy solve_ivp"
    errors = [abs(a - b) for a, b in zip(ys, ref)]
    for i, row in enumerate(rows):
        row.append(ref[i + 1])
        row.append(errors[i + 1])
    cols = cols + [f"y reference ({ref_label}) at t_(i+1)", "|error| at t_(i+1)"]
    dense = np.linspace(t0, t_end, 200)
    if exact is not None:
        dense_y = [exact(float(t)) for t in dense]
    else:
        dense_y = solve_ivp(lambda t, y: [f(t, y[0])], (t0, t_end), [y0], t_eval=dense, rtol=1e-12, atol=1e-13, method="DOP853").y[0]
    steps.append(f"Final value y({g(t_end)}) ≈ {g(ys[-1])}; reference {g(ref[-1])}; global error {g(errors[-1])}.")
    steps.append(f"The method has order {order}: halving h should reduce the global error by about 2^{order} = {2 ** order}.")
    return {
        "answers": [answer(f"y({g(t_end)}) ≈", ys[-1])], "steps": steps, "iterations": n, "converged": None,
        "columns": cols, "rows": rows, "table_title": "Step-by-step solution",
        "metrics": [{"label": "Largest error along the path", "value": max(errors)}], "notes": [f"Reference used: {ref_label}."],
        "plot": {"kind": "curves", "curves": [{"label": f"exact / reference ({ref_label})", "x": dense, "y": dense_y, "color": "#E8E8F2", "lw": 1.6},
                                              {"label": f"numerical ({method})", "x": ts, "y": ys, "ls": "--"}],
                 "points": {"x": ts, "y": ys, "label": "computed values"}, "xlabel": "t", "ylabel": "y(t)"},
        "ref_end": ref[-1], "t": ts, "y": ys, "errors": errors,
    }


# ===================================================== PART 2: WEBSITE ADAPTERS
def _run(p, method):
    f = get_expr(p, "f", ("t", "y"))
    t0, y0 = get_float(p, "t0", "t0"), get_float(p, "y0", "y(t0)")
    h = get_float(p, "h", "Step size h", 1e-9)
    n = get_int(p, "n", "Number of steps", 1, 20000)
    exact = None
    if str(p.get("exact", "")).strip():
        ex = get_expr(p, "exact", ("t",))
        exact = lambda t: ex(t)
    variant = get_select(p, "variant", ["heun", "midpoint"], "heun") if method == "rk2" else "heun"
    raw = solve_ode(f, t0, y0, h, n, method, variant, exact)
    return finish(raw, {"label": "Exact solution" if exact else "SciPy solve_ivp", "value": raw["ref_end"], "exact": exact is not None})


F = field("f", "Right-hand side f(t, y)  in  y' = f(t, y)", "expr", "y - t**2 + 1", "Use the variables t and y.", vars=["t", "y"])
COMMON = [F, field("t0", "Initial time t0", "number", "0"), field("y0", "Initial value y(t0)", "number", "0.5"),
          field("h", "Step size h", "number", "0.2"), field("n", "Number of steps", "int", "10"),
          field("exact", "Exact solution y(t) (optional)", "expr", "(t+1)**2 - 0.5*exp(t)", "If you know it, errors are measured against it.", optional=True, vars=["t"])]

SPECS = {
    "euler": {"name": "Euler's Method", "category": "diffode", "run": lambda p: _run(p, "euler"),
              "formula": r"y_{i+1}=y_i+h\,f(t_i,y_i)", "inputs": COMMON},
    "rk2": {"name": "Runge-Kutta 2 (RK2)", "category": "diffode", "run": lambda p: _run(p, "rk2"),
            "formula": r"k_1=f(t_i,y_i),\ k_2=f(t_i+h,y_i+hk_1),\ y_{i+1}=y_i+\tfrac h2(k_1+k_2)",
            "inputs": COMMON + [field("variant", "RK2 variant", "select", "heun", "", options=[{"value": "heun", "label": "Heun (improved Euler)"}, {"value": "midpoint", "label": "Midpoint"}])]},
    "rk4": {"name": "Runge-Kutta 4 (RK4)", "category": "diffode", "run": lambda p: _run(p, "rk4"),
            "formula": r"y_{i+1}=y_i+\tfrac h6\,(k_1+2k_2+2k_3+k_4)", "inputs": COMMON},
}
