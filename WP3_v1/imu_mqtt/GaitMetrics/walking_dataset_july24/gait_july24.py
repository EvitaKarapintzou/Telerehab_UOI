import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
from scipy.interpolate import UnivariateSpline
from scipy.signal import butter, filtfilt

# Function to apply a Butterworth low-pass filter
def butter_lowpass_filter(data, cutoff, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

#left_path = '/home/vtsakan/Telerehab_DSS/Telerehab_UOI/WP3/imu_mqtt/GaitMetrics/walking_dataset_july24/Evita/Oneway/01_2024-07-17_16_01_03/left_E25AD03D0194_2024-07-17_16_01_03.csv'
#right_path = '/home/vtsakan/Telerehab_DSS/Telerehab_UOI/WP3/imu_mqtt/GaitMetrics/walking_dataset_july24/Evita/Oneway/01_2024-07-17_16_01_03/right_FEAC84C53DE7_2024-07-17_16_01_03.csv'


left_path = '/home/vtsakan/Telerehab_DSS/Telerehab_UOI/WP3/imu_mqtt/GaitMetrics/walking_dataset_july24/Evita/Oneway/04_2024-07-17_16_10_18/left_E25AD03D0194_2024-07-17_16_10_18.csv'
right_path = '/home/vtsakan/Telerehab_DSS/Telerehab_UOI/WP3/imu_mqtt/GaitMetrics/walking_dataset_july24/Evita/Oneway/04_2024-07-17_16_10_18/right_FEAC84C53DE7_2024-07-17_16_10_18.csv'


left_imu = pd.read_csv(left_path)
right_imu = pd.read_csv(right_path)


# Convert the Timestamp column to datetime
left_imu['Timestamp'] = pd.to_datetime(left_imu['Timestamp'], unit='ms')
right_imu['Timestamp'] = pd.to_datetime(right_imu['Timestamp'], unit='ms')

# Sort dataframes by Timestamp and remove duplicates
left_imu = left_imu.sort_values(by='Timestamp').drop_duplicates(subset='Timestamp').reset_index(drop=True)
right_imu = right_imu.sort_values(by='Timestamp').drop_duplicates(subset='Timestamp').reset_index(drop=True)

# Ensure timestamps are strictly increasing
left_imu = left_imu[left_imu['Timestamp'].diff().dt.total_seconds() > 0]
right_imu = right_imu[right_imu['Timestamp'].diff().dt.total_seconds() > 0]

# Find the common time period
start_time = max(left_imu['Timestamp'].min(), right_imu['Timestamp'].min())
end_time = min(left_imu['Timestamp'].max(), right_imu['Timestamp'].max())

# Crop the dataframes to the common time period
left_imu = left_imu[(left_imu['Timestamp'] >= start_time) & (left_imu['Timestamp'] <= end_time)].reset_index(drop=True)
right_imu = right_imu[(right_imu['Timestamp'] >= start_time) & (right_imu['Timestamp'] <= end_time)].reset_index(drop=True)

print("Start Time:", start_time)
print("End Time:", end_time)
print("Left IMU Data Period After Cropping:", left_imu['Timestamp'].min(), "to", left_imu['Timestamp'].max())
print("Right IMU Data Period After Cropping:", right_imu['Timestamp'].min(), "to", right_imu['Timestamp'].max())

# Calculate the magnitude of the linear acceleration
left_imu['Magnitude'] = np.sqrt(left_imu['X(number)']**2 + left_imu['Y(number)']**2 + left_imu['Z (number)']**2)
right_imu['Magnitude'] = np.sqrt(right_imu['X(number)']**2 + right_imu['Y(number)']**2 + right_imu['Z (number)']**2)

# Apply a low-pass filter to the magnitude signals
fs = 100  # Sampling frequency (Hz)
cutoff = 3.0  # Cutoff frequency (Hz)

left_imu['Filtered_Magnitude'] = butter_lowpass_filter(left_imu['Magnitude'], cutoff, fs)
right_imu['Filtered_Magnitude'] = butter_lowpass_filter(right_imu['Magnitude'], cutoff, fs)

# Convert Timestamps to nanoseconds for spline fitting
left_timestamps_ns = left_imu['Timestamp'].astype(np.int64)
right_timestamps_ns = right_imu['Timestamp'].astype(np.int64)

# Create a common time series at 100 Hz within this timeframe
common_time = pd.date_range(start=start_time, end=end_time, freq='10ms')  # 100 Hz = 10ms intervals
common_time_ns = common_time.astype(np.int64)

# Fit a spline to the filtered magnitude signal of each leg
left_spline_filtered_magnitude = UnivariateSpline(left_timestamps_ns, left_imu['Filtered_Magnitude'], s=0)
right_spline_filtered_magnitude = UnivariateSpline(right_timestamps_ns, right_imu['Filtered_Magnitude'], s=0)

# Sample the spline at the time points of the common time series
left_filtered_magnitude_interpolated = left_spline_filtered_magnitude(common_time_ns)
right_filtered_magnitude_interpolated = right_spline_filtered_magnitude(common_time_ns)

# Plot the original, filtered, and spline-interpolated magnitude data for the left leg
plt.figure(figsize=(14, 6))
plt.plot(left_imu['Timestamp'], left_imu['Magnitude'], 'o', label='Left IMU Magnitude Original', color='blue')
plt.plot(left_imu['Timestamp'], left_imu['Filtered_Magnitude'], label='Left IMU Magnitude Filtered', color='green')
plt.plot(common_time, left_filtered_magnitude_interpolated, label='Left IMU Magnitude Spline', color='cyan')
plt.xlabel('Timestamp')
plt.ylabel('Linear Acceleration (Magnitude)')
plt.title('Left IMU Magnitude - Original, Filtered, and Spline')
plt.legend()
plt.grid(True)
plt.show()

# Plot the original, filtered, and spline-interpolated magnitude data for the right leg
plt.figure(figsize=(14, 6))
plt.plot(right_imu['Timestamp'], right_imu['Magnitude'], 'o', label='Right IMU Magnitude Original', color='red')
plt.plot(right_imu['Timestamp'], right_imu['Filtered_Magnitude'], label='Right IMU Magnitude Filtered', color='orange')
plt.plot(common_time, right_filtered_magnitude_interpolated, label='Right IMU Magnitude Spline', color='purple')
plt.xlabel('Timestamp')
plt.ylabel('Linear Acceleration (Magnitude)')
plt.title('Right IMU Magnitude - Original, Filtered, and Spline')
plt.legend()
plt.grid(True)
plt.show()

# Plot the spline-interpolated magnitude data for both legs
plt.figure(figsize=(14, 6))
plt.plot(common_time, left_filtered_magnitude_interpolated, label='Left IMU Magnitude Spline', color='blue')
plt.plot(common_time, right_filtered_magnitude_interpolated, label='Right IMU Magnitude Spline', color='red')
plt.xlabel('Timestamp')
plt.ylabel('Linear Acceleration (Magnitude)')
plt.title('Spline-Interpolated Linear Acceleration Magnitude - Left and Right IMU')
plt.legend()
plt.grid(True)
plt.show()

# Determine the time periods when the "left" spline is greater than the "right" and vice versa
left_greater = left_filtered_magnitude_interpolated > right_filtered_magnitude_interpolated
right_greater = right_filtered_magnitude_interpolated > left_filtered_magnitude_interpolated

# Create a step-wise plot for the comparison
plt.figure(figsize=(14, 6))
plt.plot(common_time, left_filtered_magnitude_interpolated, label='Left IMU Magnitude Spline', color='blue', alpha=0.5)
plt.plot(common_time, right_filtered_magnitude_interpolated, label='Right IMU Magnitude Spline', color='red', alpha=0.5)

# Highlight the periods where left is greater than right and vice versa
plt.fill_between(common_time, left_filtered_magnitude_interpolated, right_filtered_magnitude_interpolated,
                 where=left_greater, facecolor='blue', alpha=0.3, label='Left > Right')
plt.fill_between(common_time, left_filtered_magnitude_interpolated, right_filtered_magnitude_interpolated,
                 where=right_greater, facecolor='red', alpha=0.3, label='Right > Left')

plt.xlabel('Timestamp')
plt.ylabel('Linear Acceleration (Magnitude)')
plt.title('Spline-Interpolated Linear Acceleration Magnitude - Left and Right IMU with Highlighted Intervals')
plt.legend()
plt.grid(True)
plt.show()

from scipy.signal import find_peaks

# Detect intersection points
intersection_indices = np.where(np.diff(np.sign(left_filtered_magnitude_interpolated - right_filtered_magnitude_interpolated)))[0]
intersection_times = common_time[intersection_indices]

# Function to find local extrema (minima and maxima) between two points using find_peaks
def find_extrema_between(signal, start_idx, end_idx):
    local_segment = signal[start_idx:end_idx]
    peaks, _ = find_peaks(local_segment)
    troughs, _ = find_peaks(-local_segment)
    
    local_max = start_idx + peaks[np.argmax(local_segment[peaks])] if len(peaks) > 0 else None
    local_min = start_idx + troughs[np.argmin(local_segment[troughs])] if len(troughs) > 0 else None
    
    return local_min, local_max

# Find local minima and maxima between intersection points
left_minima_indices = []
left_maxima_indices = []
right_minima_indices = []
right_maxima_indices = []

for i in range(len(intersection_indices) - 1):
    start_idx = intersection_indices[i]
    end_idx = intersection_indices[i + 1]

    # Determine the signal behavior to find appropriate extrema
    left_min_idx, left_max_idx = find_extrema_between(left_filtered_magnitude_interpolated, start_idx, end_idx)
    right_min_idx, right_max_idx = find_extrema_between(right_filtered_magnitude_interpolated, start_idx, end_idx)
    
    # Ensure alternation of extrema detection
    if i % 2 == 0:
        if left_max_idx is not None and right_min_idx is not None:
            left_maxima_indices.append(left_max_idx)
            right_minima_indices.append(right_min_idx)
    else:
        if left_min_idx is not None and right_max_idx is not None:
            left_minima_indices.append(left_min_idx)
            right_maxima_indices.append(right_max_idx)

# Determine the gait phases
gait_phases = []
for i in range(len(intersection_times) - 1):
    start_time = intersection_times[i]
    end_time = intersection_times[i + 1]
    if np.mean(left_filtered_magnitude_interpolated[intersection_indices[i]:intersection_indices[i + 1]]) > np.mean(right_filtered_magnitude_interpolated[intersection_indices[i]:intersection_indices[i + 1]]):
        gait_phases.append(('Right Stance, Left Swing', start_time, end_time))
    else:
        gait_phases.append(('Left Stance, Right Swing', start_time, end_time))

# Calculate gait metrics
stride_times = []
step_times = []
stance_times = []
swing_times = []

for phase, start_time, end_time in gait_phases:
    duration = (end_time - start_time).total_seconds()
    if 'Left Swing' in phase:
        swing_times.append(duration)
    else:
        stance_times.append(duration)
    stride_times.append(duration)

# Correct calculation of step times
step_times = [time / 2 for time in stride_times]

# Correct calculation of cadence
total_duration = (common_time[-1] - common_time[0]).total_seconds()
total_steps = len(step_times) * 2  # Each stride corresponds to two steps
cadence = (total_steps / total_duration) * 60  # Steps per minute

# Plot the spline-interpolated magnitude data with gait events
plt.figure(figsize=(14, 6))
plt.plot(common_time, left_filtered_magnitude_interpolated, label='Left IMU Magnitude Spline', color='blue', alpha=0.5)


plt.plot(common_time, right_filtered_magnitude_interpolated, label='Right IMU Magnitude Spline', color='red', alpha=0.5)
'''
# Highlight the periods where left is greater than right and vice versa
plt.fill_between(common_time, left_filtered_magnitude_interpolated, right_filtered_magnitude_interpolated,
                 where=left_filtered_magnitude_interpolated > right_filtered_magnitude_interpolated, facecolor='blue', alpha=0.3, label='Left > Right')
plt.fill_between(common_time, left_filtered_magnitude_interpolated, right_filtered_magnitude_interpolated,
                 where=right_filtered_magnitude_interpolated > left_filtered_magnitude_interpolated, facecolor='red', alpha=0.3, label='Right > Left')
'''

# Mark the intersection points
plt.scatter(intersection_times, left_filtered_magnitude_interpolated[intersection_indices], color='black', zorder=5)

# Mark local minima (heel strikes) and maxima (toe offs and swing peaks)
plt.scatter(common_time[left_minima_indices], left_filtered_magnitude_interpolated[left_minima_indices], color='green', zorder=5, label='Left Heel Strikes')
plt.scatter(common_time[left_maxima_indices], left_filtered_magnitude_interpolated[left_maxima_indices], color='cyan', zorder=5, label='Left Toe Offs/Swing Peaks')
plt.scatter(common_time[right_minima_indices], right_filtered_magnitude_interpolated[right_minima_indices], color='yellow', zorder=5, label='Right Heel Strikes')
plt.scatter(common_time[right_maxima_indices], right_filtered_magnitude_interpolated[right_maxima_indices], color='magenta', zorder=5, label='Right Toe Offs/Swing Peaks')

# Annotate gait events
for phase, start_time, end_time in gait_phases:
    mid_time = pd.Timestamp((start_time.timestamp() + end_time.timestamp()) / 2, unit='s')
    plt.axvspan(start_time, end_time, color='yellow' if 'Left Swing' in phase else 'green', alpha=0.2)
    plt.text(mid_time, plt.ylim()[1] - 0.1 * plt.ylim()[1], phase, horizontalalignment='center', verticalalignment='top', fontsize=8, rotation=45)

plt.xlabel('Timestamp')
plt.ylabel('Linear Acceleration (Magnitude)')
plt.title('Spline-Interpolated Linear Acceleration Magnitude - Gait Events')
plt.legend()
plt.grid(True)
plt.show()

# Print gait metrics
print(f"Stride Times: {stride_times}")
print(f"Step Times: {step_times}")
print(f"Stance Times: {stance_times}")
print(f"Swing Times: {swing_times}")
print(f"Cadence: {cadence} steps/minute")

# Print gait events for reference
for phase, start_time, end_time in gait_phases:
    print(f"{phase}: {start_time} to {end_time}")


for i in range(len(intersection_indices) - 1):
    start_idx = intersection_indices[i]
    end_idx = intersection_indices[i + 1]

    left_min_idx, left_max_idx = find_extrema_between(left_filtered_magnitude_interpolated, start_idx, end_idx)
    right_min_idx, right_max_idx = find_extrema_between(right_filtered_magnitude_interpolated, start_idx, end_idx)
    
    if left_max_idx is not None and right_min_idx is not None:
        left_maxima_indices.append(left_max_idx)
        right_minima_indices.append(right_min_idx)
    elif left_min_idx is not None and right_max_idx is not None:
        left_minima_indices.append(left_min_idx)
        right_maxima_indices.append(right_max_idx)

# Determine the gait phases
gait_phases = []
for i in range(len(intersection_times) - 1):
    start_time = intersection_times[i]
    end_time = intersection_times[i + 1]
    if np.mean(left_filtered_magnitude_interpolated[intersection_indices[i]:intersection_indices[i + 1]]) > np.mean(right_filtered_magnitude_interpolated[intersection_indices[i]:intersection_indices[i + 1]]):
        gait_phases.append(('Right Stance, Left Swing', start_time, end_time))
    else:
        gait_phases.append(('Left Stance, Right Swing', start_time, end_time))

# Calculate gait metrics
stride_times = []
step_times = []
stance_times = []
swing_times = []
toe_off_times = []
swing_peak_times = []

for phase, start_time, end_time in gait_phases:
    duration = (end_time - start_time).total_seconds()
    if 'Left Swing' in phase:
        swing_times.append(duration)
    else:
        stance_times.append(duration)
    stride_times.append(duration)
    
    # Calculate toe off and swing peak times
    if 'Left Swing' in phase:
        # Left Swing Phase
        for idx in left_maxima_indices:
            if start_time <= common_time[idx] <= end_time:
                swing_peak_times.append(common_time[idx])
        for idx in right_minima_indices:
            if start_time <= common_time[idx] <= end_time:
                toe_off_times.append(common_time[idx])
    else:
        # Right Swing Phase
        for idx in right_maxima_indices:
            if start_time <= common_time[idx] <= end_time:
                swing_peak_times.append(common_time[idx])
        for idx in left_minima_indices:
            if start_time <= common_time[idx] <= end_time:
                toe_off_times.append(common_time[idx])

# Correct calculation of step times
step_times = [time / 2 for time in stride_times]

# Correct calculation of cadence
total_duration = (common_time[-1] - common_time[0]).total_seconds()
total_steps = len(step_times) * 2  # Each stride corresponds to two steps
cadence = (total_steps / total_duration) * 60  # Steps per minute

# Plot the spline-interpolated magnitude data with gait events
plt.figure(figsize=(14, 6))
plt.plot(common_time, left_filtered_magnitude_interpolated, label='Left IMU Magnitude Spline', color='blue', alpha=0.5)
plt.plot(common_time, right_filtered_magnitude_interpolated, label='Right IMU Magnitude Spline', color='red', alpha=0.5)

# Highlight the periods where left is greater than right and vice versa
plt.fill_between(common_time, left_filtered_magnitude_interpolated, right_filtered_magnitude_interpolated,
                 where=left_filtered_magnitude_interpolated > right_filtered_magnitude_interpolated, facecolor='blue', alpha=0.3, label='Left > Right')
plt.fill_between(common_time, left_filtered_magnitude_interpolated, right_filtered_magnitude_interpolated,
                 where=right_filtered_magnitude_interpolated > left_filtered_magnitude_interpolated, facecolor='red', alpha=0.3, label='Right > Left')

# Mark the intersection points
plt.scatter(intersection_times, left_filtered_magnitude_interpolated[intersection_indices], color='black', zorder=5)

# Mark local minima (heel strikes), maxima (toe offs), and swing peaks
plt.scatter(common_time[left_minima_indices], left_filtered_magnitude_interpolated[left_minima_indices], color='green', zorder=5, label='Left Heel Strikes')
plt.scatter(common_time[left_maxima_indices], left_filtered_magnitude_interpolated[left_maxima_indices], color='cyan', zorder=5, label='Left Swing Peaks')
plt.scatter(common_time[right_minima_indices], right_filtered_magnitude_interpolated[right_minima_indices], color='yellow', zorder=5, label='Right Heel Strikes')
plt.scatter(common_time[right_maxima_indices], right_filtered_magnitude_interpolated[right_maxima_indices], color='magenta', zorder=5, label='Right Swing Peaks')
plt.scatter(toe_off_times, [0] * len(toe_off_times), color='purple', zorder=5, label='Toe Offs', marker='x')
plt.scatter(swing_peak_times, [1] * len(swing_peak_times), color='orange', zorder=5, label='Swing Peaks', marker='o')

# Annotate gait events
for phase, start_time, end_time in gait_phases:
    mid_time = pd.Timestamp((start_time.timestamp() + end_time.timestamp()) / 2, unit='s')
    plt.axvspan(start_time, end_time, color='yellow' if 'Left Swing' in phase else 'green', alpha=0.2)
    plt.text(mid_time, plt.ylim()[1] - 0.1 * plt.ylim()[1], phase, horizontalalignment='center', verticalalignment='top', fontsize=8, rotation=45)

plt.xlabel('Timestamp')
plt.ylabel('Linear Acceleration (Magnitude)')
plt.title('Spline-Interpolated Linear Acceleration Magnitude - Gait Events with Toe Off and Swing Peaks')
plt.legend()
plt.grid(True)
plt.show()

# Calculate overall gait metrics
stride_times = [(end - start).total_seconds() for start, end in zip(intersection_times[:-1], intersection_times[1:])]
step_times = [time / 2 for time in stride_times]
cadence = (len(step_times) / ((common_time[-1] - common_time[0]).total_seconds())) * 60  # Steps per minute
gait_cycle_times = stride_times  # Each stride is one gait cycle

# Calculate individual foot gait metrics
left_stance_times = []
right_stance_times = []
left_swing_times = []
right_swing_times = []
double_support_times = []
single_support_times = []
left_toe_off_times = []
right_toe_off_times = []
left_swing_peak_times = []
right_swing_peak_times = []

# Calculate metrics for each phase
for phase, start_time, end_time in gait_phases:
    duration = (end_time - start_time).total_seconds()
    if 'Left Swing' in phase:
        left_swing_times.append(duration)
        # Calculate toe off and swing peak times
        for idx in left_maxima_indices:
            if start_time <= common_time[idx] <= end_time:
                left_swing_peak_times.append((common_time[idx] - start_time).total_seconds())
        for idx in right_minima_indices:
            if start_time <= common_time[idx] <= end_time:
                right_toe_off_times.append((common_time[idx] - start_time).total_seconds())
    else:
        right_swing_times.append(duration)
        # Calculate toe off and swing peak times
        for idx in right_maxima_indices:
            if start_time <= common_time[idx] <= end_time:
                right_swing_peak_times.append((common_time[idx] - start_time).total_seconds())
        for idx in left_minima_indices:
            if start_time <= common_time[idx] <= end_time:
                left_toe_off_times.append((common_time[idx] - start_time).total_seconds())

# Calculate stance times
for i in range(0, len(intersection_times) - 1, 2):
    left_stance_times.append((intersection_times[i+1] - intersection_times[i]).total_seconds())
    if i + 2 < len(intersection_times):
        right_stance_times.append((intersection_times[i+2] - intersection_times[i+1]).total_seconds())

# Calculate double support and single support times
for i in range(0, len(gait_phases) - 1, 2):
    left_phase_start, left_phase_end = gait_phases[i][1], gait_phases[i][2]
    right_phase_start, right_phase_end = gait_phases[i+1][1], gait_phases[i+1][2]
    
    double_support_start = max(left_phase_start, right_phase_start)
    double_support_end = min(left_phase_end, right_phase_end)
    double_support_duration = (double_support_end - double_support_start).total_seconds()
    double_support_times.append(double_support_duration)
    
    single_support_duration = (left_phase_end - left_phase_start).total_seconds() - double_support_duration
    single_support_times.append(single_support_duration)

# Print overall gait metrics
print(f"Stride Times: {stride_times}")
print(f"Step Times: {step_times}")
print(f"Cadence: {cadence} steps/minute")
print(f"Gait Cycle Times: {gait_cycle_times}")

# Print individual foot gait metrics
print(f"Left Stance Times: {left_stance_times}")
print(f"Right Stance Times: {right_stance_times}")
print(f"Left Swing Times: {left_swing_times}")
print(f"Right Swing Times: {right_swing_times}")
print(f"Double Support Times: {double_support_times}")
print(f"Single Support Times: {single_support_times}")
print(f"Left Toe Off Times: {left_toe_off_times}")
print(f"Right Toe Off Times: {right_toe_off_times}")
print(f"Left Swing Peak Times: {left_swing_peak_times}")
print(f"Right Swing Peak Times: {right_swing_peak_times}")

# Plotting the gait events
plt.figure(figsize=(14, 6))
plt.plot(common_time, left_filtered_magnitude_interpolated, label='Left IMU Magnitude Spline', color='blue', alpha=0.5)
plt.plot(common_time, right_filtered_magnitude_interpolated, label='Right IMU Magnitude Spline', color='red', alpha=0.5)

# Highlight the periods where left is greater than right and vice versa
plt.fill_between(common_time, left_filtered_magnitude_interpolated, right_filtered_magnitude_interpolated,
                 where=left_filtered_magnitude_interpolated > right_filtered_magnitude_interpolated, facecolor='blue', alpha=0.3, label='Left > Right')
plt.fill_between(common_time, left_filtered_magnitude_interpolated, right_filtered_magnitude_interpolated,
                 where=right_filtered_magnitude_interpolated > left_filtered_magnitude_interpolated, facecolor='red', alpha=0.3, label='Right > Left')

# Mark the intersection points
plt.scatter(intersection_times, left_filtered_magnitude_interpolated[intersection_indices], color='black', zorder=5)

# Mark local minima (heel strikes), maxima (toe offs), and swing peaks
plt.scatter(common_time[left_minima_indices], left_filtered_magnitude_interpolated[left_minima_indices], color='green', zorder=5, label='Left Heel Strikes')
plt.scatter(common_time[left_maxima_indices], left_filtered_magnitude_interpolated[left_maxima_indices], color='cyan', zorder=5, label='Left Swing Peaks')
plt.scatter(common_time[right_minima_indices], right_filtered_magnitude_interpolated[right_minima_indices], color='yellow', zorder=5, label='Right Heel Strikes')
plt.scatter(common_time[right_maxima_indices], right_filtered_magnitude_interpolated[right_maxima_indices], color='magenta', zorder=5, label='Right Swing Peaks')
plt.scatter(toe_off_times, [0] * len(toe_off_times), color='purple', zorder=5, label='Toe Offs', marker='x')
plt.scatter(swing_peak_times, [1] * len(swing_peak_times), color='orange', zorder=5, label='Swing Peaks', marker='o')

# Annotate gait events
for phase, start_time, end_time in gait_phases:
    mid_time = pd.Timestamp((start_time.timestamp() + end_time.timestamp()) / 2, unit='s')
    plt.axvspan(start_time, end_time, color='yellow' if 'Left Swing' in phase else 'green', alpha=0.2)
    plt.text(mid_time, plt.ylim()[1] - 0.1 * plt.ylim()[1], phase, horizontalalignment='center', verticalalignment='top', fontsize=8, rotation=45)

plt.xlabel('Timestamp')
plt.ylabel('Linear Acceleration (Magnitude)')
plt.title('Spline-Interpolated Linear Acceleration Magnitude - Gait Events')
plt.legend()
plt.grid(True)
plt.show()