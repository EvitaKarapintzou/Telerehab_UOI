package com.example.myapplication;

import android.os.Handler;
import android.os.Looper;
import android.util.Log;
import org.eclipse.paho.client.mqttv3.MqttPingSender;
import org.eclipse.paho.client.mqttv3.internal.ClientComms;

public class CustomPingSender implements MqttPingSender {

    private static final String TAG = "CustomPingSender";
    private ClientComms comms;
    private Handler handler;
    private Runnable pingSender;

    public CustomPingSender() {
        this.handler = new Handler(Looper.getMainLooper());
    }

    @Override
    public void init(ClientComms comms) {
        this.comms = comms;
    }

    @Override
    public void start() {
        pingSender = () -> {
            try {
                Log.i(TAG, "Sending MQTT Ping");
                comms.checkForActivity();
                handler.postDelayed(pingSender, comms.getKeepAlive());
            } catch (Exception e) {
                Log.e(TAG, "Failed to send MQTT Ping", e);
            }
        };
        handler.postDelayed(pingSender, comms.getKeepAlive());
    }

    @Override
    public void stop() {
        handler.removeCallbacks(pingSender);
    }

    @Override
    public void schedule(long delayInMilliseconds) {
        handler.removeCallbacks(pingSender);
        handler.postDelayed(pingSender, delayInMilliseconds);
    }
}
