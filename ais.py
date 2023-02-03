import sqlite3
import io
import traceback
import os
import time
import ais_db
import nmea

DATABASE = 'C:\\ais\\ais.db'

last_msg_id = 0
read_sql = ais_db.read_query('read_rawdata.sql')

try:
    conn = sqlite3.connect(DATABASE)

    conn.set_trace_callback(ais_db.sqlite_trace)

    # read talkers
    conn.row_factory = ais_db.make_dicts
    c = conn.cursor()
    try:
        sql = ais_db.read_query('read_talkers.sql')
        c.execute(sql)
        while True:
            data = c.fetchone()
            if data == None:
                break
            talkerid = data['talkerid']
            data.pop('talkerid', None)
            nmea.talkers[talkerid] = data
    finally:
        c.close()

    # read sentences
    c = conn.cursor()
    try:
        sql = ais_db.read_query('read_sentences.sql')
        c.execute(sql)
        while True:
            data = c.fetchone()
            if data == None:
                break
            sentence = data['sentence']
            data.pop('sentence', None)
            nmea.sentences[sentence] = data
    finally:
        c.close()

    # parse data

    conn.row_factory = ais_db.make_raw
    c = conn.cursor()
    try:
        c.execute(read_sql, {'id': last_msg_id})
        while True:
            row = c.fetchone()
            if row == None:
                break
            nmea.parse_nmea(row)
    finally:
        c.close()
except:
    print('Error occured')
    print('-'*80)
    print(traceback.format_exc())
finally:

    conn.close()
