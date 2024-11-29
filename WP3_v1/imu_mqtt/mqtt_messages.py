import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# MQTT Configuration
MQTT_BROKER_HOST = "192.168.0.231"
MQTT_BROKER_PORT = 1883
MQTT_KEEP_ALIVE_INTERVAL = 60

# Topics
DEMO_TOPIC = "exercise/demo"
MSG_TOPIC = "exercise/msg"

# Global Flags
ack_received = False
demo_start_received = False
demo_end_received = False
finish_received = False

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe([(DEMO_TOPIC, 0), (MSG_TOPIC, 0)])


def on_message(client, userdata, msg):
    global ack_received, demo_start_received, demo_end_received, finish_received

    payload = json.loads(msg.payload.decode())
    print(f"Received message on {msg.topic}: {payload}")

    if msg.topic == DEMO_TOPIC:
        if payload.get("action") == "ACK":
            ack_received = True
        elif payload.get("action") == "DEMO_START":
            demo_start_received = True
        elif payload.get("action") == "DEMO_END":
            demo_end_received = True
        elif payload.get("action") == "FINISH":
            finish_received = True
    elif msg.topic == MSG_TOPIC:
        if payload.get("action") == "ACK":
            ack_received = True
        elif payload.get("action") == "FINISH":
            finish_received = True


# Publish and Wait
def publish_and_wait(topic, message, timeout=1000, wait_for="ACK"):
    global ack_received, demo_start_received, demo_end_received, finish_received

    ack_received = demo_start_received = demo_end_received = finish_received = False
    client.publish(topic, json.dumps(message))
    print(f"Published: {message} to {topic}")

    start_time = time.time()
    while time.time() - start_time < timeout:
        if wait_for == "ACK" and ack_received:
            return True
        if wait_for == "DEMO_START" and demo_start_received:
            return True
        if wait_for == "DEMO_END" and demo_end_received:
            return True
        if wait_for == "FINISH" and finish_received:
            return True
        time.sleep(0.5)
    print(f"Timeout waiting for {wait_for} on message: {message}")
    return False


# Initialize MQTT Client
def init_mqtt_client():
    global client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL)
    client.loop_start()
    print("MQTT client initialized and connected to broker.")


# Function for Language Selection
def set_language(language):
    language_message = {
        "action": "LANGUAGE",
        "exercise": "/",
        "timestamp": datetime.now().isoformat(),
        "code": "",
        "message":"",
        "language":language
    }
    while not publish_and_wait(DEMO_TOPIC, language_message, wait_for="FINISH"):
        print("Retrying LANGUAGE message...")
    print(f"Language set to {language}")

#{'exerciseName': 'ex1', 'progression': 0, 'exerciseId': 1, 'weekNumber': 47, 'year': 2024}
# Function for Exercise Demonstration
def start_exercise_demo(exercise):
    if exercise['exerciseId'] == 1:
        exercise_name = f"VC holobalance_sitting_1 P{exercise['progression']}"
    elif exercise['exerciseId'] == 2:
        exercise_name = f"VC holobalance_sitting_2 P{exercise['progression']}"
    elif exercise['exerciseId'] == 3:
        exercise_name = f"VC holobalance_sitting_3 P{exercise['progression']}"
    elif exercise['exerciseId'] == 2:
        exercise_name = f"VC holobalance_sitting_2 P{exercise['progression']}"
    elif exercise['exerciseId'] == 2:
        exercise_name = f"VC holobalance_sitting_2 P{exercise['progression']}"
    elif exercise['exerciseId'] == 2:
        exercise_name = f"VC holobalance_sitting_2 P{exercise['progression']}"
    elif exercise['exerciseId'] == 2:
        exercise_name = f"VC holobalance_sitting_2 P{exercise['progression']}"
    elif exercise['exerciseId'] == 2:
        exercise_name = f"VC holobalance_sitting_2 P{exercise['progression']}"
    elif exercise['exerciseId'] == 2:
        exercise_name = f"VC holobalance_sitting_2 P{exercise['progression']}"
    elif exercise['exerciseId'] == 2:
        exercise_name = f"VC holobalance_sitting_2 P{exercise['progression']}"
    else:
        exercise_name = f"VC holobalance_sitting_3 P{exercise['progression']}"

    demo_message = {
        "action": "START",
        "exercise": exercise_name,
        "timestamp": datetime.now().isoformat(),
        "code" : "",
        "message": "",
        "language":"/"
    }
    while not publish_and_wait(DEMO_TOPIC, demo_message, wait_for="ACK"):
        print("Retrying START message...")
    while not publish_and_wait(DEMO_TOPIC, demo_message, wait_for="DEMO_START"):
        print("Retrying DEMO_START...")
    while not publish_and_wait(DEMO_TOPIC, demo_message, wait_for="DEMO_END"):
        print("Waiting for DEMO_END...")
    print(f"Exercise demonstration for {exercise_name} completed.")


# Function for Sending Oral Instructions
def send_oral_instructions(code):
    oral_message = {
        "action": "SPEAK",
        "exercise": "/",
        "timestamp": datetime.now().isoformat(),
        "code": code,
        "message":"Thats it for today. Thank you very much for your cooperation, and have a nice day. I was glad to be of help.",
        "language":"/"
    }
    while not publish_and_wait(MSG_TOPIC, oral_message, wait_for="ACK"):
        print("Retrying SPEAK message...")
    while not publish_and_wait(MSG_TOPIC, oral_message, wait_for="FINISH"):
        print("Retrying DEMO_START...")
    
