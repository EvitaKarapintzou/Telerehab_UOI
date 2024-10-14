import json
from serial.tools import list_ports

def create_configuration():
  enmu_ports = enumerate(list_ports.comports())

  detected_mats = []
  device_list = []

  for n, (p, descriptor, hid) in enmu_ports:
      # print(p, descriptor, hid)
      device_to_add = p
      serial_to_add = hid.split(' ')[2].split(' ')[0].split('=')[1]
      
      mat_to_add = {"id": int(len(detected_mats) + 1),
                    "port": device_to_add,
                    "serial": serial_to_add,
                    "index": ""
                  }

      detected_mats.append(mat_to_add)

  # Create a json file containing mat(s) configuration to be used in get_mats_quantity function
  json.dump(detected_mats, open("_detected_mats_configuration.json", 'w'))
  
  # available_mats represents the _detected_mats_configuration.json
  available_mats = get_mats_information()

  for i in range(len(available_mats)):
    # device_list represents a list of '/dev/ttyACM*'
    device_list.append(available_mats[i]["port"])
  
  print(f"{len(available_mats)} mat(s) discovered")
  print('Detected devices configuration file created')
  print(device_list)
  return device_list

# Reads the configuration file and returns the number of the connected mats
def get_mats_information():
  try:
    with open("_detected_mats_configuration.json") as detected_mats:
      return json.load(detected_mats)
  except FileNotFoundError:
    print("Running mats detection")

if __name__ == "__main__":
  create_configuration()
  get_mats_information()