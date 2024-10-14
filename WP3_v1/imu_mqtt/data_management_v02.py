import time
import json
import numpy as np
import re
from shared_variables import enableInterpolation, isFoundFirstTimestamp, firstTimestamp, imus, firstPacket, timeToCallMetrics, sensorDataToUpload, imu1Queue, imu2Queue, imu3Queue, imu4Queue, mqttState, enableMetrics, imu1FinalQueue, imu2FinalQueue, imu3FinalQueue, imu4FinalQueue, csv_file_path, imus, counter, startReceiving, lastDataTime, enableConnectionToAPI, feedbackData
#from get_online_metrics_ex_1_pr_1 import get_metrics
from SittingMetrics.MaintainingFocus_HeadUpandDown import get_metrics as get_metrics_MaintainingFocus_HeadUpandDown
#from SittingMetrics.HeelRaises import get_metrics
from SittingMetrics.MaintainingFocus_Headrotation import get_metrics as get_metrics_MaintainingFocus_Headrotation
# from SittingMetrics.MaintainingFocus_Headrotation import getMetricsSittingOld01
# from SittingMetrics.Trunk_rotation import get_metrics
# from SittingMetrics.Trunk_rotation import getMetricsSittingNew01
# from SittingMetrics.Assisted_toe_raises import get_metrics
# from SittingMetrics.Assisted_toe_raises import getMetricsSittingNew02
# from SittingMetrics.SeatedMarchingSpot import get_metrics
# from SittingMetrics.SeatedMarchingSpot import getMetricsSittingNew04
#from SittingMetrics.MaintainingFocus_HeadUpandDown import getMetricsSittingOld02
#from getMetricsSittingOld02 import get_metrics
#from getMetricsSittingOld02 import getMetricsSitting01
#from GaitMetrics.WalkingHorizontalHeadTurns import getMetricsGaitNew02
#from GaitMetrics.WalkingHorizontalHeadTurns import get_metrics
from csv_management import write_in_files
from api_management import upload_sensor_data, postExerciseScore
from sensor_data import SensorData
import multiprocessing as mp



def reformat_sensor_data(sensor_data_list):
    if not sensor_data_list:
        return []

    # Get the reference timestamp
    reference_timestamp = sensor_data_list[0].timestamp

    reformatted_data = []

    # Iterate through the sensor data list
    for data in sensor_data_list:
        timestamp = data.timestamp
        elapsed_time = timestamp - reference_timestamp
        reformatted_entry = [timestamp, elapsed_time, data.w, data.x, data.y, data.z]
        reformatted_data.append(reformatted_entry)

    return reformatted_data


def get_data_tranch(q1,q2,q3,q4, counter, exercise):
    #global imu1Listt, imu2Listt, imu3Listt, imu4Listt
    imu1List = []
    imu2List = []
    imu3List = []
    imu4List = []
    print('I am in the get_data_tranch')
    while(not q1.empty()):
        item = q1.get()
        #print('item = ', item)
        imu1List.append(item)
        #imu1FinalQueue.put(item)

    while(not q2.empty()):
        item = q2.get()
        #print('item = ', item)
        imu2List.append(item)
        #imu2FinalQueue.put(item)

    while(not q3.empty()):
        #print('item = ', item)
        item = q3.get()
        imu3List.append(item)
        #imu3FinalQueue.put(item)
    
    while(not q4.empty()):
        #print('item = ', item)
        item = q4.get()
        imu4List.append(item)
        #imu4FinalQueue.put(item)
  
    if enableMetrics:
        if (exercise == 'sitting_01'):
            returnedJson = get_metrics_MaintainingFocus_Headrotation(imu1List, imu2List, imu3List, imu4List, counter)
        elif (exercise == 'sitting_02'):
            returnedJson = get_metrics_MaintainingFocus_HeadUpandDown(imu1List, imu2List, imu3List, imu4List, counter)

    if (counter == 4):
        postExerciseScore(returnedJson, "1")
        #upload_sensor_data(returnedJson)
    print(returnedJson)

def scheduler(scheduleQueue):
	while(True):
		time.sleep(timeToCallMetrics)
		scheduleQueue.put("GO");

# Function to parse the configuration message
def parse_config_message(config_message):
    config_dict = {}
    
    # Split the message by commas to get each device configuration
    parts = config_message.split(',')
    
    # Loop through each part and further split by "=" and "-"
    for part in parts:
        if "=" in part and "-" in part:
            role, rest = part.split('=')
            mac_address, mode = rest.split('-')
            config_dict[role] = {"mac_address": mac_address, "mode": mode}
    
    # The last part is the exercise code
    exercise_code = parts[-1]
    
    return config_dict, exercise_code


def initialize_imu_data_structures(config_dict, manager):
    imu_data = {}

    # Iterate over the configuration to dynamically create lists and queues for each IMU category
    for role in config_dict.keys():
        imu_data[role] = {
            'list': manager.list(),  # List to store data for this IMU
            'queue': manager.Queue(),  # Queue for real-time data processing
            'final_queue': manager.Queue()  # Final queue for processed data
        }

    return imu_data


def receive_imu_data(q, scheduleQueue, config_message, exercise):

    # Initialize multiprocessing manager
    manager = mp.Manager()

    # Create the data structures with manager-based queues
    imu_data = initialize_imu_data_structures(config_message, manager)

    global isFoundFirstTimestamp, enableInterpolation
    # Sample configuration message
    imu_config, exercise_code = parse_config_message(config_message)
    jjj = 0;
    INTERVALS = 0;

    imu1List = []
    imu2List = []
    imu3List = []
    imu4List = []

    # Create a dictionary to map MAC addresses to lists and queues
    mac_to_resources = {}
    imu_resources = [
        (imu1List, imu1Queue, imu1FinalQueue),
        (imu2List, imu2Queue, imu2FinalQueue),
        (imu3List, imu3Queue, imu3FinalQueue),
        (imu4List, imu4Queue, imu4FinalQueue)
    ]

    # Assign the lists and queues to the MAC addresses based on the config message
    for idx, (mac, state) in enumerate(imu_config):
        if state == "Quaternion" or state == "Linear":
            mac_to_resources[mac] = imu_resources[idx]

    if exercise_code == 'exer01':
        while INTERVALS < 4 or not q.empty():
            data = q.get()  # Read data from the dataQueue

            if ":" in data:  # Check for valid sensor data format
                # Convert JSON data to SensorData object
                sensor_data = SensorData.from_json(data)

                # Use deviceMacAddress as the body part identifier
                body_part = sensor_data.deviceMacAddress

                # Fetch the relevant lists and queues from imu_data
                if body_part in imu_data:
                    imu_list, imu_queue, imu_finalqueue = imu_data[body_part]

                    # Add the sensor data to the appropriate structures
                    imu_list.append(sensor_data)
                    imu_queue.put(sensor_data)
                    imu_finalqueue.put(sensor_data)
                else:
                    print(f"Unrecognized body part: {body_part}")

                # Check if there is something in the schedule queue
                if not scheduleQueue.empty():
                    # Call the data processing function based on the queues
                    get_data_tranch(
                        imu_data['HEAD'][1],  # imu1Queue
                        imu_data['PELVIS'][1],  # imu2Queue
                        imu_data['LEFTFOOT'][1],  # imu3Queue
                        imu_data['RIGHTFOOT'][1],  # imu4Queue
                        counter,  # Pass the counter variable
                        exercise_code  # Pass the exercise code
                    )

                    scheduleQueue.get()  # Consume the scheduled task
                    INTERVALS += 1
                    print(f"Intervals = {INTERVALS}")

                    if INTERVALS == 4:
                        print("Processing the entire data stream...")
                        get_data_tranch(
                            imu_data['HEAD'][2],  # imu1FinalQueue
                            imu_data['PELVIS'][2],  # imu2FinalQueue
                            imu_data['LEFTFOOT'][2],  # imu3FinalQueue
                            imu_data['RIGHTFOOT'][2],  # imu4FinalQueue
                            INTERVALS,
                            exercise_code
                        )


    return 0;
            

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
    
def condition_checker(exercise):
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
                if (exercise == 'sitting_01'):
                    feedbackData = get_metrics_MaintainingFocus_Headrotation(imu1AllData, imu2AllData, imu3AllData, imu4AllData, counter);
                elif (exercise == 'sitting_02'):
                    feedbackData = get_metrics_MaintainingFocus_HeadUpandDown(imu1AllData, imu2AllData, imu3AllData, imu4AllData, counter);
                print(feedbackData)
            if(enableConnectionToAPI):
                sensorDataToUpload["data"] = json.dumps(feedbackData)

                #upload_sensor_data()

            csv_file_path[:] = [] 
            time.sleep(60)
        time.sleep(1)  