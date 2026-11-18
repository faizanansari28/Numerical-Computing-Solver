"""Computer arithmetic: floating point, rounding/chopping, machine epsilon, error analysis."""
import math
import struct
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

import numpy as np

from utils.errors import NumericalError
from utils.inputs import field, g, get_float, get_int, get_select
from utils.results import answer, finish


# ===================================================== PART 1: ALGORITHMS
def float_representation(text, x, precision):
    if precision == "single":
        raw = struct.unpack(">I", struct.pack(">f", x))[0]
        total, ebits, mbits, bias = 32, 8, 23, 127
        stored = float(np.float32(x))
    else:
        raw = struct.unpack(">Q", struct.pack(">d", x))[0]
        total, ebits, mbits, bias = 64, 11, 52, 1023
        stored = x
    bits = format(raw, f"0{total}b")
    sign, expo, mant = bits[0], bits[1:1 + ebits], bits[1 + ebits:]
    e = int(expo, 2)
    if e == 2 ** ebits - 1:
        raise NumericalError("That value overflows to infinity (or NaN) in this precision.")
    frac = int(mant, 2) / 2 ** mbits
    if e == 0:
        value = (-1) ** int(sign) * 2 ** (1 - bias) * frac
        form = f"(-1)^{sign} × 2^({1 - bias}) × 0.{mant[:12]}…   (subnormal number)"
    else:
        value = (-1) ** int(sign) * 2 ** (e - bias) * (1 + frac)
        form = f"(-1)^{sign} × 2^({e} − {bias}) × 1.{mant[:12]}…₂ = (-1)^{sign} × 2^{e - bias} × {g(1 + frac, 12)}"
    exact_stored = Decimal(stored)
    typed = Decimal(text) if _is_decimal(text) else Decimal(repr(x))
    err = abs(exact_stored - typed)
    steps = [f"{'Single' if precision == 'single' else 'Double'} precision uses {total} bits: 1 sign + {ebits} exponent + {mbits} fraction bits.",
             f"Sign bit = {sign} ({'negative' if sign == '1' else 'positive'}).",
             f"Exponent field = {expo}₂ = {e}; the true exponent is {e} − {bias} = {e - bias} (the bias is {bias}).",
             "Value = (-1)^s × 2^(e − bias) × (1.fraction)₂ :   " + form,
             f"Normalised scientific notation of the stored number: {stored:.{12}e}",
             f"The computer actually stores {exact_stored:.30g}; you typed {text}. Representation error = {err:.3e}."]
    rows = [["sign", sign, "+" if sign == "0" else "−"], ["exponent", expo, e - bias], ["fraction (mantissa)", mant, 1 + frac if e else frac]]
    return {
        "answers": [answer("Stored value", value)], "steps": steps, "iterations": None, "converged": None,
        "columns": ["field", "bits", "meaning"], "rows": rows, "table_title": "IEEE 754 fields",
        "metrics": [{"label": "Representation error |stored − typed|", "value": float(err)}, {"label": "Relative error", "value": float(err / abs(typed)) if typed != 0 else 0.0}],
        "plot": {"kind": "bits", "sign": sign, "exponent": expo, "mantissa": mant},
        "notes": ["Most decimal fractions (like 0.1) cannot be written exactly with a finite number of binary digits."],
        "typed": float(typed),
    }


def _is_decimal(text):
    try:
        Decimal(text)
        return True
    except Exception:
        return False


def rounding_truncation(x, digits):
    if x == 0:
        raise NumericalError("Please use a non-zero number.")
    d = Decimal(repr(x))
    exponent = d.adjusted()
    rows = []
    chosen = None
    for k in range(1, 11):
        quant = Decimal(1).scaleb(exponent - k + 1)
        chopped = d.quantize(quant, rounding=ROUND_DOWN)
        rounded = d.quantize(quant, rounding=ROUND_HALF_UP)
        rows.append([k, float(chopped), float(abs(d - chopped)), float(rounded), float(abs(d - rounded))])
        if k == digits:
            chosen = (chopped, rounded)
    chopped, rounded = chosen
    steps = [f"x = {x!r} written in normalised form: {d.scaleb(-exponent):.10g} × 10^{exponent}.",
             f"Chopping (truncation) to {digits} significant digits simply cuts the extra digits off: {float(chopped)!r}.",
             f"Rounding to {digits} significant digits looks at the next digit (5 or more rounds up): {float(rounded)!r}.",
             f"Absolute errors: chopping {float(abs(d - chopped)):.3e}, rounding {float(abs(d - rounded)):.3e}.",
             f"Rounding error ≤ ½·10^({exponent - digits + 1}) = {0.5 * 10 ** (exponent - digits + 1):.3e}, chopping error < 10^({exponent - digits + 1})."]
    return {
        "answers": [answer(f"Rounded to {digits} digits", float(rounded)), answer(f"Chopped to {digits} digits", float(chopped))],
        "steps": steps, "iterations": None, "converged": None,
        "columns": ["digits k", "chopped", "|error| chop", "rounded", "|error| round"], "rows": rows,
        "metrics": [{"label": "Absolute error (chopping)", "value": float(abs(d - chopped))}, {"label": "Absolute error (rounding)", "value": float(abs(d - rounded))}],
        "plot": {"kind": "series", "lines": [{"label": "chopping error", "x": [r[0] for r in rows], "y": [max(r[2], 1e-300) for r in rows]},
                                             {"label": "rounding error", "x": [r[0] for r in rows], "y": [max(r[4], 1e-300) for r in rows]}],
                 "logy": True, "xlabel": "significant digits kept", "ylabel": "absolute error"},
        "notes": ["Rounding is usually about twice as accurate as chopping."], "true": x,
    }


def machine_epsilon(precision):
    one = np.float32(1.0) if precision == "single" else np.float64(1.0)
    eps = one
    rows, k = [], 0
    while True:
        half = eps / type(one)(2)
        rows.append([k, float(eps), float(one + eps), float((one + half) - one)])
        if one + half == one:
            break
        eps, k = half, k + 1
    ref = float(np.finfo(type(one)).eps)
    sum_test = 0.1 + 0.2
    steps = ["Machine epsilon is the smallest number ε for which 1 + ε is still different from 1 in the computer.",
             "Algorithm: start with ε = 1 and keep halving it while 1 + ε/2 is still greater than 1.",
             f"The loop stopped after {k} halvings: ε = 2^(-{k}) = {float(eps):.6e}.",
             f"NumPy's finfo({'float32' if precision == 'single' else 'float64'}).eps = {ref:.6e}.",
             f"Consequence: 0.1 + 0.2 = {sum_test!r} and (0.1 + 0.2 == 0.3) is {sum_test == 0.3}."]
    return {
        "answers": [answer("Machine epsilon ε", float(eps))], "steps": steps, "iterations": k, "converged": None,
        "columns": ["k", "ε = 2^-k", "1 + ε", "(1 + ε/2) − 1"], "rows": rows, "table_title": "Halving ε",
        "plot": {"kind": "series", "lines": [{"label": "ε", "x": [r[0] for r in rows], "y": [r[1] for r in rows]},
                                             {"label": "(1 + ε/2) − 1  (what the computer sees)", "x": [r[0] for r in rows], "y": [r[3] for r in rows]}],
                 "logy": True, "xlabel": "k", "ylabel": "value"},
        "metrics": [{"label": "Decimal digits of precision ≈ −log10 ε", "value": -math.log10(float(eps))}],
        "notes": ["Relative rounding error of any single operation is at most about ε/2."], "ref": ref,
    }


def error_analysis(mode, exact, approx, x, terms):
    if mode == "values":
        if exact == 0:
            raise NumericalError("The exact value is 0, so the relative error is undefined. Use a non-zero exact value.")
        abs_err = abs(exact - approx)
        rel = abs_err / abs(exact)
        sig = 0 if rel >= 0.5 else int(math.floor(-math.log10(2 * rel))) if rel > 0 else 16
        steps = [f"Absolute error = |exact − approximate| = |{g(exact)} − {g(approx)}| = {g(abs_err)}.",
                 f"Relative error = absolute error / |exact| = {g(rel)}  ({g(rel * 100, 5)} %).",
                 f"Number of correct significant digits ≈ {sig} (largest s with relative error < 5×10^-s)."]
        return {"answers": [answer("Absolute error", abs_err), answer("Relative error", rel)], "steps": steps, "iterations": None, "converged": None,
                "columns": ["quantity", "value"], "rows": [["exact value", exact], ["approximate value", approx], ["absolute error", abs_err], ["relative error", rel],
                                                           ["percentage error", rel * 100], ["correct significant digits", sig]], "table_title": "Error measures",
                "plot": {"kind": "bars", "labels": ["exact", "approximate"], "values": [abs(exact), abs(approx)], "title": "Exact vs approximate (magnitude)"},
                "notes": ["Absolute error has the units of the quantity; relative error is unit-free and shows how serious the error is."], "exact_err": abs_err}
    true = math.exp(x)
    rows, s, term = [], 0.0, 1.0
    for n in range(terms):
        if n > 0:
            term = term * x / n
        s += term
        err = abs(true - s)
        bound = max(1.0, math.exp(x)) * abs(x) ** (n + 1) / math.factorial(n + 1)
        rows.append([n, s, term, err, err / abs(true), bound])
    steps = ["Taylor series: e^x = 1 + x + x²/2! + x³/3! + …  Truncating after n terms creates a TRUNCATION error.",
             f"With x = {g(x)} and {terms} terms: partial sum = {g(s)}, true value e^x = {g(true)}.",
             f"Absolute truncation error = {g(abs(true - s))}.",
             "Lagrange remainder bound after the term of degree n: max(1, e^x)·|x|^(n+1)/(n+1)!  (last column) - the real error is always below it."]
    return {"answers": [answer(f"Partial sum S_{terms - 1}", s)], "steps": steps, "iterations": terms, "converged": None,
            "columns": ["n", "partial sum S_n", "term x^n/n!", "|e^x − S_n|", "relative error", "Lagrange error bound"], "rows": rows,
            "plot": {"kind": "series", "lines": [{"label": "actual error", "x": [r[0] for r in rows], "y": [max(r[3], 1e-300) for r in rows]},
                                                 {"label": "error bound", "x": [r[0] for r in rows], "y": [r[5] for r in rows]}], "logy": True, "xlabel": "n (degree)", "ylabel": "error"},
            "notes": ["Truncation error comes from cutting an infinite process short; round-off error comes from finite-precision arithmetic."], "true": true}


# ===================================================== PART 2: WEBSITE ADAPTERS
def run_float(p):
    text = str(p.get("x", "")).strip()
    x = get_float(p, "x", "Number")
    raw = float_representation(text, x, get_select(p, "precision", ["double", "single"], "double"))
    return finish(raw)


def run_rounding(p):
    x = get_float(p, "x", "Number")
    raw = rounding_truncation(x, get_int(p, "digits", "Significant digits", 1, 10))
    return finish(raw, {"label": "True value", "value": raw["true"], "exact": True})


def run_epsilon(p):
    raw = machine_epsilon(get_select(p, "precision", ["double", "single"], "double"))
    return finish(raw, {"label": "NumPy finfo.eps", "value": raw["ref"], "exact": False})


def run_error(p):
    mode = get_select(p, "mode", ["values", "taylor"], "values")
    if mode == "values":
        raw = error_analysis(mode, get_float(p, "exact", "Exact value"), get_float(p, "approx", "Approximate value"), 0, 0)
        return finish(raw)
    x = get_float(p, "x", "x")
    raw = error_analysis(mode, 0, 0, x, get_int(p, "terms", "Number of terms", 1, 40))
    return finish(raw, {"label": "math.exp(x)", "value": raw["true"], "exact": True})


SPECS = {
    "float_repr": {"name": "Floating-Point Representation", "category": "arith", "run": run_float,
                   "formula": r"x=(-1)^s\times 2^{\,e-\text{bias}}\times(1.f)_2",
                   "inputs": [field("x", "Number", "number", "0.1"), field("precision", "Precision", "select", "double", "", options=[{"value": "double", "label": "Double (64-bit)"}, {"value": "single", "label": "Single (32-bit)"}])]},
    "rounding": {"name": "Rounding and Truncation", "category": "arith", "run": run_rounding,
                 "formula": r"\text{chop: cut digits}\qquad \text{round: } |x-\mathrm{fl}(x)|\le \tfrac12\,10^{\,e-k+1}",
                 "inputs": [field("x", "Number", "number", "3.14159265"), field("digits", "Significant digits k", "int", "4")]},
    "machine_eps": {"name": "Machine Precision", "category": "arith", "run": run_epsilon,
                    "formula": r"\varepsilon=\min\{\delta>0:\ 1+\delta>1\},\qquad \varepsilon_{64}=2^{-52}",
                    "inputs": [field("precision", "Precision", "select", "double", "", options=[{"value": "double", "label": "Double (64-bit)"}, {"value": "single", "label": "Single (32-bit)"}])]},
    "error_analysis": {"name": "Numerical Error Analysis", "category": "arith", "run": run_error,
                       "formula": r"E_{abs}=|x-\hat x|,\qquad E_{rel}=\dfrac{|x-\hat x|}{|x|}",
                       "inputs": [field("mode", "What to analyse", "select", "values", "", options=[{"value": "values", "label": "Exact vs approximate value"}, {"value": "taylor", "label": "Truncation error of e^x Taylor series"}]),
                                  field("exact", "Exact value", "number", "3.14159265358979", showIf={"mode": "values"}),
                                  field("approx", "Approximate value", "number", "3.14", showIf={"mode": "values"}),
                                  field("x", "x (for e^x)", "number", "1", showIf={"mode": "taylor"}),
                                  field("terms", "Number of terms", "int", "8", showIf={"mode": "taylor"})]},
}
