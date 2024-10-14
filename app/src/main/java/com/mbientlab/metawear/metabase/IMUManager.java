package com.mbientlab.metawear.metabase;

import static android.content.Context.BLUETOOTH_SERVICE;
import static androidx.core.content.ContextCompat.getSystemService;

import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;


import com.mbientlab.metawear.MetaWearBoard;
import com.mbientlab.metawear.android.BtleService;
import com.mbientlab.metawear.module.Led;
import com.mbientlab.metawear.module.Macro;
import com.mbientlab.metawear.module.SensorFusionBosch;
import com.mbientlab.metawear.data.Acceleration;
import com.mbientlab.metawear.module.Debug;
import com.mbientlab.metawear.data.Quaternion;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.atomic.AtomicInteger;

import static com.mbientlab.metawear.module.Led.PATTERN_REPEAT_INDEFINITELY;

import bolts.Task;
import android.bluetooth.BluetoothManager;


public class IMUManager {

    private static final String TAG = "IMUManager";
    private final BtleService.LocalBinder serviceBinder;
    private final Context context;
    private final Map<String, MetaWearBoard> imuDevices = new HashMap<>();
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final BluetoothManager btManager;

    private ConcurrentLinkedQueue<SensorData> sensorDataQueue;
    private static final String MULTICAST_GROUP = "224.1.1.1";
    private static final int MULTICAST_PORT = 10000;

    private String message = "";




    public IMUManager(BtleService.LocalBinder serviceBinder, Context context) {
        this.serviceBinder = serviceBinder;
        this.context = context;
        btManager = (BluetoothManager) context.getSystemService(Context.BLUETOOTH_SERVICE);

        publishDataToServer();

    }



    // Connect to an IMU device by its MAC address
    public void connectToIMU(String macAddress, String mode, String role) {

        final BluetoothDevice remoteDevice = btManager.getAdapter().getRemoteDevice(macAddress);
        AtomicInteger retryCount = new AtomicInteger();

        MetaWearBoard metawear = serviceBinder.getMetaWearBoard(remoteDevice);

        metawear.connectAsync(5000).continueWithTask(task -> {
            if (task.isFaulted()) {
                Log.e(TAG, "Failed to connect to MetaWear board, retrying...", task.getError());

                if (retryCount.get() < Constants.MAX_RETRY_ATTEMPTS) {
                    retryCount.getAndIncrement();
                    // Retry after a short delay (e.g., 5 seconds)
                    new Handler(Looper.getMainLooper()).postDelayed(() -> {
                        Log.i(TAG, "Retrying connection attempt #" + retryCount);
                        connectToIMU(macAddress, mode, role);  // Retry connection with mode and role
                    }, 5000);  // Retry after 5 seconds
                } else {
                    Log.e(TAG, "Max retry attempts reached. Unable to connect to MetaWear board.");
                }
            } else {
                Log.i(TAG, "Successfully connected to MetaWear board");
                imuDevices.put(macAddress, metawear);

                // Configure the IMU based on the mode (QUATERNIONS or LINEARACCELERATION)
                if (mode.equals("QUATERNIONS")) {
                    configureForQuaternions(metawear, role);  // Configure for Quaternions
                } else if (mode.equals("LINEARACCELERATION")) {
                    configureForLinearAcceleration(metawear, role);  // Configure for Linear Acceleration
                }

                retryCount.set(0);  // Reset retry count on success
            }
            return null;
        });

        //startRecordingAndDisconnect(metawear, macAddress);
    }


    private void startRecordingAndDisconnect(MetaWearBoard metawear, String tag) {
        //configureSensorFusion(metawear, tag);
        //turnOnBlueLed(metawear);
        // Start a timer to stop recording after 20 seconds
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            stopRecordingAndDisconnect(metawear, tag);
        }, Constants.RECORDING_DURATION_MS);
    }


    // Configure Sensor Fusion for a connected IMU
// Configure IMU for Quaternions
    private void configureForQuaternions(MetaWearBoard metawear, String macAddress) {
        SensorFusionBosch sensorFusion = metawear.getModule(SensorFusionBosch.class);
        if (sensorFusion != null) {
            Log.i(TAG, "Configuring Quaternions for " + macAddress);

            sensorFusion.configure()
                    .mode(SensorFusionBosch.Mode.NDOF)
                    .accRange(SensorFusionBosch.AccRange.AR_2G)
                    .gyroRange(SensorFusionBosch.GyroRange.GR_250DPS)
                    .commit();

            sensorFusion.quaternion().addRouteAsync(source -> source.stream((data, env) -> {
                //String quaternionValue = data.value(Quaternion.class).toString();


                String quaternionValue =
                        data.value(Quaternion.class).w() + "," +
                                data.value(Quaternion.class).x() + "," +
                                data.value(Quaternion.class).y() + "," +
                                data.value(Quaternion.class).z() + "," +
                                data.timestamp().getTimeInMillis()+ "\n";
                Log.i("IMU_" + macAddress, "Quaternion: " + quaternionValue);

                message = "Name"+macAddress + " " + macAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Quaternion.class).w() + " " + data.value(Quaternion.class).x() + " " + data.value(Quaternion.class).y() + " " + data.value(Quaternion.class).z();
                //addNewData(message);
                //Log.i("1->", message);
                SensorData mydata = new SensorData();
                mydata.setDeviceMacAddress(macAddress);
                mydata.setTimestamp(data.timestamp().getTimeInMillis());
                mydata.setX(data.value(Quaternion.class).x());
                mydata.setY(data.value(Quaternion.class).y());
                mydata.setZ(data.value(Quaternion.class).z());
                mydata.setW(data.value(Quaternion.class).w());
                sensorDataQueue.offer(mydata);


            })).continueWith(task -> {
                if (task.isFaulted()) {
                    Log.e(TAG, "Error setting up quaternion route for " + macAddress, task.getError());
                } else {
                    sensorFusion.quaternion().start();
                    sensorFusion.start();
                }
                turnOnBlueLed(metawear);
                return null;
            });
        } else {
            Log.e(TAG, "Sensor Fusion not supported on IMU " + macAddress);
        }
    }

    // Configure IMU for Linear Acceleration
    private void configureForLinearAcceleration(MetaWearBoard metawear, String macAddress) {
        SensorFusionBosch sensorFusion = metawear.getModule(SensorFusionBosch.class);
        if (sensorFusion != null) {
            Log.i(TAG, "Configuring Linear Acceleration for " + macAddress);

            sensorFusion.configure()
                    .mode(SensorFusionBosch.Mode.NDOF)
                    .accRange(SensorFusionBosch.AccRange.AR_2G)
                    .gyroRange(SensorFusionBosch.GyroRange.GR_250DPS)
                    .commit();

            sensorFusion.linearAcceleration().addRouteAsync(source -> source.stream((data, env) -> {
                String linearValue = data.value(Acceleration.class).toString();
                Log.i("IMU_" + macAddress, "Linear Acceleration: " + linearValue);
                SensorData mydata = new SensorData();
                mydata.setDeviceMacAddress(macAddress);
                mydata.setTimestamp(data.timestamp().getTimeInMillis());
                mydata.setX(data.value(Acceleration.class).x());
                mydata.setY(data.value(Acceleration.class).y());
                mydata.setZ(data.value(Acceleration.class).z());
                sensorDataQueue.offer(mydata);


            })).continueWith(task -> {
                if (task.isFaulted()) {
                    Log.e(TAG, "Error setting up linear acceleration route for " + macAddress, task.getError());
                } else {
                    sensorFusion.linearAcceleration().start();
                    sensorFusion.start();
                }
                turnOnBlueLed(metawear);
                return null;
            });
        } else {
            Log.e(TAG, "Sensor Fusion not supported on IMU " + macAddress);
        }
    }

    // Turn on the blue LED on the IMU
    private void turnOnBlueLed(MetaWearBoard metawear) {
        Led led = metawear.getModule(Led.class);
        if (led != null) {
            led.editPattern(Led.Color.BLUE)
                    .riseTime((short) 500)
                    .pulseDuration((short) 1000)
                    .repeatCount((byte) PATTERN_REPEAT_INDEFINITELY)
                    .highTime((short) 500)
                    .highIntensity((byte) 31)
                    .lowIntensity((byte) 0)
                    .commit();
            led.play();
        } else {
            Log.e(TAG, "LED module not available");
        }
    }


    // Stop recording and disconnect gracefully for a single IMU
    private void stopRecordingAndDisconnect(MetaWearBoard metawear, String macAddressTag) {
        SensorFusionBosch sensorFusion = metawear.getModule(SensorFusionBosch.class);
        if (sensorFusion != null) {
            sensorFusion.stop();
            sensorFusion.linearAcceleration().stop();
            Log.i(TAG, "Stopped recording data for IMU " + macAddressTag);
        }

        stopLed(metawear);

        // Gracefully disconnect
        metawear.getModule(Debug.class).disconnectAsync().continueWith(task -> {
            if (task.isFaulted()) {
                Log.e(TAG, "Error disconnecting from IMU " + macAddressTag, task.getError());
            } else {
                Log.i(TAG, "Successfully disconnected from IMU " + macAddressTag);
                imuDevices.remove(macAddressTag);  // Remove from connected devices
            }
            return null;
        });
    }


    public static Task<Void> teardownAndDc(MetaWearBoard board) {
        board.getModule(Macro.class).eraseAll();
        board.getModule(Debug.class).resetAfterGc();
        return board.getModule(Debug.class).disconnectAsync();
    }


    // Stop the LED
    private void stopLed(MetaWearBoard metawear) {
        Led led = metawear.getModule(Led.class);
        if (led != null) {
            led.stop(true);
        }
    }

    // Stop recording and disconnect gracefully from all IMUs
    public void stopRecordingAndDisconnectAll() {
        for (Map.Entry<String, MetaWearBoard> entry : imuDevices.entrySet()) {
            String macAddress = entry.getKey();
            Log.e("stopRecordingAndDisconnectAll", macAddress);

            MetaWearBoard metawear = entry.getValue();
            stopRecordingAndDisconnect(metawear, macAddress);
        }
    }

    // Clean up resources and disconnect from all devices
    public void cleanup() {
        stopRecordingAndDisconnectAll();
    }

    void publishDataToServer() {
        sensorDataQueue = new ConcurrentLinkedQueue<>();

        new Thread(() -> {
            try {
                DatagramSocket socket = new DatagramSocket();
                InetAddress group = InetAddress.getByName(MULTICAST_GROUP);

                int p = 0;
                while (true) {
                    if (!sensorDataQueue.isEmpty()) {
                        SensorData data = sensorDataQueue.poll(); // Dequeue data from the queue
                        if (data != null) {
                            String message = data.toJson();
                            byte[] buf = message.getBytes();
                            DatagramPacket packet = new DatagramPacket(buf, buf.length, group, MULTICAST_PORT);
                            socket.send(packet);
                            p = p + 1;
                            Log.i("counter", Integer.toString(p) + " " + message);
                        }
                    }
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }).start();
    }

}
