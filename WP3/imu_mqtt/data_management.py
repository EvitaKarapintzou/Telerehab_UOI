import time
import json

from shared_variables import imus, firstPacket, timeToCallMetrics, sensorDataToUpload, imu1Queue, imu2Queue, imu3Queue, imu4Queue, mqttState, enableMetrics, imu1FinalQueue, imu2FinalQueue, imu3FinalQueue, imu4FinalQueue, csv_file_path, imus, counter, startReceiving, lastDataTime, enableConnectionToAPI
#from get_online_metrics_ex_1_pr_1 import get_metrics
from getMetricsSittingOld02 import get_metrics
from getMetricsSittingOld02 import getMetricsSitting01
from csv_management import write_in_files
from api_management import upload_sensor_data

def get_data_tranch(q1,q2,q3,q4,counter):
    global imu1Listt, imu2Listt, imu3Listt, imu4Listt
    imu1List = []
    imu2List = []
    imu3List = []
    imu4List = []

    while(not q1.empty()):
        item = q1.get()
        if 'time' not in item:
            item = item.replace("[", "")
            item = item.replace("]", "")
            item = item.strip()
            imu1List.append(item)
            imu1FinalQueue.put(item)

    while(not q2.empty()):
        item = q2.get()
        if 'time' not in item:
            item = item.replace("[", "")
            item = item.replace("]", "")
            item = item.strip()
            imu2List.append(item)
            imu2FinalQueue.put(item)

    while(not q3.empty()):
        item = q3.get()
        if 'time' not in item:
            item = item.replace("[", "")
            item = item.replace("]", "")
            item = item.strip()
            imu3List.append(item)
            imu3FinalQueue.put(item)
    
    while(not q4.empty()):
        item = q4.get()
        if 'time' not in item:
            item = item.replace("[", "")
            item = item.replace("]", "")
            item = item.strip()
            imu4List.append(item)
            imu4FinalQueue.put(item)
  
    if enableMetrics:
        returnedJson = get_metrics(imu1List, imu2List, imu3List, imu4List, counter)
        print(returnedJson)

def scheduler(scheduleQueue):
	while(True):
		time.sleep(timeToCallMetrics)
		scheduleQueue.put("GO");
	
def receive_imu_data(q,scheduleQueue):
    while(True):
        imu1List = []
        imu2List = []
        imu3List = []
        imu4List = []
        while(not q.empty()):
            A = q.get()
            parts = A.split(",")
            imu1List.clear()
            imu2List.clear()
            imu3List.clear()
            imu4List.clear()
            for item in parts:
              if '[' or '"' in item:
                  item = item[1:]
              elif ']' or '"' in item:
                  item = item[:len(item)-1]
              name = item.split()
              if(len(name) > 1):
                if(name[1] == str(imus[0])):
                    imu1Queue.put(item)
                    imu1List.append(item)
                elif(name[1] == str(imus[1])):
                    imu2Queue.put(item)
                    imu2List.append(item)
                elif(name[1] == str(imus[2])):
                    imu3Queue.put(item)
                    imu3List.append(item)
                elif(name[1] == str(imus[3])):
                    imu4Queue.put(item)
                    imu4List.append(item)
            write_in_files(imu1List, imu2List, imu3List, imu4List)
                               
            if(not scheduleQueue.empty()):
                get_data_tranch(imu1Queue,imu2Queue,imu3Queue,imu4Queue, counter)
                scheduleQueue.get()

def condition_checker():
    global write_to_files, lastDataTime, firstPacket, startReceiving, mqttState

    while True:
        if (mqttState.value.decode() == "S" and startReceiving.value == True) or (time.time() - lastDataTime.value >= 60 and mqttState.value.decode() == "R" and startReceiving.value == True):
            write_to_files = True
            firstPacket.value = True
            print("Data has been saved!\n")
            startReceiving.value = False
            newValue = 'I'
            mqttState.value = newValue.encode() 
            if enableMetrics: 
                print("The overall metrics!")                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
                imu1AllData = []
                imu2AllData = []
                imu3AllData = []
                imu4AllData = []
                for i in range (len(csv_file_path)):
                    with open(csv_file_path[i], 'r') as csvfile:
                        next(csvfile)
                        
                        for line in csvfile:
                            row = line.strip()
                            if i == 0:
                                imu1AllData.append(row)
                            elif i == 1:
                                imu2AllData.append(row)
                            elif i == 2:
                                imu3AllData.append(row)
                            else:
                                imu4AllData.append(row)
                       
                feedbackData = get_metrics(imu1AllData, imu2AllData, imu3AllData, imu4AllData, counter)
                print(feedbackData)
            if(enableConnectionToAPI):
                sensorDataToUpload["data"] = json.dumps(feedbackData)
                upload_sensor_data()

            csv_file_path[:] = [] 
            time.sleep(60)
        time.sleep(1)  