import geometry
from geometry import MINX, MINY, MAXX, MAXY
import pygame.gfxdraw
import pygame
import os
import ais_db
import traceback
import helpers
import sqlite3
import math
import copy
# USE_PYGAME = False
USE_PYGAME = True

mypos = (20.293872151995963, 60.167428760910944)  # lon lat


# shapes collector
SHAPES_UPDATE = 5*60*1000  # 5 min for update shapes
shapes_timer = 0
DATABASE = 'C:\\ais\\ais.db'

# display
# ZOOM_RANGE = (1, 50, 100, 250, 500, 1000, 2000, 3000, 5000)  # , 10000, 15000, 20000, 50000)
ZOOM_RANGE = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
zoom_level = 2  # len(ZOOM_RANGE)-1
shapes = {}

# math related
SCRX, SCRY, SCRW, SCRH = 0, 0, 60, 40
VIEWBOX_RECT = (SCRX, SCRY, SCRW, SCRH)
VIEWX, VIEWY = SCRW//3, SCRH//2
CORNERS_X_INDEX = (MINX, MINX, MAXX, MAXX)
CORNERS_Y_INDEX = (MINY, MAXY, MINY, MAXY)  # indexes
framebuff = bytearray(SCRW * SCRH)

# draw related
VZOOM, VMARGIN = 8, 15
clBlue = (0, 0, 255)
clYellow = (255, 255, 0)
clSemiYellow = (26, 26, 0, 50)
clBlack = (0, 0, 0, 0)
clRed = (128, 0, 0)
clLtRed = (255, 0, 0)
clLime = (0, 255, 0)
clMaroon = (28, 0, 28)


my_xy = [5.0, 2.0]
MOVE_VALUE = 1
my_angle = 0  # degrees


def garbage_shapes():  # remove old shapes
    pass


def load_shapes():
    overlap_coeff = 1.05
    z = ZOOM_RANGE[-1]
    params = {
        'minx': my_xy[0]-(VIEWX-SCRX)*z*overlap_coeff,
        'miny': my_xy[1] - (VIEWY-SCRY)*z*overlap_coeff,
        'maxx': my_xy[0]+(SCRW - VIEWX)*z*overlap_coeff,
        'maxy': my_xy[1]+(SCRW - VIEWY)*z*overlap_coeff,
    }

    c = conn.cursor()
    shapes_count, points_count = 0, 0
    # get visible shapes
    try:
        c.execute(ais_db.sql['get_shapes'], params)
        params = []
        while True:
            data = c.fetchone()
            if data == None:
                break
            if not (data['recid'] in shapes):
                shapes[data['recid']] = {
                    'type': data['type'],
                    'name': data['name'],
                    'box': (data['minx'], data['miny'], data['maxx'], data['maxy']),
                    'origin': [],
                }
                params.append(data['recid'])
            shapes[data['recid']]['last_access'] = helpers.utc_ms()
            shapes_count += 1

        if len(params) > 0:
            query = ais_db.sql['get_points'].format(seq=','.join(['?']*len(params)))
            c.execute(query, params)
            last_recid = None
            while True:
                data = c.fetchone()
                if data == None:
                    break
                if last_recid != data['recid']:
                    last_partid = None
                    last_recid = data['recid']
                if last_partid != data['partid']:
                    last_partid = data['partid']
                    shapes[data['recid']]['origin'].append([])
                    part_id = len(shapes[data['recid']]['origin'])-1
                shapes[data['recid']]['origin'][part_id].append((data['x'], data['y']))
                points_count += 1
    finally:
        c.close()
        print(f'Loaded: {shapes_count} shapes, {points_count} points')


def update_cache():
    load_shapes()
    garbage_shapes()


def calc_visible():
    def clear_framebuff():
        for i in range(SCRW * SCRH):
            framebuff[i] = 0x00

    def transform_point(point):
        # return point
        xy = [point[0]-my_xy[0], point[1]-my_xy[1]]
        ad = geometry.decart2polar(xy)
        ad[0] -= my_angle
        ad[1] /= ZOOM_RANGE[zoom_level]
        xy = geometry.polar2decart(ad)
        # return (xy[0]+my_xy[0], xy[1]+my_xy[1])
        return xy

    def rotate_box(recid):

        for corner in range(4):
            point = (shapes[recid]['box'][CORNERS_X_INDEX[corner]], shapes[recid]['box'][CORNERS_Y_INDEX[corner]])
            new_pt = transform_point(point)
            if corner == 0:
                new_box = [new_pt[0], new_pt[1], new_pt[0], new_pt[1]]
            else:
                new_box[0] = min(new_box[0], new_pt[0])
                new_box[1] = min(new_box[1], new_pt[1])
                new_box[2] = max(new_box[2], new_pt[0])
                new_box[3] = max(new_box[3], new_pt[1])
        return new_box

    def rotate_shape(recid):
        # calculate all shape rotation with update a bounds
        first = True
        shapes[recid]['work'] = copy.deepcopy(shapes[recid]['origin'])  # copy.copy(shapes[recid]['origin'])
        for path_id in range(len(shapes[recid]['work'])):
            for point_id in range(len(shapes[recid]['work'][path_id])):
                point = transform_point(shapes[recid]['work'][path_id][point_id])
                shapes[recid]['work'][path_id][point_id] = point

                if first:
                    new_box = [point[0], point[1], point[0], point[1]]
                    first = False
                else:
                    new_box[0] = min(new_box[0], point[0])
                    new_box[1] = min(new_box[1], point[1])
                    new_box[2] = max(new_box[2], point[0])
                    new_box[3] = max(new_box[3], point[1])
        shapes[recid]['rotated'] = new_box
        return new_box

    def get_scanline(recid, scanline_no):
        def partition(low, high):
            pivot = arr[high]
            i = low-1
            for j in range(low, high):
                if arr[j] < pivot:
                    i += 1
                    arr[i], arr[j] = arr[j], arr[i]
            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            return (i + 1)

        def quickSort(low, high):
            if low < high:
                pi = partition(low, high)
                quickSort(low, pi - 1)
                quickSort(pi + 1, high)

        arr = []

        scanline_left = (shapes[recid]['rotated'][MINX]-1, scanline_no+0.5)
        scanline_right = (shapes[recid]['rotated'][MAXX]+1, scanline_no+0.5)
        for path in shapes[recid]['work']:
            prev_point = path[-1]
            for point in path:
                a = geometry.line_intersect(prev_point, point, scanline_left, scanline_right)
                if len(a) > 0:
                    arr.append(a[0])
                prev_point = point
        quickSort(0, len(arr)-1)
        return arr

    def put_scanline(scanline_no, arr):
        # print(f'scanline_no: {scanline_no}')
        for pair_no in range(0, len(arr), 2):
            x1, x2 = arr[pair_no], arr[pair_no+1]
            if (x1 >= SCRX and x1 <= SCRW) or (x2 >= SCRX and x2 <= SCRW):
                if x1 < SCRX:
                    x1 = SCRX
                if x2 >= SCRW:
                    x2 = SCRW
                # put int part
                for pix in range(math.floor(x1), math.ceil(x2)):
                    ptr = pix+SCRW*scanline_no
                    framebuff[ptr] = 0xFF
                    # print(f'set pix {pix}x{scanline_no} (ptr:{ptr})')
                # put fractional part (for antialias)

                # start = min(SCRX, arr[pair_no])
                # end= max(SCRW

    clear_framebuff()

    # rotate box and get new bounds
    for recid in shapes:
        shapes[recid]['used'] = False
        # calculate new transormed corners
        new_box = rotate_box(recid)
        if not geometry.check_rect_intersect(VIEWBOX_RECT, new_box):
            continue

        # check if full rotate geometry still visible
        new_box = rotate_shape(recid)
        if not geometry.check_rect_intersect(VIEWBOX_RECT, new_box):
            continue
        shapes[recid]['used'] = True
        for scanline in range(SCRH):
            isec_arr = get_scanline(recid, scanline)
            put_scanline(scanline, isec_arr)


def draw_screen():

    def coords_to_screen(xy: tuple, center: bool):
        x = xy[0]+VMARGIN
        if center:
            x += 0.5
        y = SCRH - xy[1]
        y = y+VMARGIN
        if center:
            y += 0.5
        return (round(x*VZOOM), round(y*VZOOM))

    # draw everything
    screen.fill(clBlack)

    # grid
    for x in range(SCRW+VMARGIN*2):
        pygame.draw.line(screen, clSemiYellow,
                         (x*VZOOM, 0),
                         (x*VZOOM, (SCRH+VMARGIN*2)*VZOOM)
                         )
    for y in range(SCRW+VMARGIN*2):
        pygame.draw.line(screen, clSemiYellow,
                         (0, y*VZOOM),
                         ((SCRW+VMARGIN*2)*VZOOM, y*VZOOM)
                         )

    for y in range(SCRY, SCRH):
        for x in range(SCRX, SCRW):
            ptr = (x-SCRX)+SCRW*(y-SCRY)
            if framebuff[ptr] == 0xFF:
                current_point = coords_to_screen((x, y), False)
                pygame.Surface.fill(screen, clMaroon,
                                    (current_point[0]+1, current_point[1]+1, VZOOM-1, VZOOM-1))

    pygame.draw.line(screen, clYellow, coords_to_screen((0, 0), True), coords_to_screen((SCRW-1, 0), True), width=2)
    pygame.draw.line(screen, clYellow, coords_to_screen((0, 0), True), coords_to_screen((0, SCRH-1), True), width=2)
    pygame.draw.line(screen, clYellow, coords_to_screen((SCRW-1, 0), True), coords_to_screen((SCRW-1, SCRH-1), True), width=2)
    pygame.draw.line(screen, clYellow, coords_to_screen((0, SCRH-1), True), coords_to_screen((SCRW-1, SCRH-1), True), width=2)

    for recid in shapes:
        sh = shapes[recid]
        if sh['used']:
            # work = shapes[recid]['work'] # shortcut
            for path_id in range(len(sh['work'])):
                # first = True
                for point_id in range(len(sh['work'][path_id])):

                    current_point = coords_to_screen(sh['work'][path_id][point_id], True)
                    # start line or draw it
                    if point_id == 0:
                        first_point = current_point  # required for closing curve
                    else:
                        pygame.draw.line(screen, clBlue, prev_point, current_point, width=2)
                    prev_point = current_point

                    # draw point number
                    # ptf = point_font.render(f'{point_id} {sh["work"][path_id][point_id]}', True, clLime)
                    ptf = point_font.render(f'{point_id}', True, clLime)
                    screen.blit(ptf, (current_point[0]+5, current_point[1]-15))

                # closinge curve for polygone
                if shapes[recid]['type'] == 5:
                    pygame.draw.line(screen, clBlue, first_point, current_point, width=2)

    pygame.draw.circle(screen, clLtRed, coords_to_screen((VIEWX, VIEWY), False), VZOOM//2)

    # fps

    text_surf = font.render(str(int(clock.get_fps())), 1, clRed)
    screen.blit(text_surf, (10, 10))

    text_surf = font.render(f'POS: {my_xy[0]:.1f}x{my_xy[1]:.1f}', 1, clRed)
    screen.blit(text_surf, (10, 30))
    text_surf = font.render(f'ANGLE: {round(my_angle,1):.2f}', 1, clRed)
    screen.blit(text_surf, (10, 50))
    text_surf = font.render(f'ZOOM: x{ZOOM_RANGE[zoom_level]} (#{zoom_level})', 1, clRed)
    screen.blit(text_surf, (10, 70))
    # pygame.Surface.blit(screen, surf, (0, 0))


try:
    ais_db.cache_queries()
    conn = ais_db.connect_db(DATABASE)
    update_cache()

    if USE_PYGAME:
        pygame.init()
        pygame.key.set_repeat(120)  # milliseconds
        scr_size = ((SCRW+VMARGIN*2)*VZOOM, (SCRH+VMARGIN*2)*VZOOM)
        screen = pygame.display.set_mode(scr_size, flags=pygame.HWSURFACE | pygame.SRCALPHA, depth=32)
        # surf = pygame.Surface(scr_size, flags=pygame.HWSURFACE | pygame.SRCALPHA,  depth=32)
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Consolas", 18, bold=True)
        point_font = pygame.font.SysFont("Consolas", 12, bold=False)

        while True:
            # Process player inputs.
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        raise SystemExit
                    elif event.key == pygame.K_LEFT:
                        my_xy[0] -= MOVE_VALUE
                    elif event.key == pygame.K_RIGHT:
                        my_xy[0] += MOVE_VALUE
                    elif event.key == pygame.K_UP:
                        my_xy[1] -= MOVE_VALUE
                    elif event.key == pygame.K_DOWN:
                        my_xy[1] += MOVE_VALUE
                    elif event.key == pygame.K_KP_MINUS:
                        if zoom_level > 0:
                            zoom_level -= 1
                    elif event.key == pygame.K_KP_PLUS:
                        if zoom_level < (len(ZOOM_RANGE)-1):
                            zoom_level += 1
                    elif event.key == pygame.K_PAGEDOWN:
                        my_angle -= MOVE_VALUE
                        if my_angle < 0.0:
                            my_angle += 360.0
                    elif event.key == pygame.K_PAGEUP:
                        my_angle += MOVE_VALUE
                        if my_angle >= 360.0:
                            my_angle -= 360.0
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        my_xy = [5.0, 4.5]
                        my_angle = 0  # degrees
                        zoom_level = 0

            calc_visible()
            draw_screen()
            pygame.display.flip()  # Refresh on-screen display
            clock.tick(60)         # wait until next frame (at 60 FPS)
    else:
        calc_visible()

except:
    print('-'*30)
    print('Error occured')
    print('-'*30)
    print(traceback.format_exc())
finally:
    conn.close()
