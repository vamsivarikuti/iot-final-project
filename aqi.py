#!/usr/bin/python -u
# coding=utf-8
# "DATASHEET": http://cl.ly/ekot
# https://gist.github.com/kadamski/92653913a53baf9dd1a8
from __future__ import print_function
import serial, struct, sys, time, json, subprocess
import time
import os
import sqlite3
#from db_utils import db_connect

DEBUG = 0
CMD_MODE = 2
CMD_QUERY_DATA = 4
CMD_DEVICE_ID = 5
CMD_SLEEP = 6
CMD_FIRMWARE = 7
CMD_WORKING_PERIOD = 8
MODE_ACTIVE = 0
MODE_QUERY = 1
PERIOD_CONTINUOUS = 0
path_db = os.path.join(os.path.dirname(__file__),'database.sqlite3')
JSON_FILE = '/var/www/html/aqi.json'

MQTT_HOST = ''
MQTT_TOPIC = '/weather/particulatematter'

ser = serial.Serial()
ser.port = "/dev/ttyUSB0"
ser.baudrate = 9600

ser.open()
ser.flushInput()

byte, data = 0, ""

def dump(d, prefix=''):
    print(prefix + ' '.join(x.encode('hex') for x in d))

def construct_command(cmd, data=[]):
    assert len(data) <= 12
    data += [0,]*(12-len(data))
    checksum = (sum(data)+cmd-2)%256
    ret = "\xaa\xb4" + chr(cmd)
    ret += ''.join(chr(x) for x in data)
    ret += "\xff\xff" + chr(checksum) + "\xab"

    if DEBUG:
        dump(ret, '> ')
    return ret

def process_data(d):
    r = struct.unpack('<HHxxBB', d[2:])
    pm25 = r[0]/10.0
    pm10 = r[1]/10.0
    checksum = sum(ord(v) for v in d[2:8])%256
    return [pm25, pm10]
    #print("PM 2.5: {} μg/m^3  PM 10: {} μg/m^3 CRC={}".format(pm25, pm10, "OK" if (checksum==r[2] and r[3]==0xab) else "NOK"))

def process_version(d):
    r = struct.unpack('<BBBHBB', d[3:])
    checksum = sum(ord(v) for v in d[2:8])%256
    print("Y: {}, M: {}, D: {}, ID: {}, CRC={}".format(r[0], r[1], r[2], hex(r[3]), "OK" if (checksum==r[4] and r[5]==0xab) else "NOK"))

def read_response():
    byte = 0
    while byte != "\xaa":
        byte = ser.read(size=1)

    d = ser.read(size=9)

    if DEBUG:
        dump(d, '< ')
    return byte + d

def cmd_set_mode(mode=MODE_QUERY):
    ser.write(construct_command(CMD_MODE, [0x1, mode]))
    read_response()

def cmd_query_data():
    ser.write(construct_command(CMD_QUERY_DATA))
    d = read_response()
    values = []
    if d[1] == "\xc0":
        values = process_data(d)
    return values

def cmd_set_sleep(sleep):
    mode = 0 if sleep else 1
    ser.write(construct_command(CMD_SLEEP, [0x1, mode]))
    read_response()

def cmd_set_working_period(period):
    ser.write(construct_command(CMD_WORKING_PERIOD, [0x1, period]))
    read_response()

def cmd_firmware_ver():
    ser.write(construct_command(CMD_FIRMWARE))
    d = read_response()
    process_version(d)

def cmd_set_id(id):
    id_h = (id>>8) % 256
    id_l = id % 256
    ser.write(construct_command(CMD_DEVICE_ID, [0]*10+[id_l, id_h]))
    read_response()

def pub_mqtt(jsonrow):
    cmd = ['mosquitto_pub', '-h', MQTT_HOST, '-t', MQTT_TOPIC, '-s']
    print('Publishing using:', cmd)
    with subprocess.Popen(cmd, shell=False, bufsize=0, stdin=subprocess.PIPE).stdin as f:
        json.dump(jsonrow, f)


def db_connect(val=path_db):
    con = sqlite3.connect(val)
    return con

if __name__ == "__main__":
    con = db_connect()
    cur = con.cursor()
    query1 = "CREATE TABLE IF NOT EXISTS aqidata(pm1 real, pm2 real, time Date DEFAULT (datetime('now', 'localtime')) )"
    cur.execute(query1)
    query2 = "INSERT INTO aqidata (pm1,pm2) VALUES (?,?)"
    
    cmd_set_sleep(0)
    cmd_firmware_ver()
    cmd_set_working_period(PERIOD_CONTINUOUS)
    cmd_set_mode(MODE_QUERY); 
    moment=time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())
    #file1 = open('output'+moment+'.log', 'a')

    path="data/"
    if not os.path.exists(path):
      os.mkdir("data/")
     #os.makedirs("data/")
    os.chdir("data/")
    file1 = open('output'+moment+'.log', 'a')
    while True:
        cmd_set_sleep(0)
        
        pm25avg = 0
        pm10avg = 0
        takes = 0
        
        for t in range(15):
            values = cmd_query_data();
            if values is not None and len(values) == 2:
                pm25avg += values[0]
                pm10avg += values[1]
                takes += 1
        pm25avg /= takes
        pm10avg /= takes
        file1.write("Time: " + time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())+"PM2.5: "+str(pm25avg)+"  PM10: "+str(pm10avg)+"\n")
        print("Time: " + time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())+"PM2.5: ", pm25avg, ", PM10: ", pm10avg)
        cur.execute(query2,(pm25avg,pm10avg))
        time.sleep(2)#time duration................................................................................
        con.commit()
              
        # open stored data
        print("Going to sleep for 1 min...")
        #cmd_set_sleep(1)
        time.sleep(30)
    #con.commit()
    con.close()