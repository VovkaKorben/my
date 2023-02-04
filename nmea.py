import helpers
vehicles, buffer, talkers, sentences, satellites = {}, {}, {}, {}, {}
own = {}


sat = helpers.satellites_class()


def add_warn(v, consolelog=False):
    if consolelog:
        print('[WARN] '+v)


def add_info(v, consolelog=False):
    if consolelog:
        print('[INFO] '+v)


def check_buff(message_type, msg_data, msg_total, msg_num, group_id):
    if (msg_total is None) or (group_id is None):
        return {'data_ok': True, 'data': {0: msg_data}}

    msg_total, msg_num, group_id = int(msg_total), int(msg_num),  int(group_id)

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


def handler_vtg(data):  # Track made good and Ground speed
    # print(f'vtg handled {data}')
    pass


def handler_vdm(data):  # Track made good and Ground speed

    print(f'VDM: {data}')

    buff = check_buff(message_type='vdm', msg_data=data[4:7], msg_total=data[1], msg_num=data[2], group_id=data[3])
    if not buff['data_ok']:
        return
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
        # append decoded data
        # app = decode_vdm(data=buff['data'][c][1], pad=buff['data'][c][2])
        # for c in app:
        #     print(c)
        # data.extend(app)


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
    print('-'*50)
    print(value)

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

    if not (TalkerID in talkers):
        add_warn(f'Unknown TalkerID: {TalkerID}')
    # else:
    #     print(f'Talker ({TalkerID}): {talkers[TalkerID]["talkerdescr"]}')

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
