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
# import logger
import pyperclip
clBlue = (0, 0, 255)
clYellow = (255, 255, 0)
clDkYellow = (16, 16, 0, 50)
clSemiYellow = (36, 36, 0, 50)
clBlack = (0, 0, 0, 0)
clRed = (128, 0, 0)
clLtRed = (255, 0, 0)
clLime = (0, 255, 0)
clMaroon = (28, 0, 28)
clSea = (60, 107, 180)
clLand = (179, 136, 76)
CENTER_SIZE = 4

# shapes collector
SHAPES_UPDATE = 5*60*1000  # 5 min for update shapes
shapes_timer = 0


# display
# ZOOM_RANGE = (1, 50, 100, 250, 500, 1000, 2000, 3000, 5000)  # , 10000, 15000, 20000, 50000)
ZOOM_RANGE = (0.1, 0.2, 0.5, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
ZOOM_INIT = 3


# math related
VIEW_WIDTH, VIEW_HEIGHT = 300, 200
CENTER_X, CENTER_Y = VIEW_WIDTH//2, VIEW_HEIGHT//2
VIEWBOX_RECT = (-CENTER_X, -CENTER_Y, VIEW_WIDTH-CENTER_X-1, VIEW_HEIGHT-CENTER_Y-1)

# CENTER_X, CENTER_Y = 2,3
CORNERS_X_INDEX = (MINX, MINX, MAXX, MAXX)
CORNERS_Y_INDEX = (MINY, MAXY, MINY, MAXY)  # indexes

my_xy, my_angle, zoom_level = [0.0, 0.0], 0.0, 4
shapes = {}
scanlines = []
for y in range(VIEW_HEIGHT):
    scanlines.append([])


# framebuff = []
# for y in range(VIEW_HEIGHT):
#     row = []
#     for x in range(VIEW_WIDTH):
#         row.append(0)
#     framebuff.append(row)


ANGLE_DELTA = 1.0
MOVE_DELTA = 1
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


def draw_screen():

    def draw_line(p0, p1, color):

        print(f'draw_line {path[point_id-1]} -> {path[point_id]}')
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

    def segment_intersect(segment_start: dict, segment_end: dict, scanline_min: float, scanline_max: float, scanline_y: float):
        """
        returns:
        [-2] = segment touches with min or max value with scanline
        [-1] = segment is parallel with scanline
        [0] = not intersect
        [1,x] = intersect in X point
        """
        # check Y-bound
        # if (not (main_rect[MAXX] <= test_rec[MINX] or main_rect[MINX] >= test_rec[MAXX] or main_rect[MINY] >= test_rec[MAXY] or main_rect[MAXY] <= test_rec[MINY]):

        # check parallel
        segment_dy = segment_end[1]-segment_start[1]
        if geometry.is_zero(segment_dy):
            return [-1]

        # check min/max
        if geometry.is_zero(segment_start[1]-scanline_y) or geometry.is_zero(segment_end[1]-scanline_y):
            return [-2]

        # check projection
        scanline_dx = scanline_max-scanline_min
        z = - scanline_dx * segment_dy
        if geometry.is_zero(z):
            return [0]
        segment_dx = segment_end[0]-segment_start[0]
        dx, dy = segment_start[0]-scanline_min, segment_start[1]-scanline_y
        ua = scanline_dx * dy / z
        if ua < 0.0 or ua > 1.0:
            return [0]
        ub = (segment_dx * dy - segment_dy * dx)/z
        if ub < 0.0 or ub > 1.0:
            return [0]

        return [1, segment_start[0] + ua*segment_dx]

    def calc_scanline(sh):

        # clear intersections buffer
        for y in range(VIEW_HEIGHT):
            scanlines[y].clear()

        minX = sh['rotated'][MINX]-1
        maxX = sh['rotated'][MAXX]+1

        curr_index = 0
        # process segments
        for path in sh['work']:
            prev_point = path[-1]
            for point in path:
                s = f'segment: {prev_point} to {point}'
                print(f'index = {curr_index}, {s}')
                pyperclip.copy(s)
                if prev_point[0] < VIEWBOX_RECT[MAXX] or point[0] < VIEWBOX_RECT[MAXX]:
                    # print(prev_point, point)

                    # get segment Y-axis min & max
                    minY = min(prev_point[1], point[1])
                    maxY = max(prev_point[1], point[1])

                    if geometry.is_zero(maxY-minY) and minY > VIEWBOX_RECT[MINY] and minY < VIEWBOX_RECT[MAXY]:
                        # if parallel to X-axis and lies into Y bounds
                        scanlines[math.floor(minY)+CENTER_Y].extend([prev_point[0], point[0]])
                    else:

                        # crop to bounds
                        minY = math.floor(max(minY, VIEWBOX_RECT[MINY]))
                        maxY = math.ceil(min(maxY, VIEWBOX_RECT[MAXY]))

                        for y in range(minY, maxY):
                            a = segment_intersect(prev_point,  point, minX, maxX, y+0.5)
                            # print(a)
                            if a[0] == 1:  # intersect
                                scanlines[y+CENTER_Y].append(a[1])
                prev_point = point
                curr_index += 1
        # del prev_point, point, minX, maxX, minY, maxY, path
        # sort & put to screen

    def draw_scanline(color):
        for y in range(VIEW_HEIGHT):
            l = len(scanlines[y])
            if l > 0:
                geometry.quickSort(scanlines[y], 0, l-1)
                ypos = VIEW_HEIGHT-y-1
                print(f'Y = {y-CENTER_Y}, data: {scanlines[y]}')
                ptr = 0
                while ptr < l:
                    start = round(scanlines[y][ptr])
                    ptr += 1
                    if ptr < l:
                        count = round(scanlines[y][ptr])
                    else:
                        count = VIEWBOX_RECT[MAXX]
                    count -= start
                    start += CENTER_X
                    ptr += 1

                    while count > 0:
                        pixarr[start][ypos] = color
                        start += 1
                        count -= 1

    def draw_text(x, y, value: str):
        # for dx in range(-2, 3):
        #     for dy in range(-2, 3):
        #         text_surf = font.render(value, 1, clBlack)
        #         screen.blit(text_surf, (x+dx, y+dy))

        ft_font.render_to(screen, (x, y), value, fgcolor=clLime)

    def draw_shape(sh, fill=None, outline=None):
        if not (fill is None):
            calc_scanline(sh)
            draw_scanline(fill)
        # outline
        if not (outline is None):
            for path in sh['work']:
                # first = True
                # print(f'len(path): {len(path)}')
                # pygame.draw.aalines(screen,clLime,True,path)
                for point_id in range(len(path)):
                    pt = (path[point_id][0]+CENTER_X, VIEW_HEIGHT-path[point_id][1]-CENTER_Y-1)
                    if point_id == 0:
                        first = pt
                    else:
                        pygame.draw.line(screen, outline, prev_pt, pt)
                    prev_pt = pt
                pygame.draw.line(screen, clLime,  pt, first)

    # prepare bg
    screen.fill(clSea)
    pixarr = pygame.PixelArray(screen)
    for recid in shapes:
        sh = shapes[recid]
        if not sh['used']:
            continue
        draw_shape(sh, fill=clLand, outline=None)

    # draw viewport center
    pygame.draw.line(screen, clRed,  (CENTER_X-CENTER_SIZE, CENTER_Y), (CENTER_X+CENTER_SIZE, CENTER_Y))
    pygame.draw.line(screen, clRed,  (CENTER_X, CENTER_Y-CENTER_SIZE), (CENTER_X, CENTER_Y+CENTER_SIZE))

    # fps + info
    draw_text(10, 10, f'FPS: {clock.get_fps():.0f}')
    draw_text(10, 25, f'POS: {my_xy[0]:.1f},{my_xy[1]:.1f}')
    draw_text(10, 40, f'ANGLE: {round(my_angle,1):.2f}')
    draw_text(10, 55, f'ZOOM: x{ZOOM_RANGE[zoom_level]} (#{zoom_level})')


def do_Test():

    try:

        calc_visible()
        draw_screen()

        for test_zoom in range(2, 6):
            zoom_level = test_zoom
            my_xy[0] = -5.0
            while my_xy[0] < 5.0:
                my_xy[1] = -5.0
                while my_xy[1] < 5.0:
                    my_angle = 0.0
                    while my_angle < 370.0:
                        logger.write_log(f'my_xy: {my_xy}, my_angle: {my_angle}, zoom_level: {zoom_level} (x{ZOOM_RANGE[zoom_level]})')
                        calc_visible()
                        draw_screen()
                        my_angle += 0.1
                    my_xy[1] += 0.1
                my_xy[0] += 0.1
    except:
        logger.write_log(f'!! my_xy: {my_xy}, my_angle: {my_angle}, zoom_level: {zoom_level}')


try:
    ais_db.cache_queries()
    conn = ais_db.connect_db(ais_db.DATABASE)
    update_cache()

    pygame.init()
    pygame.key.set_repeat(KEYBOARD_DELAY)  # milliseconds
    screen = pygame.display.set_mode((VIEW_WIDTH, VIEW_HEIGHT), flags=pygame.HWSURFACE | pygame.SRCALPHA, depth=32)

    clock = pygame.time.Clock()
    ft_font = pygame.freetype.SysFont('Consolas', 14)
    pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN])

    # do_Test()    exit

    calc_visible()
    done = False
    while not done:
        # Process player inputs.
        handled = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:

                done = True               # raise SystemExit
            if event.type == pygame.KEYDOWN:
                mult = 5 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
                if event.key == pygame.K_ESCAPE:
                    done = True
                    # raise SystemExit
                elif event.key == pygame.K_LEFT:
                    my_xy[0] -= MOVE_DELTA*mult
                elif event.key == pygame.K_RIGHT:
                    my_xy[0] += MOVE_DELTA*mult
                elif event.key == pygame.K_UP:
                    my_xy[1] += MOVE_DELTA*mult
                elif event.key == pygame.K_DOWN:
                    my_xy[1] -= MOVE_DELTA*mult
                elif event.key == pygame.K_KP_MINUS:
                    if zoom_level > 0:
                        zoom_level -= 1
                elif event.key == pygame.K_KP_PLUS:
                    if zoom_level < (len(ZOOM_RANGE)-1):
                        zoom_level += 1
                elif event.key == pygame.K_PAGEDOWN:
                    my_angle -= ANGLE_DELTA*mult
                    if my_angle < 0.0:
                        my_angle += 360.0
                elif event.key == pygame.K_PAGEUP:
                    my_angle += ANGLE_DELTA*mult
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
            # logger.write_log(f'---------------- my_xy: {my_xy}, my_angle: {my_angle}, zoom_level: {zoom_level}')
            calc_visible()
        draw_screen()
        pygame.display.flip()  # Refresh on-screen display
        clock.tick(60)         # wait until next frame (at 60 FPS)
    pygame.quit()

except:
    print('-'*30)
    print('Error occured')
    print('-'*30)
    print(traceback.format_exc())
finally:
    # logger.logfile.close()
    conn.close()
