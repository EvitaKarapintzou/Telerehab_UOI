package com.mbientlab.metawear.metabase;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * RecordingReceiver handles start/stop commands for the IMU recording.
 */
public class RecordingReceiver extends BroadcastReceiver {

    @Override
    public void onReceive(Context context, Intent intent) {
        // Extract action from the intent
        String action = intent.getAction();

        if (action != null) {
            switch (action) {
                case "com.mbientlab.metawear.metabase.START_RECORDING":
                    startRecording(context);
                    break;

                case "com.mbientlab.metawear.metabase.STOP_RECORDING":
                    stopRecording(context);
                    break;

                default:
                    Log.w("RecordingReceiver", "Unknown action received: " + action);
            }
        }
    }

    private void startRecording(Context context) {
        Log.i("RecordingReceiver", "Starting IMU recording...");
        // Start the recording process, possibly by communicating with IMUManager or BackgroundService
        Intent serviceIntent = new Intent(context, BackgroundService.class);
        serviceIntent.setAction("com.mbientlab.metawear.metabase.START_RECORDING");
        context.startService(serviceIntent);
    }

    private void stopRecording(Context context) {
        Log.i("RecordingReceiver", "Stopping IMU recording...");
        // Stop the recording process
        Intent serviceIntent = new Intent(context, BackgroundService.class);
        serviceIntent.setAction("com.mbientlab.metawear.metabase.STOP_RECORDING");
        context.startService(serviceIntent);
    }
}
