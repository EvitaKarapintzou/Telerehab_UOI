/*
 * Copyright 2015 MbientLab Inc. All rights reserved.
 *
 * IMPORTANT: Your use of this Software is limited to those specific rights
 * granted under the terms of a software license agreement between the user who
 * downloaded the software, his/her employer (which must be your employer) and
 * MbientLab Inc, (the "License").  You may not use this Software unless you
 * agree to abide by the terms of the License which can be found at
 * www.mbientlab.com/terms . The License limits your use, and you acknowledge,
 * that the  Software may not be modified, copied or distributed and can be used
 * solely and exclusively in conjunction with a MbientLab Inc, product.  Other
 * than for the foregoing purpose, you may not use, reproduce, copy, prepare
 * derivative works of, modify, distribute, perform, display or sell this
 * Software and/or its documentation for any purpose.
 *
 * YOU FURTHER ACKNOWLEDGE AND AGREE THAT THE SOFTWARE AND DOCUMENTATION ARE
 * PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING WITHOUT LIMITATION, ANY WARRANTY OF MERCHANTABILITY, TITLE,
 * NON-INFRINGEMENT AND FITNESS FOR A PARTICULAR PURPOSE. IN NO EVENT SHALL
 * MBIENTLAB OR ITS LICENSORS BE LIABLE OR OBLIGATED UNDER CONTRACT, NEGLIGENCE,
 * STRICT LIABILITY, CONTRIBUTION, BREACH OF WARRANTY, OR OTHER LEGAL EQUITABLE
 * THEORY ANY DIRECT OR INDIRECT DAMAGES OR EXPENSES INCLUDING BUT NOT LIMITED
 * TO ANY INCIDENTAL, SPECIAL, INDIRECT, PUNITIVE OR CONSEQUENTIAL DAMAGES, LOST
 * PROFITS OR LOST DATA, COST OF PROCUREMENT OF SUBSTITUTE GOODS, TECHNOLOGY,
 * SERVICES, OR ANY CLAIMS BY THIRD PARTIES (INCLUDING BUT NOT LIMITED TO ANY
 * DEFENSE THEREOF), OR OTHER SIMILAR COSTS.
 *
 * Should you have any questions regarding your right to use this Software,
 * contact MbientLab Inc, at www.mbientlab.com.
 */

package com.mbientlab.metawear.metabase;

import static android.content.ContentValues.TAG;

import static com.mbientlab.metawear.module.Led.PATTERN_REPEAT_INDEFINITELY;

import android.app.Activity;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.SharedPreferences;
import com.mbientlab.metawear.module.Led;

import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import android.os.Looper;
import android.util.Log;
import android.util.Pair;
import android.view.Menu;
import android.widget.TextView;

import com.mbientlab.function.Action;
import com.mbientlab.metawear.MetaWearBoard;
import com.mbientlab.metawear.android.BtleService;
import com.mbientlab.metawear.data.Acceleration;
import com.mbientlab.metawear.module.Debug;
import com.mbientlab.metawear.module.Macro;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

import bolts.Capture;
import bolts.Task;
import no.nordicsemi.android.dfu.DfuBaseService;

import com.mbientlab.metawear.module.SensorFusionBosch;


public class HomeActivity extends AppCompatActivity implements ServiceConnection {
    private static final String FRAGMENT_KEY= "com.mbientlab.metawear.metabase.HomeActivity.FRAGMENT_KEY",
            SHOW_METACLOUD_ABOUT = "com.mbientlab.metawear.metabase.HomeActivity.SHOW_METACLOUD_ABOUT";
    static final String SHOW_TUTORIAL = "show_tutorial";
    private static final String DEVICE_MAC_ADDRESS_01 = "EF:0F:A9:3D:48:AA";
    private static final String DEVICE_MAC_ADDRESS_02 = "EE:E2:E3:B4:9A:D7";
    private static final String DEVICE_MAC_ADDRESS_03 = "ED:B1:65:CE:EF:D4";
    private static final String DEVICE_MAC_ADDRESS_04 = "DA:C1:9F:1B:6E:40";
    private Set<String> discoveredDevices = new HashSet<>();
    private boolean allDevicesDiscovered = false;  // Flag to track when all devices are discovered
    private final Set<String> targetDevices = new HashSet<>(Arrays.asList(
            DEVICE_MAC_ADDRESS_01,
            DEVICE_MAC_ADDRESS_02,
            DEVICE_MAC_ADDRESS_03,
            DEVICE_MAC_ADDRESS_04
    ));
    private static final int RECORDING_DURATION_MS = 40000;  // 40 seconds

    private BtleService.LocalBinder serviceBinder;
    private MetaWearBoard metawear_01;
    private MetaWearBoard metawear_02;
    private MetaWearBoard metawear_03;
    private MetaWearBoard metawear_04;


    private String message = "";


    public static Task<Void> teardownAndDc(MetaWearBoard board) {
        board.getModule(Macro.class).eraseAll();
        board.getModule(Debug.class).resetAfterGc();
        return board.getModule(Debug.class).disconnectAsync();
    }

    public static Task<Void> reconnect(Activity activity, MetaWearBoard metawear, long delay, int retries, boolean showDialog) {
        final Capture<AlertDialog> dialog = new Capture<>();

        if (showDialog) {
            activity.runOnUiThread(() -> {
                AlertDialog value = new AlertDialog.Builder(activity)
                        .setTitle(R.string.title_reconnecting)
                        .setView(R.layout.indeterminate_task)
                        .setCancelable(false)
                        .create();
                dialog.set(value);
                value.show();
                ((TextView) value.findViewById(R.id.message)).setText(R.string.message_wait);
            });
        }

        final Capture<Integer> remaining = new Capture<>(retries);
        return (delay == 0L ? Task.forResult(null) : Task.delay(delay)).continueWhile(() -> !metawear.isConnected() && remaining.get() >= 0, ignored ->
            metawear.connectAsync().continueWithTask(task -> {
                if (task.isFaulted()) {
                    remaining.set(remaining.get() - 1);
                }
                return task;
            })
        ).continueWithTask(ignored -> {
            if (dialog.get() != null) {
                dialog.get().dismiss();
            }
            return ignored;
        }, Task.UI_THREAD_EXECUTOR);
    }

    private BtleScanner scanner;
    private Object parameter;
    private Action<Void> backPressedHandler;
    private BtleService.LocalBinder binder;

    private AppFragmentBase currentFragment= null;
    private Deque<Pair<String, Object>> backstack = new ArrayDeque<>();



    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        scanner = BtleScanner.getScanner(((BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE)).getAdapter(), new UUID[] {
                MetaWearBoard.METAWEAR_GATT_SERVICE
        });
        // Start scanning and handle scan results
        scanner.start(scanResult -> {
            String macAddress = scanResult.btDevice.getAddress();
            Log.i("Scanner", "Discovered device MAC: " + macAddress + " with RSSI: " + scanResult.rssi);

            if (targetDevices.contains(macAddress)) {
                discoveredDevices.add(macAddress);


                if (discoveredDevices.containsAll(targetDevices) && allDevicesDiscovered == false) {
                    allDevicesDiscovered = true;
                    Log.i("Scanner", "All target devices discovered.");
                    connect2IMUs();
                    scanner.stop();
                }
            }
        });
        getApplicationContext().bindService(new Intent(this, BtleService.class),this, Context.BIND_AUTO_CREATE);
        moveTaskToBack(true);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Unbind the service when the activity is destroyed
        getApplicationContext().unbindService(this);
    }





    // This method is called when the MetaWear board is connected
    private void startRecordingAndDisconnect(MetaWearBoard metawear, String tag) {
        //configureSensorFusion(metawear, tag);

        // Start a timer to stop recording after 20 seconds
        new Handler(Looper.getMainLooper()).postDelayed(() -> {
            stopRecordingAndDisconnect(metawear, tag);
        }, RECORDING_DURATION_MS);
    }

    // This method stops recording and disconnects gracefully
    private void stopRecordingAndDisconnect(MetaWearBoard metawear, String tag) {
        stopLed(metawear);
        SensorFusionBosch sensorFusion = metawear.getModule(SensorFusionBosch.class);
        if (sensorFusion != null) {
            // Stop the data stream and the sensor
            sensorFusion.stop();
            sensorFusion.linearAcceleration().stop();
            Log.i(tag, "Stopped recording data for " + tag);

            // Gracefully disconnect from the MetaWear board
            teardownAndDc(metawear).continueWith(task -> {
                if (task.isFaulted()) {
                    Log.e(TAG, "Error disconnecting from MetaWear board for " + tag, task.getError());
                } else {
                    Log.i(TAG, "Successfully disconnected from MetaWear board for " + tag);
                }
                return null;
            });
        }
    }
    public void connect2IMUs(){

        // Start searching for the MetaWear device using the MAC address
        final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
        final BluetoothDevice remoteDevice_01 = btManager.getAdapter().getRemoteDevice(DEVICE_MAC_ADDRESS_01);
        final BluetoothDevice remoteDevice_02 = btManager.getAdapter().getRemoteDevice(DEVICE_MAC_ADDRESS_02);
        final BluetoothDevice remoteDevice_03 = btManager.getAdapter().getRemoteDevice(DEVICE_MAC_ADDRESS_03);
        final BluetoothDevice remoteDevice_04 = btManager.getAdapter().getRemoteDevice(DEVICE_MAC_ADDRESS_04);

        metawear_01 = serviceBinder.getMetaWearBoard(remoteDevice_01);
        metawear_02 = serviceBinder.getMetaWearBoard(remoteDevice_02);
        metawear_03 = serviceBinder.getMetaWearBoard(remoteDevice_03);
        metawear_04 = serviceBinder.getMetaWearBoard(remoteDevice_04);
        connectToMetaWear_01(metawear_01);
        connectToMetaWear_02(metawear_02);
        connectToMetaWear_03(metawear_03);
        connectToMetaWear_04(metawear_04);


    }
    @Override
    public void onServiceConnected(ComponentName name, IBinder service) {
        if (service instanceof BtleService.LocalBinder) {
            binder = (BtleService.LocalBinder) service;
            serviceBinder = binder;
            /*
            // Start searching for the MetaWear device using the MAC address
            final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
            final BluetoothDevice remoteDevice_01 = btManager.getAdapter().getRemoteDevice(DEVICE_MAC_ADDRESS_01);
            final BluetoothDevice remoteDevice_02 = btManager.getAdapter().getRemoteDevice(DEVICE_MAC_ADDRESS_02);
            final BluetoothDevice remoteDevice_03 = btManager.getAdapter().getRemoteDevice(DEVICE_MAC_ADDRESS_03);
            final BluetoothDevice remoteDevice_04 = btManager.getAdapter().getRemoteDevice(DEVICE_MAC_ADDRESS_04);


            metawear_01 = serviceBinder.getMetaWearBoard(remoteDevice_01);
            metawear_02 = serviceBinder.getMetaWearBoard(remoteDevice_02);
            metawear_03 = serviceBinder.getMetaWearBoard(remoteDevice_03);
            metawear_04 = serviceBinder.getMetaWearBoard(remoteDevice_04);
            connectToMetaWear_01(metawear_01);
            connectToMetaWear_02(metawear_02);
            connectToMetaWear_03(metawear_03);
            connectToMetaWear_04(metawear_04);

            scanner.stop();
            */

        } else {
            Log.e(TAG, "Service binding failed!");
        }
    }

    private static final int MAX_RETRIES = 5;  // Set your max retries
    private int retryCount = 0;  // Track retry attempts

    private void connectToMetaWear_01(MetaWearBoard metawear) {
        metawear.connectAsync(5000).continueWithTask(task -> {
            if (task.isFaulted()) {
                Log.e(TAG, "Failed to connect to MetaWear board, retrying...", task.getError());

                if (retryCount < MAX_RETRIES) {
                    retryCount++;
                    // Retry after a short delay (e.g., 5 seconds)
                    new Handler(Looper.getMainLooper()).postDelayed(() -> {
                        Log.i(TAG, "Retrying connection attempt #" + retryCount);
                        connectToMetaWear_01(metawear);  // Retry connection
                    }, 5000);  // Retry after 5 seconds
                } else {
                    Log.e(TAG, "Max retry attempts reached. Unable to connect to MetaWear board.");
                }
            } else {
                Log.i(TAG, "Successfully connected to MetaWear board");
                turnOnBlueLed(metawear);
                configureSensorFusion(metawear, "1");  // Your sensor fusion setup
                retryCount = 0;  // Reset retry count on success
            }
            return null;
        });

        startRecordingAndDisconnect(metawear, "1");
    }


    private void connectToMetaWear_02(MetaWearBoard metawear) {
        metawear.connectAsync(5000).continueWithTask(task -> {
            if (task.isFaulted()) {
                Log.e(TAG, "Failed to connect to MetaWear board, retrying...", task.getError());
                if (retryCount < MAX_RETRIES) {
                    retryCount++;
                    // Retry after a short delay (e.g., 5 seconds)
                    new Handler(Looper.getMainLooper()).postDelayed(() -> {
                        Log.i(TAG, "Retrying connection attempt #" + retryCount);
                        connectToMetaWear_02(metawear);  // Retry connection
                    }, 5000);  // Retry after 5 seconds
                } else {
                    Log.e(TAG, "Max retry attempts reached. Unable to connect to MetaWear board.");
                }
            } else {
                Log.i(TAG, "Successfully connected to MetaWear board");
                turnOnBlueLed(metawear);
                configureSensorFusion(metawear, "2");  // Your sensor fusion setup
                retryCount = 0;  // Reset retry count on success
            }
            return null;
        });
        startRecordingAndDisconnect(metawear, "2");
    }

    private void connectToMetaWear_03(MetaWearBoard metawear) {
        metawear.connectAsync(5000).continueWithTask(task -> {
            if (task.isFaulted()) {
                Log.e(TAG, "Failed to connect to MetaWear board, retrying...", task.getError());

                if (retryCount < MAX_RETRIES) {
                    retryCount++;
                    // Retry after a short delay (e.g., 5 seconds)
                    new Handler(Looper.getMainLooper()).postDelayed(() -> {
                        Log.i(TAG, "Retrying connection attempt #" + retryCount);
                        connectToMetaWear_03(metawear);  // Retry connection
                    }, 5000);  // Retry after 5 seconds
                } else {
                    Log.e(TAG, "Max retry attempts reached. Unable to connect to MetaWear board.");
                }
            } else {
                Log.i(TAG, "Successfully connected to MetaWear board");
                turnOnBlueLed(metawear);
                configureSensorFusion(metawear, "3");  // Your sensor fusion setup
                retryCount = 0;  // Reset retry count on success
            }
            return null;
        });
        startRecordingAndDisconnect(metawear, "3");
    }

    private void connectToMetaWear_04(MetaWearBoard metawear) {
        metawear.connectAsync(5000).continueWithTask(task -> {
            if (task.isFaulted()) {
                Log.e(TAG, "Failed to connect to MetaWear board, retrying...", task.getError());

                if (retryCount < MAX_RETRIES) {
                    retryCount++;
                    // Retry after a short delay (e.g., 5 seconds)
                    new Handler(Looper.getMainLooper()).postDelayed(() -> {
                        Log.i(TAG, "Retrying connection attempt #" + retryCount);
                        connectToMetaWear_04(metawear);  // Retry connection
                    }, 5000);  // Retry after 5 seconds
                } else {
                    Log.e(TAG, "Max retry attempts reached. Unable to connect to MetaWear board.");
                }
            } else {
                Log.i(TAG, "Successfully connected to MetaWear board");
                turnOnBlueLed(metawear);
                configureSensorFusion(metawear, "4");  // Your sensor fusion setup
                retryCount = 0;  // Reset retry count on success
            }
            return null;
        });
        startRecordingAndDisconnect(metawear, "4");

    }

    private void configureSensorFusion(MetaWearBoard metawear, String mytag) {
        SensorFusionBosch sensorFusion = metawear.getModule(SensorFusionBosch.class);
        if (sensorFusion != null) {
            Log.i(TAG, "Configuring Sensor Fusion");

            sensorFusion.configure()
                    .mode(SensorFusionBosch.Mode.NDOF)
                    .accRange(SensorFusionBosch.AccRange.AR_2G)
                    .gyroRange(SensorFusionBosch.GyroRange.GR_250DPS)
                    .commit();

            sensorFusion.linearAcceleration().addRouteAsync(source -> source.stream((data, env) -> {
                String linearValue =
                        data.value(Acceleration.class).x() + "," +
                                data.value(Acceleration.class).y() + "," +
                                data.value(Acceleration.class).z() + "," +
                                data.timestamp().getTimeInMillis() + "\n";

                message = data.value(Acceleration.class).x() + " " + data.value(Acceleration.class).y() + " " + data.value(Acceleration.class).z();
                Log.i(mytag, message);
            })).continueWith(task -> {
                if (task.isFaulted()) {
                    Log.e("TAG", "Error in setting up the route for sensor fusion", task.getError());
                } else {
                    sensorFusion.linearAcceleration().start();
                    sensorFusion.start();
                }
                return null;
            });
        } else {
            Log.e(TAG, "Sensor Fusion not supported on this device");
        }
    }

    private void turnOnBlueLed(MetaWearBoard metawear) {
        // Get the LED module
        Led led = metawear.getModule(Led.class);

        if (led != null) {
            // Configure the LED to flash in blue color
            led.editPattern(Led.Color.BLUE)
                    .riseTime((short) 500)
                    .pulseDuration((short) 1000)
                    .repeatCount((byte) PATTERN_REPEAT_INDEFINITELY)  // Number of times to repeat (use Led.PATTERN_REPEAT_INDEFINITELY for continuous flashing)
                    .highTime((short) 500)
                    .highIntensity((byte) 31)  // Max intensity
                    .lowIntensity((byte) 0)
                    .commit();

            // Start the LED
            led.play();
        } else {
            Log.e("LED", "LED module not available");
        }
    }

    // To stop the LED later, you can call:
    private void stopLed(MetaWearBoard metawear) {
        Led led = metawear.getModule(Led.class);
        if (led != null) {
            led.stop(true);  // Stops and clears the LED pattern
        }
    }


    @Override
    public void onServiceDisconnected(ComponentName name) {

    }


    public static class DfuService extends DfuBaseService {
        @Override
        protected Class<? extends Activity> getNotificationTarget() {
            return HomeActivity.class;
        }
    }


}
