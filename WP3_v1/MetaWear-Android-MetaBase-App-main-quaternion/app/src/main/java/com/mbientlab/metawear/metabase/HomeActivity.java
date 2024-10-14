
package com.mbientlab.metawear.metabase;

import android.app.Activity;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.SharedPreferences;
import android.content.pm.ActivityInfo;
import android.content.pm.PackageManager;
import android.content.res.Configuration;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import androidx.fragment.app.FragmentManager;
import androidx.fragment.app.FragmentTransaction;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import android.util.Pair;
import android.view.Menu;
import android.widget.TextView;
import com.mbientlab.function.Action;
import com.mbientlab.metawear.MetaWearBoard;
import com.mbientlab.metawear.android.BtleService;
import com.mbientlab.metawear.module.Debug;
import com.mbientlab.metawear.module.Macro;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.UUID;
import bolts.Capture;
import bolts.Task;
import no.nordicsemi.android.dfu.DfuBaseService;

public class HomeActivity extends AppCompatActivity implements ActivityBus, ServiceConnection, ScannerFragment.EventBus, DeviceInfoFragment.MetaCloudOptions {
    private static final String FRAGMENT_KEY = "com.mbientlab.metawear.metabase.HomeActivity.FRAGMENT_KEY",
            SHOW_METACLOUD_ABOUT = "com.mbientlab.metawear.metabase.HomeActivity.SHOW_METACLOUD_ABOUT";
    static final String SHOW_TUTORIAL = "show_tutorial";

    private static final String CHANNEL_ID = "my_channel";
    private static final int NOTIFICATION_ID = 1;
    private static HomeActivity activeInstance;

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

    private BtleScanner scanner;
    private Object parameter;
    private Action<Void> backPressedHandler;
    private BtleService.LocalBinder binder;
    private AppFragmentBase currentFragment = null;
    private Deque<Pair<String, Object>> backstack = new ArrayDeque<>();
    private boolean appInBackground = false;

    @Override
    public void onBackPressed() {
        if (backstack.isEmpty()) {
            scanner.stop();
            super.onBackPressed();
        } else {
            if (backPressedHandler != null) {
                backPressedHandler.apply(null);
            }
            navigateBack();
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setActiveInstance(this);
        setContentView(R.layout.activity_home);
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        setRequestedOrientation(getResources().getConfiguration().orientation == Configuration.ORIENTATION_LANDSCAPE ?
                ActivityInfo.SCREEN_ORIENTATION_USER_LANDSCAPE :
                ActivityInfo.SCREEN_ORIENTATION_USER_PORTRAIT);
        if (savedInstanceState == null) {
            currentFragment = new HomeActivityFragment();
            FragmentManager fragmentManager = getSupportFragmentManager();
            FragmentTransaction transaction = fragmentManager.beginTransaction();
            transaction.add(R.id.container, currentFragment, currentFragment.getClass().getCanonicalName());
            transaction.attach(currentFragment).commit();
            invalidateOptionsMenu();
        } else {
            currentFragment = (AppFragmentBase) getSupportFragmentManager().getFragment(savedInstanceState, FRAGMENT_KEY);
        }
        scanner = BtleScanner.getScanner(((BluetoothManager) getSystemService(Context.BLUETOOTH_SERVICE)).getAdapter(), new UUID[]{
                MetaWearBoard.METAWEAR_GATT_SERVICE
        });
        getApplicationContext().bindService(new Intent(this, BtleService.class), this, Context.BIND_AUTO_CREATE);
    }

    @Override
    protected void onResume() {
        super.onResume();
        moveTaskToBack(true);//comment this if you want to change the number of the connected IMUs
        if (!appInBackground) {
            appInBackground = false;
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        clearActiveInstance();
        getApplicationContext().unbindService(this);
    }

    public static HomeActivity getActiveInstance() {

        return activeInstance;
    }

    private static void setActiveInstance(HomeActivity activity) {
        activeInstance = activity;
    }

    private static void clearActiveInstance() {
        activeInstance = null;
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        if (currentFragment != null) {
            getSupportFragmentManager().putFragment(outState, FRAGMENT_KEY, currentFragment);
        }
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.menu_home, menu);
        return super.onCreateOptionsMenu(menu);
    }

    @Override
    public boolean onPrepareOptionsMenu(Menu menu) {
        if (currentFragment.getMenuGroupResId() != null) {
            menu.setGroupVisible(currentFragment.getMenuGroupResId(), true);
        }
        return super.onPrepareOptionsMenu(menu);
    }

    @Override
    public void swapFragment(Class<? extends AppFragmentBase> nextFragmentClass) {
        swapFragment(nextFragmentClass, null);
    }

    @Override
    public void swapFragment(Class<? extends AppFragmentBase> nextFragmentClass, Object parameter) {
        if(currentFragment.getClass().getCanonicalName().toString().contains("HomeActivityFragment")) {
            scanner.stop();
            backstack.addFirst(new Pair<>(currentFragment.getClass().getCanonicalName(), this.parameter));
            this.parameter = parameter;
            backPressedHandler = null;
            FragmentManager fragmentManager = getSupportFragmentManager();
            FragmentTransaction transaction = fragmentManager.beginTransaction();
            transaction.setTransition(FragmentTransaction.TRANSIT_FRAGMENT_OPEN)
                    .detach(currentFragment);
            currentFragment = (AppFragmentBase) fragmentManager.findFragmentByTag(nextFragmentClass.getCanonicalName());
            if (currentFragment == null) {

                try {
                    currentFragment = nextFragmentClass.getConstructor().newInstance();
                } catch (Exception e) {
                    throw new RuntimeException("Cannot instantiate fragment", e);
                }
                transaction.add(R.id.container, currentFragment, nextFragmentClass.getCanonicalName());
            }
            transaction.attach(currentFragment)
                    .commitAllowingStateLoss();
            invalidateOptionsMenu();
        }
        else{
            System.out.println("EDWWWW1");
            scanner.stop();
            backstack.addFirst(new Pair<>(currentFragment.getClass().getCanonicalName(), this.parameter));
            this.parameter = parameter;
            backPressedHandler = null;
            FragmentManager fragmentManager = getSupportFragmentManager();
            FragmentTransaction transaction = fragmentManager.beginTransaction();
            transaction.replace(R.id.container, nextFragmentClass, null);
            // Commit the transaction
            transaction.addToBackStack(null)
                    .commitAllowingStateLoss();
            invalidateOptionsMenu();
            new Handler().postDelayed(new Runnable() {
                @Override
                public void run() {
                    bringAppToForeground();
                }
            }, 200);
        }
    }

    private void bringAppToForeground() {
        Intent intent = new Intent(this, HomeActivity.class);
        intent.setAction(Intent.ACTION_MAIN);
        intent.addCategory(Intent.CATEGORY_LAUNCHER);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent pendingIntent = PendingIntent.getActivity(
                this, 0, intent, PendingIntent.FLAG_IMMUTABLE
        );
        try {
            pendingIntent.send();
        } catch (PendingIntent.CanceledException e) {
            e.printStackTrace();
        }
    }

    @Override
    public MetaWearBoard getMetaWearBoard(BluetoothDevice device) {
        return binder.getMetaWearBoard(device);
    }

    @Override
    public void removeMetaWearBoard(BluetoothDevice device) {
        binder.removeMetaWearBoard(device);
    }

    @Override
    public void onServiceConnected(ComponentName name, IBinder service) {
        binder = (BtleService.LocalBinder) service;
    }

    @Override
    public void onServiceDisconnected(ComponentName name) {

    }

    @Override
    public boolean showAbout() {
        return getPreferences(MODE_PRIVATE).getBoolean(SHOW_METACLOUD_ABOUT, true);
    }

    @Override
    public void disableAbout() {
        SharedPreferences.Editor editor = getPreferences(MODE_PRIVATE).edit();
        editor.putBoolean(SHOW_METACLOUD_ABOUT, false);
        editor.apply();
    }

    public static class DfuService extends DfuBaseService {
        @Override
        protected Class<? extends Activity> getNotificationTarget() {
            return HomeActivity.class;
        }
    }

    @Override
    public Task<Void> reconnect(MetaWearBoard metawear, int retries) {
        return reconnect(this, metawear, 0L, retries, true);
    }

    @Override
    public Task<Void> reconnect(MetaWearBoard metawear, long delay, int retries) {
        return reconnect(this, metawear, delay, retries, true);
    }

    @Override
    public Object parameter() {
        return parameter;
    }

    @Override
    public BtleScanner scanner() {
        return scanner;
    }

    @Override
    public void onBackPressed(Action<Void> handler) {
        backPressedHandler = handler;
    }

    @Override
    public void popBackstack() {
        if (!backstack.isEmpty()) {
            backstack.pop();
        }
    }

    @Override
    public void navigateBack() {
        scanner.stop();
        FragmentManager fragmentManager = getSupportFragmentManager();
        FragmentTransaction transaction= fragmentManager.beginTransaction();
        if (backstack.isEmpty()) {
            currentFragment = new HomeActivityFragment();
            transaction.add(R.id.container, currentFragment, currentFragment.getClass().getCanonicalName());
        } else {
            Pair<String, Object> previous = backstack.pop();
            this.parameter = previous.second;
            backPressedHandler = null;
            transaction.setTransition(FragmentTransaction.TRANSIT_FRAGMENT_CLOSE)
                    .detach(currentFragment);
            currentFragment= (AppFragmentBase) fragmentManager.findFragmentByTag(previous.first);
        }
        transaction.attach(currentFragment)
                .commit();
        invalidateOptionsMenu();
    }

    @Override
    public void deviceAdded(MetaBaseDevice device) {
        navigateBack();
        ((HomeActivityFragment) currentFragment).deviceAdded(device);
    }
}
