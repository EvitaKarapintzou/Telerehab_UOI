package com.mbientlab.metawear.metabase;

import android.app.Service;
import android.content.Intent;
import android.os.IBinder;

import androidx.annotation.Nullable;

public class MyBackgroundService extends Service {

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        performBackgroundTasks();
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
