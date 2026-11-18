from content.helpers import entry

X123 = {"label": "Exact solution (by construction)", "value": [1, 2, 3]}
SPD = '''
A = [[4, 12, -16], [12, 37, -43], [-16, -43, 98]]     # symmetric positive definite
b = [-20, -43, 192]
n = 3
'''

CONTENT = {
"gauss_elim": entry(
    what="Gaussian elimination solves a linear system Ax = b by turning it into an upper-triangular system with row operations, then solving from the bottom up.",
    why="Linear systems appear everywhere - circuits, structures, economics, data fitting. Gaussian elimination is the standard direct method for solving them.",
    solves="Finds the vector x with Ax = b when A is a square, non-singular matrix.",
    uses="Circuit analysis, structural engineering, balancing chemical equations, and as the core of every linear-algebra library.",
    explain="Use the first equation to eliminate x₁ from all equations below it, then use the second to eliminate x₂ below it, and so on. The result is a triangular system. The last equation has one unknown; substitute upwards (back substitution) to find the others.",
    formula=r"m_{ik}=\frac{a_{ik}}{a_{kk}},\quad R_i\leftarrow R_i-m_{ik}R_k\qquad;\qquad x_i=\frac{c_i-\sum_{j>i}u_{ij}x_j}{u_{ii}}",
    variables=[[r"a_{kk}", "pivot - the diagonal entry used to eliminate"], [r"m_{ik}", "multiplier for row i"], [r"u_{ij},\ c_i", "entries of the triangular system"], [r"x_i", "solution components"]],
    why_works="Subtracting a multiple of one equation from another never changes the solution set, so every elimination step keeps the system equivalent. After n − 1 stages the matrix is upper triangular, which can be solved in a single backwards sweep. The work is about 2n³/3 operations.",
    code='''
A = [[2, 1, -1], [-3, -1, 2], [-2, 1, 2]]
b = [8, -11, -3]
n = 3

for k in range(n - 1):                       # forward elimination
    for i in range(k + 1, n):
        m = A[i][k] / A[k][k]                # multiplier
        for j in range(k, n):
            A[i][j] = A[i][j] - m * A[k][j]  # row_i = row_i - m * row_k
        b[i] = b[i] - m * b[k]

x = [0] * n
for i in range(n - 1, -1, -1):               # back substitution
    s = 0
    for j in range(i + 1, n):
        s = s + A[i][j] * x[j]
    x[i] = (b[i] - s) / A[i][i]

print("Solution x =", x)
''',
    adv=["Direct method: exact answer in a fixed number of steps (up to rounding).", "Works for any non-singular matrix when pivoting is used.", "Also gives the determinant."],
    lim=["Cost grows like n³.", "Without pivoting a zero or tiny pivot breaks it.", "Rounding errors can grow for ill-conditioned matrices."],
    related=["pivoting", "lu", "iterative"], example_intro="Solve 2x + y − z = 8, −3x − y + 2z = −11, −2x + y + 2z = −3 (the solution is x = 2, y = 3, z = −1).", exact={"label": "Exact solution", "value": [2, 3, -1]},
),
"pivoting": entry(
    what="Pivoting means swapping rows (and maybe columns) before each elimination step so that the pivot - the number you divide by - is as large as possible.",
    why="Dividing by a tiny pivot creates huge multipliers that swamp the other numbers and destroy accuracy. Pivoting prevents this.",
    solves="Keeps Gaussian elimination accurate and prevents breakdown at zero pivots.",
    uses="Every serious linear-solver library uses partial pivoting by default.",
    explain="Partial pivoting looks down column k and swaps in the row with the largest |aᵢₖ|. Complete pivoting searches the whole remaining block and swaps rows and columns. Scaled pivoting compares sizes relative to each row.",
    formula=r"\text{partial: choose } p \text{ with } |a_{pk}|=\max_{i\ge k}|a_{ik}|;\qquad \text{then all multipliers satisfy } |m_{ik}|\le 1",
    variables=[[r"a_{pk}", "chosen pivot"], [r"m_{ik}", "multipliers - kept ≤ 1 by partial pivoting"]],
    why_works="With |m| ≤ 1 no entry can grow by more than a bounded factor during elimination, so rounding errors stay under control. In the classic example [[10⁻²⁰, 1],[1, 1]] the multiplier without pivoting is 10²⁰, which wipes out the information in the second row and gives x₁ = 0 instead of 1.",
    code='''
a11 = 1e-20
a12 = 1
a21 = 1
a22 = 1
b1 = 1
b2 = 2

# WITHOUT pivoting: divide by the tiny a11
m = a21 / a11                                # huge multiplier 1e20
x2 = (b2 - m * b1) / (a22 - m * a12)
x1 = (b1 - a12 * x2) / a11
print("Without pivoting:", [x1, x2])

# WITH pivoting: swap the two rows first, so the pivot is 1
m = a11 / a21                                # tiny multiplier 1e-20
x2 = (b1 - m * b2) / (a12 - m * a22)
x1 = (b2 - a22 * x2) / a21
print("With pivoting:   ", [x1, x2])
''',
    adv=["Dramatically improves accuracy.", "Cheap for partial pivoting (just a search in one column).", "Allows factorising matrices with zeros on the diagonal."],
    lim=["Complete pivoting costs more (searching the whole block).", "Changes the order of rows/columns, so extra bookkeeping is needed."],
    related=["gauss_elim", "lu", "conditioning"], example_intro="Solve 10⁻²⁰x + y = 1, x + y = 2 (the true solution is almost exactly x = 1, y = 1) with no, partial and complete pivoting.", exact={"label": "True solution (to 20 digits)", "value": [1, 1]},
),
"lu": entry(
    what="LU factorization writes A as the product of a lower-triangular matrix L and an upper-triangular matrix U.",
    why="After A = LU is computed once, you can solve Ax = b for many different b's very cheaply (two triangular solves).",
    solves="Computes A = LU and solves Ax = b via Ly = b and Ux = y.",
    uses="Solving many systems with the same matrix, computing determinants, inverting matrices.",
    explain="The multipliers from Gaussian elimination are the entries of L; the final triangular matrix is U. The Doolittle formulas compute them directly, row by row, with ones on L's diagonal.",
    formula=r"u_{ik}=a_{ik}-\sum_{j<i}l_{ij}u_{jk},\qquad l_{ki}=\frac{a_{ki}-\sum_{j<i}l_{kj}u_{ji}}{u_{ii}},\qquad Ly=b,\ Ux=y",
    variables=[[r"L", "lower-triangular with 1s on the diagonal"], [r"U", "upper-triangular"], [r"y", "intermediate vector"], [r"\det A=\prod u_{ii}", "determinant for free"]],
    why_works="Multiplying out A = LU gives n² equations for the entries of L and U; the Doolittle order (row i of U, then column i of L) solves them one at a time. Then Ax = LUx = b becomes two easy triangular systems. It exists without row swaps only if no pivot uii becomes zero.",
    code=SPD + '''
L = [[0] * n for i in range(n)]
U = [[0] * n for i in range(n)]
for i in range(n):
    L[i][i] = 1                              # Doolittle: 1s on the diagonal of L
    for k in range(i, n):                    # row i of U
        s = 0
        for j in range(i):
            s = s + L[i][j] * U[j][k]
        U[i][k] = A[i][k] - s
    for k in range(i + 1, n):                # column i of L
        s = 0
        for j in range(i):
            s = s + L[k][j] * U[j][i]
        L[k][i] = (A[k][i] - s) / U[i][i]

y = [0] * n                                  # forward substitution: L y = b
for i in range(n):
    s = 0
    for j in range(i):
        s = s + L[i][j] * y[j]
    y[i] = b[i] - s

x = [0] * n                                  # back substitution: U x = y
for i in range(n - 1, -1, -1):
    s = 0
    for j in range(i + 1, n):
        s = s + U[i][j] * x[j]
    x[i] = (y[i] - s) / U[i][i]

print("L =", L)
print("U =", U)
print("Solution x =", x)
''',
    adv=["Reuse the factorization for many right-hand sides.", "Gives the determinant.", "Foundation for matrix inversion."],
    lim=["Fails (zero pivot) for some matrices unless rows are swapped.", "Costs about 2n³/3 operations."],
    related=["gauss_elim", "cholesky", "inverse"], example_intro="Factorise A = [[4,12,−16],[12,37,−43],[−16,−43,98]] and solve Ax = b with b = (−20, −43, 192). The solution is (1, 2, 3).", exact=X123,
),
"cholesky": entry(
    what="Cholesky factorization writes a symmetric positive definite matrix as A = L·Lᵀ with L lower-triangular.",
    why="It needs half the work of LU and is extremely stable, so it is the preferred method for symmetric positive definite systems.",
    solves="Factorises A = LLᵀ and solves Ax = b via Ly = b, Lᵀx = y.",
    uses="Least-squares problems, covariance matrices in statistics, finite-element stiffness matrices, simulation of correlated random numbers.",
    explain="Because A is symmetric we only need to find L. Compute it column by column: the diagonal entry is a square root, the entries below come from a division.",
    formula=r"l_{ii}=\sqrt{a_{ii}-\sum_{k<i}l_{ik}^2},\qquad l_{ij}=\frac{a_{ij}-\sum_{k<j}l_{ik}l_{jk}}{l_{jj}}\ (i>j)",
    variables=[[r"L", "lower-triangular factor with positive diagonal"], [r"A=A^T", "symmetric"], [r"x^TAx>0", "positive definite condition"]],
    why_works="Multiplying out LLᵀ and comparing with A entry by entry gives the formulas. The term under the square root is positive exactly when A is positive definite, so a zero or negative value proves A is not positive definite. Also det A = (Π lᵢᵢ)².",
    code=SPD + '''import math

L = [[0.0] * n for i in range(n)]
for i in range(n):
    for j in range(i + 1):
        s = 0
        for k in range(j):
            s = s + L[i][k] * L[j][k]
        if i == j:
            L[i][i] = math.sqrt(A[i][i] - s)         # diagonal: square root
        else:
            L[i][j] = (A[i][j] - s) / L[j][j]        # below the diagonal

y = [0] * n                                          # L y = b
for i in range(n):
    s = 0
    for j in range(i):
        s = s + L[i][j] * y[j]
    y[i] = (b[i] - s) / L[i][i]

x = [0] * n                                          # L^T x = y
for i in range(n - 1, -1, -1):
    s = 0
    for j in range(i + 1, n):
        s = s + L[j][i] * x[j]
    x[i] = (y[i] - s) / L[i][i]

print("L =", L)
print("Solution x =", x)
''',
    adv=["About twice as fast as LU.", "No pivoting needed; very stable.", "Also a cheap test for positive definiteness."],
    lim=["Only for symmetric positive definite matrices.", "Fails (square root of a negative number) otherwise."],
    related=["lu", "gauss_elim", "lls"], example_intro="Factorise the same matrix A = [[4,12,−16],[12,37,−43],[−16,−43,98]] (L comes out with integer entries) and solve for x = (1, 2, 3).", exact=X123,
),
"inverse": entry(
    what="Matrix inversion finds A⁻¹, the matrix with A·A⁻¹ = I. Gauss-Jordan elimination does this by row-reducing [A | I].",
    why="The inverse solves every system with matrix A at once (x = A⁻¹b) and is needed in theory and some formulas.",
    solves="Computes A⁻¹ for a square, non-singular matrix.",
    uses="Control theory, statistics formulas, coordinate transformations.",
    explain="Write A next to the identity matrix and apply row operations until the left side becomes I. The same operations turn I into A⁻¹. Each column of A⁻¹ is the solution of Ax = eⱼ.",
    formula=r"[\,A\mid I\,]\ \xrightarrow{\ \text{row operations}\ }\ [\,I\mid A^{-1}\,]",
    variables=[[r"A", "square matrix"], [r"I", "identity matrix"], [r"A^{-1}", "inverse"]],
    why_works="Row operations are multiplication on the left by invertible matrices E. If EA = I then E = A⁻¹, and applying the same operations to I produces EI = A⁻¹. If a zero pivot cannot be fixed by a swap, A is singular and has no inverse.",
    code='''
A = [[2, -1, 0], [-1, 2, -1], [0, -1, 2]]
n = 3

# build the augmented matrix [A | I]
M = [A[i][:] + [1 if i == j else 0 for j in range(n)] for i in range(n)]

for k in range(n):
    p = k                                    # partial pivoting
    for i in range(k + 1, n):
        if abs(M[i][k]) > abs(M[p][k]):
            p = i
    M[k], M[p] = M[p], M[k]
    pivot = M[k][k]
    M[k] = [v / pivot for v in M[k]]         # make the pivot equal to 1
    for i in range(n):
        if i != k:
            m = M[i][k]
            M[i] = [M[i][j] - m * M[k][j] for j in range(2 * n)]   # clear column k

inverse = [row[n:] for row in M]             # right half = A^-1
print("Inverse =", inverse)
''',
    adv=["Gives all solutions for the matrix at once.", "Simple conceptually."],
    lim=["About three times the work of solving one system.", "Less accurate than solving Ax = b directly.", "Does not exist for singular matrices."],
    related=["lu", "gauss_elim", "cond_number"], example_intro="Invert A = [[2,−1,0],[−1,2,−1],[0,−1,2]]. The exact inverse is ¼·[[3,2,1],[2,4,2],[1,2,3]].", exact={"label": "Exact inverse ¼[[3,2,1],[2,4,2],[1,2,3]]", "value": [[0.75, 0.5, 0.25], [0.5, 1, 0.5], [0.25, 0.5, 0.75]]},
),
"iterative": entry(
    what="Iterative methods solve Ax = b by starting from a guess and improving it repeatedly. Jacobi and Gauss-Seidel are the two classic ones.",
    why="For very large, sparse systems (millions of unknowns) direct elimination is too slow and uses too much memory; each iteration here is cheap.",
    solves="Finds x with Ax = b by repeating an update until the change is below a tolerance.",
    uses="Discretised physical problems (heat, fluid flow, electromagnetism), network analysis, large sparse systems.",
    explain="Solve the i-th equation for xᵢ: xᵢ = (bᵢ − Σ aᵢⱼxⱼ)/aᵢᵢ. Jacobi computes every new value from the OLD vector. Gauss-Seidel uses each new value immediately, which usually speeds things up.",
    formula=r"x_i^{(k+1)}=\frac{1}{a_{ii}}\Big(b_i-\sum_{j\ne i}a_{ij}x_j^{(k)}\Big)\ \text{(Jacobi)};\quad \text{Gauss-Seidel uses } x_j^{(k+1)}\ \text{for } j<i",
    variables=[[r"x^{(k)}", "approximation after k iterations"], [r"a_{ii}", "diagonal entries (must be non-zero)"], [r"\rho(T)", "spectral radius of the iteration matrix - must be < 1"]],
    why_works="The iteration is x ← Tx + c. The error is multiplied by T each step, so it vanishes exactly when the spectral radius ρ(T) < 1. A strictly diagonally dominant matrix (|aᵢᵢ| > Σ|aᵢⱼ|) guarantees this for both methods.",
    code='''
A = [[10, -1, 2], [-1, 11, -1], [2, -1, 10]]
b = [14, 18, 30]
n = 3
x = [0, 0, 0]                                # starting guess
tol = 1e-8

for k in range(1, 201):
    old = x[:]
    for i in range(n):                       # Gauss-Seidel: use new values at once
        s = 0
        for j in range(n):
            if j != i:
                s = s + A[i][j] * x[j]
        x[i] = (b[i] - s) / A[i][i]
    change = max(abs(x[i] - old[i]) for i in range(n))
    if change < tol:
        break

print("Solution x =", x)
print("Iterations =", k)
''',
    adv=["Cheap iterations and low memory for sparse systems.", "Self-correcting: rounding errors do not accumulate.", "Very simple to program."],
    lim=["May converge slowly or not at all.", "Needs diagonal dominance (or similar) for guaranteed convergence.", "A tolerance must be chosen."],
    related=["gauss_elim", "cg", "cond_number"], example_intro="Solve a diagonally dominant 3×3 system with Gauss-Seidel starting from (0, 0, 0). The exact solution is (1, 2, 3).", exact=X123,
),
"conditioning": entry(
    what="Matrix conditioning measures how strongly the solution of Ax = b reacts to small changes in b (or in A).",
    why="Input data always contain tiny errors. If a system is ill-conditioned, these tiny errors are magnified into large errors in the answer, however good your algorithm is.",
    solves="Quantifies and demonstrates the amplification of errors: perturb b slightly and compare the change in x.",
    uses="Judging whether a numerical result can be trusted; designing well-posed models and experiments.",
    explain="Solve Ax = b. Change b by a tiny amount δb and solve again. Compare the relative change in x with the relative change in b. The ratio is the error amplification. It can never exceed the condition number κ(A).",
    formula=r"\frac{\|\delta x\|}{\|x\|}\ \le\ \kappa(A)\,\frac{\|\delta b\|}{\|b\|}",
    variables=[[r"\delta b", "small change in the right-hand side"], [r"\delta x", "resulting change in the solution"], [r"\kappa(A)", "condition number"]],
    why_works="From Ax = b and A(x+δx) = b+δb we get δx = A⁻¹δb, so ‖δx‖ ≤ ‖A⁻¹‖‖δb‖. Dividing by ‖x‖ and using ‖b‖ ≤ ‖A‖‖x‖ gives the bound with κ = ‖A‖‖A⁻¹‖. Nearly parallel rows (as in [[1,1],[1,1.0001]]) mean A⁻¹ is huge.",
    code='''
A = [[1, 1], [1, 1.0001]]
b = [2, 2.0001]
eps = 1e-4

def solve(b):                                # solve the 2x2 system by Cramer's rule
    det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
    x1 = (b[0] * A[1][1] - A[0][1] * b[1]) / det
    x2 = (A[0][0] * b[1] - A[1][0] * b[0]) / det
    return [x1, x2]

x = solve(b)
scale = max(abs(b[0]), abs(b[1]))
db = [eps * scale, -eps * scale]             # tiny change in b
x_new = solve([b[0] + db[0], b[1] + db[1]])
dx = [x_new[0] - x[0], x_new[1] - x[1]]

rel_b = max(abs(db[0]), abs(db[1])) / scale
rel_x = max(abs(dx[0]), abs(dx[1])) / max(abs(x[0]), abs(x[1]))
print("Amplification =", rel_x / rel_b)
''',
    adv=["Shows directly how much accuracy is lost.", "Helps decide whether to trust a numerical answer."],
    lim=["The experiment depends on the particular perturbation chosen; κ(A) is the worst-case bound.", "Fixing ill-conditioning needs reformulating the problem, not a better algorithm."],
    related=["cond_number", "pivoting", "svd"], example_intro="Take A = [[1,1],[1,1.0001]], b = (2, 2.0001) (solution (1, 1)) and change b by only 0.01 %. The solution changes by thousands of percent.",
),
"cond_number": entry(
    what="The condition number κ(A) = ‖A‖·‖A⁻¹‖ is a single number that tells how sensitive linear systems with matrix A are to errors.",
    why="It predicts how many digits of accuracy you may lose when solving Ax = b, before you even compute the answer.",
    solves="Computes κ(A) in the 1-, ∞- or Frobenius norm.",
    uses="Error estimates for linear solvers, deciding when to regularise or rescale a problem.",
    explain="Compute the norm of A and of A⁻¹ and multiply. κ(A) ≥ 1 always. Values near 1 mean well-conditioned. Very large values (like 10¹⁰) mean ill-conditioned: about log₁₀κ decimal digits can be lost.",
    formula=r"\kappa(A)=\|A\|\,\|A^{-1}\|,\qquad \|A\|_\infty=\max_i\sum_j|a_{ij}|,\quad \|A\|_1=\max_j\sum_i|a_{ij}|",
    variables=[[r"\|A\|_\infty", "largest absolute row sum"], [r"\|A\|_1", "largest absolute column sum"], [r"\kappa(A)", "condition number"], [r"\log_{10}\kappa", "approximate number of digits lost"]],
    why_works="The relative error bound ‖δx‖/‖x‖ ≤ κ(A)·‖δb‖/‖b‖ shows κ is exactly the worst-case error amplification factor. Singular matrices have κ = ∞. Orthogonal matrices have κ₂ = 1, the best possible.",
    code='''
A = [[1, 1], [1, 1.0001]]

det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
inverse = [[A[1][1] / det, -A[0][1] / det],      # inverse of a 2x2 matrix
           [-A[1][0] / det, A[0][0] / det]]

def norm_inf(M):                                 # largest absolute row sum
    return max(sum(abs(v) for v in row) for row in M)

kappa = norm_inf(A) * norm_inf(inverse)
print("Condition number =", kappa)
''',
    adv=["One number summarises sensitivity.", "Independent of the right-hand side."],
    lim=["Requires (an estimate of) A⁻¹, which is expensive for big matrices.", "Depends on the chosen norm (but all norms agree on the magnitude)."],
    related=["conditioning", "inverse", "svd"], example_intro="Compute κ∞ of A = [[1,1],[1,1.0001]]: ‖A‖∞ = 2.0001 and ‖A⁻¹‖∞ ≈ 20000, so κ ≈ 40004 - about 4–5 digits can be lost.",
),
}
