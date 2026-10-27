# Infinity Machine Results

Companion artifacts for **Infinity Machine**, a self-improving AI agent for research.

This repository collects the concrete results Infinity Machine produced on open problems in quantum information,
compilers, hardware design and astronomy. Each result with a finite certificate comes with a **Lean 4 proof** that
checks it. Every certificate is taken unchanged from its public deposit, and generator scripts turn it into a Lean
data file.

> 📝 Paper: *Infinity Machine: a self-improving AI agent for research* (H. Santhanalakshmi Ganesan, 2026), arXiv preprint in preparation.

## News

- **2026-10-26**: 🧾 **Lean 4 formalizations of five results**, all building from a clean checkout with no `sorry`:
  - **Golay preparation:** the 44-gate, depth-6 circuit provably prepares the `[[23,1,7]]` Golay logical zero.
  - **Stabilizer rank:** the 10-term decomposition of `|T⟩^⊗7` is exact over `ℤ[ζ₈]`.
  - **Qutrit channel:** its coherent information is positive at `p = 0.2910672`, by a pure Mathlib real-analysis proof.
  - **SABRE routing:** all 26 routings replay validly and add 12,087 gates.
  - **Chip:** the delivered INT8 MAC netlists compute exact signed dot products for every input.
- **2026-10-26**: 🔌 **Hardware.** Infinity Machine redesigned the RTL of an open 8×8 INT8 systolic tile. Energy per MAC
  fell from **578.9 fJ to 128.8 fJ** (−77.7%) and area by 55%, through a full open RTL-to-GDS flow in ASAP7 at 600 ps.
  The design is bit-exact; see [`Chip`](InfinityMachineOutput/Chip/).
- **2026-10-26**: 🤖 **Three fully autonomous runs.** Each went from a plain-text goal to a verified report with no human
  step, for $7.59–$9.97 per run. All three ended in honest ties with the public record (see
  [below](#fully-autonomous-runs)).
- **2026-10-25**: 🔭 **An unconfirmed planet candidate.** In open-ended discovery mode on TESS photometry of 7,474 nearby M
  dwarfs, Infinity Machine surfaced a **1.6 R⊕ transiting candidate on a 5.31-day orbit around G 249-11** (TIC 417732194,
  29 pc). The evidence is about 3σ, and two false-positive scenarios remain viable. Preprint:
  [doi:10.5281/zenodo.23651676](https://doi.org/10.5281/zenodo.23651676); details in
  [`discoveries/tess_g249_11/`](discoveries/tess_g249_11/).
- **2026-10-25**: 🧭 **SABRE routing deposited** ([doi:10.5281/zenodo.23651579](https://doi.org/10.5281/zenodo.23651579)):
  **12,087** added gates on the 26-circuit SABRE suite, against 68,559 for SABRE.
- **2026-10-20**: ⚛️ **Four quantum-information records**, each deposited on Zenodo:
  - **qubit depolarizing threshold:** `p = 0.064966`;
  - **qutrit positivity frontier:** `0.2910672`;
  - **Golay preparation:** a (44 gates, depth 6) circuit;
  - **stabilizer rank:** `χ(T^⊗7) ≤ 10`.

## Results

Each row compares the best prior published result (**Prev best**, from the cited source) against **Infinity Machine**.
Arrows mark the better direction (↓ lower is better, ↑ higher is better); the winning value is in bold. The **Lean**
column says what the proofs in this repository cover.

| Track | Task | Metric | Prev best | Infinity Machine | Lean |
|---|---|---|---|---|---|
| **Quantum information** | qubit depolarizing threshold ([Zenodo](https://doi.org/10.5281/zenodo.23484691)) | certified `p` with `Q > 0` ↑ | 0.064956 <sup>a</sup> | **0.064966** | — <sup>†</sup> |
| | [`qutrit_depolarizing`](InfinityMachineOutput/Qutrit/) ([Zenodo](https://doi.org/10.5281/zenodo.23492159)) | positivity frontier `p` ↑ | 0.2870867 <sup>b</sup> | **0.2910672** | ✅ |
| | [`golay_preparation`](InfinityMachineOutput/Golay/) ([Zenodo](https://doi.org/10.5281/zenodo.23509367)) | (two-qubit gates, depth) ↓ | (44, 8), (45, 7) <sup>c</sup> | **(44, 6)** | ✅ |
| | [`stabilizer_rank_T7`](InfinityMachineOutput/StabRank/) ([Zenodo](https://doi.org/10.5281/zenodo.23525753)) | `χ(T^⊗7)` upper bound ↓ | 12 <sup>d</sup> | **10** | ✅ |
| | depolarizing private information ([Zenodo](https://doi.org/10.5281/zenodo.23516558)) | explicit finite-`n` witness `p` ↑ | 0.28222 (`n = 1`) <sup>e</sup> | **0.28466** (`n = 8`) | — <sup>†</sup> |
| **Compilers** | [`sabre_qubit_routing`](InfinityMachineOutput/Sabre/) ([Zenodo](https://doi.org/10.5281/zenodo.23651579)) | added gates ↓ | 68,559 <sup>f</sup> | **12,087** | ✅ |
| | same, 15 circuits shared with later work | added gates ↓ | 13,044 <sup>g</sup> | **9,312** | ✅ <sup>‡</sup> |
| **Hardware** | [`int8_systolic_tile`](InfinityMachineOutput/Chip/) | energy per MAC ↓ | 578.9 fJ <sup>h</sup> | **128.8 fJ** | ✅ arithmetic <sup>§</sup> |
| **AI** | AdderBoard smallest adder | parameters ↓ | 6 (disputed), 10 strict <sup>i</sup> | **5** | — |
| **Astronomy** | [`tess_g249_11`](discoveries/tess_g249_11/) ([Zenodo](https://doi.org/10.5281/zenodo.23651676)) | new transiting candidates ↑ | — | **1 candidate, ~3σ, unconfirmed** | — <sup>¶</sup> |

<sup>†</sup> Not formalized:
* **Qubit threshold:** the certificate is a 45-qubit exact computation through a Schur–Weyl reduction, using a
  third-party certifier.
* **Private information:** the witnesses are 8-qubit ensembles certified at 30 digits.

<sup>¶</sup> An observational, statistical result: G 249-11 (TIC 417732194), P = 5.307425 d, Rp = 1.61 ± 0.09 R⊕. It is
not a confirmed planet, and there is no finite certificate to formalize. Two false positives remain viable: a bound
eclipsing companion, and a G = 17.2 star 20″ away.<br>
<sup>‡</sup> Covered by the same replay theorem. The per-circuit split comes from the deposit.<br>
<sup>§</sup> Lean proves the MAC arithmetic exact for all inputs. The energy figure is a physical measurement, not a theorem
(see [Lean verification](#lean-verification)).

**Prev-best sources.**

- <sup>a</sup> A. Krohn-Grimberghe, *A certified lower bound on the quantum-capacity threshold of the depolarizing channel*
  ([arXiv:2608.15870](https://arxiv.org/abs/2608.15870)); Open Quantum Problems catalogue entry C11.
- <sup>b</sup> The hashing bound (maximally mixed input), the documented frontier of QIQC Open Problem Zoo record
  `op_6690dfacb75e8dc0` ([github.com/Naixu-Guo/quantum-open-problems](https://github.com/Naixu-Guo/quantum-open-problems)).
- <sup>c</sup> Doherty et al., *Fast stabilizer state preparation via AI-optimized graph decimation*
  ([arXiv:2603.17743](https://arxiv.org/abs/2603.17743)); zoo record `op_c847b635f53b0812`.
- <sup>d</sup> Products of known smaller decompositions, as listed in zoo record `op_37f7b003ec78a028`.
- <sup>e</sup> The one-way six-state rate with noisy preprocessing (Renes–Smith 2007), a single-use private information;
  zoo record `op_d2813fe3fcdf09ad`.
- <sup>f</sup> G. Li, Y. Ding, Y. Xie, *Tackling the qubit mapping problem for NISQ-era quantum devices*, ASPLOS 2019
  ([arXiv:1809.02573](https://arxiv.org/abs/1809.02573)), Table II, on the 43-edge IBM Q20 Tokyo graph of its Fig. 2.
- <sup>g</sup> HAIL (Xu et al., 2025, [arXiv:2502.07536](https://arxiv.org/abs/2502.07536)), the best published counts on
  the 15 circuits reported by later routing papers.
- <sup>h</sup> The original RTL of the LogikBench 8×8 INT8 weight-stationary systolic array shipped with
  OpenROAD-flow-scripts, measured with the same flow (ASAP7, 600 ps clock, gate-level switching activity).
- <sup>i</sup> AdderBoard leaderboard ([github.com/anadim/AdderBoard](https://github.com/anadim/AdderBoard)).

**Metric notes.**

- **certified `p` with `Q > 0`**: largest per-Pauli depolarizing probability at which positive quantum capacity is
  certified by an explicit input state (maximize).
- **positivity frontier `p`**: largest replacement probability of the qutrit depolarizing channel
  `N(ρ) = (1−p)ρ + p·I/3` with certified positive coherent information (maximize).
- **(two-qubit gates, depth)**: two-qubit gate count and two-qubit depth of a Clifford circuit preparing the Golay
  logical zero from `|0⟩^⊗23` (minimize; single-qubit gates are free).
- **`χ(T^⊗7)`**: number of stabilizer states needed to write `|T⟩^⊗7` exactly (minimize; an upper bound only).
- **added gates**: gates inserted by SWAP routing, 3 per SWAP, with no other rewriting (minimize).
- **energy per MAC**: total power × clock period / 64 MACs per cycle, at a fixed 600 ps clock, bit-exact output
  (minimize).
- **parameters**: unique trainable parameters of a transformer that adds two 10-digit integers (minimize).

> **Note.** All claims are upper/lower bounds witnessed by explicit artifacts. No optimality or priority claim is made;
> the claim boundary of each result is in its deposit. Results current as of **2026-10-26**.

### Fully autonomous runs

These problems were chosen, specified, verified, audited and re-checked by the system itself, with no human step after
launch. None beat its record:

| Task | Metric | Public record | Infinity Machine | Cost |
|---|---|---|---|---|
| two-deletion-correcting binary code, `n = 16` | words ↑ | 223 (Einstein Arena problem 34) | 223 (tie) | $9.86 |
| sorting network, 31 inputs | comparators ↓ | 180 (Dobbelaere's tables) | 180 (tie) | $7.59 |
| mixed binary/ternary code `N(4,5,3)`, distance 3 | words ↑ | 186 (Brouwer et al. 1998) | 186 (tie) | $9.97 |

In the first run, the system's audit rejected its own task because the record it had cited was stale. In the second
run, the agent-written score pointed the wrong way, and none of the checks caught it.

## Lean verification

| File | Statement |
|---|---|
| [`Golay/Main.lean`](InfinityMachineOutput/Golay/Main.lean) | every one of the 23 stabilizer generators of the Golay logical zero stabilizes `circuit·|0⟩^⊗23`; 44 two-qubit gates, two-qubit depth 6; code dimension 12, minimum distance 7 |
| [`StabRank/Main.lean`](InfinityMachineOutput/StabRank/Main.lean) | `Σⱼ cⱼ vⱼ = 2^{7/2}|T⟩^⊗7` exactly in `ℤ[ζ₈]`; each `vⱼ` has exactly 128 stabilizing Pauli strings (a stabilizer state) |
| [`Qutrit/Main.lean`](InfinityMachineOutput/Qutrit/Main.lean) | `cohInfo 0.2910672 > 0` and `hashing 0.2910672 < 0`, from Mercator-series bounds on `Real.log` |
| [`Sabre/Main.lean`](InfinityMachineOutput/Sabre/Main.lean) | all 26 routings replay validly on the 43-edge Tokyo graph, and the total is 12,087 added gates |
| [`Chip/Mac.lean`](InfinityMachineOutput/Chip/Mac.lean), [`Chip/Main.lean`](InfinityMachineOutput/Chip/Main.lean) | for all inputs, the gate-level MAC netlists output `Σ aᵣwᵣ (+ psum)` mod `2^18` / `2^19`, and a column's signed result is the exact dot product |

**Methods.**

* **Golay, `χ(T⁷)`, SABRE:** checked by evaluation (`native_decide`).
* **Qutrit:** a Mathlib real-analysis proof. It uses only the standard axioms.
* **Chip:** the proof is split into four parts:
  * the Brent–Kung adder, by SAT (`bv_decide`);
  * the 3:2 / 2:2 compressor tree, by an exact `linear_combination` over its 235 and 252 counters;
  * the Baugh–Wooley products, exhaustively over all 65,536 cases;
  * an `omega` step that combines them.

**Checks on the checker.**

* [`tests/golay_semantics.py`](tests/golay_semantics.py) compares the Lean Pauli-conjugation rules with a numpy unitary
  computation: 2,560 cases, 0 mismatches.
* Each module rejects a corrupted certificate:
  * Golay: a gate dropped;
  * `χ(T⁷)`: any one term dropped;
  * SABRE: a gate reordered;
  * `|T⟩^⊗7` itself is shown not to be a stabilizer state.

**Trust base.**

* **Evaluation-based proofs** trust the Lean compiler as well as the kernel. Each such use shows up in `#print axioms` as
  an auxiliary `…._native.native_decide.ax_…` or `…._native.bv_decide.ax_…` axiom.
* **SAT steps:** `bv_decide` checks an LRAT certificate from CaDiCaL.
* **Axiom report:** [`scripts/Axioms.lean`](scripts/Axioms.lean) prints the axioms of every headline theorem.

**Not formalized.**

* **Background theory**, which each statement relies on (stated in the module docstrings):
  * the stabilizer formalism (independent commuting generators with fixed signs determine the state);
  * the spectra behind the qutrit closed form;
  * the LSD theorem;
  * the equivalence of order-preserving replays and circuits.
* **The chip:** the tile's sequential logic, which was checked by gate-level simulation on the benchmark workload, and
  its energy measurement.
* **Two certificates:** the qubit threshold and the private-information witnesses.

**Note on the SABRE graph.** The routings are valid on the 43-edge Tokyo graph drawn in the SABRE paper, which is what
SABRE's own numbers use. They are not valid on Qiskit's 35-edge `FakeTokyo`, which is the real device with dead couplers.

## Build

```
lake exe cache get      # Mathlib
lake build              # all proofs; the chip module needs > 32 GB RAM
lake env lean scripts/Axioms.lean
```

Or build in a clean container with `modal run scripts/modal_build.py`. The last clean build ran on 16 vCPU with Lean and
Mathlib `v4.36.0-rc1`: 18,136 jobs in 27 min.

```
InfinityMachineOutput/   Lean sources (Golay, StabRank, Qutrit, Sabre, Chip)
data/                    certificates from the deposits, plus the chip RTL
discoveries/             results with no finite certificate (TESS planet candidate)
scripts/gen_*.py         deterministic generators: data/ -> Lean data files
tests/                   independent cross-checks
```

## Citation

If you use these results, please cite:

```bibtex
@misc{infinitymachine2026,
  title        = {Infinity Machine: a self-improving {AI} agent for research},
  author       = {Santhanalakshmi Ganesan, Harish},
  year         = {2026},
  howpublished = {\url{https://github.com/harishsg993010/infinity-machine-output}},
}
```

## License

Code (Lean sources and scripts) is licensed under the Apache License, Version 2.0; see [`LICENSE`](LICENSE).
Certificates in `data/` are CC BY 4.0, as in their Zenodo deposits.
