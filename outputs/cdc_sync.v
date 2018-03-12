`timescale 1 ns / 1 ps

module cdc_sync #
  (
    parameter integer WIDTH      = 1,
    parameter integer WITH_VLD   = 0,
    parameter real    SRC_PER_NS = 5.0,
    parameter real    DST_PER_NS = 5.0,
    parameter integer DAT_IS_REG = 0,
    parameter integer IS_PULSE   = 0
  )
  (
    input  wire             src_clk,
    input  wire [WIDTH-1:0] src_dat,
    input  wire             src_vld,
    input  wire             dst_clk,
    output wire [WIDTH-1:0] dst_dat,
    output wire             dst_vld
  );

  localparam integer PULSE_EXT = 1.5*DST_PER_NS/SRC_PER_NS;

  reg [WIDTH-1:0] dat_reg;
  reg [PULSE_EXT-1:0] pulse_array;
  reg [PULSE_EXT-1:0] vld_array;
  reg vld_reg;
  integer i;

  generate
    // Register incoming signal wrt source clock
    if (!IS_PULSE && !WITH_VLD && !DAT_IS_REG) begin
      always @(posedge src_clk) begin
        dat_reg <= src_dat;
      end
    end

    // Already registered incoming signal wrt source clock
    if (!IS_PULSE && !WITH_VLD && DAT_IS_REG) begin
      always @(*) begin
        dat_reg <= src_dat;
      end
    end

    // Register incoming signal wrt source clock when valid
    if (WITH_VLD) begin
      always @(posedge src_clk) begin
        if (src_vld) begin
          dat_reg <= src_dat;
        end
      end
    end

    // Extend pulses to 1.5x of dst period and register wrt source clock
    if (IS_PULSE) begin
      always @(posedge src_clk) begin
        dat_reg <= |pulse_array;
        for (i = 0; i<PULSE_EXT; i = i+1) begin
          if (i == 1) begin
            pulse_array[i] <= src_dat[0];
          end else begin
            pulse_array[i] <= pulse_array[i-1];
          end
        end
      end
    end

    // Extend valid to 1.5x of dst period and register wrt source clock
    if (WITH_VLD) begin
      always @(posedge src_clk) begin
        vld_reg <= |vld_array;
        for (i = 0; i<PULSE_EXT; i = i+1) begin
          if (i == 1) begin
            pulse_array[i] <= vld_reg;
          end else begin
            pulse_array[i] <= pulse_array[i-1];
          end
        end
      end
    end

    // Synchronizers
    // Sync valid
    if (WITH_VLD) begin
      xpm_cdc_single #
     (
        .DEST_SYNC_FF(4),
        .SIM_ASSERT_CHK(1),
        .SRC_INPUT_REG (0) 
     ) cdc_vld (
        .src_clk(src_clk),
        .src_in(vld_reg),
        .dest_clk(dst_clk),
        .dest_out(dst_vld)
      );
    end

    // sync data if not pulse
    if (!IS_PULSE) begin
    xpm_cdc_array_single #
      (
        .DEST_SYNC_FF(4),
        .SIM_ASSERT_CHK(1),
        .SRC_INPUT_REG(0),
        .WIDTH(WIDTH)
      ) cdc_vld (
        .src_clk(src_clk),
        .src_in(dat_reg),
        .dest_clk(dst_clk),
        .dest_out(dst_dat)
      );
    end

    // sync data if pulse
    if (IS_PULSE) begin
    xpm_cdc_pulse #
      (
        .DEST_SYNC_FF(4),
        .REG_OUTPUT(1),
        .RST_USED(0),
        .SIM_ASSERT_CHK(0)
      ) cdc_pulse (
        .src_clk(src_clk),
        .src_rst(1'b0),
        .src_pulse(dat_reg),
        .dest_clk(dst_clk),
        .dest_rst(1'b0),
        .dest_pulse(dst_dat)
      );
    end

  endgenerate

endmodule
