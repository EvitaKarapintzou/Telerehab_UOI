import time
import json
import numpy as np

from shared_variables import enableInterpolation, isFoundFirstTimestamp, firstTimestamp, imus, firstPacket, timeToCallMetrics, sensorDataToUpload, imu1Queue, imu2Queue, imu3Queue, imu4Queue, mqttState, enableMetrics, imu1FinalQueue, imu2FinalQueue, imu3FinalQueue, imu4FinalQueue, csv_file_path, imus, counter, startReceiving, lastDataTime, enableConnectionToAPI, feedbackData
#from get_online_metrics_ex_1_pr_1 import get_metrics
# from SittingMetrics.MaintainingFocus_HeadUpandDown import get_metrics
# from SittingMetrics.HeelRaises import get_metrics
# from SittingMetrics.MaintainingFocus_Headrotation import get_metrics
# from SittingMetrics.MaintainingFocus_Headrotation import getMetricsSittingOld01
# from SittingMetrics.ActiveTrunkRotation import get_metrics
# from SittingMetrics.ActiveTrunkRotation import getMetricsSittingOld03
# from SittingMetrics.TrunkRotation import get_metrics
# from GaitMetrics.WalkingHorizontalHeadTurns import get_metrics
# from SittingMetrics.ActiveTrunkRotation import getMetricsSittingOld03
# from SittingMetrics.TrunkRotation import get_metrics
# from SittingMetrics.Trunk_rotation import getMetricsSittingNew01
# from SittingMetrics.HeelRaises import get_metrics
# from SittingMetrics.AssistedToeRaises import get_metrics
# from SittingMetrics.SeatedMarchingSpot import get_metrics
# from SittingMetrics.SitToStand import get_metrics
# from SittingMetrics.SeatedMarchingSpot import getMetricsSittingNew04
# from SittingMetrics.MaintainingFocus_HeadUpandDown import getMetricsSittingOld02
#from getMetricsSittingOld02 import get_metrics
#from getMetricsSittingOld02 import getMetricsSitting01
# from GaitMetrics.WalkingHorizontalHeadTurns import getMetricsGaitNew02
# from GaitMetrics.WalkingHorizontalHeadTurns import get_metrics
#from GaitMetrics.SideStepping import get_metrics
# from StretchingMetrics.HipExternal import get_metrics
# from StretchingMetrics.LateralTrunkFlexion import get_metrics
from StretchingMetrics.Calf import get_metrics
# from StandingMetrics.MaintainBalance import get_metrics
# from StandingMetrics.BendingOver import get_metrics
#from StandingMetrics.SwivelTurning import get_metrics
#from StandingMetrics.LateralWeightShifts import get_metrics
# from StandingMetrics.AnteroposteriorDirection import get_metrics
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
    global isFoundFirstTimestamp, enableInterpolation

    imu1List = []
    imu2List = []
    imu3List = []
    imu4List = []
    while(True):
        while(not q.empty()):
            A = q.get()
            parts = A.split(",")
            if enableInterpolation == False:
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
              if '"' in name[len(name) - 1]:
                  name[len(name) - 1] = name[len(name) - 1].replace('"', '')
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
            if enableInterpolation == True:
                imu1List, imu2List, imu3List, imu4List = interpolationManager(imu1List, imu2List, imu3List, imu4List)       
                isFoundFirstTimestamp.value = False 
            if(len(imu1List) > 0 or len(imu2List) > 0 or len(imu3List) > 0 or len(imu4List) > 0):
                write_in_files(imu1List, imu2List, imu3List, imu4List)                   
            if(not scheduleQueue.empty()):
                get_data_tranch(imu1Queue,imu2Queue,imu3Queue,imu4Queue, counter)
                scheduleQueue.get()

def interpolationManager(imu1List, imu2List, imu3List, imu4List):
    global firstTimestamp, isFoundFirstTimestamp
    interpolatedListImu1 = []
    interpolatedListImu2 = []
    interpolatedListImu3 = []
    interpolatedListImu4 = []
    needListClear = False

    needListClear, interpolatedListImu1 = interpolationPerList(imu1List)
    if needListClear:
        imu1List.clear()
        needListClear = False
    needListClear, interpolatedListImu2 = interpolationPerList(imu2List)
    if needListClear:
        imu2List.clear()
        needListClear = False
    needListClear, interpolatedListImu3 = interpolationPerList(imu3List)
    if needListClear:
        imu3List.clear()
        needListClear = False
    needListClear, interpolatedListImu4 = interpolationPerList(imu4List)
    if needListClear:
        imu4List.clear()
        needListClear = False
    return interpolatedListImu1, interpolatedListImu2, interpolatedListImu3, interpolatedListImu4

def interpolationPerList(array):
    needClearList = False
    interpolatedList = []

    for item in array:
        splittedItem = item[2:-1]
        if ',' in splittedItem:
            splittedItem = splittedItem.split(',')
        else:
            splittedItem = splittedItem.split(' ')
        if "number" not in splittedItem:
            if(isFoundFirstTimestamp.value == False):
               isFoundFirstTimestamp.value = True
               firstTimestamp.value = int(splittedItem[2])
            if(len(array) < 100):
                numOfColOfList = len(splittedItem)
                if(numOfColOfList == 9): #quat
                    interpolatedList = interpolationEngine(array, "quaternion")
                elif(numOfColOfList == 8): #linear
                    interpolatedList = interpolationEngine(array, "linear")
            needClearList = True, array

    return needClearList, interpolatedList
        
def interpolationEngine(array, format):
    finalImu1ListX = []
    finalImu1ListY = []
    finalImu1ListZ = []
    finalImu1ListW = []
    finalImuTimestamp = []
    iteratorForQuaternionOrLinear = 0   # 0 for quaternion, 1 for linear

    if format == 'quaternion':
        iteratorForQuaternionOrLinear = 0
    elif format == 'linear':
        iteratorForQuaternionOrLinear = 1

    for i in array:
        splittedItem = i[2:-1]
        if ',' in splittedItem:
            splittedItem = splittedItem.split(',')
        else:
            splittedItem = splittedItem.split(' ')
        if iteratorForQuaternionOrLinear == 0:    
            splittedItem[8].replace('"', '')
            if '"' in splittedItem[8]:
                splittedItem[8] = splittedItem[8][:-1]
        if iteratorForQuaternionOrLinear == 1:    
            splittedItem[7].replace('"', '')
            if '"' in splittedItem[7]:
                splittedItem[7] = splittedItem[7][:-1]
        if iteratorForQuaternionOrLinear == 0:
            finalImu1ListW.append(float(splittedItem[5])) 
        finalImu1ListX.append(float(splittedItem[6 - iteratorForQuaternionOrLinear]))
        finalImu1ListY.append(float(splittedItem[7 - iteratorForQuaternionOrLinear]))
        finalImu1ListZ.append(float(splittedItem[8 - iteratorForQuaternionOrLinear]))    
        finalImuTimestamp.append(int(splittedItem[2]))      

    interpolatedValuesTimestamp = interAlgorithm(finalImuTimestamp)
    interpolatedValuesX = interAlgorithm(finalImu1ListX)
    interpolatedValuesY = interAlgorithm(finalImu1ListY)
    interpolatedValuesZ = interAlgorithm(finalImu1ListZ)
    interpolatedValuesW = []
    if iteratorForQuaternionOrLinear == 0:
        interpolatedValuesW = interAlgorithm(finalImu1ListW)
    finalFullList = []
    if iteratorForQuaternionOrLinear == 0:
        finalFullList = [[splittedItem[0], splittedItem[1], int(timestamp), None, None, w, x, y, z] for timestamp, w, x, y, z in zip(interpolatedValuesTimestamp, interpolatedValuesW, interpolatedValuesX, interpolatedValuesY, interpolatedValuesZ)]
        finalFullList = [' '.join(map(str, item)) for item in finalFullList]
    elif iteratorForQuaternionOrLinear == 1:    
        finalFullList = [[splittedItem[0], splittedItem[1], int(timestamp), None, None, x, y, z] for timestamp, x, y, z in zip(interpolatedValuesTimestamp, interpolatedValuesX, interpolatedValuesY, interpolatedValuesZ)]
        finalFullList = [' '.join(map(str, item)) for item in finalFullList]
    return finalFullList
    
def interAlgorithm(array):
    original_length = len(array)
    original_indices = np.linspace(0, original_length - 1, original_length)
    interpolated_indices = np.linspace(0, original_length - 1, 100)
    interpolated_values = np.interp(interpolated_indices, original_indices, array)
    return interpolated_values
    
def condition_checker():
    global write_to_files, lastDataTime, firstPacket, startReceiving, mqttState, feedbackData

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