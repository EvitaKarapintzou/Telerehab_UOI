package com.mbientlab.metawear;

import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;

import com.mbientlab.metawear.ui.main.MainFragment;

import android.app.Activity;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.os.Bundle;
import android.os.IBinder;
import com.mbientlab.metawear.android.BtleService;

public class MainActivity extends Activity implements ServiceConnection {
    private BtleService.LocalBinder serviceBinder;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Bind to the MetaWear BtleService
        getApplicationContext().bindService(new Intent(this, BtleService.class),
                this, Context.BIND_AUTO_CREATE);
    }

    @Override
    public void onServiceConnected(ComponentName name, IBinder service) {
        serviceBinder = (BtleService.LocalBinder) service;
        // You can now use serviceBinder to interact with the MetaWear API
    }

    @Override
    public void onServiceDisconnected(ComponentName name) {
        serviceBinder = null;
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        // Ensure you unbind from the service when the activity is destroyed
        getApplicationContext().unbindService(this);
    }
}
