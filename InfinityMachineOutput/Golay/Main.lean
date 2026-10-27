import InfinityMachineOutput.Golay.Circuit

/-!
# A 44-gate, two-qubit-depth-6 preparation of the Golay logical zero

Let `C` be the binary cyclic `[23,12,7]` Golay code with generator polynomial
`g(x) = 1 + x² + x⁴ + x⁵ + x⁶ + x¹⁰ + x¹¹` (coordinate `i` ↔ `xⁱ` ↔ bit `i`), and
`|0_G⟩ ∝ ∑_{c ∈ C⊥} |c⟩` the logical zero of the `[[23,1,7]]` Golay code.
`|0_G⟩` is the unique state stabilized by `X(c')` for `c' ∈ C⊥` and `Z(c)` for `c ∈ C`;
it suffices to check 11 + 12 = 23 independent generators.

The theorems below check, by evaluation:
* the code facts (`C` has dimension 12 and minimum distance 7; `C⊥` is spanned by the 11
  given rows);
* that `circuit` maps each of the 23 generators back to a `+Z`-string, i.e. every generator
  stabilizes `circuit |0⟩^⊗23`;
* that `circuit` has 44 two-qubit gates and two-qubit depth 6.

The step "23 independent commuting stabilizers with signs fixed ⇒ the state is `|0_G⟩` up to
a global phase" is the standard stabilizer-formalism fact; it is not formalized here.
-/

namespace Golay

def n : Nat := 23

/-- `g(x) = 1 + x² + x⁴ + x⁵ + x⁶ + x¹⁰ + x¹¹`. -/
def gpoly : Nat := [0, 2, 4, 5, 6, 10, 11].foldl (fun m i => m ||| (1 <<< i)) 0

/-- Generators `xⁱ g(x)`, `i = 0..11`, of the cyclic Golay code `C`. -/
def codeGens : List Nat := (List.range 12).map (gpoly <<< ·)

/-- `(1 + x) g(x)`: generates the even-weight subcode, which is `C⊥`. -/
def dualPoly : Nat := gpoly ^^^ (gpoly <<< 1)

/-- Generators `xⁱ (1+x) g(x)`, `i = 0..10`, of `C⊥`. -/
def dualGens : List Nat := (List.range 11).map (dualPoly <<< ·)

/-- The 23 stabilizer generators of `|0_G⟩`, all with phase `+1`. -/
def stabGens : List Pauli :=
  dualGens.map (fun c => { x := c, z := 0, r := 0 }) ++
  codeGens.map (fun c => { x := 0, z := c, r := 0 })

theorem code_dim : rank codeGens = 12 := by native_decide
theorem dual_dim : rank dualGens = 11 := by native_decide
theorem dual_orthogonal : dualGens.all (fun u => codeGens.all (fun v => dot u v == 0)) = true := by
  native_decide

/-- Every nonzero codeword of `C` has weight at least 7, and weight 7 occurs. -/
theorem min_distance :
    ((span codeGens).all (fun c => c == 0 || weight c ≥ 7)) = true ∧
    ((span codeGens).any (fun c => weight c == 7)) = true := by
  native_decide

theorem codewords_fit : (codeGens ++ dualGens).all (· < 2 ^ n) = true := by native_decide

/-- The 23 generators are independent (X part and Z part separately). -/
theorem gens_independent :
    rank (stabGens.map (fun P => (P.x <<< n) ||| P.z)) = n := by native_decide

theorem gens_commute : stabGens.all (fun P => stabGens.all (commute P)) = true := by native_decide

theorem circuit_wellFormed : wellFormed n circuit = true := by native_decide

/-- Every Golay stabilizer generator stabilizes `circuit |0⟩^⊗23`. -/
theorem circuit_prepares_golay_zero : stabGens.all (stabilizes circuit) = true := by native_decide

theorem circuit_two_qubit_gates : twoQubitCount circuit = 44 := by native_decide

theorem circuit_two_qubit_depth : twoQubitDepth n circuit = 6 := by native_decide

/-- Sanity check of the checker: dropping the last two-qubit gate breaks the preparation. -/
def dropLastTwoQubit (C : List Gate) : List Gate :=
  let i := (C.zipIdx.filter (fun p => isTwoQubit p.1)).getLast?.map (·.2) |>.getD 0
  C.eraseIdx i

theorem checker_rejects_truncated :
    stabGens.all (stabilizes (dropLastTwoQubit circuit)) = false := by native_decide

end Golay
