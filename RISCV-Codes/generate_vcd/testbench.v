`timescale 1ns/1ps

module testbench;
    reg clk;
    reg start;

    PipelineCPU dut_clean (.clk(clk), .start(start));
    PipelineCPU_trojan_comb dut_comb (.clk(clk), .start(start));
    PipelineCPU_trojan_seq dut_seq (.clk(clk), .start(start));
    PipelineCPU_trojan_ctrl dut_ctrl (.clk(clk), .start(start));

    
    initial clk = 0;
    always #10 clk = ~clk;    // 20ns period

    initial begin
        start = 0;            
        #25 start = 1;        
        #5200 $finish;
    end
    
    initial begin
        $dumpfile("all_designs.vcd");
        $dumpvars(0, testbench);
    end

endmodule