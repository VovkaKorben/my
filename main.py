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
import yaml
import json

clBlue = (0, 0, 255)
clYellow = (255, 255, 0)
clSemiYellow = (26, 26, 0, 50)
clBlack = (0, 0, 0, 0)
clRed = (128, 0, 0)
clLtRed = (255, 0, 0)
clLime = (0, 255, 0)
clMaroon = (28, 0, 28)


USE_PYGAME = False
USE_PYGAME = True


# shapes collector
SHAPES_UPDATE = 5*60*1000  # 5 min for update shapes
shapes_timer = 0
DATABASE = 'C:\\ais\\ais.db'

# display
# ZOOM_RANGE = (1, 50, 100, 250, 500, 1000, 2000, 3000, 5000)  # , 10000, 15000, 20000, 50000)
ZOOM_RANGE = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
zoom_level = 0  # len(ZOOM_RANGE)-1
shapes = {}

# math related
VIEW_W, VIEW_H = 60, 40
VIEW_X, VIEW_Y = VIEW_W//3, VIEW_H//2
VIEWBOX_RECT = (-VIEW_X, -VIEW_Y, VIEW_W-VIEW_X, VIEW_H-VIEW_Y)

# VIEW_X, VIEW_Y = 2,3
CORNERS_X_INDEX = (MINX, MINX, MAXX, MAXX)
CORNERS_Y_INDEX = (MINY, MAXY, MINY, MAXY)  # indexes
framebuff = bytearray(VIEW_W * VIEW_H)

# draw related
VZOOM, VMARGIN = 15, 4

my_xy = [0.0, 0.0]
my_angle = 45  # degrees
ANGLE_DELTA = 5.0
MOVE_DELTA = 0.2
KEYBOARD_DELAY = 120


def garbage_shapes():  # remove old shapes
    pass


def load_shapes():
    overlap_coeff = 1.05 * ZOOM_RANGE[-1]
    params = {
        'minx': my_xy[0]+VIEWBOX_RECT[0]*overlap_coeff,
        'miny': my_xy[1]+VIEWBOX_RECT[1]*overlap_coeff,
        'maxx': my_xy[0]+VIEWBOX_RECT[2]*overlap_coeff,
        'maxy': my_xy[1]+VIEWBOX_RECT[3]*overlap_coeff,
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
        for i in range(VIEW_W * VIEW_H):
            framebuff[i] = 0x00

    def transform_point(point):
        # return point
        xy = [point[0]-my_xy[0], point[1]-my_xy[1]]
        ad = geometry.decart2polar(xy)
        ad[0] -= my_angle
        ad[1] /= ZOOM_RANGE[zoom_level]
        xy = geometry.polar2decart(ad)
        return xy

    # def transform_point(point):
    #     dx, dy = point[0]-my_xy[0], point[1]-my_xy[1]
    #     a = my_angle/180*math.pi
    #     cosine, sine = math.cos(a), math.sin(a)
    #     x = my_xy[0] + dx*cosine-dy*sine
    #     y = my_xy[1] + dx*sine+dy*cosine
    #     return (x, y)

    def rotate_box(recid):
        print(f'--- Rotate box ({recid}) =============')
        for corner in range(4):
            point = (shapes[recid]['box'][CORNERS_X_INDEX[corner]], shapes[recid]['box'][CORNERS_Y_INDEX[corner]])
            new_pt = transform_point(point)
            print(f'new_pt: {new_pt[0]:.3f},{new_pt[1]:.3f}')
            if corner == 0:
                new_box = [new_pt[0], new_pt[1], new_pt[0], new_pt[1]]
            else:
                new_box[0] = min(new_box[0], new_pt[0])
                new_box[1] = min(new_box[1], new_pt[1])
                new_box[2] = max(new_box[2], new_pt[0])
                new_box[3] = max(new_box[3], new_pt[1])
        print(f'box: {new_box})')
        return new_box

    def rotate_shape(recid):
        # calculate all shape rotation with update a bounds
        print(f'--- Rotate shape ({recid}) =============')
        first = True
        shapes[recid]['work'] = copy.deepcopy(shapes[recid]['origin'])
        for path_id in range(len(shapes[recid]['work'])):
            for point_id in range(len(shapes[recid]['work'][path_id])):
                new_pt = transform_point(shapes[recid]['work'][path_id][point_id])
                shapes[recid]['work'][path_id][point_id] = new_pt
                print(f'new_pt: {new_pt[0]:.3f},{new_pt[1]:.3f}')
                if first:
                    new_box = [new_pt[0], new_pt[1], new_pt[0], new_pt[1]]
                    first = False
                else:
                    new_box[0] = min(new_box[0], new_pt[0])
                    new_box[1] = min(new_box[1], new_pt[1])
                    new_box[2] = max(new_box[2], new_pt[0])
                    new_box[3] = max(new_box[3], new_pt[1])
        shapes[recid]['rotated'] = new_box
        print(f'box: {new_box})')
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
            if (x1 >= SCRX and x1 <= VIEW_W) or (x2 >= SCRX and x2 <= VIEW_W):
                if x1 < SCRX:
                    x1 = SCRX
                if x2 >= VIEW_W:
                    x2 = VIEW_W
                # put int part
                for pix in range(math.floor(x1), math.ceil(x2)):
                    ptr = pix+VIEW_W*scanline_no
                    framebuff[ptr] = 0xFF
                    # print(f'set pix {pix}x{scanline_no} (ptr:{ptr})')
                # put fractional part (for antialias)

                # start = min(SCRX, arr[pair_no])
                # end= max(VIEW_W

    clear_framebuff()

    # rotate box and get new bounds
    for recid in shapes:
        shapes[recid]['used'] = False
        # calculate new transormed corners
        new_box = rotate_box(recid)
        print(f'rotate_box(recid #{recid}): {new_box})')
        if not geometry.check_rect_intersect(VIEWBOX_RECT, new_box):
            continue

        # check if full rotate geometry still visible
        new_box = rotate_shape(recid)
        if not geometry.check_rect_intersect(VIEWBOX_RECT, new_box):
            continue
        shapes[recid]['used'] = True
        # for scanline in range(VIEW_H):
        #     isec_arr = get_scanline(recid, scanline)
        #     put_scanline(scanline, isec_arr)


def draw_screen():
    def draw_text(x, y, value):
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                text_surf = font.render(value, 1, clBlack)
                screen.blit(text_surf, (x+dx, y+dy))

        text_surf = font.render(value, 1, clLime)
        screen.blit(text_surf, (x, y))

    def coords_to_screen(point: tuple, center: bool):
        x = point[0]+VMARGIN+VIEW_X
        if center:
            x += 0.5
        y = VIEW_H - (point[1]+VIEW_Y)
        y = y+VMARGIN
        if center:
            y += 0.5
        return (round(x*VZOOM), round(y*VZOOM))

    # draw everything
    screen.fill(clBlack)

    # grid
    for x in range(VIEW_W+VMARGIN*2):
        pygame.draw.line(screen, clSemiYellow,
                         (x*VZOOM, 0),
                         (x*VZOOM, (VIEW_H+VMARGIN*2)*VZOOM)
                         )
    for y in range(VIEW_W+VMARGIN*2):
        pygame.draw.line(screen, clSemiYellow,
                         (0, y*VZOOM),
                         ((VIEW_W+VMARGIN*2)*VZOOM, y*VZOOM)
                         )
    # draw "pixels"
    for y in range(VIEW_H):
        for x in range(VIEW_W):
            ptr = x+VIEW_W*y
            if framebuff[ptr] == 0xFF:
                current_point = coords_to_screen((x, y), False)
                pygame.Surface.fill(screen, clMaroon,
                                    (current_point[0]+1, current_point[1]+1, VZOOM-1, VZOOM-1))
    # draw bounds rect
    pygame.draw.rect(screen, clYellow, (
                     (VMARGIN*VZOOM, VMARGIN*VZOOM),
                     (VIEW_W*VZOOM+1, VIEW_H*VZOOM+1)
                     ), width=1)

    # draw viewport center
    pygame.draw.circle(screen, clLtRed, ((VIEW_X+VMARGIN)*VZOOM, (VIEW_H-VIEW_Y+VMARGIN)*VZOOM), 3)

    # draw shapes

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

    # fps + info
    draw_text(10, 10, f'FPS: {clock.get_fps():.0f}')
    draw_text(10, 30, f'POS: {my_xy[0]:.1f},{my_xy[1]:.1f}')
    draw_text(10, 50, f'ANGLE: {round(my_angle,1):.2f}')
    draw_text(10, 70, f'ZOOM: x{ZOOM_RANGE[zoom_level]} (#{zoom_level})')


try:
    ais_db.cache_queries()
    conn = ais_db.connect_db(DATABASE)
    update_cache()

    if USE_PYGAME:
        pygame.init()
        pygame.key.set_repeat(KEYBOARD_DELAY)  # milliseconds
        scr_size = ((VIEW_W+VMARGIN*2)*VZOOM, (VIEW_H+VMARGIN*2)*VZOOM)
        screen = pygame.display.set_mode(scr_size, flags=pygame.HWSURFACE | pygame.SRCALPHA, depth=32)
        # surf = pygame.Surface(scr_size, flags=pygame.HWSURFACE | pygame.SRCALPHA,  depth=32)
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Consolas", 18, bold=True)
        point_font = pygame.font.SysFont("Consolas", 12, bold=False)

        calc_visible()
        while True:
            # Process player inputs.
            handled = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        raise SystemExit
                    elif event.key == pygame.K_LEFT:
                        my_xy[0] -= MOVE_DELTA
                    elif event.key == pygame.K_RIGHT:
                        my_xy[0] += MOVE_DELTA
                    elif event.key == pygame.K_UP:
                        my_xy[1] += MOVE_DELTA
                    elif event.key == pygame.K_DOWN:
                        my_xy[1] -= MOVE_DELTA
                    elif event.key == pygame.K_KP_MINUS:
                        if zoom_level > 0:
                            zoom_level -= 1
                    elif event.key == pygame.K_KP_PLUS:
                        if zoom_level < (len(ZOOM_RANGE)-1):
                            zoom_level += 1
                    elif event.key == pygame.K_PAGEDOWN:
                        my_angle -= ANGLE_DELTA
                        if my_angle < 0.0:
                            my_angle += 360.0
                    elif event.key == pygame.K_PAGEUP:
                        my_angle += ANGLE_DELTA
                        if my_angle >= 360.0:
                            my_angle -= 360.0
                    elif event.key == pygame.K_RETURN:
                        my_xy = [5.0, 4.5]
                        my_angle = 0  # degrees
                        zoom_level = 0
                    elif event.key == pygame.K_KP_ENTER:
                        # print(yaml.dump(shapes, default_flow_style=False))
                        print(json.dumps(shapes, indent=2, default=str))
                    if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN, pygame.K_KP_MINUS, pygame.K_KP_PLUS,
                                     pygame.K_PAGEDOWN, pygame.K_PAGEUP, pygame.K_RETURN, pygame.K_KP_ENTER]:
                        handled = True

            if handled:
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
