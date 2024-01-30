package com.mbientlab.metawear.metabase;

import static android.app.Service.START_STICKY;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

import androidx.annotation.Nullable;

public class MyBackgroundService extends Service {

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        // Perform your background tasks here
        performBackgroundTasks();

        // Continue running the service even if the app is in the background
        return START_STICKY;
    }

    private void performBackgroundTasks() {
        // Add your commands from onCreate here
        // ...
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
