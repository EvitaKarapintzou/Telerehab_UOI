import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.signal import argrelextrema

# imu_data_back = pd.read_csv(r'C:\Users\xrysa\OneDrive\Υπολογιστής\Sitting_data\02\old_sitting_2\normal\2024-02-16_14_05_36_old_sitting_2_normal_3\back_E15561CB9161_2024-02-16_14_05_36.csv')
# imu_data_head = pd.read_csv(r'C:\Users\xrysa\OneDrive\Υπολογιστής\Sitting_data\02\old_sitting_2\normal\2024-02-16_14_05_36_old_sitting_2_normal_3\head_E25AD03D0194_2024-02-16_14_05_36.csv')

# imu_data_left = pd.read_csv(r'C:\Users\xrysa\OneDrive\Υπολογιστής\Sitting_data\02\old_sitting_2\normal\2024-02-16_14_05_36_old_sitting_2_normal_3\left_C8925E7DC6BD_2024-02-16_14_05_36.csv')
# imu_data_right = pd.read_csv(r'C:\Users\xrysa\OneDrive\Υπολογιστής\Sitting_data\02\old_sitting_2\normal\2024-02-16_14_05_36_old_sitting_2_normal_3\right_FEAC84C532024-03-12_14_29_57DE7_2024-02-16_14_05_36.csv')




#imu_data_back = pd.read_csv(r'C:\Users\xrysa\OneDrive\Υπολογιστής\ALLData\Gaitlinear1\Gaitlinear\NewGait1\01_normal_2024-03-29_16_02_13\back_E15561CB9161_2024-03-29_16_02_13.csv')
#imu_data_head = pd.read_csv(r'C:\Users\xrysa\OneDrive\Υπολογιστής\ALLData\Standing data\OldStanding4\01_OldStanding4_2024-04-01_12_49_11\Head_E15561CB9161_2024-04-01_13_30_07.csv')

imu_data_left = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/imu_mqtt/results/Gaitlinear/NewGait2/01_Walk_2024-03-29_14:56:45/left_C8925E7DC6BD_2024-03-29_14:56:45.csv')
imu_data_right = pd.read_csv(r'/home/uoi/Documents/GitHub/Telerehab_UOI/WP3/imu_mqtt/results/Gaitlinear/NewGait2/01_Walk_2024-03-29_14:56:45/right_FEAC84C53DE7_2024-03-29_14:56:45.csv')
#print(imu_data_back)


# # Extract the acceleration data from the IMU (assuming x, y, z columns for acceleration)
# #acc_df = df[['x-axis (g)', 'y-axis (g)', 'z-axis (g)']].to_numpy()
# acc_Ldf = imu_data_left[['W(number)', 'X(number)', 'Y (number)', 'Z (number)']].to_numpy()
# acc_Rdf = imu_data_right[['W(number)', 'X(number)', 'Y (number)', 'Z (number)']].to_numpy()


# # Extract the y-axis component of the acceleration
# acc_Ly = acc_Ldf[:, 1]
# acc_Ry = acc_Rdf[:, 1]



# # Apply a low-pass filter to the acceleration data
# cutoff_freq = 20.0
# fs = 100.0
# nyquist_freq = fs / 2.0
# filter_order = 4
# b, a = signal.butter(filter_order, cutoff_freq / nyquist_freq, 'low')
# acc_Ly_filtered = signal.filtfilt(b, a, acc_Ly)
# acc_Ry_filtered = signal.filtfilt(b, a, acc_Ry)


# #Find local maxima in the filtered acceleration signal
# # You can adjust the order parameter to control the sensitivity of the peak detection
# step_indices_Left = signal.argrelextrema(acc_Ly_filtered, np.greater, order=20)[0]
# heel_indices_Left = signal.argrelextrema(acc_Ly_filtered, np.less, order=5)[0]
# toe_off_indices_Left = signal.argrelextrema(acc_Ly_filtered, np.greater, order=10)[0]




# # Define the area of interest in terms of index
# start_index = int(4 * fs)  # 4 seconds
# end_index_Left = len(acc_Ly_filtered) - int(6 * fs)
# toe_off_indices_Left = toe_off_indices_Left[start_index:end_index_Left]
# heel_indices_Left = heel_indices_Left[start_index:end_index_Left]

# # Detect toe-off events
# toe_off_indices_Left = signal.argrelextrema(acc_Ly_filtered, np.greater, order=13)[0]
# toe_off_Left = [i for i in toe_off_indices_Left if -0.55 < acc_Ly_filtered[i] < 0.45]

# # Detect heel strike events
# heel_indices_Left = signal.argrelextrema(acc_Ly_filtered, np.less, order=13)[0]
# heel_strike_Left = [i for i in heel_indices_Left if -0.63 < acc_Ly_filtered[i] < -0.67]

# # Filter the events to keep only the ones within the area of interest
# heel_indices_Left = heel_indices_Left[(heel_indices_Left >= start_index) & (heel_indices_Left <= end_index_Left)]
# toe_off_indices_Left = toe_off_indices_Left[(toe_off_indices_Left >= start_index) & (toe_off_indices_Left <= end_index_Left)]         


# # Detect toe off and heel strike events
# index_to_Left = signal.argrelextrema(acc_Ly_filtered, np.greater, order=13)[0]
# toe_off_Left = []

# for i in range(len(index_to_Left)):
#     if -0.55 < acc_Ly_filtered[index_to_Left[i]] < 0.45:
#         toe_off_Left.append(index_to_Left[i])

# index_hs_Left = signal.argrelextrema(acc_Ly_filtered, np.less, order=13)[0]
# heel_strike_Left = []

# for i in range(len(index_hs_Left)):
#     if -0.63 < acc_Ly_filtered[index_hs_Left[i]] < -0.65:
#         heel_strike_Left.append(index_hs_Left[i])
        


# # Convert the step_indices to times
# step_times_Left = step_indices_Left / fs
# heel_times_Left = heel_indices_Left / fs
# toe_off_times_Left = toe_off_indices_Left / fs
# #print(len(heel_times_Left))
# print(len(toe_off_times_Left))

# # Create a DataFrame with heel strike and toe off times
# data = {'Heel Strike Times': heel_times_Left*100, 'Toe Off Times': toe_off_times_Left*100}
# df = pd.DataFrame(data)


# # Save the DataFrame to a CSV file
# df.to_csv('Left_Leg_events_times.csv', index=False)

# # Define the time range for plotting (excluding first 4 seconds and last 4 seconds)
# t_Left = np.arange(len(acc_Ly)) / fs
# plot_start_time_Left = 4.0  # seconds
# plot_end_time_Left = len(acc_Ly) / fs - 6.0  # seconds
# plot_indices_Left = np.where((t_Left >= plot_start_time_Left) & (t_Left <= plot_end_time_Left))[0]


# # Plot the results
# #plt.plot(step_times, acc_Ly_filtered[step_indices], 'go', label='Steps')
# plt.plot(heel_times_Left*100, acc_Ly_filtered[heel_indices_Left], 'bs', label='Heel Strikes Left Leg')
# plt.plot(toe_off_times_Left*100, acc_Ly_filtered[toe_off_indices_Left], 'ro', label='Toe Off Left Leg')
# plt.plot(t_Left*100, acc_Ly, label='Acceleration along y-axis')
# plt.plot(t_Left*100, acc_Ly_filtered, label='Filtered acceleration along y-axis')
# plt.xlim(plot_start_time_Left*100, plot_end_time_Left*100)
# plt.ylim(-1, -0.3)  # Set y-axis limits
# plt.legend()
# plt.xlabel('Time (s)')
# plt.ylabel('Acceleration (m/s^2)')



# legend = plt.legend()
# for text in legend.get_texts():
#     text.set_fontsize(10)
    
# print("Step times:", step_times_Left*100)
# print("Heel strike times Left Leg:", heel_times_Left*100)
# print("Toe off times Left Leg:", toe_off_times_Left*100)

# plt.show()



plt.figure(figsize=(14, 10))


plt.subplot(3, 1, 1)
#plt.plot(imu_data_back['Elapsed(s)'], imu_data_back['W(number)'],label='X Component Back', color='blue')
plt.plot(imu_data_right['Elapsed(s)'], imu_data_right['W(number)'],label='X Component Right', color='darkgreen')
plt.plot(imu_data_left['Elapsed(s)'], imu_data_left['W(number)'], label='X Component Left', color='darkviolet')
#plt.plot(imu_data_head['Elapsed(s)'], imu_data_head['W(number)'], label='W Component Head', color='r')
plt.title('X Value over Time of 1st Gait')
plt.xlabel('Elapsed Time (s)')
plt.ylabel('X Value')
plt.grid(True)
plt.legend()

# plt.subplot(3, 1, 4)
# plt.plot(imu_data_back['Elapsed(s)'], imu_data_back['Z (number)'], label='Z Component Back', color='blue')
# plt.plot(imu_data_right['Elapsed(s)'], imu_data_right['Z (number)'], label='Z Component Right', color='darkgreen')
# plt.plot(imu_data_left['Elapsed(s)'], imu_data_left['Z (number)'], label='Z Component Left', color='darkviolet')
# #plt.plot(imu_data_head['Elapsed(s)'], imu_data_head['Z (number)'], label='Z Component Head', color='r')
# plt.title('Z Value over Time of 4th Old Standing')
# plt.xlabel('Elapsed Time (s)')
# plt.ylabel('Z Value')
# plt.grid(True)
# plt.legend()

plt.subplot(3, 1, 2)
#plt.plot(imu_data_back['Elapsed(s)'], imu_data_back['X(number)'], label='Y Component Back', color='blue')
plt.plot(imu_data_right['Elapsed(s)'], imu_data_right['X(number)'], label='Y Component Right', color='darkgreen')
plt.plot(imu_data_left['Elapsed(s)'], imu_data_left['X(number)'], label='Y Component Left', color='darkviolet')
#plt.plot(imu_data_head['Elapsed(s)'], imu_data_head['X(number)'], label='X Component Head', color='r')
plt.title('Y Value over Time of 1st Gait')
plt.xlabel('Elapsed Time (s)')
plt.ylabel('Y Value')
plt.grid(True)
plt.legend()

plt.subplot(3, 1, 3)
#plt.plot(imu_data_back['Elapsed(s)'], imu_data_back['Y (number)'], label='Z Component Back', color='blue')
plt.plot(imu_data_right['Elapsed(s)'], imu_data_right['Y (number)'], label='Z Component Right', color='darkgreen')
plt.plot(imu_data_left['Elapsed(s)'], imu_data_left['Y (number)'], label='Z Component Left', color='darkviolet')
#plt.plot(imu_data_head['Elapsed(s)'], imu_data_head['Y (number)'], label='Y Component Head', color='r')
plt.title('Z Value over Time of 1st Gait')
plt.xlabel('Elapsed Time (s)')
plt.ylabel('Z Value')
plt.grid(True)
plt.legend()



plt.tight_layout()
plt.show()