import time
from shared_variables import queueData, counter, startReceiving, lastDataTime, mqttState

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("location/123")

def on_message(client, userdata, msg):
    global counter, mqttState 
    counter = 1
    startReceiving.value = True   
    lastDataTime.value = time.time()
    #print("Message Received. ", msg.payload.decode(), " ", counter)
    if 'start' in msg.payload.decode():
        new_value = "R"
        mqttState.value = new_value.encode()  
        print("Exercise started!") 
    elif 'stop' in msg.payload.decode():
        new_value = "S"
        mqttState.value = new_value.encode()  
        print("Exercise finished!") 
    queueData.put(msg.payload.decode())
