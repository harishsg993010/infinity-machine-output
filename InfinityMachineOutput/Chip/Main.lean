import InfinityMachineOutput.Chip.Mac

/-!
# The energy-optimised 8×8 INT8 systolic tile computes exact dot products

The tile was produced by the Infinity Machine chip run (`data/chip/tpu.sv`, `data/chip/mac.sv`).
Energy per MAC fell from 578.9 to 128.8 fJ in ASAP7 at 600 ps. The arithmetic was rewritten from
Yosys `*`/`+` into explicit Baugh-Wooley partial products, a 3:2 / 2:2 compressor tree and a
Brent-Kung adder. Each column of the array is split into two such stages of four rows.

`mac_s0_correct` and `mac_s1_correct` (in `Mac.lean`, generated from the delivered gate-level
netlist) prove, for **all** inputs:
* stage 0 outputs `Σ_{r<4} a_r w_r mod 2^18`;
* stage 1 outputs `psum + Σ_{4≤r<8} a_r w_r mod 2^19`.

`column_exact` below shows that the 19-bit result, sign-extended to 32 bits as the tile does,
equals the exact integer dot product. That holds because `|Σ_{r<8} a_r w_r| ≤ 8 · 2^14 < 2^18`,
so no information is lost modulo `2^19`.

Not covered: the clocking, clock gating, delay lines and registers of `tpu.sv`. Those were
checked bit-exactly by gate-level simulation on the benchmark workload, not proved.
-/

namespace Chip

/-- Reading a `w`-bit unsigned value `u ∈ [0, 2^w)` as two's complement. This is `BitVec.toInt`
on the bits, and it is how the tile reads the stage-0 register (`psum_north`) and the 19-bit
result (sign-extended to 32 bits). -/
def signed (w : ℕ) (u : ℤ) : ℤ := if u < 2 ^ (w - 1) then u else u - 2 ^ w

/-- One output column. `X0` and `X1` are the exact sums over rows 0–3 and rows 4–7. If stage 0
outputs `u0 = X0 mod 2^18` and stage 1 outputs `u1 = (signed u0 + X1) mod 2^19`, as
`mac_s0_correct` and `mac_s1_correct` prove, then the signed 19-bit result is the exact dot
product `X0 + X1`. -/
theorem column_exact (X0 X1 u0 u1 : ℤ)
    (hX0 : -(4 * 2 ^ 14) ≤ X0 ∧ X0 ≤ 4 * 2 ^ 14) (hX1 : -(4 * 2 ^ 14) ≤ X1 ∧ X1 ≤ 4 * 2 ^ 14)
    (h0 : u0 = X0 % 2 ^ 18) (h1 : u1 = (signed 18 u0 + X1) % 2 ^ 19) :
    signed 19 u1 = X0 + X1 := by
  unfold signed at *
  norm_num at *
  split_ifs at * <;> omega

/-- Each signed INT8 product lies in `[-2^14 + 128, 2^14]`, so four of them are bounded by
`4 · 2^14`, as `column_exact` needs. -/
theorem product_bound : ∀ a w : BitVec 8,
    -(2 ^ 14) ≤ a.toInt * w.toInt ∧ a.toInt * w.toInt ≤ 2 ^ 14 := by
  native_decide

end Chip
