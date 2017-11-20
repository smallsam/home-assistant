"""
Support for MyAir AC Zoning Control.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.myair/
"""
import logging

import voluptuous as vol

from homeassistant.components.nest import DATA_NEST
from homeassistant.components.climate import (
    STATE_AUTO, STATE_COOL, STATE_HEAT, ClimateDevice,
    PLATFORM_SCHEMA, ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW,
    ATTR_TEMPERATURE)
from homeassistant.const import (
    TEMP_CELSIUS, TEMP_FAHRENHEIT,
    CONF_SCAN_INTERVAL, STATE_ON, STATE_OFF, STATE_UNKNOWN)

#DEPENDENCIES = ['pymyair']
_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_SCAN_INTERVAL):
        vol.All(vol.Coerce(int), vol.Range(min=1)),
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the MyAir Zoning"""
    if discovery_info is None:
        return

    _LOGGER.debug("Setting up myair")

    temp_unit = hass.config.units.temperature_unit

    myairdevice = hass.data[DATA_MYAIR]

    add_devices(
        [MyAirZone(zoneid, myairdevice.myair)
         for zoneid in myairdevice.zones()],
        True
        )

class MyAirZone(ClimateDevice):
    """Representation of a MyAir Zone."""

    def __init__(self, zone_id, myair_system):
        """Initialize the thermostat."""
        self.name = None
        self.zone_id = zone_id
        self.myair_system = myair_system
        self._fan_list = ['low', 'medium', 'high', STATE_AUTO]
        self._operation_list = [STATE_OFF, STATE_HEAT, STATE_COOL, STATE_DRY, STATE_FAN_ONLY]

        # feature of device
        self._has_fan = True

        # data attributes
        self._name = None
        self._humidity = None
        self._target_temperature = None
        self._temperature = None
        self._temperature_scale = TEMP_CELSIUS
        self._mode = None
        self._fan = None
        self._is_locked = None
        self._locked_temperature = None

    @property
    def name(self):
        """Return the name of the zone, if any."""
        return self._name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._temperature_scale

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._temperature

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        if self._mode in [STATE_HEAT, STATE_COOL, STATE_DRY, STATE_FAN_ONLY, STATE_OFF]:
            return self._mode
        else:
            return STATE_UNKNOWN

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temp = kwargs.get(ATTR_TEMPERATURE)
        _LOGGER.debug("MyAir set_temperature-output-value=%s", temp)
        self.myair_system.setZone(self.zoneid, target=temp)

    def set_operation_mode(self, operation_mode):
        """Set operation mode."""
        if operation_mode in [STATE_HEAT, STATE_COOL, STATE_DRY, STATE_FAN_ONLY, STATE_OFF]:
            _LOGGER.debug("Myair set_operation-mode=%s", operation_mode)
            # TODO: changing one zone changes all zones operation mode, update refresh should reflect for all zones
            # This is confusing!! 
            if operation_mode in [STATE_ON, STATE_OFF]:
                self.myair_system.setZone(self.zoneid, state=operation_mode)
            else:
                self.myair_system.setSystem(state=operation_mode)
    @property
    def operation_list(self):
        """List of available operation modes."""
        return self._operation_list

    @property
    def current_fan_mode(self):
        """Return whether the fan is on."""
        if self._has_fan:
            # Return whether the fan is on
            return STATE_ON if self._fan else STATE_AUTO
        else:
            # No Fan available so disable slider
            return None

    @property
    def fan_list(self):
        """List of available fan modes."""
        return self._fan_list

    def set_fan_mode(self, fan):
        """Turn fan on/off."""
        self.device.fan = fan.lower()


    def update(self):
        """Cache value from MyAir"""
        zone_state = self.myair_system.getZone(self.zone_id)
        system_mode = self.myair_system.getMode()
        self._name = zone_state.get('name')
        self._temperature = zone_state.get('actualTemp')
        self._mode = self.myair_system.get('setting')
        self._target_temperature = zone_state.get('desiredTemp')
        self.operation_mode = system_mode

