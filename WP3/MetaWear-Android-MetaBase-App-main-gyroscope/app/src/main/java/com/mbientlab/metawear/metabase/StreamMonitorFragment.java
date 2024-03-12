

package com.mbientlab.metawear.metabase;

import android.app.ActivityManager;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.ComponentName;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.media.MediaScannerConnection;
import android.os.Binder;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.IBinder;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import com.google.android.material.textfield.TextInputLayout;
import androidx.appcompat.app.AlertDialog;
import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;
import android.util.Log;
import android.util.Pair;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import com.mbientlab.function.Action3;
import com.mbientlab.metawear.MetaWearBoard;
import com.mbientlab.metawear.Route;
import com.mbientlab.metawear.android.BtleService;
import com.mbientlab.metawear.impl.JseMetaWearBoard;
import com.mbientlab.metawear.module.Debug;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import bolts.Capture;
import bolts.Task;
import bolts.TaskCompletionSource;
import static com.mbientlab.metawear.metabase.Global.FIREBASE_PARAM_LOG_DURATION;

public class StreamMonitorFragment extends AppFragmentBase implements ServiceConnection {
    private final static String FIREBASE_EVENT_STREAM_STOP = "stop_stream";

    static class Parameter {
        List<Pair<MetaBaseDevice, Map<SensorConfig, Route>>> devices;
        List<AppState.Session> sessions;
        String name;
    }

    public static class Service extends android.app.Service implements ServiceConnection {
        @Override
        public void onServiceConnected(ComponentName name, IBinder service) {

        }

        @Override
        public void onServiceDisconnected(ComponentName name) {

        }

        private final LocalBinder localBinder = new LocalBinder();
        class LocalBinder extends Binder {
            boolean active;

            Parameter parameter;
            List<MetaWearBoard> metawears;
            List<DataHandler> dataHandlers;
            AppState.Session session;
            long start;
            List<DataHandler.SampleCountDataHandler> streamMetrics;
            Map<MetaBaseDevice, List<Pair<SensorConfig, DataHandler.SampleCountDataHandler>>> samples;

            public void showNotifcation(String title, String body, Context context) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    final String CHANNEL_ID = "HEADS_UP_NOTIFICATIONS";
                    NotificationChannel channel = new NotificationChannel(
                            CHANNEL_ID,
                            "MyNotification",
                            NotificationManager.IMPORTANCE_HIGH);

                    context.getSystemService(NotificationManager.class).createNotificationChannel(channel);
                    Notification.Builder notification = new Notification.Builder(context, CHANNEL_ID)
                            .setContentTitle(title)
                            .setContentText(body)
                            .setSmallIcon(R.drawable.imuicon_drawio_removebg_preview)
                            .setAutoCancel(true);
                    if (ActivityCompat.checkSelfPermission(context, android.Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                        return;
                    }
                    NotificationManagerCompat.from(context).notify(1, notification.build());

                }else{
                    String NOTIFICATION_CHANNEL_ID = "my_channel_id_01";
                    NotificationCompat.Builder notificationBuilder = new NotificationCompat.Builder(context, NOTIFICATION_CHANNEL_ID)
                            .setContentTitle(title)
                            .setContentText(body)
                            .setSmallIcon(R.drawable.imuicon_drawio_removebg_preview)
                            .setAutoCancel(true);

                    NotificationManager notificationManager =
                            (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);
                    notificationManager.notify(/*notification id*/1, notificationBuilder.build());
                }
            }

            void start(Parameter parameter) {
                this.parameter = parameter;
                metawears = new ArrayList<>();
                dataHandlers = new ArrayList<>();
                streamMetrics = new ArrayList<>();
                samples = new LinkedHashMap<>();

                getApplicationContext().bindService(new Intent(Service.this, BtleService.class), Service.this, Context.BIND_AUTO_CREATE);
                active = true;
                showNotifcation("IMU sensors", "The data logging has started!", getApplicationContext());
            }
        }

        @Override
        public void onDestroy() {
            localBinder.active = false;
            Constants urlPort = new Constants();
            String hostUrl = urlPort.getHostUrl();
            Integer port = urlPort.getPort();
            Client newClient = new Client(hostUrl,port, "TERMINATED");
            newClient.execute();
            getApplicationContext().unbindService(this);

            super.onDestroy();
        }

        @Nullable
        @Override
        public IBinder onBind(Intent intent) {
            return localBinder;
        }
    }

    private Parameter parameter;
    private Service.LocalBinder binder;
    private Intent streamServiceIntent;
    private TextView elapsedTimeText;

    private Handler uiScheduler= new Handler();
    private final Runnable updateValues= new Runnable() {
        @Override
        public void run() {
            for(DataHandler.SampleCountDataHandler it: binder.streamMetrics) {
                it.sampleCountView.setText(String.format(Locale.US, "%d", it.samples));
            }

            long elapsed= System.nanoTime() - binder.start;
            elapsedTimeText.setText(String.format(Locale.US, "%02d:%02d:%02d", (elapsed / 3600000000000L) % 24, (elapsed / 60000000000L) % 60, (elapsed / 1000000000L) % 60));

            uiScheduler.postDelayed(updateValues, 1000L);
        }
    };

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container, @Nullable Bundle savedInstanceState) {
        return inflater.inflate(R.layout.fragment_stream_monitor, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        elapsedTimeText= view.findViewById(R.id.elapsed_time);
        elapsedTimeText.setText("00:00:00");
        view.findViewById(R.id.stream_stop).setOnClickListener(v -> {

            owner.stopService(streamServiceIntent);

            final long stop = System.nanoTime();
            uiScheduler.removeCallbacks(updateValues);

            final AlertDialog resetDialog = new AlertDialog.Builder(owner)
                    .setTitle(R.string.title_cleanup)
                    .setView(R.layout.indeterminate_task)
                    .create();
            resetDialog.show();
            ((TextView) resetDialog.findViewById(R.id.message)).setText(R.string.message_reset_devices);

            List<Task<Void>> tasks = new ArrayList<>();
            for(MetaWearBoard m: binder.metawears) {
                if (m.isConnected()) {
                    tasks.add(m.getModule(Debug.class).resetAsync());
                }
            }
            Task.whenAll(tasks).continueWithTask(ignored -> {
                for(DataHandler it: binder.dataHandlers) {
                    it.stop();
                }
                for(Pair<MetaBaseDevice, Map<SensorConfig, Route>> it: binder.parameter.devices) {
                    it.first.isDiscovered = false;
                    activityBus.removeMetaWearBoard(it.first.btDevice);
                }

                if (BuildConfig.LOG_EVENT) {
                    Bundle bundle = new Bundle();
                    bundle.putLong(FIREBASE_PARAM_LOG_DURATION, (stop - binder.start) / 1000L);
                    for (Map.Entry<MetaBaseDevice, List<Pair<SensorConfig, DataHandler.SampleCountDataHandler>>> it : binder.samples.entrySet()) {
                        for (Pair<SensorConfig, DataHandler.SampleCountDataHandler> it2 : it.getValue()) {
                            bundle.putInt(getString(it2.first.nameResId).toLowerCase().replaceAll(" ", "_"), it2.second.samples);
                        }
                    }
                }

                final Capture<EditText> sessionName = new Capture<>();
                final Capture<TextInputLayout> sessionNameTextWrapper = new Capture<>();
                TaskCompletionSource<String> sessionNameTaskSource = new TaskCompletionSource<>();
                owner.runOnUiThread(() -> {
                    resetDialog.dismiss();
                    final AlertDialog sessionDialog = new AlertDialog.Builder(owner)
                            .setTitle(R.string.title_session_name)
                            .setView(R.layout.dialog_item_naming)
                            .setCancelable(false)
                            .setPositiveButton(android.R.string.ok, null)
                            .create();
                    sessionDialog.show();

                    ((TextView) sessionDialog.findViewById(R.id.instructions_text)).setText(R.string.instruction_name_session);
                    sessionName.set(sessionDialog.findViewById(R.id.item_name));
                    sessionNameTextWrapper.set(sessionDialog.findViewById(R.id.item_name_wrapper));

                    Calendar calendar = Calendar.getInstance();
                    SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd-HH-mm-ss", Locale.getDefault());
                    String currentDateTime = dateFormat.format(calendar.getTime());

                    sessionDialog.dismiss();
                    sessionNameTaskSource.setResult(currentDateTime);

                    sessionDialog.getButton(DialogInterface.BUTTON_POSITIVE).setOnClickListener(v2 -> {
                        String customName = sessionName.get().getText().toString();
                        if (customName.contains("_")) {
                            sessionNameTextWrapper.get().setError(owner.getString(R.string.error_underscore));
                        } else {
                            sessionNameTextWrapper.get().setError(null);
                            sessionDialog.dismiss();

                            sessionNameTaskSource.setResult(customName);
                        }
                    });
                });
                return sessionNameTaskSource.getTask();
            }).continueWith(task -> {
                String name = task.getResult();
                binder.session.name = name.length() == 0 ?
                        String.format(Locale.US, "%sSession %d", binder.parameter.devices.size() > 1 ? binder.parameter.name + " ": "", binder.parameter.sessions.size() + 1) :
                        name;

                String[] paths = new String[binder.session.files.size()];
                int i = 0;
                List<File> renamed = new ArrayList<>();
                for(File it: binder.session.files) {
                    File newName = new File(it.getParent(), String.format(Locale.US, "%s_%s", binder.session.name, it.getName()));
                    if (it.renameTo(newName)) {
                        renamed.add(newName);
                        paths[i] = newName.getAbsolutePath();
                    } else {
                        renamed.add(it);
                        paths[i] = it.getAbsolutePath();
                    }
                    i++;
                }

                MediaScannerConnection.scanFile(owner, paths, null, null);

                binder.session.files.clear();
                binder.session.files.addAll(renamed);
                binder.parameter.sessions.add(0, binder.session);
//                System.exit(1);
                activityBus.navigateBack();

                return null;
            });
//            Constants urlPort = new Constants();
//            String hostUrl = urlPort.getHostUrl();
//            Integer port = urlPort.getPort();
//            Client newClient = new Client(hostUrl,port, "TERMINATED");
//            newClient.execute();

//            new Handler().postDelayed(() -> {
//                //owner.getApplicationContext().unbindService(this);
//                //super.onDestroy();
//                //Intent intent = new Intent(owner.getApplicationContext(), HomeActivity.class);
//                //startActivity(intent);
//                bringAppToForeground();
//                System.out.println("!!!!!!!!!!!!!!!!!!!!11111111111");
//            }, 2000);
            new Handler().postDelayed(() -> {
                //owner.getApplicationContext().unbindService(this);
                //super.onDestroy();
                //Intent intent = new Intent(owner.getApplicationContext(), HomeActivity.class);
                //startActivity(intent);
                System.out.println("!!!!!!!!!!!!!!!!!!!!22222222");
//                System.runFinalization();
//                Runtime.getRuntime().gc();
//                System.gc();
                //owner.finishAffinity();
                //printRunningProcesses();
                //closeProcesses();
                //System.exit(1);
                int pid = android.os.Process.myPid();
                getActivity().finish();
                getActivity().finishAffinity();
                System.out.println("$$$$$ " + pid);
                binder.showNotifcation("IMU sensors", "The data logging has been completed!", getContext());
                android.os.Process.killProcess(pid);

                System.exit(0);

//                new Handler().postDelayed(new Runnable() {
//                    @Override
//                    public void run() {
//                        bringAppToForeground();
//                    }
//                }, 200);
            }, 15000);



        });
        new Handler().postDelayed(() -> {
            Button streamStopButton = view.findViewById(R.id.stream_stop);
            if (streamStopButton != null) {
                streamStopButton.performClick();
                //System.exit(1);
            }
        }, 121000);
    }

    private void printRunningProcesses() {
        ActivityManager activityManager = (ActivityManager) owner.getSystemService(Context.ACTIVITY_SERVICE);
        List<ActivityManager.RunningAppProcessInfo> runningAppProcesses = activityManager.getRunningAppProcesses();

        if (runningAppProcesses != null) {
            Log.d("RunningProcesses", "Printing running processes:");
            for (ActivityManager.RunningAppProcessInfo processInfo : runningAppProcesses) {
                Log.d("RunningProcesses", "Process Name: " + processInfo.processName);
            }
        }
    }

    private void closeProcesses() {
        ActivityManager activityManager = (ActivityManager) owner.getSystemService(Context.ACTIVITY_SERVICE);
        List<ActivityManager.RunningAppProcessInfo> runningAppProcesses = activityManager.getRunningAppProcesses();

        if (runningAppProcesses != null) {
            Log.d("CloseProcesses", "Closing processes:");
            for (ActivityManager.RunningAppProcessInfo processInfo : runningAppProcesses) {
                // Exclude your own application process
                //if (!processInfo.processName.equals(getPackageName())) {
                    Log.d("CloseProcesses", "Closing process: " + processInfo.processName);
                    activityManager.killBackgroundProcesses(processInfo.processName);
                //}
            }
        }
    }

    private void bringAppToForeground() {
        Intent intent = new Intent(HomeActivity.getActiveInstance().getApplicationContext(), HomeActivity.class);
        intent.setAction(Intent.ACTION_MAIN);
        intent.addCategory(Intent.CATEGORY_LAUNCHER);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_SINGLE_TOP);

        PendingIntent pendingIntent = PendingIntent.getActivity(
                owner.getApplicationContext(), 0, intent, PendingIntent.FLAG_IMMUTABLE
        );

        try {
            pendingIntent.send();

            new Handler().postDelayed(new Runnable() {
                @Override
                public void run() {
                    closeProcesses();
                }
            }, 2000);


        } catch (PendingIntent.CanceledException e) {
            e.printStackTrace();
        }
    }

    @Override
    public void onActivityCreated(@Nullable Bundle savedInstanceState) {

        super.onActivityCreated(savedInstanceState);

        parameter = (Parameter) activityBus.parameter();
        streamServiceIntent = new Intent(owner, Service.class);
        owner.startService(streamServiceIntent);
        owner.getApplicationContext().bindService(streamServiceIntent, this, Context.BIND_AUTO_CREATE);

        activityBus.popBackstack();
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();

        owner.getApplicationContext().unbindService(this);
    }

    @Override
    Integer getMenuGroupResId() {
        return null;
    }

    @Override
    public void onServiceConnected(ComponentName name, IBinder service) {
        binder = (Service.LocalBinder) service;

        Action3<MetaWearBoard, TextView, ImageView> dcHandler = (m, deviceName, alert) -> {
            owner.runOnUiThread(() -> {
                deviceName.setTextColor(Color.argb(0xff, 0xcc, 0x00, 0x00));
                alert.setVisibility(View.VISIBLE);
            });
            final Capture<Integer> delay = new Capture<>(5000);
            Task.forResult(null).continueWhile(() -> !m.isConnected(), ignored -> m.connectAsync().continueWithTask(connTask -> {
                if (connTask.isFaulted()) {
                    return Task.delay(delay.get()).continueWithTask(ignored2 -> {
                        delay.set(Math.min((int) (delay.get() * 1.5), 30000));
                        return m.connectAsync();
                    });
                }
                return connTask;
            })).onSuccess(ignored3 -> {
                deviceName.setTextColor(Color.argb(0xff, 0x66, 0x99, 0x6e));
                alert.setVisibility(View.INVISIBLE);
                return null;
            }, Task.UI_THREAD_EXECUTOR);
        };
        if (!binder.active) {
            binder.start(parameter);

            Calendar now = Calendar.getInstance();
            binder.session = new AppState.Session("", String.format(Locale.US, DataHandler.CsvDataHandler.TIMESTAMP_FORMAT, now));

            LinearLayout metrics = getView().findViewById(R.id.metrics);
            //System.out.println("!!!!!!!! " + parameter.devices.size());

            try {
                for (Pair<MetaBaseDevice, Map<SensorConfig, Route>> it : parameter.devices) {
                    final DataHandler.SampleCountDataHandler sampleCounter = new DataHandler.SampleCountDataHandler();
                    sampleCounter.init();
                    binder.dataHandlers.add(sampleCounter);
                    binder.streamMetrics.add(sampleCounter);

                    LinearLayout status = (LinearLayout) getLayoutInflater().inflate(R.layout.board_status, null);
                    final TextView deviceName = status.findViewById(R.id.device_name);
                    final ImageView alert = status.findViewById(R.id.alert_reconnecting);

                    deviceName.setText(it.first.name);
                    sampleCounter.sampleCountView = status.findViewById(R.id.sample_count);
                    sampleCounter.sampleCountView.setText("0");

                    final MetaWearBoard m = activityBus.getMetaWearBoard(it.first.btDevice);
                    m.onUnexpectedDisconnect(code -> dcHandler.apply(m, deviceName, alert));
                    binder.metawears.add(m);

                    List<Pair<SensorConfig, DataHandler.SampleCountDataHandler>> sensorSamples = new ArrayList<>();
                    JseMetaWearBoard casted = (JseMetaWearBoard) m;
                    File csvDest = new File(AppState.devicesPath, it.first.getFileFriendlyMac());
                    for (Map.Entry<SensorConfig, Route> it2 : it.second.entrySet()) {
                        String filename = String.format(Locale.US, "%s_" + DataHandler.CsvDataHandler.TIMESTAMP_FORMAT + "_%s_%s_%s_%s.csv",
                                it.first.name,
                                now,
                                it.first.getFileFriendlyMac(),
                                owner.getString(it2.getKey().nameResId),
                                it2.getKey().selectedFreqText(),
                                casted.getFirmware()
                        );
                        File output = new File(csvDest, filename);
                        //binder.session.files.add(output);
                        final DataHandler csvWriter;
                        //Client newClient = new Client("195.130.118.252",12345, "!!!!!!!!");
                        try {
                            DataHandler.SampleCountDataHandler sensorCount = new DataHandler.SampleCountDataHandler();
                            sensorSamples.add(new Pair<>(it2.getKey(), sensorCount));

                            csvWriter = new DataHandler.CsvDataHandler(new FileOutputStream(output), it2.getValue().generateIdentifier(0), it2.getKey().frequency(m), true);
                            csvWriter.init();
                            //csvWriter.setClient(newClient);
                            //binder.dataHandlers.add(csvWriter);

                            csvWriter.setName(it.first.name);
                            csvWriter.setMac(it.first.getFileFriendlyMac());
                            it2.getValue().resubscribe(0, (data, env) -> {
                                sampleCounter.process(data);
                                csvWriter.process(data);
                                sensorCount.process(data);
                            });
//                        Constants urlPort = new Constants();
//                        String hostUrl = urlPort.getHostUrl();
//                        Integer port = urlPort.getPort();
//                        String message = csvWriter.getMessage();
//                        Client newClient = new Client(hostUrl,port, message);
//
//                        newClient.execute();

                        } catch (FileNotFoundException e) {
                            Log.w("metabase", "Failed to create CSV file for sensor [" + owner.getString(it2.getKey().nameResId) + ", " + m.getMacAddress() + "]");
                        }
                    }

                    binder.samples.put(it.first, sensorSamples);
                    metrics.addView(status);
                }

                for (int i = 0; i < parameter.devices.size(); i++) {
                    for (Map.Entry<SensorConfig, Route> it2 : parameter.devices.get(i).second.entrySet()) {
                        it2.getKey().start(binder.metawears.get(i));
                    }
                }
            }
            catch (Exception e){
                Intent intent = getActivity().getBaseContext().getPackageManager().getLaunchIntentForPackage(getActivity().getBaseContext().getPackageName());
                intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
                startActivity(intent);
                getActivity().finish();
            }
//            }
//            catch (Exception e){
//                System.out.println("%%%%%%%%%222");
//                Intent intent = owner.getBaseContext().getPackageManager().getLaunchIntentForPackage(owner.getBaseContext().getPackageName());
//                intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
//                startActivity(intent);
//                new Handler().postDelayed(new Runnable() {
//                    @Override
//                    public void run() {
//                        bringAppToForeground();
//                    }
//                }, 200);
//            }
            binder.start = System.nanoTime();
            uiScheduler.postDelayed(updateValues, 1000L);
        } else {
            LinearLayout metrics = getView().findViewById(R.id.metrics);
            int i = 0;
            for (MetaBaseDevice d: binder.samples.keySet()) {
                LinearLayout status = (LinearLayout) getLayoutInflater().inflate(R.layout.board_status, null);
                final TextView deviceName = status.findViewById(R.id.device_name);
                final ImageView alert = status.findViewById(R.id.alert_reconnecting);

                MetaWearBoard m = activityBus.getMetaWearBoard(d.btDevice);
                m.onUnexpectedDisconnect(code -> dcHandler.apply(m, deviceName, alert));

                deviceName.setText(d.name);
                binder.streamMetrics.get(i).sampleCountView = status.findViewById(R.id.sample_count);
                binder.streamMetrics.get(i).sampleCountView.setText(String.format(Locale.US, "%d", binder.streamMetrics.get(i).samples));

                metrics.addView(status);
            }
        }
    }

    @Override
    public void onServiceDisconnected(ComponentName name) {

    }
}
