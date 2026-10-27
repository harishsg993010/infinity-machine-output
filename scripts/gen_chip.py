"""Write InfinityMachineOutput/Chip/Mac.lean from data/chip/mac.sv (the delivered MAC netlist).

Each `wire t = expr;` and `assign x[b] = expr;` becomes a Bool variable with an equation hypothesis. The
Brent-Kung adder's always-block is unrolled following Verilog blocking-assignment semantics (each
reassignment of G[k] / P[k] is a fresh variable). Expressions are parsed with Verilog precedence
(~ > & > ^ > |) and emitted fully parenthesized, so Lean's operator precedence plays no role.

A monolithic bv_decide on the four 8x8 multipliers does not finish within an hour, so the proof is split:
  1. the adder: SAT shows each Brent-Kung group carry equals the ripple carry; then sum = x + y - 2^W c;
  2. the compressor tree: an exact integer identity, the weighted sum of all partial-product bits equals
     x + y + 2^W * (carries dropped off the top), by linear_combination of one lemma per 3:2 / 2:2 counter;
  3. Baugh-Wooley: for each product, the weighted partial-product bits minus a constant equal
     a.toInt * w.toInt, checked for all 65,536 inputs;
  4. omega combines them."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
src = (ROOT / "data/chip/mac.sv").read_text()

TOK = re.compile(r"\s*(~|&|\^|\||\(|\)|1'b[01]|[A-Za-z_]\w*\[\d+\]|[A-Za-z_]\w*)")


def parse(expr):
    toks = []
    pos = 0
    while pos < len(expr):
        m = TOK.match(expr, pos)
        if not m:
            if expr[pos:].strip() == "":
                break
            raise ValueError(f"cannot tokenize {expr[pos:]!r}")
        toks.append(m.group(1)); pos = m.end()
    i = [0]

    def peek(): return toks[i[0]] if i[0] < len(toks) else None
    def take(): i[0] += 1; return toks[i[0] - 1]

    def atom():
        t = take()
        if t == "~": return f"(!{atom()})"
        if t == "(":
            e = level(0)
            assert take() == ")"
            return e
        if t == "1'b1": return "true"
        if t == "1'b0": return "false"
        m = re.fullmatch(r"(\w+)\[(\d+)\]", t)
        if m: return f"({m.group(1)}.getLsbD {m.group(2)})"
        return t
    ops = [("|", "||"), ("^", "^^"), ("&", "&&")]

    def level(k):
        if k == len(ops): return atom()
        e = level(k + 1)
        while peek() == ops[k][0]:
            take(); e = f"({e} {ops[k][1]} {level(k + 1)})"
        return e
    e = level(0)
    assert i[0] == len(toks), (expr, toks[i[0]:])
    return e


def split_top(e, op):
    """Split a Verilog expression at top-level occurrences of the single-char operator `op`."""
    parts, depth, cur = [], 0, ""
    for ch in e:
        if ch == "(": depth += 1
        elif ch == ")": depth -= 1
        if ch == op and depth == 0:
            parts.append(cur.strip()); cur = ""
        else:
            cur += ch
    parts.append(cur.strip())
    return parts


def atom_weight(item):
    """Column of an initial item, or None for a constant / wire."""
    m = re.fullmatch(r"~?\(a\d\[(\d+)\] & w\d\[(\d+)\]\)", item)
    if m: return int(m.group(1)) + int(m.group(2))
    m = re.fullmatch(r"~?psum_north\[(\d+)\]", item)
    if m: return int(m.group(1))
    return None


def module(name):
    m = re.search(rf"module {name}\((.*?)\);(.*?)endmodule", src, re.S)
    ports, body = m.group(1), m.group(2)
    pw = int(re.search(r"input \[(\d+):0\] psum_north", ports).group(1)) + 1
    W = int(re.search(r"output \[(\d+):0\] sum", ports).group(1)) + 1
    wires = re.findall(r"wire (t\d+) = (.*?);", body)
    assigns = re.findall(r"assign ([xy])\[(\d+)\] = (.*?);", body)
    assert re.search(rf"bk_add_{W} u_add\(\.x\(x\), \.y\(y\), \.s\(sum\)\)", body)
    eqs = [(v, parse(e)) for v, e in wires] + [(f"{xy}{b}", parse(e)) for xy, b, e in assigns]

    # ---- compressor bookkeeping: counters, columns, conservation
    weight, used, counters, init, dropped = {}, set(), [], [], []
    wl = list(wires)
    k = 0
    while k < len(wl):
        (s, se), (c, ce) = wl[k], wl[k + 1]
        items = split_top(se, "^")
        if len(items) == 3:
            x, y, z = items
            assert ce == f"({x} & {y}) | ({x} & {z}) | ({y} & {z})", (s, c)
            kind = "fa"
        else:
            assert len(items) == 2
            x, y = items
            assert ce == f"{x} & {y}", (s, c)
            kind = "ha"
        cols = set()
        for it in items:
            if it in weight:
                assert it not in used, it
                used.add(it); cols.add(weight[it])
            elif atom_weight(it) is not None:
                cols.add(atom_weight(it))
        assert len(cols) == 1, (s, items, cols)
        col = cols.pop()
        for it in items:
            if it not in weight:
                init.append((col, it))
        weight[s], weight[c] = col, col + 1
        counters.append((kind, s, c, col))
        k += 2
    for xy, b, e in assigns:
        b = int(b)
        if e in weight:
            assert weight[e] == b and e not in used, (xy, b, e)
            used.add(e)
        else:
            assert atom_weight(e) in (b, None), (xy, b, e)
            init.append((b, e))
    for v, wgt in weight.items():
        if v not in used:
            assert wgt == W, (v, wgt)   # only carries off the top may be unused
            dropped.append(v)

    # ---- Brent-Kung adder, unrolled
    G = {k: f"g{k}_0" for k in range(W)}
    P = {k: f"p{k}_0" for k in range(W)}
    add_eqs = []
    for k in range(W):
        add_eqs.append((G[k], f"(x{k} && y{k})"))
        add_eqs.append((P[k], f"(x{k} ^^ y{k})"))
    P0 = dict(P)
    ver = {k: 0 for k in range(W)}

    def upd(k, d):
        ver[k] += 1
        g, p = f"g{k}_{ver[k]}", f"p{k}_{ver[k]}"
        add_eqs.append((g, f"({G[k]} || ({P[k]} && {G[k - d]}))"))
        add_eqs.append((p, f"({P[k]} && {P[k - d]})"))
        G[k], P[k] = g, p
    d = 1
    while d < W:
        for k in range(2 * d - 1, W, 2 * d): upd(k, d)
        d *= 2
    d = 16
    while d >= 1:
        for k in range(3 * d - 1, W, 2 * d): upd(k, d)
        d //= 2
    for k in range(W):
        add_eqs.append((f"s{k}", f"({P0[k]} ^^ {G[k - 1]})" if k else P0[k]))
    return dict(pw=pw, W=W, eqs=eqs, add_eqs=add_eqs, Gfinal=G, counters=counters, init=init,
                dropped=dropped)


def toZ(e):
    return f"(({e}).toNat : ℤ)"


def adder_lemma(W, add_eqs, Gfinal):
    xs = " ".join(f"x{k}" for k in range(W)); ys = " ".join(f"y{k}" for k in range(W))
    vars_ = " ".join(v for v, _ in add_eqs)
    hyps = "\n".join(f"    (h_{v} : {v} = {e})" for v, e in add_eqs)
    S = " + ".join(f"{2 ** k} * {toZ(f's{k}')}" for k in range(W))
    XY = " + ".join(f"{2 ** k} * ({toZ(f'x{k}')} + {toZ(f'y{k}')})" for k in range(W))
    L = [f"/-- The {W}-bit Brent-Kung adder `bk_add_{W}` computes `x + y` modulo `2^{W}`. -/",
         f"theorem bk_add_{W}_correct ({xs} {ys} : Bool)", f"    ({vars_} : Bool)", hyps, " :",
         f"    ∃ cout : Bool, {S} =", f"      ({XY}) - {2 ** W} * {toZ('cout')} := by"]
    # ripple carries r1..rW; the prefix network's group generates equal them (Bool-only SAT)
    L.append("  obtain ⟨r1, hr1⟩ : ∃ r : Bool, r = (x0 && y0) := ⟨_, rfl⟩")
    for k in range(1, W):
        L.append(f"  obtain ⟨r{k + 1}, hr{k + 1}⟩ : ∃ r : Bool, r = ((x{k} && y{k}) || ((x{k} ^^ y{k}) && r{k})) := ⟨_, rfl⟩")
    for k in range(W - 1):
        L.append(f"  have c{k + 1} : {Gfinal[k]} = r{k + 1} := by bv_decide")
    L.append(f"  have f0 : {toZ('x0')} + {toZ('y0')} = {toZ('s0')} + 2 * {toZ('r1')} := by")
    L.append(f"    rw [h_s0, h_p0_0, hr1]; exact ha_counter rfl rfl")
    for k in range(1, W):
        L.append(f"  have f{k} : {toZ(f'x{k}')} + {toZ(f'y{k}')} + {toZ(f'r{k}')} = {toZ(f's{k}')} + 2 * {toZ(f'r{k + 1}')} := by")
        L.append(f"    rw [h_s{k}, h_p{k}_0, c{k}, hr{k + 1}]; exact fa_ripple x{k} y{k} r{k}")
    L.append(f"  refine ⟨r{W}, ?_⟩")
    L.append("  linear_combination " + " ".join(f"- {2 ** k} * f{k}" for k in range(W)))
    return "\n".join(L)


def emit(name, lean_name, doc, prod_lemma, has_psum):
    M = module(name)
    W, pw = M["W"], M["pw"]
    all_eqs = M["eqs"] + M["add_eqs"]
    vars_ = " ".join(v for v, _ in all_eqs)
    hyps = "\n".join(f"    (h_{v} : {v} = {e})" for v, e in all_eqs)
    spec = " + ".join(f"a{r}.toInt * w{r}.toInt" for r in range(4)) + (" + psum_north.toInt" if has_psum else "")
    S = " + ".join(f"{2 ** k} * {toZ(f's{k}')}" for k in range(W))
    L = [f"/-- `{name}`: {doc} -/", f"theorem {lean_name}",
         f"    (a0 w0 a1 w1 a2 w2 a3 w3 : BitVec 8) (psum_north : BitVec {pw})",
         f"    ({vars_} : Bool)", hyps, " :",
         f"    {S} = ({spec}) % {2 ** W} := by"]
    # 1. adder
    adder_args = " ".join(f"x{k}" for k in range(W)) + " " + " ".join(f"y{k}" for k in range(W)) + " " + \
        " ".join(v for v, _ in M["add_eqs"]) + " " + " ".join(f"h_{v}" for v, _ in M["add_eqs"])
    L.append(f"  obtain ⟨cout, hadd⟩ := bk_add_{W}_correct {adder_args}")
    # 2. compressor
    for i, (kind, s, c, col) in enumerate(M["counters"]):
        L.append(f"  have k{i} := {kind}_counter h_{s} h_{c}")
    for k in range(W):
        for xy in "xy":
            e = dict(M["eqs"])[f"{xy}{k}"]
            L.append(f"  have a{xy}{k} : {toZ(f'{xy}{k}')} = {toZ(e)} := by rw [h_{xy}{k}]")
    init = " + ".join(f"{2 ** col} * {toZ(parse(it))}" for col, it in M["init"])
    drop = " + ".join(toZ(v) for v in M["dropped"]) or "0"
    comb = " + ".join(f"{2 ** col} * k{i}" for i, (_, _, _, col) in enumerate(M["counters"]))
    comb += " - " + " - ".join(f"{2 ** k} * a{xy}{k}" for k in range(W) for xy in "xy")
    L.append(f"  have hcomp : ({init}) =")
    XY = " + ".join(f"{2 ** k} * ({toZ('x' + str(k))} + {toZ('y' + str(k))})" for k in range(W))
    L.append(f"      ({XY})")
    L.append(f"      + {2 ** W} * ({drop}) := by")
    L.append(f"    linear_combination {comb}")
    # 3. Baugh-Wooley products and psum
    for r in range(4):
        L.append(f"  have m{r} := {prod_lemma} a{r} w{r}")
    if has_psum:
        L.append(f"  have hps := psum_bits_{pw} psum_north")
    # 4. combine
    L.append("  simp only [Bool.toNat_true, Bool.toNat_false, Nat.cast_one, Nat.cast_zero] at hcomp")
    for k in range(W):
        L.append(f"  have b{k} := Bool.toNat_le s{k}")
    L.append("  generalize " + " at *\n  generalize ".join(f"a{r}.toInt * w{r}.toInt = q{r}" for r in range(4)) + " at *")
    L.append("  omega")
    return "\n".join(L), M


def prod_terms(W, a, w):
    t = []
    for i in range(8):
        for j in range(8):
            if i + j >= W: continue
            e = f"({a}.getLsbD {i} && {w}.getLsbD {j})"
            if (i == 7) != (j == 7): e = f"(!{e})"
            t.append(f"{2 ** (i + j)} * (({e}).toNat : ℤ)")
    return " + ".join(t)


K_BW = sum(1 << (i + j) for i in range(8) for j in range(8) if (i == 7) != (j == 7))

out = ["import Mathlib", "",
       "/-! Generated by `scripts/gen_chip.py` from `data/chip/mac.sv`. See `Chip/Main.lean`. -/", "",
       "namespace Chip", "", "set_option maxHeartbeats 0", "set_option maxRecDepth 100000",
       "set_option linter.style.longLine false", "",
       "theorem fa_counter {x y z s c : Bool} (hs : s = ((x ^^ y) ^^ z))",
       "    (hc : c = (((x && y) || (x && z)) || (y && z))) :",
       "    (x.toNat : ℤ) + y.toNat + z.toNat = s.toNat + 2 * c.toNat := by",
       "  subst hs hc; cases x <;> cases y <;> cases z <;> rfl", "",
       "theorem ha_counter {x y s c : Bool} (hs : s = (x ^^ y)) (hc : c = (x && y)) :",
       "    (x.toNat : ℤ) + y.toNat = s.toNat + 2 * c.toNat := by",
       "  subst hs hc; cases x <;> cases y <;> rfl", "",
       "theorem fa_ripple (x y r : Bool) :",
       "    (x.toNat : ℤ) + y.toNat + r.toNat =",
       "      ((x ^^ y) ^^ r).toNat + 2 * ((x && y) || ((x ^^ y) && r)).toNat := by",
       "  cases x <;> cases y <;> cases r <;> rfl", "",
       "/-- Baugh-Wooley: the weighted partial-product bits, with the bits that involve exactly one sign bit",
       f"inverted, minus {K_BW} equal the signed product. Checked for all 65,536 inputs. -/",
       "theorem baugh_wooley : ∀ a w : BitVec 8,",
       f"    ({prod_terms(99, 'a', 'w')}) - {K_BW} = a.toInt * w.toInt := by native_decide", ""]
for pw in (18,):
    terms = " + ".join(f"{2 ** b} * ((psum_north.getLsbD {b}).toNat : ℤ)" for b in range(pw - 1))
    out += [f"/-- A {pw}-bit two's-complement value from its bits, with the top bit inverted as in the netlist. -/",
            f"theorem psum_bits_{pw} : ∀ psum_north : BitVec {pw},",
            f"    ({terms} + {2 ** (pw - 1)} * ((!psum_north.getLsbD {pw - 1}).toNat : ℤ)) - {2 ** (pw - 1)} =",
            f"      psum_north.toInt := by native_decide", ""]
for name, W in (("tpu_mac_s0", 18), ("tpu_mac_s1", 19)):
    M = module(name)
    out += [adder_lemma(M["W"], M["add_eqs"], M["Gfinal"]), ""]
t, _ = emit("tpu_mac_s0", "mac_s0_correct",
            "rows 0-3. The 18-bit output is `Σ_r a_r·w_r` (signed INT8) modulo `2^18`; "
            "the stage-0 `psum_north` port is tied to 0 and unused.", "baugh_wooley", False)
out += [t, ""]
t, _ = emit("tpu_mac_s1", "mac_s1_correct",
            "rows 4-7. The 19-bit output is `psum_north + Σ_r a_r·w_r` (signed) modulo `2^19`.",
            "baugh_wooley", True)
out += [t, "", "end Chip", ""]
(ROOT / "InfinityMachineOutput/Chip").mkdir(exist_ok=True)
(ROOT / "InfinityMachineOutput/Chip/Mac.lean").write_text("\n".join(out), encoding="utf-8")
for name in ("tpu_mac_s0", "tpu_mac_s1"):
    M = module(name)
    print(name, "W", M["W"], "counters", len(M["counters"]), "init items", len(M["init"]), "dropped", M["dropped"])
