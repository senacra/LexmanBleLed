"""Platform for light integration."""
import logging
import subprocess

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
# Import the device class from the component that you want to support
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_HS_COLOR,
    ATTR_WHITE_VALUE,
    PLATFORM_SCHEMA,
    Light,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_WHITE_VALUE
)
import homeassistant.util.color as color_util


LOGGER = logging.getLogger(__name__)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required('address'): cv.string,
    vol.Required('name'): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    add_entities([BleRGBWLight(config['address'], config['name'])])


class BleRGBWLight(Light):

    def __init__(self, address, name):
        self._address = address
        self._interactor = GATTToolRGBWInteractor(address)
        self._name = name
        # TODO: can we interrogate device for state here?
        self._state = False
        self._brightness = 255
        self._hs_color = [0., 0.]
        self._white_value = 0

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def brightness(self):
        """Return the brightness of the light.
        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        return self._brightness

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    @property
    def hs_color(self):
        return self._hs_color

    @property
    def white_value(self):
        return self._white_value

    def turn_on(self, **kwargs):
        """Instruct the light to turn on.
        You can skip the brightness part if your light does not support
        brightness control.
        """
        if not self._state:
            self._interactor.set_on()
            self._state = True

        if ATTR_BRIGHTNESS in kwargs or ATTR_HS_COLOR in kwargs:
            # Controlling color brightness or color
            self._brightness = kwargs.get(ATTR_BRIGHTNESS, self._brightness)
            self._hs_color = kwargs.get(ATTR_HS_COLOR, self._hs_color)
            rgb = color_util.color_hsv_to_RGB(*self._hs_color, self._brightness * 100 / 255)
            # TODO: support changing pixel order
            LOGGER.warning(f'Sending RGB value {rgb}')
            self._interactor.set_color(*rgb)

        if ATTR_WHITE_VALUE in kwargs:
            self._white_value = kwargs.get(ATTR_WHITE_VALUE, self._white_value)
            LOGGER.warning(f'Sending white value {self._white_value}')
            self._interactor.set_white(self._white_value)

    def turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        if self._state:
            self._interactor.set_off()
            self._state = False

    def update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        pass

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR | SUPPORT_WHITE_VALUE


class GATTToolRGBWInteractor(object):
    executable = 'gatttool'
    control_handle = '0x0007'

    def __init__(self, address):
        self.address = address

    def write(self, handle, value):
        LOGGER.warning(f'Sending value {value}')
        command = [self.executable, '-b', self.address, '--char-write-req', f'--handle={handle}', f'--value={value}']
        for n in range(5):
            try:
                subprocess.run(command, capture_output=True, check=True)
                break
            except subprocess.CalledProcessError as e:
                LOGGER.warning(f'Command failed attempt {n} - {e}')


    def set_on(self):
        self.write(self.control_handle, 'cc2333')

    def set_off(self):
        self.write(self.control_handle, 'cc2433')

    def set_color(self, red_value, green_value, blue_value):
        self.write(self.control_handle, f'56{red_value:02x}{green_value:02x}{blue_value:02x}00f0aa')

    def set_white(self, white_value):
        self.write(self.control_handle, f'56000000{white_value:02x}0faa')
