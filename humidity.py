import Adafruit_DHT
import time           #package for getting time
import os             #package creating the directory and change to that directory
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
moment=time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())  #Get local time
path="HumidityData/"         #set directory path variable
if not os.path.exists(path): #check if this directory already exists or not
    os.mkdir("HumidityData/")   #If directory with specified name(HumidityData) not exisits,then will be creating the directory with that name.  
os.chdir("HumidityData/")    #move to the directory specified
file1 = open('output'+moment+'.log', 'a') #create a logfile and open that file

while True:
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if humidity is not None and temperature is not None:
        file1.write("Time: "+time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())+"Temperature "+str(temperature)+"  Humidity: "+str(humidity)+"\n")     #write data to the file opened
        print("Time: "+time.strftime("%Y-%b-%d__%H_%M_%S",time.localtime())+" Temp={0:0.1f}*C  Humidity={1:0.1f}%".format(temperature, humidity))
        
    else:
        print("Failed to retrieve data from humidity sensor")
        file1.close()        #close the file which is opened earlier
       
    time.sleep(30)    #time interval 





    
