# Infinity Machine — machine-checked outputs

Lean 4 proofs of the results produced by the **Infinity Machine**, a self-improving AI research agent
(paper: *Infinity Machine: a self-improving AI agent for research*). Each result's certificate is taken
unchanged from its public Zenodo deposit and checked in Lean.

| result | statement checked in Lean | file | method |
|---|---|---|---|
| **Golay state preparation** ([Zenodo 10.5281/zenodo.23509367](https://doi.org/10.5281/zenodo.23509367)) | the 44-gate circuit maps every one of the 23 stabilizer generators of the `[[23,1,7]]` Golay logical zero to a `+Z`-string, so it prepares that state; it has 44 two-qubit gates and two-qubit depth 6; the code has dimension 12 and minimum distance 7 | `Golay/Main.lean` | Heisenberg-picture Pauli simulation, by evaluation |
| **Stabilizer rank χ(T^⊗7) ≤ 10** (was 12; [10.5281/zenodo.23525753](https://doi.org/10.5281/zenodo.23525753)) | `Σⱼ cⱼ vⱼ = 2^{7/2}|T⟩^⊗7` exactly in `ℤ[ζ₈]`, all 128 amplitudes; each `vⱼ` has exactly 128 stabilizing Pauli strings, so it is a stabilizer state; dropping any term breaks the identity | `StabRank/Main.lean` | exact cyclotomic arithmetic, by evaluation |
| **Qutrit depolarizing channel, frontier 0.2910672** ([10.5281/zenodo.23492159](https://doi.org/10.5281/zenodo.23492159)) | the closed-form coherent information of the rank-2 input is `> 0` at `p = 0.2910672`, and the hashing value is `< 0` there | `Qutrit/Main.lean` | real analysis in Mathlib (Mercator series bounds on `Real.log`), no evaluation |
| **SABRE qubit routing on IBM Q20 Tokyo** ([10.5281/zenodo.23651580](https://doi.org/10.5281/zenodo.23651580)) | all 26 deposited routings replay validly (every gate exactly once, per-qubit order preserved, every two-qubit gate and SWAP on a coupler); the total is **12,087** added gates, against 68,559 in the SABRE paper | `Sabre/Main.lean` | exact replay, by evaluation |
| **Energy-optimised 8×8 INT8 systolic tile** (578.9 → 128.8 fJ/MAC) | for **all** inputs, the delivered gate-level MAC netlists compute `Σ aᵣwᵣ (+ psum)` modulo `2^18` / `2^19`; a column's signed 19-bit result is the exact dot product | `Chip/Mac.lean`, `Chip/Main.lean` | Brent-Kung adder by SAT (`bv_decide`), compressor tree by `linear_combination`, Baugh-Wooley products exhaustively (65,536 cases), combined by `omega` |

The **headline numbers themselves** are what Lean checks: the gate counts and depth, the 10 terms, the
coherent information's sign, the 12,087 gates, and the bit-exact arithmetic. Each result's
optimality/novelty claim, as stated in its deposit, is a literature comparison and is not a theorem here.

## What is not formalized (and why)

* **The background theory each certificate relies on**:
  * the stabilizer formalism ("23 independent commuting generators with fixed signs determine the state");
  * the Dehaene–De Moor normal form (also checked directly through the Pauli count);
  * the spectra behind the qutrit closed form;
  * the LSD theorem (coherent information > 0 ⇒ quantum capacity > 0);
  * the equivalence of order-preserving replays and circuits.

  These are textbook results stated in the module docstrings.
* **The chip tile's sequential logic.** Clock gating, delay lines and registers in `tpu.sv` are not proved; they were checked
  bit-exactly by gate-level simulation. The **energy** figure comes from a physical flow (OpenROAD, ASAP7, SPEF-annotated
  power analysis) and is a measurement, not a theorem.
* **Qubit depolarizing threshold p = 0.064966** ([10.5281/zenodo.23484691](https://doi.org/10.5281/zenodo.23484691)). The
  certificate evaluates a 45-qubit coherent information through a Schur–Weyl block decomposition, with
  224-bit square-root enclosures and Gershgorin bounds. Formalizing that reduction is a research project in its own right.
  The certificate is an exact-arithmetic Python certifier by a third party (Krohn-Grimberghe), run unchanged.
* **Private-information witnesses for the qubit depolarizing channel.** These are explicit
  8-qubit ensembles evaluated numerically and certified with mpmath. Not formalized.

## Trust base

Theorems marked "by evaluation" use `native_decide` or `bv_decide`. They trust the Lean compiler
in addition to the kernel; each such use appears in `#print axioms` as an auxiliary axiom named
`…._native.native_decide.ax_…` or `…._native.bv_decide.ax_…`. `scripts/Axioms.lean` prints the
axioms of every headline theorem.

`bv_decide` checks an LRAT proof produced by CaDiCaL. `Qutrit.cohInfo_pos`, `Qutrit.hashing_neg`
and `Chip.column_exact` use only the standard axioms (`propext`, `Classical.choice`, `Quot.sound`).
No theorem uses `sorry`.

The last clean build ran on Modal (16 vCPU), with Lean `v4.36.0-rc1` and Mathlib `v4.36.0-rc1`:
`lake build` completed successfully (18,136 jobs) in 27 min wall time.

The definitions are the specification: read `*/Basic.lean` and the docstrings of `*/Main.lean`.
Independent cross-checks:

* `tests/golay_semantics.py` compares the Lean Pauli-conjugation rules against a numpy unitary
  computation: 2,560 cases, 0 mismatches.
* Each module has a negative test showing the checker rejects a corrupted certificate:
  * Golay: one gate dropped;
  * χ(T⁷): any one term dropped;
  * SABRE: a gate reordered;
  * `|T⟩^⊗7` itself is shown not to be a stabilizer state.

## Layout

```
InfinityMachineOutput/       Lean sources (Golay, StabRank, Qutrit, Sabre, Chip)
data/                        certificates copied from the Zenodo deposits (+ chip RTL)
scripts/gen_*.py             generators: data/ -> Lean data files (deterministic)
scripts/Axioms.lean          axiom report
scripts/modal_build.py       clean-room build on Modal (the chip proof needs ~>32 GB RAM)
tests/                       independent cross-checks
```

## Build

```
lake exe cache get    # Mathlib
lake build            # all proofs; the chip module needs a large-memory machine
lake env lean scripts/Axioms.lean
```

or `modal run scripts/modal_build.py` to build in a clean container.

Data: CC BY 4.0, as in the original deposits. Author: Harish Santhanalakshmi Ganesan.
