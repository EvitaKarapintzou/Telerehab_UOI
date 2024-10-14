package com.example.myapplication;

import android.content.Context;
import android.util.Log;

import org.eclipse.paho.android.service.MqttAndroidClient;
import org.eclipse.paho.client.mqttv3.IMqttActionListener;
import org.eclipse.paho.client.mqttv3.IMqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.IMqttToken;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;

public class MqttPublisher {

    private static final String TAG = "MqttPublisher";
    private MqttAndroidClient mqttClient;
    private String serverUri;
    private String clientId;

    public MqttPublisher(String serverUri, String clientId, Context context) {
        this.serverUri = serverUri;
        this.clientId = clientId;

        // Create the MQTT client using the CustomPingSender
        mqttClient = new MqttAndroidClient(context, serverUri, clientId);

        mqttClient.setCallback(new MqttCallback() {
            @Override
            public void connectionLost(Throwable cause) {
                Log.e(TAG, "Connection lost", cause);
            }

            @Override
            public void messageArrived(String topic, MqttMessage message) throws Exception {
                Log.i(TAG, "Message arrived from topic " + topic + ": " + message.toString());
            }

            @Override
            public void deliveryComplete(IMqttDeliveryToken token) {
                Log.i(TAG, "Delivery complete: " + token.toString());
            }
        });
    }

    public void connect() {
        try {
            IMqttToken token = mqttClient.connect();
            token.setActionCallback(new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {
                    Log.i(TAG, "Connected to MQTT broker: " + serverUri);
                }

                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                    Log.e(TAG, "Failed to connect to MQTT broker: " + serverUri, exception);
                }
            });
        } catch (MqttException e) {
            Log.e(TAG, "Error connecting to MQTT broker", e);
        }
    }

    public void disconnect() {
        if (!mqttClient.isConnected()) {
            Log.i(TAG, "MQTT client is already disconnected.");
            return;
        }

        try {
            IMqttToken token = mqttClient.disconnect();
            token.setActionCallback(new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {
                    Log.i(TAG, "Successfully disconnected from MQTT broker");
                }

                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                    Log.e(TAG, "Failed to disconnect from MQTT broker", exception);
                }
            });
        } catch (MqttException e) {
            Log.e(TAG, "Error disconnecting from MQTT broker", e);
        }
    }

    public void publish(String topic, String payload, int qos) {
        if (!mqttClient.isConnected()) {
            Log.e(TAG, "Cannot publish. MQTT client is not connected.");
            return;
        }

        try {
            MqttMessage message = new MqttMessage();
            message.setPayload(payload.getBytes());
            message.setQos(qos);

            mqttClient.publish(topic, message, null, new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {
                    Log.i(TAG, "Message published to topic: " + topic);
                }

                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                    Log.e(TAG, "Failed to publish message to topic: " + topic, exception);
                }
            });
        } catch (MqttException e) {
            Log.e(TAG, "Error publishing message", e);
        }
    }

    public void subscribe(String topic, int qos) {
        if (!mqttClient.isConnected()) {
            Log.e(TAG, "Cannot subscribe. MQTT client is not connected.");
            return;
        }

        try {
            IMqttToken token = mqttClient.subscribe(topic, qos);
            token.setActionCallback(new IMqttActionListener() {
                @Override
                public void onSuccess(IMqttToken asyncActionToken) {
                    Log.i(TAG, "Subscribed to topic: " + topic);
                }

                @Override
                public void onFailure(IMqttToken asyncActionToken, Throwable exception) {
                    Log.e(TAG, "Failed to subscribe to topic: " + topic, exception);
                }
            });
        } catch (MqttException e) {
            Log.e(TAG, "Error subscribing to topic", e);
        }
    }
}
