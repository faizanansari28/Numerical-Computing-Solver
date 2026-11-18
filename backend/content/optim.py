from content.helpers import entry

MIN = {"label": "Exact minimiser (16/7, −18/7)", "value": [16 / 7, -18 / 7]}
FUNC = '''
def f(x, y):
    return (x - 1)**2 + 2 * (y + 2)**2 + x * y
'''

CONTENT = {
"gradient": entry(
    what="Gradient descent minimises a function by repeatedly stepping in the direction in which it decreases fastest - the negative gradient.",
    why="Many problems (fitting models, designing structures, training neural networks) are 'find the inputs that make this quantity smallest'.",
    solves="Finds a local minimum of f(x, y) starting from an initial point.",
    uses="Machine learning, parameter estimation, engineering design optimisation.",
    explain="The gradient ∇f points uphill, so −∇f points downhill. Take a step of size α in that direction and repeat. Stop when the gradient is almost zero, because the slope is zero at a minimum.",
    formula=r"\mathbf{x}_{k+1}=\mathbf{x}_k-\alpha\,\nabla f(\mathbf{x}_k)",
    variables=[[r"\mathbf{x}_k", "current point (x, y)"], [r"\nabla f", "gradient: the vector of partial derivatives"], [r"\alpha", "step size (learning rate)"]],
    why_works="For small α, f(x − α∇f) ≈ f(x) − α‖∇f‖², which is smaller than f(x). So every step lowers f. A step that is too big overshoots and can diverge; for a quadratic with Hessian eigenvalues between λ_min and λ_max the method converges if α < 2/λ_max.",
    code=FUNC + '''
def gradient(x, y):
    return [2 * (x - 1) + y, 4 * (y + 2) + x]        # [df/dx, df/dy]

x = 0
y = 0
alpha = 0.1                                  # step size
tol = 1e-8

for k in range(500):
    gx, gy = gradient(x, y)
    size = (gx**2 + gy**2) ** 0.5            # length of the gradient
    if size < tol:                           # flat -> we are at the minimum
        break
    x = x - alpha * gx                       # walk downhill
    y = y - alpha * gy

print("Minimiser =", [x, y])
print("f =", f(x, y))
''',
    adv=["Simple and works for any number of variables.", "Only needs first derivatives.", "Cheap per iteration."],
    lim=["Can be slow, especially in narrow valleys (zig-zagging).", "The step size must be tuned (too large diverges).", "Finds only a local minimum."],
    related=["cg", "newton_opt", "newton"], example_intro="Minimise f(x, y) = (x−1)² + 2(y+2)² + xy from (0, 0) using α = 0.1. The exact minimiser solves 2(x−1)+y = 0, 4(y+2)+x = 0, i.e. (16/7, −18/7).", exact=MIN,
),
"cg": entry(
    what="The conjugate gradient method minimises a quadratic function ½xᵀAx − bᵀx (equivalently solves Ax = b for symmetric positive definite A) using smartly chosen search directions.",
    why="It converges in at most n steps for an n-variable quadratic, far faster than plain gradient descent, and needs only matrix-vector products.",
    solves="Finds x with Ax = b, A symmetric positive definite.",
    uses="Large sparse systems from finite elements and physics simulations, and the basis of many optimisation algorithms.",
    explain="Start going downhill (the residual direction). After each step choose the next direction as the new residual plus a multiple of the previous direction, so that the directions are 'conjugate': dᵢᵀAdⱼ = 0. Minimising along conjugate directions never undoes earlier progress.",
    formula=r"\alpha_k=\frac{r_k^Tr_k}{d_k^TAd_k},\ x_{k+1}=x_k+\alpha_kd_k,\ r_{k+1}=r_k-\alpha_kAd_k,\ \beta_k=\frac{r_{k+1}^Tr_{k+1}}{r_k^Tr_k},\ d_{k+1}=r_{k+1}+\beta_kd_k",
    variables=[[r"r_k=b-Ax_k", "residual (= minus the gradient)"], [r"d_k", "search direction"], [r"\alpha_k", "exact step length along d_k"], [r"\beta_k", "mixing factor for the new direction"]],
    why_works="The directions d_k are A-conjugate, so minimising along each in turn gives the exact minimum over the growing subspace span{d₀,…,d_k}. After n steps this subspace is the whole space, so (in exact arithmetic) x_n is the exact solution.",
    code='''
A = [[4, 1], [1, 3]]
b = [1, 2]
x = [0, 0]
n = 2

def matvec(M, v):
    return [sum(M[i][j] * v[j] for j in range(n)) for i in range(n)]

def dot(u, v):
    return sum(u[i] * v[i] for i in range(n))

r = [b[i] - matvec(A, x)[i] for i in range(n)]       # residual
d = r[:]                                             # first direction
for k in range(n):                                   # n steps are enough
    Ad = matvec(A, d)
    alpha = dot(r, r) / dot(d, Ad)                   # exact step length
    x = [x[i] + alpha * d[i] for i in range(n)]
    r_new = [r[i] - alpha * Ad[i] for i in range(n)]
    beta = dot(r_new, r_new) / dot(r, r)
    d = [r_new[i] + beta * d[i] for i in range(n)]   # new conjugate direction
    r = r_new

print("Solution x =", x)
''',
    adv=["Finishes in at most n steps (exact arithmetic).", "Only matrix-vector products - ideal for sparse matrices.", "No step size to tune."],
    lim=["Only for symmetric positive definite matrices.", "Rounding errors can lose conjugacy; preconditioning helps for ill-conditioned problems."],
    related=["gradient", "iterative", "newton_opt"], example_intro="Minimise ½xᵀAx − bᵀx with A = [[4,1],[1,3]], b = (1, 2). CG needs only 2 iterations; the answer is (1/11, 7/11).", exact={"label": "Exact solution (1/11, 7/11)", "value": [1 / 11, 7 / 11]},
),
"newton_opt": entry(
    what="Newton's method for optimisation uses both the gradient and the Hessian (second derivatives) to jump directly to the minimum of a local quadratic model.",
    why="It converges quadratically near a minimum, needing far fewer iterations than gradient descent.",
    solves="Finds a critical point (∇f = 0) of f(x, y).",
    uses="Fast optimisation in engineering and statistics (maximum-likelihood estimation).",
    explain="Approximate f near the current point by a quadratic (second-order Taylor expansion). The minimum of that quadratic is at p = −H⁻¹∇f, where H is the Hessian matrix. Move there and repeat. In practice solve Hp = −∇f instead of inverting H.",
    formula=r"H(\mathbf{x}_k)\,\mathbf{p}_k=-\nabla f(\mathbf{x}_k),\qquad \mathbf{x}_{k+1}=\mathbf{x}_k+\mathbf{p}_k,\qquad H=\begin{pmatrix}f_{xx}&f_{xy}\\f_{xy}&f_{yy}\end{pmatrix}",
    variables=[[r"\nabla f", "gradient vector"], [r"H", "Hessian matrix of second derivatives"], [r"\mathbf{p}_k", "Newton step"]],
    why_works="Newton's method for root finding applied to the equation ∇f = 0 gives exactly x − H⁻¹∇f. For a quadratic function the Taylor model is exact, so one step lands on the minimum. Near a minimum with positive definite H the error is squared at each step.",
    code=FUNC + '''
x = 0
y = 0

for k in range(20):
    gx = 2 * (x - 1) + y                     # gradient
    gy = 4 * (y + 2) + x
    if (gx**2 + gy**2) ** 0.5 < 1e-8:
        break
    hxx, hxy, hyy = 2, 1, 4                  # Hessian (constant for this f)
    det = hxx * hyy - hxy * hxy
    px = (-gx * hyy + gy * hxy) / det        # solve H p = -gradient (2x2)
    py = (-gy * hxx + gx * hxy) / det
    x = x + px
    y = y + py

print("Minimiser =", [x, y])
''',
    adv=["Quadratic convergence near the solution.", "Takes curvature into account, so no step size is needed.", "Exact in one step for quadratics."],
    lim=["Needs second derivatives (expensive for many variables).", "Hessian must be positive definite - otherwise the step may go uphill.", "Can diverge from a bad starting point."],
    related=["gradient", "cg", "newton"], example_intro="Minimise the same f(x, y) = (x−1)² + 2(y+2)² + xy. Because f is quadratic, Newton's method finds the exact minimiser (16/7, −18/7) in one step.", exact=MIN,
),
"eigen": entry(
    what="The power method approximates the dominant eigenvalue (largest in absolute value) and its eigenvector by repeatedly multiplying a vector by A.",
    why="Eigenvalues describe vibration frequencies, stability, principal directions and the long-term behaviour of systems. Computing them directly is hard for large matrices; the power method needs only matrix-vector products.",
    solves="Finds λ and x with Ax = λx. Variants find the smallest eigenvalue (inverse power) or the one nearest a chosen shift (shifted inverse power).",
    uses="Google's PageRank, vibration analysis of structures, population models, principal component analysis.",
    explain="Almost any starting vector is a mix of eigenvectors. Each multiplication by A stretches the component of the dominant eigenvector more than the others, so after many steps the vector points along the dominant eigenvector. Normalise each step to avoid overflow and estimate λ with the Rayleigh quotient xᵀAx/xᵀx.",
    formula=r"x_{k+1}=\frac{A\,x_k}{\|A\,x_k\|_\infty},\qquad \lambda\approx\frac{x^TAx}{x^Tx}",
    variables=[[r"x_k", "current vector estimate"], [r"\lambda", "eigenvalue estimate (Rayleigh quotient)"], [r"|\lambda_2/\lambda_1|", "convergence rate"]],
    why_works="Write x₀ = c₁v₁ + c₂v₂ + …. Then Aᵏx₀ = c₁λ₁ᵏv₁ + c₂λ₂ᵏv₂ + … = λ₁ᵏ(c₁v₁ + c₂(λ₂/λ₁)ᵏv₂ + …). If |λ₁| > |λ₂| the other terms die out like |λ₂/λ₁|ᵏ. Applying the same idea to A⁻¹ (solving a linear system each step) finds the smallest eigenvalue, and to (A − μI)⁻¹ the eigenvalue nearest μ.",
    code='''
A = [[4, 1], [2, 3]]
x = [1, 1]                                   # starting vector
tol = 1e-10
lam_old = None

for k in range(1, 501):
    y = [A[0][0] * x[0] + A[0][1] * x[1],    # y = A x
         A[1][0] * x[0] + A[1][1] * x[1]]
    big = max(y, key=abs)                    # largest entry (in size)
    x = [y[0] / big, y[1] / big]             # scale so the largest entry is 1
    Ax = [A[0][0] * x[0] + A[0][1] * x[1],
          A[1][0] * x[0] + A[1][1] * x[1]]
    lam = (x[0] * Ax[0] + x[1] * Ax[1]) / (x[0] ** 2 + x[1] ** 2)   # Rayleigh quotient
    if lam_old is not None and abs(lam - lam_old) < tol:
        break
    lam_old = lam

print("Dominant eigenvalue =", lam)
print("Eigenvector =", x)
''',
    adv=["Only matrix-vector products - cheap and simple.", "Works for huge sparse matrices.", "Shifts and inverse iteration find other eigenvalues."],
    lim=["Finds only one eigenvalue at a time.", "Slow if |λ₂| ≈ |λ₁|.", "Fails if the dominant eigenvalues are complex or equal in magnitude."],
    related=["svd", "cg", "newton_opt"], example_intro="Find the dominant eigenvalue of A = [[4,1],[2,3]] (the exact eigenvalues are 5 and 2).", exact={"label": "Exact dominant eigenvalue", "value": 5},
),
}
