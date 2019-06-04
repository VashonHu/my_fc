from my_fc.cpu import Cpu


def test_split_bit():
    c = Cpu(bytearray(1))
    origin_v = 50688
    low, high = c.low_high(origin_v)
    v = c.from_low_high_to_int(low, high)
    assert v == origin_v, 'test_split_bit fail'


if __name__ == '__main__':
    test_split_bit()
