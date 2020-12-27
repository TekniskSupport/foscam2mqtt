import time, sys, os
from datetime import datetime
import paho.mqtt.client as paho
import json
from bs4 import BeautifulSoup
import requests

path = os.path.dirname(os.path.abspath(__file__))
with open(path +'/config.json') as f:
  conf = json.load(f)

def getMotionDetection(host, port, user, pwd):
    page   = requests.get('http://'+ host +':'+ port +
                          '/cgi-bin/CGIProxy.fcgi?cmd=getDevState&usr='+
                           user +'&pwd='+ pwd+'', timeout=3)
    soup   = BeautifulSoup(page.content, "html.parser")
    motion = soup.select("motiondetectalarm")[0].get_text()

    return motion

def publishMqtt(device, state):
    client= paho.Client("foscam2mqtt-client")
    client.connect(conf["broker"])
    client.publish("foscam2mqtt/"+ device +"/motion",state)
    client.disconnect()

def timestamp():
    my_date = datetime.now()

    return my_date.isoformat()

currentValues = {}
while True:
    for camera in conf["devices"]:
        try:
            name   = camera["name"]
            motion = getMotionDetection(
                camera["host"],
                camera["port"],
                camera["user"],
                camera["pwd"]
            )
            if name in currentValues:
                currentValue = currentValues[name]
            else:
                currentValue = "-1"
                print(timestamp() + " " + name + " initial state -1")

            if   (int(motion) == 2):
                currentValues[name] = motion
                print(timestamp() + " Changed value on " + name + " to ON")
                publishMqtt(name, '{ "plug": '+ name +', "reason": "motion", "name": '+ name +' }')
            elif (int(motion) == 1 and currentValue != motion):
                currentValues[name] = motion
                print(timestamp() + " Changed value on " + name + " to OFF")
                publishMqtt(name, "")
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.Timeout
        ):
               print (timestamp() + ' timeout on '+ name)
        except:
               e = sys.exc_info()[0]
               print (e)
               print (timestamp() + ' There was an exception on '+ name)

    time.sleep(.2)
