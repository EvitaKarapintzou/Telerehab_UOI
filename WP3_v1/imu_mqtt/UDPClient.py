import socket
import FindMyIP as ip
import time

def SendMyIP():
    for i in range(10):

        multicast_group = '224.1.1.1'
        port = 10001

        local_ip = ip.internal()
        #print("I'm sending message!!!!!!!!!!!!!!!!!")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(local_ip.encode(), (multicast_group, port))
        time.sleep(1)
    return 0
