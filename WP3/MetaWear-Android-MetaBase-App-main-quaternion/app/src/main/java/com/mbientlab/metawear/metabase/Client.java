package com.mbientlab.metawear.metabase;

import android.os.AsyncTask;
import android.util.Log;
import java.io.IOException;
import java.io.OutputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

public class Client extends AsyncTask<Void, Void, Void> {

    private String host = "195.130.118.252";
    private int port = 1234;
    private String message = "";

    public Client(String host, int port, String message) {
        this.host = host;
        this.port = port;
        this.message = message;
    }

    @Override
    protected Void doInBackground(Void... voids) {
        try {
            Socket socket = new Socket(host, port);
            OutputStream outputStream = socket.getOutputStream();
            outputStream.write(message.getBytes(StandardCharsets.UTF_8));
            outputStream.close();
            socket.close();
        } catch (IOException e) {
            Log.e("Client", "Error: " + e.getMessage());
        }

        return null;
    }

}
