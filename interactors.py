import logging
import subprocess


LOGGER = logging.getLogger(__name__)


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

