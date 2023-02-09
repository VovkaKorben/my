    # # Types 1, 2 and 3: Position Report Class A
    # if msg_id == 1 or msg_id == 2 or msg_id == 3:
    #     mmsi = bitcollector.get_int(8, 30)
    #     check_vessel(mmsi)

    #     tmp = bitcollector.get_int(42, 8)
    #     if tmp != 128:
    #         vessels[mmsi]['turn'] = tmp

    #     tmp = bitcollector.get_int(50, 10)
    #     if tmp != 1023:
    #         vessels[mmsi]['speed'] = tmp*0.1852  # knots => in km/h

    #     tmp = bitcollector.get_int(61, 28, signed=True)
    #     if tmp != 0x6791AC0:
    #         vessels[mmsi]['lon'] = tmp/600000

    #     tmp = bitcollector.get_int(89, 27, signed=True)
    #     if tmp != 0x3412140:
    #         vessels[mmsi]['lat'] = tmp/600000

    #     tmp = bitcollector.get_int(116, 12)
    #     if tmp != 3600:
    #         vessels[mmsi]['course'] = tmp/10

    #     tmp = bitcollector.get_int(128, 9)
    #     if tmp != 511:
    #         vessels[mmsi]['heading'] = tmp

    #     vessels[mmsi]['repeat'] = bitcollector.get_int(6, 2)
    #     vessels[mmsi]['status'] = bitcollector.get_int(38, 4)
    #     vessels[mmsi]['accuracy'] = bitcollector.get_int(60, 1)
    #     vessels[mmsi]['maneuver'] = bitcollector.get_int(143, 2)
    #     vessels[mmsi]['raim'] = bitcollector.get_int(148, 1)
    #     vessels[mmsi]['radio'] = bitcollector.get_int(149, 19)
    # # Type 4: Base Station Report
    # elif msg_id == 4:
    #     mmsi = bitcollector.get_int(8, 30)
    #     check_vessel(mmsi)

    #     tmp = bitcollector.get_int(57, 28, signed=True)
    #     if tmp != 0x6791AC0:
    #         vessels[mmsi]['lon'] = tmp/600000

    #     tmp = bitcollector.get_int(85, 27, signed=True)
    #     if tmp != 0x3412140:
    #         vessels[mmsi]['lat'] = tmp/600000

    #     vessels[mmsi]['accuracy'] = bitcollector.get_int(78, 1)
    #     vessels[mmsi]['epfd'] = bitcollector.get_int(134, 4)
    #     vessels[mmsi]['raim'] = bitcollector.get_int(148, 1)
    #     vessels[mmsi]['radio'] = bitcollector.get_int(149, 19)

    #     vessels[mmsi]['time'] = {
    #         'year': bitcollector.get_int(38, 14),
    #         'month': bitcollector.get_int(52, 4),
    #         'day': bitcollector.get_int(56, 5),
    #         'hour': bitcollector.get_int(61, 5),
    #         'minute': bitcollector.get_int(66, 6),
    #         'second': bitcollector.get_int(72, 6),
    #     }
    # # Type 5: Static and Voyage Related Data
    # elif msg_id == 5:
    #     mmsi = bitcollector.get_int(8, 30)
    #     check_vessel(mmsi)
    #     vessels[mmsi]['imo'] = bitcollector.get_int(40, 30)
    #     vessels[mmsi]['callsign'] = bitcollector.get_str(70, 7)
    #     vessels[mmsi]['shipname'] = bitcollector.get_str(112, 20)
    #     vessels[mmsi]['shiptype'] = bitcollector.get_int(232, 8)
    #     vessels[mmsi]['size'] = (
    #         bitcollector.get_int(240, 9),
    #         bitcollector.get_int(249, 9),
    #         bitcollector.get_int(258, 6),
    #         bitcollector.get_int(264, 6))
    #     vessels[mmsi]['epfd'] = bitcollector.get_int(270, 4)
    #     vessels[mmsi]['draught'] = bitcollector.get_int(294, 8)/10
    #     vessels[mmsi]['destination'] = bitcollector.get_str(302, 20)
    # # Type 18: Standard Class B CS Position Report
    # elif msg_id == 18:
    #     mmsi = bitcollector.get_int(8, 30)
    #     check_vessel(mmsi)

    #     tmp = bitcollector.get_int(46, 10)
    #     if tmp != 1023:
    #         vessels[mmsi]['speed'] = tmp*0.1852  # knots => in km/h

    #     tmp = bitcollector.get_int(57, 28, signed=True)
    #     if tmp != 0x6791AC0:
    #         vessels[mmsi]['lon'] = tmp/600000

    #     tmp = bitcollector.get_int(85, 27, signed=True)
    #     if tmp != 0x3412140:
    #         vessels[mmsi]['lat'] = tmp/600000

    #     tmp = bitcollector.get_int(112, 12)
    #     if tmp != 3600:
    #         vessels[mmsi]['course'] = tmp/10

    #     tmp = bitcollector.get_int(124, 9)
    #     if tmp != 511:
    #         vessels[mmsi]['heading'] = tmp

    #     vessels[mmsi]['repeat'] = bitcollector.get_int(6, 2)
    #     vessels[mmsi]['accuracy'] = bitcollector.get_int(56, 1)
    #     vessels[mmsi]['cs'] = bitcollector.get_int(141, 1)
    #     vessels[mmsi]['display'] = bitcollector.get_int(142, 1)
    #     vessels[mmsi]['dsc'] = bitcollector.get_int(143, 1)
    #     vessels[mmsi]['band'] = bitcollector.get_int(144, 1)
    #     vessels[mmsi]['msg22'] = bitcollector.get_int(145, 1)
    #     vessels[mmsi]['assigned'] = bitcollector.get_int(146, 1)
    #     vessels[mmsi]['raim'] = bitcollector.get_int(147, 1)
    #     vessels[mmsi]['radio'] = bitcollector.get_int(148, 20)

    #     # check_lon_lat(mmsi) # just for debuf
    # # Type 21: Aid-to-Navigation Report
    # elif msg_id == 21:
    #     mmsi = bitcollector.get_int(8, 30)
    #     check_vessel(mmsi)

    #     vessels[mmsi]['repeat'] = bitcollector.get_int(6, 2)
    #     vessels[mmsi]['aid_type'] = bitcollector.get_int(38, 5)
    #     vessels[mmsi]['name'] = bitcollector.get_str(43, 20)

    #     vessels[mmsi]['accuracy'] = bitcollector.get_int(163, 1)
    #     vessels[mmsi]['size'] = (
    #         bitcollector.get_int(219, 9),
    #         bitcollector.get_int(228, 9),
    #         bitcollector.get_int(237, 6),
    #         bitcollector.get_int(243, 6))
    # else:
    #     add_warn(f'VDM: unknown msgID={msg_id}')
    # pass
