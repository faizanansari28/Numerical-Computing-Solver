from content.helpers import entry

EXACT = {"label": "Exact ∫₀⁴ x² dx = 4³/3 = 64/3", "value": 64 / 3}
HEAD = '''
def f(x):
    return x**2                  # the function to integrate

a = 0                            # lower limit
b = 4                            # upper limit
'''

CONTENT = {
"midpoint": entry(
    what="The midpoint rule approximates the area under a curve by rectangles whose height is the function value at the middle of each subinterval.",
    why="Most integrals have no neat antiderivative (for example ∫e^(−x²)dx). Numerical integration gives the area anyway.",
    solves="Approximates the definite integral of f from a to b.",
    uses="Computing areas, total distance from speed, total energy from power, probability from a density.",
    explain="Cut [a, b] into n equal strips of width h. On each strip pretend the function is constant, equal to its value at the strip's centre. Add the n rectangle areas.",
    formula=r"\int_a^b f(x)\,dx\approx h\sum_{i=1}^{n}f\!\left(a+\left(i-\tfrac12\right)h\right),\qquad h=\frac{b-a}{n}",
    variables=[[r"a,\ b", "integration limits"], [r"n", "number of subintervals"], [r"h", "width of each strip"], [r"x_i=a+(i-\frac12)h", "centre of strip i"]],
    why_works="Taylor expansion about the midpoint shows the error of one strip is f''(ξ)h³/24 - the first-order error terms cancel because the midpoint is symmetric. The total error is therefore about (b − a)h²f''/24: second order, so halving h cuts the error by about 4.",
    code=HEAD + '''n = 4                            # number of rectangles
h = (b - a) / n                  # width of each rectangle

total = 0
for i in range(1, n + 1):
    x = a + (i - 0.5) * h        # middle of strip i
    total = total + f(x)

result = h * total               # width times the sum of heights
print("Integral =", result)
''',
    adv=["Simple and uses no endpoint values.", "More accurate than left/right rectangles (second order).", "Good when f is undefined at an endpoint."],
    lim=["Needs many strips for high accuracy.", "Less accurate than Simpson's rule for smooth functions.", "Error depends on the second derivative."],
    related=["trapezoid", "simpson", "gauss"], example_intro="Integrate f(x) = x² from 0 to 4 with n = 4 rectangles.", exact=EXACT,
),
"trapezoid": entry(
    what="The trapezoidal rule replaces the curve on each subinterval by a straight line and adds up the areas of the resulting trapezoids.",
    why="It is one of the most basic and widely used rules: easy to program, and works even if only tabulated data points are available.",
    solves="Approximates the definite integral of f from a to b.",
    uses="Integrating measured data (speed → distance), area under experimental curves, signal processing.",
    explain="Cut [a, b] into n strips. Over each strip connect the two end points of the curve by a straight line. The shape under that line is a trapezoid with area (h/2)(f(left) + f(right)). Every inner point is used by two neighbouring trapezoids, so it gets weight 2.",
    formula=r"\int_a^b f\,dx\approx\frac h2\Big[f(x_0)+2\sum_{i=1}^{n-1}f(x_i)+f(x_n)\Big],\qquad h=\frac{b-a}{n}",
    variables=[[r"x_i=a+ih", "the n+1 equally spaced points"], [r"h", "strip width"], [r"f(x_0),\ f(x_n)", "values at the two end points (weight 1)"], [r"f(x_i)", "inner values (weight 2)"]],
    why_works="A trapezoid with parallel sides f(xᵢ) and f(xᵢ₊₁) and width h has area h(f(xᵢ) + f(xᵢ₊₁))/2. Adding all of them counts every inner value twice, giving the formula. The error is −(b−a)h²f''(ξ)/12: second order.",
    code=HEAD + '''n = 4                            # number of strips
h = (b - a) / n

total = f(a) + f(b)              # end points have weight 1

for i in range(1, n):
    x = a + i * h
    total += 2 * f(x)            # inner points have weight 2

result = (h / 2) * total
print("Integral =", result)
''',
    adv=["Very simple; works on tabulated data.", "Excellent for periodic functions over a full period.", "Error shrinks like h²."],
    lim=["Overestimates convex functions (and underestimates concave ones).", "Needs many strips for high accuracy.", "Less accurate than Simpson's rule."],
    related=["midpoint", "simpson", "newton_cotes"], example_intro="Integrate f(x) = x² from 0 to 4 with n = 4 trapezoids.", exact=EXACT,
),
"simpson": entry(
    what="Simpson's rule replaces the curve on each PAIR of strips by a parabola through three points and integrates that parabola exactly.",
    why="Parabolas follow a curve much better than straight lines, so Simpson's rule is far more accurate than the trapezoidal rule at the same cost.",
    solves="Approximates the definite integral of f from a to b (n must be even).",
    uses="Engineering calculations, physics simulations, and as a default accurate rule for smooth functions.",
    explain="Take three consecutive points x₀, x₁, x₂ with spacing h. The parabola through them has area (h/3)(f₀ + 4f₁ + f₂). Doing this for every pair of strips and adding gives weights 1, 4, 2, 4, 2, …, 4, 1.",
    formula=r"\int_a^b f\,dx\approx\frac h3\Big[f_0+4\!\!\sum_{i\ \mathrm{odd}}\!\!f_i+2\!\!\sum_{i\ \mathrm{even}}\!\!f_i+f_n\Big]",
    variables=[[r"n", "number of strips - MUST be even"], [r"h=\frac{b-a}{n}", "strip width"], [r"f_i=f(a+ih)", "function values"]],
    why_works="Integrating the interpolating parabola gives (h/3)(f₀+4f₁+f₂). Surprisingly the rule is also exact for cubics, so its error is −(b−a)h⁴f⁽⁴⁾(ξ)/180: fourth order. Halving h cuts the error by about 16.",
    code=HEAD + '''n = 4                            # must be EVEN
h = (b - a) / n

total = f(a) + f(b)              # end points: weight 1
for i in range(1, n):
    x = a + i * h
    if i % 2 == 1:
        total += 4 * f(x)        # odd points: weight 4
    else:
        total += 2 * f(x)        # even inner points: weight 2

result = (h / 3) * total
print("Integral =", result)
''',
    adv=["Fourth-order accuracy.", "Exact for polynomials up to degree 3.", "Same number of evaluations as trapezoid but much more accurate."],
    lim=["Needs an even number of intervals.", "Needs f to be smooth (four derivatives).", "Poor for functions with kinks or singularities."],
    related=["trapezoid", "newton_cotes", "gauss"], example_intro="Integrate f(x) = x² from 0 to 4 with n = 4 (two parabola pieces). Because x² is a polynomial of degree 2, Simpson's rule is exact.", exact=EXACT,
),
"newton_cotes": entry(
    what="Newton-Cotes rules are a family of quadrature formulas obtained by integrating the interpolating polynomial through equally spaced points.",
    why="Trapezoid, Simpson 1/3, Simpson 3/8 and Boole's rule are all members of this one family - understanding it explains where each formula comes from.",
    solves="Approximates ∫f over [a, b] using a weighted sum of function values at equally spaced points.",
    uses="Building blocks of composite integration rules in numerical libraries.",
    explain="Choose degree m, take m+1 equally spaced points, interpolate, and integrate the polynomial. The weights wₖ = ∫Lₖ(x)dx depend only on m. For m = 1, 2, 3, 4 they are (1,1)·h/2, (1,4,1)·h/3, (1,3,3,1)·3h/8 and (7,32,12,32,7)·2h/45.",
    formula=r"\int_a^b f\,dx\approx\sum_{k=0}^{m}w_kf(x_k),\qquad x_k=a+kh,\ h=\tfrac{b-a}{m},\ w_k=\int_a^bL_k(x)\,dx",
    variables=[[r"m", "degree of the rule (number of intervals per panel)"], [r"w_k", "quadrature weights"], [r"x_k", "equally spaced nodes"]],
    why_works="Since the rule integrates the interpolating polynomial of degree m exactly, it is exact for all polynomials of degree ≤ m (and ≤ m+1 when m is even, by symmetry). Higher m is not always better: for large m some weights become negative and rounding errors grow, so in practice we split [a, b] into panels and use a low-degree rule on each.",
    code=HEAD + '''# Boole's rule (degree 4): 5 points, weights 7, 32, 12, 32, 7, factor 2h/45
m = 4
h = (b - a) / m
weights = [7, 32, 12, 32, 7]

total = 0
for k in range(m + 1):
    x = a + k * h
    total = total + weights[k] * f(x)

result = (2 * h / 45) * total
print("Integral =", result)
''',
    adv=["One unified idea behind many classic rules.", "Easy to apply to tabulated, equally spaced data.", "Composite versions give very good accuracy."],
    lim=["Needs equally spaced nodes.", "High-degree rules have negative weights and are unstable.", "Gaussian quadrature is more accurate for the same number of evaluations."],
    related=["trapezoid", "simpson", "gauss"], example_intro="Integrate x² from 0 to 4 with Boole's rule (degree 4, one panel). It is exact for polynomials up to degree 5.", exact=EXACT,
),
"gauss": entry(
    what="Gaussian quadrature chooses BOTH the evaluation points and the weights cleverly, so that n points integrate every polynomial up to degree 2n − 1 exactly.",
    why="With the same number of function evaluations it is far more accurate than Newton-Cotes rules, which matters when f is expensive to evaluate.",
    solves="Approximates ∫f from a to b using n well-chosen points.",
    uses="Finite element software, physics and engineering simulations, any place where an integrand is costly to evaluate.",
    explain="On [−1, 1] the best nodes are the roots of the Legendre polynomial Pₙ and the weights are wᵢ = 2/((1 − tᵢ²)[Pₙ'(tᵢ)]²). To integrate on [a, b] map the nodes with x = (b−a)/2·t + (a+b)/2 and multiply the sum by (b−a)/2.",
    formula=r"\int_a^b f\,dx\approx\frac{b-a}{2}\sum_{i=1}^{n}w_i\,f\!\Big(\tfrac{b-a}{2}t_i+\tfrac{a+b}{2}\Big),\quad P_n(t_i)=0,\ \ w_i=\frac{2}{(1-t_i^2)\,[P_n'(t_i)]^2}",
    variables=[[r"t_i", "Gauss nodes = roots of the Legendre polynomial P_n"], [r"w_i", "Gauss weights (they add up to 2)"], [r"x_i", "nodes mapped from [-1, 1] to [a, b]"]],
    why_works="2n free numbers (n nodes and n weights) can satisfy 2n conditions: exactness for 1, x, x², …, x^(2n−1). Orthogonality of Legendre polynomials shows the nodes must be the roots of Pₙ. A degree-(2n−1) polynomial divided by Pₙ leaves a quotient and remainder of degree < n, and the quotient integrates to 0 against Pₙ.",
    code='''
import math

def f(x):
    return x**2

a = 0
b = 4
# 3-point Gauss-Legendre: roots of P3 and their weights
t = [-math.sqrt(3 / 5), 0, math.sqrt(3 / 5)]
w = [5 / 9, 8 / 9, 5 / 9]

half = (b - a) / 2               # scale factor for the interval
middle = (b + a) / 2             # shift to the middle of [a, b]

total = 0
for i in range(3):
    x = half * t[i] + middle     # map node from [-1, 1] to [a, b]
    total = total + w[i] * f(x)

result = half * total
print("Integral =", result)
''',
    adv=["Highest possible accuracy per function evaluation.", "Exact for polynomials up to degree 2n − 1.", "Excellent for smooth integrands."],
    lim=["Nodes are not equally spaced, so it cannot reuse earlier points or tabulated data.", "Nodes and weights must be computed or tabulated.", "Not suited to non-smooth integrands without splitting the interval."],
    related=["legendre", "simpson", "newton_cotes"], example_intro="Integrate x² from 0 to 4 with n = 3 Gauss points (exact up to degree 5).", exact=EXACT, example={"npts": "3"},
),
"legendre": entry(
    what="Legendre polynomials P₀, P₁, P₂, … are a special family of polynomials that are orthogonal on [−1, 1].",
    why="Their roots are exactly the nodes of Gaussian quadrature, and they are the basis of many approximation methods.",
    solves="Generates Pₙ(x), shows its roots and checks the orthogonality property.",
    uses="Gaussian quadrature, spectral methods for differential equations, solving potential problems in physics.",
    explain="Start with P₀ = 1 and P₁ = x. All later polynomials follow from a three-term recurrence. Two different Legendre polynomials have zero 'overlap' integral over [−1, 1], while the overlap of Pₙ with itself is 2/(2n+1).",
    formula=r"(k+1)P_{k+1}(x)=(2k+1)\,x\,P_k(x)-k\,P_{k-1}(x),\qquad \int_{-1}^{1}P_mP_n\,dx=\begin{cases}0&m\ne n\\ \frac{2}{2n+1}&m=n\end{cases}",
    variables=[[r"P_k(x)", "Legendre polynomial of degree k"], [r"x", "point in [−1, 1]"], [r"\delta_{mn}", "orthogonality: zero unless m = n"]],
    why_works="Legendre polynomials come from applying Gram-Schmidt orthogonalisation to 1, x, x², … with the inner product ⟨f,g⟩ = ∫₋₁¹ f g dx. The recurrence follows from that orthogonality, and Pₙ has n distinct real roots in (−1, 1).",
    code='''
n = 4                            # degree wanted
x = 0.5                          # evaluate at this point

p_old = 1                        # P0(x) = 1
p_now = x                        # P1(x) = x
for k in range(1, n):
    p_new = ((2 * k + 1) * x * p_now - k * p_old) / (k + 1)   # recurrence
    p_old = p_now
    p_now = p_new

print("P4(0.5) =", p_now)
''',
    adv=["Cheap, stable three-term recurrence.", "Orthogonality makes least-squares problems easy.", "Roots give optimal quadrature nodes."],
    lim=["Defined naturally only on [−1, 1] (other intervals need a change of variable).", "Not directly an integration method by itself."],
    related=["gauss", "newton_cotes", "poly_approx"], example_intro="Evaluate P₄(0.5), list the roots of P₄ and verify orthogonality. Since P₄(x) = (35x⁴ − 30x² + 3)/8, P₄(0.5) = −0.2890625.", exact={"label": "Exact P₄(0.5) = (35·0.0625 − 30·0.25 + 3)/8", "value": -0.2890625},
),
}
