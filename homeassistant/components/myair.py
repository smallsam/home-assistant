"""
Support for MyAir devices.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/myair/
"""
import logging
import socket

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.const import (CONF_STRUCTURE, CONF_FILENAME)
from homeassistant.loader import get_component

_CONFIGURING = {}
_LOGGER = logging.getLogger(__name__)

DOMAIN = 'myair'

DATA_MYAIR = 'myair'

CONF_IP = 'ip'
CONF_PORT = 'port'
CONF_KEY = 'key'
CONF_NAME = 'name'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_IP): cv.string,
        vol.Required(CONF_PORT): vol.All(vol.Coerce(int), vol.Range(min=1)),,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_KEY): cv.string
    })
})

def setup(hass, config):
    """Setup the Myair component."""

    import myair

    conf = config[DOMAIN]

    _LOGGER.debug("proceeding with setup")

    conf = config[DOMAIN]
    conf_ip = conf[CONF_IP]
    conf_port = conf[CONF_PORT]
    conf_key = conf[CONF_KEY]

    myair = myair.MyAir(conf_ip,conf_port,conf_key)
    
    hass.data[DATA_MYAIR] = MyAirDevice(hass, conf, myair)
    
    _LOGGER.debug("proceeding with discovery")
    discovery.load_platform(hass, 'climate', DOMAIN, {}, config)
    _LOGGER.debug("setup done")

    return True


class MyAirDevice(object):
    """Structure MyAir functions for hass."""

    def __init__(self, hass, conf, myair):
        """Init MyAir Devices."""
        self.hass = hass
        self._myair = myair

    def zones(self):
        """Generator returning list of devices and their location."""
        try:
            zonecount = self._myair.getZoneCount()
            for zoneid in range(1,zonecount+1):
                yield zoneid
        except socket.error:
            _LOGGER.error(
                "Connection error connecting to the myair system")

    @property
    def myair(self):
        return self._myair
    


