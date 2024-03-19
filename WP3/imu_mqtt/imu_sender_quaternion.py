from email import message
import random
import time
import csv
import random
from paho.mqtt import client as mqtt_client


broker = '195.251.196.168'
port = 1883
topic = "location/123"
client_id = f'publish-{random.randint(0, 1000)}'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def format_message(name, mac,row):
    splitRow = str(row).split(',')
    m = ""
    for i in range(len(splitRow)):
        m = m + " " + str(splitRow[i])
    message = name + " " + mac + m
    return message

def publish(client):
    msg_count = 1
    imu1 = open('sensor01Quaternion.csv', newline='')
    imu1Reader = csv.reader(imu1, delimiter=' ', quotechar='|')
    imu2 = open('sensor02Quaternion.csv', newline='')
    imu2Reader = csv.reader(imu2, delimiter=' ', quotechar='|')
    imu3 = open('sensor03Quaternion.csv', newline='')
    imu3Reader = csv.reader(imu3, delimiter=' ', quotechar='|')
    imu4 = open('sensor04Quaternion.csv', newline='')
    imu4Reader = csv.reader(imu4, delimiter=' ', quotechar='|')

    imu1Data = []
    imu2Data = []
    imu3Data = []
    imu4Data = []

    for row in imu1Reader:
        imu1Data.append(format_message("MetaWear06", "FBCB666B9506", ', '.join(row)))
        
    for row in imu2Reader:
        imu2Data.append(format_message("MetaWearA4", "E524A8BDE1A4", ', '.join(row)))

    for row in imu3Reader:
        imu3Data.append(format_message("MetaWearC5", "C172766109C5", ', '.join(row)))

    for row in imu4Reader:
        imu4Data.append(format_message("MetaWearE7", "FEAC84C53DE7", ', '.join(row)))
    sendData = []
    
    len1 = len(imu1Data)
    len2 = len(imu2Data)
    len3 = len(imu3Data)
    len4 = len(imu4Data)
    c1 = 0;
    c2 = 0;
    c3 = 0;
    c4 = 0;

    client.publish(topic, "start")

    #for i in range(min(len(imu1Data),len(imu2Data),len(imu3Data), len(imu4Data))):
    while(c1 < len1 or c2 < len2 or c3 < len3 or c4 < len4):
        r = random.randint(1, 4)
        if (r == 1):
            if (c1 < len1):
                sendData.append(imu1Data[c1])
                c1 = c1 + 1;
        elif (r == 2):
            if (c2 < len2):
                sendData.append(imu2Data[c2])
                c2 = c2 + 1
        elif (r == 3):
            if (c3 < len3):
                sendData.append(imu3Data[c3])
                c3 = c3 + 1;
        else:
            if (c4 < len4):
                sendData.append(imu4Data[c4])
                c4 = c4 + 1
        time.sleep(1/1000.0)
        if(len(sendData) >= 1000):
            sendDataString = ""

            sendDataString = ", ".join(["\"" + item + "\"" for item in sendData])
            result = client.publish(topic, str(sendDataString))
            time.sleep(1/4.0)
            sendData = []
    client.publish(topic, "stop")

def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    print("telos")
    client.loop_stop()

if __name__ == '__main__':
    run()
