import RPi.GPIO as GPIO
import time
import os
# Setup the Shinyei input

channel = 11
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(channel, GPIO.IN)
GPIO.input(channel)
duration=0;
sampletime_ms = 3; 
lowpulseoccupancy = 0;
ratio = 0;
concentration = 0;

# Get the current time
starttime = time.time()
moment=time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())
path="Dustdata/"
if not os.path.exists(path):
 print("1")
 os.mkdir("Dustdata/")
os.chdir("Dustdata/")

file1 = open('output'+moment+'.log', 'a')

while True:   
   # Get the low pulse duration on the input signal
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
        file1.write("Time: "+ time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime()) +" Concentration: "+str(concentration)+"\n")
        print ("Concentration = {0} pcs/0.01cf".format(concentration))
        lowpulseoccupancy = 0
        starttime = time.time()
        time.sleep(30)
 finally:
   a=2
   

