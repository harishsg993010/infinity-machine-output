import InfinityMachineOutput.StabRank.Data

/-!
# Stabilizer rank of `|T⟩^{⊗7}` is at most 10

`|T⟩ = (|0⟩ + e^{iπ/4}|1⟩)/√2`. The deposited decomposition writes `2^{7/2}|T⟩^{⊗7}` as a
`ℚ(ζ₈)`-linear combination of 10 vectors given in stabilizer normal form. The previous best
upper bound was 12.

Checked here, by evaluation in exact `ℤ[ζ₈]` arithmetic (no floating point):
* `decomposition_exact`: `∑ⱼ (4cⱼ) vⱼ = 4 · 2^{7/2}|T⟩^{⊗7}` entry by entry, all 128 amplitudes;
* `each_is_stabilizer_state`: each `vⱼ` is nonzero and exactly `2^7 = 128` Hermitian Pauli
  strings `P` satisfy `P vⱼ = ± vⱼ`, so each `vⱼ` is a stabilizer state (up to normalization);
* `each_support_full_rank`: each `G` has full row rank, as the normal form requires.

Hence `χ(T^{⊗7}) ≤ 10`.
-/

namespace StabRank

def vecs : List Vec := forms.map (Form.vec m)

theorem ten_terms : forms.length = 10 ∧ coeffs.length = 10 := by native_decide

theorem decomposition_exact :
    combo m coeffs vecs = (target m).map (Z8.smul denom) := by native_decide

theorem each_is_stabilizer_state :
    vecs.all (fun v => nonzero v && stabilizerCount m v == 2 ^ m) = true := by native_decide

theorem each_support_full_rank : forms.all (fun f => rank f.G == f.G.length) = true := by
  native_decide

/-- Sanity check of the checker: `|T⟩^{⊗7}` itself is not a stabilizer state. -/
theorem target_not_stabilizer : stabilizerCount m (target m) < 2 ^ m := by native_decide

/-- Sanity check of the checker: dropping any one term breaks the identity. -/
theorem nine_terms_fail :
    (List.range 10).all (fun i =>
      combo m (coeffs.eraseIdx i) (vecs.eraseIdx i) != (target m).map (Z8.smul denom)) = true := by
  native_decide

end StabRank
