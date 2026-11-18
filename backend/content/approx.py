from content.helpers import entry

LS = {"label": "Exact least-squares solution (normal equations)", "value": [3.5, 1.4]}
DATA = '''
A = [[1, 1], [1, 2], [1, 3], [1, 4]]         # first column of 1s -> intercept
b = [6, 5, 7, 10]
'''

CONTENT = {
"lls": entry(
    what="Linear least squares finds the vector x that makes Ax as close as possible to b when the system has more equations than unknowns.",
    why="Measurement problems give many more equations than unknowns, and no x satisfies them all exactly. We want the best compromise.",
    solves="Minimises ‖b − Ax‖₂ for a tall matrix A (more rows than columns).",
    uses="Linear regression, fitting models to experimental data, calibration, GPS position estimation.",
    explain="Geometrically Ax lies in the column space of A, and the closest point to b in that space is its orthogonal projection. The leftover error b − Ax must therefore be perpendicular to every column of A, i.e. Aᵀ(b − Ax) = 0. That is the normal equation AᵀAx = Aᵀb.",
    formula=r"\min_x\|b-Ax\|_2\ \Longleftrightarrow\ A^TAx=A^Tb",
    variables=[[r"A", "m×n matrix (m > n)"], [r"b", "right-hand side with m entries"], [r"r=b-Ax", "residual vector"], [r"A^TA", "small n×n symmetric matrix"]],
    why_works="Expanding ‖b − Ax‖² and setting its gradient 2Aᵀ(Ax − b) to zero gives the normal equations. If the columns of A are independent, AᵀA is positive definite, so the solution is unique and is the minimum.",
    code=DATA + '''m = 4

# build A^T A (2x2) and A^T b
s11 = s12 = s22 = 0
t1 = t2 = 0
for i in range(m):
    s11 = s11 + A[i][0] * A[i][0]
    s12 = s12 + A[i][0] * A[i][1]
    s22 = s22 + A[i][1] * A[i][1]
    t1 = t1 + A[i][0] * b[i]
    t2 = t2 + A[i][1] * b[i]

det = s11 * s22 - s12 * s12                  # solve the 2x2 normal equations
x1 = (t1 * s22 - s12 * t2) / det
x2 = (s11 * t2 - s12 * t1) / det
print("Least-squares solution =", [x1, x2])
''',
    adv=["Handles over-determined, noisy data.", "A unique best answer exists when the columns are independent.", "Direct formula (normal equations)."],
    lim=["Forming AᵀA squares the condition number - use QR for accuracy.", "Sensitive to outliers.", "Needs independent columns."],
    related=["qr", "least_squares", "svd"], example_intro="Fit the line y = x₁ + x₂·t to (1,6), (2,5), (3,7), (4,10): four equations, two unknowns.", exact=LS,
),
"gram_schmidt": entry(
    what="Gram-Schmidt orthonormalization converts a set of independent vectors into a set of perpendicular vectors of length 1 that span the same space.",
    why="Orthonormal vectors make projections and least-squares problems trivial and numerically very stable.",
    solves="Given the columns a₁,…,aₙ of A, produces orthonormal columns q₁,…,qₙ (and the factor R with A = QR).",
    uses="QR factorization, least squares, building orthogonal bases in signal processing and quantum mechanics.",
    explain="Take the first vector and scale it to length 1. For each next vector subtract its projections onto all earlier q's - what remains is perpendicular to them - then scale it to length 1.",
    formula=r"v_j=a_j-\sum_{i<j}(q_i^Ta_j)\,q_i,\qquad q_j=\frac{v_j}{\|v_j\|},\qquad r_{ij}=q_i^Ta_j,\ \ r_{jj}=\|v_j\|",
    variables=[[r"a_j", "j-th column of A"], [r"q_j", "j-th orthonormal vector"], [r"r_{ij}", "projection coefficients, forming R"]],
    why_works="Subtracting the projection (qᵢᵀa)qᵢ removes exactly the component of a along qᵢ, leaving a vector orthogonal to qᵢ. Since each qᵢ was already orthogonal to the earlier ones, orthogonality is preserved. The modified version projects the already-updated vector, which is far more stable in floating-point arithmetic.",
    code='''
A = [[1, 1, 0], [1, 0, 1], [0, 1, 1]]
n = 3
cols = [[A[i][j] for i in range(n)] for j in range(n)]   # the columns of A

Q = []                                       # orthonormal vectors found so far
for j in range(n):
    v = cols[j][:]
    for i in range(j):
        r = sum(Q[i][k] * v[k] for k in range(n))        # projection coefficient
        v = [v[k] - r * Q[i][k] for k in range(n)]       # remove that component
    length = sum(t * t for t in v) ** 0.5
    Q.append([t / length for t in v])                    # scale to length 1

for j in range(n):
    print("q" + str(j + 1), "=", Q[j])
''',
    adv=["Easy to understand and implement.", "Gives QR factorization directly.", "Modified version is quite stable."],
    lim=["Classical version loses orthogonality for nearly dependent vectors.", "Fails if the vectors are linearly dependent (a zero vector appears).", "Householder QR is more reliable."],
    related=["qr", "lls", "legendre"], example_intro="Orthonormalise the columns of A = [[1,1,0],[1,0,1],[0,1,1]].",
),
"qr": entry(
    what="QR factorization writes A = Q·R where Q has orthonormal columns (QᵀQ = I) and R is upper triangular. Here Q and R are built with Householder reflections.",
    why="It solves least-squares problems far more accurately than the normal equations, because orthogonal matrices do not amplify errors.",
    solves="Factorises A = QR and solves min ‖b − Ax‖ via the triangular system Rx = Qᵀb.",
    uses="Least squares, eigenvalue algorithms (the QR algorithm), numerical stability-critical regression.",
    explain="A Householder reflection H = I − 2vvᵀ mirrors a vector so that all entries below the first become zero. Apply one reflection per column to turn A into the triangular R; the product of the reflections is Qᵀ.",
    formula=r"A=QR,\qquad H=I-2vv^T,\qquad \min\|b-Ax\|\ \Rightarrow\ Rx=Q^Tb",
    variables=[[r"Q", "orthogonal: Q^TQ=I"], [r"R", "upper triangular"], [r"v", "unit vector defining the reflection"]],
    why_works="Because Q is orthogonal, ‖b − Ax‖ = ‖Qᵀb − Rx‖. The first n rows can be made zero exactly by solving Rx = (Qᵀb)₁..ₙ, and the remaining rows are the unavoidable residual. Orthogonal transformations keep the condition number unchanged (κ(R) = κ(A), unlike κ(AᵀA) = κ(A)²).",
    code=DATA + '''m = 4
n = 2
cols = [[A[i][j] for i in range(m)] for j in range(n)]

Q = []                                       # Gram-Schmidt gives the same Q and R
R = [[0, 0], [0, 0]]
for j in range(n):
    v = cols[j][:]
    for i in range(j):
        R[i][j] = sum(Q[i][k] * v[k] for k in range(m))
        v = [v[k] - R[i][j] * Q[i][k] for k in range(m)]
    R[j][j] = sum(t * t for t in v) ** 0.5
    Q.append([t / R[j][j] for t in v])

# least squares: solve R x = Q^T b by back substitution
qtb = [sum(Q[j][k] * b[k] for k in range(m)) for j in range(n)]
x = [0] * n
for i in range(n - 1, -1, -1):
    s = 0
    for j in range(i + 1, n):
        s = s + R[i][j] * x[j]
    x[i] = (qtb[i] - s) / R[i][i]

print("R =", R)
print("Solution x =", x)
''',
    adv=["Numerically stable least-squares solver.", "Householder QR works for any matrix.", "Q is perfectly conditioned."],
    lim=["About twice the cost of the normal equations.", "Q can be large (m×m) for tall matrices."],
    related=["gram_schmidt", "lls", "svd"], example_intro="Factorise the 4×2 matrix A = [[1,1],[1,2],[1,3],[1,4]] and use it to solve the least-squares problem with b = (6, 5, 7, 10).", exact=LS,
),
"svd": entry(
    what="The singular value decomposition factorises any matrix as A = UΣVᵀ with orthogonal U and V and non-negative singular values σ on the diagonal of Σ.",
    why="The SVD reveals the rank, the condition number, and the best low-rank approximations of a matrix - it is the most informative matrix factorization.",
    solves="Computes the singular values and vectors of A.",
    uses="Image compression, principal component analysis (PCA), recommender systems, solving ill-conditioned least-squares problems.",
    explain="The matrix AᵀA is symmetric with non-negative eigenvalues λᵢ. The singular values are σᵢ = √λᵢ, the eigenvectors are the columns of V, and uᵢ = Avᵢ/σᵢ. NUMERIQ finds the eigenvalues with Jacobi rotations.",
    formula=r"A=U\Sigma V^T,\qquad \sigma_i=\sqrt{\lambda_i(A^TA)},\qquad u_i=\frac{Av_i}{\sigma_i},\qquad \kappa_2(A)=\frac{\sigma_1}{\sigma_r}",
    variables=[[r"\sigma_i", "singular values, σ₁ ≥ σ₂ ≥ … ≥ 0"], [r"v_i", "right singular vectors (columns of V)"], [r"u_i", "left singular vectors (columns of U)"]],
    why_works="AᵀA = VΣ²Vᵀ, so V diagonalises it with eigenvalues σ². Defining uᵢ = Avᵢ/σᵢ gives orthonormal vectors and AV = UΣ, hence A = UΣVᵀ. The Eckart-Young theorem says that truncating after k singular values gives the best rank-k approximation, with error √(σ²ₖ₊₁ + …).",
    code='''
import math

A = [[3, 2, 2], [2, 3, -2]]                  # 2 x 3 matrix

# for a 2-row matrix we can use A A^T (2x2) whose eigenvalues are sigma^2
p = sum(A[0][k] * A[0][k] for k in range(3))     # (A A^T)[0][0]
q = sum(A[0][k] * A[1][k] for k in range(3))     # (A A^T)[0][1]
r = sum(A[1][k] * A[1][k] for k in range(3))     # (A A^T)[1][1]

mean = (p + r) / 2
radius = math.sqrt(((p - r) / 2) ** 2 + q ** 2)
lam1 = mean + radius                         # larger eigenvalue
lam2 = mean - radius                         # smaller eigenvalue

sigma1 = math.sqrt(lam1)
sigma2 = math.sqrt(lam2)
print("Singular values =", [sigma1, sigma2])
''',
    adv=["Works for every matrix, even rank-deficient or rectangular.", "Gives rank, condition number and best low-rank approximations.", "Very stable."],
    lim=["More expensive than QR or LU.", "The AᵀA route squares the condition number (production codes use other algorithms)."],
    related=["qr", "cond_number", "lls"], example_intro="Find the singular values of A = [[3,2,2],[2,3,−2]]. The eigenvalues of AAᵀ = [[17,8],[8,17]] are 25 and 9, so σ = 5 and 3.", exact={"label": "Exact singular values", "value": [5, 3]},
),
}
