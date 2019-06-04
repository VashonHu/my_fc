def ones_from_length(length):  # 这个 length 是多少, 那么这个 mask 就是从右边开始有多少个1
    mask = 0
    for i in range(length):
        mask <<= 1
        mask |= 1
    return mask


class FlagByte(object):
    def __init__(self, flag):
        self.flag = flag

    def __getitem__(self, index):
        flag = self.flag
        if isinstance(index, int):
            mask = 1
            r = flag >> index  # 将所需要的位的值放在最右边
            r &= mask  # 1的二进制最右边是1, 其他全为0; 与上它, 保证了除了最右边的那位外, 全部置零了
        elif isinstance(index, slice):
            start = index.start
            stop = index.stop
            length = stop - start

            mask = ones_from_length(length)
            mask <<= start

            r = flag & mask
            r >>= start
        else:
            raise IndexError("index must be in [0, 7]")
        return r

    def __setitem__(self, index, value):
        if isinstance(index, int):
            if value == 1:
                mask = 1 << index
                self.flag |= mask
            elif value == 0:
                mask = 1 << index
                mask = ~mask
                self.flag &= mask
            else:
                raise ValueError("value must be 0 or 1")
        elif isinstance(index, slice):
            result = self.flag
            start = index.start
            stop = index.stop
            length = stop - start

            mask = ones_from_length(length)
            mask <<= start
            mask = ~mask
            result &= mask

            value <<= start
            result |= value
            self.flag = result

    @property
    def value(self):
        return self.flag

    @value.setter
    def value(self, value):
        self.flag = value


if __name__ == '__main__':
    r = FlagByte(300)
    print(bin(300))
    print(r[0:8], r[8:16])
