--
-- UART: transmitter
--
-- Copyrighted by Manuel Naranjo 2009 <manuel@aircable.net>
-- Copyrighted by Wincent Balin
-- Idea by Jean P. Nicolle
--

library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_arith.all;

entity UARTTransmitter is
	generic
	(
		freq_divider: integer := 138 -- freq/baud 16MHz/115200 do it manually
	);
	port
	(
		clk				: in std_logic;
		txd				: out std_logic;
		txd_data		: in std_logic_vector(7 downto 0);
		txd_start		: in std_logic;
		txd_busy		: out std_logic
	);
end entity UARTTransmitter;

architecture UARTTransmitterArch of UARTTransmitter is
-- defining types
type state_type is (idle, start, bit0, bit1, bit2, bit3, bit4, bit5, bit6, bit7, stop1, stop2, reset);
-- defining signals
signal state : state_type := idle; -- transmitter's state
signal data : std_logic_vector(7 downto 0);
signal baud_tick : std_logic;
signal busy : std_logic := '0';
signal baud_counter : integer range 0 to freq_divider:= 0;
constant baud_counter_limit : integer := freq_divider;

begin
	-- processes
	baud_gen : process(clk)
	begin
		if clk'event and clk = '1' then
			--if busy = '1' then
				baud_counter <= baud_counter + 1;
				if baud_counter >= baud_counter_limit then
					baud_tick <= '1';
					baud_counter <= 0;
				else
					baud_tick <= '0';
				end if;
			--else
			--	baud_counter <= 0;
			--end if;
		end if;
	end process baud_gen;
	--
	state_proc : process(clk)
	begin
		if clk'event and clk = '1' then
			case state is
				when idle =>
					if txd_start = '1' and baud_tick = '1' then --sync with baud tick
						state <= start;
					end if;
				when start =>
					if baud_tick = '1' then
						state <= bit0;
					end if;
				when bit0 =>
					if baud_tick = '1' then
						state <= bit1;
					end if;
				when bit1 =>
					if baud_tick = '1' then
						state <= bit2;
					end if;
				when bit2 =>
					if baud_tick = '1' then
						state <= bit3;
					end if;
				when bit3 =>
					if baud_tick = '1' then
						state <= bit4;
					end if;
				when bit4 =>
					if baud_tick = '1' then
						state <= bit5;
					end if;
				when bit5 =>
					if baud_tick = '1' then
						state <= bit6;
					end if;
				when bit6 =>
					if baud_tick = '1' then
						state <= bit7;
					end if;
				when bit7 =>
					if baud_tick = '1' then
						state <= stop1;
					end if;
				when stop1 =>
					if baud_tick = '1' then
						--state <= stop2;
						state <= reset;
					end if;
				when stop2 =>
					if baud_tick = '1' then
						state <= reset;
					end if;
				when reset =>
					if txd_start = '0' then --reset is not synced with uart clock, but it's in sync with global clock
						state <= idle;
					end if;
			end case;
		end if;
	end process state_proc;
	--
	data_load_proc : process(clk)
	begin
		if clk'event and clk = '1' then
			if txd_start = '1' and busy = '0' then --only load when we really can
				data <= txd_data;
			end if;
		end if;
	end process data_load_proc;
	--
	txd_proc : process(clk)
	begin
		if clk'event and clk = '1' then
			case state is
				when idle => txd <= '1';
				when start => txd <= '0';
				when bit0 => txd <= data(0);
				when bit1 => txd <= data(1);
				when bit2 => txd <= data(2);
				when bit3 => txd <= data(3);
				when bit4 => txd <= data(4);
				when bit5 => txd <= data(5);
				when bit6 => txd <= data(6);
				when bit7 => txd <= data(7);
				when stop1 => txd <= '1';
				when stop2 => txd <= '1';
				when reset => txd <= '1';
			end case;
		end if;
	end process txd_proc;
	--
	busy_proc : process(clk)
	begin
		if clk'event and clk = '1' then
			if state = idle or state = reset then
				busy <= '0'; txd_busy <= '0';
			else
				busy <= '1'; txd_busy <= '1';
			end if;
		end if;
	end process busy_proc;
end UARTTransmitterArch;


