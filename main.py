# 解析 net ROM 里面的内容
from my_fc.fc import FC

if __name__ == '__main__':
    fc = FC()
    fc.load_rom()
    fc.run()
