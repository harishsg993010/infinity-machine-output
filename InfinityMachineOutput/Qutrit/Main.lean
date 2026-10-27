import Mathlib

/-!
# The qutrit depolarizing channel has positive coherent information at `p = 0.2910672`

The channel is `N_p(ρ) = (1-p) ρ + p I/3` on `ℂ³`. The input is `σ₂ = P₂/2`, maximally mixed on a
two-dimensional subspace. Its purification `|Φ⟩` lives on `ℂ² ⊗ ℂ³`.

Spectra, read off directly in a basis adapted to `P₂`:
* output `N_p(σ₂)`: eigenvalue `a = (1-p)/2 + p/3` twice and `b = p/3` once;
* joint `(id ⊗ N_p)(|Φ⟩⟨Φ|) = (1-p)|Φ⟩⟨Φ| + p · I/2 ⊗ I/3`: eigenvalue `c = 1 - p + p/6` once
  (on `|Φ⟩`) and `e = p/6` five times.

So the coherent information, in nats, is

  `I(p) = 2η(a) + η(b) - η(c) - 5η(e)`,   `η(x) = -x log x`.

**Proved here:** `I(2910672/10⁷) > 0`.

The hashing (maximally mixed) input gives `log 3 - η((1-p) + p/9) - 8η(p/9)`, which is negative
at the same `p`. So at `p = 0.2910672` the rank-2 input beats hashing, and the previously
documented frontier 0.2870867 moves to 0.2910672.

The spectra above and the step "positive coherent information at `p` ⇒ `Q(N_p) > 0`
(LSD theorem)" are standard and are not formalized. The step "⇒ for all smaller `p`" uses the
fact that `N_p` is a degradation of `N_{p'}` for `p' < p` (composition of depolarizing
channels); it is not formalized either.
-/

namespace Qutrit

open Real Finset

noncomputable def η (x : ℝ) : ℝ := -x * log x

noncomputable def cohInfo (p : ℝ) : ℝ :=
  2 * η ((1 - p) / 2 + p / 3) + η (p / 3) - η (1 - p + p / 6) - 5 * η (p / 6)

noncomputable def hashing (p : ℝ) : ℝ :=
  log 3 - η ((1 - p) + p / 9) - 8 * η (p / 9)

/-- `log (1 - x)` from the Mercator series, truncated after `n` terms. -/
lemma log_one_sub_bounds {x : ℝ} (h : |x| < 1) (n : ℕ) :
    -(∑ i ∈ range n, x ^ (i + 1) / (i + 1)) - |x| ^ (n + 1) / (1 - |x|) ≤ log (1 - x) ∧
    log (1 - x) ≤ -(∑ i ∈ range n, x ^ (i + 1) / (i + 1)) + |x| ^ (n + 1) / (1 - |x|) := by
  have := abs_log_sub_add_sum_range_le h n
  rw [abs_le] at this
  constructor <;> linarith [this.1, this.2]

def p₀ : ℚ := 2910672 / 10000000

theorem cohInfo_pos : 0 < cohInfo (p₀ : ℝ) := by
  have hp : ((p₀ : ℚ) : ℝ) = 2910672 / 10000000 := by norm_num [p₀]
  obtain ⟨P, hP⟩ : ∃ P : ℝ, P = 2910672 / 10000000 := ⟨_, rfl⟩
  rw [hp, ← hP]
  -- the four eigenvalues: a = (1 - P/3)/2, b = (8P/3)/8, c = 1 - 5P/6, e = (8P/3)/16
  have ha : log ((1 - P) / 2 + P / 3) = log (1 - P / 3) - log 2 := by
    rw [← log_div (by rw [hP]; norm_num) (by norm_num)]; congr 1; ring
  have hb : log (P / 3) = log (1 - (1 - 8 * P / 3)) - 3 * log 2 := by
    rw [show (3 : ℝ) * log 2 = log (2 ^ 3) by rw [log_pow]; norm_num,
      ← log_div (by rw [hP]; norm_num) (by norm_num)]; congr 1; ring
  have he : log (P / 6) = log (1 - (1 - 8 * P / 3)) - 4 * log 2 := by
    rw [show (4 : ℝ) * log 2 = log (2 ^ 4) by rw [log_pow]; norm_num,
      ← log_div (by rw [hP]; norm_num) (by norm_num)]; congr 1; ring
  have hc : 1 - P + P / 6 = 1 - 5 * P / 6 := by ring
  obtain ⟨l1, u1⟩ := log_one_sub_bounds (x := P / 3)
    (by rw [hP, abs_lt]; constructor <;> norm_num) 18
  obtain ⟨l2, u2⟩ := log_one_sub_bounds (x := 1 - 8 * P / 3)
    (by rw [hP, abs_lt]; constructor <;> norm_num) 18
  obtain ⟨l3, u3⟩ := log_one_sub_bounds (x := 5 * P / 6)
    (by rw [hP, abs_lt]; constructor <;> norm_num) 18
  have t1 := log_two_gt_d9
  have t2 := log_two_lt_d9
  simp only [cohInfo, η]
  rw [ha, hb, he, hc]
  generalize log (1 - P / 3) = L1 at *
  generalize log (1 - (1 - 8 * P / 3)) = L2 at *
  generalize log (1 - 5 * P / 6) = L3 at *
  generalize log 2 = L at *
  subst hP
  norm_num [Finset.sum_range_succ, abs_of_pos] at l1 u1 l2 u2 l3 u3 ⊢
  linarith

theorem hashing_neg : hashing (p₀ : ℝ) < 0 := by
  have hp : ((p₀ : ℚ) : ℝ) = 2910672 / 10000000 := by norm_num [p₀]
  obtain ⟨P, hP⟩ : ∃ P : ℝ, P = 2910672 / 10000000 := ⟨_, rfl⟩
  rw [hp, ← hP]
  have h3 : log 3 = log (1 - 1 / 4) + 2 * log 2 := by
    rw [show (2 : ℝ) * log 2 = log (2 ^ 2) by rw [log_pow]; norm_num,
      ← log_mul (by norm_num) (by norm_num)]; norm_num
  have hc : 1 - P + P / 9 = 1 - 8 * P / 9 := by ring
  have he : log (P / 9) = log (1 - (1 - 32 * P / 9)) - 5 * log 2 := by
    rw [show (5 : ℝ) * log 2 = log (2 ^ 5) by rw [log_pow]; norm_num,
      ← log_div (by rw [hP]; norm_num) (by norm_num)]; congr 1; ring
  obtain ⟨l0, u0⟩ := log_one_sub_bounds (x := 1 / 4) (by rw [abs_lt]; constructor <;> norm_num) 18
  obtain ⟨l1, u1⟩ := log_one_sub_bounds (x := 8 * P / 9)
    (by rw [hP, abs_lt]; constructor <;> norm_num) 18
  obtain ⟨l2, u2⟩ := log_one_sub_bounds (x := 1 - 32 * P / 9)
    (by rw [hP, abs_lt]; constructor <;> norm_num) 18
  have t1 := log_two_gt_d9
  have t2 := log_two_lt_d9
  simp only [hashing, η]
  rw [h3, hc, he]
  generalize log (1 - 1 / 4) = L0 at *
  generalize log (1 - 8 * P / 9) = L1 at *
  generalize log (1 - (1 - 32 * P / 9)) = L2 at *
  generalize log 2 = L at *
  subst hP
  norm_num [Finset.sum_range_succ, abs_of_pos, abs_of_neg] at l0 u0 l1 u1 l2 u2 ⊢
  linarith

end Qutrit
