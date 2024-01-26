import paho.mqtt.client as mqtt
import multiprocessing as mp
from multiprocessing import Process, Manager, Value
import time
from get_online_metrics_ex_1_pr_1 import get_metrics


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


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("location/123")

def on_message(client, userdata, msg):
    global counter
    counter = counter + 1
    #print("Message Recieved. ", msg.payload.decode(), " ", counter)
    queueData.put(msg.payload.decode())


def get_data_tranch(q1,q2,q3,q4):

    # tempQ1 = q1
    # tempQ2 = q2
    # tempQ3 = q3
    # tempQ4 = q4

    imu1List = []
    imu2List = []
    imu3List = []
    imu4List = []

    while(not q1.empty()):
        imu1List.append(q1.get())

    while(not q2.empty()):
        imu2List.append(q2.get())

    while(not q3.empty()):
        imu3List.append(q3.get())
    
    while(not q4.empty()):
        imu4List.append(q4.get())

    get_metrics(imu1List,imu2List,imu3List,imu4List)
    
    #while not imu1Queue.empty():
    #	imu1Queue.get()
    #while not imu2Queue.empty():
    #	imu2Queue.get()
    #while not imu3Queue.empty():
    #	imu3Queue.get()
    #while not imu4Queue.empty():
    #	imu4Queue.get()

def scheduler(scheduleQueue):
	#for i in range(80):
	while(True):
		time.sleep(0.5)
		scheduleQueue.put("GO");
	

def receive_imu_data(q,scheduleQueue):
    while(True):

		
        #while not imu1Queue.empty():
        #    imu1Queue.get()
        #while not imu2Queue.empty():
        #    imu2Queue.get()
        #while not imu3Queue.empty():
        #    imu3Queue.get()
        #while not imu4Queue.empty():
        #    imu4Queue.get()
            
        while(not q.empty()):
            A = q.get()
            parts = A.split(",")
            
            # imu1Queue.put("1")
            # imu2Queue.put("2")
            # imu3Queue.put("3")
            # imu4Queue.put("4")
            
            #while not q.empty():
            #	q.get()
            
            #print(A)
            
            for item in parts:
              name = item.split()
             # print(name[1])
              if(name[1] == "E15561CB9161"):
                  imu1Queue.put(item)
              elif(name[1] == "E25AD03D0194"):
                  imu2Queue.put(item)
              elif(name[1] == "C8925E7DC6BD"):
                  imu3Queue.put(item)
              elif(name[1] == "FEAC84C53DE7"):
                  imu4Queue.put(item)

            
                 
            #print(imu1Queue.qsize(), " ", imu2Queue.qsize(), " ", imu3Queue.qsize(), " ", imu4Queue.qsize())
            if(not scheduleQueue.empty()):
                get_data_tranch(imu1Queue,imu2Queue,imu3Queue,imu4Queue)
                
                scheduleQueue.get()

mbB = mp.Process(target=receive_imu_data,args=(queueData,scheduleQueue,));
mbB.start();
mbB1 = mp.Process(target=scheduler,args=(scheduleQueue,));
mbB1.start();

client = mqtt.Client()
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL)
client.on_connect = on_connect
client.on_message = on_message


client.loop_forever()
