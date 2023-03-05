import sqlite3
import traceback
import struct
import os
import io
import helpers


# OSM file reader
SHAPE_FILENAME = 'C:\\ais\\map\\gis_osm_water_a_free_1.shp'
# SHAPE_FILENAME = 'C:\\ais\\map\\gis_osm_waterways_free_1.shp'
SHAPE_FILENAME = 'C:\\ais\\map\\land_polygons.shp'
# C: \ais\map\gis_osm_water_a_free_1.shp
DATABASE = 'C:\\ais\\ais.db'
SQL_PATH = 'C:\\ais\\my\\sql'
LOG_FILE = 'C:\\ais\\my\\osm.txt'

# UK
# EXTRACT_REGION = (-12.345767664073696, 49.40525200162512, 1.7606783869700509, 59.574398313438344)

# Europe
# EXTRACT_REGION = (-23.551822587369724, 27.67574202007593, 46.32122794583772, 69.62344855425523)

# alands
EXTRACT_REGION = (18.746602417457805, 59.09602946996111, 21.85573326803449, 61.03075261195945)



def exec_sql(sql, params=[]):
    c = conn.cursor()
    c.executemany(sql, params)
    conn.commit()


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


def read_polyline(recid):
    # write_log(f'\tpolyline')
    box = read_data('4d')
    numparts = read_data('<i')[0]

    numpoints = read_data('<i')[0]
    # write_log(f'\tnumparts: {numparts}, numpoints: {numpoints}')
    parts = read_data(f'<{numparts}i')
    points = read_data(f'<{numpoints*2}d')

    if helpers.is_intersect(EXTRACT_REGION, box):
        webmercator0 = helpers.latlon2meter(box[0], box[1])
        webmercator1 = helpers.latlon2meter(box[2], box[3])
        exec_sql(sql_shapes, params=[{
            'id': recid,
            'minx': webmercator0[0],
            'miny': webmercator0[1],
            'maxx': webmercator1[0],
            'maxy': webmercator1[1],
            'type': 3,
            'parts': numparts,
            'points': numpoints
        }])
        params = []
        for i in range(len(points)//2):
            webmercator = helpers.latlon2meter(points[i*2], points[i*2+1])
            params.append({
                'recid': recid,
                'partid': 0,
                'pointid': i,
                'x': webmercator[0],
                'y': webmercator[1]
            })
        exec_sql(sql_points, params)


def read_polygon(recid):
    box = read_data('4d')
    numparts = read_data('<i')[0]
    numpoints = read_data('<i')[0]

    result = helpers.is_intersect(EXTRACT_REGION, box)
    if result:
        write_log(f'recid: {recid}, {box}')
        parts = read_data(f'<{numparts}i')
        points = read_data(f'<{numpoints*2}d')
        webmercator0 = helpers.latlon2meter(box[0], box[1])
        webmercator1 = helpers.latlon2meter(box[2], box[3])
        exec_sql(sql_shapes, params=[{
            'recid': recid,
            'minx': webmercator0[0],
            'miny': webmercator0[1],
            'maxx': webmercator1[0],
            'maxy': webmercator1[1],
            'type': 5,
            'parts': numparts,
            'points': numpoints
        }])

        parts.append(len(points)//2)
        current_part = 0
        params = []
        for i in range(len(points)//2):
            if i == parts[current_part+1]:
                current_part += 1
            webmercator = helpers.latlon2meter(points[i*2], points[i*2+1])
            params.append({
                'recid': recid,
                'partid': current_part,
                'pointid': i,
                'x': webmercator[0],
                'y': webmercator[1]
            })
        exec_sql(sql_points, params)
    else:
        shape_file.seek(numparts*4+numpoints*16, 1)
    return result


#webmercator = helpers.latlon2meter(1,1)

if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
logfile = io.open(LOG_FILE, mode='w', encoding='utf-8')

sql_shapes = read_query('put_shape_header.sql')
sql_points = read_query('put_points.sql')
conn = sqlite3.connect(DATABASE)
conn.executescript('DELETE  FROM "shapes"; DELETE  FROM "points";')
conn.commit()

file_stats = os.stat(SHAPE_FILENAME)
shape_file = open(SHAPE_FILENAME, mode="rb")

try:
    # read header
    hdr = read_data(('>7i', '<2i', '8d'))  # cause python dont allow to change endianess in the middle of pattern
    if hdr[0] != 0x270a:
        write_log(f'File header differs, expected 0x{0x270a:X}, got 0x{hdr[0]:X}', console=True, raiseexception=True)
    if hdr[6]*2 != file_stats.st_size:
        write_log(f'File size differs, expected {hdr[6]*2:,}, got {file_stats.st_size:,}', console=True, raiseexception=True)
    print("Started...")
    shapes_accepted, shapes_count = 0, 0
    while shape_file.tell() < file_stats.st_size:
        print(f'{shape_file.tell()/file_stats.st_size*100:.3f}% done, shapes: {shapes_accepted}/{shapes_count}                 \r', end='')
        # read record header
        rec = read_data('>2i')
        # write_log(f'\nrecid: {rec[0]}')
        end_of_rec = shape_file.tell()+rec[1]*2

        # print(f'Rec: #{rec[0]}, len: {rec[1]*2}, offset: 0x{file_pos:X}')

        # parse each shape in record
        while shape_file.tell() < end_of_rec:
            shape_type = read_data('<i')[0]
            shapes_count += 1
            if shape_type == 3:
                read_polyline(rec[0])
            elif shape_type == 5:
                if read_polygon(rec[0]):
                    shapes_accepted += 1
            else:
                write_log(f'Unknown shape type: {shape_type}', console=True, raiseexception=True)

except:
    write_log('Error occured', console=True)
    write_log('-'*80, console=True)
    write_log(traceback.format_exc(), console=True)
finally:
    print("")
    print("Finished!")
    conn.close()
    logfile.close()
    shape_file.close()
