"""Helpers that read and validate the values sent from the website."""
import math
import re

from utils.errors import NumericalError
from utils.safe_expr import Expr, number


def get_expr(p, name, variables=("x",), label=None):
    label = label or name
    return Expr(p.get(name, ""), variables)


def get_float(p, name, label=None, minimum=None, maximum=None):
    label = label or name
    raw = p.get(name, "")
    if raw is None or str(raw).strip() == "":
        raise NumericalError(f"Please enter a value for '{label}'.")
    try:
        v = number(raw)
    except NumericalError:
        raise NumericalError(f"'{label}' must be a number (you typed '{raw}').")
    if not math.isfinite(v):
        raise NumericalError(f"'{label}' must be a finite number.")
    if minimum is not None and v < minimum:
        raise NumericalError(f"'{label}' must be at least {minimum}.")
    if maximum is not None and v > maximum:
        raise NumericalError(f"'{label}' must be at most {maximum}.")
    return v


def get_int(p, name, label=None, minimum=1, maximum=100000):
    v = get_float(p, name, label)
    if abs(v - round(v)) > 1e-9:
        raise NumericalError(f"'{label or name}' must be a whole number.")
    v = int(round(v))
    if v < minimum or v > maximum:
        raise NumericalError(f"'{label or name}' must be between {minimum} and {maximum}.")
    return v


def get_select(p, name, options, default=None):
    v = p.get(name, default)
    if v not in options:
        raise NumericalError(f"Invalid choice for '{name}'.")
    return v


def get_list(p, name, label=None, min_len=1):
    """'1, 2, 3.5' -> [1.0, 2.0, 3.5]"""
    label = label or name
    raw = str(p.get(name, "")).strip()
    parts = [s for s in re.split(r"[,\s;]+", raw) if s]
    if len(parts) < min_len:
        raise NumericalError(f"'{label}' needs at least {min_len} value(s), separated by commas.")
    out = []
    for s in parts:
        try:
            out.append(number(s))
        except NumericalError:
            raise NumericalError(f"'{label}' contains '{s}', which is not a number.")
    return out


def get_matrix(p, name, label=None, square=False):
    """Rows separated by new lines or ';', entries by commas or spaces."""
    label = label or name
    raw = str(p.get(name, "")).strip()
    rows = [r for r in re.split(r"[\n;]+", raw) if r.strip()]
    if not rows:
        raise NumericalError(f"Please enter matrix {label}.")
    matrix = []
    for r in rows:
        r = r.strip().strip("[]")
        parts = [s for s in re.split(r"[,\s]+", r) if s]
        try:
            matrix.append([number(s) for s in parts])
        except NumericalError:
            raise NumericalError(f"Matrix {label} contains something that is not a number.")
    width = len(matrix[0])
    if any(len(r) != width for r in matrix):
        raise NumericalError(f"Every row of matrix {label} must have the same number of entries.")
    if square and len(matrix) != width:
        raise NumericalError(f"Matrix {label} must be square (it is {len(matrix)} x {width}).")
    if len(matrix) > 12 or width > 12:
        raise NumericalError("Please keep matrices at most 12 x 12.")
    return matrix


def get_vector(p, name, label=None, length=None):
    v = get_list(p, name, label)
    if length is not None and len(v) != length:
        raise NumericalError(f"'{label or name}' must have {length} entries (it has {len(v)}).")
    return v


def g(x, digits=8):
    """Short number formatting used inside step-by-step text."""
    if isinstance(x, str):
        return x
    if x == 0:
        return "0"
    if abs(x) >= 1e7 or abs(x) < 1e-5:
        return f"{x:.{digits - 3}e}"
    return f"{x:.{digits}g}"


def field(name, label, ftype, default, help="", **extra):
    """Describes one input box of a method's form (the website builds the form from this)."""
    d = {"name": name, "label": label, "type": ftype, "default": default, "help": help}
    d.update(extra)
    return d
