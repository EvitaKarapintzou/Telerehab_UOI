import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

right = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/imu_mqtt/results/Gaitlinear/NewGait2/01_Walk_2024-03-29_14:56:45/right_FEAC84C53DE7_2024-03-29_14:56:45.csv')
#left = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/imu_mqtt/results/Gaitlinear/NewGait2/01_Walk_2024-03-29_14:56:45/left_C8925E7DC6BD_2024-03-29_14:56:45.csv')

plt.figure(figsize=(16,12))

plt.subplot(3,1,1)
plt.plot(right['Elapsed(s)'], right['W(number)'], label = 'X Component Right', color='darkgreen')
plt.plot(left['Elapsed(s)'], left['W(number)'], label = 'X Component Left', color='darkviolet')
plt.title('X Value over time of 2nd New Gait' )
plt.xlabel('Elapsed Time (s)')
plt.ylabel('X Value')
plt.grid(True)
plt.legend()

plt.subplot(3,1,2)
plt.plot(right['Elapsed(s)'], right['X(number)'], label = 'Y Component Right', color='darkgreen')
plt.plot(left['Elapsed(s)'], left['X(number)'], label = 'Y Component Left', color='darkviolet')
plt.title('Y Value over time of 2nd New Gait' )
plt.xlabel('Elapsed Time (s)')
plt.ylabel('Y Value')
plt.grid(True)
plt.legend()

plt.subplot(3,1,3)
plt.plot(right['Elapsed(s)'], right['Y (number)'], label = 'Z Component Right', color='darkgreen')
plt.plot(left['Elapsed(s)'], left['Y (number)'], label = 'Z Component Left', color='darkviolet')
plt.title('Z Value over time of 2nd New Gait' )
plt.xlabel('Elapsed Time (s)')
plt.ylabel('Z Value')
plt.grid(True)
plt.legend()


plt.tight_layout()
plt.show()