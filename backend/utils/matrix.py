"""Tiny matrix helpers written with plain Python lists (no NumPy),
so that every step of the algorithms stays easy to read."""
import math


def zeros(m, n):
    return [[0.0] * n for _ in range(m)]


def identity(n):
    I = zeros(n, n)
    for i in range(n):
        I[i][i] = 1.0
    return I


def copy(A):
    return [row[:] for row in A]


def transpose(A):
    return [[A[i][j] for i in range(len(A))] for j in range(len(A[0]))]


def mat_mul(A, B):
    m, k, n = len(A), len(B), len(B[0])
    C = zeros(m, n)
    for i in range(m):
        for j in range(n):
            total = 0.0
            for t in range(k):
                total += A[i][t] * B[t][j]
            C[i][j] = total
    return C


def mat_vec(A, x):
    return [sum(A[i][j] * x[j] for j in range(len(x))) for i in range(len(A))]


def dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def norm2(v):
    return math.sqrt(sum(a * a for a in v))


def norm_inf(v):
    return max(abs(a) for a in v)


def vec_sub(u, v):
    return [a - b for a, b in zip(u, v)]


def mat_sub(A, B):
    return [[A[i][j] - B[i][j] for j in range(len(A[0]))] for i in range(len(A))]


def frobenius(A):
    return math.sqrt(sum(a * a for row in A for a in row))


def is_symmetric(A, tol=1e-10):
    n = len(A)
    scale = max(1.0, max(abs(a) for row in A for a in row))
    return all(abs(A[i][j] - A[j][i]) <= tol * scale for i in range(n) for j in range(n))
