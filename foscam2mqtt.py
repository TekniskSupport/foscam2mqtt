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

def publishMqtt(topic, state):
    client= paho.Client("foscam2mqtt-client")
    client.connect(conf["broker"])
    client.publish("foscam2mqtt/"+ topic,state)
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

            if (int(motion) == 2):
                print(timestamp() + " Changed value on " + name + " to ON")
                currentValues[name] = motion
                publishMqtt(name + '/motion', "ON")
                publishMqtt(name + "/motion/json", '{ "device": "'+ name +'", "eventType": "motion", "state": "true" }')
                publishMqtt(name + "/shinobi", '{ "plug": "'+ name +'", "reason": "motion", "name": "'+ name +'"}')
            elif (int(motion) == 1 and currentValue != motion): 
                print(timestamp() + " Changed value on " + name + " to OFF")
                currentValues[name] = motion
                publishMqtt(name + "/motion", "OFF")
                publishMqtt(name + "/motion/json", '{ "device": "'+ name +'", "eventType": "motion", "state": "false" }')
                publishMqtt(name + "/shinobi", '{ "plug": "'+ name +'", "reason": "motion", "name": "'+ name + '"}')
                
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

    time.sleep(.5)
