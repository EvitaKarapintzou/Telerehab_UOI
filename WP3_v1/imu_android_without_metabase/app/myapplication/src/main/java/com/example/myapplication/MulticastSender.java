package com.example.myapplication;

import android.os.AsyncTask;
import android.util.Log;
import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;

public class MulticastSender extends AsyncTask<Void, Void, Void> {
    private static final String TAG = "MulticastSender";
    private static final String MULTICAST_GROUP = "224.1.1.1";
    private static final int MULTICAST_PORT = 10000;
    private String message;

    public MulticastSender(String message) {
        this.message = message;
    }

    @Override
    protected Void doInBackground(Void... params) {
        DatagramSocket socket = null;
        try {
            socket = new DatagramSocket();
            InetAddress group = InetAddress.getByName(MULTICAST_GROUP);
            byte[] buf = message.getBytes();
            DatagramPacket packet = new DatagramPacket(buf, buf.length, group, MULTICAST_PORT);
            socket.send(packet);
            Log.i(TAG, "Message sent: " + message);
        } catch (IOException e) {
            Log.e(TAG, "IOException: ", e);
        } finally {
            if (socket != null && !socket.isClosed()) {
                socket.close();
            }
        }
        return null;
    }
}
