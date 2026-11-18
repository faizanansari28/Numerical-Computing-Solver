"""Tiny symbolic differentiation for user expressions.

Used so that Newton's method and the optimisation methods can use the EXACT
derivative / gradient of what the user typed. If an expression cannot be
differentiated (for example abs(x)) the caller falls back to finite differences.
"""
import ast
import math

from utils.errors import NumericalError
from utils.safe_expr import Expr, evaluate


def _is_num(n, value=None):
    ok = isinstance(n, ast.Constant)
    return ok and (value is None or n.value == value)


def _num(v):
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        v = int(v)
    return ast.Constant(v)


def _depends(n, var):
    return any(isinstance(m, ast.Name) and m.id == var for m in ast.walk(n))


def _neg(a):
    if _is_num(a):
        return _num(-a.value)
    return ast.UnaryOp(ast.USub(), a)


def _add(a, b):
    if _is_num(a, 0):
        return b
    if _is_num(b, 0):
        return a
    if _is_num(a) and _is_num(b):
        return _num(a.value + b.value)
    return ast.BinOp(a, ast.Add(), b)


def _sub(a, b):
    if _is_num(b, 0):
        return a
    if _is_num(a, 0):
        return _neg(b)
    if _is_num(a) and _is_num(b):
        return _num(a.value - b.value)
    return ast.BinOp(a, ast.Sub(), b)


def _mul(a, b):
    if _is_num(a, 0) or _is_num(b, 0):
        return _num(0)
    if _is_num(a, 1):
        return b
    if _is_num(b, 1):
        return a
    if _is_num(a) and _is_num(b):
        return _num(a.value * b.value)
    return ast.BinOp(a, ast.Mult(), b)


def _div(a, b):
    if _is_num(a, 0):
        return _num(0)
    if _is_num(b, 1):
        return a
    return ast.BinOp(a, ast.Div(), b)


def _pow(a, n):
    if _is_num(n, 1):
        return a
    if _is_num(n, 0):
        return _num(1)
    return ast.BinOp(a, ast.Pow(), n)


def _call(name, a):
    return ast.Call(ast.Name(name, ast.Load()), [a], [])


def diff(node, var):
    """Return the derivative tree of `node` with respect to variable `var`."""
    if isinstance(node, ast.Constant):
        return _num(0)
    if isinstance(node, ast.Name):
        return _num(1) if node.id == var else _num(0)
    if isinstance(node, ast.UnaryOp):
        d = diff(node.operand, var)
        return _neg(d) if isinstance(node.op, ast.USub) else d
    if isinstance(node, ast.BinOp):
        a, b = node.left, node.right
        da, db = diff(a, var), diff(b, var)
        if isinstance(node.op, ast.Add):
            return _add(da, db)
        if isinstance(node.op, ast.Sub):
            return _sub(da, db)
        if isinstance(node.op, ast.Mult):
            return _add(_mul(da, b), _mul(a, db))
        if isinstance(node.op, ast.Div):
            return _div(_sub(_mul(da, b), _mul(a, db)), _pow(b, _num(2)))
        # power
        if not _depends(b, var):                      # (a)^n
            n = float(evaluate(b, {}))
            return _mul(_mul(_num(n), _pow(a, _num(n - 1))), da)
        if not _depends(a, var):                      # c^(b)
            return _mul(_mul(node, _call("log", a)), db)
        return _mul(node, _add(_mul(db, _call("log", a)), _div(_mul(b, da), a)))  # general
    if isinstance(node, ast.Call):
        name, u = node.func.id, node.args[0]
        du = diff(u, var)
        rules = {
            "sin": lambda: _call("cos", u),
            "cos": lambda: _neg(_call("sin", u)),
            "tan": lambda: _div(_num(1), _pow(_call("cos", u), _num(2))),
            "exp": lambda: node,
            "log": lambda: _div(_num(1), u),
            "ln": lambda: _div(_num(1), u),
            "log10": lambda: _div(_num(1), _mul(u, _num(math.log(10)))),
            "log2": lambda: _div(_num(1), _mul(u, _num(math.log(2)))),
            "sqrt": lambda: _div(_num(1), _mul(_num(2), node)),
            "sinh": lambda: _call("cosh", u),
            "cosh": lambda: _call("sinh", u),
            "tanh": lambda: _sub(_num(1), _pow(node, _num(2))),
            "atan": lambda: _div(_num(1), _add(_num(1), _pow(u, _num(2)))),
            "asin": lambda: _div(_num(1), _call("sqrt", _sub(_num(1), _pow(u, _num(2))))),
            "acos": lambda: _neg(_div(_num(1), _call("sqrt", _sub(_num(1), _pow(u, _num(2)))))),
            "cbrt": lambda: _div(_num(1), _mul(_num(3), _pow(node, _num(2)))),
        }
        if name not in rules:
            raise NumericalError(f"Cannot differentiate {name}() symbolically.")
        return _mul(rules[name](), du)
    raise NumericalError("Cannot differentiate that expression.")


def derivative(expr, var=None):
    """Expr -> Expr for d/dvar. Returns None if it cannot be differentiated."""
    var = var or expr.variables[0]
    try:
        tree = diff(expr.tree, var)
    except NumericalError:
        return None
    return Expr(ast.unparse(tree), expr.variables, tree=tree)


def numeric_derivative(f, x, h=1e-6):
    """Central difference fallback: (f(x+h) - f(x-h)) / (2h)."""
    return (f(x + h) - f(x - h)) / (2 * h)
