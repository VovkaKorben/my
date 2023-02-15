import sqlite3
import helpers
import traceback
import ais_db
import os
import pygame
import pygame.gfxdraw
import geometry
mypos = (20.293872151995963, 60.167428760910944)  # lon lat
my_xy = [0, 0]
my_angle = 0  # degrees

# shapes collector
SHAPES_UPDATE = 5*60*1000  # 5 min for update shapes
shapes_timer = 0
DATABASE = 'C:\\ais\\ais.db'


ZOOM_RANGE = (1, 50, 100, 250, 500, 1000, 2000, 3000, 5000)  # , 10000, 15000, 20000, 50000)
zoom_level = 0  # len(ZOOM_RANGE)-1

shapes = {}

SCRW, SCRH = 10, 9
VZOOM, VMARGIN = 50, 2
clYellow = (255, 255, 0)
clSemiYellow = (26, 26, 0, 200)
clBlack = (0, 0, 0)


def pt(x, y):
    x = (x+VMARGIN)*VZOOM
    y = SCRH - y
    y = (y+VMARGIN)*VZOOM
    return (x, y)


def transform_point(pt):
    xy = [pt[0]-my_xy[0], pt[1]-my_xy[1]]
    ad = geometry.decart2polar(xy)
    ad[0] -= my_angle
    ad[1] /= ZOOM_RANGE[zoom_level]
    xy = geometry.polar2decart(ad)
    return (xy[0]+my_xy[0], xy[1]+my_xy[1])


def garbage_shapes():  # remove old shapes
    pass


def load_shapes():
    max_distance = ZOOM_RANGE[len(ZOOM_RANGE)-1]
    params = {
        'minx': my_xy[0]-max_distance,
        'miny': my_xy[1]-max_distance,
        'maxx': my_xy[0]+max_distance,
        'maxy': my_xy[1]+max_distance,
    }

    c = conn.cursor()
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
                    'origin': {
                        'box': (data['minx'], data['miny'], data['maxx'], data['maxy']),
                        'path': {}
                    }
                }
                params.append(data['recid'])
            shapes[data['recid']]['last_access'] = helpers.utc_ms()

        if len(params) > 0:
            query = ais_db.sql['get_points'].format(seq=','.join(['?']*len(params)))
            c.execute(query, params)
            while True:
                data = c.fetchone()
                if data == None:
                    break
                if not (data['partid'] in shapes[data['recid']]['origin']['path']):
                    shapes[data['recid']]['origin']['path'][data['partid']] = []
                shapes[data['recid']]['origin']['path'][data['partid']].append((data['x'], data['y']))
    finally:
        c.close()


def update_cache():
    load_shapes()
    garbage_shapes()


def process_frame():
    pass
    # detect my position


def calc_visible():
    box_corners = ((0, 1), (0, 3), (2, 1), (2, 3))  # indexes
    draw_rec = []
    # VIEWBOX = (0, 0, SCRW*ZOOM_RANGE[zoom_level], SCRH*ZOOM_RANGE[zoom_level])
    VIEWBOX = (0, 0, SCRW, SCRH)
    # rotate box and get new bounds
    for recid in shapes:
        origin = shapes[recid]['origin']

        # calculate new transormed corners
        for corner in range(4):
            ix, iy = box_corners[corner][0], box_corners[corner][1]
            new_pt = transform_point((origin['box'][ix], origin['box'][iy]))
            if corner == 0:
                new_box = [new_pt[0], new_pt[1], new_pt[0], new_pt[1]]
            else:
                new_box[0] = min(new_box[0], new_pt[0])
                new_box[1] = min(new_box[1], new_pt[1])
                new_box[2] = max(new_box[2], new_pt[0])
                new_box[3] = max(new_box[3], new_pt[1])

        if not geometry.rect_intersect(new_box, VIEWBOX):
            continue

        work = shapes[recid]['work'] = {

            'path': {}
        }

        # calculate all shape rotation with update a bounds
        first = True
        for path in origin['path']:
            work['path'][path] = []
            for point in origin['path'][path]:
                new_pt = transform_point(point)
                work['path'][path].append(new_pt)

                if first:
                    first = False
                    new_box = []
                    new_box.extend(new_pt)
                    new_box.extend(new_pt)
                else:
                    new_box[0] = min(new_box[0], new_pt[0])
                    new_box[1] = min(new_box[1], new_pt[1])
                    new_box[2] = max(new_box[2], new_pt[0])
                    new_box[3] = max(new_box[3], new_pt[1])

        if geometry.rect_intersect(new_box, VIEWBOX):
            draw_rec.append(recid)


try:
    # init
    # SCRW, SCRH = 10, 9 VZOOM, VMARGIN = 20, 2
    ais_db.cache_queries()
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = ais_db.make_dicts
    conn.set_trace_callback(ais_db.sqlite_trace)
    # first load of shapes
    # my_xy = helpers.latlon2meter(mypos)
    my_xy = [5, 4.5]
    update_cache()

    calc_visible()

    # при трансформации разворота сразу считать новые

    # check for shape in bounds

    passed_shapes = []
    # for
    """
    pygame.init()
    window = pygame.display.set_mode(((SCRW+VMARGIN*2)*VZOOM, (SCRH+VMARGIN*2)*VZOOM))
    clock = pygame.time.Clock()

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
        window.fill(clBlack)

        # grid
        for x in range(SCRW+VMARGIN*2):
            pygame.draw.line(window, clSemiYellow,
                             (x*VZOOM, 0),
                             (x*VZOOM, (SCRH+VMARGIN*2)*VZOOM)
                             )
        for y in range(SCRW+VMARGIN*2):
            pygame.draw.line(window, clSemiYellow,
                             (0, y*VZOOM),
                             ((SCRW+VMARGIN*2)*VZOOM, y*VZOOM)
                             )
        pygame.draw.line(window, clYellow, pt(0, 0), pt(SCRW,0 ), width=3)
        pygame.draw.line(window, clYellow, pt(0, 0), pt(0, SCRH),width=3)
        pygame.draw.line(window, clYellow, pt(SCRW, 0), pt(SCRW, SCRH), width=3)
        pygame.draw.line(window, clYellow, pt(0, SCRH), pt(SCRW, SCRH), width=3)

     


        # pygame.draw.rect(window, clYellow, (VMARGIN*VZOOM, VMARGIN*VZOOM, 10, 10)),
        # process_frame()
        # Do logical updates here.
        # ...

        # Fill the display with a solid color

        # Render the graphics here.
        # ...

        pygame.display.flip()  # Refresh on-screen display
        clock.tick(60)         # wait until next frame (at 60 FPS)
    """

except:
    print('Error occured')
    print('-'*80)
    print(traceback.format_exc())
finally:
    conn.close()
