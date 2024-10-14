package com.mbientlab.metawear.metabase;

import android.app.Activity;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.bluetooth.BluetoothManager;
import android.content.Context;
import android.content.Intent;
import android.os.Build;
import android.os.PowerManager;
import android.os.SystemClock;
import android.widget.TextView;
import androidx.appcompat.app.AlertDialog;
import androidx.core.app.JobIntentService;
import androidx.core.app.NotificationCompat;
import com.mbientlab.metawear.MetaWearBoard;
import com.mbientlab.metawear.android.BtleService;
import com.mbientlab.metawear.module.Debug;
import com.mbientlab.metawear.module.Macro;
import java.util.UUID;
import bolts.Capture;
import bolts.Task;

public class MyJobIntentService extends JobIntentService {

    private static final int JOB_ID = 1001;
    private static final String CHANNEL_ID = "my_channel";
    private static final int NOTIFICATION_ID = 1;
    private BtleScanner scanner;
    private BtleService.LocalBinder binder;


    private PowerManager.WakeLock wakeLock;

    public static void enqueueWork(Context context, Intent work) {
        enqueueWork(context, MyJobIntentService.class, JOB_ID, work);
    }

    private static final String FRAGMENT_KEY = "com.mbientlab.metawear.metabase.HomeActivity.FRAGMENT_KEY",
            SHOW_METACLOUD_ABOUT = "com.mbientlab.metawear.metabase.HomeActivity.SHOW_METACLOUD_ABOUT";
    static final String SHOW_TUTORIAL = "show_tutorial";

    public static Task<Void> teardownAndDc(MetaWearBoard board) {
        board.getModule(Macro.class).eraseAll();
        board.getModule(Debug.class).resetAfterGc();
        return board.getModule(Debug.class).disconnectAsync();
    }

    public static Task<Void> reconnect(Activity activity, MetaWearBoard metawear, long delay, int retries, boolean showDialog) {
        final Capture<AlertDialog> dialog = new Capture<>();
        if (showDialog) {
            activity.runOnUiThread(() -> {
                AlertDialog value = new AlertDialog.Builder(activity)
                        .setTitle(R.string.title_reconnecting)
                        .setView(R.layout.indeterminate_task)
                        .setCancelable(false)
                        .create();
                dialog.set(value);
                value.show();
                ((TextView) value.findViewById(R.id.message)).setText(R.string.message_wait);
            });
        }

        final Capture<Integer> remaining = new Capture<>(retries);
        return (delay == 0L ? Task.forResult(null) : Task.delay(delay)).continueWhile(() -> !metawear.isConnected() && remaining.get() >= 0, ignored ->
                metawear.connectAsync().continueWithTask(task -> {
                    if (task.isFaulted()) {
                        remaining.set(remaining.get() - 1);
                    }
                    return task;
                })
        ).continueWithTask(ignored -> {
            if (dialog.get() != null) {
                dialog.get().dismiss();
            }
            return ignored;
        }, Task.UI_THREAD_EXECUTOR);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        acquireWakeLock();
        startForeground(NOTIFICATION_ID, createNotification());
    }

    @Override
    protected void onHandleWork(Intent intent) {
        int contextIdentifier = intent.getIntExtra("contextIdentifier", -1);
        HomeActivity homeActivity = findHomeActivityByHashCode(contextIdentifier);
        if (homeActivity != null) {
            scanner = BtleScanner.getScanner(((BluetoothManager) homeActivity.getSystemService(Context.BLUETOOTH_SERVICE)).getAdapter(), new UUID[]{
                    MetaWearBoard.METAWEAR_GATT_SERVICE
            });
            homeActivity.getApplicationContext().bindService(new Intent(homeActivity, BtleService.class), homeActivity, Context.BIND_AUTO_CREATE);
        }
        SystemClock.sleep(5000); // Simulating 5 seconds of work
    }

    private HomeActivity findHomeActivityByHashCode(int hashCode) {
        HomeActivity activity = HomeActivity.getActiveInstance();
        if (activity != null && activity.hashCode() == hashCode) {
            return activity;
        }
        return null; // Not found
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        releaseWakeLock();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            CharSequence name = "My Channel";
            String description = "Channel for my app";
            int importance = NotificationManager.IMPORTANCE_DEFAULT;
            NotificationChannel channel = new NotificationChannel(CHANNEL_ID, name, importance);
            channel.setDescription(description);
            NotificationManager notificationManager = getSystemService(NotificationManager.class);
            notificationManager.createNotificationChannel(channel);
        }
    }

    private Notification createNotification() {
        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
                .setSmallIcon(R.drawable.rssi_level)
                .setContentTitle("Background Task in Progress")
                .setContentText("Your background task is running")
                .setPriority(NotificationCompat.PRIORITY_DEFAULT);

        return builder.build();
    }

    private void acquireWakeLock() {
        PowerManager powerManager = (PowerManager) getSystemService(Context.POWER_SERVICE);
        if (powerManager != null) {
            wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "MyJobIntentService::WakeLock");
            wakeLock.acquire();
        }
    }

    private void releaseWakeLock() {
        if (wakeLock != null && wakeLock.isHeld()) {
            wakeLock.release();
            wakeLock = null;
        }
    }

}
