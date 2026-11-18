import math
from content.helpers import entry

ROOT_EXACT = None

CONTENT = {
"bisection": entry(
    what="The bisection method finds a root of f(x) = 0 by repeatedly cutting an interval [a, b] in half and keeping the half in which the function changes sign.",
    why="Many equations (like x³ − x − 2 = 0) cannot be solved with algebra. Bisection is slow but extremely reliable, so it is the safe fallback when other methods fail.",
    solves="Given a continuous function f and an interval [a, b] with f(a)·f(b) < 0, it finds x* in [a, b] with f(x*) = 0.",
    uses="Engineering design (finding the operating point of a circuit), finance (solving for an interest rate), and as the starting stage of faster hybrid solvers such as Brent's method.",
    explain="If a continuous function is negative at one end of an interval and positive at the other, the graph must cross the x-axis somewhere inside (Intermediate Value Theorem). Look at the midpoint c: the root lies in whichever half still shows a sign change. Repeat until the interval is as small as you like.",
    formula=r"c_n=\dfrac{a_n+b_n}{2},\qquad \text{if } f(a_n)f(c_n)<0:\ b_{n+1}=c_n,\ \text{else } a_{n+1}=c_n",
    variables=[[r"a_n,\ b_n", "ends of the current interval"], [r"c_n", "midpoint, the current approximation of the root"], [r"f(x)", "the function whose root we want"], [r"\text{tol}", "stop when the half-width (b − a)/2 is smaller than this"]],
    why_works="Each step halves the interval, so after n steps the root is trapped in an interval of length (b − a)/2ⁿ. The error therefore shrinks by a factor 2 every iteration, and n ≥ log₂((b − a)/tol) steps always suffice.",
    code='''
def f(x):
    return x**3 - x - 2          # the equation f(x) = 0

a = 1                            # left end of the interval
b = 2                            # right end (f(1) < 0 and f(2) > 0)
tol = 1e-8                       # how accurate we want the answer
count = 0                        # counts the iterations

while True:
    c = (a + b) / 2              # midpoint of the interval
    count = count + 1
    if f(c) == 0 or (b - a) / 2 < tol:
        break                    # exact root found or interval small enough
    if f(a) * f(c) < 0:          # sign change in the LEFT half
        b = c                    # keep [a, c]
    else:
        a = c                    # keep [c, b]

print("Root =", c)
print("Iterations =", count)
''',
    adv=["Guaranteed to converge when f is continuous and f(a)·f(b) < 0.", "Simple and needs no derivative.", "The number of iterations needed is known in advance."],
    lim=["Slow: only one binary digit of accuracy per iteration (linear convergence).", "Needs a bracketing interval where the sign changes.", "Cannot find roots where the graph only touches the axis (like x² = 0), or several roots inside one interval at once."],
    related=["newton", "secant", "fixed_point"],
    example_intro="Solve x³ − x − 2 = 0 on [1, 2]. Here f(1) = −2 < 0 and f(2) = 4 > 0, so a root is guaranteed inside.",
),
"fixed_point": entry(
    what="Fixed-point iteration rewrites f(x) = 0 as x = g(x) and then repeats x ← g(x) until the value stops changing.",
    why="It is the simplest iterative idea and the foundation of many advanced methods (Newton's method is itself a fixed-point iteration).",
    solves="Finds a number x* with g(x*) = x*, which is a root of f(x) = x − g(x).",
    uses="Solving equations in physics and economics models, iterative solvers for large systems, and as the theory behind convergence of other iterations.",
    explain="Rearrange the equation so x is alone on one side. For x³ − x − 2 = 0 we can write x = (x + 2)^(1/3). Start with a guess, feed it into g, take the output as the new guess, and repeat. If the values settle down, you have found a fixed point.",
    formula=r"x_{n+1}=g(x_n),\qquad \text{converges if } |g'(x)|<1 \text{ near } x^*",
    variables=[[r"g(x)", "the rearranged equation, x = g(x)"], [r"x_0", "starting guess"], [r"x_n", "approximation after n steps"], [r"g'(x^*)", "slope of g at the fixed point - it decides convergence"]],
    why_works="Near x*, the error satisfies e_{n+1} ≈ g'(x*)·e_n. If |g'(x*)| < 1 each step multiplies the error by something smaller than 1, so it vanishes; if |g'(x*)| > 1 the error grows. That is why a good rearrangement g matters.",
    code='''
def g(x):
    return (x + 2) ** (1 / 3)    # x**3 - x - 2 = 0 rewritten as x = (x + 2)^(1/3)

x = 1.5                          # starting guess
tol = 1e-8

for i in range(1, 101):          # at most 100 iterations
    x_new = g(x)                 # one fixed-point step
    change = abs(x_new - x)      # how much did the value move?
    x = x_new
    if change < tol:             # stop when it hardly moves
        break

print("Fixed point =", x)
print("Iterations =", i)
''',
    adv=["Very easy to program.", "Needs no derivative.", "Convergence can be proven with the condition |g'(x)| < 1."],
    lim=["Different rearrangements behave very differently - some diverge.", "Convergence is only linear.", "Needs a starting value close enough to the fixed point."],
    related=["newton", "bisection", "secant"],
    example_intro="Solve x³ − x − 2 = 0 using the rearrangement g(x) = (x + 2)^(1/3), starting from x₀ = 1.5. Near the root |g'| ≈ 0.14 < 1, so the iteration converges.",
),
"newton": entry(
    what="Newton-Raphson uses the tangent line of f at the current guess and moves to the point where that tangent crosses the x-axis.",
    why="Near the root it converges extremely fast - the number of correct digits roughly doubles each step - which is why it is the workhorse of numerical solvers.",
    solves="Finds x* with f(x*) = 0 for a differentiable function f, starting from an initial guess x₀.",
    uses="Computing square roots in calculators, power-flow analysis in electrical grids, solving nonlinear equations inside optimisation and simulation software.",
    explain="Replace the curve by its tangent line at the current guess. The tangent is a straight line, so its x-intercept is easy to compute: that intercept is the next guess. Because the tangent hugs the curve near the root, the new guess lands very close to the true root.",
    formula=r"x_{n+1}=x_n-\dfrac{f(x_n)}{f'(x_n)}",
    variables=[[r"x_n", "current guess"], [r"f(x_n)", "function value at the guess"], [r"f'(x_n)", "slope of the tangent (derivative)"], [r"x_{n+1}", "next guess = x-intercept of the tangent"]],
    why_works="The tangent line is y = f(x_n) + f'(x_n)(x − x_n). Setting y = 0 and solving for x gives exactly the formula. For a simple root the error obeys e_{n+1} ≈ (f''/2f')·e_n², i.e. it is squared at every step (quadratic convergence).",
    code='''
def f(x):
    return x**3 - x - 2

def df(x):
    return 3 * x**2 - 1          # derivative of f

x = 1.5                          # starting guess
tol = 1e-8

for n in range(50):
    if df(x) == 0:               # a flat tangent never crosses the axis
        print("Derivative is zero - choose another start")
        break
    x_new = x - f(x) / df(x)     # Newton step
    change = abs(x_new - x)
    x = x_new
    if change < tol:
        break

print("Root =", x)
print("Iterations =", n + 1)
''',
    adv=["Quadratic convergence - very few iterations.", "Works for any differentiable function, also in several variables."],
    lim=["Needs the derivative f'(x).", "Fails if f'(x) = 0 at some iterate.", "A poor starting guess can diverge or jump to a different root.", "Only linear convergence at multiple roots."],
    related=["secant", "bisection", "newton_opt"],
    example_intro="Solve x³ − x − 2 = 0 starting from x₀ = 1.5, using f'(x) = 3x² − 1.",
),
"secant": entry(
    what="The secant method is Newton's method without derivatives: it replaces the tangent line with the line through the last two points (the secant line).",
    why="Often f'(x) is hard or expensive to compute. The secant method keeps most of Newton's speed using only function values.",
    solves="Finds x* with f(x*) = 0 from two starting guesses x₀ and x₁.",
    uses="Root finding when the function comes from a simulation or measurement and has no formula for its derivative.",
    explain="Draw a straight line through (x₍ₙ₋₁₎, f(x₍ₙ₋₁₎)) and (xₙ, f(xₙ)). Where this line crosses the x-axis is the next guess. Unlike bisection the two points do not have to surround the root.",
    formula=r"x_{n+1}=x_n-f(x_n)\,\dfrac{x_n-x_{n-1}}{f(x_n)-f(x_{n-1})}",
    variables=[[r"x_{n-1},\ x_n", "the two most recent guesses"], [r"f(x_{n-1}),\ f(x_n)", "function values at those guesses"], [r"x_{n+1}", "x-intercept of the secant line"]],
    why_works="Newton's formula uses f'(x_n). The secant method approximates that slope by the difference quotient (f(x_n) − f(x_{n-1}))/(x_n − x_{n-1}). The resulting order of convergence is the golden ratio ≈ 1.618 - faster than linear, slower than Newton's 2.",
    code='''
def f(x):
    return x**3 - x - 2

x0 = 1                           # first guess
x1 = 2                           # second guess
tol = 1e-8

for i in range(1, 51):
    if f(x1) - f(x0) == 0:       # horizontal secant line: cannot divide
        print("Denominator is zero")
        break
    x2 = x1 - f(x1) * (x1 - x0) / (f(x1) - f(x0))   # secant step
    change = abs(x2 - x1)
    x0 = x1                      # shift the pair of guesses
    x1 = x2
    if change < tol:
        break

print("Root =", x1)
print("Iterations =", i)
''',
    adv=["No derivative needed.", "Superlinear convergence (order ≈ 1.618).", "Only one new function evaluation per iteration."],
    lim=["Needs two starting values.", "Can fail when f(x_n) = f(x_(n-1)).", "Not guaranteed to converge (no bracketing)."],
    related=["newton", "bisection", "fixed_point"],
    example_intro="Solve x³ − x − 2 = 0 starting from x₀ = 1 and x₁ = 2.",
),
}
