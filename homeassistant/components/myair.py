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

REQUIREMENTS = ['pymyair==0.1.0']

DOMAIN = 'myair'

DATA_MYAIR = 'myair'

CONF_IP = 'ip'
CONF_PORT = 'port'


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_IP): cv.string,
        vol.Required(CONF_PORT, default=2025): vol.All(vol.Coerce(int), vol.Range(min=1))
    })
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    _LOGGER.debug("proceeding with discovery")
    for platform in ['climate', 'sensor']:
        discovery.load_platform(hass, platform, DOMAIN, {CONF_IP: config[DOMAIN].get(CONF_IP), CONF_PORT: config[DOMAIN].get(CONF_PORT)}, config)
    _LOGGER.debug("setup done")

    return True

