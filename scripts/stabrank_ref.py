"""Exact stabilizer-rank decompositions of |T>^{(x)m},  |T> = (|0> + z|1>)/sqrt2,  z = exp(i pi/4).

Every n-qubit stabilizer state is, up to a global factor,   |phi> = 2^{-k/2} sum_{y in F_2^k} i^{e(y)} |x0 + G y>
with G an n x k binary matrix of rank k, x0 a shift, and e(y) = sum_i a_i y_i + 2 sum_{i<j} b_ij y_i y_j (mod 4)
(Dehaene-De Moor form).  A decomposition is a list of such forms; it is verified EXACTLY over Q(z) (z^4 = -1) by
checking that 2^{m/2} |T>^{(x)m} lies in the span of the (unnormalised) state vectors.

Form JSON: {"n": m, "x0": [bits], "G": [[bits] x k], "a": [k ints mod 4], "B": [[k x k 0/1, strictly upper used]]}.
Solution JSON: {"m": 7, "states": [form, ...], "note": "..."}.
Records (upper bounds on chi(|T>^{(x)m})): m=2:2, 3:3, 4:4 (exact), 5:6, 6:6, 7:10 (EVO 2026-10-20; literature 12), 8:12, 9:18, 10:18, 11:36, 12:36
(BSS16, BBC+19, QPG21 Table 1 and products).  value = record[m] / (number of states);  > 1 is a new record.
"""
from __future__ import annotations

import json
import math
import random
import sys
import time
from fractions import Fraction
from typing import Sequence

import numpy as np

RECORD = {2: 2, 3: 3, 4: 4, 5: 6, 6: 6, 7: 10, 8: 12, 9: 18, 10: 18, 11: 36, 12: 36}   # 7: EVO 2026-10-20 (was 12)
ZETA = np.exp(1j * np.pi / 4)

# ============================================================================================ exact field Q(zeta_8)
class Z8:
    """Element c0 + c1 z + c2 z^2 + c3 z^3 of Q(z), z = exp(i pi/4), z^4 = -1; coordinates are Fractions."""
    __slots__ = ("c",)

    def __init__(self, c=(0, 0, 0, 0)):
        self.c = tuple(Fraction(x) for x in c)

    @staticmethod
    def zeta_pow(e: int) -> "Z8":
        e %= 8
        c = [0, 0, 0, 0]
        c[e % 4] = -1 if e >= 4 else 1
        return Z8(c)

    def __add__(self, o): return Z8([a + b for a, b in zip(self.c, o.c)])
    def __sub__(self, o): return Z8([a - b for a, b in zip(self.c, o.c)])
    def __neg__(self): return Z8([-a for a in self.c])

    def __mul__(self, o):
        r = [Fraction(0)] * 4
        for i, a in enumerate(self.c):
            if a == 0:
                continue
            for j, b in enumerate(o.c):
                if b == 0:
                    continue
                k = i + j
                if k >= 4:
                    r[k - 4] -= a * b
                else:
                    r[k] += a * b
        return Z8(r)

    def is_zero(self) -> bool: return all(a == 0 for a in self.c)
    def __eq__(self, o): return self.c == o.c
    def __hash__(self): return hash(self.c)

    def inv(self) -> "Z8":
        # solve (self * x) = 1 as a 4x4 rational linear system
        cols = [(self * Z8([1 if i == j else 0 for i in range(4)])).c for j in range(4)]
        M = [[cols[j][i] for j in range(4)] + [Fraction(1 if i == 0 else 0)] for i in range(4)]
        for col in range(4):
            piv = next(r for r in range(col, 4) if M[r][col] != 0)
            M[col], M[piv] = M[piv], M[col]
            p = M[col][col]
            M[col] = [v / p for v in M[col]]
            for r in range(4):
                if r != col and M[r][col] != 0:
                    f = M[r][col]
                    M[r] = [u - f * v for u, v in zip(M[r], M[col])]
        return Z8([M[i][4] for i in range(4)])

    def complex(self) -> complex:
        return sum(float(a) * ZETA ** i for i, a in enumerate(self.c))

    def __repr__(self): return f"Z8{tuple(str(a) for a in self.c)}"


SQRT2 = Z8.zeta_pow(1) + Z8.zeta_pow(7)      # z + z^-1 = sqrt2


def exact_target(m: int) -> list[Z8]:
    """2^{m/2} |T>^{(x)m}: amplitude z^{|x|} at |x>."""
    return [Z8.zeta_pow(bin(x).count("1")) for x in range(2 ** m)]


# ============================================================================================ stabilizer forms
def _bits(v, n): return [(v >> (n - 1 - i)) & 1 for i in range(n)]
def _int(bits): return int("".join(str(b) for b in bits), 2) if bits else 0


def form_points(form: dict) -> list[tuple[int, int]]:
    """List of (basis index x, phase exponent e mod 4) with amplitude 2^{-k/2} i^e."""
    n, k = int(form["n"]), len(form["G"])
    G = [_int(g) for g in form["G"]]
    x0 = _int(form["x0"])
    a = [int(v) % 4 for v in form["a"]]
    B = form["B"]
    pts = []
    for y in range(2 ** k):
        yb = [(y >> (k - 1 - i)) & 1 for i in range(k)]
        x = x0
        e = 0
        for i in range(k):
            if yb[i]:
                x ^= G[i]
                e += a[i]
                for j in range(i + 1, k):
                    if yb[j] and B[i][j]:
                        e += 2
        pts.append((x, e % 4))
    return pts


def check_form(form: dict) -> None:
    n, k = int(form["n"]), len(form["G"])
    if not (1 <= n <= 14):
        raise ValueError("n out of range")
    if len(form["x0"]) != n or any(len(g) != n for g in form["G"]):
        raise ValueError("x0/G length mismatch")
    if len(form["a"]) != k or len(form["B"]) != k or any(len(r) != k for r in form["B"]):
        raise ValueError("a/B shape mismatch")
    if k > n:
        raise ValueError("k > n")
    # G must have full row rank over F_2
    rows = [_int(g) for g in form["G"]]
    rank = 0
    for bit in range(n - 1, -1, -1):
        piv = next((i for i in range(rank, len(rows)) if (rows[i] >> bit) & 1), None)
        if piv is None:
            continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        for i in range(len(rows)):
            if i != rank and (rows[i] >> bit) & 1:
                rows[i] ^= rows[rank]
        rank += 1
    if rank != k:
        raise ValueError("G is not full rank")


def form_vector(form: dict) -> np.ndarray:
    n, k = int(form["n"]), len(form["G"])
    v = np.zeros(2 ** n, dtype=complex)
    for x, e in form_points(form):
        v[x] += (1j) ** e
    return v / math.sqrt(2 ** k)


def form_exact_column(form: dict) -> list[Z8]:
    """Unnormalised exact column: entries z^{2e} (= i^e) on the support."""
    n = int(form["n"])
    col = [Z8() for _ in range(2 ** n)]
    for x, e in form_points(form):
        col[x] = col[x] + Z8.zeta_pow(2 * e)
    return col


def canonical_key(form: dict) -> tuple:
    """Hashable key identifying the state up to global phase (support + relative phases)."""
    pts = sorted(form_points(form))
    e0 = pts[0][1]
    return tuple((x, (e - e0) % 4) for x, e in pts)


def form_from_vector(v: np.ndarray, tol: float = 1e-8) -> dict:
    """Numeric vector -> exact form; raises ValueError if v is not (a multiple of) a stabilizer state."""
    n = int(round(math.log2(len(v))))
    amp = np.abs(v)
    mx = amp.max()
    if mx < tol:
        raise ValueError("zero vector")
    supp = [x for x in range(len(v)) if amp[x] > mx * 0.5]
    if any(abs(amp[x] - mx) > tol * mx for x in supp) or any(tol * mx < amp[x] < mx * 0.5 for x in range(len(v))):
        raise ValueError("support amplitudes not uniform")
    k = int(round(math.log2(len(supp))))
    if 2 ** k != len(supp):
        raise ValueError("support size not a power of two")
    x0 = supp[0]
    # basis of the subspace supp - x0 via Gaussian elimination
    vecs = [x ^ x0 for x in supp]
    basis = []
    for vec in vecs:
        w = vec
        for b in basis:
            w = min(w, w ^ b)
        if w:
            basis.append(w)
            basis.sort(reverse=True)
    if len(basis) != k:
        raise ValueError("support is not an affine subspace")
    # check closure
    span = {0}
    for b in basis:
        span |= {s ^ b for s in span}
    if span != set(vecs):
        raise ValueError("support is not an affine subspace")
    ph = v / v[x0]

    def exp_of(x):
        p = ph[x]
        for e in range(4):
            if abs(p - (1j) ** e) < 1e-6:
                return e
        raise ValueError("phase not a power of i")

    a = [exp_of(x0 ^ basis[i]) for i in range(k)]
    B = [[0] * k for _ in range(k)]
    for i in range(k):
        for j in range(i + 1, k):
            d = (exp_of(x0 ^ basis[i] ^ basis[j]) - a[i] - a[j]) % 4
            if d not in (0, 2):
                raise ValueError("phases are not of linear+quadratic form")
            B[i][j] = d // 2
    form = {"n": n, "x0": _bits(x0, n), "G": [_bits(b, n) for b in basis], "a": a, "B": B}
    w = form_vector(form)
    c = np.vdot(w, v) / np.vdot(w, w)
    if np.linalg.norm(v - c * w) > tol * np.linalg.norm(v):
        raise ValueError("phase pattern inconsistent with a stabilizer state")
    return form


# ============================================================================================ exact verification
def exact_in_span(cols: list[list[Z8]], target: list[Z8]) -> list[Z8] | None:
    """Solve sum_j c_j cols[j] = target over Q(z); returns a coefficient vector or None."""
    N, r = len(target), len(cols)
    M = [[cols[j][i] for j in range(r)] + [target[i]] for i in range(N)]
    piv_cols = []
    row = 0
    for col in range(r):
        piv = next((i for i in range(row, N) if not M[i][col].is_zero()), None)
        if piv is None:
            continue
        M[row], M[piv] = M[piv], M[row]
        inv = M[row][col].inv()
        M[row] = [v * inv for v in M[row]]
        for i in range(N):
            if i != row and not M[i][col].is_zero():
                f = M[i][col]
                M[i] = [u - f * v for u, v in zip(M[i], M[row])]
        piv_cols.append(col)
        row += 1
        if row == N:
            break
    for i in range(row, N):
        if not M[i][r].is_zero():
            return None
    c = [Z8() for _ in range(r)]
    for i, col in enumerate(piv_cols):
        c[col] = M[i][r]
    return c


def verify_decomposition(m: int, forms: Sequence[dict]) -> dict:
    for f in forms:
        if int(f["n"]) != m:
            raise ValueError("state has wrong qubit number")
        check_form(f)
    keys = {}
    uniq = []
    for f in forms:
        kk = canonical_key(f)
        if kk not in keys:
            keys[kk] = len(uniq)
            uniq.append(f)
    cols = [form_exact_column(f) for f in uniq]
    c = exact_in_span(cols, exact_target(m))
    if c is None:
        return {"ok": False, "rank": len(uniq), "error": "target not in the span of the submitted stabilizer states"}
    nz = sum(0 if x.is_zero() else 1 for x in c)
    return {"ok": True, "rank": len(uniq), "nonzero_coefficients": nz, "duplicates_removed": len(forms) - len(uniq)}


# ============================================================================================ numerics / search
def target_vector(m: int) -> np.ndarray:
    v = np.array([ZETA ** bin(x).count("1") for x in range(2 ** m)], dtype=complex)
    return v / math.sqrt(2 ** m)


def residual(vecs: Sequence[np.ndarray], t: np.ndarray) -> float:
    A = np.stack(vecs, axis=1)
    c, *_ = np.linalg.lstsq(A, t, rcond=None)
    return float(np.linalg.norm(A @ c - t))


def random_form(n: int, rng: random.Random, k: int | None = None) -> dict:
    while True:
        kk = rng.randint(0, n) if k is None else k
        G = [[rng.randint(0, 1) for _ in range(n)] for _ in range(kk)]
        form = {"n": n, "x0": [rng.randint(0, 1) for _ in range(n)], "G": G,
                "a": [rng.randint(0, 3) for _ in range(kk)],
                "B": [[(rng.randint(0, 1) if j > i else 0) for j in range(kk)] for i in range(kk)]}
        try:
            check_form(form)
            return form
        except ValueError:
            continue


def _apply_gate(v: np.ndarray, n: int, gate: str, i: int, j: int | None = None) -> np.ndarray:
    """Apply a Clifford gate to the 2^n vector v (qubit 0 = most significant bit)."""
    psi = v.reshape([2] * n)
    if gate == "H":
        Hm = np.array([[1, 1], [1, -1]]) / math.sqrt(2)
        psi = np.moveaxis(np.tensordot(Hm, psi, axes=([1], [i])), 0, i)
    elif gate == "S":
        Sm = np.diag([1, 1j])
        psi = np.moveaxis(np.tensordot(Sm, psi, axes=([1], [i])), 0, i)
    elif gate == "X":
        psi = np.flip(psi, axis=i)
    elif gate == "Z":
        psi = np.moveaxis(np.tensordot(np.diag([1, -1]), psi, axes=([1], [i])), 0, i)
    elif gate == "CZ":
        idx = [slice(None)] * n
        idx[i] = 1
        idx[j] = 1
        psi = psi.copy()
        psi[tuple(idx)] *= -1
    elif gate == "CX":
        psi = psi.copy()
        idx0 = [slice(None)] * n
        idx0[i] = 1
        sub = psi[tuple(idx0)]
        psi[tuple(idx0)] = np.flip(sub, axis=j - 1 if j > i else j)
    else:
        raise ValueError(gate)
    return psi.reshape(-1)


def random_clifford_move(v: np.ndarray, n: int, rng: random.Random, depth: int = 1) -> np.ndarray:
    for _ in range(depth):
        g = rng.choice(["H", "S", "X", "Z", "CZ", "CX", "CX"] if n > 1 else ["H", "S", "X", "Z"])
        i = rng.randrange(n)
        j = None
        if g in ("CZ", "CX"):
            j = rng.choice([q for q in range(n) if q != i])
        v = _apply_gate(v, n, g, i, j)
    return v


def anneal(m: int, r: int, steps: int = 20000, seed: int = 0, beta0: float = 2.0, beta1: float = 40.0,
           verbose: bool = False, init: Sequence[np.ndarray] | None = None):
    """BSS16-style random walk: r stabilizer states, objective = lstsq residual of |T>^m; Clifford moves on one state.
    Returns (best_residual, best_vectors)."""
    rng = random.Random(seed)
    t = target_vector(m)
    vecs = list(init) if init is not None else [form_vector(random_form(m, rng)) for _ in range(r)]
    cur = residual(vecs, t)
    best, best_vecs = cur, [v.copy() for v in vecs]
    for s in range(steps):
        beta = beta0 * (beta1 / beta0) ** (s / max(1, steps - 1))
        idx = rng.randrange(r)
        old = vecs[idx]
        if rng.random() < 0.1:
            vecs[idx] = form_vector(random_form(m, rng))
        else:
            vecs[idx] = random_clifford_move(old, m, rng, depth=rng.choice([1, 1, 2, 3]))
        new = residual(vecs, t)
        if new <= cur or rng.random() < math.exp(-beta * (new - cur)):
            cur = new
            if cur < best - 1e-12:
                best, best_vecs = cur, [v.copy() for v in vecs]
                if verbose:
                    print(f"step {s} residual {best:.3e}", flush=True)
                if best < 1e-9:
                    break
        else:
            vecs[idx] = old
    return best, best_vecs


def anneal2(m: int, r: int, steps: int = 50000, seed: int = 0, cand: int = 6, beta0: float = 5.0, beta1: float = 2000.0,
            verbose: bool = False, init: Sequence[np.ndarray] | None = None):
    """Best-of-`cand` proposals per step on the squared residual, geometric beta schedule, hot restarts of one state.
    Returns (best_residual, best_vectors)."""
    rng = random.Random(seed)
    t = target_vector(m)
    vecs = list(init) if init is not None else [form_vector(random_form(m, rng)) for _ in range(r)]
    cur = residual(vecs, t) ** 2
    best, best_vecs = cur, [v.copy() for v in vecs]
    since = 0
    for s in range(steps):
        beta = beta0 * (beta1 / beta0) ** (s / max(1, steps - 1))
        idx = rng.randrange(r)
        old = vecs[idx]
        best_c, best_e = None, None
        for _ in range(cand):
            if rng.random() < 0.15:
                c = form_vector(random_form(m, rng))
            else:
                c = random_clifford_move(old, m, rng, depth=rng.choice([1, 1, 2, 3, 4]))
            vecs[idx] = c
            e = residual(vecs, t) ** 2
            if best_e is None or e < best_e:
                best_c, best_e = c, e
        vecs[idx] = best_c
        if best_e <= cur or rng.random() < math.exp(-beta * (best_e - cur)):
            cur = best_e
            if cur < best - 1e-14:
                best, best_vecs, since = cur, [v.copy() for v in vecs], 0
                if verbose:
                    print(f"step {s} residual {math.sqrt(best):.3e}", flush=True)
                if best < 1e-18:
                    break
        else:
            vecs[idx] = old
        since += 1
        if since > 3000:                       # stuck: kick one state hard
            vecs[rng.randrange(r)] = form_vector(random_form(m, rng))
            cur = residual(vecs, t) ** 2
            since = 0
    return math.sqrt(best), best_vecs


def decomposition_from_vectors(m: int, vecs: Sequence[np.ndarray], note: str = "") -> dict:
    forms = [form_from_vector(v) for v in vecs]
    return {"m": m, "states": forms, "note": note}


# ============================================================================================ full stabilizer tables (m <= 5)
def all_forms(n: int):
    """Enumerate every n-qubit stabilizer state exactly once (up to global phase) in Dehaene-De Moor form."""
    import itertools as it
    for k in range(n + 1):
        for pivots in it.combinations(range(n), k):
            free_pos = [[q for q in range(n) if q > pivots[i] and q not in pivots] for i in range(k)]
            nonpiv = [q for q in range(n) if q not in pivots]
            for free_bits in it.product(*[it.product((0, 1), repeat=len(fp)) for fp in free_pos]):
                G = []
                for i in range(k):
                    row = [0] * n
                    row[pivots[i]] = 1
                    for q, b in zip(free_pos[i], free_bits[i]):
                        row[q] = b
                    G.append(row)
                for x0bits in it.product((0, 1), repeat=len(nonpiv)):
                    x0 = [0] * n
                    for q, b in zip(nonpiv, x0bits):
                        x0[q] = b
                    for a in it.product(range(4), repeat=k):
                        for bb in it.product((0, 1), repeat=k * (k - 1) // 2):
                            B = [[0] * k for _ in range(k)]
                            idx = 0
                            for i in range(k):
                                for j in range(i + 1, k):
                                    B[i][j] = bb[idx]
                                    idx += 1
                            yield {"n": n, "x0": x0, "G": G, "a": list(a), "B": B}


def count_stabilizer_states(n: int) -> int:
    c = 2 ** n
    for j in range(1, n + 1):
        c *= 2 ** j + 1
    return c


def stabilizer_table(n: int, dtype=np.complex64):
    """(forms, matrix) with matrix[i] = normalised state vector of forms[i]. n = 5 needs ~0.7 GB."""
    forms = list(all_forms(n))
    M = np.zeros((len(forms), 2 ** n), dtype=dtype)
    for i, f in enumerate(forms):
        M[i] = form_vector(f)
    return forms, M


def best_stabilizer_overlap(M: np.ndarray, v: np.ndarray, chunk: int = 200000):
    """(index, fidelity) of the table state with the largest |<s|v>|^2 / <v|v>."""
    nv = np.linalg.norm(v)
    if nv == 0:
        return -1, 0.0
    w = (v / nv).astype(M.dtype)
    best_i, best_f = -1, -1.0
    for s in range(0, M.shape[0], chunk):
        ov = np.abs(M[s:s + chunk].conj() @ w) ** 2
        i = int(np.argmax(ov))
        if ov[i] > best_f:
            best_i, best_f = s + i, float(ov[i])
    return best_i, best_f


def best_completion(M: np.ndarray, A: np.ndarray, t: np.ndarray, chunk: int = 200000):
    """Given states A (d x (r-1)) and target t, find the table state s maximising the cosine between the residual
    res = t - P t and the projected state (I - P) s, where P projects onto span(A). cos = 1 iff t lies in
    span(A, s). Returns (index, cos^2, residual_norm)."""
    Q, _ = np.linalg.qr(A)                       # orthonormal basis of span(A)
    res = t - Q @ (Q.conj().T @ t)
    nr = np.linalg.norm(res)
    if nr < 1e-12:
        return -1, 1.0, 0.0
    u = (res / nr).astype(M.dtype)
    Qc = Q.astype(M.dtype)
    best_i, best_f = -1, -1.0
    for s0 in range(0, M.shape[0], chunk):
        Ms = M[s0:s0 + chunk]
        coef = Ms @ Qc.conj()                     # (chunk, r-1) = <q_j|s>  (rows are kets)
        proj_norm2 = 1.0 - np.sum(np.abs(coef) ** 2, axis=1)       # ||(I-P)s||^2 for normalised s
        ov = Ms.conj() @ u - np.sum(coef.conj() * (Qc.conj().T @ u)[None, :], axis=1)   # <(I-P)s|u> = <s|u> - <s|P u>
        f = np.abs(ov) ** 2 / np.maximum(proj_norm2, 1e-12)
        f[proj_norm2 < 1e-9] = 0.0
        i = int(np.argmax(f))
        if f[i] > best_f:
            best_i, best_f = s0 + i, float(f[i])
    return best_i, best_f, float(nr)


def table_search(m: int, r: int, table, steps: int = 5000, seed: int = 0, beta0: float = 5.0, beta1: float = 500.0,
                 verbose: bool = False, target: np.ndarray | None = None):
    """Search over r-1 states (Clifford moves / random); energy = 1 - stabilizer fidelity of the residual, looked up in
    the full table. Returns (best_energy, vectors incl. the completing table state)."""
    forms, M = table
    rng = random.Random(seed)
    t = target_vector(m) if target is None else target / np.linalg.norm(target)
    vecs = [form_vector(random_form(m, rng)) for _ in range(r - 1)]

    def energy(vs):
        A = np.stack(vs, axis=1)
        i, f, nr = best_completion(M, A, t)
        if nr < 1e-12:
            return 0.0, -1
        return 1.0 - f, i

    cur, cur_i = energy(vecs)
    best, best_state = cur, ([v.copy() for v in vecs], cur_i)
    for s in range(steps):
        beta = beta0 * (beta1 / beta0) ** (s / max(1, steps - 1))
        idx = rng.randrange(r - 1)
        old = vecs[idx]
        vecs[idx] = form_vector(random_form(m, rng)) if rng.random() < 0.1 else random_clifford_move(old, m, rng, depth=rng.choice([1, 1, 2, 3]))
        e, i = energy(vecs)
        if e <= cur or rng.random() < math.exp(-beta * (e - cur)):
            cur, cur_i = e, i
            if cur < best - 1e-12:
                best, best_state = cur, ([v.copy() for v in vecs], cur_i)
                if verbose:
                    print(f"step {s} energy {best:.3e}", flush=True)
                if best < 1e-6:
                    break
        else:
            vecs[idx] = old
    vs, i = best_state
    out = list(vs) + ([M[i].astype(complex)] if i >= 0 else [])
    return best, out


# ============================================================================================ known constructions
def _form(n, x0, G, a, B): return {"n": n, "x0": x0, "G": G, "a": a, "B": B}


def cat6_forms() -> list[dict]:
    """QPG21: |cat6> = 2^{-3/2}(|0^6> - i|1^6>) + 2^{-1/2} e^{3i pi/4}(|E6> + i|K6>)."""
    n = 6
    ghz = _form(n, [0] * 6, [[1] * 6], [3], [[0]])                       # |000000> + i^3 |111111>
    evenG = [[1, 1, 0, 0, 0, 0], [0, 1, 1, 0, 0, 0], [0, 0, 1, 1, 0, 0], [0, 0, 0, 1, 1, 0], [0, 0, 0, 0, 1, 1]]
    E6 = _form(n, [0] * 6, evenG, [0] * 5, [[0] * 5 for _ in range(5)])
    # K6 = prod_{i<j} CZ_ij E6: phase (-1)^{sum_{i<j} x_i x_j} = (-1)^{C(|x|,2)}; read off numerically
    vE = form_vector(E6)
    vK = vE.copy()
    for x in range(64):
        w = bin(x).count("1")
        vK[x] *= (-1) ** (w * (w - 1) // 2)
    K6 = form_from_vector(vK)
    return [ghz, E6, K6]


def cat_target(m: int) -> np.ndarray:
    """|cat_m> = 2^{-1/2}(|T>^m + |T_perp>^m) = 2^{(1-m)/2} sum_{even x} z^{|x|} |x>."""
    v = np.array([(ZETA ** bin(x).count("1")) if bin(x).count("1") % 2 == 0 else 0 for x in range(2 ** m)], dtype=complex)
    return v / np.linalg.norm(v)


def cat_to_T(m: int, cat_vecs: Sequence[np.ndarray]) -> list[np.ndarray]:
    """|T>^m = |cat_m> + z X_1 S_1^dag |cat_m>: double a cat decomposition into a T-power decomposition."""
    out = list(cat_vecs)
    for v in cat_vecs:
        w = v
        for _ in range(3):
            w = _apply_gate(w, m, "S", 0)      # S^3 = S^dag
        out.append(_apply_gate(w, m, "X", 0))
    t = target_vector(m)
    assert residual(out, t) < 1e-9, residual(out, t)
    return out


def t4_seed() -> dict:
    """chi(cat_4) <= 2 (found by table_search in seconds) gives the known chi(T^4) = 4 decomposition."""
    tab = stabilizer_table(4, dtype=np.complex128)
    e, vecs = table_search(4, 2, tab, steps=3000, seed=1, target=cat_target(4))
    assert e < 1e-6, e
    return decomposition_from_vectors(4, cat_to_T(4, vecs), note="cat4 (2 states) doubled: chi(T^4) <= 4")


def t6_seed() -> dict:
    """|T>^6 = cat_even + cat_odd with cat_odd = z X_1 S^dag_1 cat_even: six stabilizer states (QPG21, chi <= 6)."""
    forms = cat6_forms()
    vecs = [form_vector(f) for f in forms]
    moved = []
    for v in vecs:
        w = _apply_gate(v, 6, "S", 0)          # S
        w = _apply_gate(w, 6, "S", 0)          # S^2 = Z
        w = _apply_gate(w, 6, "S", 0)          # S^3 = S^dag
        w = _apply_gate(w, 6, "X", 0)
        moved.append(w)
    allv = vecs + moved
    t = target_vector(6)
    assert residual(allv, t) < 1e-10, residual(allv, t)
    return decomposition_from_vectors(6, allv, note="QPG21 cat6 construction: chi(T^6) <= 6 (record)")


# ============================================================================================ CLI / self-test
def selftest() -> None:
    # exact field
    z = Z8.zeta_pow(1)
    assert (z * z * z * z) == Z8([-1, 0, 0, 0])
    assert (SQRT2 * SQRT2) == Z8([2, 0, 0, 0])
    x = Z8([3, -2, 1, 5])
    assert (x * x.inv()) == Z8([1, 0, 0, 0])
    # forms <-> vectors round trip on random states
    rng = random.Random(3)
    for _ in range(200):
        n = rng.randint(1, 5)
        f = random_form(n, rng)
        v = form_vector(f)
        g = form_from_vector(v * np.exp(1j * rng.random()) * 2.0)
        assert np.linalg.norm(np.abs(np.vdot(form_vector(g), v)) - 1) < 1e-9
        # exact column matches numeric vector up to scale
        col = form_exact_column(f)
        num = np.array([c.complex() for c in col])
        assert np.linalg.norm(num / math.sqrt(2 ** len(f["G"])) - v) < 1e-9
    # non-stabilizer vectors are rejected
    for m in (1, 2, 3):
        try:
            form_from_vector(target_vector(m))
            raise AssertionError("T^m accepted as stabilizer")
        except ValueError:
            pass
    # known decompositions: T^1 = 2 states, T^2 = 2 (|T>^2 = ... ), via annealing
    assert count_stabilizer_states(2) == 60 and len(list(all_forms(2))) == 60 and len(list(all_forms(3))) == 1080
    for m, r in ((1, 2), (2, 2), (3, 3)):
        best, vecs = anneal2(m, r, steps=20000, seed=1)
        assert best < 1e-9, (m, r, best)
        dec = decomposition_from_vectors(m, vecs)
        res = verify_decomposition(m, dec["states"])
        assert res["ok"], res
        print(f"m={m}: rank {r} decomposition found and verified exactly ({res})")
    assert count_stabilizer_states(4) == len(list(all_forms(4))) == 36720
    dec = t4_seed()
    res = verify_decomposition(4, dec["states"])
    assert res["ok"] and res["rank"] == 4, res
    print("m=4: rank 4 via cat4 table search + doubling, verified exactly", res)
    # record seed at m = 6
    seed = t6_seed()
    res = verify_decomposition(6, seed["states"])
    assert res["ok"] and res["rank"] == 6, res
    print("T^6 cat6 seed verified exactly:", res)
    # negative control: 5 random states at m = 4 are rejected
    rng = random.Random(7)
    res = verify_decomposition(4, [random_form(4, rng) for _ in range(5)])
    assert not res["ok"]
    print("selftest ok")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        selftest()
    elif len(sys.argv) > 1 and sys.argv[1] == "table":
        m, r, steps, seed = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
        t0 = time.time()
        tab = stabilizer_table(m)
        print(f"table m={m}: {len(tab[0])} states in {time.time() - t0:.0f}s", flush=True)
        e, vecs = table_search(m, r, tab, steps=steps, seed=seed, verbose=True)
        print(f"m={m} r={r}: best energy {e:.3e} in {time.time() - t0:.0f}s")
        if e < 1e-6:
            dec = decomposition_from_vectors(m, vecs, note=f"table_search m={m} r={r} steps={steps} seed={seed}")
            print("exact verification:", verify_decomposition(m, dec["states"]))
            json.dump(dec, open(f"dec_m{m}_r{r}_s{seed}.json", "w"))
    elif len(sys.argv) > 1 and sys.argv[1] == "anneal":
        m, r, steps, seed = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
        t0 = time.time()
        best, vecs = anneal(m, r, steps=steps, seed=seed, verbose=True)
        print(f"m={m} r={r}: best residual {best:.3e} in {time.time() - t0:.0f}s")
        if best < 1e-9:
            dec = decomposition_from_vectors(m, vecs, note=f"anneal m={m} r={r} steps={steps} seed={seed}")
            print("exact verification:", verify_decomposition(m, dec["states"]))
            json.dump(dec, open(f"dec_m{m}_r{r}_s{seed}.json", "w"))
    else:
        data = json.load(open(sys.argv[1], encoding="utf-8"))
        res = verify_decomposition(int(data["m"]), data["states"])
        print(res, "value =", RECORD.get(int(data["m"]), float("nan")) / res["rank"] if res["ok"] else 0)
