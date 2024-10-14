import logging
import sys
import os

# Set up logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(message)s')

# Create file handler to log to a file
file_handler = logging.FileHandler('app.log', mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Create console handler to log to the command line
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Suppress debug logging for matplotlib
logging.getLogger('matplotlib').setLevel(logging.WARNING)

# Redirect stdout and stderr to logger
class StreamToLogger:
    def __init__(self, log_level):
        self.log_level = log_level
        self.line_buffer = ''

    def write(self, message):
        if message.strip():
            self.log_level(message.strip())

    def flush(self):
        pass

# Redirect stdout and stderr to the logger
sys.stdout = StreamToLogger(logger.info)  # Redirect stdout to logger.info
sys.stderr = StreamToLogger(logger.error)  # Redirect stderr to logger.error

import multiprocessing as mp
import paho.mqtt.client as mqtt
import time, re
import logging
from data_management_v03  import scheduler, receive_imu_data
from api_management import login, get_device_api_key
from configure_file_management import read_configure_file
from shared_variables import queueData, scheduleQueue, imus, enableConnectionToAPI, MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL
from shared_variables import counter, startReceiving, lastDataTime, mqttState
import multiprocessing as mp
from websocketServer import run_websocket_server
import csv
import psutil
from UDPSERVER import start_multicast_server
from sensor_data import SensorData

import requests
import configparser



logging.info('This is a test log entry.')


# Function to get daily schedule
def get_daily_schedule():
    # Load API key from config file
    config = configparser.ConfigParser()
    config.read('/home/uoi/Documents/GitHub/Telerehab_UOI/WP3_v1/imu_mqtt/config.ini')
    api_key_edge = config['API'].get('key_edge', '')

    # Define the API endpoint
    daily_schedule_url = 'https://telerehab-develop.biomed.ntua.gr/api/PatientSchedule/daily'

    headers = {
        'accept': '*/*',
        'Authorization': api_key_edge
    }
    response = requests.get(daily_schedule_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def save_to_csv(data):
    with open('sensor_data.csv', mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([data.device_mac_address, data.timestamp, data.w, data.x, data.y, data.z])

# Define appStatus as a shared string (character array)
appStatus = mp.Array('c', b'down')
startExercise = mp.Array('c', b'false')
finishExercise = mp.Array('c', b'false')

import threading


read_configure_file()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("IMUsettings")
    client.subscribe("DeviceStatus")
    client.subscribe("StopRecording")

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
    elif 'StopRecording' in msg.payload.decode():
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

    elif 'exit' in msg.payload.decode():
        print('EXIT');

    elif 'Quaternion' in msg.payload.decode():
        print(msg.payload.decode())
    elif 'Linear' in msg.payload.decode():
        print(msg.payload.decode());
    elif '=' in msg.payload.decode():
        print('config message sent')
    else:
        print(msg.payload.decode())

    
def runScenario(queueData):
    try:
        print('running scenario')
        exercises = get_daily_schedule()
        if not exercises:
            print("No exercises found. Exiting loop.")
            return -1;
        for exercise in exercises:

            mbB1 = mp.Process(target=scheduler,args=(scheduleQueue,));
            mbB1.start();
            print(exercise)
            print(f"Exercise Name: {exercise['exerciseName']}, Progression: {exercise['progression']}")

            current_exercise = exercises[0];
            if (exercise['exerciseName'] == 'ex1'):
                config_message = "HEAD=FE:AC:84:C5:3D:E7-QUATERNIONS,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-LINEARACCELERATION,RIGHTFOOT=E1:55:61:CB:91:61-LINEARACCELERATION,exer_01"
            elif (exercise['exerciseName'] == 'ex2'):
                config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-LINEARACCELERATION,RIGHTFOOT=E1:55:61:CB:91:61-LINEARACCELERATION,exer_02"

            topic = "IMUsettings"
            with appStatus.get_lock():
                GETappStatus = bytes(appStatus.value).decode()  
            with startExercise.get_lock():
                GETstartExercise = bytes(startExercise.value).decode()
            
            '''
            while (GETappStatus != 'up'):
                print('waiting for the VC app...')
                time.sleep(1);
                with appStatus.get_lock():
                    GETappStatus = bytes(appStatus.value).decode()  
            '''
            #mobile app is up and running
            print('---I got UP. mobile app is up and running---')

            #start exercise
            print('---I am initiating ' + exercise['exerciseName'] + '---');

            print("config_message_01 =", config_message)
            print("exercise =", exercise)

            message = config_message;
            client.publish(topic, message);
            time.sleep(5);
            client.publish('StartRecording', 'start');

            mbB = mp.Process(target=receive_imu_data,args=(queueData, scheduleQueue, config_message, exercise, ));
            mbB.start();
            mbB.join();
            mbB1.kill();

            #input();
            client.publish('StopRecording', 'StopRecording')

            #client.publish(topic, 'stop');

            # communication with the VC

            time.sleep(10); #wait
            #start exercise sitting 02

            #client.publish(topic, 'exit');

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}");

    



if(enableConnectionToAPI):
    login()
    get_device_api_key()

server_process = mp.Process(target=start_multicast_server, args=(queueData,))
server_process.start()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL)

def publish_loop():
    topic = "IMUsettings"
    message1 = "myIMUsettings"

    while True:
        with appStatus.get_lock():
            current_status = bytes(appStatus.value).decode()  # Properly decode to string
        with startExercise.get_lock():
            startExer = bytes(startExercise.value).decode()  # Properly decode to string

        if current_status == 'down':
            #client.publish(topic, message1)
            print('waiting...')
            time.sleep(1)
        elif current_status == 'up':
            if (startExer == 'e01'):
                message = config_message;
                client.publish(topic, message);
            with startExercise.get_lock():
                startExercise.value = b'false'                
        else:
            time.sleep(1)  # Sleep to avoid busy-waiting


# Start the publishing loop in another thread
thread = threading.Thread(target=publish_loop)
#thread.start()

threadscenario = threading.Thread(target=runScenario, args=(queueData, ))
threadscenario.start()

client.loop_forever()

#thread.join()
threadscenario.join()
