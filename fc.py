import math

from my_fc.rom import ROM
from my_fc.cpu import Cpu
from my_fc.ppu import PPU


class FC:
    def __init__(self, argument=None, rom=None):
        from my_fc.mapper import BaseMapper

        self.rom: ROM = rom
        self.argument: list = argument
        self.ppu: PPU = PPU()
        self.cpu: Cpu = Cpu(self.ppu)
        self.mapper: BaseMapper = BaseMapper(self)

    def load_rom(self, rom_name: str = 'nestest.nes'):
        with open(rom_name, 'rb') as f:
            rom_info = f.read()
            self.rom = ROM(rom_info)
        self.load_mapper(self.rom.mapper_number)
        self.mapper.reset()

    def unload_rom(self):
        self.rom = None

    def run(self):
        self.cpu.running = True
        self.cpu.run()

    def load_mapper(self, _id: int):
        from my_fc.mapper import load_mapper
        return load_mapper(self, _id)

    def __str__(self):
        return "count_prgrom16kb: {}, count_chrrom_8kb: {}, mapper_number: {}".format(self.rom.count_prgrom16kb,
                                                                                      self.rom.count_chrrom_8kb,
                                                                                      self.rom.mapper_number)
