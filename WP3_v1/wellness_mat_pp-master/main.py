import os
from pathlib import Path
from detect_available_mats import create_configuration
import menu_options

  
try:
    filename = Path("_detected_mats_configuration.json")
    if filename.is_file():
      os.remove(filename)
      print('Existing configuration file removed')
    print("\n")
    create_configuration()
    print("\n")
except OSError:
    pass

# def clear_screen():
#   time.sleep(1)
#   os.system('cls' if os.name == 'nt' else 'clear')

def menu():
  # clear_screen()
  print("Please type in a number to select the respective menu option")
  print("\n")
  print("[0] Terminate the application")
  print("[1] Create connected mats sequence")
  print("[2] Start Standing excersise")
  print("[3] Start Walking excersise")
  print("\n")

def get_user_input():
  try:
    selection = int(input("Enter your selection: "))
  except ValueError:
    print("Please input a valid option")
  return selection

while True:
  # clear_screen()
  menu()
  option = get_user_input()

  if option == 0:
    print("Application Terminated")
    break
  
  elif option == 1:
    menu_options.create_sequence()

  elif option == 2:
    menu_options.standing_excercise()
    
  elif option == 3:
    menu_options.walking_excercise()

  else:
    print("Please input a valid option")

  print("\n")

if __name__ == "__main__":
  menu()