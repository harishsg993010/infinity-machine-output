// Energy-optimised 8x8 INT8 weight-stationary tile (same ports/protocol/latency as the reference).
// - Broadcast dataflow: activation row i is delayed (7+i) cycles and fed to all 8 PEs of row i at once,
//   so no east-going activation registers and no output de-skew registers are needed.
// - Psum registers have minimal width per row (16..19 bits), sign-extended at the output.
// - Datapath registers carry no reset (only the valid pipe does); results are only observed with c_valid.
// - Each pipeline depth s is clocked by a glitch-free gated clock enabled only when valid data enters it.
`ifndef USE_CG
 `define USE_CG 1
`endif
module tpu_cg(input clk, input en, output gclk);
   reg l;
   always_latch if (!clk) l <= en;
   assign gclk = clk & l;
endmodule

module tpu
  #(parameter N = 8, parameter DW = 8, parameter ACCW = 32)
   (input clk, input rst, input w_valid, input [N*DW-1:0] w_data,
    input a_valid, input [N*DW-1:0] a_data,
    output c_valid, output [N*ACCW-1:0] c_data);

   localparam LAT = 15;

   // valid pipe: v[s] = a_valid delayed s cycles (v[0] is the input)
   reg [LAT-1:0] vp;
   always @(posedge clk) begin
      if (rst) vp <= {LAT{1'b0}};
      else     vp <= {vp[LAT-2:0], a_valid};
   end
   assign c_valid = vp[LAT-1];
   wire [LAT-1:0] ven = {vp[LAT-2:0], a_valid};   // ven[s-1] enables depth-s registers

   // clocks: depth 13..15 gated by the valid pipe; ring write clocks; per-row weight clocks
   wire [LAT:13] gclk;
   genvar s;
   generate
     for (s = 13; s <= LAT; s = s + 1) begin : g_clk
       tpu_cg u (.clk(clk), .en(ven[s-1]), .gclk(gclk[s]));
     end
   endgenerate

   // weights: row r is written directly in cycle k=7-r of a load (no shifting); one-hot pointer
   reg [N-1:0] wptr;
   always @(posedge clk) begin
      if (rst) wptr <= 8'b1;
      else if (w_valid) wptr <= {wptr[N-2:0], wptr[N-1]};
   end
   wire [DW-1:0] w [0:N-1][0:N-1];
   genvar i, j;
   generate
     for (i = 0; i < N; i = i + 1) begin : g_wr
       wire wclk;
       tpu_cg uw (.clk(clk), .en(w_valid & wptr[N-1-i]), .gclk(wclk));
       reg [N*DW-1:0] q;
       always @(posedge wclk) q <= w_data;
       for (j = 0; j < N; j = j + 1) begin : g_wc
         assign w[i][j] = q[j*DW +: DW];
       end
     end
   endgenerate

   // activation delay: ring buffer of K=13 entries (written round-robin, only one entry clocked per cycle),
   // read through an AND-OR mux into a gated output register (holds when idle -> MAC logic is quiet).
   localparam K = 13;
   reg [K-1:0] ptr;
   always @(posedge clk) begin
      if (rst) ptr <= {{(K-1){1'b0}}, 1'b1};
      else     ptr <= {ptr[K-2:0], ptr[K-1]};
   end
   wire [N*DW-1:0] ent [0:K-1];
   generate
     for (i = 0; i < K; i = i + 1) begin : g_ent
       wire rclk;
       tpu_cg ur (.clk(clk), .en(ptr[i] & a_valid), .gclk(rclk));
       reg [N*DW-1:0] q;
       always @(posedge rclk) q <= a_data;
       assign ent[i] = q;
     end
   endgenerate

   wire [DW-1:0] a_row [0:N-1];
   generate
     for (i = 0; i < N; i = i + 1) begin : g_ch
       // rows 0-3: total delay 13 (read in cycle t+12 -> select rotated by one); rows 4-7: delay 14
       wire [K-1:0] sel;
       for (j = 0; j < K; j = j + 1) begin : g_sel
         if (i < 4) begin : lo
           assign sel[j] = ptr[(j+K-1) % K];
         end else begin : hi
           assign sel[j] = ptr[j];
         end
       end
       reg [DW-1:0] rd;
       integer kk;
       always @* begin
         rd = {DW{1'b0}};
         for (kk = 0; kk < K; kk = kk + 1)
           rd = rd | (ent[kk][i*DW +: DW] & {DW{sel[kk]}});
       end
       reg [DW-1:0] q;
       always @(posedge gclk[13 + i/4]) q <= rd;
       assign a_row[i] = q;
     end
   endgenerate

   // psum stages: stage s covers rows 2s,2s+1, registered at depth 12+s
   function integer wid(input integer r);
     begin
       case (r) 0: wid = 16; 1: wid = 17; 2: wid = 17; 3: wid = 18; 4: wid = 18;
                5: wid = 18; 6: wid = 18; default: wid = 19; endcase
     end
   endfunction

   wire [18:0] ps [0:1][0:N-1];
   generate
     for (i = 0; i < 2; i = i + 1) begin : g_pr
       localparam W = wid(4*i+3);
       localparam WP = (i == 0) ? 16 : wid(3);
       for (j = 0; j < N; j = j + 1) begin : g_pc
         wire [W-1:0] sum;
         wire [WP-1:0] pn;
         if (i == 0) begin : f0
           assign pn = {WP{1'b0}};
         end else begin : f1
           assign pn = g_pr[i-1].g_pc[j].p;
         end
         if (i == 0) begin : m
           tpu_mac_s0 u (.a0(a_row[0]), .w0(w[0][j]), .a1(a_row[1]), .w1(w[1][j]), .a2(a_row[2]), .w2(w[2][j]), .a3(a_row[3]), .w3(w[3][j]), .psum_north(pn), .sum(sum));
         end else begin : m
           tpu_mac_s1 u (.a0(a_row[4]), .w0(w[4][j]), .a1(a_row[5]), .w1(w[5][j]), .a2(a_row[6]), .w2(w[6][j]), .a3(a_row[7]), .w3(w[7][j]), .psum_north(pn), .sum(sum));
         end
         reg [W-1:0] p;
         always @(posedge gclk[14+i]) p <= sum;
         assign ps[i][j] = {{(19-W){p[W-1]}}, p};
       end
     end
   endgenerate

   generate
     for (j = 0; j < N; j = j + 1) begin : g_out
       assign c_data[j*ACCW +: ACCW] = {{(ACCW-19){ps[1][j][18]}}, ps[1][j]};
     end
   endgenerate
endmodule
