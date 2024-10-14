import pandas as pd
from datetime import datetime as dt
import json

# *** *** *** Print DataFrame in Terminal and export to xlsx file *** *** *** 
def print_data_frame(current_map):
  # Prepare the data for DataFrame
  list_of_sensor_maps = [device_map['sensors'] for device_map in current_map]
  
  # Flatten each 48x48 sensor map to have a row with 48 elements
  flattened_data = [sensor_row for sensor_map in list_of_sensor_maps for sensor_row in sensor_map]

  # Create the DataFrame with 48 columns
  pd.set_option("display.max_rows", None)
  df = pd.DataFrame(flattened_data)
  print(df)

  # Save DataFrame to an Excel file
  df.to_excel('_data.xlsx', index=False)



# *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** *** ***

def export_to_json(current_map):
  timepoint = dt.now().isoformat()
  filename = f"_Standing_Exercise_{timepoint}.json"

  json.dump(current_map, open(filename,'w'))
  print('The standing excercise was completed and the file was created ')

if __name__ == "__main__":
  export_to_json()
  print_data_frame()