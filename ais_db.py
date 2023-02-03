import sqlite3
import os
import io
SQL_PATH = 'C:\\ais\\my\\sql'


def make_raw(cursor, row):
    return row[0]


def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value) for idx, value in enumerate(row))


def read_query(sqlfilename):

    sqlfilepath = os.path.join(SQL_PATH, sqlfilename)
    if not os.path.isfile(sqlfilepath):
        raise Exception(f'No SQL file: {sqlfilename}')
    try:
        sqlfile = io.open(sqlfilepath, mode='r', encoding='utf-8')
        return sqlfile.read()
    finally:
        sqlfile.close()


def exec_sql(conn, sqlfilename=None, sqlstring=None, script=False, params=[]):  # for select sql
    if not (sqlfilename is None):
        sqlstring = read_query(sqlfilename)
    elif sqlstring is None:
        raise Exception('You must specify query filename OR query string')
    c = conn.cursor()
    if script:
        c.executescript(sqlstring)
    else:
        c.executemany(sqlstring, params)
    conn.commit()


def sqlite_trace(value):
    return
    # print(value)
