import multiprocessing as mp
import paho.mqtt.client as mqtt
import time, re
import logging
from data_management_v02  import scheduler, receive_imu_data, condition_checker
from api_management import login, get_device_api_key
from configure_file_management import read_configure_file
from shared_variables import queueData, scheduleQueue, imus, enableConnectionToAPI, MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL
from shared_variables import counter, startReceiving, lastDataTime, mqttState
import multiprocessing as mp
from websocketServer import run_websocket_server
import csv
import psutil



from sensor_data import SensorData
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='app.log', filemode='w')

def save_to_csv(data):
    with open('sensor_data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([data.device_mac_address, data.timestamp, data.w, data.x, data.y, data.z])

# Define appStatus as a shared string (character array)
appStatus = mp.Array('c', b'down')
startExercise = mp.Array('c', b'false')
finishExercise = mp.Array('c', b'false')

import threading


config_message_01 = "[DA:C1:9F:1B:6E:40, Quaternion], [ED:B1:65:CE:EF:D4, OFF], [EF:0F:A9:3D:48:AA, OFF], [EB:0B:A9:F4:5E:4E, OFF], [sitting_01]"
config_message_02 = "[DA:C1:9F:1B:6E:40, Quaternion], [ED:B1:65:CE:EF:D4, OFF], [EF:0F:A9:3D:48:AA, OFF], [EB:0B:A9:F4:5E:4E, OFF], [sitting_02]"


read_configure_file()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("location/123")
    client.subscribe("IMUsettings")
    client.subscribe("IMUdata")

def on_message(client, userdata, msg):
    global mqttState 
    startReceiving.value = True   
    lastDataTime.value = time.time()
    
    logging.info(f"Message Received -> {msg.payload.decode()}")

    if 'start' in msg.payload.decode():
        new_value = "R"
        mqttState.value = new_value.encode()  
        print("\033[1m\033[93mExercise started!\033[0m")
        startExercise.value = b'e01';
        print('I got START');
    
    elif 'done' in msg.payload.decode():
        print("\033[1m\033[93mI got done from mobile app\033[0m")
        with finishExercise.get_lock(): 
            finishExercise.value = b'true'
        
    elif 'stop' in msg.payload.decode():
        new_value = "S"
        mqttState.value = new_value.encode()  
        print("\033[1m\033[93mExercise finished!\033[0m") 
    elif 'up' in msg.payload.decode():
        with appStatus.get_lock():  # Synchronize access
            appStatus.value = b'up'
        with finishExercise.get_lock(): 
            finishExercise.value = b'false'
        print('I got UP');
    elif 'myIMUsettings' in msg.payload.decode():
        print();
    elif 'Quaternion' in msg.payload.decode():
        print(msg.payload.decode())
    elif 'Linear' in msg.payload.decode():
        print(msg.payload.decode())
    else:
        data = SensorData.from_json(msg.payload.decode())
        #print("Message Received-> ", data)
        queueData.put(data)
        save_to_csv(data)
    


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL)

# Start the loop in a separate thread
#client.loop_start()

client.loop_forever()


