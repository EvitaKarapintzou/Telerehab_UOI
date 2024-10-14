import socket
import struct
import json
import time
import random

mock_data = [
    {"deviceMacAddress": "RIGHTFOOT", "timestamp": 1728801927643, "w": 0.0, "x": -0.004409260116517544, "y": -0.006363841705024242, "z": -0.009383820928633213},
    {"deviceMacAddress": "LEFTFOOT", "timestamp": 1728801927645, "w": 0.0, "x": -0.002107941545546055, "y": -0.0057915388606488705, "z": -0.010091443546116352},
    {"deviceMacAddress": "PELVIS", "timestamp": 1728801927672, "w": 0.9925862550735474, "x": -0.11607484519481659, "y": -0.036043792963027954, "z": -1.8021991081695887E-6}
]

def random_float():
    return random.uniform(-1.0, 1.0)


def start_multicast_server(queueData):
    multicast_group = '224.1.1.1'
    server_address = ('', 10000)
    timestamp_increment = 10   # Increment in milliseconds


    # Create the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind to the server address
    sock.bind(server_address)

    # Tell the operating system to add the socket to the multicast group on all interfaces
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print("Listening for multicast messages...")

    try:
        while True:
            data, address = sock.recvfrom(1024)
            #print(f'Received {len(data)} bytes from {address}: {data.decode()}')
            #queueData.put(data.decode())

            json_data = json.loads(data.decode())
            #json_data = random.choice(mock_data)
            # Increment the timestamp for the selected body part
            #json_data['timestamp'] += timestamp_increment

            # Generate random values for w, x, y, z
            #json_data['w'] = random_float()
            #json_data['x'] = random_float()
            #json_data['y'] = random_float()
            #json_data['z'] = random_float()
            # Add system timestamp to the parsed data
            #json_data["systemTimestamp"] = int(time.time() * 1000)  # Current timestamp in milliseconds
            # Add the updated data back to the queue
            queueData.put(json.dumps(json_data))  # Convert back to a JSON string
            #time.sleep(0.005)
            #print(f'Received and updated {len(data)} bytes from {address}: {json_data}');
    finally:
        print('Closing socket')
        sock.close()
