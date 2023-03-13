import os
import io
import mysql.connector
from mysql.connector import Error
import pymysql.cursors
SQL_PATH = 'C:\\ais\\my\\mysql'
DATABASE = 'ais'
HOST = 'localhost'


def connect_db(user, password):
    try:
        connection = mysql.connector.connect(
            host=HOST,
            database=DATABASE,
            user=user,
            password=password,
            # buffered=True
        )
        if connection.is_connected():
            db_Info = connection.get_server_info()
            print("Connected to MySQL Server version ", db_Info)
            cursor = connection.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            print("You're connected to database: ", record)
            return connection
    except Error as e:
        print("Error while connecting to MySQL", e)
    finally:
        if connection.is_connected():
            cursor.close()


def cache_queries():
    global cached_query_string
    cached_query_string = {'get_shapes': 'get_shapes.sql',
                           'get_points': 'get_points.sql',
                           }
    for qn in cached_query_string:
        filename = cached_query_string[qn]
        sqlfilepath = os.path.join(SQL_PATH, 'geo', filename)

        # flatten query
        s = read_query(sqlfilepath)
        for r in ['\n', '\t', '  ']:
            while True:
                p = s.find(r)
                if p == -1:
                    break
                s = s[:p] + ' ' + s[p+len(r):]

        cached_query_string[qn] = s
        # cached_query_string[s] = cached_query_string[s].replace('\t', ' ')
        # print(cached_query_string[s])


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
