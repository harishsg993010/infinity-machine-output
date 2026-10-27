"""Regenerate qft_13.qasm and qft_20.qasm (not in the Zulehner-Paler-Wille repository).

Generator inferred from qft_10.qasm / qft_16.qasm of that repository: for each qubit i, a Hadamard, then for every
j > i the controlled-phase decomposition rz(-a) q[i]; cx q[i],q[j]; rz(a) q[i]; cx q[i],q[j] with a = 0.7854/2^(j-i-1) (pi/4 rounded, then halved);
finally a Hadamard on every qubit. Angles are printed with 5 significant digits. These two files therefore do NOT
match the SABRE paper's qft_13 / qft_20 (403 / 970 gates there, 338 / 800 here).

    python gen_qft.py 13 16 > qft_13.qasm      (register width 16, as in the file used for the paper)
    python gen_qft.py 20 > qft_20.qasm
Both outputs are identical to the benchmark files used here (modulo line endings).
"""
import sys


def qft(n: int, width: int) -> str:
    out = ['OPENQASM 2.0;', 'include "qelib1.inc";', f"qreg q[{width}];", f"creg c[{width}];"]
    for i in range(n):
        out.append(f"h q[{i}];")
        for j in range(i + 1, n):
            a = f"{0.7854 / 2 ** (j - i - 1):.5g}"
            out += [f"rz(-{a}) q[{i}];", f"cx q[{i}],q[{j}];", f"rz({a}) q[{i}];", f"cx q[{i}],q[{j}];"]
    out += [f"h q[{i}];" for i in range(n)]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    n = int(sys.argv[1])
    sys.stdout.write(qft(n, int(sys.argv[2]) if len(sys.argv) > 2 else n))
