import helpers
import os
import io

vessels, buffer, talkers, sentences, satellites = {}, {}, {}, {}, {}
own = {}


sat = helpers.satellites_class()


def check_vessel(mmsi):
    if not (mmsi in vessels):
        vessels[mmsi] = {}
        vessels[mmsi]['last_access'] = helpers.utc_ms()


def add_warn(v, consolelog=True):
    if consolelog:
        print('--- [WARN] '+v)


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


def check_buff(message_type, msg_data, msg_total, msg_num, group_id):
    if (msg_total is None) or (group_id is None):
        return {'data_ok': True, 'data': {1: msg_data}}

    # msg_total, msg_num, group_id = int(msg_total), int(msg_num),  int(group_id)

    if not (message_type in buffer):
        buffer[message_type] = {}
    if not (group_id in buffer[message_type]):
        buffer[message_type][group_id] = {}
    buffer[message_type][group_id][msg_num] = msg_data
    if len(buffer[message_type][group_id]) == msg_total:
        data = buffer[message_type][group_id]
        buffer[message_type][group_id] = {}
        return {'data_ok': True, 'data': data}

    return {'data_ok': False}


def check_lon_lat(mmsi):
    if ('lat' in vessels[mmsi]) and ('lon' in vessels[mmsi]):
        add_info(f'{mmsi};{vessels[mmsi]["lat"]};{vessels[mmsi]["lon"]};', consolelog=True, filelog=True)

################################################################
#
# message handlers
#


def handler_vtg(data):
    # print(f'vtg handled {data}')
    pass


# Field	Len	Description	Member	T	Units
# 0-5	6	Message Type	type	u	Constant: 1-3
# 06.июл	2	Repeat Indicator	repeat	u	Message repeat count
# авг.37	30	MMSI	mmsi	u	9 decimal digits
# 38-41	4	Navigation Status	status	e	See "Navigation Status"
# 42-49	8	Rate of Turn(ROT)	turn	I3	See below
# 50-59	10	Speed Over Ground(SOG)	speed	U1	See below
# 60-60	1	Position Accuracy	accuracy	b	See below
# 61-88	28	Longitude	lon	I4	Minutes/10000 (see below)
# 89-115	27	Latitude	lat	I4	Minutes/10000 (see below)
# 116-127	12	Course Over Ground(COG)	course	U1	Relative to true north, to 0.1 degree precision
# 128-136	9	True Heading(HDG)	heading	u	0 to 359 degrees, 511 = not available.
# 137-142	6	Time Stamp	second	u	Second of UTC timestamp
# 143-144	2	Maneuver Indicator	maneuver	e	See "Maneuver Indicator"
# 145-147	3	Spare		x	Not used
# 148-148	1	RAIM flag	raim	b	See below
# 149-167	19	Radio status	radio	u	See below

vdm_process = {1: [  # Types 1, 2 and 3: Position Report Class A
    ['repeat', 6, 2, 'u'],
    ['lon', 61,  28],
    ['lat', 89, 27],
    ['turn', 42, 8],
    ['speed', 50, 10, 'u'],
    ['accuracy', 60, 1, 'u'],
    ['course', 116, 12, 'u-1'],
    ['heading', 128, 9],
    ['maneuver', 143, 2, 'u'],
    ['raim', 148, 1, 'u'],
    ['radio', 149, 19, 'u'],
    ['second', 137, 6, 'u'],
],
    2: [  # Types 1, 2 and 3: Position Report Class A
    ['repeat', 6, 2, 'u'],
    ['lon', 61,  28],
    ['lat', 89, 27],
    ['turn', 42, 8],
    ['speed', 50, 10, 'u'],
    ['accuracy', 60, 1, 'u'],
    ['course', 116, 12, 'u-1'],
    ['heading', 128, 9],
    ['maneuver', 143, 2, 'u'],
    ['raim', 148, 1, 'u'],
    ['radio', 149, 19, 'u'],
    ['second', 137, 6, 'u'],
],
    3: [  # Types 1, 2 and 3: Position Report Class A
    ['repeat', 6, 2, 'u'],
    ['lon', 61,  28],
    ['lat', 89, 27],
    ['turn', 42, 8],
    ['speed', 50, 10, 'u'],
    ['accuracy', 60, 1, 'u'],
    ['course', 116, 12, 'u-1'],
    ['heading', 128, 9],
    ['maneuver', 143, 2, 'u'],
    ['raim', 148, 1, 'u'],
    ['radio', 149, 19, 'u'],
    ['second', 137, 6, 'u'],
],



    4: [  # Type 4: Base Station Report
    ['repeat', 6, 2, 'u'],
    ['year', 38,  14, 'u'],
    ['month', 52, 4, 'u'],
    ['day', 56, 5, 'u'],
    ['hour', 61, 5, 'u'],
    ['minute', 66, 6, 'u'],
    ['second', 72, 6, 'u'],
    ['accuracy', 78, 1, 'u'],
    ['lon', 79,  28],
    ['lat', 107, 27],
    ['epfd', 134, 4, 'u'],
    ['raim', 148, 1, 'u'],
    ['radio', 149, 19, 'u'],

],

    5: [  # Type 5: Static and Voyage Related Data
    ['repeat', 6, 2, 'u'],
    ['ais_version', 38,  2, 'u'],
    ['imo', 40, 30, 'u'],
    ['callsign', 70, 7, 's'],
    ['shipname', 112, 20, 's'],
    ['shiptype', 232, 8, 'u'],
    ['to_bow', 240, 9, 'u'],
    ['to_stern', 249, 9, 'u'],
    ['to_port', 258, 6, 'u'],
    ['to_starboard', 264, 6, 'u'],
    ['epfd', 270, 4, 'u'],
    ['month', 274, 4, 'u'],
    ['day', 278, 5, 'u'],
    ['hour', 283, 5, 'u'],
    ['minute', 288, 6, 'u'],
    ['draught', 294, 8, 'u-1'],
    ['destination', 302, 20, 's'],
    ['dte', 422, 1, 'u'],
],
    18: [  # Type 18: Standard Class B CS Position Report
    ['repeat', 6, 2, 'u'],
    ['speed', 46, 10, 'u'],
    ['accuracy', 56, 1, 'u'],
    ['lon', 57,  28],
    ['lat', 85, 27],
    ['course', 112, 12, 'u-1'],
    ['heading', 124, 9],
    ['second', 133, 6, 'u'],
    ['cs', 141, 1, 'u'],
    ['display', 142, 1, 'u'],
    ['dsc', 143, 1, 'u'],
    ['band', 144, 1, 'u'],
    ['msg22', 145, 1, 'u'],
    ['assigned', 146, 1, 'u'],
    ['raim', 147, 1, 'u'],
    ['radio', 148, 20, 'u'],

],

    19: [  # Type 19: Extended Class B CS Position Report
    ['repeat', 6, 2, 'u'],
    ['speed', 46, 10, 'u'],
    ['accuracy', 56, 1, 'u'],
    ['lon', 57,  28],
    ['lat', 85, 27],
    ['course', 112, 12, 'u-1'],
    ['heading', 124, 9],
    ['second', 133, 6, 'u'],
    ['shipname', 143, 20, 's'],
    ['shiptype', 263, 8, 'u'],
    ['to_bow', 271, 9, 'u'],
    ['to_stern', 280, 9, 'u'],
    ['to_port', 289, 6, 'u'],
    ['to_starboard', 295, 6, 'u'],
    ['epfd', 301, 4, 'u'],
    ['raim', 305, 1, 'u'],
    ['dte', 306, 1, 'u'],
    ['assigned', 307, 1, 'u'],
],
    21: [  # Type 21: Aid-to-Navigation Report
    ['repeat', 6, 2, 'u'],
    ['aid_type', 38, 5, 'u'],
    ['name', 43, 20, 's'],
    ['accuracy', 163, 1, 'u'],
    ['lon', 164,  28],
    ['lat', 192, 27],
    ['to_bow', 219, 9, 'u'],
    ['to_stern', 228, 9, 'u'],
    ['to_port', 237, 6, 'u'],
    ['to_starboard', 243, 6, 'u'],
    ['epfd', 249, 4, 'u'],
    ['second', 253, 6, 'u'],
    ['off_position', 259, 1, 'u'],
    ['raim', 268, 1, 'u'],
    ['virtual_aid', 269, 1, 'u'],
    ['assigned', 270, 1, 'u'],
],

    24: [  # Type 24: Static Data Report (Equivalent of a Type 5 message for ships using Class B equipment.)
        ['repeat', 6, 2, 'u'],
        ['partno', 38,  2, 'u'],
],
    # ----- no nav info
    16: [  # Type 16: Assignment Mode Command
    ['repeat', 6, 2, 'u'],
],
    17: [  # Type 17: DGNSS Broadcast Binary Message
    ['repeat', 6, 2, 'u'],
],
    20: [  # Type 20 Data Link Management Message
    ['repeat', 6, 2, 'u'],
],

    # ----- binary
    6: [  # Type 6: Binary Addressed Message
    ['repeat', 6, 2, 'u'],
],
    8: [  # Type 8: Binary Broadcast Message
    ['repeat', 6, 2, 'u'],
],

    # ----- datetime operations
    10: [  # Type 10: UTC/Date Inquiry
    ['repeat', 6, 2, 'u'],
],
}


def handler_vdm(data):

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
    if msg_id in vdm_process:
        check_vessel(mmsi)
        possibles = locals().copy()

        # print(f'--- {msg_id} ---')

        for field in vdm_process[msg_id]:

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
    # print(f'gsa handled {data}')
    return


def handler_gsv(data):  # Satellites in view
    buff = check_buff(message_type='gsv', msg_data=data[3:], msg_total=data[1], msg_num=data[2], group_id=0)
    if buff['data_ok']:
        data = []
        satellite_count = int(buff['data'][1][0])  # get sattelice count from first message

        # merge all messages in one, excluding satellite_count field
        for c in buff['data']:
            data.extend(buff['data'][c][1:])
        if len(data) != (satellite_count*4):
            add_info(f'GSV satellite data len(data len = {len(data)}) differs from declared(declared count={satellite_count})')
        for c in range(len(data)//4):
            sat.modify(data[c*4], data[c*4+1], data[c*4+2], data[c*4+3])


def handler_dcn(data):
    return


def parse_nmea(value):
    # print('-'*50)
    # print(value)

    # print(a)

    # check hdr corrrect
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
    # for i in range(1, len(a)):
    #     v = a[i]
    #     if len(v) == 0:
    #         a[i] = None
    #     elif helpers.is_int(v):
    #         a[i] = int(v)
    #     elif helpers.is_float(v):
    #         a[i] = float(v)

    # check if talker proprietary device (first talkerid letter is P)

    TalkerID = a[0][:-3].upper()
    MessageType = a[0][-3:].upper()
    if len(TalkerID) > 0:
        if TalkerID[0].upper() == 'P':
            # proprietary talker
            pass
        elif not (TalkerID in talkers):
            add_warn(f'Unknown TalkerID: {TalkerID}')
        else:
            if not (MessageType in sentences):
                add_warn(f'Unknown MessageType: {MessageType}', consolelog=True)
            # else:
            #     print(f'Message ({MessageType}): {sentences[MessageType]["sentencedescr"]}')

            handler_name = f'handler_{MessageType.lower()}'  # set by the command line options
            possibles = globals().copy()
            possibles.update(locals())
            method = possibles.get(handler_name)
            if not method:
                add_warn(f'No handler for {MessageType}', consolelog=True)
                # print(f'No handler for {MessageType}')
                # raise NotImplementedError("Method %s not implemented" % handler_name)
            else:
                method(a)

    return
