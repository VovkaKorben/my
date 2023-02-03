import sqlite3
import io
import traceback
import os
import time


DATABASE = 'C:\\ais\\ais.db'
SAMPLE_DATA = 'C:\\ais\\example\\nmea_sample1.txt'
SQL_PATH = 'C:\\ais\\my\\sql'
MAX_BULK = 100


def read_query(sqlfilename):
    try:
        sqlfilepath = os.path.join(SQL_PATH, sqlfilename)
        if not os.path.isfile(sqlfilepath):
            raise Exception(f'No SQL file: {sqlfilename}')
        sqlfile = io.open(sqlfilepath, mode='r', encoding='utf-8')
        return sqlfile.read()
    finally:
        sqlfile.close()


def exec_sql(sqlfilename=None, sqlstring=None, script=False, params=[]):  # for select sql
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


def check_params(params, forced):
    if len(params) >= MAX_BULK or forced:
        exec_sql(sqlstring=cached_query, params=params)
        return True
    return False


try:
    conn = sqlite3.connect(DATABASE)
    exec_sql(sqlfilename='make_rawdata_table.sql', script=True)
    samples = io.open(SAMPLE_DATA, mode='r', encoding='utf-8')
    cached_query = read_query('insert_rawdata.sql')
    params = []

    while True:
        data = samples.readline()
        if not data:
            break

        data = data.strip()
        if len(data) > 0:
            params.append({
                'data': data,
                'tm': time.time_ns()//1000000
            })
        if check_params(params, forced=False):
            params = []

    check_params(params, forced=True)

except:
    print('Error occured')
    print('-'*80)
    print(traceback.format_exc())
finally:
    samples.close()
    conn.close()
