import paho.mqtt.client as mqtt
import multiprocessing as mp
from multiprocessing import Process, Manager, Value
import time
from get_online_metrics_ex_1_pr_1 import get_metrics
import csv
from datetime import datetime
import os
import time

MQTT_BROKER_HOST = '195.130.118.252'
MQTT_BROKER_PORT = 1883
MQTT_KEEP_ALIVE_INTERVAL = 60
counter = 0
queueData=mp.Queue();
imu1Queue = mp.Queue();
imu2Queue = mp.Queue();
imu3Queue = mp.Queue();
imu4Queue = mp.Queue();
imu1FinalQueue = mp.Queue();
imu2FinalQueue = mp.Queue();
imu3FinalQueue = mp.Queue();
imu4FinalQueue = mp.Queue();
scheduleQueue = mp.Queue();
imus = []
firstPacket = mp.Value('b', True)
fileName = ""
lastDataTime = mp.Value('d',time.time())
startReceiving = mp.Value('b', False)
manager = mp.Manager()
csv_file_path = manager.list()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("location/123")

def on_message(client, userdata, msg):
    global counter, startReceiving, lastDataTime
    counter = counter + 1
    startReceiving.value = True   
    lastDataTime.value = time.time()
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
                

def get_data_tranch(q1,q2,q3,q4,):
    global imu1Listt, imu2Listt, imu3Listt, imu4Listt
    imu1List = []
    imu2List = []
    imu3List = []
    imu4List = []

    while(not q1.empty()):
        item = q1.get()
        item = item.replace("[", "")
        item = item.replace("]", "")
        item = item.strip()
        imu1List.append(item)
        imu1FinalQueue.put(item)

    while(not q2.empty()):
        item = q2.get()
        item = item.replace("[", "")
        item = item.replace("]", "")
        item = item.strip()
        imu2List.append(item)
        imu2FinalQueue.put(item)

    while(not q3.empty()):
        item = q3.get()
        item = item.replace("[", "")
        item = item.replace("]", "")
        item = item.strip()
        imu3List.append(item)
        imu3FinalQueue.put(item)
    
    while(not q4.empty()):
        item = q4.get()
        item = item.replace("[", "")
        item = item.replace("]", "")
        item = item.strip()
        imu4List.append(item)
        imu4FinalQueue.put(item)
  
    writeInFiles(imu1List, imu2List, imu3List, imu4List)
    get_metrics(imu1List, imu2List, imu3List, imu4List)

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
              if(len(name) > 0):
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

def create_csv_files(imus, csv_file_path):
    currentTime = datetime.now()
    currentTime = currentTime.strftime("%Y-%m-%d_%H:%M:%S")
    folderPath = f"results/{currentTime}" 

    for imu in range(len(imus)):
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)
        csv_file_path.append(f"{folderPath}/{imus[imu]}_{currentTime}.csv")
        headers = ["Device", "MAC", "Timestamp", "Time(03:00)", "Elapsed(s)", "W(number)", "X(number)", "Y (number)", "Z (number)"]
        with open(csv_file_path[imu], 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(headers)

def write_in_a_specific_file(deviceData, csv_file_path):
    global write_to_files, firstPacket
    device = ""

    if(len(deviceData) > 0):
        firstData = deviceData[0].split()
        device = firstData[1] 
    
    if (firstPacket.value == True):
        firstPacket.value = False
        create_csv_files(imus, csv_file_path)
     
    for allData in deviceData:
        device = csv_file_path[imus.index(allData.split()[1])]
        with open(device, 'a', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            allData = allData[1:len(allData)-1]
            csv_writer.writerow(allData.split())

def writeInFiles(imu1List, imu2List, imu3List, imu4List):
    write_in_a_specific_file(imu1List, csv_file_path)
    write_in_a_specific_file(imu2List, csv_file_path)
    write_in_a_specific_file(imu3List, csv_file_path)
    write_in_a_specific_file(imu4List, csv_file_path)

def condition_checker():
    global write_to_files, lastDataTime, firstPacket, startReceiving
    c = 0
    imu1List = []
    while True:
        if time.time() - lastDataTime.value >= 10 and startReceiving.value == True :
            print(scheduleQueue)
            write_to_files = True
            firstPacket.value = True
            print("Data has been saved!\n")
            startReceiving.value = False
            csv_file_path[:] = [] 
        time.sleep(1)  

read_configure_file()

mbB = mp.Process(target=receive_imu_data,args=(queueData,scheduleQueue,));
mbB.start();
mbB1 = mp.Process(target=scheduler,args=(scheduleQueue,));
mbB1.start();
condition_thread = mp.Process(target=condition_checker);
condition_thread.start()

client = mqtt.Client()
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL)
client.on_connect = on_connect
client.on_message = on_message

client.loop_forever()
