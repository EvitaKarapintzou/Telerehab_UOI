# python 3.6

from email import message
import random
import time
import csv

from paho.mqtt import client as mqtt_client


broker = '192.168.0.231'
port = 1883
topic = "location/123"
client_id = f'publish-{random.randint(0, 1000)}'
# username = 'emqx'
# password = 'public'

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def format_message(name, mac,row):
    splitRow = str(row).split(',')
    m = ""
    for i in range(len(splitRow)):
        m = m + " " + str(splitRow[i])
    #print("WWWW " + str(m))
    
    message = name + " " + mac + m
    return message

#MetaWear61 E15561CB9161 1706108668349 2024-01-24T17:04:28.349 58.4 0.9966065 -0.054574832 0.06161933 -1.982326E-5
    

def publish(client):
    msg_count = 1
    imu1 = open('2024-01-24-17-04-37_MetaWear61_2024-01-24T17.03.29.677_E15561CB9161_Quaternion_100.000Hz_1.7.3.csv', newline='')
    imu1Reader = csv.reader(imu1, delimiter=' ', quotechar='|')
    imu2 = open('2024-01-24-17-04-37_MetaWear94_2024-01-24T17.03.29.677_E25AD03D0194_Quaternion_100.000Hz_1.7.3.csv', newline='')
    imu2Reader = csv.reader(imu2, delimiter=' ', quotechar='|')
    imu3 = open('2024-01-24-17-04-37_MetaWearBD_2024-01-24T17.03.29.677_C8925E7DC6BD_Quaternion_100.000Hz_1.7.3.csv', newline='')
    imu3Reader = csv.reader(imu3, delimiter=' ', quotechar='|')
    imu4 = open('2024-01-24-17-04-37_MetaWearE7_2024-01-24T17.03.29.677_FEAC84C53DE7_Quaternion_100.000Hz_1.7.3.csv', newline='')
    imu4Reader = csv.reader(imu4, delimiter=' ', quotechar='|')

    imu1Data = []
    imu2Data = []
    imu3Data = []
    imu4Data = []

    for row in imu1Reader:
        #print(', '.join(row))
        imu1Data.append(format_message("MetaWear61", "E15561CB9161", ', '.join(row)))
        
    for row in imu2Reader:
        #print(', '.join(row))
        imu2Data.append(format_message("MetaWear94", "E25AD03D0194", ', '.join(row)))

    for row in imu3Reader:
        #print(', '.join(row))
        imu3Data.append(format_message("MetaWearBD", "C8925E7DC6BD", ', '.join(row)))

    for row in imu4Reader:
        #print(', '.join(row))
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
            
            result = client.publish(topic, str(sendData))
            sendData = []
            #time.sleep(0.3)


def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)
    print("telos")
    client.loop_stop()


if __name__ == '__main__':
    run()
