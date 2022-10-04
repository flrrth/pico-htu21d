import math

from micropython import const
from utime import sleep_ms

from .htu21d_configuration import HTU21DConfiguration


class HTU21D:
    """This class represents the HTU21D Digital Relative Humidity sensor
    https://github.com/flrrth/pico-htu21d
    
    The datasheet can be found here: https://www.te.com/usa-en/product-CAT-HSC0004.html.
    """

    # Constants used for dew point temperature calculation:
    A = const(8.1332)
    B = const(1762.39)
    C = const(235.66)

    def __init__(self, address, i2c, configuration=HTU21DConfiguration()):
        self._address = address
        self._i2c = i2c
        self.reset()
        self.configuration = configuration

    def reset(self):
        """Reset the HTU21D."""
        self._i2c.writeto(self._address, b'\xFE')
        sleep_ms(15)
        
    @property
    def configuration(self):
        """Get configuration."""
        return self._configuration
    
    @configuration.setter
    def configuration(self, configuration):
        """Set configuration.

        Keyword arguments:
        configuration -- the configuration
        """
        self._configuration = configuration
        data = bytearray(1)
        data[0] = configuration.measurement_resolution | 1 << 2 if configuration.heater_enabled else 0
        self._write_user_register(data)

    def _temperature(self) -> tuple[int, float, bool | None]:
        """Calculate temperature."""
        rxdata = bytearray(3)
        self._i2c.readfrom_mem_into(self._address, 0xE3, rxdata)        
        crc_ok = None
        
        if self._configuration.crc_enabled:
            crc_ok = self._crc_check("{0:b}".format(rxdata[0] << 8 | rxdata[1]), "{0:08b}".format(rxdata[2]))
            
        s_temp = rxdata[0] << 8 | ((rxdata[1] >> 2) << 2)
        temp = -46.85 + (175.72 * (s_temp / 65536))  # see datasheet page 15, 'Temperature conversion'.
        return s_temp, temp, crc_ok
    
    def _humidity(self) -> tuple[int, float, bool | None]:
        """Calculate humidity."""
        rxdata = bytearray(3)
        self._i2c.readfrom_mem_into(self._address, 0xE5, rxdata)
        crc_ok = None
        
        if self._configuration.crc_enabled:
            crc_ok = self._crc_check("{0:b}".format(rxdata[0] << 8 | rxdata[1]), "{0:08b}".format(rxdata[2]))

        s_rh = rxdata[0] << 8 | ((rxdata[1] >> 2) << 2)
        rh = -6 + (125 * (s_rh / 65536))  # see datasheet page 15, 'Relative Humidity conversion'.
        return s_rh, rh, crc_ok
    
    def _partial_pressure(self, temperature) -> float:
        """Calculate partial pressure."""
        return 10 ** (HTU21D.A - (HTU21D.B / (temperature + HTU21D.C)))
    
    def _dew_point(self, temperature, humidity) -> float:
        """Calculate dew point."""
        
        # See datasheet page 15, 'application: dew point temperature measurement'.
        return -1 * ((HTU21D.B / (math.log10(humidity * (self._partial_pressure(temperature) / 100)) - HTU21D.A)) + HTU21D.C)
    
    @property
    def measurements(self) -> dict:
        """Get measurements."""
        temperature = self._temperature()
        humidity = self._humidity()
        # see datasheet page 4, 'Temperature coefficient compensation equation'.
        humidity_compensated = humidity[1] + (-0.15 * (25 - temperature[1]))
        dew_point = self._dew_point(temperature[1], humidity_compensated)
        
        return {
            't': temperature[1],
            't_dew_point': dew_point,
            't_crc_ok': temperature[2],
            't_adc': temperature[0],
            'h': humidity_compensated,
            'h_crc_ok': humidity[2],
            'h_adc': humidity[0]
        }
    
    @property
    def user_register(self):
        """Get user_register."""
        rxdata = bytearray(1)
        self._i2c.readfrom_mem_into(self._address, 0xE7, rxdata)
        return rxdata[0]
    
    def _write_user_register(self, data: bytearray):
        """Write configuration to the user register.

        Keyword arguments:
        data -- the data to be written to the user register
        """
        # Read the current configuration: (see datasheet page 12, 'User register')
        current_config = self.user_register
        # Gather the reserved bits:
        reserved_bits = ((current_config >> 3) & 7) << 3
        # Create the new configuration with the original values of the reserved bits:
        rxdata = bytearray(1)
        rxdata[0] = ((data[0] >> 6) << 6) | reserved_bits | ((data[0] << 6) >> 6)
        
        self._i2c.writeto_mem(self._address, 0xE6, rxdata)

    def _crc_check(self, input_bitstring: str, check_value: str) -> bool:
        """Calculate the CRC check of a string of bits using a fixed polynomial.
        
        See https://en.wikipedia.org/wiki/Cyclic_redundancy_check
        
        Keyword arguments:
        input_bitstring -- the data to verify
        check_value -- the CRC received with the data
        """
        
        polynomial_bitstring = "100110001"  # See datasheet page 14, 'CRC for HTU21D(F) sensors using I²C Protocol'.
        len_input = len(input_bitstring)
        initial_padding = check_value
        input_padded_array = list(input_bitstring + initial_padding)
        
        while '1' in input_padded_array[:len_input]:
            cur_shift = input_padded_array.index('1')
            
            for i in range(len(polynomial_bitstring)):
                input_padded_array[cur_shift + i] = \
                    str(int(polynomial_bitstring[i] != input_padded_array[cur_shift + i]))
                
        return '1' not in ''.join(input_padded_array)[len_input:]
