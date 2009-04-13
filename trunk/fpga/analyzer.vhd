----------------------------------------------------------------------------------
--
-- Description: Main module for a simple analyzer
--
-- Copyright (C) 2009  Manuel Francisco Naranjo <manuel@aircable.net>
-- Copyright (C) 2009  Martín Rassia
-- This program is free software; you can redistribute it and/or
-- modify it under the terms of the GNU General Public License
-- as published by the Free Software Foundation; either version 2
-- of the License, or (at your option) any later version.
-- 
-- This program is distributed in the hope that it will be useful,
-- but WITHOUT ANY WARRANTY; without even the implied warranty of
-- MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
-- GNU General Public License for more details.
-- 
-- You should have received a copy of the GNU General Public License
-- along with this program; if not, write to the Free Software
-- Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
--
----------------------------------------------------------------------------------
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

---- Uncomment the following library declaration if instantiating
---- any Xilinx primitives in this code.
--library UNISIM;
--use UNISIM.VComponents.all;
library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.STD_LOGIC_ARITH.ALL;
use IEEE.STD_LOGIC_UNSIGNED.ALL;

---- Uncomment the following library declaration if instantiating
---- any Xilinx primitives in this code.
--library UNISIM;
--use UNISIM.VComponents.all;

entity analyzer is
    Port (  
	    CLK : in  STD_LOGIC;
            TX : out  STD_LOGIC;
            led : out  STD_LOGIC_VECTOR (3 downto 0);
	    data : in STD_LOGIC_VECTOR (7 downto 0)
	);
end analyzer;

architecture Behavioral of analyzer is

	signal txd_data : std_logic_vector(7 downto 0);
	signal txd_start : std_logic := '0';
	signal txd_busy : std_logic;
	signal int_tx: std_logic;
	
	COMPONENT UARTTransmitter
	GENERIC
	(
			 freq_divider : integer
	);
	PORT(
			 clk : IN std_logic;
			 txd_data : IN std_logic_vector(7 downto 0);
			 txd_start : IN std_logic;
			 txd : OUT std_logic;
			 txd_busy : OUT std_logic
			 );
	END COMPONENT;

	type state_type is (idle, busy);

	signal state: state_type := idle;

begin

	-- instantiating components
	Inst_UARTTransmitter: UARTTransmitter
	GENERIC MAP
	(
		--freq_divider => 138 -- 16MHz / 115200
		freq_divider => 69 -- 16MHz / 230400
		--freq_divider => 35 -- 16MHz / 460800
	)
	PORT MAP(
		clk => clk,
		txd => int_tx,
		txd_data => txd_data,
		txd_start => txd_start,
		txd_busy => txd_busy
	);
	
	-- Connect signals
	TX<=int_tx;
	
	led <= data(3 downto 0);
		  
	-- Wait for UART to be ready, to push new data into it
	do_job: process(clk) is
	begin
		if clk='1' and clk'event then			
			if state=idle then
				txd_data ( 7 downto 0 ) <= data ( 7 downto 0 );
				txd_start <= '1';
			else 
				if txd_start = '1' then
					txd_start<='0'; -- if we don't lower it then we never restart the transmitter
				end if;
			end if;
		end if;
	end process;
	
	-- Keep state machine up to date
	busy_proc: process(clk) is
	begin
		if clk'event and clk='1'then
				if txd_busy='1' and state=idle then
					state <= busy;
				else 
					if txd_busy='0' and state = busy then
						state <= idle;
					end if;
				end if;
		end if;
	end process;

end Behavioral;

