import sys
R=int(sys.argv[1])   # rows per stage
out=[]
def emit(s): out.append(s)
def gen(name, PW, IW, first):
    # columns: list of bit-expr strings
    cols=[[] for _ in range(PW)]
    const=0
    for r in range(R):
        for i in range(8):
            for j in range(8):
                k=i+j
                if k>=PW: continue
                inv = (i==7) != (j==7)
                e=f"(a{r}[{i}] & w{r}[{j}])"
                if inv:
                    e="~"+e; const -= (1<<k)
                cols[k].append(e)
    if not first:
        for b in range(IW):
            if b==IW-1:
                cols[b].append(f"~psum_north[{b}]"); const -= (1<<(IW-1))
            else:
                cols[b].append(f"psum_north[{b}]")
    const %= (1<<PW)
    for b in range(PW):
        if (const>>b)&1: cols[b].append("1'b1")
    body=[]; n=[0]
    def new():
        n[0]+=1; return f"t{n[0]}"
    seq=[2]
    while seq[-1] < max(len(c) for c in cols): seq.append({2:3,3:4,4:6,6:9,9:13,13:19,19:28,28:42}[seq[-1]])
    for tgt in reversed(seq[:-1]):
        new_cols=[[] for _ in range(PW)]
        carry_in=[[] for _ in range(PW+1)]
        for b in range(PW):
            col=list(cols[b])
            # height with incoming carries from this stage
            while len(col)+len(carry_in[b])+len(new_cols[b]) > tgt:
                excess=len(col)+len(carry_in[b])+len(new_cols[b])-tgt
                if excess>=2 and len(col)>=3:
                    x,y,z=col.pop(0),col.pop(0),col.pop(0)
                    s,c=new(),new()
                    body.append(f"   wire {s} = {x} ^ {y} ^ {z};")
                    body.append(f"   wire {c} = ({x} & {y}) | ({x} & {z}) | ({y} & {z});")
                    new_cols[b].append(s)
                    if b+1<PW: carry_in[b+1].append(c)
                else:
                    x,y=col.pop(0),col.pop(0)
                    s,c=new(),new()
                    body.append(f"   wire {s} = {x} ^ {y};")
                    body.append(f"   wire {c} = {x} & {y};")
                    new_cols[b].append(s)
                    if b+1<PW: carry_in[b+1].append(c)
            new_cols[b]+=col
            new_cols[b]+=carry_in[b]
        cols=new_cols
    assert all(len(c)<=2 for c in cols), [len(c) for c in cols]
    emit(f"module {name}(")
    ports=[]
    for r in range(R): ports+= [f"input [7:0] a{r}", f"input [7:0] w{r}"]
    ports.append(f"input [{max(IW,1)-1}:0] psum_north")
    ports.append(f"output [{PW-1}:0] sum")
    emit("  "+",\n  ".join(ports)+");")
    out.extend(body)
    emit(f"   wire [{PW-1}:0] x, y;")
    for b in range(PW):
        c=cols[b]+["1'b0"]*2
        emit(f"   assign x[{b}] = {c[0]};")
        emit(f"   assign y[{b}] = {c[1]};")
    emit(f"   bk_add_{PW} u_add(.x(x), .y(y), .s(sum));")
    emit("endmodule\n")

def bk(PW):
    emit(f"""module bk_add_{PW}(input [{PW-1}:0] x, input [{PW-1}:0] y, output [{PW-1}:0] s);
   localparam W = {PW};
   reg [W-1:0] G, P, P0;
   integer d, k;
   always @* begin
     G = x & y; P = x ^ y; P0 = P;
     for (d = 1; d < W; d = d * 2)
       for (k = 2*d-1; k < W; k = k + 2*d) begin
         G[k] = G[k] | (P[k] & G[k-d]);
         P[k] = P[k] & P[k-d];
       end
     for (d = 16; d >= 1; d = d / 2)
       for (k = 3*d-1; k < W; k = k + 2*d) begin
         G[k] = G[k] | (P[k] & G[k-d]);
         P[k] = P[k] & P[k-d];
       end
   end
   assign s = P0 ^ {{G[W-2:0], 1'b0}};
endmodule
""")
widths={}
def wid(r): return [16,17,17,18,18,18,18,19][r]
stages=8//R
for s in range(stages):
    PW=wid(R*s+R-1); IW=wid(R*s-1) if s>0 else 16
    widths[s]=(PW,IW)
for PW in sorted(set(p for p,_ in widths.values())): bk(PW)
for s in range(stages):
    PW,IW=widths[s]
    gen(f"tpu_mac_s{s}",PW,IW,s==0)
print("\n".join(out))
