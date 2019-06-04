from my_fc.fc import FC


class BaseMapper:
    _id = 0xFF

    def __init__(self, fc: FC):
        self.fc = fc
        self.fc.mapper = self

    def load_prgrom_8k(self, src: int, des: int):
        src_addr_start = src * 8 * 2014 + 0x8000

        des_addr_start = des * 8 * 2014
        des_addr_end = (des + 1) * 8 * 2014

        self.fc.cpu.memory[src_addr_start:] = self.fc.rom.data_prgrom[des_addr_start:des_addr_end]

    def load_chrrom_8k(self, src: int, des: int):
        src_addr_start = src * 8 * 1024
        src_addr_end = (src + 1) * 8 * 1024

        des_addr_start = des * 8 * 1024
        des_addr_end = (des + 1) * 8 * 1024

        self.fc.ppu.memory[src_addr_start:src_addr_end] = self.fc.rom.data_prgrom[des_addr_start:des_addr_end]

    def reset(self):
        pass


class Mapper0(BaseMapper):
    _id = 0x0

    def __init__(self, fc: FC):
        super(Mapper0, self).__init__(fc)

    def reset(self):
        if self.fc.rom.count_prgrom16kb == 0 or self.fc.rom.count_prgrom16kb > 2:
            raise ValueError('bad count: count_prgrom16kb is {}'.format(self.fc.rom.count_prgrom16kb))

        #     // 16KB -> 载入 $8000-$BFFF, $C000-$FFFF 为镜像
        #     // 32KB -> 载入 $8000-$FFFF
        count = self.fc.rom.count_prgrom16kb & 0x2

        self.load_prgrom_8k(0, 0)

        self.load_prgrom_8k(1, 1)

        self.load_prgrom_8k(2, count + 0)

        self.load_prgrom_8k(3, count + 1)

        self.load_chrrom_8k(0, 0)


def load_mapper(fc: FC, _id: 000):
    mapper_str = ''
    try:
        mapper_str = "Mapper{}(fc)".format(_id)
        mapper = eval(mapper_str)
    except:
        raise ValueError('{} no found'.format(mapper_str))

    return mapper


if __name__ == '__main__':
    print(3 & 0x2)
