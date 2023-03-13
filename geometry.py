import math

X, Y = 0, 1
MINX, MINY, MAXX, MAXY = 0, 1, 2, 3

RECT_NOT_INTERSECT = -1
RECT_INCLUDE = 0
RECT_INTERSECT = 1


def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def check_rect_intersect(rect0, rect1):
    return ((rect0[0] <= rect1[2]) and (rect0[2] >= rect1[0]) and (rect0[3] >= rect1[1]) and (rect0[1] <= rect1[3]))


def rect_intersect(main_rect, test_rec):
    if main_rect[MAXX] >= test_rec[MAXX] and main_rect[MINX] <= test_rec[MINX] and main_rect[MAXY] >= test_rec[MAXY] and main_rect[MINY] <= test_rec[MINY]:
        return RECT_INCLUDE
    elif not (main_rect[MAXX] <= test_rec[MINX] or main_rect[MINX] >= test_rec[MAXX] or main_rect[MINY] >= test_rec[MAXY] or main_rect[MAXY] <= test_rec[MINY]):
        return RECT_INTERSECT
    else:
        return RECT_NOT_INTERSECT


def ptinrect(pt, rect):
    return ((pt[0] >= rect[0]) and (pt[0] <= rect[2]) and (pt[1] >= rect[1]) and (pt[1] <= rect[3]))


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


# def line_intersect(p1, p2, p3, p4):
#     dx1, dy1 = p2[0]-p1[0], p2[1]-p1[1]
#     dx2, dy2 = p4[0]-p3[0], p4[1]-p3[1]
#     z = dy2 * dx1 - dx2 * dy1
#     if z != 0:
#         dxx, dyy = p1[0]-p3[0], p1[1]-p3[1]
#         ua = (dx2 * dyy - dy2 * dxx)/z
#         ub = (dx1 * dyy - dy1 * dxx)/z
#         x = p1[0] + ua*dx1
#         y = p1[1] + ua*dx2
#         return (x, y)

DETM = 0.0
DETP = 1.0


def line_intersect(p1, p2, p3, p4):
    dx1, dy1 = p2[0]-p1[0], p2[1]-p1[1]
    dx2, dy2 = p4[0]-p3[0], p4[1]-p3[1]
    z = dy2 * dx1 - dx2 * dy1
    if math.isclose(z, 0.0,  rel_tol=1e-09, abs_tol=0.0):
        return ()
    dxx, dyy = p1[0]-p3[0], p1[1]-p3[1]
    ua = (dx2 * dyy - dy2 * dxx)/z
    if ua < DETM or ua > DETP:
        return ()
    ub = (dx1 * dyy - dy1 * dxx)/z
    if ub < DETM or ub > DETP:
        return ()
    print (ua,ub)
    return (p1[0] + ua*dx1, p1[1] + ua*dy1)


def partition(a, low, high):
    pivot = a[high]
    i = low-1
    for j in range(low, high):
        if a[j] < pivot:
            i += 1
            a[i], a[j] = a[j], a[i]
    a[i + 1], a[high] = a[high], a[i + 1]
    return (i + 1)


def quickSort(a, low, high):
    if low < high:
        pi = partition(a, low, high)
        quickSort(a, low, pi - 1)
        quickSort(a, pi + 1, high)


def remove_duplicates(a):
    # check for closest points (i.e. values like -23.999999999999996, -23.999999999999993 => counts as one value)
    ra = []
    src_ptr, src_len = 0, len(a)
    while src_ptr < src_len:
        if src_ptr == 0:
            ra.append(a[src_ptr])
        else:
            if not math.isclose(a[src_ptr], ra[-1]):
                ra.append(a[src_ptr])
        src_ptr += 1
    return ra



# for dx in range(1, 6):
#     p1 = (1, 2)
#     p2 = (5, 2)
#     p3 = (1, 0)
#     p4 = (dx, 4)
#     r = line_intersect(p1, p2, p3, p4)
#     print(p4,r)
