from enum import IntFlag, unique


@unique
class Control1(IntFlag):
    VMIRROR = 0x01
    SAVERAM = 0x02
    TRAINER = 0x04
    FOUR_SCREEN = 0x08


@unique
class Control2(IntFlag):
    VS_UNISYSTEM = 0x01
    Playchoice10 = 0x02


class NesHeader:
    def __init__(self, header: bytes):
        if len(header) < 8:
            raise ValueError('length must bigger or equal 8')

        self.id: bytes = b'NES\x1a'
        if header[:4] != self.id:
            raise ValueError('unsupported header')

        self.count_prgrom16kb: int = header[4]  # 16k 程序只读储存器 数量, 一个字节
        self.count_chrrom_8kb: int = header[5]  # 8k 角色只读存储器 数量, 一个字节
        self.control1: int = header[6]  # 控制信息1, 一个字节
        self.control2: int = header[7]  # # 控制信息2, 一个字节
        self.reserved: bytes = header[7:16]  # # 保留数据, 8个字节

    @property
    def trainer(self):
        return self.control1 & Control1.TRAINER

    @property
    def mapper_number(self):
        return (self.control1 >> 4) | (self.control2 & 0xF0)

    @property
    def vmirroring(self):
        return (self.control1 & Control1.VMIRROR) > 0

    @property
    def four_screen(self):
        return (self.control1 & Control1.FOUR_SCREEN) > 0

    @property
    def save_ram(self):
        return (self.control1 & Control1.SAVERAM) > 0

    @property
    def vs_unisystem(self):
        return self.control2 & Control2.VS_UNISYSTEM

    @property
    def play_choice_10(self):
        return self.control2 & Control2.Playchoice10


class ROM:
    def __init__(self, rom: bytes):
        offset = 0
        header = NesHeader(rom[offset: offset + 16])
        offset += 16

        # TODO 实现对于 Trainer 的处理
        if header.trainer:
            offset += 512

        #  PRG-ROM 程序只读储存器 数据指针
        size1 = 16 * 1024 * header.count_prgrom16kb
        self.data_prgrom: bytes = rom[offset: offset + size1]
        offset += size1

        #  CHR-ROM 角色只读存储器 数据指针
        size2 = 8 * 1024 * header.count_chrrom_8kb
        self.data_chrrom: bytes = rom[offset: offset + size2]
        offset += size2

        #  16KB为单位 程序只读储存器 数据长度
        self.count_prgrom16kb: int = header.count_prgrom16kb

        #   8KB为单位 角色只读存储器 数据长度
        self.count_chrrom_8kb: int = header.count_chrrom_8kb

        #  Mapper 编号
        self.mapper_number: int = header.mapper_number

        #  是否Vertical Mirroring(否即为水平)
        self.vmirroring: int = header.vmirroring

        #  是否FourScreen
        self.four_screen: int = header.four_screen

        #  是否有SRAM(电池供电的)
        self.save_ram: int = header.save_ram

        #  保留以对齐
        self.reserved: int = header.reserved

        assert not header.trainer, "unsupported"
        assert not header.vs_unisystem, "unsupported"
        assert not header.play_choice_10, "unsupported"
