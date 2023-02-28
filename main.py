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
clDkYellow = (16, 16, 0, 50)
clSemiYellow = (36, 36, 0, 50)
clBlack = (0, 0, 0, 0)
clRed = (128, 0, 0)
clLtRed = (255, 0, 0)
clLime = (0, 255, 0)
clMaroon = (28, 0, 28)


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
VIEW_WIDTH, VIEW_HEIGHT = 480, 320
CENTER_X, CENTER_Y = VIEW_WIDTH//2, VIEW_HEIGHT//2
VIEWBOX_RECT = (-CENTER_X, -CENTER_Y, VIEW_WIDTH-CENTER_X-1, VIEW_HEIGHT-CENTER_Y-1)

# CENTER_X, CENTER_Y = 2,3
CORNERS_X_INDEX = (MINX, MINX, MAXX, MAXX)
CORNERS_Y_INDEX = (MINY, MAXY, MINY, MAXY)  # indexes


# framebuff = []
# for y in range(VIEW_HEIGHT):
#     row = []
#     for x in range(VIEW_WIDTH):
#         row.append(0)
#     framebuff.append(row)


my_xy = [0.0, 0.0]
my_angle = 0  # degrees
ANGLE_DELTA = 5.0
MOVE_DELTA = 1
KEYBOARD_DELAY = 120


def draw_line(p0, p1, color):

    x, y = p0[0], p0[1]
    error = 0

    a = p1[1]-p0[1]
    b = p0[0]-p1[0]
    dx, dy = -geometry.sign(b), geometry.sign(a)

    if (b == 0):  # vertical
        while y != p1[1]:
            plot(x, y, color)
            y += dy
    elif (a == 0):  # horizontal
        while x != p1[0]:
            plot(x, y, color)
            x += dx
    # elif (abs(a) == abs(b)):  # diagonal
    #     pass
    # else:

        while x != p1[0] or y != p1[1]:
            plot(x, y, color)

            ex = error + a*dx
            ey = error + b*dy

            if abs(ex) < abs(ey):
                x += dx
                error = ex
            else:
                y += dy
                error = ey

    plot(x, y, color)


def plot(x, y, color):
    """
    input coordinates relative to CENTER
    """

    # print(f'plot ({x},{y}): {color}', end='...')
    if x > VIEWBOX_RECT[MAXX] or x < VIEWBOX_RECT[MINX] or y > VIEWBOX_RECT[MAXY] or y < VIEWBOX_RECT[MINY]:
        # print('skipped')
        return

    x += CENTER_X
    y += CENTER_Y
    # print (f'plot ({x},{y}): {color}')
    pixarr[x][y] = color
    # framebuff[y][x] = color
    # print('OK')


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

    # def clear_framebuff():
    #     for x in range(VIEW_WIDTH):
    #         for y in range(VIEW_HEIGHT):
    #             framebuff[y][x] = clBlack

    def transform_point(point):
        dx = point[0]-my_xy[0]
        dy = point[1]-my_xy[1]

        ad = geometry.decart2polar((dx, dy))
        ad[0] -= my_angle
        ad[1] /= ZOOM_RANGE[zoom_level]
        xy = geometry.polar2decart(ad)
        return xy

    def rotate_box(recid):
        for corner in range(4):
            point = (shapes[recid]['box'][CORNERS_X_INDEX[corner]], shapes[recid]['box'][CORNERS_Y_INDEX[corner]])
            new_pt = transform_point(point)
            # print(f'new_pt: {new_pt[0]:.3f},{new_pt[1]:.3f}')
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
        # print(f'--- Rotate shape ({recid}) =============')
        first = True
        shapes[recid]['work'] = copy.deepcopy(shapes[recid]['origin'])
        for path_id in range(len(shapes[recid]['work'])):
            for point_id in range(len(shapes[recid]['work'][path_id])):
                new_pt = transform_point(shapes[recid]['work'][path_id][point_id])
                shapes[recid]['work'][path_id][point_id] = new_pt
                # print(f'new_pt: {new_pt[0]:.3f},{new_pt[1]:.3f}')
                # print(f'new_pt: {new_pt[0]:.2f},{new_pt[1]:.2f}')
                if first:
                    new_box = [new_pt[0], new_pt[1], new_pt[0], new_pt[1]]
                    first = False
                else:
                    new_box[0] = min(new_box[0], new_pt[0])
                    new_box[1] = min(new_box[1], new_pt[1])
                    new_box[2] = max(new_box[2], new_pt[0])
                    new_box[3] = max(new_box[3], new_pt[1])
        shapes[recid]['rotated'] = new_box
        # print(f'box: {new_box})')
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
        # print(f'put_scanline #{scanline_no}: {arr}')
        for pair_no in range(0, len(arr), 2):
            x1, x2 = arr[pair_no], arr[pair_no+1]

            if (x1 >= VIEWBOX_RECT[MINX] and x1 <= VIEWBOX_RECT[MAXX]) or (x2 >= VIEWBOX_RECT[MINX] and x2 <= VIEWBOX_RECT[MAXX]):
                if x1 < VIEWBOX_RECT[MINX]:
                    x1 = VIEWBOX_RECT[MINX]
                if x2 > VIEWBOX_RECT[MAXX]:
                    x2 = VIEWBOX_RECT[MAXX]
                # put int part
                x1i, x2i = round(x1), round(x2)
                for x in range(x1i, x2i+1):
                    plot(x, scanline_no, clMaroon)
                # for pix in range(math.floor(x1), math.ceil(x2)):
                #     ptr = pix+CENTER_X+VIEW_WIDTH*scanline_no
                #     framebuff[ptr] = 0xFF
                #     print(f'set pix {pix}x{scanline_no} (ptr:{ptr})')
                # put fractional part (for antialias)

    # prepare
    # clear_framebuff()

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

        minY = math.floor(max(new_box[MINY], VIEWBOX_RECT[MINY]))
        maxY = math.ceil(min(new_box[MAXY], VIEWBOX_RECT[MAXY]))

        for scanline in range(minY, maxY+1):
            isec_arr = get_scanline(recid, scanline)
            put_scanline(scanline, isec_arr)

    plot(0, 0, clLime)


def draw_screen():

    def draw_text(x, y, value: str):
        # for dx in range(-2, 3):
        #     for dy in range(-2, 3):
        #         text_surf = font.render(value, 1, clBlack)
        #         screen.blit(text_surf, (x+dx, y+dy))

        ft_font.render_to(screen, (x, y), value, fgcolor=clLime)

    def coords_to_screen(point: tuple, pix_adjust: bool = False, move_center: bool = False):
        x = point[0]+VMARGIN
        y = VMARGIN + VIEW_HEIGHT - point[1]
        if move_center:
            x += CENTER_X
            y -= CENTER_Y
        if pix_adjust:
            x += 0.5
            y += 0.5
        x *= VZOOM
        y *= VZOOM
        return (x, y)

    # prepare bg
    screen.fill(clBlack)

    for recid in shapes:
        sh = shapes[recid]
        if not sh['used']:
            continue
        for path in sh['work']:
            # first = True
            for point_id in range(1, len(path)):
                draw_line(path[point_id-1], path[point_id])

    # draw viewport center
    pygame.draw.circle(screen, clLtRed, (CENTER_X, VIEW_HEIGHT-CENTER_Y), 1)

    # fps + info
    draw_text(10, 10, f'FPS: {clock.get_fps():.0f}')
    draw_text(10, 25, f'POS: {my_xy[0]:.1f},{my_xy[1]:.1f}')
    draw_text(10, 40, f'ANGLE: {round(my_angle,1):.2f}')
    draw_text(10, 55, f'ZOOM: x{ZOOM_RANGE[zoom_level]} (#{zoom_level})')

    return


try:
    ais_db.cache_queries()
    conn = ais_db.connect_db(DATABASE)
    update_cache()

    pygame.init()
    pygame.key.set_repeat(KEYBOARD_DELAY)  # milliseconds
    screen = pygame.display.set_mode((VIEW_WIDTH, VIEW_HEIGHT), flags=pygame.HWSURFACE | pygame.SRCALPHA, depth=32)
    pixarr = pygame.PixelArray(screen)

    clock = pygame.time.Clock()
    ft_font = pygame.freetype.SysFont('Consolas', 14)

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
                    my_xy = [0, 0]
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

except:
    print('-'*30)
    print('Error occured')
    print('-'*30)
    print(traceback.format_exc())
finally:
    conn.close()
