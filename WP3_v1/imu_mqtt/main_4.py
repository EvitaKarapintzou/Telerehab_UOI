import logging
import json
import paho.mqtt.client as mqtt
import sys
import os
import multiprocessing as mp
import threading
import time
import requests
import configparser
from datetime import datetime
from mqtt_messages import init_mqtt_client, set_language, start_exercise_demo, send_oral_instructions,publish_and_wait
from data_management_v05 import scheduler, receive_imu_data
from api_management import login, get_device_api_key
from configure_file_management import read_configure_file
from Polar_test import start_ble_process 
from shared_variables import (
    queueData, scheduleQueue, enableConnectionToAPI,
    MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL,
    mqttState
)
from UDPSERVER import start_multicast_server
from websocketServer import run_websocket_server

# Set up logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(message)s')
file_handler = logging.FileHandler('app.log', mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Redirect stdout and stderr to logger
class StreamToLogger:
    def __init__(self, log_level):
        self.log_level = log_level

    def write(self, message):
        if message.strip():
            self.log_level(message.strip())

    def flush(self):
        pass

# sys.stdout = StreamToLogger(logger.info)
# sys.stderr = StreamToLogger(logger.error)

# Helper functions for API interaction
def get_daily_schedule():
    """Fetch the daily schedule from the API."""
    config = configparser.ConfigParser()
    config.read('/home/uoi/Documents/GitHub/Telerehab_UOI/WP3_v1/imu_mqtt/config.ini')
    api_key_edge = config['API'].get('key_edge', '')
    
    url = 'http://telerehab-develop.biomed.ntua.gr/api/PatientSchedule/daily'
    headers = {
        'accept': '*/*',
        'Authorization': 'QYuNcxPG6DYF4r8VJdjrirec2vLdDEDc2CrtFAvj'
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()

def post_results(score, exercise_id):
    """Post metrics to the PerformanceScore API."""
    try:
        url = "https://telerehab-develop.biomed.ntua.gr/api/PerformanceScore"
        date_posted = datetime.now().isoformat()
        post_data = {
            "score": score,
            "exerciseId": exercise_id,
            "datePosted": date_posted
        }
        headers = {
            "Authorization": "QYuNcxPG6DYF4r8VJdjrirec2vLdDEDc2CrtFAvj",  
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=post_data, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Metrics successfully posted for exercise ID {exercise_id}")
        else:
            logger.error(f"Failed to post metrics for exercise ID {exercise_id}. Status code: {response.status_code}")
            logger.error("Response: " + response.text)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error posting results: {e}")

# Main logic to run scenario
def runScenario(queueData):
    init_mqtt_client()

    try:
        set_language("EN")
    except Exception as e:
        print(f"Language selection failed{e}")
        return


    try:
        metrics_queue = mp.Queue()
        polar_queue = mp.Queue()
        logger.info('Running scenario...')
        
        while True:
            # Fetch the daily schedule
            exercises = get_daily_schedule()
            print("Get list",exercises)
            if not exercises:
                logger.info("No exercises found. Exiting.")
                break

            # Process each exercise in the schedule
            for exercise in exercises:
                logger.info(f"Processing Exercise ID: {exercise['exerciseId']}")
                
                try:
                    start_exercise_demo(exercise)
                except Exception as e:
                    logger.error(f"Demonstration failed for Exercise ID {exercise['exerciseId']}: {e}")
                    continue

                
                # Determine the config message based on exercise ID
                if exercise['exerciseId'] == 1:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-QUATERNIONS,PELVIS=E2:5A:D0:3D:01:94-OFF,LEFTFOOT=EF:0F:A9:3D:48:AA-OFF,RIGHTFOOT=E1:55:61:CB:91:61-OFF,exer_01"
                elif exercise['exerciseId'] == 2:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-QUATERNIONS,PELVIS=E2:5A:D0:3D:01:94-OFF,LEFTFOOT=C8:92:5E:7D:C6:BD-OFF,RIGHTFOOT=E1:55:61:CB:91:61-OFF,exer_02"
                elif exercise['exerciseId'] == 3:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-QUATERNIONS,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-OFF,RIGHTFOOT=E1:55:61:CB:91:61-OFF,exer_03"
                elif exercise['exerciseId'] == 4:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-OFF,RIGHTFOOT=E1:55:61:CB:91:61-OFF,exer_04"
                elif exercise['exerciseId'] == 5:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-OFF,LEFTFOOT=C8:92:5E:7D:C6:BD-QUATERNIONS,RIGHTFOOT=E1:55:61:CB:91:61-QUATERNIONS,exer_05"
                elif exercise['exerciseId'] == 6:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-OFF,LEFTFOOT=C8:92:5E:7D:C6:BD-QUATERNIONS,RIGHTFOOT=E1:55:61:CB:91:61-QUATERNIONS,exer_06"
                elif exercise['exerciseId'] == 7:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-QUATERNIONS,RIGHTFOOT=E1:55:61:CB:91:61-QUATERNIONS,exer_07"
                elif exercise['exerciseId'] == 8:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-QUATERNIONS,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-OFF,RIGHTFOOT=E1:55:61:CB:91:61-OFF,exer_08"
                elif exercise['exerciseId'] == 9:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-OFF,RIGHTFOOT=E1:55:61:CB:91:61-OFF,exer_09"
                elif exercise['exerciseId'] == 10:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-OFF,RIGHTFOOT=E1:55:61:CB:91:61-OFF,exer_10"
                elif exercise['exerciseId'] == 11:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-QUATERNIONS,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-OFF,RIGHTFOOT=E1:55:61:CB:91:61-OFF,exer_11"
                elif exercise['exerciseId'] == 12:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-QUATERNIONS,RIGHTFOOT=E1:55:61:CB:91:61-QUATERNIONS,exer_12"
                elif exercise['exerciseId'] == 13:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-QUATERNIONS,RIGHTFOOT=E1:55:61:CB:91:61-QUATERNIONS,exer_13"
                elif exercise['exerciseId'] == 14:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-OFF,RIGHTFOOT=E1:55:61:CB:91:61-OFF,exer_14"
                elif exercise['exerciseId'] == 15:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-QUATERNIONS,RIGHTFOOT=E1:55:61:CB:91:61-QUATERNIONS,exer_15"
                elif exercise['exerciseId'] == 16:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-QUATERNIONS,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-LINEARACCELERATION,RIGHTFOOT=E1:55:61:CB:91:61-LINEARACCELERATION,exer_16"
                elif exercise['exerciseId'] == 17:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-QUATERNIONS,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-LINEARACCELERATION,RIGHTFOOT=E1:55:61:CB:91:61-LINEARACCELERATION,exer_17"
                elif exercise['exerciseId'] == 18:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-QUATERNIONS,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-LINEARACCELERATION,RIGHTFOOT=E1:55:61:CB:91:61-LINEARACCELERATION,exer_18"
                elif exercise['exerciseId'] == 19:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-OFF,PELVIS=E2:5A:D0:3D:01:94-OFF,LEFTFOOT=C8:92:5E:7D:C6:BD-LINEARACCELERATION,RIGHTFOOT=E1:55:61:CB:91:61-LINEARACCELERATION,exer_19"
                elif exercise['exerciseId'] == 20:
                    config_message = "HEAD=FE:AC:84:C5:3D:E7-QUATERNIONS,PELVIS=E2:5A:D0:3D:01:94-QUATERNIONS,LEFTFOOT=C8:92:5E:7D:C6:BD-LINEARACCELERATION,RIGHTFOOT=E1:55:61:CB:91:61-LINEARACCELERATION,exer_20"
                else:
                    logger.warning(f"No config message found for Exercise ID: {exercise['exerciseId']}")
                    continue
                
                # Publish configuration and start the exercise
                topic = "IMUsettings"

                # Publish the configuration message to start the exercise
                print('--- Starting the exercise ---')
                client.publish(topic, config_message)
                time.sleep(2)
                client.publish('StartRecording', 'start')

                # Start the scheduler process
                scheduler_process = mp.Process(target=scheduler, args=(scheduleQueue,))
                scheduler_process.start()

                # Send Oral Instruction after the system 
                try:
                     send_oral_instructions("bph0082")
                except Exception as e:
                     logger.error(f"Failed to send oral instruction for Exercise ID {exercise['exerciseId']}: {e}")
                     continue
                
                polar_proc = mp.Process(target=start_ble_process, args=(0, polar_queue))  # Adjust adapter index if needed
                polar_proc.start()

                # Start the process to receive and process IMU data
                imu_process = mp.Process(
                    target=receive_imu_data,
                    args=(queueData, scheduleQueue, config_message, exercise,metrics_queue)
                )
                imu_process.start()

                # Wait for the IMU process to finish
                imu_process.join()

                # Terminate the scheduler process
                scheduler_process.terminate()
                scheduler_process.join()

                # Stop recording after data collection is done
                client.publish('StopRecording', 'StopRecording')
                time.sleep(2)

                polar_proc.terminate()
                polar_proc.join()
                
                polar_data = []
                while not polar_queue.empty():
                    polar_data.append(polar_queue.get())
                
                # Post metrics after the exercise ends
                if not metrics_queue.empty():
                    metrics = metrics_queue.get()
                    try:
                        metrics = json.loads(metrics) if isinstance(metrics, str) else metrics
                    except json.JSONDecodeError:
                        print("Metrics could not be parsed as JSON.")
                        return
                    print(f"Metrics for Exercise {exercise['exerciseId']}: {metrics}")

                    # Post the results
                    metrics["polar_data"] = polar_data
                    post_results(json.dumps(metrics), exercise['exerciseId'])
                     # Send Oral Instruction after the system 
                    try:
                        send_oral_instructions("bph0083")
                    except Exception as e:
                        logger.error(f"Failed to send oral instruction for Exercise ID {exercise['exerciseId']}: {e}")
                        continue
                # Mark the exercise as completed
                print(f"Exercise {exercise['exerciseName']} completed.")

            
            # Fetch updated schedule after processing current exercises
            exercises = get_daily_schedule()

    except requests.exceptions.RequestException as e:
        logger.error(f"Error: {e}")

# MQTT setup
def on_connect(client, userdata, flags, rc):
    logger.info("Connected to MQTT broker with result code " + str(rc))
    client.subscribe("IMUsettings")
    client.subscribe("DeviceStatus")
    client.subscribe("StopRecording")

def on_message(client, userdata, msg):
    logger.info(f"Message Received -> {msg.payload.decode()}")

# Start MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL)

# Publish loop
def publish_loop():
    topic = "IMUsettings"
    while True:
        time.sleep(1)

# Start necessary processes
if enableConnectionToAPI:
    login()
    get_device_api_key()

server_process = mp.Process(target=start_multicast_server, args=(queueData,))
server_process.start()

thread = threading.Thread(target=publish_loop)
thread.start()

threadscenario = threading.Thread(target=runScenario, args=(queueData,))
threadscenario.start()

client.loop_forever()
