import math


def line_intersect(p1, p2, p3, p4):
    pass


def rect_intersect(rect0, rect1):
    return ((rect0[0] < rect1[2]) and (rect0[2] > rect1[0]) and (rect0[3] > rect1[1]) and (rect0[1] < rect1[3]))


def decart2polar(pt):
    if pt[0] == 0:
        if pt[1] < 0:
            a = 270.0
        else:
            a = 90.0
    else:
        a = math.atan(pt[1]/pt[0])/math.pi*180
        if pt[0] < 0:
            a += 180.0
        elif pt[1] < 0:
            a += 360.0
    d = math.sqrt(pt[0]**2 + pt[1]**2)
    return [a, d]


def polar2decart(pt):
    a = pt[0]*math.pi/180
    # !! transform to radians
    return [pt[1]*math.cos(a), pt[1]*math.sin(a)]


# for y in range(-3, 4):
#     for x in range(-3, 4):
#         ad = decart2polar((x, y))
#         print(f'{x},{y},{ad[0]},{ad[1]}')
