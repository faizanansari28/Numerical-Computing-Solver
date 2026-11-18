import math
from content.helpers import entry

ODE_EXACT = {"label": "Exact y(2) = (2+1)² − ½e²", "value": 9 - 0.5 * math.e ** 2}
ODE_HEAD = '''
def f(t, y):
    return y - t**2 + 1          # the differential equation y' = f(t, y)

t = 0                            # start time
y = 0.5                          # initial value y(0)
h = 0.2                          # step size
steps = 10                       # 10 steps of 0.2 reach t = 2
'''

CONTENT = {
"numdiff": entry(
    what="Numerical differentiation estimates the derivative of a function from its values at nearby points, using difference quotients.",
    why="Sometimes we only have data or a program for f(x), not a formula for f'(x). We still need slopes - for velocity from positions, for example.",
    solves="Approximates f'(x) (or f''(x)) at a point x using a small step size h.",
    uses="Velocity and acceleration from measured positions, gradient calculations in optimisation, finite-difference methods for differential equations.",
    explain="The derivative is the limit of (f(x+h) − f(x))/h as h → 0. Using a small but finite h gives the forward difference. Using points on both sides gives the more accurate central difference. Combining more points (five-point formula) cancels more error terms.",
    formula=r"f'(x)\approx\frac{f(x+h)-f(x-h)}{2h}\ \ (O(h^2)),\qquad f''(x)\approx\frac{f(x+h)-2f(x)+f(x-h)}{h^2}",
    variables=[[r"h", "step size (small)"], [r"f(x\pm h)", "function values on either side of x"], [r"O(h^p)", "the error shrinks like h^p"]],
    why_works="Taylor: f(x±h) = f ± hf' + h²f''/2 ± h³f'''/6 + …. Subtracting the two cancels the f and f'' terms, leaving 2hf' + O(h³), so the central difference has error ~h²f'''/6. There is a trade-off: very small h gives large rounding errors because we subtract two nearly equal numbers.",
    code='''
import math

def f(x):
    return math.sin(x)

x = 1
h = 0.1

forward = (f(x + h) - f(x)) / h                  # error ~ h
central = (f(x + h) - f(x - h)) / (2 * h)        # error ~ h^2

print("Forward difference =", forward)
print("Central difference =", central)
print("Exact cos(1) =", math.cos(x))
''',
    adv=["Needs only function values.", "Higher-order formulas give excellent accuracy.", "Easy to implement."],
    lim=["Too small h amplifies rounding errors.", "Too large h gives truncation error.", "Noisy data makes derivatives very unreliable."],
    related=["euler", "rk4", "newton_opt"], example_intro="Approximate f'(1) for f(x) = sin x with h = 0.1 using the central difference. The exact value is cos 1 ≈ 0.5403.", exact={"label": "Exact f'(1) = cos 1", "value": math.cos(1)},
),
"euler": entry(
    what="Euler's method solves a differential equation y' = f(t, y) by taking small steps along the tangent line.",
    why="Most differential equations cannot be solved with formulas. Euler's method is the simplest way to follow the solution numerically.",
    solves="Given y' = f(t, y) and y(t₀) = y₀, it approximates y at t₀ + h, t₀ + 2h, ….",
    uses="Simulation of motion, population growth, cooling, electric circuits.",
    explain="At the current point (tᵢ, yᵢ) the slope of the solution is f(tᵢ, yᵢ). Walk a distance h along that slope: yᵢ₊₁ = yᵢ + h·f(tᵢ, yᵢ). Repeat from the new point.",
    formula=r"y_{i+1}=y_i+h\,f(t_i,y_i),\qquad t_{i+1}=t_i+h",
    variables=[[r"t_i,\ y_i", "current time and value"], [r"h", "step size"], [r"f(t_i,y_i)", "slope at the current point"]],
    why_works="It is the first two terms of the Taylor series y(t+h) = y + hy' + h²y''/2 + …. The dropped term makes the error per step O(h²) and the total error at a fixed final time O(h): first order, so halving h halves the error.",
    code=ODE_HEAD + '''
for i in range(steps):
    slope = f(t, y)              # slope at the current point
    y = y + h * slope            # walk along the tangent
    t = t + h

print("y(2) =", y)
''',
    adv=["Very simple.", "Good first method for understanding ODE solvers."],
    lim=["Only first order - needs very small h.", "Can be unstable for stiff equations.", "Errors accumulate steadily."],
    related=["rk2", "rk4", "numdiff"], example_intro="Solve y' = y − t² + 1, y(0) = 0.5 up to t = 2 with h = 0.2. The exact solution is y = (t+1)² − 0.5eᵗ.", exact=ODE_EXACT,
),
"rk2": entry(
    what="The second-order Runge-Kutta method (Heun's) improves Euler's method by averaging the slope at the start and the slope at the predicted end of each step.",
    why="Euler uses only the slope at the beginning of the step, which is wrong when the solution curves. Averaging two slopes gives second-order accuracy.",
    solves="Approximates the solution of y' = f(t, y) with error proportional to h².",
    uses="Simulation where moderate accuracy is needed cheaply.",
    explain="First do an Euler step to predict the end point and compute the slope k₂ there. Then use the average of k₁ (slope at the start) and k₂ (slope at the predicted end) for the real step.",
    formula=r"k_1=f(t_i,y_i),\quad k_2=f(t_i+h,\,y_i+hk_1),\quad y_{i+1}=y_i+\frac h2(k_1+k_2)",
    variables=[[r"k_1", "slope at the start of the step"], [r"k_2", "slope at the predicted end point"], [r"h", "step size"]],
    why_works="This is the trapezoidal rule applied to ∫f dt over the step, with the unknown end value predicted by Euler. Matching the Taylor series of the true solution up to the h² term shows the local error is O(h³), global error O(h²).",
    code=ODE_HEAD + '''
for i in range(steps):
    k1 = f(t, y)                         # slope at the start
    k2 = f(t + h, y + h * k1)            # slope at the predicted end
    y = y + h / 2 * (k1 + k2)            # average of the two slopes
    t = t + h

print("y(2) =", y)
''',
    adv=["Second-order accuracy for only two evaluations per step.", "Easy to program."],
    lim=["Still needs small h for high accuracy.", "RK4 is usually better value."],
    related=["euler", "rk4", "trapezoid"], example_intro="Solve y' = y − t² + 1, y(0) = 0.5 up to t = 2 with h = 0.2 using Heun's RK2.", exact=ODE_EXACT,
),
"rk4": entry(
    what="The classical fourth-order Runge-Kutta method takes a weighted average of four slopes per step and is the standard general-purpose ODE solver.",
    why="It achieves high accuracy (error ∝ h⁴) with reasonably large steps and without computing any derivatives of f.",
    solves="Approximates the solution of y' = f(t, y), y(t₀) = y₀.",
    uses="Physics simulations, orbit calculations, control systems, games.",
    explain="Compute four slopes: k₁ at the start, k₂ and k₃ at the midpoint (using two different predictions), and k₄ at the end. Combine them with Simpson-like weights 1, 2, 2, 1.",
    formula=r"y_{i+1}=y_i+\frac h6\,(k_1+2k_2+2k_3+k_4),\quad k_1=f(t_i,y_i),\ k_2=f\!\left(t_i+\tfrac h2,y_i+\tfrac h2k_1\right),\ k_3=f\!\left(t_i+\tfrac h2,y_i+\tfrac h2k_2\right),\ k_4=f(t_i+h,y_i+hk_3)",
    variables=[[r"k_1,\dots,k_4", "four slope estimates"], [r"h", "step size"], [r"\tfrac16(1,2,2,1)", "weights, like Simpson's rule"]],
    why_works="The combination is chosen so that the Taylor expansion of y_{i+1} agrees with that of the exact solution up to the h⁴ term. The local error is O(h⁵) and the global error O(h⁴): halving h divides the error by 16.",
    code=ODE_HEAD + '''
for i in range(steps):
    k1 = f(t, y)
    k2 = f(t + h / 2, y + h / 2 * k1)
    k3 = f(t + h / 2, y + h / 2 * k2)
    k4 = f(t + h, y + h * k3)
    y = y + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)   # weighted average
    t = t + h

print("y(2) =", y)
''',
    adv=["Fourth-order accuracy.", "No derivatives of f needed.", "Self-starting and robust."],
    lim=["Four function evaluations per step.", "Fixed step size cannot adapt to difficult regions.", "Not ideal for stiff problems."],
    related=["rk2", "euler", "simpson"], example_intro="Solve y' = y − t² + 1, y(0) = 0.5 up to t = 2 with h = 0.2 using RK4; compare the error with Euler's.", exact=ODE_EXACT,
),
}
