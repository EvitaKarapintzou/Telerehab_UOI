package com.mbientlab.metawear.metabase;

import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.util.Log;

import com.mbientlab.metawear.MetaWearBoard;
import com.mbientlab.metawear.data.Acceleration;
import com.mbientlab.metawear.data.Quaternion;
import com.mbientlab.metawear.module.SensorFusionBosch;

import org.eclipse.paho.android.service.MqttAndroidClient;
import org.eclipse.paho.client.mqttv3.IMqttActionListener;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.IMqttToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;


import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttCallbackExtended;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;



public class MQTTManager {
    private static final String TAG = "MQTTManager";
    private MqttClient mqttClient;
    private MainActivity mainActivity;  // Reference to MainActivity to trigger the service

    private String brokerUrl;
    private String clientId;


    public MQTTManager(Context context, String brokerUrl) {
        String serverURI = "tcp://192.168.1.58:1883";
        String clientId = "your_client_id";
        this.mainActivity = (MainActivity) context;
        Intent intent = new Intent(context, BackgroundService.class);


        this.brokerUrl = serverURI;
        try {
            mqttClient = new MqttClient(serverURI, clientId, new MemoryPersistence());
            MqttConnectOptions options = new MqttConnectOptions();

            mqttClient.setCallback(new MqttCallbackExtended() {
                @Override
                public void connectComplete(boolean reconnect, String serverURI) {
                    // Connection successful
                    try {
                        mqttClient.subscribe("IMUsettings", 0);
                        mqttClient.subscribe("StartRecording", 0);
                        mqttClient.subscribe("DeviceStatus", 0);
                        mqttClient.subscribe("StopRecording", 0);
                        Log.i("MQTTMANAGER", "Subscriptions OK");
                        publishMessage("DeviceStatus", "up");
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
                    String messagePayload = new String(message.getPayload());
                    Log.i("MQTTManager", "MESSAGE: " + messagePayload);

                    if (topic.equals("IMUsettings")) {
                        // Send the configuration message to BackgroundService via Intent
                        Intent intent = new Intent(context, BackgroundService.class);
                        intent.setAction("SET_IMU_CONFIG");
                        intent.putExtra("IMU_CONFIG_MESSAGE", messagePayload);  // Pass the message as an extra
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            context.startForegroundService(intent);
                        } else {
                            context.startService(intent);
                        }

                    } else if (topic.equals("StartRecording")) {
                        // Second MQTT message: Start recording
                        Intent intent = new Intent(context, BackgroundService.class);
                        intent.setAction("START_RECORDING");
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            context.startForegroundService(intent);
                        } else {
                            context.startService(intent);
                        }
                    } else if (topic.equals("StopRecording")) {
                        // Second MQTT message: Stop recording
                        Intent intent = new Intent(context, BackgroundService.class);
                        intent.setAction("STOP_RECORDING");
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            context.startForegroundService(intent);
                        } else {
                            context.startService(intent);
                        }
                    }
                }

                @Override
                public void deliveryComplete(IMqttDeliveryToken token) {
                    // Message delivery complete
                }
            });

        }catch (MqttException e) {
            e.printStackTrace();
        }

        Log.i(TAG, "MQTTManager initialized");
    }

    // Connect to the MQTT broker
    public void connect() {
        Log.i(TAG, "Attempting to connect to MQTT broker: " + brokerUrl);

        try {
            MqttConnectOptions options = new MqttConnectOptions();
            mqttClient.connect(options);

            if (mqttClient.isConnected()) {
                Log.i("MQTTManager", "Client is connected.");
            } else {
                Log.i("MQTTManager", "Client is not connected.");
            }

        } catch (MqttException e) {
            Log.e("MQTTManager", "Error connecting to MQTT broker", e);
        }
    }

    // Method to publish a message to a topic
    public void publishMessage(String topic, String message) {
        try {
            if (mqttClient.isConnected()) {
                MqttMessage mqttMessage = new MqttMessage(message.getBytes());
                mqttMessage.setQos(1); // Set QoS (0, 1, or 2)
                mqttClient.publish(topic, mqttMessage);  // Publish the message
                Log.i(TAG, "Message published to topic: " + topic);
            } else {
                Log.e(TAG, "MQTT Client is not connected.");
            }
        } catch (MqttException e) {
            Log.e(TAG, "Error publishing message", e);
        }
    }


}
