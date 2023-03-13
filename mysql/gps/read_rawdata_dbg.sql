SELECT `id`,
    `data`
FROM `rawdata`
where `id` > %s
-- and (`data` like '%gsa%'
-- or `data` like '%gga%')
ORDER BY `id` asc
-- limit 125,1111
;