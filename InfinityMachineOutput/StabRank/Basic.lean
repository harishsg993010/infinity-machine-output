/-!
# Exact arithmetic in `ℤ[ζ₈]` and stabilizer states in quadratic-form representation

`Z8` is `c₀ + c₁ζ + c₂ζ² + c₃ζ³` with `ζ = e^{iπ/4}`, `ζ⁴ = -1`, integer coordinates.

A *form* `(x₀, G, a, B)` on `m` qubits with `k = |G|` rows describes the (unnormalized) vector

  `v(x) = ∑_{y ∈ 𝔽₂ᵏ, x₀ + yG = x} i^{a·y + 2 ∑_{i<j} B_ij y_i y_j}`,

the Dehaene–De Moor normal form of a stabilizer state (affine support, quadratic phase).
Independently of that theorem, `stabilizerCount` counts the Hermitian Pauli strings `P` with
`P v = ± v`; a nonzero vector whose count is `2^m` is a stabilizer state.
-/

namespace StabRank

structure Z8 where
  c0 : Int
  c1 : Int
  c2 : Int
  c3 : Int
  deriving Repr, DecidableEq, Inhabited

namespace Z8
def zero : Z8 := ⟨0, 0, 0, 0⟩
instance : Add Z8 := ⟨fun a b => ⟨a.c0 + b.c0, a.c1 + b.c1, a.c2 + b.c2, a.c3 + b.c3⟩⟩
instance : Neg Z8 := ⟨fun a => ⟨-a.c0, -a.c1, -a.c2, -a.c3⟩⟩
instance : Mul Z8 := ⟨fun a b =>
  ⟨a.c0*b.c0 - a.c1*b.c3 - a.c2*b.c2 - a.c3*b.c1,
   a.c0*b.c1 + a.c1*b.c0 - a.c2*b.c3 - a.c3*b.c2,
   a.c0*b.c2 + a.c1*b.c1 + a.c2*b.c0 - a.c3*b.c3,
   a.c0*b.c3 + a.c1*b.c2 + a.c2*b.c1 + a.c3*b.c0⟩⟩
/-- `ζ^e`. -/
def zpow (e : Nat) : Z8 :=
  let s : Int := if e % 8 < 4 then 1 else -1
  match e % 4 with
  | 0 => ⟨s, 0, 0, 0⟩
  | 1 => ⟨0, s, 0, 0⟩
  | 2 => ⟨0, 0, s, 0⟩
  | _ => ⟨0, 0, 0, s⟩
def smul (k : Int) (a : Z8) : Z8 := ⟨k*a.c0, k*a.c1, k*a.c2, k*a.c3⟩
end Z8

abbrev Vec := Array Z8

def popcount (v : Nat) : Nat := (List.range (v.log2 + 1)).countP (v.testBit ·)

structure Form where
  x0 : Nat
  G : List Nat
  a : List Nat
  B : List (List Nat)
  deriving Repr

/-- The vector of a form, unnormalized: entries `i^e = ζ^{2e}` on the support. -/
def Form.vec (m : Nat) (f : Form) : Vec := Id.run do
  let k := f.G.length
  let mut v : Vec := Array.replicate (2 ^ m) Z8.zero
  for y in List.range (2 ^ k) do
    -- y_i is the bit `k-1-i` of `y` (row 0 is the most significant), as in the deposited checker
    let yb : List Nat := (List.range k).map (fun i => if y.testBit (k - 1 - i) then 1 else 0)
    let mut x := f.x0
    let mut e := 0
    for i in List.range k do
      if yb[i]! = 1 then
        x := x ^^^ f.G[i]!
        e := e + f.a[i]!
        for j in List.range k do
          if i < j && yb[j]! = 1 && (f.B[i]!)[j]! != 0 then e := e + 2
    v := v.modify x (· + Z8.zpow (2 * (e % 4)))
  return v

/-- `2^{m/2} |T⟩^{⊗m}`: amplitude `ζ^{|x|}` at `|x⟩`. -/
def target (m : Nat) : Vec := (Array.range (2 ^ m)).map (fun x => Z8.zpow (popcount x))

/-- `∑ⱼ cⱼ vⱼ`. -/
def combo (m : Nat) (cs : List Z8) (vs : List Vec) : Vec :=
  (cs.zip vs).foldl (fun acc (c, v) => (acc.zip v).map (fun (s, t) => s + c * t))
    (Array.replicate (2 ^ m) Z8.zero)

/-- Apply the Hermitian Pauli string `i^{|x ∧ z|} X^x Z^z`. -/
def applyPauli (x z : Nat) (v : Vec) : Vec :=
  let ph := Z8.zpow (2 * (popcount (x &&& z) % 4))
  (Array.range v.size).map fun b =>
    let c := b ^^^ x
    let s := if popcount (z &&& c) % 2 = 0 then v[c]! else -v[c]!
    ph * s

def isPlusMinusEigen (P v : Vec) : Bool := P == v || P == v.map (- ·)

/-- Number of Hermitian Pauli strings `P` (no sign) with `P v = ± v`. -/
def stabilizerCount (m : Nat) (v : Vec) : Nat :=
  (List.range (2 ^ m)).foldl (fun acc x =>
    (List.range (2 ^ m)).foldl (fun acc z =>
      if isPlusMinusEigen (applyPauli x z v) v then acc + 1 else acc) acc) 0

def nonzero (v : Vec) : Bool := v.any (· != Z8.zero)

/-- Rank over GF(2) of bitmask rows. -/
def rank (rows : List Nat) : Nat :=
  let rec go (fuel : Nat) (rows : List Nat) : Nat :=
    match fuel with
    | 0 => 0
    | fuel + 1 =>
      match rows.filter (· != 0) with
      | [] => 0
      | r :: rest =>
        let top := r.log2
        1 + go fuel (rest.map fun v => if v.testBit top then v ^^^ r else v)
  go (rows.length + 1) rows

end StabRank
