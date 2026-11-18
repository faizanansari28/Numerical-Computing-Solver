"""Safe math-expression parser.

We NEVER use eval() or exec() on user text.
Steps:
  1. Clean the text (x^2 -> x**2, 2x -> 2*x).
  2. Turn it into a syntax tree with Python's `ast` module.
  3. Check every node of the tree against a small WHITELIST
     (numbers, + - * / **, a few math functions, the allowed variables).
  4. Evaluate the tree ourselves with NumPy functions.
"""
import ast
import math
import re

import numpy as np

from utils.errors import NumericalError

FUNCTIONS = {
    "sin": np.sin, "cos": np.cos, "tan": np.tan,
    "asin": np.arcsin, "acos": np.arccos, "atan": np.arctan,
    "sinh": np.sinh, "cosh": np.cosh, "tanh": np.tanh,
    "exp": np.exp, "log": np.log, "ln": np.log,
    "log10": np.log10, "log2": np.log2,
    "sqrt": np.sqrt, "abs": np.abs, "cbrt": np.cbrt,
}
CONSTANTS = {"pi": math.pi, "e": math.e}
MAX_LENGTH = 200
MAX_NODES = 250


def _preprocess(text):
    s = text.strip().replace("^", "**").replace("×", "*").replace("−", "-")
    # 2x -> 2*x, 3pi -> 3*pi, 2(x+1) -> 2*(x+1)   (but keep 1e-6 and log10(x) intact)
    s = re.sub(r"(?<![A-Za-z_\d.])(\d+\.?\d*)(?=[A-DF-Za-df-z_(]|[eE](?![\d+\-]))", r"\1*", s)
    # (x+1)(x-1) -> (x+1)*(x-1)
    s = re.sub(r"\)\s*(?=[A-Za-z_(\d])", ")*", s)
    return s


def _validate(node, variables, counter):
    counter[0] += 1
    if counter[0] > MAX_NODES:
        raise NumericalError("That expression is too long or too complicated.")
    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            raise NumericalError("Only + - * / and ^ (power) are allowed.")
        _validate(node.left, variables, counter)
        _validate(node.right, variables, counter)
    elif isinstance(node, ast.UnaryOp):
        if not isinstance(node.op, (ast.UAdd, ast.USub)):
            raise NumericalError("Only a leading + or - sign is allowed.")
        _validate(node.operand, variables, counter)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise NumericalError("Only numbers are allowed as constants.")
    elif isinstance(node, ast.Name):
        if node.id not in variables and node.id not in CONSTANTS:
            allowed = ", ".join(variables) if variables else "no variables"
            raise NumericalError(
                f"Unknown symbol '{node.id}'. Allowed variables here: {allowed} "
                f"(constants: pi, e)."
            )
    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in FUNCTIONS:
            name = getattr(node.func, "id", "that function")
            raise NumericalError(
                f"Function '{name}' is not supported. Use: " + ", ".join(sorted(FUNCTIONS)) + "."
            )
        if node.keywords or len(node.args) != 1:
            raise NumericalError(f"{node.func.id}() takes exactly one argument.")
        _validate(node.args[0], variables, counter)
    else:
        raise NumericalError("That expression contains something that is not allowed.")


def parse(text, variables=("x",)):
    if not isinstance(text, str) or not text.strip():
        raise NumericalError("Please enter a mathematical expression.")
    if len(text) > MAX_LENGTH:
        raise NumericalError("That expression is too long.")
    s = _preprocess(text)
    if re.search(r"[^0-9A-Za-z_+\-*/().\s]", s):
        raise NumericalError("The expression has a character that is not allowed. Use digits, x, + - * / ^ ( ) and functions like sin(x).")
    try:
        tree = ast.parse(s, mode="eval")
    except SyntaxError:
        raise NumericalError(f"I could not understand '{text}'. Check the brackets and operators.")
    _validate(tree.body, set(variables), [0])
    return tree.body


def evaluate(node, env):
    """Evaluate a validated tree. env maps variable name -> number or array."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env[node.id] if node.id in env else CONSTANTS[node.id]
    if isinstance(node, ast.UnaryOp):
        v = evaluate(node.operand, env)
        return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.BinOp):
        a = evaluate(node.left, env)
        b = evaluate(node.right, env)
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        if isinstance(node.op, ast.Div):
            return np.true_divide(a, b)
        return np.power(np.asarray(a, dtype=float) if not np.isscalar(a) else float(a), b)
    if isinstance(node, ast.Call):
        return FUNCTIONS[node.func.id](evaluate(node.args[0], env))
    raise NumericalError("Cannot evaluate that expression.")


class Expr:
    """A user expression turned into a callable: f = Expr('x**2 - 2'); f(3.0)."""

    def __init__(self, text, variables=("x",), tree=None):
        self.text = text
        self.variables = tuple(variables)
        self.tree = tree if tree is not None else parse(text, self.variables)

    def __call__(self, *args):
        """Strict scalar evaluation: raises a friendly error if the result is not finite."""
        env = {v: float(a) for v, a in zip(self.variables, args)}
        with np.errstate(all="ignore"):
            try:
                val = evaluate(self.tree, env)
            except (OverflowError, ValueError):
                val = float("nan")
        val = float(val)
        if not math.isfinite(val):
            where = ", ".join(f"{v} = {float(a):.6g}" for v, a in zip(self.variables, args))
            raise NumericalError(
                f"The function is not defined (division by zero, log of a negative number, overflow, ...) at {where}."
            )
        return val

    def vec(self, *arrays):
        """Lenient vectorised evaluation for plotting (NaN where undefined)."""
        env = {v: np.asarray(a, dtype=float) for v, a in zip(self.variables, arrays)}
        with np.errstate(all="ignore"):
            out = evaluate(self.tree, env)
        out = np.asarray(out, dtype=float)
        if out.shape != env[self.variables[0]].shape:
            out = np.full(env[self.variables[0]].shape, float(out))
        return out

    def pretty(self):
        return ast.unparse(self.tree).replace("**", "^")


def number(text):
    """Parse a plain number or constant expression such as '2', '1e-6', 'pi/2'."""
    if isinstance(text, (int, float)) and not isinstance(text, bool):
        v = float(text)
    else:
        v = Expr(str(text), variables=())()
    return v
