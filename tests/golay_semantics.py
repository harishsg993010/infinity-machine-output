"""Compare Golay.pullback (Lean) with a numpy computation of C^dagger P C on random 3-qubit circuits."""
import itertools, json, random, subprocess, sys
import numpy as np
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
rng = random.Random(1)
n = 3
names = ["h", "s", "sdg", "x", "y", "z", "cz", "cx"]
circs = []
for _ in range(40):
    C = []
    for _ in range(12):
        g = rng.choice(names)
        if g in ("cz", "cx"):
            a, b = rng.sample(range(n), 2); C.append((g, a, b))
        else:
            C.append((g, rng.randrange(n)))
    circs.append(C)
paulis = [(x, z) for x in range(8) for z in range(8)]
lean = "import InfinityMachineOutput.Golay.Basic\nopen Golay\n"
lean += "def tests : List (List Gate) := [" + ",".join("[" + ",".join(f".{g[0]} " + " ".join(map(str, g[1:])) for g in C) + "]" for C in circs) + "]\n"
lean += "def ps : List (Nat × Nat) := " + str(paulis).replace("(", "(").replace(" ", "") + "\n"
lean += '#eval IO.println (String.intercalate ";" (tests.flatMap fun C => ps.map fun (x, z) => let P := pullback C {x := x, z := z, r := 0}; s!"{P.x},{P.z},{P.r}"))\n'
(ROOT / "tests/Semantics.lean").write_text(lean, encoding="utf-8")
out = subprocess.run(["lake", "env", "lean", "tests/Semantics.lean"], cwd=ROOT, capture_output=True, text=True, shell=False)
vals = out.stdout.strip().split(";")
I = np.eye(2); X = np.array([[0, 1], [1, 0]]); Z = np.diag([1, -1]); H = (X + Z) / np.sqrt(2)
S = np.diag([1, 1j]); Y = 1j * X @ Z
def one(U, q):
    ops = [I] * n; ops[q] = U
    M = np.array([[1]]); [M := np.kron(M, o) for o in ops]  # qubit 0 = leftmost factor
    return M
def bitop(f):
    M = np.zeros((2**n, 2**n), complex)
    for b in range(2**n):
        bits = [(b >> (n - 1 - q)) & 1 for q in range(n)]
        nb, ph = f(bits); M[sum(v << (n - 1 - q) for q, v in enumerate(nb)), b] = ph
    return M
def gate(g):
    if g[0] == "cz": return bitop(lambda b: (b, (-1) ** (b[g[1]] & b[g[2]])))
    if g[0] == "cx":
        def f(b):
            b = list(b); b[g[2]] ^= b[g[1]]; return b, 1
        return bitop(f)
    return one({"h": H, "s": S, "sdg": S.conj().T, "x": X, "y": Y, "z": Z}[g[0]], g[1])
def pauli(x, z, r):
    M = np.array([[1]])
    for q in range(n):
        M = np.kron(M, np.linalg.matrix_power(X, (x >> q) & 1) @ np.linalg.matrix_power(Z, (z >> q) & 1))
    return (1j) ** r * M
k = 0; bad = 0
for C in circs:
    U = np.eye(2**n)
    for g in C: U = gate(g) @ U
    for (x, z) in paulis:
        lx, lz, lr = map(int, vals[k].split(",")); k += 1
        if not np.allclose(U.conj().T @ pauli(x, z, 0) @ U, pauli(lx, lz, lr)): bad += 1
print(f"{k} pullbacks compared, {bad} mismatches")
sys.exit(1 if bad or k != len(circs) * len(paulis) else 0)
