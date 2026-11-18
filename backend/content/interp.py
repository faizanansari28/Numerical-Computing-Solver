from content.helpers import entry
import math

SIN = {"label": "True value sin(2.5) (the table gives sin x rounded to 4 decimals)", "value": math.sin(2.5)}
DATA_CODE = '''
xs = [0, 1, 2, 3, 4]                         # x data
ys = [0, 0.8415, 0.9093, 0.1411, -0.7568]    # y data (sin x rounded)
'''

CONTENT = {
"lagrange": entry(
    what="Lagrange interpolation builds the one polynomial of degree n that passes exactly through n + 1 data points.",
    why="Experiments give a table of values, but we often need the value between the table entries. A polynomial through the points lets us estimate it.",
    solves="Given points (x₀, y₀) … (xₙ, yₙ) with distinct x, find P(x) with P(xₖ) = yₖ and evaluate it at a new x.",
    uses="Estimating values from tables (steam tables, sensor calibration), computer graphics, and as the basis of numerical integration formulas.",
    explain="For every data point build a basis polynomial Lₖ(x) that equals 1 at xₖ and 0 at all the other data x-values. Multiply each by its y-value and add: the result matches every data point.",
    formula=r"P(x)=\sum_{k=0}^{n}y_k\,L_k(x),\qquad L_k(x)=\prod_{j\neq k}\frac{x-x_j}{x_k-x_j}",
    variables=[[r"(x_k,y_k)", "the data points"], [r"L_k(x)", "k-th basis polynomial: 1 at x_k, 0 at every other x_j"], [r"P(x)", "interpolating polynomial of degree ≤ n"]],
    why_works="At x = x_j every basis polynomial except L_j is zero (it contains the factor x_j − x_j) and L_j(x_j) = 1, so P(x_j) = y_j. A polynomial of degree ≤ n through n+1 points is unique, so this IS the interpolating polynomial. Error: f(x) − P(x) = f⁽ⁿ⁺¹⁾(ξ)/(n+1)! · Π(x − xᵢ).",
    code=DATA_CODE + '''
x = 2.5                          # where we want the value
total = 0

for k in range(len(xs)):
    L = 1                        # basis polynomial L_k(x)
    for j in range(len(xs)):
        if j != k:
            L = L * (x - xs[j]) / (xs[k] - xs[j])
    total = total + ys[k] * L    # add y_k * L_k(x)

print("P(2.5) =", total)
''',
    adv=["Passes exactly through all data points.", "Simple closed formula; no linear system to solve."],
    lim=["High degree polynomials oscillate wildly (Runge phenomenon).", "All basis functions change when a point is added.", "Extrapolation outside the data range is unreliable."],
    related=["hermite", "spline", "poly_approx"],
    example_intro="Estimate sin(2.5) from the five points x = 0, 1, 2, 3, 4 (the true value is 0.5985).", exact=SIN,
),
"hermite": entry(
    what="Hermite interpolation finds a polynomial that matches both the VALUES and the SLOPES (first derivatives) at every data point.",
    why="When we know how fast a quantity changes as well as its value (position and velocity, for example) we can build a smoother and more accurate curve.",
    solves="Given xᵢ, f(xᵢ) and f'(xᵢ), find H(x) of degree ≤ 2n+1 with H(xᵢ) = f(xᵢ) and H'(xᵢ) = f'(xᵢ).",
    uses="Animation paths with velocity control, trajectory planning, and the construction of cubic Hermite splines in computer graphics.",
    explain="Treat every node as if it appeared twice. Newton's divided-difference table can then be built as usual; whenever it would divide 0 by 0 (a repeated node) we simply insert the known derivative instead.",
    formula=r"H(x)=f[z_0]+\sum_{k=1}^{2n+1}f[z_0,\dots,z_k]\prod_{i=0}^{k-1}(x-z_i),\quad z_{2i}=z_{2i+1}=x_i,\ \ f[z_{2i},z_{2i+1}]=f'(x_i)",
    variables=[[r"z_i", "the nodes, each repeated twice"], [r"f[z_0,\dots,z_k]", "divided difference (the coefficients)"], [r"f'(x_i)", "given slope at node x_i"]],
    why_works="A divided difference with equal nodes is the limit of the usual quotient (f(x+h) − f(x))/h as h → 0, which is the derivative. So the double node forces the polynomial to have the right slope. 2n+2 conditions determine exactly one polynomial of degree 2n+1.",
    code=DATA_CODE + '''dys = [1, 0.5403, -0.4161, -0.99, -0.6536]  # slopes (cos x rounded)
x = 2.5
n = len(xs)

z = []                           # every node appears twice
q = []                           # first column of the divided-difference table
for i in range(n):
    z = z + [xs[i], xs[i]]
    q = q + [ys[i], ys[i]]

coef = [q[0]]                    # the top edge of the table = coefficients
column = q
for level in range(1, 2 * n):
    new_col = []
    for i in range(2 * n - level):
        if z[i + level] == z[i]:
            new_col.append(dys[i // 2])          # repeated node -> use the slope
        else:
            new_col.append((column[i + 1] - column[i]) / (z[i + level] - z[i]))
    column = new_col
    coef.append(column[0])

result = coef[-1]                # evaluate the Newton form (Horner style)
for k in range(2 * n - 2, -1, -1):
    result = result * (x - z[k]) + coef[k]

print("H(2.5) =", result)
''',
    adv=["Matches values and slopes, so the curve is smoother.", "Often far more accurate than Lagrange with the same nodes."],
    lim=["Needs derivative values, which are not always known.", "The degree is high (2n+1), so oscillation can still occur.", "Slopes with measurement errors damage the whole curve."],
    related=["lagrange", "spline", "poly_approx"],
    example_intro="Estimate sin(2.5) from the values AND slopes (cos x) at x = 0, 1, 2, 3, 4.", exact=SIN,
),
"spline": entry(
    what="A natural cubic spline joins the data points with a separate cubic polynomial on every interval, arranged so the whole curve is smooth.",
    why="A single high-degree polynomial through many points wiggles. Splines stay smooth and well-behaved no matter how many points are used.",
    solves="Given points (x₀,y₀)…(xₙ,yₙ), build S(x) that passes through every point and has continuous slope and curvature.",
    uses="Computer-aided design (car bodies, fonts), animation curves, smoothing sensor data, and plotting libraries.",
    explain="On every interval [xᵢ, xᵢ₊₁] use a cubic. The unknowns are the curvatures Mᵢ = S''(xᵢ) at the points. Requiring continuous slope at every inner point gives a tridiagonal linear system for the Mᵢ; natural ends set M₀ = Mₙ = 0. Once the Mᵢ are known each cubic is explicit.",
    formula=r"S_i(x)=\frac{M_i(x_{i+1}-x)^3+M_{i+1}(x-x_i)^3}{6h_i}+\Big(\frac{y_i}{h_i}-\frac{M_ih_i}{6}\Big)(x_{i+1}-x)+\Big(\frac{y_{i+1}}{h_i}-\frac{M_{i+1}h_i}{6}\Big)(x-x_i)",
    variables=[[r"h_i", "interval width x_(i+1) − x_i"], [r"M_i", "second derivative of the spline at x_i"], [r"S_i(x)", "the cubic used on [x_i, x_(i+1)]"]],
    why_works="S_i is cubic, equals y_i and y_(i+1) at the ends (so the curve is continuous), and has second derivative M_i and M_(i+1) at the ends - so S'' is continuous by construction. Matching S' at the inner points gives h₍ᵢ₋₁₎M₍ᵢ₋₁₎ + 2(h₍ᵢ₋₁₎+hᵢ)Mᵢ + hᵢM₍ᵢ₊₁₎ = 6[(yᵢ₊₁−yᵢ)/hᵢ − (yᵢ−yᵢ₋₁)/hᵢ₋₁], a tridiagonal system that always has a unique solution.",
    code=DATA_CODE + '''x = 2.5
n = len(xs)
h = [xs[i + 1] - xs[i] for i in range(n - 1)]      # interval widths

# tridiagonal system for the inner second derivatives M[1] ... M[n-2]
m = n - 2
lower = [0] * m
diag = [0] * m
upper = [0] * m
rhs = [0] * m
for i in range(1, n - 1):
    lower[i - 1] = h[i - 1]
    diag[i - 1] = 2 * (h[i - 1] + h[i])
    upper[i - 1] = h[i]
    rhs[i - 1] = 6 * ((ys[i + 1] - ys[i]) / h[i] - (ys[i] - ys[i - 1]) / h[i - 1])

for i in range(1, m):            # forward elimination (Thomas algorithm)
    factor = lower[i] / diag[i - 1]
    diag[i] = diag[i] - factor * upper[i - 1]
    rhs[i] = rhs[i] - factor * rhs[i - 1]
inner = [0] * m
inner[m - 1] = rhs[m - 1] / diag[m - 1]
for i in range(m - 2, -1, -1):   # back substitution
    inner[i] = (rhs[i] - upper[i] * inner[i + 1]) / diag[i]

M = [0] + inner + [0]            # natural spline: M[0] = M[n-1] = 0

i = 0                            # find the interval that contains x
while i < n - 2 and x > xs[i + 1]:
    i = i + 1
a = xs[i + 1] - x
b = x - xs[i]
S = (M[i] * a**3 + M[i + 1] * b**3) / (6 * h[i]) + (ys[i] / h[i] - M[i] * h[i] / 6) * a + (ys[i + 1] / h[i] - M[i + 1] * h[i] / 6) * b

print("S(2.5) =", S)
''',
    adv=["Smooth (continuous slope and curvature) and does not oscillate.", "Works well for many points; the tridiagonal system is cheap to solve.", "Local changes have mostly local effects."],
    lim=["More complicated to compute by hand.", "Natural end conditions can be inaccurate near the ends.", "Does not use known slope information."],
    related=["lagrange", "hermite", "least_squares"],
    example_intro="Estimate sin(2.5) from five points with a natural cubic spline.", exact=SIN,
),
"poly_approx": entry(
    what="Polynomial approximation replaces a complicated function f(x) on an interval [a, b] by a polynomial that is easy to evaluate, here built with Newton's divided differences.",
    why="Computers can only add and multiply. Polynomials use only those operations, so every function (sin, exp, …) ultimately has to be approximated by polynomials.",
    solves="Given f and an interval, find a polynomial Pₙ(x) with Pₙ ≈ f and estimate how large the error is.",
    uses="Fast function evaluation in calculators and GPUs, simplifying models in engineering, and as the foundation for integration and differentiation formulas.",
    explain="Choose n+1 equally spaced nodes on [a, b], compute f at them, and build the divided-difference table. The Newton form P(x) = f[z₀] + f[z₀,z₁](x−z₀) + … is the same unique polynomial as Lagrange's, but it is cheaper to extend and evaluate.",
    formula=r"P_n(x)=\sum_{k=0}^{n}f[z_0,\dots,z_k]\prod_{i<k}(x-z_i),\qquad f(x)-P_n(x)=\frac{f^{(n+1)}(\xi)}{(n+1)!}\prod_{i=0}^{n}(x-z_i)",
    variables=[[r"z_i", "equally spaced nodes in [a, b]"], [r"f[z_0,\dots,z_k]", "k-th divided difference"], [r"\xi", "an unknown point in (a, b) used in the error formula"]],
    why_works="The divided differences are exactly the coefficients that force P to agree with f at every node. The error formula shows the error is small when f's (n+1)-th derivative is small and the nodes are close together - but it can grow for large n with equally spaced nodes (Runge phenomenon).",
    code='''
import math

def f(x):
    return math.exp(x)

a = 0
b = 2
degree = 3
x = 1.5                          # evaluate the polynomial here
n = degree + 1                   # number of nodes
h = (b - a) / degree

z = [a + i * h for i in range(n)]            # equally spaced nodes
table = [f(t) for t in z]                    # f[z_i]
coef = [table[0]]
for level in range(1, n):                    # build divided differences
    table = [(table[i + 1] - table[i]) / (z[i + level] - z[i]) for i in range(n - level)]
    coef.append(table[0])

result = coef[-1]                            # Horner-style evaluation
for k in range(n - 2, -1, -1):
    result = result * (x - z[k]) + coef[k]

print("P(1.5) =", result)
print("True f(1.5) =", f(1.5))
''',
    adv=["Polynomials are trivial to evaluate, differentiate and integrate.", "An explicit error formula is available.", "Nodes can be added without recomputing earlier coefficients."],
    lim=["Equally spaced nodes with high degree can give large errors near the ends (Runge).", "Needs f to be smooth (many derivatives).", "Accuracy depends on the interval length."],
    related=["lagrange", "spline", "least_squares"],
    example_intro="Approximate eˣ on [0, 2] by a cubic polynomial through 4 equally spaced nodes and evaluate it at x = 1.5.", exact={"label": "True value e^1.5", "value": math.exp(1.5)},
),
"least_squares": entry(
    what="The method of least squares finds the straight line y = mx + c that fits scattered data best by making the total squared error as small as possible.",
    why="Real measurements contain noise, so forcing a curve through every point would copy the noise. A best-fit line captures the trend instead.",
    solves="Given points (xᵢ, yᵢ), find m and c that minimise E = Σ (yᵢ − m·xᵢ − c)².",
    uses="Trend lines in science and economics, calibration of sensors, machine learning (linear regression).",
    explain="E is a smooth function of m and c. At its minimum both partial derivatives are zero. That gives two linear equations - the normal equations - which can be solved directly.",
    formula=r"m=\frac{n\sum x_iy_i-\sum x_i\sum y_i}{n\sum x_i^2-\left(\sum x_i\right)^2},\qquad c=\frac{\sum y_i-m\sum x_i}{n}",
    variables=[[r"n", "number of data points"], [r"\sum x_i,\ \sum y_i", "sums of the data"], [r"\sum x_iy_i,\ \sum x_i^2", "sums of products and squares"], [r"m,\ c", "slope and intercept of the best line"]],
    why_works="Setting ∂E/∂c = 0 gives Σyᵢ = mΣxᵢ + nc and ∂E/∂m = 0 gives Σxᵢyᵢ = mΣxᵢ² + cΣxᵢ. Solving these two equations produces the formulas above. Because E is a convex bowl shape, this single stationary point is the minimum.",
    code='''
xs = [1, 2, 3, 4]
ys = [6, 5, 7, 10]
n = len(xs)

sum_x = 0
sum_y = 0
sum_xy = 0
sum_xx = 0
for i in range(n):               # collect the four sums
    sum_x = sum_x + xs[i]
    sum_y = sum_y + ys[i]
    sum_xy = sum_xy + xs[i] * ys[i]
    sum_xx = sum_xx + xs[i] ** 2

m = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)   # slope
c = (sum_y - m * sum_x) / n                                    # intercept

print("Slope m =", m)
print("Intercept c =", c)
''',
    adv=["Closed-form answer - no iteration.", "Averages out random measurement noise.", "R² tells how good the fit is."],
    lim=["Sensitive to outliers (squared errors punish them heavily).", "Only fits straight lines (use curve fitting for other shapes).", "Assumes errors are in y only."],
    related=["curve_fitting", "lls", "lagrange"],
    example_intro="Fit a line to the points (1,6), (2,5), (3,7), (4,10).", exact={"label": "Exact solution of the normal equations", "value": [1.4, 3.5]},
),
"curve_fitting": entry(
    what="Curve fitting extends least squares to curved models such as polynomials, exponentials and power laws.",
    why="Many real processes are not linear: populations grow exponentially, cooling follows a decaying curve, and so on.",
    solves="Given data and a model type, find the parameters that make the model fit the data in the least-squares sense.",
    uses="Growth and decay modelling, fitting calibration curves, extracting parameters from experiments.",
    explain="For polynomials, build the Vandermonde matrix A with columns 1, x, x², … and solve the normal equations AᵀAc = Aᵀy. For y = a·e^(bx) take logarithms: ln y = ln a + bx is a straight line in (x, ln y), so ordinary least squares applies.",
    formula=r"(A^TA)\,\mathbf{c}=A^T\mathbf{y},\qquad y=ae^{bx}\ \Rightarrow\ \ln y=\ln a+bx",
    variables=[[r"A", "design matrix built from the model (one row per data point)"], [r"\mathbf{c}", "unknown parameters"], [r"\mathbf{y}", "measured values"]],
    why_works="Minimising ‖y − Ac‖² gives the normal equations (the error vector must be perpendicular to every column of A). Linearising by logarithms turns a nonlinear model into a linear one, at the price of minimising the error in ln y instead of y.",
    code='''
import math

xs = [0, 1, 2, 3, 4]
ys = [1.1, 2.9, 8.2, 20.5, 54.0]
n = len(xs)

# model y = a * e^(b x)  ->  ln y = ln a + b x  (a straight line)
ln_y = [math.log(y) for y in ys]

sum_x = sum(xs)
sum_ly = sum(ln_y)
sum_xly = sum(xs[i] * ln_y[i] for i in range(n))
sum_xx = sum(x * x for x in xs)

b = (n * sum_xly - sum_x * sum_ly) / (n * sum_xx - sum_x ** 2)   # slope of the line
ln_a = (sum_ly - b * sum_x) / n                                  # intercept
a = math.exp(ln_a)

print("a =", a)
print("b =", b)
''',
    adv=["Handles many model types.", "Linearisation keeps the mathematics simple.", "R² and residuals show quality of fit."],
    lim=["The model type must be chosen by you.", "Linearised fits are not the same as a true nonlinear least-squares fit.", "High-degree polynomials overfit the noise."],
    related=["least_squares", "lls", "spline"],
    example_intro="Fit y = a·e^(bx) to growth data (0, 1.1), (1, 2.9), (2, 8.2), (3, 20.5), (4, 54.0).",
),
}
