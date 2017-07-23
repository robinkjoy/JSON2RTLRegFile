# pkg
libraries = '''library IEEE;
use ieee.std_logic_1164.all;
'''
pkg_header = libraries+'''use ieee.numeric_std.all;
package pl_reg_pkg is

'''
pkg_reg_addr = '  constant {:{}} : natural := {};\n'
pkg_mask = '  constant {:{}} : std_logic_vector (31 downto 0) := x"{}";\n'
pkg_footer = '''
  procedure axilite_write (
    constant addr  : in  natural;
    constant data  : in  std_logic_vector (31 downto 0);
    constant per   : in  time;
    signal clk     : in  std_logic;
    signal awready : in  std_logic;
    signal awvalid : out std_logic;
    signal awaddr  : out std_logic_vector (31 downto 0);
    signal wready  : in  std_logic;
    signal wvalid  : out std_logic;
    signal wdata   : out std_logic_vector (31 downto 0);
    signal wstrb   : out std_logic_vector (3 downto 0);
    signal bvalid  : in  std_logic;
    signal bready  : out std_logic
    );
  procedure axilite_read (
    constant addr  : in  natural;
    variable data  : out std_logic_vector (31 downto 0);
    constant per   : in  time;
    signal clk     : in  std_logic;
    signal arready : in  std_logic;
    signal arvalid : out std_logic;
    signal araddr  : out std_logic_vector (31 downto 0);
    signal rready  : out std_logic;
    signal rvalid  : in  std_logic;
    signal rdata   : in  std_logic_vector (31 downto 0)
    );

end package pl_reg_pkg;

package body pl_reg_pkg is

  procedure axilite_write (
    constant addr  : in  natural;
    constant data  : in  std_logic_vector (31 downto 0);
    constant per   : in  time;
    signal clk     : in  std_logic;
    signal awready : in  std_logic;
    signal awvalid : out std_logic;
    signal awaddr  : out std_logic_vector (31 downto 0);
    signal wready  : in  std_logic;
    signal wvalid  : out std_logic;
    signal wdata   : out std_logic_vector (31 downto 0);
    signal wstrb   : out std_logic_vector (3 downto 0);
    signal bvalid  : in  std_logic;
    signal bready  : out std_logic
    ) is
  begin
    bready  <= '0';
    awvalid <= '1';
    awaddr  <= std_logic_vector(to_unsigned(addr, awaddr'length));
    wvalid  <= '1';
    wdata   <= data;
    wstrb   <= (others => '1');
    wait until rising_edge(clk) and awready = '1' and wready = '1';
    awvalid <= '0';
    wvalid  <= '0';
    bready  <= '1';
    wait until rising_edge(clk) and bvalid = '1';
  end axilite_write;

  procedure axilite_read (
    constant addr  : in  natural;
    variable data  : out std_logic_vector (31 downto 0);
    constant per   : in  time;
    signal clk     : in  std_logic;
    signal arready : in  std_logic;
    signal arvalid : out std_logic;
    signal araddr  : out std_logic_vector (31 downto 0);
    signal rready  : out std_logic;
    signal rvalid  : in  std_logic;
    signal rdata   : in  std_logic_vector (31 downto 0)
    ) is
  begin
    rready  <= '0';
    arvalid <= '1';
    araddr  <= std_logic_vector(to_unsigned(addr, araddr'length));
    wait until rising_edge(clk) and arready = '1';
    arvalid <= '0';
    rready  <= '1';
    wait until rising_edge(clk) and rvalid = '1';
    data    := rdata;
  end axilite_read;

end package body pl_reg_pkg;
'''

# c header
c_header = '''#ifndef PL_REGS_H
#define PL_REGS_H

#include "xil_io.h"
#include "xparameters.h"
'''
c_reg_addr = '#define {:{}} {}U\n'
c_mask = '#define {:{}} 0x{}U\n'
c_read_write_fn = '''
/* Write to a PL Register */
#define PL_WriteReg(RegOffset, RegisterValue) \\
	Xil_Out32((XPAR_M_AXI_REG_BASEADDR) + (RegOffset), (RegisterValue))

/* Read from a PL Register */
#define PL_ReadReg(RegOffset) \\
	Xil_In32((XPAR_M_AXI_REG_BASEADDR) + (RegOffset))
'''
c_footer='''
#endif
'''
