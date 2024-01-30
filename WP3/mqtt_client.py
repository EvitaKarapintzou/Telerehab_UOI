import paho.mqtt.client as mqtt
import multiprocessing as mp
from multiprocessing import Process, Manager, Value
import time
from get_online_metrics_ex_1_pr_1 import get_metrics
import csv
from datetime import datetime
import os
import time
import threading

MQTT_BROKER_HOST = '192.168.0.231'
MQTT_BROKER_PORT = 1883
MQTT_KEEP_ALIVE_INTERVAL = 60
counter = 0
queueData=mp.Queue();
imu1Queue = mp.Queue();
imu2Queue = mp.Queue();
imu3Queue = mp.Queue();
imu4Queue = mp.Queue();
scheduleQueue = mp.Queue();
imus = []

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("location/123")

def on_message(client, userdata, msg):
    global counter
    counter = counter + 1
    #print("Message Recieved. ", msg.payload.decode(), " ", counter)
    queueData.put(msg.payload.decode())

def read_configure_file():
    global imus
    with open('configure.txt', 'r') as file:
        content = file.read()
        lines = content.splitlines()
        for line in lines:
            parts = line.split()
            if(parts[0] == 'IMU'):
                imus = parts[1:] 

def get_data_tranch(q1,q2,q3,q4):
    global imu1Listt, imu2Listt, imu3Listt, imu4Listt
    imu1List = []
    imu2List = []
    imu3List = []
    imu4List = []

    while(not q1.empty()):
        item = q1.get()
        imu1List.append(item)

    while(not q2.empty()):
        item = q2.get()
        imu2List.append(item)

    while(not q3.empty()):
        item = q3.get()
        imu3List.append(item)
    
    while(not q4.empty()):
        item = q4.get()
        imu4List.append(item)
  
    get_metrics(imu1List,imu2List,imu3List,imu4List)

def scheduler(scheduleQueue):
	while(True):
		time.sleep(0.5)
		scheduleQueue.put("GO");
	
def receive_imu_data(q,scheduleQueue):
    while(True):
            
        while(not q.empty()):
            A = q.get()
            parts = A.split(",")
            
            for item in parts:
              name = item.split()
              if(name[1] == str(imus[0])):
                  imu1Queue.put(item)
              elif(name[1] == str(imus[1])):
                  imu2Queue.put(item)
              elif(name[1] == str(imus[2])):
                  imu3Queue.put(item)
              elif(name[1] == str(imus[3])):
                  imu4Queue.put(item)

            if(not scheduleQueue.empty()):
                get_data_tranch(imu1Queue,imu2Queue,imu3Queue,imu4Queue)
                scheduleQueue.get()

read_configure_file()

mbB = mp.Process(target=receive_imu_data,args=(queueData,scheduleQueue,));
mbB.start();
mbB1 = mp.Process(target=scheduler,args=(scheduleQueue,));
mbB1.start();

client = mqtt.Client()
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL)
client.on_connect = on_connect
client.on_message = on_message

client.loop_forever()
