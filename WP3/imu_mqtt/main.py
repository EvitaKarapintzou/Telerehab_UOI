import multiprocessing as mp
import paho.mqtt.client as mqtt

from mqtt_management import on_connect, on_message
from data_management import scheduler, receive_imu_data, condition_checker
from api_management import login, get_device_api_key
from configure_file_management import read_configure_file
from shared_variables import queueData, scheduleQueue, imus, enableConnectionToAPI, MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL

read_configure_file()

if(enableConnectionToAPI):
    login()
    get_device_api_key()

mbB = mp.Process(target=receive_imu_data,args=(queueData,scheduleQueue,));
mbB.start();
mbB1 = mp.Process(target=scheduler,args=(scheduleQueue,));
mbB1.start();
condition_thread = mp.Process(target=condition_checker);
condition_thread.start()

client = mqtt.Client()
client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEP_ALIVE_INTERVAL)
client.on_connect = on_connect
client.on_message = on_message

client.loop_forever()
'''
topic = "IMUsettings"
message = "myIMUsettings"  # Change this to your desired message

client.publish(topic, message)
while (appStatus == 'down'):
    client.publish(topic, message)
    time.sleep(1)

message = "[DA:C1:9F:1B:6E:40, Linear], [EB:0B:A9:F4:5E:4E, Quaternion], [EF:0F:A9:3D:48:AA, OFF], [ED:B1:65:CE:EF:D4, Quaternion]";
client.publish(topic, message)
'''