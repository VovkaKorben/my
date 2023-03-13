import helpers
import os
import io
import ais_mysql
import math
from mysql.connector import Error
import mysql.connector
import traceback
vessels, buffer, talkers, sentences, satellites = {}, {}, {}, {}, {}
own = {}
VDM_TYPES = {}
VDM_DEFS = {}
NMEA_TYPE_INT = 0
NMEA_TYPE_FLOAT = 1
NMEA_TYPE_STRING = 2
sat = helpers.satellites_class()
gps = helpers.gps_class()


def dm_s2deg(dms):
    if type(dms) != float:
        return None
    i = math.floor(dms)
    s = dms - i
    m = i % 100
    d = i // 100
    result = d + m/60 + s/3600
    return result


def add_warn(msg, consolelog=True, raiseerror=False):
    s = f'[WARN] {msg}'
    if consolelog:
        print(msg)
    if raiseerror:
        raise Exception(msg)


def add_info(v, consolelog=True, filelog=False):
    if consolelog:
        print('---- [INFO] '+v)
    if filelog:
        path = os.getcwd()
        logfilename = os.path.join(path, 'log.csv')
        logfile = io.open(logfilename, mode='a', encoding='utf-8')
        try:
            logfile.write(v+'\n')
        finally:
            logfile.close()


def check_buff(talker, sentence, data):
    message_total = int(data[0])
    message_num = int(data[1])
    if sentence == 'vdm':
        group_num = int(data[2])
        data = data[3:]
    else:
        group_num = 0
        data = data[2:]

    # single message, dont use buffer, direct return
    if message_total == 1:
        return {'valid': True, 'data': {1: data}}

    if not (sentence in buffer):
        buffer[sentence] = {}
    if not (group_num in buffer[sentence]):
        buffer[sentence][group_num] = {}
    buffer[sentence][group_num][message_num] = data
    if len(buffer[sentence][group_num]) == message_total:
        return {'valid': True, 'data': buffer[sentence].pop(group_num)}
    else:
        return {'valid': False}

    # if (msg_total is None) or (group_id is None):
    #     return {'data_ok': True, 'data': {1: msg_data}}

    # # msg_total, msg_num, group_id = int(msg_total), int(msg_num),  int(group_id)

    # if not (message_type in buffer):
    #     buffer[message_type] = {}
    # if not (group_id in buffer[message_type]):
    #     buffer[message_type][group_id] = {}
    # buffer[message_type][group_id][msg_num] = msg_data
    # if len(buffer[message_type][group_id]) == msg_total:
    #     data = buffer[message_type][group_id]
    #     buffer[message_type][group_id] = {}
    #     return {'data_ok': True, 'data': data}

    # return {'data_ok': False}


def check_lon_lat(mmsi):
    if ('lat' in vessels[mmsi]) and ('lon' in vessels[mmsi]):
        add_info(f'{mmsi};{vessels[mmsi]["lat"]};{vessels[mmsi]["lon"]};', consolelog=True, filelog=True)


def get_int(v):
    return int(v) if helpers.is_int(v) else None


def get_char(v):
    return v[0].lower() if type(v) == str and len(v) > 0 else None


def get_float(v):
    if type(v) != float:
        if helpers.is_float(v):
            return float(v)
    else:
        return v
################################################################
#
# message handlers
#


def handler_gga(data):
    tmp_float = get_float(data[0])
    if not tmp_float is None:
        gps.datetime = gps.datetime.replace(
            hour=int(tmp_float) // 10000,
            minute=(int(tmp_float) // 100) % 100,
            second=int(tmp_float) % 100)

    tmp_float = get_float(data[1])
    tmp_char = get_char(data[2])
    if not (tmp_float is None or tmp_char is None):
        gps.lat = dm_s2deg(tmp_float)
        if tmp_char == 's':
            gps.lat = -gps.lat

    tmp_float = get_float(data[3])
    tmp_char = get_char(data[4])
    if not (tmp_float is None or tmp_char is None):
        gps.lon = dm_s2deg(tmp_float)
        if tmp_char == 's':
            gps.lon = -gps.lon

    return {'ok': True}


def handler_rmc(data):
    valid = data[1].lower()
    if valid == 'v':
        return {'ok': False}
    t = helpers.floatstr2int(data[0])
    gps.datetime = gps.datetime.replace(hour=t // 10000,  minute=(t // 100) % 100, second=t % 100)
    t = helpers.floatstr2int(data[8])
    gps.datetime = gps.datetime.replace(day=t // 10000,  month=(t // 100) % 100, year=t % 100)

    gps.lat = float(data[2])
    gps.lat = dm_s2deg(gps.lat)
    if data[3].lower() == 's':
        gps.lat = -gps.lat
    gps.lon = float(data[4])
    gps.lon = dm_s2deg(gps.lon)
    if data[5].lower() == 'w':
        gps.lon = -gps.lon

    return {'ok': True}


def handler_vtg(data):
    ptr = 0
    while (ptr+2) < len(data):
        c = data[ptr+1]
        if len(c) > 0:
            c = c.lower()
            v = float(data[ptr]) if helpers.is_float(data[ptr]) else None
            if c == 't':
                gps.hog_true = v
            elif c == 'm':
                gps.hog_magnetic = v
            elif c == 'n':
                gps.sog_knots = v
            elif c == 'k':
                gps.sog_km = v
        ptr += 2
    return {'ok': True}


def handler_vdm(data):
    def check_vessel(mmsi):
        if not (mmsi in vessels):
            vessels[mmsi] = {}
        vessels[mmsi]['last_access'] = helpers.utc_ms()

    def field_lon(field):
        tmp = bitcollector.get_int(field[1], field[2], signed=True)
        return None if tmp == 0x6791AC0 else tmp/600000

    def field_lat(field):
        tmp = bitcollector.get_int(field[1], field[2], signed=True)
        return None if tmp == 0x3412140 else tmp/600000

    def field_turn(field):
        tmp = bitcollector.get_int(field[1], field[2], signed=True)
        return tmp

    # def field_course(field):
    #     return bitcollector.get_int(field[1], field[2])/10

    def field_heading(field):
        tmp = bitcollector.get_int(field[1], field[2])
        return None if tmp == 511 else tmp

    def field_speed(field):
        tmp = bitcollector.get_int(field[1], field[2])
        return None if tmp == 1023 else tmp*0.1852  # knots => in km/h

    # def field_draught(field):
    #     return bitcollector.get_int(field[1], field[2])/10

    # print(f'VDM: {data}')

    # collect messages
    buff = check_buff(message_type='vdm',
                      msg_data=data[4:7],
                      msg_total=int(data[2]) if helpers.is_int(data[1]) else None,
                      msg_num=int(data[2]) if helpers.is_int(data[2]) else None,
                      group_id=int(data[2]) if helpers.is_int(data[3]) else None
                      )
    if not buff['data_ok']:
        return

    # collect bits
    bitcollector = helpers.bit_collector()
    channel = buff['data'][1][0]
    channel_diff_warn = False
    for c in buff['data']:
        # check that channel the same on each message in group
        if buff['data'][c][0] != channel:
            if not channel_diff_warn:
                add_warn('VGM: Channel differs')
            channel_diff_warn = True
        bitcollector.decode_vdm(data=buff['data'][c][1], pad=buff['data'][c][2])

    # parse messages
    msg_id = bitcollector.get_int(0, 6)
    mmsi = bitcollector.get_int(8, 30)
    if msg_id in VDM_FIELDS:
        check_vessel(mmsi)
        possibles = locals().copy()

        # print(f'--- {msg_id} ---')

        for field in VDM_FIELDS[msg_id]:

            # field has named handler
            if len(field) <= 3:
                method_name = f'field_{field[0]}'
                method = possibles.get(method_name)
                if not method:
                    add_warn(f'No handler for field \'{field[0]}\', expected \'{method_name}\'', consolelog=True)
                else:
                    vessels[mmsi][field[0]] = method(field)

            # for simple fields
            else:
                if len(field[3]) > 1:  # has a multiplier or divider
                    mod = pow(10, int(field[3][2:]))
                    if field[3][1] == '-':
                        mod = 1/mod
                else:
                    mod = None

                if field[3][0] == 'u':
                    vessels[mmsi][field[0]] = bitcollector.get_int(field[1], field[2])
                    if not (mod is None):
                        vessels[mmsi][field[0]] *= mod
                elif field[3][0] == 's':
                    vessels[mmsi][field[0]] = bitcollector.get_str(field[1], field[2])
                else:
                    add_warn(f'No type defined for field \'{field[0]}\'', consolelog=True)
            # print(field[0])

    #         possibles = globals().copy()
    # possibles.update(locals())
    # method = possibles.get(handler_name)
    # if not method:
    #     add_warn(f'No handler for {MessageType}', consolelog=True)
    #     # print(f'No handler for {MessageType}')
    #     # raise NotImplementedError("Method %s not implemented" % handler_name)
    # else:
    #     method(a)

    else:
        add_warn(f'VDM: unknown msgID={msg_id}')
    pass


def handler_gsa(data):  # GPS DOP and active satellites

    gps.modeAM, gps.modeFIX = get_char(data[0]), get_int(data[1])
    gps.pdop, gps.hdop, gps.vdop = get_float(data[14]), get_float(data[15]), get_float(data[16])

    gps.used_sv.clear()
    for x in range(2, 14):
        prn = get_int(data[x])
        if not prn is None:
            gps.used_sv.append(prn)
    return {'ok': True}


def handler_gsv(data):  # Satellites in view
    first, count = True, 0
    for msg_id in data:
        if len(data[msg_id]) > 0:
            sc_tmp = get_int(data[msg_id][0])
            if first:
                satellite_count = sc_tmp
                first = False
            elif sc_tmp != satellite_count:
                return {'ok': False, 'msg': 'the number of satellites differs in consecutive messages'}
            ptr = 1
            while (ptr+4) < len(data[msg_id]):
                sat.modify(data[msg_id][ptr:ptr+4])
                count += 1
                ptr += 4
    return {'ok': True}


def handler_dcn(data):
    return


def parse_nmea(value):

    # check hdr correct
    if (value[0] != '!') and (value[0] != '$'):
        add_warn(f'Start symbol ({value[0] }) not allowed')
    # check asterisk
    asterisk_pos = value.find('*')
    if asterisk_pos == -1:
        add_warn(f'Asterisk not found in message')

    # calc checksum
    pos = 1
    cs = 0
    while (pos < asterisk_pos):
        cs ^= ord(value[pos])
        pos += 1
    if (value[asterisk_pos+1:] != f'{cs:02X}'):
        add_warn(f'Message checksum ({value[asterisk_pos+1:]}) differs from computed ({cs:02X})')

    # split to pieces and align to correspond forms
    a = value[1:asterisk_pos].split(',')
    talker = a[0][:-3].lower()
    sentence = a[0][-3:].lower()
    if len(talker) > 0:
        if talker[0].lower() == 'p':
            # proprietary talker
            pass
        elif not (talker in talkers):
            add_warn(f'Unknown talker: {talker.upper()}', consolelog=True)
        if not (sentence in sentences):
            add_warn(f'Unknown sentence: {sentence.upper()}', consolelog=True, raiseerror=True)
        else:
            try:
                if sentences[sentence]['grouped']:
                    buff = check_buff(talker=talker, sentence=sentence, data=a[1:])
                    if buff['valid']:
                        sentences[sentence]['handler'](buff['data'])
                else:
                    sentences[sentence]['handler'](a[1:])
            except:
                print('------ NMEA ERROR ------')
                print(value)
                # print('-'*80)
                print(traceback.format_exc())


def load_tables():

    try:
        conn = ais_mysql.connect_db(user='nmearead', password='nmearead')
        try:
            c = conn.cursor(True, dictionary=True)

            sql = ais_mysql.read_query('nmea/read_vdm_defs.sql')
            c.execute(sql)
            tmp = c.fetchall()
            for item in tmp:
                msg_id = item.pop('id')
                if not (msg_id in VDM_DEFS):
                    VDM_DEFS[msg_id] = []
                VDM_DEFS[msg_id].append(item)
            # c.reset()

            sql = ais_mysql.read_query('nmea/read_vdm_types.sql')
            c.execute(sql)
            tmp = c.fetchall()
            for item in tmp:
                msg_id = item.pop('id')
                VDM_TYPES[msg_id] = item
            # c.reset()

            sql = ais_mysql.read_query('nmea/read_talkers.sql')
            c.execute(sql)
            tmp = c.fetchall()
            for item in tmp:
                talker = item.pop('id')
                talkers[talker.lower()] = item
            # c.reset()

            sql = ais_mysql.read_query('nmea/read_sentences.sql')
            c.execute(sql)
            tmp = c.fetchall()
            for item in tmp:
                sentence = item.pop('id')
                sentences[sentence.lower()] = item
            # c.reset()

        finally:
            c.close()
    except mysql.connector.Error as error:
        print(f'MySQL error: {error}')
        conn.close()

    # assign handlers for sentences
    possibles = globals().copy()
    # possibles.update(locals())
    for sentence in sentences:
        # print(sentence)
        handler_name = f'handler_{sentence.lower()}'
        method = possibles.get(handler_name)
        if not method:
            raise Exception(f'No handler found for {sentence.upper()} sentence. Execution stopped.')
        sentences[sentence]['handler'] = method

        # print(f'No handler for {MessageType}')
        # raise NotImplementedError("Method %s not implemented" % handler_name)
        #  else:
        #  method(a)


def create_vdm(message_id, data, header='AI', group_id: int = 1):
    def get_checksum(s: str):
        cs = 0
        for c in s:
            cs ^= ord(c)
        return cs

    def collect_bits(bc):

        if not (message_id in VDM_DEFS):
            raise Exception(f'[MSG_ID:{message_id}] Not found in VDM_DEFS')
        if not (message_id in VDM_TYPES):
            raise Exception(f'[MSG_ID:{message_id}] Not found in VDM_TYPES')

        bc.add_bits(message_id, 6)

        for field in VDM_DEFS[message_id]:
            # print(f'Field: {field["name"]} ({field})')
            if field['start'] != bc.length:
                raise Exception(f'[MSG_ID:{message_id}] No field with start at: {bc.length}')
            if not (field['name'] in data):
                if 'default' in field:
                    value = field['default']
                else:
                    raise Exception(f'[MSG_ID:{message_id}] No default value for {field["name"]}')
            else:
                value = data[field['name']]
            # value_bitlen=helpers.bit_collector.get_len(value)
            # if value_bitlen > field['len']:
            #     raise Exception(f'[MSG_ID:{message_id}] Value for {field["name"]}={value} exceed maximum length. Maximum allowed {field["len"]}, got {value_bitlen}.')
            value_type = type(value)
            if field['type'] == NMEA_TYPE_INT:
                bc.add_bits(value, field['len'])
            elif field['type'] == NMEA_TYPE_FLOAT:
                bc.add_bits(round(value*field['exp']), field['len'])
            elif field['type'] == NMEA_TYPE_STRING:
                if value_type != str:
                    raise Exception(f'[MSG_ID:{message_id}] {field["name"]}: string expected, got {value_type}')
                value = value.upper()
                l = len(value)
                if l < field['len']:
                    value += '@' * (field['len']-l)
                    l = field['len']
                else:
                    l = min(len(value), field['len'])

                for c in range(l):
                    i = helpers.bit_collector.NMEA_CHARS.find(value[c])

                    if i == -1:
                        raise Exception(f'[MSG_ID:{message_id}] {field["name"]}: unsupported character `{value[c]}`')
                    bc.add_bits(i, 6)
            else:
                raise Exception(f'[MSG_ID:{message_id}] Unknown field type ({field["type"]})')
        if bc.length != VDM_TYPES[message_id]['len']:
            raise Exception(f'[MSG_ID:{message_id}] Message len error, expected {VDM_TYPES[message_id]["len"]}, got {bc.length}')

    def create_str(bc):
        MAX_PAYLOAD = 336  # max bits in one message
        ptr = 0
        result = []
        collected = 0
        collect = r''
        while ptr < bc.length:
            b = bc.get_int(ptr, 6)
            c = b + 48
            if c > 87:
                c += 8
            # print(f'{b}\t{c}\t{chr(c)}')
            collect += chr(c)
            ptr += 6
            collected += 6
            if collected >= MAX_PAYLOAD or ptr >= bc.length:
                result.append(collect)
                collected = 0
                collect = r''
        return result

    def create_messages(messages: dict, header: str, channel: str = 'A', group_id: int = None):
        result = []
        messages_count = len(messages)
        for i in range(messages_count):
            s = header+'VDM'
            s = f'{s},{messages_count},{i+1},'
            if messages_count > 1:
                s = f'{s}{messages_count}'
            s = f'{s},{channel},{messages[i]},0'

            cs = get_checksum(s)
            s = f'!{s}*{format(cs, "02X")}'
            print(s)
            result.append(s)

        return result

    bitcollector = helpers.bit_collector()
    collect_bits(bitcollector)
    messages = create_str(bitcollector)
    if len(messages) > 1 and group_id is None:
        raise Exception(f'[MSG_ID:{message_id}] For multiple message sequences you must provide GROUP_ID')
    nmea = create_messages(messages, header)
    # print(nmea)
    return nmea


def test_create_vdm():

    vessel = {
        'repeat': 0,
        'lon': 29.726505062210823,
        'lat': 62.595683709205275,
        'status': 8,  # Under way sailing
        'turn': -5,
        'speed': 40,
        'accuracy': 1,
        'course': 12.3,
        'heading': 22,
        'maneuver': 8,
        'raim': 0,
        'second': 30,
        'ais_version': 0,
        'imo': 11223344,
        'callsign': 'TARDIS',
        'shipname': 'ENOLA',
        'shiptype': 36,
        'to_bow': 5,
        'to_stern': 3,
        'to_port': 1,
        'to_starboard': 1,

        'month': 4,
        'day': 27,
        'hour': 9,
        'minute': 30,
        'draught': 12,
        'destination': 'HEAVEN',

        'mmsi': 12345678,
    }

    # create_vdm(message_id=1, data=vessel)
    create_vdm(message_id=5, data=vessel)


load_tables()
# test_create_vdm()

# 55P5TL01VIaAL@7WKO@mBplU@<PDhh000000001S;AJ::4A80?4i@E53
#!AIVDM,2,1,3,B,55P5TL01VIaAL@7WKO@mBplU@<PDhh000000001S;AJ::4A80?4i@E53,0*3E
