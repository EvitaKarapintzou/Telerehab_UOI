import time
from shared_variables import appStatus, queueData, counter, startReceiving, lastDataTime, mqttState

'''
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("IMUsettings")
    client.subscribe("DeviceStatus")


def on_message(client, userdata, msg):
    global counter, mqttState 
    counter = 1
    startReceiving.value = True   
    lastDataTime.value = time.time()
    print("Message Received. ", msg.payload.decode(), " ", counter)
    if 'start' in msg.payload.decode():
        new_value = "R"
        mqttState.value = new_value.encode()  
        print("\033[1m\033[93mExercise started!\033[0m") 
    elif 'stop' in msg.payload.decode():
        new_value = "S"
        mqttState.value = new_value.encode()  
        print("\033[1m\033[93mExercise finished!\033[0m") 
    elif 'up' in msg.payload.decode():
        appStatus = 'up';
        print('I got UP');
    queueData.put(msg.payload.decode())
'''