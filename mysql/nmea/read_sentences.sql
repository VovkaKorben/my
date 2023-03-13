SELECT `id`,
    `pattern`,
    `grouped`,
    `description`
    FROM `sentences`
WHERE `handled` = 1
ORDER BY `id` ASC;