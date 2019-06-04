from my_fc.fc import FC


def test_jmp():
    fc = FC()
    fc.load_rom()
    fc.cpu.registers.PC = 0xC000
    fc.memory[0xC000 + 0] = 0x4C
    fc.memory[0xC000 + 1] = 0xF5
    fc.memory[0xC000 + 2] = 0xC5
    fc.memory[0xC5F5] = 0x00
    fc.run()
    assert fc.cpu.registers.PC == 0xC5F5, 'test jmp instruction'
