select *
from points
where recid in ({seq})
order by recid asc,
    partid asc,
    pointid asc;