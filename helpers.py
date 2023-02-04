import re
import time

re_float = re.compile(r'[-+]?([0-9]*[.])?[0-9]+([eE][-+]?\d+)?')


def is_int(s):
    try:
        i = int(s)
    except ValueError:
        return False
    else:
        return True


def is_float(s):
    matches = re_float.match(s)
    if matches == None:
        return False
    return (matches.span()[1] == len(s))


def utc_ms(add_time: int = 0):
    return (time.time_ns()//1000000)+add_time


class satellites_class():
    def __init__(self):
        self.sl = {}

    def modify(self, prn, elevation, azimuth, snr):
        if not (prn in self.sl):
            self.sl[prn] = {}
        self.sl[prn]['elevation'] = elevation
        self.sl[prn]['azimuth'] = azimuth
        self.sl[prn]['snr'] = snr
        self.sl[prn]['last_access'] = utc_ms()


mask, bits, v, c, b = [], [], 0, 32, 1
while c > 0:
    mask.append(v)
    v = (v << 1) | 1
    bits.append(b)
    b <<= 1
    c -= 1


class bit_collector():
    def __init__(self):
        self.raw_len = 10
        self.data = bytearray(self.raw_len)
        self.clear()

    def clear(self):
        self.length = 0
        for c in range(len(self.data)):
            self.data[c] = 0

    def push(self, data, length):
        while length > 0:
            if data & bits[length]:
                self.data[self.length // 8] |= bits[self.length % 8]
            length -= 1
            self.length += 1

    def get_int(self, start, length):
        result = 0
        while length > 0:
            if self.data[start // 8] & bits[start % 8]:
                result |= 1
            result <<= 1
            length -= 1
            start += 1

        pass

    def decode_vdm(self, data, pad):
        for ch in data:
            code = ord(ch)-48
            if code > 40:
                code -= 8
            self.push(code, 6)

    def get_str(data, start, len):
        pass

    def get_float(data, start, len, delitimer):
        pass

    # def push(self, data, length):
    #     while length > 0:
    #         bits_free = 8 - (self.length % 8)  # free bits count in last byte
    #         bits_to_insert = min(bits_free, length)  # how many bits we can insert in last byte

    #         # clipped_len = length-bits_to_insert
    #         clipped_bits = data >> (length-bits_to_insert)  # clip data bits to fit
    #         data_to_paste = clipped_bits << (bits_free - bits_to_insert)  # move clipped bits to align free space on the left
    #         self.data[self.length // 8] |= data_to_paste  # put data to array

    #         self.length += bits_to_insert
    #         length -= bits_to_insert
    #         data &= mask[length]
