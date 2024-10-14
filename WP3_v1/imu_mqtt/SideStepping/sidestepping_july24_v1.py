import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
from scipy.interpolate import UnivariateSpline
from scipy.signal import butter, filtfilt

from scipy.optimize import brentq
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
from scipy.interpolate import UnivariateSpline
from scipy.signal import butter, filtfilt
# Define thresholds
intersection_distance_threshold = 0.2  # seconds
signal_magnitude_threshold = 0.35  # magnitude
peaks_distance_threshold = 0.5 * 100  # 0.7 seconds converted to samples


# Function to apply a Butterworth low-pass filter
def butter_lowpass_filter(data, cutoff, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

left_path = '/home/vtsakan/Telerehab_DSS/Telerehab_UOI/WP3/imu_mqtt/SideStepping/Chrysa/05_2024-07-23_16:14:24/left_FEAC84C53DE7_2024-07-23_16:14:24.csv'
right_path = '/home/vtsakan/Telerehab_DSS/Telerehab_UOI/WP3/imu_mqtt/SideStepping/Chrysa/05_2024-07-23_16:14:24/right_E25AD03D0194_2024-07-23_16:14:24.csv'

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

# Find peaks in the filtered magnitude signals, ensuring peaks are at least 0.7 seconds apart
left_peaks, _ = find_peaks(left_filtered_magnitude_interpolated, height=signal_magnitude_threshold, distance=peaks_distance_threshold)
right_peaks, _ = find_peaks(right_filtered_magnitude_interpolated, height=signal_magnitude_threshold, distance=peaks_distance_threshold)

# Combine peaks into a single list with labels to identify which IMU they belong to
peak_times = np.concatenate([common_time[left_peaks], common_time[right_peaks]])
peak_labels = ['left'] * len(left_peaks) + ['right'] * len(right_peaks)

# Sort peaks by time
sorted_indices = np.argsort(peak_times)
peak_times = peak_times[sorted_indices]
peak_labels = np.array(peak_labels)[sorted_indices]

# Find all minima in the left and right filtered magnitude signals separately
left_minima_indices, _ = find_peaks(-left_filtered_magnitude_interpolated, distance=peaks_distance_threshold)
right_minima_indices, _ = find_peaks(-right_filtered_magnitude_interpolated, distance=peaks_distance_threshold)

left_minima_times = common_time_ns[left_minima_indices]
right_minima_times = common_time_ns[right_minima_indices]

left_minima_values = left_filtered_magnitude_interpolated[left_minima_indices]
right_minima_values = right_filtered_magnitude_interpolated[right_minima_indices]

# Identify the point where the alternating pattern breaks
change_point = None
for i in range(1, len(peak_labels) - 1):
    if peak_labels[i] == peak_labels[i - 1] == peak_labels[i + 1]:
        # Determine if the break is in the left or right signal
        if peak_labels[i] == 'left':
            prev_peak_time_ns = peak_times[i - 1].astype(np.int64)
            next_peak_time_ns = peak_times[i + 1].astype(np.int64)
            min_between_peaks = left_minima_times[(left_minima_times > prev_peak_time_ns) & (left_minima_times < next_peak_time_ns)]
            if len(min_between_peaks) > 0:
                change_point = pd.to_datetime(min_between_peaks[np.argmin(left_minima_values[(left_minima_times > prev_peak_time_ns) & (left_minima_times < next_peak_time_ns)])])
        else:
            prev_peak_time_ns = peak_times[i - 1].astype(np.int64)
            next_peak_time_ns = peak_times[i + 1].astype(np.int64)
            min_between_peaks = right_minima_times[(right_minima_times > prev_peak_time_ns) & (right_minima_times < next_peak_time_ns)]
            if len(min_between_peaks) > 0:
                change_point = pd.to_datetime(min_between_peaks[np.argmin(right_minima_values[(right_minima_times > prev_peak_time_ns) & (right_minima_times < next_peak_time_ns)])])
        break

if change_point is not None:
    print("Change in direction detected at:", change_point)
else:
    print("No significant change in direction detected")

# Visualize the change point on the filtered magnitude data
plt.figure(figsize=(14, 6))
plt.plot(common_time, left_filtered_magnitude_interpolated, label='Left IMU Magnitude Spline', color='blue')
plt.plot(common_time[left_peaks], left_filtered_magnitude_interpolated[left_peaks], 'x', label='Left IMU Peaks', color='cyan')
plt.plot(common_time, right_filtered_magnitude_interpolated, label='Right IMU Magnitude Spline', color='red')
plt.plot(common_time[right_peaks], right_filtered_magnitude_interpolated[right_peaks], 'x', label='Right IMU Peaks', color='purple')
plt.plot(common_time[left_minima_indices], left_filtered_magnitude_interpolated[left_minima_indices], 'o', label='Left Minima', color='black')
plt.plot(common_time[right_minima_indices], right_filtered_magnitude_interpolated[right_minima_indices], 'o', label='Right Minima', color='green')
if change_point is not None:
    plt.axvline(change_point, color='green', linestyle='--', label='Change Direction Point')
plt.xlabel('Timestamp')
plt.ylabel('Linear Acceleration (Magnitude)')
plt.title('Identified Steps and Change Direction in Linear Acceleration Magnitude')
plt.legend()
plt.grid(True)
plt.show()

# Split data into before and after change point
if change_point is not None:
    change_point_ns = change_point.value
    before_indices = common_time_ns < change_point_ns
    after_indices = common_time_ns >= change_point_ns
    
    left_peaks_before = [peak for peak in left_peaks if before_indices[peak]]
    right_peaks_before = [peak for peak in right_peaks if before_indices[peak]]
    left_peaks_after = [peak for peak in left_peaks if after_indices[peak]]
    right_peaks_after = [peak for peak in right_peaks if after_indices[peak]]

    left_minima_before = left_minima_indices[before_indices[left_minima_indices]]
    right_minima_before = right_minima_indices[before_indices[right_minima_indices]]
    left_minima_after = left_minima_indices[after_indices[left_minima_indices]]
    right_minima_after = right_minima_indices[after_indices[right_minima_indices]]

    # Calculate metrics before and after change point
    def calculate_metrics(peaks, minima):
        step_count = len(peaks)
        step_duration = np.diff(common_time_ns[peaks]) / 1e9  # Convert from ns to s
        step_frequency = step_count / ((common_time_ns[peaks][-1] - common_time_ns[peaks][0]) / 1e9 / 60)  # Steps per minute
        step_duration_mean = np.mean(step_duration)
        step_duration_std = np.std(step_duration)
        return step_count, step_frequency, step_duration_mean, step_duration_std

    left_metrics_before = calculate_metrics(left_peaks_before, left_minima_before)
    right_metrics_before = calculate_metrics(right_peaks_before, right_minima_before)
    left_metrics_after = calculate_metrics(left_peaks_after, left_minima_after)
    right_metrics_after = calculate_metrics(right_peaks_after, right_minima_after)

    # Calculate symmetry and consistency before and after change point
    symmetry_before = abs(left_metrics_before[0] - right_metrics_before[0])
    consistency_before = (left_metrics_before[3] + right_metrics_before[3]) / 2
    symmetry_after = abs(left_metrics_after[0] - right_metrics_after[0])
    consistency_after = (left_metrics_after[3] + right_metrics_after[3]) / 2

    # Print metrics
    print("Metrics before change point:")
    print("Left Step Count:", left_metrics_before[0])
    print("Right Step Count:", right_metrics_before[0])
    print("Left Step Frequency (steps/min):", left_metrics_before[1])
    print("Right Step Frequency (steps/min):", right_metrics_before[1])
    print("Left Step Duration Mean (s):", left_metrics_before[2])
    print("Right Step Duration Mean (s):", right_metrics_before[2])
    print("Left Step Duration Std Dev (s):", left_metrics_before[3])
    print("Right Step Duration Std Dev (s):", right_metrics_before[3])
    print("Symmetry (difference in step count):", symmetry_before)
    print("Consistency (mean of std dev in step duration):", consistency_before)

    print("\nMetrics after change point:")
    print("Left Step Count:", left_metrics_after[0])
    print("Right Step Count:", right_metrics_after[0])
    print("Left Step Frequency (steps/min):", left_metrics_after[1])
    print("Right Step Frequency (steps/min):", right_metrics_after[1])
    print("Left Step Duration Mean (s):", left_metrics_after[2])
    print("Right Step Duration Mean (s):", right_metrics_after[2])
    print("Left Step Duration Std Dev (s):", left_metrics_after[3])
    print("Right Step Duration Std Dev (s):", right_metrics_after[3])
    print("Symmetry (difference in step count):", symmetry_after)
    print("Consistency (mean of std dev in step duration):", consistency_after)

    # Compare metrics between directions
    step_count_diff = abs((left_metrics_before[0] + left_metrics_after[0]) - (right_metrics_before[0] + right_metrics_after[0]))
    step_frequency_diff = abs((left_metrics_before[1] + left_metrics_after[1]) - (right_metrics_before[1] + right_metrics_after[1]))
    step_duration_diff = abs((left_metrics_before[2] + left_metrics_after[2]) - (right_metrics_before[2] + right_metrics_after[2]))
    step_std_dev_diff = abs((left_metrics_before[3] + left_metrics_after[3]) - (right_metrics_before[3] + right_metrics_after[3]))

    print("\nComparison of metrics between directions:")
    print("Step Count Difference:", step_count_diff)
    print("Step Frequency Difference (steps/min):", step_frequency_diff)
    print("Step Duration Mean Difference (s):", step_duration_diff)
    print("Step Duration Std Dev Difference (s):", step_std_dev_diff)
else:
    print("No change point detected, metrics will not be split.")


# Function to find the intersection points
def find_intersections(x, y1, y2):
    intersections = []
    for i in range(len(x) - 1):
        if (y1[i] - y2[i]) * (y1[i + 1] - y2[i + 1]) < 0:
            root = brentq(lambda t: np.interp(t, x, y1) - np.interp(t, x, y2), x[i], x[i + 1])
            intersections.append(root)
    return intersections

# Find intersection points
intersection_points = find_intersections(common_time_ns, left_filtered_magnitude_interpolated, right_filtered_magnitude_interpolated)

# Filter intersection points to ensure they are at least 0.5 seconds apart
min_distance_ns = 0.5 * 1e9  # 0.5 seconds in nanoseconds
filtered_intersections = []
for point in intersection_points:
    if len(filtered_intersections) == 0 or (point - filtered_intersections[-1]) >= min_distance_ns:
        filtered_intersections.append(point)

# Convert intersection points to datetime
intersection_points_dt = [pd.to_datetime(int_point) for int_point in filtered_intersections]

# Print intersection points
print("Intersection Points:", intersection_points_dt)

# Plot intersection points on the filtered magnitude data
plt.figure(figsize=(14, 6))
plt.plot(common_time, left_filtered_magnitude_interpolated, label='Left IMU Magnitude Spline', color='blue')
plt.plot(common_time, right_filtered_magnitude_interpolated, label='Right IMU Magnitude Spline', color='red')
for int_point in intersection_points_dt:
    plt.axvline(int_point, color='orange', linestyle='--', label='Intersection Point')
plt.xlabel('Timestamp')
plt.ylabel('Linear Acceleration (Magnitude)')
plt.title('Intersection Points in Linear Acceleration Magnitude')
plt.legend()
plt.grid(True)
plt.show()

# Define the height threshold
height_threshold = 0.1

# Find peaks in the filtered magnitude signals, ensuring peaks are at least 0.7 seconds apart
left_peaks, _ = find_peaks(left_filtered_magnitude_interpolated, distance=peaks_distance_threshold)
right_peaks, _ = find_peaks(right_filtered_magnitude_interpolated, distance=peaks_distance_threshold)

# Filter out peaks lower than the height threshold
left_peaks = [peak for peak in left_peaks if left_filtered_magnitude_interpolated[peak] >= height_threshold]
right_peaks = [peak for peak in right_peaks if right_filtered_magnitude_interpolated[peak] >= height_threshold]

# Combine peaks into a single list with labels to identify which IMU they belong to
peak_times = np.concatenate([common_time[left_peaks], common_time[right_peaks]])
peak_labels = ['left'] * len(left_peaks) + ['right'] * len(right_peaks)

# Sort peaks by time
sorted_indices = np.argsort(peak_times)
peak_times = peak_times[sorted_indices]
peak_labels = np.array(peak_labels)[sorted_indices]


# Determine which foot has the first maximum over 0.1
if len(left_peaks) > 0 and len(right_peaks) > 0:
    first_left_peak = common_time[left_peaks[0]]
    first_right_peak = common_time[right_peaks[0]]
    use_left = first_left_peak < first_right_peak
else:
    use_left = len(left_peaks) > 0  # Default to left if only left peaks exist



# Ensure only one maximum between two intersection points alternately, keeping the larger maximum


# Split data into before and after change point
if change_point is not None:
    change_point_ns = change_point.value
    before_indices = common_time_ns < change_point_ns
    after_indices = common_time_ns >= change_point_ns

    # Process for before change point
    filtered_intersections_before = [point for point in filtered_intersections if point < change_point_ns]
    
    filtered_left_peaks_before = []
    filtered_right_peaks_before = []

    for i in range(len(filtered_intersections_before) - 1):
        start = filtered_intersections_before[i]
        end = filtered_intersections_before[i + 1]
        between_indices = (common_time_ns >= start) & (common_time_ns <= end)
        left_max_in_between = find_peaks(left_filtered_magnitude_interpolated[between_indices])[0]
        right_max_in_between = find_peaks(right_filtered_magnitude_interpolated[between_indices])[0]

        # Filter out peaks lower than the height threshold
        left_max_in_between = left_max_in_between[left_filtered_magnitude_interpolated[between_indices][left_max_in_between] >= height_threshold]
        right_max_in_between = right_max_in_between[right_filtered_magnitude_interpolated[between_indices][right_max_in_between] >= height_threshold]

        if use_left and len(left_max_in_between) > 0:
            largest_left_peak = left_max_in_between[np.argmax(left_filtered_magnitude_interpolated[between_indices][left_max_in_between])]
            filtered_left_peaks_before.extend(common_time_ns[between_indices][[largest_left_peak]])
            use_left = False
        elif not use_left and len(right_max_in_between) > 0:
            largest_right_peak = right_max_in_between[np.argmax(right_filtered_magnitude_interpolated[between_indices][right_max_in_between])]
            filtered_right_peaks_before.extend(common_time_ns[between_indices][[largest_right_peak]])
            use_left = True

    # Recalculate use_left after the change point
    left_peaks_after_change = [peak for peak in left_peaks if common_time[peak] >= change_point]
    right_peaks_after_change = [peak for peak in right_peaks if common_time[peak] >= change_point]

    if len(left_peaks_after_change) > 0 and len(right_peaks_after_change) > 0:
        first_left_peak_after = common_time[left_peaks_after_change[0]]
        first_right_peak_after = common_time[right_peaks_after_change[0]]
        use_left = first_left_peak_after < first_right_peak_after
    else:
        use_left = len(left_peaks_after_change) > 0  # Default to left if only left peaks exist

    # Process for after change point
    filtered_intersections_after = [point for point in filtered_intersections if point >= change_point_ns]
    
    filtered_left_peaks_after = []
    filtered_right_peaks_after = []

    # Initial part to be analyzed between change_point and first intersection point
    if len(filtered_intersections_after) > 0:
        start = change_point_ns
        end = filtered_intersections_after[0]
        between_indices = (common_time_ns >= start) & (common_time_ns <= end)
        left_max_in_between = find_peaks(left_filtered_magnitude_interpolated[between_indices])[0]
        right_max_in_between = find_peaks(right_filtered_magnitude_interpolated[between_indices])[0]

        # Filter out peaks lower than the height threshold
        left_max_in_between = left_max_in_between[left_filtered_magnitude_interpolated[between_indices][left_max_in_between] >= height_threshold]
        right_max_in_between = right_max_in_between[right_filtered_magnitude_interpolated[between_indices][right_max_in_between] >= height_threshold]

        if use_left and len(left_max_in_between) > 0:
            largest_left_peak = left_max_in_between[np.argmax(left_filtered_magnitude_interpolated[between_indices][left_max_in_between])]
            filtered_left_peaks_after.extend(common_time_ns[between_indices][[largest_left_peak]])
            use_left = False
        elif not use_left and len(right_max_in_between) > 0:
            largest_right_peak = right_max_in_between[np.argmax(right_filtered_magnitude_interpolated[between_indices][right_max_in_between])]
            filtered_right_peaks_after.extend(common_time_ns[between_indices][[largest_right_peak]])
            use_left = True

        # Process the rest of the intervals
        for i in range(len(filtered_intersections_after) - 1):
            start = filtered_intersections_after[i]
            end = filtered_intersections_after[i + 1]
            between_indices = (common_time_ns >= start) & (common_time_ns <= end)
            left_max_in_between = find_peaks(left_filtered_magnitude_interpolated[between_indices])[0]
            right_max_in_between = find_peaks(right_filtered_magnitude_interpolated[between_indices])[0]

            # Filter out peaks lower than the height threshold
            left_max_in_between = left_max_in_between[left_filtered_magnitude_interpolated[between_indices][left_max_in_between] >= height_threshold]
            right_max_in_between = right_max_in_between[right_filtered_magnitude_interpolated[between_indices][right_max_in_between] >= height_threshold]

            if use_left and len(left_max_in_between) > 0:
                largest_left_peak = left_max_in_between[np.argmax(left_filtered_magnitude_interpolated[between_indices][left_max_in_between])]
                filtered_left_peaks_after.extend(common_time_ns[between_indices][[largest_left_peak]])
                use_left = False
            elif not use_left and len(right_max_in_between) > 0:
                largest_right_peak = right_max_in_between[np.argmax(right_filtered_magnitude_interpolated[between_indices][right_max_in_between])]
                filtered_right_peaks_after.extend(common_time_ns[between_indices][[largest_right_peak]])
                use_left = True

    # Combine filtered peaks before and after
    filtered_left_peaks = np.concatenate([filtered_left_peaks_before, filtered_left_peaks_after])
    filtered_right_peaks = np.concatenate([filtered_right_peaks_before, filtered_right_peaks_after])

    # Convert filtered peaks back to indices
    filtered_left_peaks_indices = [np.searchsorted(common_time_ns, peak) for peak in filtered_left_peaks]
    filtered_right_peaks_indices = [np.searchsorted(common_time_ns, peak) for peak in filtered_right_peaks]

    # Plot the filtered maxima and intersection points on the filtered magnitude data
    plt.figure(figsize=(14, 6))
    plt.plot(common_time, left_filtered_magnitude_interpolated, label='Left IMU Magnitude Spline', color='blue')
    plt.plot(common_time[filtered_left_peaks_indices], left_filtered_magnitude_interpolated[filtered_left_peaks_indices], 'x', label='Filtered Left IMU Peaks', color='cyan')
    plt.plot(common_time, right_filtered_magnitude_interpolated, label='Right IMU Magnitude Spline', color='red')
    plt.plot(common_time[filtered_right_peaks_indices], right_filtered_magnitude_interpolated[filtered_right_peaks_indices], 'x', label='Filtered Right IMU Peaks', color='purple')
    for int_point in intersection_points_dt:
        plt.axvline(int_point, color='orange', linestyle='--', label='Intersection Point')
    if change_point is not None:
        plt.axvline(change_point, color='green', linestyle='--', label='Change Direction Point')
    plt.xlabel('Timestamp')
    plt.ylabel('Linear Acceleration (Magnitude)')
    plt.title('Filtered Maxima and Intersection Points in Linear Acceleration Magnitude')
    plt.legend()
    plt.grid(True)
    plt.show()

else:
    print("No change point detected, metrics will not be split.")

# Calculate the metrics using the latest filtered maxima and minima

# Split peaks into before and after change point
left_peaks_before = [peak for peak in filtered_left_peaks_indices if common_time_ns[peak] < change_point_ns]
right_peaks_before = [peak for peak in filtered_right_peaks_indices if common_time_ns[peak] < change_point_ns]
left_peaks_after = [peak for peak in filtered_left_peaks_indices if common_time_ns[peak] >= change_point_ns]
right_peaks_after = [peak for peak in filtered_right_peaks_indices if common_time_ns[peak] >= change_point_ns]

# Split minima into before and after change point
left_minima_before = [minima for minima in left_minima_indices if common_time_ns[minima] < change_point_ns]
right_minima_before = [minima for minima in right_minima_indices if common_time_ns[minima] < change_point_ns]
left_minima_after = [minima for minima in left_minima_indices if common_time_ns[minima] >= change_point_ns]
right_minima_after = [minima for minima in right_minima_indices if common_time_ns[minima] >= change_point_ns]

# Calculate metrics
def calculate_metrics(peaks, minima):
    step_count = len(peaks)
    if step_count > 1:
        step_duration = np.diff(common_time_ns[peaks]) / 1e9  # Convert from ns to s
        step_frequency = step_count / ((common_time_ns[peaks][-1] - common_time_ns[peaks][0]) / 1e9 / 60)  # Steps per minute
        step_duration_mean = np.mean(step_duration)
        step_duration_std = np.std(step_duration)
    else:
        step_frequency = 0
        step_duration_mean = 0
        step_duration_std = 0
    return step_count, step_frequency, step_duration_mean, step_duration_std

left_metrics_before = calculate_metrics(left_peaks_before, left_minima_before)
right_metrics_before = calculate_metrics(right_peaks_before, right_minima_before)
left_metrics_after = calculate_metrics(left_peaks_after, left_minima_after)
right_metrics_after = calculate_metrics(right_peaks_after, right_minima_after)

# Calculate symmetry and consistency before and after change point
symmetry_before = abs(left_metrics_before[0] - right_metrics_before[0])
consistency_before = (left_metrics_before[3] + right_metrics_before[3]) / 2
symmetry_after = abs(left_metrics_after[0] - right_metrics_after[0])
consistency_after = (left_metrics_after[3] + right_metrics_after[3]) / 2

# Print metrics
print("Metrics before change point:")
print("Left Step Count:", left_metrics_before[0])
print("Right Step Count:", right_metrics_before[0])
print("Left Step Frequency (steps/min):", left_metrics_before[1])
print("Right Step Frequency (steps/min):", right_metrics_before[1])
print("Left Step Duration Mean (s):", left_metrics_before[2])
print("Right Step Duration Mean (s):", right_metrics_before[2])
print("Left Step Duration Std Dev (s):", left_metrics_before[3])
print("Right Step Duration Std Dev (s):", right_metrics_before[3])
print("Symmetry (difference in step count):", symmetry_before)
print("Consistency (mean of std dev in step duration):", consistency_before)

print("\nMetrics after change point:")
print("Left Step Count:", left_metrics_after[0])
print("Right Step Count:", right_metrics_after[0])
print("Left Step Frequency (steps/min):", left_metrics_after[1])
print("Right Step Frequency (steps/min):", right_metrics_after[1])
print("Left Step Duration Mean (s):", left_metrics_after[2])
print("Right Step Duration Mean (s):", right_metrics_after[2])
print("Left Step Duration Std Dev (s):", left_metrics_after[3])
print("Right Step Duration Std Dev (s):", right_metrics_after[3])
print("Symmetry (difference in step count):", symmetry_after)
print("Consistency (mean of std dev in step duration):", consistency_after)

# Compare metrics between directions
step_count_diff = abs((left_metrics_before[0] + left_metrics_after[0]) - (right_metrics_before[0] + right_metrics_after[0]))
step_frequency_diff = abs((left_metrics_before[1] + left_metrics_after[1]) - (right_metrics_before[1] + right_metrics_after[1]))
step_duration_diff = abs((left_metrics_before[2] + left_metrics_after[2]) - (right_metrics_before[2] + right_metrics_after[2]))
step_std_dev_diff = abs((left_metrics_before[3] + left_metrics_after[3]) - (right_metrics_before[3] + right_metrics_after[3]))

print("\nComparison of metrics between directions:")
print("Step Count Difference:", step_count_diff)
print("Step Frequency Difference (steps/min):", step_frequency_diff)
print("Step Duration Mean Difference (s):", step_duration_diff)
print("Step Duration Std Dev Difference (s):", step_std_dev_diff)
