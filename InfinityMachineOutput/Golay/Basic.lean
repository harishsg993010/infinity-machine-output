/-!
# Stabilizer (Heisenberg-picture) simulation of Clifford circuits

A Pauli operator on `n` qubits is stored as `i^r · ⊗_q X^{x_q} Z^{z_q}` with bitmasks `x`, `z`
and a phase exponent `r` modulo 4.

For a circuit `C = U_k ⋯ U_1` (gate `U_1` applied first) and a Pauli `P`, `pullback C P`
computes `C† P C` by conjugating with `U_k`, then `U_{k-1}`, …, then `U_1`, each step
`P ↦ U† P U`.

`P` stabilizes `C|0…0⟩` iff `C† P C` stabilizes `|0…0⟩`, i.e. iff `C† P C` is a product of `Z`s
with phase `+1`. The update rules below are the standard ones; the derivation of each sign is
in the comments.
-/

namespace Golay

inductive Gate where
  | h (q : Nat)
  | s (q : Nat)
  | sdg (q : Nat)
  | x (q : Nat)
  | y (q : Nat)
  | z (q : Nat)
  | cz (a b : Nat)
  | cx (c t : Nat)
  deriving Repr, DecidableEq

structure Pauli where
  x : Nat
  z : Nat
  r : Nat
  deriving Repr, DecidableEq

@[inline] def bit (m q : Nat) : Nat := if m.testBit q then 1 else 0
@[inline] def flip (m q b : Nat) : Nat := if b = 1 then m ^^^ (1 <<< q) else m

/-- `U† P U` for a single gate `U`. -/
def conj (P : Pauli) : Gate → Pauli
  -- H X^a Z^b H = Z^a X^b = (-1)^{ab} X^b Z^a
  | .h q =>
    let a := bit P.x q; let b := bit P.z q
    { x := flip P.x q (a ^^^ b), z := flip P.z q (a ^^^ b), r := (P.r + 2 * a * b) % 4 }
  -- S† X S = -Y = -i X Z,  S† Z S = Z
  | .s q =>
    let a := bit P.x q
    { P with z := flip P.z q a, r := (P.r + 3 * a) % 4 }
  -- S X S† = Y = i X Z
  | .sdg q =>
    let a := bit P.x q
    { P with z := flip P.z q a, r := (P.r + a) % 4 }
  -- X Z X = -Z
  | .x q => { P with r := (P.r + 2 * bit P.z q) % 4 }
  -- Z X Z = -X
  | .z q => { P with r := (P.r + 2 * bit P.x q) % 4 }
  -- Y X Y = -X, Y Z Y = -Z
  | .y q => { P with r := (P.r + 2 * (bit P.x q + bit P.z q)) % 4 }
  -- CZ: X_a ↦ X_a Z_b, X_b ↦ Z_a X_b; reordering Z_b^{x_a} X_b^{x_b} costs (-1)^{x_a x_b}
  | .cz a b =>
    let xa := bit P.x a; let xb := bit P.x b
    { x := P.x, z := flip (flip P.z a xb) b xa, r := (P.r + 2 * xa * xb) % 4 }
  -- CX(c→t): X_c ↦ X_c X_t, Z_t ↦ Z_c Z_t; no sign
  | .cx c t =>
    { x := flip P.x t (bit P.x c), z := flip P.z c (bit P.z t), r := P.r }

/-- `C† P C` for the circuit `C` listed in application order. -/
def pullback (C : List Gate) (P : Pauli) : Pauli :=
  C.foldr (fun g acc => conj acc g) P

/-- `P` stabilizes `|0…0⟩`: no `X` part and phase `+1`. -/
def fixesZero (P : Pauli) : Bool := P.x == 0 && P.r % 4 == 0

/-- `P` stabilizes `C|0…0⟩`. -/
def stabilizes (C : List Gate) (P : Pauli) : Bool := fixesZero (pullback C P)

def isTwoQubit : Gate → Bool
  | .cz .. | .cx .. => true
  | _ => false

def twoQubitCount (C : List Gate) : Nat := (C.filter isTwoQubit).length

/-- Two-qubit depth: ASAP layering where single-qubit gates are free. -/
def twoQubitDepth (n : Nat) (C : List Gate) : Nat :=
  let step (lv : Array Nat) (g : Gate) : Array Nat :=
    match g with
    | .cz a b | .cx a b =>
      let d := max (lv.getD a 0) (lv.getD b 0) + 1
      (lv.set! a d).set! b d
    | _ => lv
  (C.foldl step (Array.replicate n 0)).foldl max 0

/-- Every two-qubit gate acts on two distinct wires below `n`. -/
def wellFormed (n : Nat) (C : List Gate) : Bool :=
  C.all fun
    | .cz a b | .cx a b => a < n && b < n && a != b
    | .h q | .s q | .sdg q | .x q | .y q | .z q => q < n

/-! ## Linear algebra over GF(2) on bitmasks -/

/-- Rank over GF(2) of a list of bitmasks (Gaussian elimination by leading bit). -/
def rank (rows : List Nat) : Nat :=
  let rec go (fuel : Nat) (rows : List Nat) : Nat :=
    match fuel with
    | 0 => 0
    | fuel + 1 =>
      match rows.filter (· != 0) with
      | [] => 0
      | r :: rest =>
        let top := r.log2
        let reduce (v : Nat) := if v.testBit top then v ^^^ r else v
        1 + go fuel (rest.map reduce)
  go (rows.length + 1) rows

/-- Hamming weight. -/
def weight (v : Nat) : Nat := (List.range (v.log2 + 1)).countP (v.testBit ·)

/-- Binary inner product. -/
def dot (u v : Nat) : Nat := weight (u &&& v) % 2

/-- All `2^k` sums of a list of `k` generators. -/
def span (gens : List Nat) : List Nat :=
  gens.foldl (fun acc g => acc ++ acc.map (· ^^^ g)) [0]

/-- Symplectic commutation of two Paulis. -/
def commute (P Q : Pauli) : Bool := (dot P.x Q.z + dot P.z Q.x) % 2 == 0

end Golay
