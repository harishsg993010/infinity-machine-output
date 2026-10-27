import InfinityMachineOutput

/-! Run with `lake env lean scripts/Axioms.lean` after `lake build`: lists the axioms each headline
theorem depends on. Expect `propext`, `Classical.choice`, `Quot.sound`, and, for theorems checked
by evaluation (`native_decide`, `bv_decide`), `Lean.ofReduceBool` (trust in the compiler). -/

#print axioms Golay.circuit_prepares_golay_zero
#print axioms Golay.min_distance
#print axioms Golay.circuit_two_qubit_depth
#print axioms StabRank.decomposition_exact
#print axioms StabRank.each_is_stabilizer_state
#print axioms Qutrit.cohInfo_pos
#print axioms Qutrit.hashing_neg
#print axioms Sabre.all_routings_valid
#print axioms Sabre.total_added_gates
#print axioms Chip.mac_s0_correct
#print axioms Chip.mac_s1_correct
#print axioms Chip.column_exact
