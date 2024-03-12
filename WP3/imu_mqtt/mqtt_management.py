import time
from shared_variables import queueData, counter, startReceiving, lastDataTime

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("location/123")

def on_message(client, userdata, msg):
    global counter
    counter = counter + 1
    startReceiving.value = True   
    lastDataTime.value = time.time()
    #print("Message Recieved. ", msg.payload.decode(), " ", counter)
    queueData.put(msg.payload.decode())