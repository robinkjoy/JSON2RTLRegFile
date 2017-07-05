library IEEE;
use IEEE.std_logic_1164.all;
use IEEE.numeric_std.all;
use IEEE.math_real.ceil;

library xpm;
use xpm.vcomponents.all;

entity cdc_sync is
  generic (
    WIDTH      : natural := 1;
    WITH_VLD   : boolean := false;
    SRC_PER_NS : real    := 5.0;
    DST_PER_NS : real    := 8.0;
    DAT_IS_REG : boolean := true;
    IS_PULSE   : boolean := false
    );
  port (
    src_clk : in  std_logic;
    src_dat : in  std_logic_vector (WIDTH-1 downto 0);
    src_vld : in  std_logic;
    dst_clk : in  std_logic;
    dst_dat : out std_logic_vector (WIDTH-1 downto 0);
    dst_vld : out std_logic
    );
end entity cdc_sync;

architecture behav of cdc_sync is

  constant PULSE_EXT : natural := integer(ceil(1.5*DST_PER_NS/SRC_PER_NS));
  type st_array is array (1 to PULSE_EXT) of std_logic;

  function or_reduce(a : st_array) return std_logic is
    variable ret : std_logic := '0';
  begin
    for i in a'range loop
      ret := ret or a(i);
    end loop;
    return ret;
  end function or_reduce;

  signal dat_reg     : std_logic_vector (WIDTH-1 downto 0) := (others => '0');
  signal pulse_array : st_array                            := (others => '0');

  signal vld_array : st_array  := (others => '0');
  signal vld_in    : std_logic := '0';
  signal vld_reg   : std_logic := '0';

begin

  -- Register incoming signal wrt source clock
  NO_VLD_NO_REG : if not IS_PULSE and not WITH_VLD and not DAT_IS_REG generate
    process (src_clk)
    begin
      if rising_edge(src_clk) then
        dat_reg <= src_dat;
      end if;
    end process;
  end generate NO_VLD_NO_REG;

  -- Already registered incoming signal wrt source clock
  NO_VLD_REG : if not IS_PULSE and not WITH_VLD and DAT_IS_REG generate
    dat_reg <= src_dat;
  end generate NO_VLD_REG;

  -- Register incoming signal wrt source clock when valid
  REG_VLD_DAT : if WITH_VLD generate
    process (src_clk)
    begin
      if rising_edge(src_clk) then
        if src_vld = '1' then
          dat_reg <= src_dat;
        end if;
      end if;
    end process;
  end generate REG_VLD_DAT;

  -- Extend pulses to 1.5x of dst period and register wrt source clock
  PULSE_REG : if IS_PULSE generate
    process (src_clk)
    begin
      if rising_edge(src_clk) then
        dat_reg(0) <= or_reduce(pulse_array);
        for i in 1 to PULSE_EXT loop
          if i = 1 then
            pulse_array(i) <= src_dat(0);
          else
            pulse_array(i) <= pulse_array(i-1);
          end if;
        end loop;
      end if;
    end process;
  end generate PULSE_REG;

  -- Extend valid to 1.5x of dst period and register wrt source clock
  REG_VLD : if WITH_VLD generate
    process (src_clk)
    begin
      if rising_edge(src_clk) then
        vld_reg <= or_reduce(vld_array);
        for i in 1 to PULSE_EXT loop
          if i = 1 then
            vld_array(i) <= src_vld;
          else
            vld_array(i) <= vld_array(i-1);
          end if;
        end loop;
      end if;
    end process;
  end generate REG_VLD;

  -- Synchronizers
  -- Sync valid
  SYNC_VLD : if WITH_VLD generate
    cdc_vld : xpm_cdc_single
      generic map (
        DEST_SYNC_FF   => 4,  -- integer; range: 2-10
        SIM_ASSERT_CHK => 1,  -- integer; 0=disable simulation messages, 1=enable simulation messages
        SRC_INPUT_REG  => 0   -- integer; 0=do not register input, 1=register input
        )
      port map (
        src_clk  => src_clk,  -- optional; required when SRC_INPUT_REG = 1
        src_in   => vld_reg,
        dest_clk => dst_clk,
        dest_out => dst_vld
        );
  end generate SYNC_VLD;

  -- sync data if not pulse
  SYNC_DAT : if not IS_PULSE generate
    cdc_vld : xpm_cdc_array_single
      generic map (

        -- Common module generics
        DEST_SYNC_FF   => 4,      -- integer; range: 2-10
        SIM_ASSERT_CHK => 1,      -- integer; 0=disable simulation messages, 1=enable simulation messages
        SRC_INPUT_REG  => 0,      -- integer; 0=do not register input, 1=register input
        WIDTH          => WIDTH   -- integer; range: 1-1024
        )
      port map (
        src_clk  => src_clk,  -- optional; required when SRC_INPUT_REG = 1
        src_in   => dat_reg,
        dest_clk => dst_clk,
        dest_out => dst_dat
        );
  end generate SYNC_DAT;

  -- sync data if pulse
  SYNC_PULSE : if IS_PULSE generate
    cdc_pulse : xpm_cdc_pulse
      generic map (
        -- Common module generics
        DEST_SYNC_FF   => 4,  -- integer; range: 2-10
        REG_OUTPUT     => 1,  -- integer; 0=disable registered output,   1=enable registered output
        RST_USED       => 0,  -- integer; 0=no reset, 1=implement reset
        SIM_ASSERT_CHK => 0   -- integer; 0=disable simulation messages, 1=enable simulation messages
        )
      port map (
        src_clk    => src_clk,
        src_rst    => '0',             -- optional; required when RST_USED = 1
        src_pulse  => dat_reg(0),
        dest_clk   => dst_clk,
        dest_rst   => '0',             -- optional; required when RST_USED = 1
        dest_pulse => dst_dat(0)
        );
  end generate SYNC_PULSE;

end behav;
