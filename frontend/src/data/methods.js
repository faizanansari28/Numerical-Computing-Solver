// The method archive. `id` values must match the ids used by the Python backend.
export const CATEGORIES = [
  { id: "root", name: "Root Finding", short: "Roots", blurb: "Solve f(x) = 0" },
  { id: "interp", name: "Interpolation & Curve Fitting", short: "Interpolation", blurb: "Curves through or near data" },
  { id: "integration", name: "Numerical Integration", short: "Integration", blurb: "Areas under curves" },
  { id: "diffode", name: "Differentiation & ODEs", short: "Derivatives & ODEs", blurb: "Slopes and changing systems" },
  { id: "linalg", name: "Numerical Linear Algebra", short: "Linear Algebra", blurb: "Systems, factorizations, conditioning" },
  { id: "approx", name: "Best Approximation", short: "Approximation", blurb: "Least squares, QR and SVD" },
  { id: "optim", name: "Optimization & Eigenvalues", short: "Optimization", blurb: "Minima and eigenpairs" },
  { id: "arith", name: "Computer Arithmetic & Errors", short: "Arithmetic", blurb: "How computers store numbers" },
];

const m = (id, name, cat, blurb) => ({ id, name, cat, blurb });

export const METHODS = [
  m("bisection", "Bisection Method", "root", "Halve a bracketing interval again and again until the root is trapped."),
  m("fixed_point", "Fixed-Point Iteration", "root", "Rewrite f(x)=0 as x=g(x) and iterate until the value settles."),
  m("newton", "Newton-Raphson Method", "root", "Follow tangent lines to the axis - the digits double each step."),
  m("secant", "Secant Method", "root", "Newton's speed without derivatives, using the line through two points."),
  m("lagrange", "Lagrange Interpolation", "interp", "The unique polynomial through every data point, built from basis polynomials."),
  m("hermite", "Hermite Interpolation", "interp", "Interpolate values AND slopes for a smoother, tighter curve."),
  m("spline", "Spline Interpolation", "interp", "Smooth piecewise cubics that never wiggle wildly."),
  m("poly_approx", "Polynomial Approximation", "interp", "Replace a complicated function by a polynomial and measure the error."),
  m("least_squares", "Method of Least Squares", "interp", "The best straight line through noisy data."),
  m("curve_fitting", "Curve Fitting", "interp", "Fit polynomial, exponential, power and logarithmic models."),
  m("midpoint", "Midpoint Rule", "integration", "Rectangles measured at the centre of every strip."),
  m("trapezoid", "Trapezoidal Rule", "integration", "Straight-line tops: add up trapezoids under the curve."),
  m("simpson", "Simpson's Rule", "integration", "Parabolic arcs give fourth-order accuracy."),
  m("newton_cotes", "Newton-Cotes Quadrature", "integration", "The family of rules from integrating interpolating polynomials."),
  m("gauss", "Gaussian Quadrature", "integration", "Cleverly chosen nodes: n points, exact to degree 2n-1."),
  m("legendre", "Legendre Polynomials", "integration", "The orthogonal polynomials whose roots power Gaussian quadrature."),
  m("numdiff", "Numerical Differentiation", "diffode", "Estimate slopes from function values with difference quotients."),
  m("euler", "Euler's Method", "diffode", "Step along the tangent line to solve y' = f(t, y)."),
  m("rk2", "Runge-Kutta 2", "diffode", "Average two slopes per step for second-order accuracy."),
  m("rk4", "Runge-Kutta 4", "diffode", "The classic four-slope method with fourth-order accuracy."),
  m("gauss_elim", "Gaussian Elimination", "linalg", "Reduce Ax = b to a triangular system and back-substitute."),
  m("pivoting", "Pivoting Strategies", "linalg", "Swap rows so tiny pivots can't destroy accuracy."),
  m("lu", "LU Factorization", "linalg", "Factor A = LU once, solve for any right-hand side cheaply."),
  m("cholesky", "Cholesky Factorization", "linalg", "A = LLᵀ for symmetric positive definite matrices."),
  m("inverse", "Matrix Inversion", "linalg", "Gauss-Jordan elimination on [A | I] produces A⁻¹."),
  m("iterative", "Iterative Methods", "linalg", "Jacobi and Gauss-Seidel: improve a guess until Ax = b holds."),
  m("conditioning", "Matrix Conditioning", "linalg", "See how tiny input changes explode into big output changes."),
  m("cond_number", "Condition Number", "linalg", "κ(A) = ‖A‖‖A⁻¹‖ predicts the digits you will lose."),
  m("lls", "Linear Least Squares", "approx", "Solve over-determined systems with the normal equations."),
  m("gram_schmidt", "Gram-Schmidt Orthonormalization", "approx", "Turn independent vectors into an orthonormal basis."),
  m("qr", "QR Factorization", "approx", "Orthogonal Q and triangular R via Householder reflections."),
  m("svd", "Singular Value Decomposition", "approx", "A = UΣVᵀ reveals rank, conditioning and best approximations."),
  m("gradient", "Gradient Methods", "optim", "Walk downhill along the negative gradient to a minimum."),
  m("cg", "Conjugate Gradient Method", "optim", "Conjugate directions solve an n-variable quadratic in n steps."),
  m("newton_opt", "Newton's Method in Optimization", "optim", "Use the Hessian to jump straight to the minimum."),
  m("eigen", "Eigenvalue Approximation", "optim", "Power and inverse iteration find eigenvalues and eigenvectors."),
  m("float_repr", "Floating-Point Representation", "arith", "Sign, exponent and fraction: the 64 bits behind every real number."),
  m("rounding", "Rounding and Truncation", "arith", "Chopping versus rounding and their error bounds."),
  m("machine_eps", "Machine Precision", "arith", "The smallest gap above 1 that a computer can see."),
  m("error_analysis", "Numerical Error Analysis", "arith", "Absolute, relative and truncation error explained."),
];

export const byId = Object.fromEntries(METHODS.map((x) => [x.id, x]));
export const catById = Object.fromEntries(CATEGORIES.map((c) => [c.id, c]));
export const indexOfMethod = (id) => METHODS.findIndex((x) => x.id === id);
