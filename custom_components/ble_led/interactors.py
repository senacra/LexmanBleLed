import abc
import logging
import math
import subprocess

from btlewrap.bluepy import BluepyBackend
from btlewrap.base import BluetoothInterface

LOGGER = logging.getLogger(__name__)


class RGBWInteractor(abc.ABC):
    control_handle = 0x0007
    rgb_offsets = [5*8, 4*8, 3*8]
    rgb_base = 0x5600000000f0aa
    white_offset = 2*8
    white_base = 0x56000000000faa

    def __init__(self, address):
        self.address = address

    @abc.abstractmethod
    def _write(self, value):
        raise NotImplemented

    def set_on(self):
        self.write(0xcc2333)

    def set_off(self):
        self.write(0xcc2433)

    def set_color(self, *values):
        self.write(self.rgb_base + sum(
            v << o for v, o in zip(values, self.rgb_offsets)
        ))

    def set_white(self, value):
        self.write(self.white_base + (value << self.white_offset))


class GATTToolRGBWInteractor(RGBWInteractor):
    executable = 'gatttool'

    def _write(self, value):
        LOGGER.warning(f'Sending value {value}')
        command = [self.executable, '-b', self.address, '--char-write-req', f'--handle=0x{self.control_handle:04x}', f'--value={value:0x}']
        LOGGER.warning(f'Command is: {command}')
        for n in range(5):
            try:
                subprocess.run(command, capture_output=True, check=True)
                break
            except subprocess.CalledProcessError as e:
                LOGGER.warning(f'Command failed attempt {n} - {e}\n{e.stdout}\n{e.stderr}')


class BtlewrapRGBWInteractor(RGBWInteractor):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interface = BluetoothInterface(BluepyBackend)

    def _pack(self, value):
        num_bytes = math.ceil(value.bit_length() / 8)
        return value.to_bytes(num_bytes, byteorder='big')

    def _write(self, value):
        with self.interface.connect(self.address) as connection:
            connection.write_handle(self.control_handle, self._pack(value))
