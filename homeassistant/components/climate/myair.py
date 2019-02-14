"""
Support for MyAir AC Zoning Control.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/climate.myair/
"""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant.components.climate import (
    STATE_AUTO, STATE_COOL, STATE_HEAT, ClimateDevice,
    PLATFORM_SCHEMA, ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW,
    ATTR_TEMPERATURE, SUPPORT_TARGET_TEMPERATURE, SUPPORT_OPERATION_MODE,
    SUPPORT_FAN_MODE, SUPPORT_ON_OFF)
from homeassistant.const import (
    TEMP_CELSIUS, TEMP_FAHRENHEIT,
    CONF_SCAN_INTERVAL, STATE_ON, STATE_OFF, STATE_UNKNOWN)
import json

DOMAIN = 'myair'

CONF_IP = 'ip'
CONF_PORT = 'port'

STATE_DRY = 'dry'
STATE_FAN_ONLY = 'fan'

SUPPORT_FLAGS_UNIT = (SUPPORT_FAN_MODE | SUPPORT_OPERATION_MODE | SUPPORT_ON_OFF )
SUPPORT_FLAGS_ZONE = ( SUPPORT_TARGET_TEMPERATURE | SUPPORT_ON_OFF )


#DEPENDENCIES = ['pymyair']
_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_IP): cv.string,
    vol.Required(CONF_PORT, default=2025): cv.port,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the MyAir Zoning"""
    if discovery_info is None:
        return

    temp_unit = hass.config.units.temperature_unit
    
    conf_ip = discovery_info.get(CONF_IP)
    conf_port = discovery_info.get(CONF_PORT)

    _LOGGER.info("got conf: %s" % ( conf_ip ) )
    
    # connect to myair in order to create 1 climate entity per AC unit controlled by the system
    # often only one AC unit, but the controller is capable of controlling multiple
    from pymyair.pymyair import MyAir
    myair = MyAir(conf_ip,conf_port)
    myair.update()
    units = myair.system['aircons']

    ac_units = [MyAirACUnit(conf_ip, conf_port, aircon=unit)
         for unit in units]
    add_entities(
        ac_units,
        True
        )
    
    zones = []

    for unit in ac_units:
        unit.update()
        for zone in unit.myair_system.zones:
            zones += [MyAirZone(zone, unit)]

    # For each AC unit, enumerate zones
    add_entities(
        zones,
        True
        )

class MyAirACUnit(ClimateDevice):
    """Representation of a MyAir Controller."""

    def __init__(self, ip, port, aircon):
        from pymyair.pymyair import MyAir

        self.myair_system = MyAir(ip,port,aircon=aircon)
        self._fan_list = ['low', 'medium', 'high', STATE_AUTO]
        self._operation_list = [STATE_OFF, STATE_HEAT, STATE_COOL, STATE_DRY, STATE_FAN_ONLY]

        self._has_fan = True

        # data attributes
        self._humidity = None
        self._target_temperature = None
        self._temperature = None
        self._temperature_scale = TEMP_CELSIUS
        self._mode = None
        self._fan = None
        self._is_locked = None
        self._locked_temperature = None

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS_UNIT

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        if self._mode in [STATE_HEAT, STATE_COOL, STATE_DRY, STATE_FAN_ONLY, STATE_OFF]:
            return self._mode
        else:
            return STATE_UNKNOWN

    @property
    def temperature_unit(self):
        return self._temperature_scale

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._temperature
    
    def update(self):
        """Cache value from MyAir"""
        #zone_state = self.myair_system.getZone(self.zone_id)
        #system_mode = self.myair_system.getMode()
        #self._name = zone_state.get('name')
        self.myair_system.update()
        self._mode = self.myair_system.mode
        #TODO myzone? self._target_temperature = 
        #TODO myzone? self._temperature = self.myair_system.

class MyAirZone(ClimateDevice):
    """Representation of a MyAir Zone."""

    def __init__(self, zone_id, myair_controller):
        """Initialize the thermostat."""
        self.zone_id = zone_id
        self.myair_system = myair_controller.myair_system
        self._name = ("Zone %s" % (zone_id))

        # data attributes
        self._humidity = None
        self._target_temperature = None
        self._temperature = None
        self._temperature_scale = TEMP_CELSIUS
        self._mode = None
        self._fan = None
        self._is_locked = None
        self._locked_temperature = None


    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS_ZONE
           
    @property
    def name(self):
        """Return the name of the zone, if any."""
        return self._name

    @property
    def temperature_unit(self):
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
        self.myair_system.update()
        #self._name = zone_state.get('name')
        #self._mode = self.myair_system.mode  
        #self._target_temperature = self.myair_system.zones[self.zoneid]['setTemp']
        #self._temperature = self.myair_system.zones[self.zoneid]['actualTemp']


