package com.example.myapplication;

import static com.example.myapplication.Database.clearData;
import static com.example.myapplication.Database.getData;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
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
import com.mbientlab.metawear.data.Quaternion;
import com.mbientlab.metawear.module.SensorFusionBosch;
import com.mbientlab.metawear.module.SensorFusionBosch.AccRange;
import com.mbientlab.metawear.module.SensorFusionBosch.GyroRange;
import com.mbientlab.metawear.module.SensorFusionBosch.Mode;

import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Method;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.URI;
import java.util.ArrayList;
import java.util.Objects;
import java.util.Properties;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import bolts.Continuation;
import bolts.Task;


public class MainActivity extends AppCompatActivity implements ServiceConnection {
    private static final int REQUEST_BLUETOOTH_CONNECT_PERMISSION = 1;

    private BtleService.LocalBinder serviceBinder;
    private String DEVICE_MAC_ADDRESS_1 = "EF:0F:A9:3D:48:AA"; // Quaternion
    //private final String DEVICE_MAC_ADDRESS_1 = "ED:B1:65:CE:EF:D4";
    private String DEVICE_TYPE_1 = "Quaternion";
    private String DEVICE_MAC_ADDRESS_2 = "DA:C1:9F:1B:6E:40";
    private String DEVICE_TYPE_2 = "Quaternion";
    private String DEVICE_MAC_ADDRESS_3 = "EE:E2:E3:B4:9A:D7";
    private String DEVICE_TYPE_3 = "OFF";
    private String DEVICE_MAC_ADDRESS_4 = "EB:0B:A9:F4:5E:4E";
    private String DEVICE_TYPE_4 = "OFF";
    private boolean secondDeviceConnectionAttempted = false;
    private boolean thirdDeviceConnectionAttempted = false;
    private boolean forthDeviceConnectionAttempted = false;
    int numOfSensors = 4;    // set the number of IMUs
    boolean[] sensorsConnected = new boolean[numOfSensors];
    MetaWearBoard[] boardsConnected = new MetaWearBoard[numOfSensors];
        private String message = "";
    private boolean creationLocallyCSVs = true; //true if you want

    private FileOutputStream outputStreamSensor01;
    private FileOutputStream outputStreamSensor02;
    private FileOutputStream outputStreamSensor03;
    private FileOutputStream outputStreamSensor04;
    private MqttPublisher mqttPublisher;

    private BluetoothManager btManager;
    private BluetoothAdapter btAdapter;
    private ConcurrentLinkedQueue<SensorData> sensorDataQueue;

    private ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);


    private static final String MULTICAST_GROUP = "224.1.1.1";
    private static final int MULTICAST_PORT = 10000;
    private String mqttServerIp;
    private MqttClient mqttClient;


    //private ActivityBus activityBus;



    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        Log.i("MainActivity", "I entered MainActivity");
        //initializeBLEvariables();
        //loadConfig();


        //AsyncTask<Void, Void, Void> mcs = new MulticastSender("multicast").execute();


        //mqttPublisher = new MqttPublisher("tcp://192.168.1.109:1883", "AndroidClient", this);
        //mqttPublisher = new MqttPublisher("tcp://192.168.0.247:1883", "AndroidClient", this); //medlab
        //mqttPublisher = new MqttPublisher("tcp://192.168.1.96:1883", "AndroidClient", this); //vtsakan
        //mqttPublisher = new MqttPublisher(mqttServerIp, "AndroidClient", this);


        //mqttPublisher.connect();
        //mqttPublisher.subscribe("IMUsettings", 1);
        //mqttPublisher.publish("IMUsettings", "up", 1);

        //publishDataToServer();

        // Check if the BLUETOOTH_CONNECT permission is granted
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.BLUETOOTH_CONNECT)
                    != PackageManager.PERMISSION_GRANTED) {
                // Permission not granted, request it
                ActivityCompat.requestPermissions(this,
                        new String[]{Manifest.permission.BLUETOOTH_CONNECT},
                        REQUEST_BLUETOOTH_CONNECT_PERMISSION);

            } else {
                Log.i("VERSION", "OK");
            }
        } else {
            Log.i("VERSION", "LOW VERSION");
        }
        try {
            outputStreamSensor01 = openFileOutput("SENSOR01.csv", Context.MODE_PRIVATE);
            outputStreamSensor02 = openFileOutput("SENSOR02.csv", Context.MODE_PRIVATE);
            outputStreamSensor03 = openFileOutput("SENSOR03.csv", Context.MODE_PRIVATE);
            outputStreamSensor04 = openFileOutput("SENSOR04.csv", Context.MODE_PRIVATE);
            Log.i("FILES", "FILES CREATED SUCCESSFULLY");

            // Get the path to the internal storage directory
            String filesDir = getFilesDir().getAbsolutePath();

            // Print the path using Log
            Log.d("FilesDir", "Path to getFilesDir(): " + filesDir);



        } catch (IOException e) {
            e.printStackTrace();
        }

        // Bind to the MetaWear BtleService
        //Intent intent = new Intent(this, BtleService.class);
        //bindService(intent, this, 1);
        //moveTaskToBack(true);

        String serverURI = "tcp://192.168.1.96:1883";
        String clientId = "your_client_id";

        try {
            mqttClient = new MqttClient(serverURI, clientId, new MemoryPersistence());
            MqttConnectOptions options = new MqttConnectOptions();

            mqttClient.setCallback(new MqttCallbackExtended() {
                @Override
                public void connectComplete(boolean reconnect, String serverURI)
                {
                    // Connection successful
                    try {
                        mqttClient.subscribe("your_topic", 0);
                    } catch (MqttException e) {
                        e.printStackTrace();
                    }
                }

                @Override
                public void connectionLost(Throwable cause) {
                    // Connection lost
                }

                @Override
                public void messageArrived(String topic, MqttMessage message) throws Exception {
                    // Message received  

                    String messagePayload = new String(message.getPayload());
                    // Update UI with messagePayload
                }

                @Override
                public void deliveryComplete(IMqttDeliveryToken token) {
                    // Message delivery complete
                }
            });

            mqttClient.connect(options);

            if (mqttClient.isConnected()) {
                Log.i("MainActivity", "Client is connected.");
            } else {
                Log.i("MainActivity", "Client is not connected.");
            }

            mqttClient.subscribe("test", 0);


        } catch (MqttException e) {
            e.printStackTrace();
        }
    }


    private void loadConfig() {
        Properties properties = new Properties();
        try {
            InputStream rawResource = getResources().openRawResource(R.raw.config);
            properties.load(rawResource);
            mqttServerIp = properties.getProperty("mqtt_server_ip");
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void disconnectAndShutdown() {
        // Schedule a task to disconnect IMUs and shutdown the app after 60 seconds
        scheduler.schedule(() -> {
            // Disconnect all connected IMUs
            for (int k = 0; k < numOfSensors; k++) {
                if (sensorsConnected[k]) {
                    int finalK = k;
                    boardsConnected[k].disconnectAsync().continueWith(new Continuation<Void, Void>() {
                        @Override
                        public Void then(Task<Void> task) throws Exception {
                            Log.i("MainActivity", "Disconnected from IMU: " + finalK);
                            return null;
                        }
                    });
                }
            }

            // Schedule shutdown after 5 seconds to ensure all disconnects are completed
            scheduler.schedule(() -> {
                Log.i("MainActivity", "Shutting down the application.");
                //System.exit(1);
            }, 5, TimeUnit.SECONDS);
        }, 60, TimeUnit.SECONDS);

    }


    private void disconnectBoards() {

        numOfSensors = 4;
        scheduler.schedule(() -> {
            for (int k = 0; k < numOfSensors; k++) {
                if (sensorsConnected[k]) {
                    int finalK = k;
                    boardsConnected[k].disconnectAsync().continueWith(new Continuation<Void, Void>() {
                        @Override
                        public Void then(Task<Void> task) throws Exception {
                            Log.i("MainActivity", "Disconnected from IMU: " + finalK);
                            return null;
                        }
                    });
                }
            }
        }, 5, TimeUnit.SECONDS);
    }


    //@Override
    public void onServiceConnected(ComponentName name, IBinder service) {
        Log.i("MainActivity", "Service Connected");
        serviceBinder = (BtleService.LocalBinder) service;
        initiateConnection();

        //final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
        //final BluetoothAdapter btAdapter = btManager.getAdapter();

        // Connect to the first MetaWear board
        //if (DEVICE_TYPE_1 != "OFF") {
        //    connectToIMU1(DEVICE_MAC_ADDRESS_1, btAdapter, 5);
        //}
        //else if (DEVICE_TYPE_2 != "OFF") {
        //    connectToIMU2(DEVICE_MAC_ADDRESS_2, btAdapter, 5);
        //}
        //else if (DEVICE_TYPE_3 != "OFF") {
        //    connectToIMU3(DEVICE_MAC_ADDRESS_3, btAdapter, 5);
        //}
        //else if (DEVICE_TYPE_4 != "OFF") {
        //    connectToIMU4(DEVICE_MAC_ADDRESS_4, btAdapter, 5);
        //}
    }


    private void initiateConnection() {

        // Check if any device type is not "OFF" and initiate connection accordingly
        if (DEVICE_TYPE_1 != "OFF") {
            Log.i(DEVICE_MAC_ADDRESS_1, "connecting to 1");
            //connectToIMU1(DEVICE_MAC_ADDRESS_1, btAdapter, 5);
        }
        /*
        if (DEVICE_TYPE_2 != "OFF") {
            connectToIMU2(DEVICE_MAC_ADDRESS_2, btAdapter, 5);
        }
        if (DEVICE_TYPE_3 != "OFF") {
            connectToIMU3(DEVICE_MAC_ADDRESS_3, btAdapter, 5);
        }
        if (DEVICE_TYPE_4 != "OFF") {
            connectToIMU4(DEVICE_MAC_ADDRESS_4, btAdapter, 5);
        }*/
    }
    private void connectToIMU1(String deviceMacAddress, BluetoothAdapter btAdapter, int retryCount) {
        final BluetoothDevice remoteDevice = btAdapter.getRemoteDevice(deviceMacAddress);
        final MetaWearBoard board = serviceBinder.getMetaWearBoard(remoteDevice);
        final long connectionTimeout = 15000; // 15 seconds

        if (retryCount == 0) {
            configure_device_1(null, null);
        }

        // Properly disconnect the board before retrying connection
        if (board != null && board.isConnected()) {
            Log.i("MainActivity", "Disconnecting previous connection before retry...");
            disconnectIMU(board);
        }

        board.connectAsync().continueWithTask(task -> {
            if (task.isFaulted() || task.isCancelled()) {
                Log.e("MainActivity", "Failed to connect to MetaWear board: " + deviceMacAddress, task.getError());

                // Ensure proper disconnection if connection fails
                disconnectIMU(board);

                // Reconnect logic using the `HomeActivity.reconnect` method
                return Task.forResult(null);//reconnect(this, board, 0L, 3, false);
            } else if (task.isCompleted()) {
                Log.i("MainActivity", "Successfully connected to MetaWear board: " + deviceMacAddress);
                configure_device_1(board, deviceMacAddress); // Ensure to pass along any needed parameters
                return Task.forResult(null);
            }
            return Task.forResult(null);
        }).continueWith(task -> {
            // Retry connection logic
            if (task.isFaulted()) {
                if (retryCount > 0) {
                    Log.i("MainActivity", "Attempting to reconnect to: " + deviceMacAddress + ". Retries left: " + retryCount);
                    final int newRetryCount = retryCount - 1;
                    // Use a handler to introduce a delay before retrying
                    new Handler(Looper.getMainLooper()).postDelayed(() -> connectToIMU1(deviceMacAddress, btAdapter, newRetryCount), 15000); // Retry after 15 seconds
                }
            }
            return null;
        });
    }

    private void disconnectIMU(MetaWearBoard board) {
        if (board != null) {
            board.disconnectAsync().continueWith(task -> {
                Log.i("MainActivity", "Disconnected from MetaWear board");
                return null;
            });
        }
    }


    private boolean refreshDeviceCache(BluetoothGatt gatt) {
        try {
            // Using reflection to clear the GATT cache
            Method refresh = gatt.getClass().getMethod("refresh");
            if (refresh != null) {
                boolean result = (boolean) refresh.invoke(gatt);
                Log.i("MainActivity", "GATT cache refresh result: " + result);
                return result;
            }
        } catch (Exception e) {
            Log.e("MainActivity", "An error occurred while refreshing device cache", e);
        }
        return false;
    }


    private void connectToIMU2(String deviceMacAddress, BluetoothAdapter btAdapter, int retryCount) {
        final BluetoothDevice remoteDevice = btAdapter.getRemoteDevice(deviceMacAddress);
        final MetaWearBoard board = serviceBinder.getMetaWearBoard(remoteDevice);

        if(retryCount == 0){
            configure_device_2(null, null);
        }
        board.connectAsync().continueWith(task -> {
            if (task.isFaulted()) {
                Log.e("MainActivity", "Failed to connect to MetaWear board: " + deviceMacAddress, task.getError());
                // Check if we should retry
                if (retryCount > 0) {
                    Log.i("MainActivity", "Attempting to reconnect to: " + deviceMacAddress + ". Retries left: " + retryCount);
                    final int newRetryCount = retryCount - 1;
                    // Use a handler to introduce a delay before retrying
                    new Handler(Looper.getMainLooper()).postDelayed(() -> connectToIMU2(deviceMacAddress, btAdapter, newRetryCount), 10000); // Retry after 5 seconds
                }
            } else if (task.isCompleted()) {
                Log.i("MainActivity", "Successfully connected to MetaWear board: " + deviceMacAddress);
                //configureSensorFusionForLinearAcceleration(board, deviceMacAddress); // Ensure to pass along any needed parameters
                configure_device_2(board, deviceMacAddress);
                // If using gyroscope or other sensors, configure them here

            }
            return null;
        });
    }


    private void connectToIMU3(String deviceMacAddress, BluetoothAdapter btAdapter, int retryCount) {
        final BluetoothDevice remoteDevice = btAdapter.getRemoteDevice(deviceMacAddress);
        final MetaWearBoard board = serviceBinder.getMetaWearBoard(remoteDevice);

        if(retryCount == 0){
            configure_device_3(null, null);
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
                //configureQuantranion2(board, deviceMacAddress); // Ensure to pass along any needed parameters
                configure_device_3(board, deviceMacAddress);
            }
            return null;
        });
    }

    private void connectToIMU4(String deviceMacAddress, BluetoothAdapter btAdapter, int retryCount) {
        final BluetoothDevice remoteDevice = btAdapter.getRemoteDevice(deviceMacAddress);
        final MetaWearBoard board = serviceBinder.getMetaWearBoard(remoteDevice);

        if(retryCount == 0){
            configure_device_4(null, null);
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
                //configureSensorFusionForLinearAcceleration2(board, deviceMacAddress); // Ensure to pass along any needed parameters
                configure_device_4(board, deviceMacAddress);
            }
            return null;
        });
    }



    private void configure_device_1(MetaWearBoard board, String deviceMacAddress) {

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
                        if (!DEVICE_TYPE_2.equals("OFF")) {
                            connectToIMU2(DEVICE_MAC_ADDRESS_2, btAdapter, 5);
                        }
                    });
                }
            }

        }

        else {
            sensorsConnected[0] = true;
            boardsConnected[0] = board;
            SensorFusionBosch sensorFusion = board.getModule(SensorFusionBosch.class);

            if (Objects.equals(DEVICE_TYPE_1, "Linear")) {
                if (sensorFusion == null) {
                    Log.e("MainActivity", "Sensor Fusion module not available on this device: " + deviceMacAddress);
                    return;
                }
                Log.e(DEVICE_MAC_ADDRESS_1, "Configuring 1");
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
                                    data.timestamp().getTimeInMillis() + "\n";

                    message = "Name" + deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Acceleration.class).x() + " " + data.value(Acceleration.class).y() + " " + data.value(Acceleration.class).z();
                    Log.i("1->", message);
                    SensorData mydata = new SensorData();
                    mydata.setDeviceMacAddress(deviceMacAddress);
                    mydata.setTimestamp(data.timestamp().getTimeInMillis());
                    mydata.setX(data.value(Acceleration.class).x());
                    mydata.setY(data.value(Acceleration.class).y());
                    mydata.setZ(data.value(Acceleration.class).z());
                    sensorDataQueue.offer(mydata);
                    //addNewData(message);
                    //Log.e("Sensor1", message);
                    ArrayList<String> retData = getData();

                    if(retData.size() >= 100){
                        try {
                            Gson gson = new Gson();

                            clearData();
                        }catch (Exception e)
                        {
                            e.printStackTrace();
                        }
                    }
                    if (creationLocallyCSVs){
                        try {
                            if ( (sensorsConnected[0] || DEVICE_TYPE_1 == "OFF") &&
                                    (sensorsConnected[1] || DEVICE_TYPE_2 == "OFF") &&
                                    (sensorsConnected[2] || DEVICE_TYPE_3 == "OFF") &&
                                    (sensorsConnected[3] || DEVICE_TYPE_4 == "OFF") )
                                        outputStreamSensor01.write(linearValue.getBytes());
                        } catch (IOException e) {
                            e.printStackTrace();
                        }

                    }

                    if (numOfSensors >= 2 && sensorsConnected[1] == false) {
                        if (DEVICE_MAC_ADDRESS_1.equals(deviceMacAddress) && !secondDeviceConnectionAttempted) {
                            secondDeviceConnectionAttempted = true; // Prevent multiple connection attempts
                            sensorsConnected[1] = true;
                            // Use a handler to post a task for connecting to the second device, allows you to add a slight delay if necessary
                            new Handler(Looper.getMainLooper()).post(() -> {
                                final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
                                final BluetoothAdapter btAdapter = btManager.getAdapter();
                                if (DEVICE_TYPE_2 != "OFF") {
                                    connectToIMU2(DEVICE_MAC_ADDRESS_2, btAdapter, 5);
                                }
                            });
                        }
                    }
                })).continueWith((Continuation<Route, Void>) ignored -> {
                    sensorFusion.linearAcceleration().start();
                    sensorFusion.start();
                    return null;
                });

            } else {

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

                    String quaternionValue =
                            data.value(Quaternion.class).w() + "," +
                            data.value(Quaternion.class).x() + "," +
                            data.value(Quaternion.class).y() + "," +
                            data.value(Quaternion.class).z() + "," +
                            data.timestamp().getTimeInMillis()+ "\n";

                    message = "Name"+deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Quaternion.class).w() + " " + data.value(Quaternion.class).x() + " " + data.value(Quaternion.class).y() + " " + data.value(Quaternion.class).z();
                    //addNewData(message);
                    //Log.i("1->", message);
                    SensorData mydata = new SensorData();
                    mydata.setDeviceMacAddress(deviceMacAddress);
                    mydata.setTimestamp(data.timestamp().getTimeInMillis());
                    mydata.setX(data.value(Quaternion.class).x());
                    mydata.setY(data.value(Quaternion.class).y());
                    mydata.setZ(data.value(Quaternion.class).z());
                    mydata.setW(data.value(Quaternion.class).w());
                    sensorDataQueue.offer(mydata);

                    ArrayList<String> retData = getData();

                    if(retData.size() >= 100){
                        try {
                            Gson gson = new Gson();

                            clearData();
                        }
                        catch (Exception e)
                        {
                            e.printStackTrace();
                        }
                    }

                    if (creationLocallyCSVs) {
                        try {
                            if ( (sensorsConnected[0] || DEVICE_TYPE_1 == "OFF") &&
                                    (sensorsConnected[1] || DEVICE_TYPE_2 == "OFF") &&
                                    (sensorsConnected[2] || DEVICE_TYPE_3 == "OFF") &&
                                    (sensorsConnected[3] || DEVICE_TYPE_4 == "OFF") )
                                        outputStreamSensor01.write(quaternionValue.getBytes());
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
                                if (!DEVICE_TYPE_2.equals("OFF")) {
                                    connectToIMU2(DEVICE_MAC_ADDRESS_2, btAdapter, 5);
                                }
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
    }

    private void configure_device_2(MetaWearBoard board, String deviceMacAddress) {
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
                        if (!DEVICE_TYPE_3.equals("OFF")) {
                            connectToIMU3(DEVICE_MAC_ADDRESS_3, btAdapter, 5);
                        }
                    });
                }
            }
        }

        else {
            SensorFusionBosch sensorFusion = board.getModule(SensorFusionBosch.class);

            boardsConnected[1] = board;
            sensorsConnected[1] = true;

            if (Objects.equals(DEVICE_TYPE_2, "Linear")) {
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
                                    data.timestamp().getTimeInMillis() + "\n";

                    message = "Name" + deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Acceleration.class).x() + " " + data.value(Acceleration.class).y() + " " + data.value(Acceleration.class).z();
                    //addNewData(message);
                    SensorData mydata = new SensorData();
                    mydata.setDeviceMacAddress(deviceMacAddress);
                    mydata.setTimestamp(data.timestamp().getTimeInMillis());
                    mydata.setX(data.value(Acceleration.class).x());
                    mydata.setY(data.value(Acceleration.class).y());
                    mydata.setZ(data.value(Acceleration.class).z());
                    sensorDataQueue.offer(mydata);

                    //Log.i("Sensor2", message);
                    ArrayList<String> retData = getData();

                    if (retData.size() >= 100) {
                        try {
                            Gson gson = new Gson();

                            clearData();
                        } catch (Exception e) {
                            e.printStackTrace();
                        }
                    }
                    if (creationLocallyCSVs) {

                        try {
                            if ( (sensorsConnected[0] || DEVICE_TYPE_1 == "OFF") &&
                                    (sensorsConnected[1] || DEVICE_TYPE_2 == "OFF") &&
                                    (sensorsConnected[2] || DEVICE_TYPE_3 == "OFF") &&
                                    (sensorsConnected[3] || DEVICE_TYPE_4 == "OFF") )
                                        outputStreamSensor02.write(linearValue.getBytes());
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
                                if (!DEVICE_TYPE_3.equals("OFF")) {
                                    connectToIMU3(DEVICE_MAC_ADDRESS_3, btAdapter, 5);
                                }
                            });
                        }
                    }
                })).continueWith((Continuation<Route, Void>) ignored -> {
                    sensorFusion.linearAcceleration().start();
                    sensorFusion.start();
                    return null;
                });
            }
            else if (Objects.equals(DEVICE_TYPE_2, "Quaternion")) {
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

                    String quaternionValue =
                            data.value(Quaternion.class).w() + "," +
                                    data.value(Quaternion.class).x() + "," +
                                    data.value(Quaternion.class).y() + "," +
                                    data.value(Quaternion.class).z() + "," +
                                    data.timestamp().getTimeInMillis()+ "\n";

                    message = "Name"+deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Quaternion.class).w() + " " + data.value(Quaternion.class).x() + " " + data.value(Quaternion.class).y() + " " + data.value(Quaternion.class).z();
                    //addNewData(message);
                    //Log.i("2->", message);
                    SensorData mydata = new SensorData();
                    mydata.setDeviceMacAddress(deviceMacAddress);
                    mydata.setTimestamp(data.timestamp().getTimeInMillis());
                    mydata.setX(data.value(Quaternion.class).x());
                    mydata.setY(data.value(Quaternion.class).y());
                    mydata.setZ(data.value(Quaternion.class).z());
                    mydata.setW(data.value(Quaternion.class).w());
                    sensorDataQueue.offer(mydata);

                    ArrayList<String> retData = getData();

                    if(retData.size() >= 100){
                        try {
                            Gson gson = new Gson();

                            clearData();
                        }
                        catch (Exception e)
                        {
                            e.printStackTrace();
                        }
                    }

                    if (creationLocallyCSVs) {
                        try {
                            if ( (sensorsConnected[0] || DEVICE_TYPE_1 == "OFF") &&
                                    (sensorsConnected[1] || DEVICE_TYPE_2 == "OFF") &&
                                    (sensorsConnected[2] || DEVICE_TYPE_3 == "OFF") &&
                                    (sensorsConnected[3] || DEVICE_TYPE_4 == "OFF") )
                                        outputStreamSensor02.write(quaternionValue.getBytes());
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }

                    if (numOfSensors >= 3 && sensorsConnected[2] == false) {
                        // If this is the first device and we haven't attempted to connect to the second device yet, do so now
                        if (DEVICE_MAC_ADDRESS_2.equals(deviceMacAddress) && !thirdDeviceConnectionAttempted) {
                            thirdDeviceConnectionAttempted = true; // Prevent multiple connection attempts
                            sensorsConnected[2] = true;
                            // Use a handler to post a task for connecting to the second device, allows you to add a slight delay if necessary
                            new Handler(Looper.getMainLooper()).post(() -> {
                                final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
                                final BluetoothAdapter btAdapter = btManager.getAdapter();
                                if (!DEVICE_TYPE_3.equals("OFF")) {
                                    connectToIMU3(DEVICE_MAC_ADDRESS_3, btAdapter, 5);
                                }
                            });
                        }
                    }

                })).continueWith((Continuation<Route, Void>) ignored -> {
                    sensorFusion.quaternion().start();
                    sensorFusion.start();
                    return null;
                });
            }
            else {
                if (numOfSensors >= 3 && sensorsConnected[2] == false) {
                    // If this is the first device and we haven't attempted to connect to the second device yet, do so now
                    if (DEVICE_MAC_ADDRESS_2.equals(deviceMacAddress) && !thirdDeviceConnectionAttempted) {
                        thirdDeviceConnectionAttempted = true; // Prevent multiple connection attempts
                        sensorsConnected[2] = true;
                        // Use a handler to post a task for connecting to the second device, allows you to add a slight delay if necessary
                        new Handler(Looper.getMainLooper()).post(() -> {
                            final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
                            final BluetoothAdapter btAdapter = btManager.getAdapter();
                            if (!DEVICE_TYPE_3.equals("OFF")) {
                                connectToIMU3(DEVICE_MAC_ADDRESS_3, btAdapter, 5);
                            }
                        });
                    }
                }
            }
        }
    }

    private void configure_device_3(MetaWearBoard board, String deviceMacAddress) {
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
                        if (!DEVICE_TYPE_4.equals("OFF")) {
                            connectToIMU4(DEVICE_MAC_ADDRESS_4, btAdapter, 5);
                        }
                    });
                }
            }
        }

        else {
            boardsConnected[2] = board;
            sensorsConnected[2] = true;
            SensorFusionBosch sensorFusion = board.getModule(SensorFusionBosch.class);


            if (Objects.equals(DEVICE_TYPE_3, "Quaternion")) {
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
                            data.timestamp().getTimeInMillis() + "\n";

                    message = "Name" + deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Quaternion.class).w() + " " + data.value(Quaternion.class).x() + " " + data.value(Quaternion.class).y() + " " + data.value(Quaternion.class).z();
                    //addNewData(message);
                    //Log.i("3->", message);
                    SensorData mydata = new SensorData();
                    mydata.setDeviceMacAddress(deviceMacAddress);
                    mydata.setTimestamp(data.timestamp().getTimeInMillis());
                    mydata.setX(data.value(Quaternion.class).x());
                    mydata.setY(data.value(Quaternion.class).y());
                    mydata.setZ(data.value(Quaternion.class).z());
                    mydata.setW(data.value(Quaternion.class).w());
                    sensorDataQueue.offer(mydata);
                    ArrayList<String> retData = getData();

                    if (retData.size() >= 100) {
                        try {
                            Gson gson = new Gson();

                            clearData();
                        } catch (Exception e) {
                            e.printStackTrace();
                        }
                    }

                    if (creationLocallyCSVs) {

                        try {
                            if ( (sensorsConnected[0] || DEVICE_TYPE_1 == "OFF") &&
                                    (sensorsConnected[1] || DEVICE_TYPE_2 == "OFF") &&
                                    (sensorsConnected[2] || DEVICE_TYPE_3 == "OFF") &&
                                    (sensorsConnected[3] || DEVICE_TYPE_4 == "OFF") )
                                        outputStreamSensor03.write(quaternionValue.getBytes());
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
                                if (!DEVICE_TYPE_4.equals("OFF")) {
                                    connectToIMU4(DEVICE_MAC_ADDRESS_4, btAdapter, 5);
                                }
                            });
                        }
                    }

                })).continueWith((Continuation<Route, Void>) ignored -> {
                    sensorFusion.quaternion().start();
                    sensorFusion.start();
                    return null;
                });
            }
            else if (Objects.equals(DEVICE_TYPE_3, "Linear")) {
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
                                    data.timestamp().getTimeInMillis() + "\n";

                    message = "Name" + deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Acceleration.class).x() + " " + data.value(Acceleration.class).y() + " " + data.value(Acceleration.class).z();
                    //addNewData(message);
                    SensorData mydata = new SensorData();
                    mydata.setDeviceMacAddress(deviceMacAddress);
                    mydata.setTimestamp(data.timestamp().getTimeInMillis());
                    mydata.setX(data.value(Acceleration.class).x());
                    mydata.setY(data.value(Acceleration.class).y());
                    mydata.setZ(data.value(Acceleration.class).z());
                    sensorDataQueue.offer(mydata);
                    ArrayList<String> retData = getData();

                    if (retData.size() >= 100) {
                        try {
                            Gson gson = new Gson();

                            clearData();
                        } catch (Exception e) {
                            e.printStackTrace();
                        }
                    }
                    if (creationLocallyCSVs) {
                        try {
                            if ( (sensorsConnected[0] && DEVICE_TYPE_1 == "OFF") &&
                                 (sensorsConnected[1] && DEVICE_TYPE_2 == "OFF") &&
                                 (sensorsConnected[2] && DEVICE_TYPE_3 == "OFF") &&
                                 (sensorsConnected[3] && DEVICE_TYPE_4 == "OFF") )
                                        outputStreamSensor03.write(linearValue.getBytes());
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }

                    if (numOfSensors >= 4 && sensorsConnected[3] == false) {
                        if (DEVICE_MAC_ADDRESS_3.equals(deviceMacAddress) && !forthDeviceConnectionAttempted) {
                            forthDeviceConnectionAttempted = true; // Prevent multiple connection attempts
                            sensorsConnected[3] = true;
                            // Use a handler to post a task for connecting to the second device, allows you to add a slight delay if necessary
                            new Handler(Looper.getMainLooper()).post(() -> {
                                final BluetoothManager btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
                                final BluetoothAdapter btAdapter = btManager.getAdapter();
                                if (!DEVICE_TYPE_4.equals("OFF")) {
                                    connectToIMU4(DEVICE_MAC_ADDRESS_4, btAdapter, 5);
                                }
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
        }

    private void configure_device_4(MetaWearBoard board, String deviceMacAddress) {
        // Obtain the SensorFusion module from the board

        if(board==null && deviceMacAddress==null) {
            return;
        }

        else {
            SensorFusionBosch sensorFusion = board.getModule(SensorFusionBosch.class);
            sensorsConnected[3] = true;
            boardsConnected[3] = board;
            if (sensorFusion == null) {
                Log.e("MainActivity", "Sensor Fusion module not available on this device: " + deviceMacAddress);
                return;
            }

            if (Objects.equals(DEVICE_TYPE_4, "Linear")) {

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
                                    data.timestamp().getTimeInMillis() + "\n";

                    message = "Name" + deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Acceleration.class).x() + " " + data.value(Acceleration.class).y() + " " + data.value(Acceleration.class).z();
                    //addNewData(message);
                    SensorData mydata = new SensorData();
                    mydata.setDeviceMacAddress(deviceMacAddress);
                    mydata.setTimestamp(data.timestamp().getTimeInMillis());
                    mydata.setX(data.value(Acceleration.class).x());
                    mydata.setY(data.value(Acceleration.class).y());
                    mydata.setZ(data.value(Acceleration.class).z());
                    sensorDataQueue.offer(mydata);
                    ArrayList<String> retData = getData();

                    if (retData.size() >= 100) {
                        try {
                            Gson gson = new Gson();

                            clearData();
                        } catch (Exception e) {
                            e.printStackTrace();
                        }
                    }

                    if (creationLocallyCSVs) {
                        try {
                            if ( (sensorsConnected[0] || DEVICE_TYPE_1 == "OFF") &&
                                    (sensorsConnected[1] || DEVICE_TYPE_2 == "OFF") &&
                                    (sensorsConnected[2] || DEVICE_TYPE_3 == "OFF") &&
                                    (sensorsConnected[3] || DEVICE_TYPE_4 == "OFF") )
                                        outputStreamSensor04.write(linearValue.getBytes());
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }

                })).continueWith((Continuation<Route, Void>) ignored -> {
                    sensorFusion.linearAcceleration().start();
                    sensorFusion.start();
                    return null;
                });
            }
            else if (Objects.equals(DEVICE_TYPE_4, "Quaternion")) {
                // Configure the sensor fusion module
                sensorFusion.configure()
                        .mode(SensorFusionBosch.Mode.NDOF)
                        .accRange(AccRange.AR_2G)
                        .gyroRange(GyroRange.GR_250DPS)
                        .commit();
                // Configure the sensor fusion module


                sensorFusion.quaternion().addRouteAsync(source -> source.stream((data, env) -> {
                    // Handle accelerometer data here
                    //String logMessage = "Log.i(\"MainActivity\", \"Quantranion from \" + deviceMacAddress + \": \" + data.value(Quaternion.class).toString());";

                    String quaternionValue =
                            data.value(Quaternion.class).w() + "," +
                                    data.value(Quaternion.class).x() + "," +
                                    data.value(Quaternion.class).y() + "," +
                                    data.value(Quaternion.class).z() + "," +
                                    data.timestamp().getTimeInMillis()+ "\n";
                    sensorsConnected[3] = true;
                    message = "Name"+deviceMacAddress + " " + deviceMacAddress.replaceAll(":", "") + " " + data.timestamp().getTimeInMillis() + " null" + " " + "null" + " " + data.value(Quaternion.class).w() + " " + data.value(Quaternion.class).x() + " " + data.value(Quaternion.class).y() + " " + data.value(Quaternion.class).z();
                    //addNewData(message);
                    //Log.i("4->", message);
                    SensorData mydata = new SensorData();
                    mydata.setDeviceMacAddress(deviceMacAddress);
                    mydata.setTimestamp(data.timestamp().getTimeInMillis());
                    mydata.setX(data.value(Quaternion.class).x());
                    mydata.setY(data.value(Quaternion.class).y());
                    mydata.setZ(data.value(Quaternion.class).z());
                    mydata.setW(data.value(Quaternion.class).w());
                    sensorDataQueue.offer(mydata);
                    ArrayList<String> retData = getData();

                    if (retData.size() >= 100) {
                        try {
                            Gson gson = new Gson();

                            clearData();
                        } catch (Exception e) {
                            e.printStackTrace();
                        }
                    }

                    if (creationLocallyCSVs) {
                        try {
                            if ( (sensorsConnected[0] || DEVICE_TYPE_1 == "OFF") &&
                                    (sensorsConnected[1] || DEVICE_TYPE_2 == "OFF") &&
                                    (sensorsConnected[2] || DEVICE_TYPE_3 == "OFF") &&
                                    (sensorsConnected[3] || DEVICE_TYPE_4 == "OFF") )
                                        outputStreamSensor04.write(quaternionValue.getBytes());
                        } catch (IOException e) {
                            e.printStackTrace();
                        }
                    }

                })).continueWith((Continuation<Route, Void>) ignored -> {
                    sensorFusion.quaternion().start();
                    sensorFusion.start();
                    return null;
                });


            }
        }
    }


    //@Override
    public void onServiceDisconnected(ComponentName name) {
        serviceBinder = null;
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Ensure you unbind from the service when the activity is destroyed
        unbindService(this);
        mqttPublisher.disconnect();

        try {
            outputStreamSensor01.close();
            outputStreamSensor02.close();
            outputStreamSensor03.close();
            outputStreamSensor04.close();

        } catch (IOException e) {
            e.printStackTrace();
        }
    }


    public void onMessageReceived(String topic, String message) {
        // Convert the received message to a string
        String receivedMessage = message.toString();
        Log.i("received ", receivedMessage);

        // Check if the received message contains the MAC addresses for the MetaWear boards
        if (topic.equals("IMUsettings") && receivedMessage.contains("[") ) {
            Log.w("onMessageReceived", "Received data");
            initializeBLEvariables();
            //disconnectBoards();

            // Remove brackets and split the received message by comma and space to extract MAC addresses and types
            String[] data = receivedMessage.replaceAll("[\\[\\]]", "").split(", ");

            // Check if the received message contains valid data
            if (data.length % 2 == 0) {
                // Iterate over the data array in pairs to extract MAC addresses and types
                for (int i = 0; i < data.length; i += 2) {
                    String macAddress = data[i];
                    String deviceType = data[i + 1];

                    // Update DEVICE_MAC_ADDRESS_X variables with the received MAC addresses
                    if (i / 2 == 0) {
                        DEVICE_MAC_ADDRESS_1 = macAddress;
                        DEVICE_TYPE_1 = deviceType;
                    } else if (i / 2 == 1) {
                        DEVICE_MAC_ADDRESS_2 = macAddress;
                        DEVICE_TYPE_2 = deviceType;
                    } else if (i / 2 == 2) {
                        DEVICE_MAC_ADDRESS_3 = macAddress;
                        DEVICE_TYPE_3 = deviceType;
                    } else if (i / 2 == 3) {
                        DEVICE_MAC_ADDRESS_4 = macAddress;
                        DEVICE_TYPE_4 = deviceType;
                    }
                }

                // Log the updated MAC addresses and types
                Log.i("MainActivity", "Updated DEVICE_MAC_ADDRESS_1: " + DEVICE_MAC_ADDRESS_1 + ", DEVICE_TYPE_1: " + DEVICE_TYPE_1);
                Log.i("MainActivity", "Updated DEVICE_MAC_ADDRESS_2: " + DEVICE_MAC_ADDRESS_2 + ", DEVICE_TYPE_2: " + DEVICE_TYPE_2);
                Log.i("MainActivity", "Updated DEVICE_MAC_ADDRESS_3: " + DEVICE_MAC_ADDRESS_3 + ", DEVICE_TYPE_3: " + DEVICE_TYPE_3);
                Log.i("MainActivity", "Updated DEVICE_MAC_ADDRESS_4: " + DEVICE_MAC_ADDRESS_4 + ", DEVICE_TYPE_4: " + DEVICE_TYPE_4);

                initiateConnection();
            } else {
                // Log a warning if the received message does not contain valid data
                Log.w("MainActivity", "Received invalid data for MAC addresses and types");
            }
        }

        if (topic.equals("IMUsettings") && receivedMessage.contains("exit") ) {
            System.exit(0);
        }

        if (topic.equals("IMUsettings") && receivedMessage.contains("stop") ) {

            disconnectBoards();


        }
    }
/*
    void publishDataToServer() {
        new Thread(() -> {
            MqttPublisher mqttPublisher2 = new MqttPublisher("tcp://192.168.1.109:1883", "AndroidClient2", this);
            //MqttPublisher mqttPublisher2 = new MqttPublisher("tcp://192.168.0.247:1883", "AndroidClient2", this);
            //MqttPublisher mqttPublisher2 = new MqttPublisher("tcp://192.168.70.105:1883", "AndroidClient2", this);
            mqttPublisher2.connect();
            //mqttPublisher2.subscribe("IMUdata", 1);
            int p = 0;
            while (true) {
                if (!sensorDataQueue.isEmpty()) {
                    SensorData data = sensorDataQueue.poll(); // Dequeue data from the queue
                    if (data != null) {
                        mqttPublisher2.publish("IMUdata", data.toJson(), 0);
                        p = p + 1;
                        Log.i("counter", Integer.toString(p));

                    }
                }
            }
        }).start();
    }
*/



    public class MyWebSocketClient extends WebSocketClient {

        public MyWebSocketClient(URI serverUri) {
            super(serverUri);
        }

        @Override
        public void onOpen(ServerHandshake handshakedata) {
            Log.i("WebSocket", "Opened connection");
        }

        @Override
        public void onMessage(String message) {
            Log.i("WebSocket", "Received message: " + message);
        }

        @Override
        public void onClose(int code, String reason, boolean remote) {
            Log.i("WebSocket", "Closed connection");
        }

        @Override
        public void onError(Exception ex) {
            Log.e("WebSocket", "Error: ", ex);
        }
    }

    // Function to publish data using WebSocket
    /*
    void publishDataToServer() {
        new Thread(() -> {
            try {
                URI uri = new URI("ws://192.168.1.109:8765");
                MyWebSocketClient webSocketClient = new MyWebSocketClient(uri);
                webSocketClient.connectBlocking(); // Wait until the connection is established

                int p = 0;
                while (true) {
                    if (!sensorDataQueue.isEmpty()) {
                        SensorData data = sensorDataQueue.poll(); // Dequeue data from the queue
                        if (data != null) {
                            webSocketClient.send(data.toJson());
                            p = p + 1;
                            Log.i("counter", Integer.toString(p) + data.toJson());
                        }
                    }
                }
            } catch (URISyntaxException | InterruptedException e) {
                e.printStackTrace();
            }
        }).start();
    }*/

    void publishDataToServer() {
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



    void initializeBLEvariables(){
        numOfSensors = 4;
        btManager = (BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE);
        btAdapter = btManager.getAdapter();
        sensorDataQueue = new ConcurrentLinkedQueue<>();

        for(int i=0; i< numOfSensors; i++)
            sensorsConnected[i] = false;

    }

}
