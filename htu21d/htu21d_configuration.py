from micropython import const


class HTU21DConfiguration:
    """Configuration for the HTU21D Digital Relative Humidity sensor with Temperature output
    https://github.com/flrrth/pico-htu21d
    
    The datasheet can be found here: https://www.te.com/usa-en/product-CAT-HSC0004.html
    """
    
    # Resolution settings for relative humidity (RH) and temperature (T):
    RH_12_T_14_BIT = const(0)
    RH_8_T_12_BIT = const(1)
    RH_10_T_13_BIT = const(128)
    RH_11_T_11_BIT = const(129)
    
    # Heater settings:
    HEATER_ENABLED = const(4)
    HEATER_DISABLED = const(0)
    
    def __init__(self):
        self._measurement_resolution = HTU21DConfiguration.RH_12_T_14_BIT
        self._heater_enabled = HTU21DConfiguration.HEATER_DISABLED
        self._crc_enabled = True
        
    @property
    def measurement_resolution(self) -> int:
        """Get measurement_resolution."""
        return self._measurement_resolution
    
    @measurement_resolution.setter
    def measurement_resolution(self, measurement_resolution: int):
        """Set measurement_resolution."""
        self._measurement_resolution = measurement_resolution
    
    @property
    def heater_enabled(self) -> bool:
        """Get heater_enabled."""
        return bool(self._heater_enabled)
    
    @heater_enabled.setter
    def heater_enabled(self, enabled: bool):
        """Set heater_enabled."""
        if enabled:
            self._heater_enabled = HTU21DConfiguration.HEATER_ENABLED
        else:
            self._heater_enabled = HTU21DConfiguration.HEATER_DISABLED

    @property
    def crc_enabled(self) -> bool:
        """Get crc_enabled."""
        return self._crc_enabled
    
    @crc_enabled.setter
    def crc_enabled(self, crc_enabled: bool):
        """Set crc_enabled."""
        self._crc_enabled = crc_enabled
