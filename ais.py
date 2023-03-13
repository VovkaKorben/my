import traceback
import os
import time
import ais_mysql
import nmea
import helpers
import pygame.gfxdraw
import pygame
import pprint

clBlue = (0, 0, 255)
clYellow = (255, 255, 0)
clDkYellow = (16, 16, 0, 50)
clSemiYellow = (36, 36, 0, 50)
clBlack = (0, 0, 0)
clRed = (128, 0, 0)
clLtRed = (255, 0, 0)
clLime = (0, 255, 0)
clMaroon = (28, 0, 28)
clDkGray = (64, 64, 64)
clGray = (128, 128, 128)
clLtGray = (192, 192, 192)

VIEW_WIDTH, VIEW_HEIGHT = 1100, 900
KEYBOARD_DELAY = 120
FONT_SIZE = 14

last_msg_id, messages_count = 0, 0
read_sql = ais_mysql.read_query('main/read_rawdata.sql')

last_msg_id = -1  # dbg


def read_nmea():
    global last_msg_id, messages_count
    try:
        # c = mysql_conn.cursor(dictionary=True)
        mysql_cursor.execute(read_sql, (last_msg_id,))
        # print(mysql_cursor.statement)
        while True:
            row = mysql_cursor.fetchone()
            if row == None:
                break
            nmea.parse_nmea(row['data'])
            last_msg_id = row['id']
            messages_count += 1
    finally:
        mysql_conn.commit()
        # pass
        # c.close()


def draw_screen():
    def draw_text(x, y, value: str, fgcolor=clLime):
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                ft_font.render_to(screen, (x+dx, y+dy), value, clBlack)

        ft_font.render_to(screen, (x, y), value, fgcolor)

    global messages_count
    screen.fill(clBlack)

    draw_text(10, 10, f'FPS: {clock.get_fps():.0f}')
    draw_text(10, 30, f'Messages: {messages_count}', clYellow)
    draw_text(10, 50, f'lat:{nmea.gps.lat:.12f},lon:{nmea.gps.lon:.12f}', clYellow)
    draw_text(10, 70, f'Used sat:{nmea.gps.used_sv}', clYellow)

    # nmea.sat.sat_list = sorted(nmea.sat.sat_list)

    prn_list = list(nmea.sat.sat_list.keys())
    prn_list.sort()
    y = 5
    ms = helpers.utc_ms()
    for prn in prn_list:
        tm = nmea.sat.sat_list[prn]["last_access"]
        tm = (ms - tm)/1000
        draw_text(400, y, f'PRN:{prn}', clYellow)
        draw_text(500, y, f'Tm:{ tm:>5.1f}', clYellow)
        v = '-' if nmea.sat.sat_list[prn]["elevation"] == None else str(nmea.sat.sat_list[prn]["elevation"])
        draw_text(600, y, f'Elev:{ v:>3}', clYellow)
        v = '-' if nmea.sat.sat_list[prn]["azimuth"] == None else str(nmea.sat.sat_list[prn]["azimuth"])
        draw_text(700, y, f'Azim:{ v:>3}', clYellow)
        v = '-' if nmea.sat.sat_list[prn]["snr"] == None else str(nmea.sat.sat_list[prn]["snr"])
        draw_text(800, y, f'SNR:{ v:>3}', clYellow)
        # draw_text(600, y, f'Az:{ nmea.sat.sat_list[prn]["azimuth"]:>3}', clYellow)
        # draw_text(700, y, f'Snr:{ nmea.sat.sat_list[prn]["snr"]:>3}', clYellow)

        y += FONT_SIZE
        # sorted_dict = {i: nmea.sat.sat_list[i] for i in myKeys}

    v1 = '-' if nmea.gps.modeAM == None else str(nmea.gps.modeAM)
    v2 = '-' if nmea.gps.modeFIX == None else str(nmea.gps.modeFIX)
    draw_text(10, 100, f'A/M: {v1} FIX: {v2}', clYellow)

    v1 = '-' if nmea.gps.pdop == None else str(nmea.gps.pdop)
    v2 = '-' if nmea.gps.hdop == None else str(nmea.gps.hdop)
    v3 = '-' if nmea.gps.vdop == None else str(nmea.gps.vdop)
    draw_text(10, 120, f'PDOP: {v1} HDOP: {v2} VDOP: {v3}', clYellow)


try:
    # setup pygame
    pygame.init()
    pygame.key.set_repeat(KEYBOARD_DELAY)  # milliseconds
    screen = pygame.display.set_mode((VIEW_WIDTH, VIEW_HEIGHT), flags=pygame.HWSURFACE | pygame.SRCALPHA, depth=32)
    clock = pygame.time.Clock()
    ft_font = pygame.freetype.SysFont('Consolas', FONT_SIZE)
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN])
    
    # setup sql
    mysql_conn = ais_mysql.connect_db(user='nmearead', password='nmearead')
    mysql_cursor = mysql_conn.cursor(dictionary=True)
    # retrieve max ID
    sql = ais_mysql.read_query('main/get_max_id.sql')
    mysql_cursor.execute(sql)
    row = mysql_cursor.fetchone()
    last_msg_id = int(row['maxid'])
    mysql_conn.commit()

    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True               # raise SystemExit
            if event.type == pygame.KEYDOWN:
                mult = 5 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
                if event.key == pygame.K_ESCAPE:
                    done = True
        read_nmea()
        draw_screen()
        pygame.display.flip()  # Refresh on-screen display
        clock.tick(60)         # wait until next frame (at 60 FPS)

except:
    print('------ MAIN ERROR ------')
    print(traceback.format_exc())
finally:
    pygame.quit()
    mysql_cursor.close()
    mysql_conn.close()
