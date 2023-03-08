import re
import time
import xlsxwriter
import os
import math
re_float = re.compile(r'[-+]?([0-9]*[.])?[0-9]+([eE][-+]?\d+)?')
# PI = 3.14159265359
tb, sb, mb = [], [0], [0]
c, b = 32, 1
while c > 0:
    tb.append(b)
    sb.append(b)
    mb.append(b-1)
    b <<= 1
    c -= 1
test_bit = tuple(tb)
sign_bit = tuple(sb)
mask_bit = tuple(mb)
del b, c, sb, mb, tb


def is_intersect(rect1, rect2):
    return ((rect1[0] < rect2[2]) and (rect1[2] > rect2[0]) and (rect1[3] > rect2[1]) and (rect1[1] < rect2[3]))


def sign(a):
    if a > 0:
        return 1
    elif a < 0:
        return -1
    else:
        return 0


def latlon2meter(coords):  # in format (lon,lat)
    x = (coords[0] * 20037508.34) / 180
    if abs(coords[1]) >= 85.051129:
        # The value 85.051129° is the latitude at which the full projected map becomes a square
        y = sign(coords[1]) * abs(coords[1])*111.132952777
    else:
        y = math.log(math.tan(((90 + coords[1]) * math.pi) / 360)) / (math.pi / 180)
        y = (y * 20037508.34) / 180
    return [x, y]


# backward (in JS)
# function epsg3857toEpsg4326(pos) {
#     let x = pos[0]
#     let y = pos[1]
#     x = (x * 180) / 20037508.34
#     y = (y * 180) / 20037508.34
#     y = (Math.atan(Math.pow(Math.E, y * (Math.PI / 180))) * 360) / Math.PI - 90
#   return [x, y]; }


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


class bit_collector():
    NMEA_CHARS = '@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_ !"#$%&\\()*+,-./0123456789:;<=>?'
    @staticmethod
    def get_len(v):
        if type(v) == int:
            if v == 0:
                return 0
            else:
                if v < 0:
                    v = ~v + 1
                return math.ceil(math.log(v, 2))
        elif type(v) == float:
            pass
        else:
            raise Exception(f'bit_collector.get_len: Unknown type({type(v)})')

    def twos_comp(self, val, bits):
        """compute the 2's complement of int value val"""
        if (val & sign_bit[bits]) != 0:
            val -= test_bit[bits]
        return val

    def __init__(self):
        self._buff_len = 150  # bytes
        self.buff = bytearray(self._buff_len)
        self.clear()

    def clear(self):
        self.length = 0
        for c in range(self._buff_len):
            self.buff[c] = 0

    def add_bits(self, data, length: int):
        while length > 0:
            if data & test_bit[length-1]:
                self.buff[self.length >> 3] |= test_bit[self.length & 7 ^ 7]
            length -= 1
            self.length += 1

    def get_int(self, start: int, length: int, signed: bool = False):
        result = 0
        length_counter = length

        while length_counter > 0:
            result <<= 1
            if self.buff[start >> 3] & test_bit[start & 7 ^ 7]:
                result |= 1
            length_counter -= 1
            start += 1

        if signed:
            result = self.twos_comp(result, length)
        # sign = bits[length-1]

        # if signed and (result & test_bit[length-1]) != 0:            result = -(result ^ (bits[length]-1))
        return result

    def get_str(self,  start: int, length: int):
        

        result = ''
        while length > 0:
            code = self.get_int(start, 6)
            # print(code)
            if code == 0:  # or code==32:
                break
            result += bit_collector.NMEA_CHARS[code]
            start += 6
            length -= 1
        return result

    def decode_vdm(self, data, pad):
        # print(f'datalen={len(data)} (data={data})')
        for ch in data:
            code = ord(ch)-48
            if code > 40:
                code -= 8
            self.push(code, 6)
        self.length -= int(pad)
        # print(f'char={ch}\tcode={code}\tbufflen={self.length}')


# def pretty_print(obj):
#     def collect_keys_length(depth):
#         if depth in
#         for k in


#     keys_length=[]

def wr_ex(vessels):
    filename = "vessels.xlsx"

    mmsi_collect = {}
    col_names = {}

    if os.path.exists(filename):
        os.remove(filename)

    workbook = xlsxwriter.Workbook(filename)
    worksheet = workbook.add_worksheet()

    row = 1
    for mmsi in vessels:

        if not (mmsi in mmsi_collect):
            mmsi_collect[mmsi] = len(mmsi_collect)
            worksheet.write_string(mmsi_collect[mmsi]+1, 0, str(mmsi))
        row = mmsi_collect[mmsi]+1

        for k in vessels[mmsi]:
            if not (k in col_names):
                col_names[k] = len(col_names)
                worksheet.write_string(0, col_names[k]+1, str(k))

            worksheet.write_string(row, col_names[k]+1, str(vessels[mmsi][k]))
        # worksheet.write(row, column, item)

        # incrementing the value of row by one with each iterations.
        # row += 1

    workbook.close()
