select recid,
    type,
    name,
    minx,
    miny,
    maxx,
    maxy
from shapes
where %s < maxx
    and %s < maxy
    and %s > minx
    and %s > miny
order by recid;