package com.example.myapplication;

import static androidx.constraintlayout.helper.widget.MotionEffect.TAG;

import static com.example.myapplication.Database.addNewData;
import static com.example.myapplication.Database.clearData;
import static com.example.myapplication.Database.getData;

import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.Manifest;
import android.os.Build;
import android.os.Bundle;
import android.content.pm.PackageManager;
import android.os.Environment;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import com.google.gson.Gson;
import com.mbientlab.metawear.MetaWearBoard;
import com.mbientlab.metawear.Route;
import com.mbientlab.metawear.android.BtleService;
import com.mbientlab.metawear.data.Acceleration;
import com.mbientlab.metawear.data.AngularVelocity;
import com.mbientlab.metawear.data.Quaternion;
import com.mbientlab.metawear.module.Accelerometer;
import com.mbientlab.metawear.module.AccelerometerBosch;
import com.mbientlab.metawear.module.AccelerometerMma8452q;
import com.mbientlab.metawear.module.GyroBmi160;
import com.mbientlab.metawear.module.SensorFusionBosch;
import com.mbientlab.metawear.module.SensorFusionBosch.*;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import bolts.Continuation;
import bolts.Task;

public class MainActivity extends AppCompatActivity implements ServiceConnection {
    private static final int REQUEST_BLUETOOTH_CONNECT_PERMISSION = 1;

    private BtleService.LocalBinder serviceBinder;
    private final String DEVICE_MAC_ADDRESS_1 = "E1:55:61:CB:91:61"; // Quaternion
    private final String DEVICE_MAC_ADDRESS_2 = "E2:5A:D0:3D:01:94"; // Linear
    private final String DEVICE_MAC_ADDRESS_3 = "C8:92:5E:7D:C6:BD"; // Quaternion
    private final String DEVICE_MAC_ADDRESS_4 = "FE:AC:84:C5:3D:E7"; // Linear
    private boolean secondDeviceConnectionAttempted = false;
    private boolean thirdDeviceConnectionAttempted = false;
    private boolean forthDeviceConnectionAttempted = false;
    int numOfSensors = 4;    // set the number of IMUs
    boolean []sensorsConnected = new boolean[numOfSensors];
    MetaWearBoard []boardsConnected = new MetaWearBoard[numOfSensors];
    private String message = "";
    private boolean creationLocallyCSVs = false; //true if you want

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Log.i("MainActivity", "OK1");

        for(int i=0; i< numOfSensors; i++)
            sensorsConnected[i] = false;

        // Check if the BLUETOOTH_CONNECT permission is granted
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT)
                    != PackageManager.PERMISSION_GRANTED) {
                // Permission not granted, request it
                ActivityCompat.requestPermissions(this,
                        new String[]{Manifest.permission.BLUETOOTH_CONNECT},
                        REQUEST_BLUETOOTH_CONNECT_PERMISSION);
            } else {
                // Permission granted, proceed with Bluetooth operations
                // Start connecting to your MetaWear device
            }
        } else {
            // For devices running versions lower than Android 6.0 (API level 23),
            // BLUETOOTH_CONNECT permission is granted at installation time.
            // Proceed with Bluetooth operations
            // Start connecting to your MetaWear device
        }

//        if (ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
//                != PackageManager.PERMISSION_GRANTED) {
//            ActivityCompat.requestPermissions(this, new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, PERMISSION_REQUEST_CODE);
//        } else {
//            createFolderAndWriteToCsv();
//        }

        // Bind to the MetaWear BtleService
        Intent intent = new Intent(this, BtleService.class);
        bindService(intent, this, BIND_AUTO_CREATE);

        moveTaskToBack(true);
    }

    @Override
    public void onServiceConnected(ComponentName name, IBinder service) {
        Log.i("MainActivity", "Service Connected");
        serviceBinder = (BtleService.LocalBinder) service;

        final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
        final BluetoothAdapter btAdapter = btManager.getAdapter();

        // Connect to the first MetaWear board
        connectToIMU1(DEVICE_MAC_ADDRESS_1, btAdapter, 5);

        // Connect to the second MetaWear board
        // connectToDevice(DEVICE_MAC_ADDRESS_2, btAdapter);
       // boolean b = new Handler().postDelayed(() -> connectToDevice(DEVICE_MAC_ADDRESS_2, btAdapter), 10000);// Delay of 1000ms (1 second)
    }

    private void connectToIMU1(String deviceMacAddress, BluetoothAdapter btAdapter, int retryCount) {
        final BluetoothDevice remoteDevice = btAdapter.getRemoteDevice(deviceMacAddress);
        final MetaWearBoard board = serviceBinder.getMetaWearBoard(remoteDevice);

        if(retryCount == 0){
            configureQuantranion(null, null);
        }
        board.connectAsync().continueWith(task -> {
            if (task.isFaulted()) {
                Log.e("MainActivity", "Failed to connect to MetaWear board: " + deviceMacAddress, task.getError());
                // Check if we should retry
                if (retryCount > 0) {
                    Log.i("MainActivity", "Attempting to reconnect to: " + deviceMacAddress + ". Retries left: " + retryCount);
                    final int newRetryCount = retryCount - 1;
                    // Use a handler to introduce a delay before retrying
                    new Handler(Looper.getMainLooper()).postDelayed(() -> connectToIMU1(deviceMacAddress, btAdapter, newRetryCount), 5000); // Retry after 5 seconds
                }
            } else if (task.isCompleted()) {
                Log.i("MainActivity", "Successfully connected to MetaWear board: " + deviceMacAddress);
                configureQuantranion(board, deviceMacAddress); // Ensure to pass along any needed parameters
            }
            return null;
        });
    }

    private void connectToIMU3(String deviceMacAddress, BluetoothAdapter btAdapter, int retryCount) {
        final BluetoothDevice remoteDevice = btAdapter.getRemoteDevice(deviceMacAddress);
        final MetaWearBoard board = serviceBinder.getMetaWearBoard(remoteDevice);

        if(retryCount == 0){
            configureQuantranion2(null, null);
        }
        board.connectAsync().continueWith(task -> {
            if (task.isFaulted()) {
                Log.e("MainActivity", "Failed to connect to MetaWear board: " + deviceMacAddress, task.getError());
                // Check if we should retry
                if (retryCount > 0) {
                    Log.i("MainActivity", "Attempting to reconnect to: " + deviceMacAddress + ". Retries left: " + retryCount);
                    final int newRetryCount = retryCount - 1;
                    // Use a handler to introduce a delay before retrying
                    new Handler(Looper.getMainLooper()).postDelayed(() -> connectToIMU3(deviceMacAddress, btAdapter, newRetryCount), 5000); // Retry after 5 seconds
                }
            } else if (task.isCompleted()) {
                Log.i("MainActivity", "Successfully connected to MetaWear board: " + deviceMacAddress);
                configureQuantranion2(board, deviceMacAddress); // Ensure to pass along any needed parameters
            }
            return null;
        });
    }
    private void connectToIMU2(String deviceMacAddress, BluetoothAdapter btAdapter, int retryCount) {
        final BluetoothDevice remoteDevice = btAdapter.getRemoteDevice(deviceMacAddress);
        final MetaWearBoard board = serviceBinder.getMetaWearBoard(remoteDevice);

        if(retryCount == 0){
            configureSensorFusionForLinearAcceleration(null, null);
        }
        board.connectAsync().continueWith(task -> {
            if (task.isFaulted()) {
                Log.e("MainActivity", "Failed to connect to MetaWear board: " + deviceMacAddress, task.getError());
                // Check if we should retry
                if (retryCount > 0) {
                    Log.i("MainActivity", "Attempting to reconnect to: " + deviceMacAddress + ". Retries left: " + retryCount);
                    final int newRetryCount = retryCount - 1;
                    // Use a handler to introduce a delay before retrying
                    new Handler(Looper.getMainLooper()).postDelayed(() -> connectToIMU2(deviceMacAddress, btAdapter, newRetryCount), 5000); // Retry after 5 seconds
                }
            } else if (task.isCompleted()) {
                Log.i("MainActivity", "Successfully connected to MetaWear board: " + deviceMacAddress);
                configureSensorFusionForLinearAcceleration(board, deviceMacAddress); // Ensure to pass along any needed parameters
                // If using gyroscope or other sensors, configure them here
            }
            return null;
        });
    }

    private void connectToIMU4(String deviceMacAddress, BluetoothAdapter btAdapter, int retryCount) {
        final BluetoothDevice remoteDevice = btAdapter.getRemoteDevice(deviceMacAddress);
        final MetaWearBoard board = serviceBinder.getMetaWearBoard(remoteDevice);

        if(retryCount == 0){
            configureSensorFusionForLinearAcceleration2(null, null);
        }
        board.connectAsync().continueWith(task -> {
            if (task.isFaulted()) {
                Log.e("MainActivity", "Failed to connect to MetaWear board: " + deviceMacAddress, task.getError());
                // Check if we should retry
                if (retryCount > 0) {
                    Log.i("MainActivity", "Attempting to reconnect to: " + deviceMacAddress + ". Retries left: " + retryCount);
                    final int newRetryCount = retryCount - 1;
                    // Use a handler to introduce a delay before retrying
                    new Handler(Looper.getMainLooper()).postDelayed(() -> connectToIMU4(deviceMacAddress, btAdapter, newRetryCount), 5000); // Retry after 5 seconds
                }
            } else if (task.isCompleted()) {
                Log.i("MainActivity", "Successfully connected to MetaWear board: " + deviceMacAddress);
                configureSensorFusionForLinearAcceleration2(board, deviceMacAddress); // Ensure to pass along any needed parameters
                // If using gyroscope or other sensors, configure them here
            }
            return null;
        });
    }

    private void configureSensorFusionForLinearAcceleration(MetaWearBoard board, String deviceMacAddress) {
        // Obtain the SensorFusion module from the board

        if(board==null && deviceMacAddress==null) {
            if (numOfSensors >= 3 && sensorsConnected[2] == false) {
                // If this is the first device and we haven't attempted to connect to the second device yet, do so now
                if (!thirdDeviceConnectionAttempted) {
                    thirdDeviceConnectionAttempted = true; // Prevent multiple connection attempts
                    sensorsConnected[2] = true;
                    // Use a handler to post a task for connecting to the second device, allows you to add a slight delay if necessary
                    new Handler(Looper.getMainLooper()).post(() -> {
                        final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
                        final BluetoothAdapter btAdapter = btManager.getAdapter();
                        connectToIMU3(DEVICE_MAC_ADDRESS_3, btAdapter, 5);
                    });
                }
            }
        }

        else {
            SensorFusionBosch sensorFusion = board.getModule(SensorFusionBosch.class);
            boardsConnected[1] = board;
            if (sensorFusion == null) {
                Log.e("MainActivity", "Sensor Fusion module not available on this device: " + deviceMacAddress);
                return;
            }

            // Configure the sensor fusion module
            sensorFusion.configure()
                    .mode(Mode.NDOF)
                    .accRange(AccRange.AR_2G)
                    .gyroRange(GyroRange.GR_250DPS)
                    .commit();

            // Subscribe to linear acceleration data
            sensorFusion.linearAcceleration().addRouteAsync(source -> source.stream((data, env) -> {
                // Handle linear acceleration data here
                //Log.i("MainActivity", "Linear Acceleration from " + deviceMacAddress + ": " + data.value(Acceleration.class).toString());

                String linearValue =
                        data.value(Acceleration.class).x() + "," +
                                data.value(Acceleration.class).y() + "," +
                                data.value(Acceleration.class).z() + "," +
                                data.timestamp().getTimeInMillis();

                message = "Name"+deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Acceleration.class).x() + " " + data.value(Acceleration.class).y() + " " + data.value(Acceleration.class).z();
                addNewData(message);
                ArrayList<String> retData = getData();

                if(retData.size() >= 100){
                    Gson gson = new Gson();
                    String json = gson.toJson(retData);
                    MqttPublisher publisher = new MqttPublisher("tcp://192.168.0.231:1883", "AndroidClient");  //nuc
                    //MqttPublisher publisher = new MqttPublisher("tcp://195.251.196.168:1883", "AndroidClient");    //orthopedikh
                    //https://147.102.33.212/index.html

                    publisher.connect();
                    publisher.publish("location/123", json, 2);
                    publisher.disconnect();
                    clearData();
                }
                if (creationLocallyCSVs){
                    // Create folder in external storage
                    File folder = new File(Environment.getExternalStorageDirectory(), "MyLogs");
                    if (!folder.exists()) {
                        if (!folder.mkdirs()) {
                            Log.e(TAG, "Failed to create directory");
                            return;
                        }
                    }

                    // Write to CSV file inside the folder
                    File file = new File(folder, "log_linear_sensor2_data.csv");
                    try {
                        FileWriter csvWriter = new FileWriter(file, true);
                        // Check if file is empty and add headers if so
                        if (file.length() == 0) {
                            csvWriter.append("imu,x,y,z,time\n");
                        }
                        csvWriter.append(deviceMacAddress);
                        csvWriter.append(",");
                        csvWriter.append(linearValue);
                        csvWriter.append("\n");
                        csvWriter.flush();
                        csvWriter.close();
                        Log.i(TAG, "Data written to " + file.getAbsolutePath());
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }

                if (numOfSensors >= 3 && sensorsConnected[2] == false) {
                    if (DEVICE_MAC_ADDRESS_2.equals(deviceMacAddress) && !thirdDeviceConnectionAttempted) {
                        thirdDeviceConnectionAttempted = true; // Prevent multiple connection attempts
                        sensorsConnected[2] = true;
                        // Use a handler to post a task for connecting to the second device, allows you to add a slight delay if necessary
                        new Handler(Looper.getMainLooper()).post(() -> {
                            final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
                            final BluetoothAdapter btAdapter = btManager.getAdapter();
                            connectToIMU3(DEVICE_MAC_ADDRESS_3, btAdapter, 5);
                        });
                    }
                }
            })).continueWith((Continuation<Route, Void>) ignored -> {
                sensorFusion.linearAcceleration().start();
                sensorFusion.start();
                return null;
            });
        }
    }

    private void configureSensorFusionForLinearAcceleration2(MetaWearBoard board, String deviceMacAddress) {
        // Obtain the SensorFusion module from the board

        if(board==null && deviceMacAddress==null) {
            return;
        }

        else {


            SensorFusionBosch sensorFusion = board.getModule(SensorFusionBosch.class);
            boardsConnected[3] = board;
            if (sensorFusion == null) {
                Log.e("MainActivity", "Sensor Fusion module not available on this device: " + deviceMacAddress);
                return;
            }

            // Configure the sensor fusion module
            sensorFusion.configure()
                    .mode(Mode.NDOF)
                    .accRange(AccRange.AR_2G)
                    .gyroRange(GyroRange.GR_250DPS)
                    .commit();

            // Subscribe to linear acceleration data
            sensorFusion.linearAcceleration().addRouteAsync(source -> source.stream((data, env) -> {
                // Handle linear acceleration data here
                //Log.i("MainActivity", "Linear Acceleration from " + deviceMacAddress + ": " + data.value(Acceleration.class).toString());

                String linearValue =
                        data.value(Acceleration.class).x() + "," +
                                data.value(Acceleration.class).y() + "," +
                                data.value(Acceleration.class).z() + "," +
                                data.timestamp().getTimeInMillis();

                message = "Name"+deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Acceleration.class).x() + " " + data.value(Acceleration.class).y() + " " + data.value(Acceleration.class).z();
                addNewData(message);
                ArrayList<String> retData = getData();

                if(retData.size() >= 100){
                    Gson gson = new Gson();
                    String json = gson.toJson(retData);
                    MqttPublisher publisher = new MqttPublisher("tcp://192.168.0.231:1883", "AndroidClient");  //nuc
                    //MqttPublisher publisher = new MqttPublisher("tcp://195.251.196.168:1883", "AndroidClient");    //orthopedikh
                    //https://147.102.33.212/index.html

                    publisher.connect();
                    publisher.publish("location/123", json, 2);
                    publisher.disconnect();
                    clearData();
                }

                if (creationLocallyCSVs) {
                    // Create folder in external storage
                    File folder = new File(Environment.getExternalStorageDirectory(), "MyLogs");
                    if (!folder.exists()) {
                        if (!folder.mkdirs()) {
                            Log.e(TAG, "Failed to create directory");
                            return;
                        }
                    }

                    // Write to CSV file inside the folder
                    File file = new File(folder, "log_linear_sensor4_data.csv");
                    try {
                        FileWriter csvWriter = new FileWriter(file, true);
                        // Check if file is empty and add headers if so
                        if (file.length() == 0) {
                            csvWriter.append("imu,x,y,z,time\n");
                        }
                        csvWriter.append(deviceMacAddress);
                        csvWriter.append(",");
                        csvWriter.append(linearValue);
                        csvWriter.append("\n");
                        csvWriter.flush();
                        csvWriter.close();
                        Log.i(TAG, "Data written to " + file.getAbsolutePath());
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }

            })).continueWith((Continuation<Route, Void>) ignored -> {
                sensorFusion.linearAcceleration().start();
                sensorFusion.start();
                return null;
            });

            MqttPublisher publisher = new MqttPublisher("tcp://192.168.0.231:1883", "AndroidClient");  //nuc
            //MqttPublisher publisher = new MqttPublisher("tcp://195.251.196.168:1883", "AndroidClient");    //orthopedikh
            publisher.connect();
            publisher.publish("location/123", "start", 2);
            publisher.disconnect();


            new Thread(() -> {
                try{
                    Thread.sleep(60000);
                } catch (Exception e) {
                }
                new Thread(() -> {
                    for(int i=0;i<numOfSensors;i++){
                        if(sensorsConnected[i]){
                            boardsConnected[i].disconnectAsync().continueWith(new Continuation<Void, Void>() {
                                @Override
                                public Void then(Task<Void> task) throws Exception {
                                    Log.i("MainActivity", "Disconnected!!!!!!!");
                                    return null;
                                }
                            });
                        }
                    }
                    //MqttPublisher jsonPublisher = new MqttPublisher("tcp://195.251.196.168:1883", "AndroidClient");   //orthopedikh
                    MqttPublisher jsonPublisher = new MqttPublisher("tcp://192.168.0.231:1883", "AndroidClient");  //nuc
                    jsonPublisher.connect();
                    jsonPublisher.publish("location/123", "stop", 2);
                    jsonPublisher.disconnect();
                    try {
                        Thread.sleep(5000);
                        System.exit(1);
                    } catch (InterruptedException e) {
                        throw new RuntimeException(e);
                    }
                }).start();
            }).start();
        }
    }

    private void configureQuantranion(MetaWearBoard board, String deviceMacAddress) {

        if(board==null && deviceMacAddress==null) {
            if (numOfSensors >= 2 && sensorsConnected[1] == false) {
                // If this is the first device and we haven't attempted to connect to the second device yet, do so now
                if (!secondDeviceConnectionAttempted) {
                    secondDeviceConnectionAttempted = true; // Prevent multiple connection attempts
                    sensorsConnected[1] = true;
                    // Use a handler to post a task for connecting to the second device, allows you to add a slight delay if necessary
                    new Handler(Looper.getMainLooper()).post(() -> {
                        final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
                        final BluetoothAdapter btAdapter = btManager.getAdapter();
                        connectToIMU2(DEVICE_MAC_ADDRESS_2, btAdapter, 5);
                    });
                }
            }

        }

        else {
            sensorsConnected[0] = true;
            AccelerometerMma8452q accelerometerBosch = board.getModule((AccelerometerMma8452q.class));

            SensorFusionBosch sensorFusion = board.getModule(SensorFusionBosch.class);
            boardsConnected[0] = board;
            if (sensorFusion == null) {
                Log.e("MainActivity", "Sensor Fusion module not available on this device.");

            }
            sensorFusion.configure()
                    .mode(SensorFusionBosch.Mode.NDOF)
                    .accRange(AccRange.AR_2G)
                    .gyroRange(GyroRange.GR_250DPS)
                    .commit();
            // Configure the sensor fusion module

            sensorFusion.quaternion().addRouteAsync(source -> source.stream((data, env) -> {
                // Handle accelerometer data here
                //String logMessage = "Log.i(\"MainActivity\", \"Quantranion from \" + deviceMacAddress + \": \" + data.value(Quaternion.class).toString());";

                String quaternionValue = data.value(Quaternion.class).w() + "," +
                        data.value(Quaternion.class).x() + "," +
                        data.value(Quaternion.class).y() + "," +
                        data.value(Quaternion.class).z() + "," +
                        data.timestamp().getTimeInMillis();

                message = "Name"+deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Quaternion.class).w() + " " + data.value(Quaternion.class).x() + " " + data.value(Quaternion.class).y() + " " + data.value(Quaternion.class).z();
                addNewData(message);
                ArrayList<String> retData = getData();

                if(retData.size() >= 100){
                    Gson gson = new Gson();
                    String json = gson.toJson(retData);
                    MqttPublisher publisher = new MqttPublisher("tcp://192.168.0.231:1883", "AndroidClient");  //nuc
                    //MqttPublisher publisher = new MqttPublisher("tcp://195.251.196.168:1883", "AndroidClient");    //orthopedikh
                    //https://147.102.33.212/index.html

                    publisher.connect();
                    publisher.publish("location/123", json, 2);
                    publisher.disconnect();
                    clearData();
                }

                if (creationLocallyCSVs) {
                    // Create folder in external storage
                    File folder = new File(Environment.getExternalStorageDirectory(), "MyLogs");
                    if (!folder.exists()) {
                        if (!folder.mkdirs()) {
                            Log.e(TAG, "Failed to create directory");
                            return;
                        }
                    }

                    // Write to CSV file inside the folder
                    File file = new File(folder, "log_quat_sensor1_data.csv");
                    try {
                        FileWriter csvWriter = new FileWriter(file, true);
                        // Check if file is empty and add headers if so
                        if (file.length() == 0) {
                            csvWriter.append("imu,w,x,y,z,time\n");
                        }
                        csvWriter.append(deviceMacAddress);
                        csvWriter.append(",");
                        csvWriter.append(quaternionValue);
                        csvWriter.append("\n");
                        csvWriter.flush();
                        csvWriter.close();
                        Log.i(TAG, "Data written to " + file.getAbsolutePath());
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                }

                if (numOfSensors >= 2 && sensorsConnected[1] == false) {
                    // If this is the first device and we haven't attempted to connect to the second device yet, do so now
                    if (DEVICE_MAC_ADDRESS_1.equals(deviceMacAddress) && !secondDeviceConnectionAttempted) {
                        secondDeviceConnectionAttempted = true; // Prevent multiple connection attempts
                        sensorsConnected[1] = true;
                        // Use a handler to post a task for connecting to the second device, allows you to add a slight delay if necessary
                        new Handler(Looper.getMainLooper()).post(() -> {
                            final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
                            final BluetoothAdapter btAdapter = btManager.getAdapter();
                            connectToIMU2(DEVICE_MAC_ADDRESS_2, btAdapter, 5);
                        });
                    }
                }

            })).continueWith((Continuation<Route, Void>) ignored -> {
                sensorFusion.quaternion().start();
                sensorFusion.start();
                return null;
            });


        }
    }

    private void configureQuantranion2(MetaWearBoard board, String deviceMacAddress) {
        if(board==null && deviceMacAddress==null) {
            if (numOfSensors >= 4 && sensorsConnected[3] == false) {
                // If this is the first device and we haven't attempted to connect to the second device yet, do so now
                if (!forthDeviceConnectionAttempted) {
                    forthDeviceConnectionAttempted = true; // Prevent multiple connection attempts
                    sensorsConnected[3] = true;
                    // Use a handler to post a task for connecting to the second device, allows you to add a slight delay if necessary
                    new Handler(Looper.getMainLooper()).post(() -> {
                        final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
                        final BluetoothAdapter btAdapter = btManager.getAdapter();
                        connectToIMU4(DEVICE_MAC_ADDRESS_4, btAdapter, 5);
                    });
                }
            }
        }

        else {

            AccelerometerMma8452q accelerometerBosch = board.getModule((AccelerometerMma8452q.class));

            SensorFusionBosch sensorFusion = board.getModule(SensorFusionBosch.class);
            boardsConnected[2] = board;
            if (sensorFusion == null) {
                Log.e("MainActivity", "Sensor Fusion module not available on this device.");

            }
            sensorFusion.configure()
                    .mode(SensorFusionBosch.Mode.NDOF) // NDOF mode for comprehensive motion tracking
                    .accRange(AccRange.AR_2G) // Accelerometer range ±2g
                    .gyroRange(GyroRange.GR_250DPS) // Gyroscope range ±250 degrees per second
                    .commit(); // Apply the configuration
            // Configure the sensor fusion module

            sensorFusion.quaternion().addRouteAsync(source -> source.stream((data, env) -> {
                // Handle accelerometer data here
                //String logMessage = "Log.i(\"MainActivity\", \"Quantranion from \" + deviceMacAddress + \": \" + data.value(Quaternion.class).toString());";

                String quaternionValue = data.value(Quaternion.class).w() + "," +
                        data.value(Quaternion.class).x() + "," +
                        data.value(Quaternion.class).y() + "," +
                        data.value(Quaternion.class).z() + "," +
                        data.timestamp().getTimeInMillis();

                message = "Name"+deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Quaternion.class).w() + " " + data.value(Quaternion.class).x() + " " + data.value(Quaternion.class).y() + " " + data.value(Quaternion.class).z();
                addNewData(message);
                ArrayList<String> retData = getData();

                if(retData.size() >= 100){
                    Gson gson = new Gson();
                    String json = gson.toJson(retData);
                    MqttPublisher publisher = new MqttPublisher("tcp://192.168.0.231:1883", "AndroidClient");  //nuc
                    //MqttPublisher publisher = new MqttPublisher("tcp://195.251.196.168:1883", "AndroidClient");    //orthopedikh
                    //https://147.102.33.212/index.html

                    publisher.connect();
                    publisher.publish("location/123", json, 2);
                    publisher.disconnect();
                    clearData();
                }

                if (creationLocallyCSVs) {
                    // Create folder in external storage
                    File folder = new File(Environment.getExternalStorageDirectory(), "MyLogs");
                    if (!folder.exists()) {
                        if (!folder.mkdirs()) {
                            Log.e(TAG, "Failed to create directory");
                            return;
                        }
                    }

                    // Write to CSV file inside the folder
                    File file = new File(folder, "log_quat_sensor3_data.csv");
                    try {
                        FileWriter csvWriter = new FileWriter(file, true);
                        // Check if file is empty and add headers if so
                        if (file.length() == 0) {
                            csvWriter.append("imu,w,x,y,z,time\n");
                        }
                        csvWriter.append(deviceMacAddress);
                        csvWriter.append(",");
                        csvWriter.append(quaternionValue);
                        csvWriter.append("\n");
                        csvWriter.flush();
                        csvWriter.close();
                        Log.i(TAG, "Data written to " + file.getAbsolutePath());
                    } catch (IOException e) {
                        e.printStackTrace();
                    }

                }
                if (numOfSensors >= 4 && sensorsConnected[3] == false) {
                    // If this is the first device and we haven't attempted to connect to the second device yet, do so now
                    if (DEVICE_MAC_ADDRESS_3.equals(deviceMacAddress) && !forthDeviceConnectionAttempted) {
                        forthDeviceConnectionAttempted = true; // Prevent multiple connection attempts
                        sensorsConnected[3] = true;
                        // Use a handler to post a task for connecting to the second device, allows you to add a slight delay if necessary
                        new Handler(Looper.getMainLooper()).post(() -> {
                            final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
                            final BluetoothAdapter btAdapter = btManager.getAdapter();
                            connectToIMU4(DEVICE_MAC_ADDRESS_4, btAdapter, 5);
                        });
                    }
                }

            })).continueWith((Continuation<Route, Void>) ignored -> {
                sensorFusion.quaternion().start();
                sensorFusion.start();
                return null;
            });
        }
    }

    @Override
    public void onServiceDisconnected(ComponentName name) {
        serviceBinder = null;
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Ensure you unbind from the service when the activity is destroyed
        unbindService(this);
    }
}
