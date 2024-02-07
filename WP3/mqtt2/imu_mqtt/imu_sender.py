
from email import message
import random
import time
import csv

from paho.mqtt import client as mqtt_client


broker = '195.130.118.252'
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
    imu1 = open('DAC19F1B6E40_2024-02-05_13:24:22.csv', newline='')
    imu1Reader = csv.reader(imu1, delimiter=' ', quotechar='|')
    imu2 = open('E25AD03D0194_2024-02-05_13:24:22.csv', newline='')
    imu2Reader = csv.reader(imu2, delimiter=' ', quotechar='|')
    imu3 = open('C8925E7DC6BD_2024-02-05_13:24:22.csv', newline='')
    imu3Reader = csv.reader(imu3, delimiter=' ', quotechar='|')
    imu4 = open('FEAC84C53DE7_2024-02-05_13:24:22.csv', newline='')
    imu4Reader = csv.reader(imu4, delimiter=' ', quotechar='|')

    imu1Data = []
    imu2Data = []
    imu3Data = []
    imu4Data = []

    for row in imu1Reader:
        imu1Data.append(format_message("MetaWear40", "DAC19F1B6E40", ', '.join(row)))
        
    for row in imu2Reader:
        imu2Data.append(format_message("MetaWear94", "E25AD03D0194", ', '.join(row)))

    for row in imu3Reader:
        imu3Data.append(format_message("MetaWearBD", "C8925E7DC6BD", ', '.join(row)))

    for row in imu4Reader:
        imu4Data.append(format_message("MetaWearE7", "FEAC84C53DE7", ', '.join(row)))

    sendData = []
    
    for i in range(min(len(imu1Data),len(imu2Data),len(imu3Data), len(imu4Data))):

        sendData.append(imu1Data[i])
        sendData.append(imu2Data[i])
        sendData.append(imu3Data[i])
        sendData.append(imu4Data[i])
        
        print(sendData)
        if(len(sendData) >=100):
            sendDataString = ""

            sendDataString = ", ".join(["\"" + item + "\"" for item in sendData])
            result = client.publish(topic, str(sendDataString))
            sendData = []

def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    print("telos")
    client.loop_stop()

if __name__ == '__main__':
    run()
