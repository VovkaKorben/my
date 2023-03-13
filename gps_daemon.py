import mysql.connector
from mysql.connector import Error
import socket
import ais_mysql
import helpers
import time
SEP, buff = b'\r\n', b''
start_pos,messages_count = 0,0


def socket_connect():
    global gps_socket
    connected = False
    HOST, PORT = "192.168.1.2", 50000
    while not connected:
        try:
            gps_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            gps_socket.connect((HOST, PORT))
            print(f"Connected to {HOST}:{PORT}")
            connected = True
        except:
            print(f"Can't connect to {HOST}:{PORT}")
            time.sleep(3)


def parse_data(recv_data):
    global buff, start_pos, messages_count
    ms = helpers.utc_ms()
    buff = buff + recv_data
    params = []
    while True:
        end_pos = buff.find(SEP, start_pos)
        if end_pos == -1:
            buff = buff[start_pos:]
            start_pos = 0
            break
        line = buff[start_pos:end_pos].decode(encoding="utf-8")
        params.append((line, ms))
        start_pos = end_pos+len(SEP)
        messages_count +=1
    mysql_cursor.executemany(sql, params)
    mysql_conn.commit()
    print(f'Messages: {messages_count}             \r', end = '')


try:
    mysql_conn = ais_mysql.connect_db(user='gpsdaemon', password='gpsdaemon')
    sql = ais_mysql.read_query('daemon\write_data.sql')
    mysql_cursor = mysql_conn.cursor()

    socket_connect()
    while True:
        recv = gps_socket.recv(512)
        if not recv:
            socket_connect()
        parse_data(recv)

except mysql.connector.Error as error:
    print("Failed to insert record into MySQL table {}".format(error))


finally:
    print('Done!')
    if mysql_conn.is_connected():
        mysql_cursor.close()
        mysql_conn.close()
        print("MySQL connection is closed")
