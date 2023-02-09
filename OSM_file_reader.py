# OSM file reader
import io
import os
import struct
import traceback
import sqlite3
SHAPE_FILENAME = 'C:\\ais\\map\\gis_osm_water_a_free_1.shp'
#SHAPE_FILENAME = 'C:\\ais\\map\\gis_osm_waterways_free_1.shp'
# C: \ais\map\gis_osm_water_a_free_1.shp
DATABASE = 'C:\\ais\\ais.db'
SQL_PATH = 'C:\\ais\\my\\sql'
LOG_FILE = 'C:\\ais\\my\\osm.txt'


def write_log(msg, console=False, raiseexception=False):
    logfile.write(msg)
    logfile.flush()
    if console:
        print(msg)
    if raiseexception:
        raise Exception(msg)


def read_query(sqlfilename):
    try:
        sqlfilepath = os.path.join(SQL_PATH, sqlfilename)
        if not os.path.isfile(sqlfilepath):
            raise Exception(f'No SQL file: {sqlfilename}')
        sqlfile = io.open(sqlfilepath, mode='r', encoding='utf-8')
        return sqlfile.read()
    finally:
        sqlfile.close()


def read_data(signature):
    buff_size = 0
    is_complex = (type(signature) is tuple) or (type(signature) is list)
    if is_complex:
        buff_size = 0
        for i in signature:
            buff_size += struct.calcsize(i)
    else:
        buff_size = struct.calcsize(signature)

    buff = shape_file.read(buff_size)

    pos, result = 0, []
    if is_complex:
        for i in signature:
            result.extend(struct.unpack_from(i, buff, pos))
            pos += struct.calcsize(i)
    else:
        result.extend(struct.unpack(signature, buff))
    return result


def read_polyline():
    write_log(f'\tpolyline')
    box = read_data('4d')
    numparts = read_data('<i')[0]

    numpoints = read_data('<i')[0]
    write_log(f'\tnumparts: {numparts}, numpoints: {numpoints}')
    parts = read_data(f'<{numparts}i')
    points = read_data(f'<{numpoints*2}d')

    if numparts != 1:
        write_log(f'\tnumparts more than one', console=True, raiseexception=True)


def read_polygon():
    write_log(f'\tpolygon')
    box = read_data('4d')
    numparts = read_data('<i')[0]

    numpoints = read_data('<i')[0]
    write_log(f'\tnumparts: {numparts}, numpoints: {numpoints}')
    parts = read_data(f'<{numparts}i')
    points = read_data(f'<{numpoints*2}d')


if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
logfile = io.open(LOG_FILE, mode='w', encoding='utf-8')
file_stats = os.stat(SHAPE_FILENAME)
shape_file = open(SHAPE_FILENAME, mode="rb")
try:
    # read header
    hdr = read_data(('>7i', '<2i', '8d'))  # cause python dont allow to change endianess in the middle of pattern
    if hdr[0] != 0x270a:
        write_log(f'File header differs, expected 0x{0x270a:X}, got 0x{hdr[0]:X}', console=True, raiseexception=True)
    if hdr[6]*2 != file_stats.st_size:
        write_log(f'File size differs, expected {hdr[6]*2:,}, got {file_stats.st_size:,}', console=True, raiseexception=True)

    while shape_file.tell() < file_stats.st_size:

        # read record header
        rec = read_data('>2i')
        write_log(f'\nrecid: {rec[0]}')
        end_of_rec = shape_file.tell()+rec[1]*2

        # print(f'Rec: #{rec[0]}, len: {rec[1]*2}, offset: 0x{file_pos:X}')

        while shape_file.tell() < end_of_rec:
            shape_type = read_data('<i')[0]
            if shape_type == 3:
                read_polyline()
            elif shape_type == 5:
                read_polygon()
            else:
                write_log(f'Unknown shape type: {shape_type}', console=True, raiseexception=True)
        # for skip
        # file_pos += rec[1]*2+8
        # shape_file.seek(file_pos, 0)
except:
    write_log('Error occured', console=True)
    write_log('-'*80, console=True)
    write_log(traceback.format_exc(), console=True)
finally:
    logfile.close()
    shape_file.close()
