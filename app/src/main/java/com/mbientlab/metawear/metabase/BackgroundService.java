package com.mbientlab.metawear.metabase;

import static android.content.ContentValues.TAG;
import static com.mbientlab.metawear.module.Led.PATTERN_REPEAT_INDEFINITELY;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;

import androidx.core.app.NotificationCompat;

import com.mbientlab.metawear.MetaWearBoard;
import com.mbientlab.metawear.android.BtleService;
import com.mbientlab.metawear.data.Acceleration;
import com.mbientlab.metawear.metabase.IMUManager;
import com.mbientlab.metawear.metabase.Constants;
import com.mbientlab.metawear.module.Debug;
import com.mbientlab.metawear.module.Led;
import com.mbientlab.metawear.module.Macro;
import com.mbientlab.metawear.module.SensorFusionBosch;


import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

import bolts.Task;

public class BackgroundService extends Service implements ServiceConnection {

    private static final String TAG = "BackgroundService";
    private BtleService.LocalBinder serviceBinder;
    private IMUManager imuManager;
    private Set<String> discoveredDevices = new HashSet<>();
    private boolean allDevicesConnected = false;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private BtleScanner scanner;
    private static final String DEVICE_MAC_ADDRESS_01 = "EF:0F:A9:3D:48:AA";
    private static final String DEVICE_MAC_ADDRESS_02 = "EE:E2:E3:B4:9A:D7";
    private static final String DEVICE_MAC_ADDRESS_03 = "ED:B1:65:CE:EF:D4";
    private static final String DEVICE_MAC_ADDRESS_04 = "DA:C1:9F:1B:6E:40";
    private boolean allDevicesDiscovered = false;  // Flag to track when all devices are discovered
    private final Set<String> targetDevices = new HashSet<>(Arrays.asList(
            DEVICE_MAC_ADDRESS_01,
            DEVICE_MAC_ADDRESS_02,
            DEVICE_MAC_ADDRESS_03,
            DEVICE_MAC_ADDRESS_04
    ));
    private BtleService.LocalBinder binder;

    private MetaWearBoard metawear_01;
    private MetaWearBoard metawear_02;
    private MetaWearBoard metawear_03;
    private MetaWearBoard metawear_04;
    private int retryCount = 0;  // Track retry attempts
    private String message = "";
    private BluetoothManager btManager;

    private final Map<String, String[]> imuConfigurations = new HashMap<>();



    @Override
    public void onCreate() {

        super.onCreate();
        Log.i(TAG, "BackgroundService created");

        btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);

        // Bind to the BtleService
        getApplicationContext().bindService(new Intent(this, BtleService.class),this, Context.BIND_AUTO_CREATE);
    }
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // Check for Android O or higher to start the service in the foreground
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    "ForegroundServiceChannel",
                    "Foreground Service Channel",
                    NotificationManager.IMPORTANCE_DEFAULT
            );
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }

            // Build and start the notification for the foreground service
            Notification notification = new NotificationCompat.Builder(this, "ForegroundServiceChannel")
                    .setContentTitle("IMU Service Running")
                    .setContentText("The service is running in the background.")
                    .setSmallIcon(R.drawable.ic_stat_notify_dfu)  // Provide a notification icon
                    .setPriority(NotificationCompat.PRIORITY_DEFAULT)
                    .build();

            // Start the service in the foreground
            startForeground(1, notification);
        }

        // Handle the different actions from the Intent
        String configMessage;
        if (intent != null && intent.getAction() != null) {
            switch (intent.getAction()) {
                case "SET_IMU_CONFIG":
                    configMessage = intent.getStringExtra("IMU_CONFIG_MESSAGE");
                    handleIMUConfig(configMessage);
                    break;

                case "SET_MAC_ADDRESSES":
                    // Set the MAC addresses for IMU devices dynamically
                    String[] macAddresses = intent.getStringArrayExtra("MAC_ADDRESSES");
                    setTargetDevices(macAddresses);
                    break;

                case "START_RECORDING":
                    // Start scanning and recording based on the configured IMUs
                    startDeviceScanning();
                    break;

                case "STOP_RECORDING":
                    // Start scanning and recording based on the configured IMUs
                    imuManager.stopRecordingAndDisconnectAll();
                    break;
            }
        }

        // Keep the service running if called from the foreground
        return START_STICKY;
    }

    private void startDeviceScanning() {
        // Check if the Bluetooth Manager is available
        if (btManager == null) {
            Log.e(TAG, "Bluetooth Manager not available");
            return;
        }

        Log.i(TAG, "Starting device scanning...");

        // Initialize the scanner with the MetaWear GATT service UUID
        scanner = BtleScanner.getScanner(((BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE)).getAdapter(), new UUID[]{
                MetaWearBoard.METAWEAR_GATT_SERVICE
        });

// Start scanning and handle scan results
        scanner.start(scanResult -> {
            String macAddress = scanResult.btDevice.getAddress();
            Log.i("Scanner", "Discovered device MAC: " + macAddress + " with RSSI: " + scanResult.rssi);

            // Loop through imuConfigurations to find the matching MAC address
            for (Map.Entry<String, String[]> entry : imuConfigurations.entrySet()) {
                String[] config = entry.getValue();  // config[0] is the MAC address, config[1] is the mode
                //Log.i("config 0", config[0]);
                //Log.i("config 1", config[1]);
                if (config[0].equals(macAddress)) {
                    Log.i(TAG, "Device found in IMU configuration: " + entry.getKey());

                    String mode = config[1];  // Mode is the second element

                    // Only add devices that are not set to "OFF"
                    if (!mode.equals("OFF")) {
                        discoveredDevices.add(macAddress);
                        Log.e(TAG, imuConfigurations.keySet().toString());

                        // Optionally stop scanning once all required devices are discovered
                        if (discoveredDevices.size() == imuConfigurations.size() && !allDevicesDiscovered) {
                            allDevicesDiscovered = true;
                            Log.i("Scanner", "All target devices discovered.");

                            // Now connect to the devices using IMUManager
                            connectToDevices();

                            // Stop scanning
                            scanner.stop();
                            discoveredDevices.clear();
                            allDevicesDiscovered = false;
                        }
                    }
                }
            }
        });

    }




    // Store the IMU configurations in a HashMap

    private void handleIMUConfig(String configMessage) {
        String[] parts = configMessage.split(",");

        String exerciseCode = "";

        // Clear previous configurations if necessary
        imuConfigurations.clear();

        for (String part : parts) {
            if (part.contains("-")) {
                String[] keyValue = part.split("=");
                String role = keyValue[0];  // e.g., HEAD, RIGHTFOOT
                String[] macAndMode = keyValue[1].split("-");  // Splitting MAC and Mode

                if (macAndMode.length == 2) {
                    String macAddress = macAndMode[0];  // e.g., EF:0F:A9:3D:48:AA
                    String mode = macAndMode[1];  // e.g., QUATERNIONS, LINEARACCELERATION, OFF

                    if (!mode.equals("OFF")) {
                        // Store role, MAC address, and mode in the map
                        imuConfigurations.put(role, new String[] { macAddress, mode });
                    }
                }
            } else {
                // The last part should be the exercise code
                exerciseCode = part;
            }
        }

        Log.i(TAG, "IMU Configuration stored. Exercise Code: " + exerciseCode);
        for (Map.Entry<String, String[]> entry : imuConfigurations.entrySet()) {
            String role = entry.getKey();
            String[] config = entry.getValue();
            Log.i("IMU Config", "Role: " + role + ", MAC Address: " + config[0] + ", Mode: " + config[1]);
        }
        // Now you have the configuration stored, wait for the next message to start scanning
    }


    public static Task<Void> teardownAndDc(MetaWearBoard board) {
        board.getModule(Macro.class).eraseAll();
        board.getModule(Debug.class).resetAfterGc();
        return board.getModule(Debug.class).disconnectAsync();
    }

    private void connectToDevices() {
        Log.i(TAG, "Connecting to discovered devices...");
        imuManager = new IMUManager(serviceBinder, this);

        // Iterate through the stored IMU configurations
        for (Map.Entry<String, String[]> entry : imuConfigurations.entrySet()) {
            String role = entry.getKey();  // IMU role like HEAD, RIGHTFOOT
            String[] macAndMode = entry.getValue();  // The stored array with MAC address and mode
            String macAddress = macAndMode[0];
            String mode = macAndMode[1];  // Mode can be QUATERNIONS, LINEARACCELERATION, or OFF

            if (!mode.equals("OFF") && discoveredDevices.contains(macAddress)) {
                // Pass the MAC address and mode (QUATERNIONS or LINEARACCELERATION) to IMUManager
                imuManager.connectToIMU(macAddress, mode, role);  // Pass mode and role as arguments
            }
        }

        //handler.postDelayed(this::stopRecordingAndDisconnect, Constants.RECORDING_DURATION_MS);
    }



    private void stopRecordingAndDisconnect() {
        Log.i(TAG, "Stopping recording and disconnecting all devices...");
        imuManager.stopRecordingAndDisconnectAll();
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        Log.i(TAG, "BackgroundService destroyed");

        if (imuManager != null) {
            imuManager.cleanup();
        }
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onServiceConnected(ComponentName name, IBinder service) {
        if (service instanceof BtleService.LocalBinder) {
            binder = (BtleService.LocalBinder) service;
            serviceBinder = binder;


        } else {
            Log.e(TAG, "Service binding failed!");
        }
    }

    @Override
    public void onServiceDisconnected(ComponentName name) {

    }

    // Call this method upon receiving the first MQTT message with the MAC addresses
    public void setTargetDevices(String[] macAddresses) {
        targetDevices.clear();  // Clear any previously stored addresses
        targetDevices.addAll(Arrays.asList(macAddresses));
        Log.i("TargetDevices", "Updated MAC addresses: " + targetDevices.toString());
    }

}
