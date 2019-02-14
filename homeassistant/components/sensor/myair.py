from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import Entity


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Setup the sensor platform."""
        """Setup the MyAir Zoning"""
    if discovery_info is None:
        return

    conf_ip = discovery_info.get(CONF_IP)
    conf_port = discovery_info.get(CONF_PORT)
    
    # connect to myair in order to create 1 climate entity per AC unit controlled by the system
    # often only one AC unit, but the controller is capable of controlling multiple
    from pymyair.pymyair import MyAir
    myair = MyAir(conf_ip,conf_port)
    myair.update()
    units = myair.system['aircons']

    ac_units = [MyAirACUnit(conf_ip, conf_port, aircon=unit)
         for unit in units]
    
    zones = []

    # For each AC unit, enumerate zones
    for unit in ac_units:
        unit.update()
        for zone in unit.myair_system.zones:
            zones += [MyAirTemperatureSensor(zone, unit)]

    add_entities(
        zones,
        True
        )


class MyAirTemperatureSensor(Entity):
    """Representation of a Sensor."""

    def __init__(self, myair_system, zoneid):
        """Initialize the sensor."""
        self._state = None
        self.myair_system = myair_system
        self.zoneid = zoneid
        self._name = "Zone %s" % zoneid

    @property
    def name(self):
        """Return the name of the sensor."""
        return _name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    def update(self):
        """Fetch new state data for the sensor.

        This is the only method that should fetch new data for Home Assistant.
        """
        self.myair_system.update()
        self._state = self.myair_system.zones[self.zoneid]['currentTemp']