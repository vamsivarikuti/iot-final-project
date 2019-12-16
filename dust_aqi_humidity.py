#!/usr/bin/python -u
# coding=utf-8
# "DATASHEET": http://cl.ly/ekot
# https://gist.github.com/kadamski/92653913a53baf9dd1a8
from __future__ import print_function
import serial, struct, sys, time, json, subprocess
import time
import os
import sqlite3
import RPi.GPIO as GPIO
#from db_utils import db_connect

# star dustduino
channel = 11
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(channel, GPIO.IN)
GPIO.input(channel)
duration=0
sampletime_ms = 3 
lowpulseoccupancy = 0
ratio = 0
concentration = 0

# Get the current time
starttime = time.time()
moment=time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())
path="Dustdata/"
if not os.path.exists(path):
 print("1")
 os.mkdir("Dustdata/")

dust_file = open('Dustdata/output'+moment+'.log', 'a')



# For Humidity
import Adafruit_DHT
import time           #package for getting time
import os             #package creating the directory and change to that directory
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
moment=time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())  #Get local time
path="HumidityData/"         #set directory path variable
if not os.path.exists(path): #check if this directory already exists or not
    os.mkdir("HumidityData/")   #If directory with specified name(HumidityData) not exisits,then will be creating the directory with that name.  
#os.chdir("HumidityData/")    #move to the directory specified
humid_file = open('HumidityData/output'+moment+'.log', 'a') #create a logfile and open that file
#END For Humidity

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
path_db = os.path.join(os.path.dirname(__file__),'adatabase.sqlite3')
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
    query1 = "CREATE TABLE IF NOT EXISTS aqi(pm1 real, pm2 real, humidity real, temperature real, concentration real, time Date DEFAULT (datetime('now', 'localtime')) )"
    try:
        cur.execute(query1)
    except:
        "Failed to create Table"
    query2 = "INSERT INTO aqi (pm1,pm2,humidity,temperature, concentration) VALUES (?,?,?,?,?)"
    
    cmd_set_sleep(0)
    cmd_firmware_ver()
    cmd_set_working_period(PERIOD_CONTINUOUS)
    cmd_set_mode(MODE_QUERY)
    moment=time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())
    #file1 = open('output'+moment+'.log', 'a')

    path="data/"
    if not os.path.exists(path):
      os.mkdir("data/")
     #os.makedirs("data/")
    #os.chdir("data/")
    file1 = open('data/output'+moment+'.log', 'a')
    while True:
        cmd_set_sleep(0)
        
        pm25avg = 0
        pm10avg = 0
        takes = 0
        concentration = 0
        
        try:
           GPIO.wait_for_edge(channel, GPIO.FALLING)
           #print("hi1")
           tstart = time.time()
           GPIO.wait_for_edge(channel, GPIO.RISING)
           tend = time.time()
           duration = tend - tstart 
           #print("hi2")
           lowpulseoccupancy += duration
           #print(time.time())
           #print(starttime)
           #print(time.time() - starttime)
           if ((time.time() - starttime) > sampletime_ms):
                #print("hi3")
                ratio = lowpulseoccupancy/(sampletime_ms*10.0)
                concentration = 1.1*pow(ratio,3)-3.8*pow(ratio,2)+520*ratio+0.62
                dust_file.write("Time: "+ time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime()) +" Concentration: "+str(concentration)+"\n")
                print ("Concentration = {0} pcs/0.01cf".format(concentration))
                lowpulseoccupancy = 0
                starttime = time.time()
        except:
            print("failed to get dust sensor")
       
        for t in range(5):
            values = cmd_query_data();
            if values is not None and len(values) == 2:
                pm25avg += values[0]
                pm10avg += values[1]
                takes += 1
                time.sleep(1)#time duration................................................................................
            
        pm25avg /= takes
        pm10avg /= takes
        pm25avg = round(pm25avg, 2)
        pm10avg = round(pm10avg, 2)
        concentration = round(concentration, 2)
        
        file1.write("Time: " + time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())+" PM2.5: "+str(pm25avg)+"  PM10: "+str(pm10avg)+"\n")
        print("Time: " + time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())+" PM2.5: ", pm25avg, ", PM10: ", pm10avg)
        
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
        humidity = round(humidity, 2)
        temperature = round(temperature, 2)
        
        if humidity is not None and temperature is not None:
            humid_file.write("Time: "+time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())+"Temperature "+str(temperature)+"  Humidity: "+str(humidity)+"\n")     #write data to the file opened
            print("Time: "+time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())+" Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))
        else:
            print("Failed to retrieve data from humidity sensor")
            
        try:            
            cur.execute(query2,(pm25avg,pm10avg, humidity, temperature, concentration))
            time.sleep(1)
            con.commit()
        except:
            print("Failed to insert")
            
            
        
        # open stored data
        print("Going to sleep for 1 min...")
        #cmd_set_sleep(1)
        time.sleep(30)
    #con.commit()
    con.close()
    humid_file.close()        #close the file which is opened earlier
    file1.close()
    dust_file.close()


            


            
