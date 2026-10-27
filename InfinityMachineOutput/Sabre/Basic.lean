/-!
# Exact replay of SWAP-routed circuits on IBM Q20 Tokyo

The benchmark rule is from Li, Ding, Xie (ASPLOS 2019): the number of added gates is three times
the number of inserted SWAPs, with no other rewriting.

A routed circuit gives an initial injective map from logical to physical qubits, and a sequence of
operations. Each operation is either the index of an original gate or a SWAP of two physical
qubits. The routing is valid when all of the following hold:
* every original gate executes exactly once;
* each gate executes only when it is the next unexecuted gate on every qubit it touches, so the
  per-qubit gate order is preserved;
* every two-qubit gate lands on a coupler under the current mapping;
* every SWAP is on a coupler.

Preserving the per-qubit order makes the executed sequence equal to the original circuit up to
commuting gates on disjoint qubits, followed by a final relabelling of qubits. That equivalence
is the standard argument and is not formalized here.
-/

namespace Sabre

/-- IBM Q20 Tokyo as drawn in Fig. 2 of the SABRE paper. It is a 4 × 5 grid with all
horizontal and vertical couplers plus 12 diagonal couplers, giving 43 undirected edges.
This is not Qiskit's `FakeTokyo` (35 edges). -/
def tokyoEdges : List (Nat × Nat) := Id.run do
  let mut E : List (Nat × Nat) := []
  for r in List.range 4 do
    for c in List.range 5 do
      let q := 5 * r + c
      if c < 4 then E := (q, q + 1) :: E
      if r < 3 then E := (q, q + 5) :: E
  return E ++ [(1, 7), (2, 6), (3, 9), (4, 8), (5, 11), (6, 10), (7, 13), (8, 12), (11, 17),
    (12, 16), (13, 19), (14, 18)]

def nPhys : Nat := 20

/-- Adjacency matrix as a flat `20 × 20` array. -/
def adj : Array Bool := Id.run do
  let mut A := Array.replicate (nPhys * nPhys) false
  for (a, b) in tokyoEdges do
    A := (A.set! (a * nPhys + b) true).set! (b * nPhys + a) true
  return A

def isEdge (a b : Nat) : Bool := a < nPhys && b < nPhys && adj[a * nPhys + b]!

structure Instance where
  name : String
  n : Nat
  mapping : List Nat
  sabreRef : Nat
  gates : String
  ops : String

inductive Op where
  | gate (g : Nat)
  | swap (p q : Nat)
  deriving Inhabited

def parseGates (s : String) : Array (List Nat) :=
  ((s.splitOn ";").map fun g => (g.splitOn ",").map String.toNat!).toArray

def parseOps (s : String) : List Op :=
  (s.splitOn " ").map fun t =>
    match t.splitOn "-" with
    | [p, q] => .swap p.toNat! q.toNat!
    | _ => .gate t.toNat!

/-- Replays a routing. Returns `some (number of SWAPs)` if it is valid, `none` otherwise. -/
def replay (n : Nat) (gates : Array (List Nat)) (mapping : List Nat) (ops : List Op) :
    Option Nat := Id.run do
  -- the initial map is injective, into the 20 physical qubits, one entry per logical qubit
  if mapping.length != n || mapping.any (· ≥ nPhys) || mapping.eraseDups.length != n then
    return none
  if gates.any (fun qs => qs.any (· ≥ n) || qs.length == 0 || qs.length > 2 ||
      (qs.length == 2 && qs[0]! == qs[1]!)) then
    return none
  -- per-qubit gate lists, in circuit order
  let mut perQ : Array (Array Nat) := Array.replicate n #[]
  for g in List.range gates.size do
    for q in gates[g]! do
      perQ := perQ.modify q (·.push g)
  let mut ptr : Array Nat := Array.replicate n 0
  let mut l2p : Array Nat := mapping.toArray
  let mut p2l : Array (Option Nat) := Array.replicate nPhys none
  for l in List.range n do
    p2l := p2l.set! l2p[l]! (some l)
  let mut swaps := 0
  let mut executed := 0
  for op in ops do
    match op with
    | .swap p q =>
      if !isEdge p q then return none
      let lp := p2l[p]!
      let lq := p2l[q]!
      if let some l := lp then l2p := l2p.set! l q
      if let some l := lq then l2p := l2p.set! l p
      p2l := (p2l.set! p lq).set! q lp
      swaps := swaps + 1
    | .gate g =>
      if g ≥ gates.size then return none
      let qs := gates[g]!
      -- g must be the next unexecuted gate on each of its qubits
      if qs.any (fun q => (perQ[q]!)[ptr[q]!]? != some g) then return none
      if qs.length == 2 && !isEdge l2p[qs[0]!]! l2p[qs[1]!]! then return none
      for q in qs do
        ptr := ptr.modify q (· + 1)
      executed := executed + 1
  if executed != gates.size then return none
  return some swaps

def Instance.addedGates (I : Instance) : Option Nat :=
  (replay I.n (parseGates I.gates) I.mapping (parseOps I.ops)).map (3 * ·)

end Sabre
