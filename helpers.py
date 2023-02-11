import re
import time
import xlsxwriter
import os
import math
bits, c, b = [],  32, 1
while c > 0:
    bits.append(b)
    b <<= 1
    c -= 1
re_float = re.compile(r'[-+]?([0-9]*[.])?[0-9]+([eE][-+]?\d+)?')
PI = 3.14159265359


def latlon2meter(lon, lat):
    print(f'lon: {lon}, lat: {lat}')
    x = (lon * 20037508.34) / 180
    y = math.log(math.tan(((90 + lat) * PI) / 360)) / (PI / 180)
    y = (y * 20037508.34) / 180
    return [x, y]


 y = math.log(math.tan(((90 + lat) * PI) / 360)) / (PI / 180)

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
    def __init__(self):
        self._buff_len = 150  # bytes
        self.buff = bytearray(self._buff_len)
        self.clear()

    def clear(self):
        self.length = 0
        for c in range(self._buff_len):
            self.buff[c] = 0

    def push(self, data, length):
        while length > 0:
            if data & bits[length-1]:
                self.buff[self.length >> 3] |= bits[self.length & 7 ^ 7]
            length -= 1
            self.length += 1

    def get_int(self, start: int, length: int, signed: bool = False):
        result = 0
        length_counter = length

        while length_counter > 0:
            result <<= 1
            if self.buff[start >> 3] & bits[start & 7 ^ 7]:
                result |= 1
            length_counter -= 1
            start += 1
        # sign = bits[length-1]
        if signed and (result & bits[length-1]) != 0:
            result = -(result ^ (bits[length]-1))

        return result

    def get_str(self,  start: int, length: int):
        # print('----------------------------')
        char_lut = '@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_ !"#$%&\\()*+,-./0123456789:;<=>?'
        result = ''
        while length > 0:
            code = self.get_int(start, 6)
            # print(code)
            if code == 0:  # or code==32:
                break
            result += char_lut[code]
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
