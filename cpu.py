import math
from enum import IntFlag
from typing import List

from my_fc.flagbyte import FlagByte
from my_fc import opcodes
from my_fc import ppu
from my_fc import logdiffer
from my_fc import base_class


class Vector(IntFlag):
    NMI = 0xFFFA  # 不可屏蔽中断
    RESET = 0xFFFC  # 重置CP指针地址
    IRQBRK = 0xFFFE  # 中断重定向


class Registers:
    PC = 0  # Program Counter

    # A = 0  # Accumulator
    # X = 0  # Indexes
    # Y = 0  # Indexes
    # S = 0xFD  # Stack Pointer
    _INNER = bytearray([0, 0, 0, 0xFD])
    _P = FlagByte(0x24)  # Status Register
    r'''
    7  bit  0
    ---- ----
    NVss DIZC
    |||| ||||
    |||| |||+- Carry
    |||| ||+-- Zero
    |||| |+--- Interrupt Disable
    |||| +---- Decimal
    ||++------ No CPU effect, see: the B flag
    |+-------- Overflow
    +--------- Negative
    
    关于 B flag
    注意：第几位 是从 第 0 位 开始数的
    
    第 5 位永远为 1
    当 P 被 指令 PHP BRK 压入栈时， 压入的 P 的第 4 位被设置成 1
    当 P 由于 中断 \IRQ \NMI 被压入栈时， 压入的 P 的第 4 位被设置成 0
    当 P 被指令 PLP RTI 设置为栈中弹出的值时，不影响 第 4 5 位
    '''

    @property
    def A(self):
        return self._INNER[0]

    @A.setter
    def A(self, value):
        self._INNER[0] = value

    @property
    def X(self):
        return self._INNER[1]

    @X.setter
    def X(self, value):
        self._INNER[1] = value

    @property
    def Y(self):
        return self._INNER[2]

    @Y.setter
    def Y(self, value):
        self._INNER[2] = value

    @property
    def S(self):
        return self._INNER[3]

    @S.setter
    def S(self, value):
        self._INNER[3] = value

    @property
    def carry(self):
        return self._P[0]

    @carry.setter
    def carry(self, value):
        self._P[0] = value

    @property
    def zero(self):
        return self._P[1]

    @zero.setter
    def zero(self, value):
        self._P[1] = value

    @property
    def interrupt_disable(self):
        return self._P[2]

    @interrupt_disable.setter
    def interrupt_disable(self, value):
        self._P[2] = value

    @property
    def decimal(self):
        return self._P[3]

    @decimal.setter
    def decimal(self, value):
        self._P[3] = value

    @property
    def b_flag(self):
        return self._P[4]

    @b_flag.setter
    def b_flag(self, value):
        self._P[4] = value

    @property
    def overflow(self):
        return self._P[6]

    @overflow.setter
    def overflow(self, value):
        self._P[6] = value

    @property
    def negative(self):
        return self._P[7]

    @negative.setter
    def negative(self, value):
        self._P[7] = value

    @property
    def P(self):
        return self._P.value

    @P.setter
    def P(self, value):
        self._P = FlagByte(value)

    @classmethod
    def to_real_address(cls, sp):
        return sp | (0x01 << 8)


class Cpu(base_class.BaseClass):
    def __init__(self, ppu: ppu.PPU):
        super(Cpu, self).__init__()
        json_path = 'nestest_log.json'
        self.log_differ = logdiffer.LogDiffer.from_json(json_path)
        self._running = True
        self._count = 1

        self._memory: bytearray = bytearray(int(math.pow(2, 16)))
        self._registers = Registers()
        self._ppu = ppu

        self.address_len = {  # 寻址模式和其对应的字节数
            'ABS': 3,  # 绝对寻址
            'IMM': 2,  # 立即寻址
            'IMP': 1,  # 隐含寻址
            'ZPG': 2,  # 零页寻址
            'ABX': 3,  # 绝对 X 变址
            'ABY': 3,  # 绝对 Y 变址
            'INX': 2,  # 间接 X 变址
            'INY': 2,  # 间接 Y 变址
            'ZPX': 2,  # 零页 X 变址
            'ZPY': 2,  # 零页 Y 变址
            'REL': 2,  # 相对寻址
            'IND': 3,  # 间接寻址
        }

        self.opcodes = opcodes.codes

    @property
    def ppu(self):
        return self._ppu

    def run(self):
        # self._registers.PC = 0xC000  # TODO debug mode, 从第一个16k 的 programdata 的末端开始运行
        self._registers.PC = self.from_low_high_to_int(self._memory[0xFFFC], self._memory[0xFFFD])
        self._memory[0x2002] = 0b10100000

        while self._running:
            self.execute()

    def execute(self):
        # 在获取这一行指令的机器码前
        # 就取得各个寄存器的值（包括 PC)
        # 以和 nestest.log 对比
        # 当然，各个用来做键的字符串，要和下面展示的一样才可以（
        info = {
            'PC': self._registers.PC,
            'A': self._registers.A,
            'X': self._registers.X,
            'Y': self._registers.Y,
            'P': self._registers.P,
            'S': self._registers.S,
        }

        code = self.read_address(self._registers.PC)
        if code not in self.opcodes:
            raise ValueError('无法解析的操作命令')
        code_tuple = self.opcodes[code]
        ins, address_way = code_tuple

        address, data = self.to_real_address(address_way)
        # info['op'] = ins
        # info['address'] = address
        # #
        # # # 用存了以上信息的 info 调用 diff 方法
        # # # 第一次调用 diff() 方法，是和 log 的第一行进行比较
        # # # 第二次调用，则和第二行进行比较，以此类推
        # # # 所以像这样每次只传一行的信息进去即可
        # try:
        #     self.log_differ.diff(info)
        # except logdiffer.AllTestsPassed:
        #     # 通过所有测试之后会引发这个 AllTestsPassed 的自定义异常
        #     # 感谢 AD 聚聚友情 PR
        #     self._running = False

        # 测试PPU相关处理代码
        # print(self._count)
        # if self._count == 20000:
        #     d = [int(i) for i in self.ppu.memory[0x2000:0x23FF + 1]]
        #     if d == [32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 45, 45, 32, 82, 117, 110, 32, 97, 108, 108, 32, 116, 101, 115, 116,
        #              115, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 45, 45, 32, 66, 114, 97, 110,
        #              99, 104, 32, 116, 101, 115, 116, 115, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 45, 45, 32, 70, 108, 97, 103, 32, 116, 101, 115, 116, 115, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 45, 45, 32, 73, 109, 109, 101, 100, 105, 97, 116, 101,
        #              32, 116, 101, 115, 116, 115, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 45, 45, 32,
        #              73, 109, 112, 108, 105, 101, 100, 32, 116, 101, 115, 116, 115, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 45, 45, 32, 83, 116, 97, 99, 107, 32, 116, 101, 115, 116, 115, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 45, 45, 32, 65, 99, 99, 117, 109,
        #              117, 108, 97, 116, 111, 114, 32, 116, 101, 115, 116, 115, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 45, 45, 32, 40, 73, 110, 100, 105, 114, 101, 99, 116, 44, 88, 41, 32, 116, 101, 115, 116,
        #              115, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 45, 45, 32, 90, 101, 114, 111, 112, 97, 103, 101,
        #              32, 116, 101, 115, 116, 115, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 45, 45,
        #              32, 65, 98, 115, 111, 108, 117, 116, 101, 32, 116, 101, 115, 116, 115, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 45, 45, 32, 40, 73, 110, 100, 105, 114, 101, 99, 116, 41, 44, 89,
        #              32, 116, 101, 115, 116, 115, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 45, 45, 32, 65, 98, 115,
        #              111, 108, 117, 116, 101, 44, 89, 32, 116, 101, 115, 116, 115, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 45, 45, 32, 90, 101, 114, 111, 112, 97, 103, 101, 44, 88, 32, 116, 101, 115, 116,
        #              115, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 45, 45, 32, 65, 98, 115, 111, 108, 117,
        #              116, 101, 44, 88, 32, 116, 101, 115, 116, 115, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 85, 112, 47, 68, 111, 119, 110, 58, 32,
        #              115, 101, 108, 101, 99, 116, 32, 116, 101, 115, 116, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 83, 116, 97, 114, 116, 58, 32, 114, 117, 110, 32, 116, 101, 115, 116, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 83, 101, 108, 101, 99, 116, 58, 32, 73, 110, 118,
        #              97, 108, 105, 100, 32, 111, 112, 115, 33, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32,
        #              32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 32, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        #              0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        #              0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]:
        #         raise ValueError('成功啦')
        #     else:
        #         raise ValueError('失败啦')

        self.habdle_ins(ins, address, data)
        self._count += 1

    def habdle_ins(self, ins, address, data):
        if ins == 'JMP':
            self._registers.PC = address
        elif ins == 'BRK':
            self._running = False
            return
        elif ins == 'LDX':
            self._registers.X = data
            self.set_zero_negative(data)
        elif ins == 'STX':
            self.write_address(address, self._registers.X)
        elif ins == 'JSR':
            pc = self._registers.PC - 1
            self.push_stack(pc, hex_digit=True)
            self._registers.PC = address
        elif ins == 'SEC':
            self._registers.carry = 1
        elif ins == 'SEI':
            self._registers.interrupt_disable = 1
        elif ins == 'SED':
            self._registers.decimal = 1
        elif ins == 'BCS':
            if self._registers.carry == 1:
                self._registers.PC = address
        elif ins == 'CLC':
            self._registers.carry = 0
        elif ins == 'BCC':
            if self._registers.carry == 0:
                self._registers.PC = address
        elif ins == 'LDA':
            self._registers.A = data
            self.set_zero_negative(data)
        elif ins == 'BEQ':
            if self._registers.zero == 1:
                self._registers.PC = address
        elif ins == 'BNE':
            if self._registers.zero == 0:
                self._registers.PC = address
        elif ins == 'STA':
            self.write_address(address, self._registers.A)
        elif ins == 'STY':
            self.write_address(address, self._registers.Y)
        elif ins == 'BIT':
            zf = 0 if self._registers.A & data else 1
            self._registers.zero = zf
            self.set_negative(data)
            self.set_overflow(data)
        elif ins == 'BVS':
            if self._registers.overflow == 1:
                self._registers.PC = address
        elif ins == 'BVC':
            if self._registers.overflow == 0:
                self._registers.PC = address
        elif ins == 'BPL':
            if self._registers.negative == 0:
                self._registers.PC = address
        elif ins == 'RTS':
            pc = self.pop_stack(hex_digit=True)
            self._registers.PC = pc + 1
        elif ins == 'PHP':
            p = FlagByte(self._registers.P)
            p[4] = 1  # 当 P 被 指令 PHP BRK 压入栈时， 压入的 P 的第 4 位被设置成 1
            self.push_stack(p.value)
        elif ins == 'PLA':
            data_ = self.pop_stack()
            self.set_zero_negative(data_)
            self._registers.A = data_
        elif ins == 'PLP':
            data_ = FlagByte(self.pop_stack())
            # 用弹出的值的 第 0 1 2 3 6 7 位 来设置 P 的 第 0 1 2 3 6 7 位 的值
            pre_p = self._registers.P
            pre_p = FlagByte(pre_p)
            data_[4] = pre_p[4]
            data_[5] = pre_p[5]
            self._registers.P = data_.value
        elif ins == 'AND':
            a = self._registers.A
            a &= data
            self.set_zero_negative(a)
            self._registers.A = a
        elif ins == 'CMP':
            result = self._registers.A - data
            self.set_zero_negative(result)
            self.set_negative(result)
            self.set_carry(result >= 0)
        elif ins == 'CLD':
            self._registers.decimal = 0
        elif ins == 'PHA':
            self.push_stack(self._registers.A)
        elif ins == 'ORA':
            self._registers.A |= data
            self.set_zero_negative(self._registers.A)
        elif ins == 'CLV':
            self._registers.overflow = 0
        elif ins == 'EOR':
            self._registers.A ^= data
            self.set_zero_negative(self._registers.A)
        elif ins == 'ADC':
            a = self._registers.A
            result = self._registers.A + data + self._registers.carry
            self.set_carry(result >> 8)
            low, high = self.split_number(result)
            self._registers.A = low
            self.set_overflow_by_expression(not ((a ^ data) & 0x80) and ((a ^ low) & 0x80))
            self.set_zero_negative(low)
        elif ins == 'LDY':
            self._registers.Y = data
            self.set_zero_negative(data)
        elif ins == 'CPY':
            res = self._registers.Y - data
            self.set_carry(self._registers.Y >= data)
            self.set_zero_negative(res)
        elif ins == 'CPX':
            res = self._registers.X - data
            self.set_carry(self._registers.X >= data)
            self.set_zero_negative(res)
        elif ins == 'SBC':
            res = self._registers.A - data - (0 if self._registers.carry else 1)
            low, high = self.split_number(res)
            self.set_carry(not high)
            self.set_overflow_by_expression(((self._registers.A ^ data) & 0x80) & ((self._registers.A ^ high) & 0x80))
            self._registers.A = low
            self.set_zero_negative(low)
        elif ins == 'INY':
            res = self._registers.Y + 1
            res = self.eight_digit(res)
            self.set_zero_negative(res)
            self._registers.Y = res
        elif ins == 'INX':
            res = self._registers.X + 1
            res = self.eight_digit(res)
            self.set_zero_negative(res)
            self._registers.X = res
        elif ins == 'DEY':
            res = self._registers.Y - 1
            res = self.eight_digit(res)
            self.set_zero_negative(res)
            self._registers.Y = res
        elif ins == 'DEX':
            res = self._registers.X - 1
            res = self.eight_digit(res)
            self.set_zero_negative(res)
            self._registers.X = res
        elif ins == 'TAY':
            res = self._registers.A
            self.set_zero_negative(res)
            self._registers.Y = res
        elif ins == 'TAX':
            res = self._registers.A
            self.set_zero_negative(res)
            self._registers.X = res
        elif ins == 'TYA':
            res = self._registers.Y
            self.set_zero_negative(res)
            self._registers.A = res
        elif ins == 'TXA':
            res = self._registers.X
            self.set_zero_negative(res)
            self._registers.A = res
        elif ins == 'TSX':
            res = self._registers.S
            self.set_zero_negative(res)
            self._registers.X = res
        elif ins == 'TXS':
            res = self._registers.X
            self._registers.S = res
        elif ins == 'RTI':
            p = self.pop_stack()
            p = FlagByte(p)
            p[4] = self._registers.b_flag
            p[5] = 1
            self._registers.P = p.value
            self._registers.PC = self.pop_stack(hex_digit=True)
        elif ins == 'LSR':
            if address != -1:
                a = data
            else:
                a = self._registers.A
            self._registers.carry = a & 1
            a >>= 1
            a = self.eight_digit(a)
            self.set_zero_negative(a)
            if address != -1:
                self.write_address(address, a)
            else:
                self._registers.A = a
        elif ins == 'ASL':
            if address != -1:
                a = data
            else:
                a = self._registers.A
            self._registers.carry = a >> 7
            a <<= 1
            a = self.eight_digit(a)
            self.set_zero_negative(a)
            if address != -1:
                self.write_address(address, a)
            else:
                self._registers.A = a
        elif ins == 'ROR':
            if address != -1:
                a = data
            else:
                a = self._registers.A
            zero = a & 1
            a >>= 1
            a ^= self._registers.carry << 7
            self._registers.carry = zero
            a = self.eight_digit(a)
            self.set_zero_negative(a)
            if address != -1:
                self.write_address(address, a)
            else:
                self._registers.A = a
        elif ins == 'ROL':
            if address != -1:
                a = data
            else:
                a = self._registers.A
            seven = (a & 1 << 7) >> 7
            a <<= 1
            a ^= self._registers.carry
            self._registers.carry = seven
            a = self.eight_digit(a)
            self.set_zero_negative(a)
            if address != -1:
                self.write_address(address, a)
            else:
                self._registers.A = a
        elif ins == 'NOP':
            pass
        elif ins == 'BMI':
            if self._registers.negative == 1:
                self._registers.PC = address
        elif ins == "INC":
            d = self.eight_digit(data + 1)
            self.set_zero_negative(d)
            self.write_address(address, d)
        elif ins == "DEC":
            d = self.eight_digit(data - 1)
            self.set_zero_negative(d)
            self.write_address(address, d)
        elif ins == 'LAX':
            self._registers.X = self._registers.A = data
            self.set_zero_negative(data)
        elif ins == 'SAX':
            self.write_address(address, self._registers.A & self._registers.X)
        elif ins == 'DCP':
            data -= 1
            data = self.eight_digit(data)
            self.write_address(address, data)
            result = self.hex_digit(self._registers.A - data)
            self.set_carry(result < 0x100)
            self.set_zero_negative(self.eight_digit(result))
        elif ins == 'ISB':
            data += 1
            data = self.eight_digit(data)
            self.write_address(address, data)

            resul16 = self.hex_digit(self._registers.A - data - (0 if self._registers.carry else 1))
            self.set_carry(not resul16 >> 8)
            result8 = self.eight_digit(resul16)
            A = self._registers.A
            self.set_overflow_by_expression(((A ^ result8) & 0x80) and ((A ^ data) & 0x80))
            self._registers.A = result8
            self.set_zero_negative(result8)
        elif ins == 'SLO':
            self.set_carry(data >> 7)
            data <<= 1
            data = self.eight_digit(data)
            self.write_address(address, data)
            self._registers.A |= data
            self.set_zero_negative(self._registers.A)
        elif ins == 'RLA':
            data <<= 1
            data = self.hex_digit(data)
            if self._registers.carry:
                data |= 0x1
            self.set_carry(data > 0xff)
            result8 = self.eight_digit(data)
            self.write_address(address, result8)
            a = self._registers.A & result8
            self.set_zero_negative(a)
            self._registers.A = a
        elif ins == 'SRE':
            self.set_carry(data & 1)
            data >>= 1
            data = self.eight_digit(data)
            self.write_address(address, data)
            a = self._registers.A
            a ^= data
            self.set_zero_negative(a)
            self._registers.A = a
        elif ins == 'RRA':
            if self._registers.carry:
                data |= 0x100
            self._registers.carry = data & 1
            data >>= 1
            self.write_address(address, self.eight_digit(data))

            a = self._registers.A
            resul16 = a + data + (1 if self._registers.carry else 0)
            self.set_carry(resul16 >> 8)
            result8 = self.eight_digit(resul16)
            self.set_overflow_by_expression(not ((a ^ data) & 0x80) and ((a ^ result8) & 0x80))
            self._registers.A = result8
            self.set_zero_negative(result8)
        else:
            raise NotImplementedError("稍等一下, {} 指令还没实现".format(ins))

    def set_negative(self, data):
        data = FlagByte(data)
        negative = data[7]
        self._registers.negative = negative

    def set_overflow(self, data):
        data = FlagByte(data)
        overflow = data[6]
        self._registers.overflow = overflow

    def set_overflow_by_expression(self, expression):
        self._registers.overflow = 1 if expression else 0

    def set_zero_negative(self, data):
        if data == 0:
            self._registers.zero = 1
        else:
            self._registers.zero = 0

        self.set_negative(data)

    def set_carry(self, expression):
        self._registers.carry = 1 if expression else 0

    def to_real_address(self, address: str):
        '''
        :param address:
        :return: real_address, data
        '''
        old_pc = self._registers.PC
        self._registers.PC += self.address_len[address]
        m = self._memory
        pc = self._registers.PC

        def safe_fetch(addr):
            if addr > len(self._memory) - 1 or addr < 0:
                return -1
            else:
                return self._memory[addr]

        if address == 'ABS':
            addr = m[old_pc + 1] | (m[old_pc + 2]) << 8
            return addr, safe_fetch(addr)
        elif address == 'IMP':
            return -1, -1
        elif address == 'IMM':
            addr = m[old_pc + 1]
            return addr, addr
        elif address == 'ZPG':
            addr = m[old_pc + 1] | (0x00 << 8)
            return addr, safe_fetch(addr)
        elif address == 'REL':
            addr = pc + self.number_from_bytes([m[old_pc + 1]], signed=True)
            return addr, safe_fetch(addr)
        elif address == 'ABX':
            addr = self._registers.X + (m[old_pc + 1] | (m[old_pc + 2] << 8))
            return addr, safe_fetch(addr)
        elif address == 'ABY':
            addr = self._registers.Y + (m[old_pc + 1] | (m[old_pc + 2] << 8))
            addr = self.hex_digit(addr)
            return addr, safe_fetch(addr)
        elif address == 'INX':
            ind_x = m[old_pc + 1] + self._registers.X
            addr = m[self.eight_digit(ind_x)] | (m[self.eight_digit(ind_x + 1)] << 8)
            return addr, safe_fetch(addr)
        elif address == 'INY':
            tmp = m[old_pc + 1]
            addr = m[self.eight_digit(tmp)] | (m[self.eight_digit(tmp + 1)] << 8)
            addr += self._registers.Y
            addr = self.hex_digit(addr)
            return addr, safe_fetch(addr)
        elif address == 'IND':
            addr = m[old_pc + 1] | m[old_pc + 2] << 8
            addr2 = (addr & 0xFF00) | ((addr + 1) & 0x00FF)
            real_addr = m[addr] | (m[addr2] << 8)
            return real_addr, safe_fetch(real_addr)
        elif address == 'ZPX':
            addr = (m[old_pc + 1] + self._registers.X) & 0xFF
            return addr, safe_fetch(addr)
        elif address == 'ZPY':
            addr = (m[old_pc + 1] + self._registers.Y) & 0xFF
            return addr, safe_fetch(addr)
        else:
            return -1, -1

    def read_address(self, address: int):
        '''
        CPU 地址空间
    +---------+-------+-------+-----------------------+
    | 地址    | 大小  | 标记  |         描述          |
    +---------+-------+-------+-----------------------+
    | $0000   | $800  |       | RAM                   |
    | $0800   | $800  | M     | RAM                   |
    | $1000   | $800  | M     | RAM                   |
    | $1800   | $800  | M     | RAM                   |
    | $2000   | 8     |       | Registers             |
    | $2008   | $1FF8 | R     | Registers             |
    | $4000   | $20   |       | Registers             |
    | $4020   | $1FDF |       | Expansion ROM         |
    | $6000   | $2000 |       | SRAM                  |
    | $8000   | $4000 |       | PRG-ROM               |
    | $C000   | $4000 |       | PRG-ROM               |
    +---------+-------+-------+-----------------------+
    标记图例: M = $0000的镜像
              R = $2000-2008 每 8 bytes 的镜像
            (e.g. $2008=$2000, $2018=$2000, etc.)
        :param address:
        :return:
        '''
        if address in self._ppu.ADD_range:
            return self._ppu.read_address_from_cpu(address)
        else:
            return self._memory[address]

    def write_address(self, address: int, data):
        if address in self._ppu.ADD_range:
            self._ppu.write_address_from_cpu(address, data)
        else:
            self._memory[address] = data

    def push_stack(self, data, hex_digit=False):
        sp = self._registers.S
        if hex_digit is True:
            low, high = self.low_high(data)
            self.write_address(self._registers.to_real_address(sp), high)
            self.write_address(self._registers.to_real_address(sp - 1), low)
            self._registers.S -= 2
        else:
            self.write_address(self._registers.to_real_address(sp), data)
            self._registers.S -= 1

    def pop_stack(self, hex_digit=False):
        sp = self._registers.S
        if hex_digit is True:
            low = self.read_address(self._registers.to_real_address(sp + 1))
            high = self.read_address(self._registers.to_real_address(sp + 2))
            data = self.from_low_high_to_int(low, high)
            self._registers.S += 2
        else:
            data = self.read_address(self._registers.to_real_address(sp + 1))
            self._registers.S += 1
        return data


if __name__ == '__main__':
    c = Cpu()
    origin_v = 127 + 128 + 1
    n = c.split_number(origin_v)
    print(n)
