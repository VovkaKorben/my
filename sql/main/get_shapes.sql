select recid,
    type,
    name,
    minx,
    miny,
    maxx,
    maxy
from shapes
where :minx < maxx
    and :maxx > minx
    and :maxy > miny
    and :miny < maxy
order by recid