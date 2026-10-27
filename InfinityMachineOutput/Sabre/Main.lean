import InfinityMachineOutput.Sabre.Data

/-!
# SABRE benchmarks on Tokyo: 12,087 added gates

All 26 deposited routings replay validly on the 43-edge Tokyo graph. Together they add
12,087 gates (4,029 SWAPs). The SABRE paper's Table II reports 68,559 added gates on the same
benchmarks; that figure is the published reference (`sabreRef`), not something proved here.
-/

namespace Sabre

theorem tokyo_has_43_edges : tokyoEdges.length = 43 ∧ tokyoEdges.eraseDups.length = 43 := by
  native_decide

theorem twenty_six_benchmarks : instances.length = 26 := by native_decide

/-- Every routing is valid. -/
theorem all_routings_valid : instances.all (fun I => I.addedGates.isSome) = true := by
  native_decide

/-- Total added gates over the 26 benchmarks. -/
theorem total_added_gates :
    (instances.map (fun I => I.addedGates.getD 0)).sum = 12087 := by native_decide

/-- The published SABRE total on the same benchmarks, which is the comparison point. -/
theorem sabre_reference_total : (instances.map (·.sabreRef)).sum = 68559 := by native_decide

/-- Sanity check of the checker: moving the first two-qubit gate of `qft_10` before its
predecessors is rejected. -/
theorem checker_rejects_reordering :
    (instances.find? (·.name == "qft_10")).map (fun I =>
      let ops := parseOps I.ops
      let gs := parseGates I.gates
      let i := (ops.findIdx? fun | .gate g => (gs[g]!).length == 2 | _ => false).getD 0
      let op := ops[i]!
      replay I.n gs I.mapping (op :: ops.eraseIdx i)) = some none := by
  native_decide

end Sabre
