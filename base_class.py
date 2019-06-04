import math
from typing import List

from my_fc.flagbyte import FlagByte


class BaseClass:
    def __init__(self):
        self._memory: bytearray = bytearray(int(math.pow(2, 16)))

    def run(self):
        pass

    @property
    def memory(self):
        return self._memory

    @memory.setter
    def memory(self, index, data):
        if isinstance(index, int):
            self._memory[index] = data
        elif isinstance(index, slice):
            start = index.start
            stop = index.stop
            self._memory[start:stop] = data

    def execute(self):
        pass

    def eight_digit(self, data):
        return data % 256

    def hex_digit(self, data):
        return data % 65536

    def number_from_bytes(self, byte_list: List[int], *, signed=False):
        """
        [1]                     => 1
        [0, 1]                  => 256
        [255]                   => 255
        [255], signed=True      => -1
        [255, 255], signed=True => -1
        [256]                   => 因为 256 > 255 所以 raise Exception
        """
        bs = bytes(byte_list)
        return int.from_bytes(bs, 'little', signed=signed)

    @classmethod
    def low_high(cls, val):
        pc = FlagByte(val)
        return pc[0:8], pc[8:16]

    @classmethod
    def from_low_high_to_int(cls, low: int or bytes, high: int or bytes):
        v = FlagByte(0x0)
        v[0:8] = low
        v[8:16] = high
        return v.value

    @classmethod
    def split_number(cls, num: int):
        n = FlagByte(num)
        low, high = n[0:8], n[8:16]
        return low, high
