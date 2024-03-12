
package com.mbientlab.metawear.metabase;

import android.app.Activity;;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.content.FileProvider;
import androidx.recyclerview.widget.RecyclerView;
import android.os.Handler;
import android.view.LayoutInflater;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import bolts.TaskCompletionSource;

public class DeviceInfoFragment extends AppFragmentBase {
    private static final String FIREBASE_EVENT_CLOUD_SYNC_SUCCESS = "sync_metacloud";

    interface MetaCloudOptions {
        boolean showAbout();
        void disableAbout();
    }

    private static final int LOGIN_REQUEST = 0;

    private TaskCompletionSource<Void> loginTaskSource;

    private MetaBaseDevice.Adapter devicesAdapter;
    private AppState.Session.Adapter sessionsAdapter;
    private Button startBtn;
    private TextView title;
    private SelectedGrouping parameter;
    private MetaCloudOptions options;
    private Handler handler = new Handler();
    private AppFragmentBase currentFragment = null;
    public DeviceInfoFragment() {
        // Required empty public constructor
    }

    @Override
    public void onActivityResult(int requestCode, int resultCode, Intent data) {
        switch(requestCode) {
            case LOGIN_REQUEST:
                if (resultCode == Activity.RESULT_OK) {
                    loginTaskSource.setResult(null);
                } else if (resultCode == Activity.RESULT_CANCELED) {
                    loginTaskSource.setCancelled();
                } else {
                    loginTaskSource.setError(new RuntimeException("MetaCloud login failed"));
                }
                break;
            default:
                super.onActivityResult(requestCode, resultCode, data);
        }
    }


    private void updateStartBtn() {
        boolean present = true;
        boolean enableDownload = false;

        for(MetaBaseDevice d: parameter.devices) {
            enableDownload |= d.isRecording;
            present &= d.isDiscovered;
        }

        if (present) {
            startBtn.setVisibility(View.VISIBLE);
            if (enableDownload) {
                startBtn.setText(R.string.title_download);
                startBtn.setOnClickListener(v -> activityBus.swapFragment(DataDownloadFragment.class, parameter));
            } else {
                System.out.println("EDWWWWWWWWWWW");
                startBtn.setText(R.string.label_new_session);
                activityBus.swapFragment(DeviceConfigFragment.class, parameter);
            }
        } else {
            startBtn.setVisibility(View.GONE);
            startBtn.setOnClickListener(null);
        }
    }

    @Override
    public void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        devicesAdapter = new MetaBaseDevice.Adapter();
        devicesAdapter.itemClicked = arg1 -> activityBus.swapFragment(DiagnosticFragment.class, arg1);
        sessionsAdapter = new AppState.Session.Adapter();
        setHasOptionsMenu(true);
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        switch(item.getItemId()) {
            default:
                return super.onOptionsItemSelected(item);
        }
    }

    @Override
    public void onActivityCreated(@Nullable Bundle savedInstanceState) {
        super.onActivityCreated(savedInstanceState);
        if (!(getActivity() instanceof MetaCloudOptions)) {
            throw new ClassCastException("Owning activity does not derive from MetaCloudOptions");
        }
        options = (MetaCloudOptions) getActivity();
        parameter = (SelectedGrouping) activityBus.parameter();
        if (parameter.devices.size() == 1) {
            title.setText(R.string.label_device);
        } else {
            title.setText(parameter.name);
        }
        devicesAdapter.items.clear();
        devicesAdapter.items.addAll(parameter.devices);
        devicesAdapter.notifyDataSetChanged();
        sessionsAdapter.items.clear();
        sessionsAdapter.items.addAll(parameter.sessions);
        sessionsAdapter.notifyDataSetChanged();
        sessionsAdapter.shareSession = arg1 -> {
            final StringBuilder devices = new StringBuilder();
            boolean first = true;
            for(MetaBaseDevice d: parameter.devices) {
                if (!first) {
                    devices.append(", ");
                }
                devices.append(d.mac);
                first = false;
            }
            final Intent intentShareFile = new Intent(Intent.ACTION_SEND_MULTIPLE);
            intentShareFile.setType("text/plain");
            intentShareFile.putExtra(Intent.EXTRA_SUBJECT, String.format(Locale.US, "MetaBase Session: %s", arg1.name));
            ArrayList<Uri> uris = new ArrayList<>();
            for (File it : arg1.files) {
                uris.add(FileProvider.getUriForFile(owner, "com.mbientlab.metawear.metabase.fileprovider", it));
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    intentShareFile.setData(FileProvider.getUriForFile(owner, "com.mbientlab.metawear.metabase.fileprovider", it));
                    intentShareFile.setFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
                }
            }
            intentShareFile.putParcelableArrayListExtra(Intent.EXTRA_STREAM, uris);
            intentShareFile.putExtra(Intent.EXTRA_TEXT, String.format(Locale.US, "Boards: [%s]", devices.toString()));
            Intent chooser = Intent.createChooser(intentShareFile, "Share File");
            List<ResolveInfo> resInfoList = owner.getPackageManager().queryIntentActivities(chooser, PackageManager.MATCH_DEFAULT_ONLY);
            for (ResolveInfo resolveInfo : resInfoList) {
                String packageName = resolveInfo.activityInfo.packageName;
                for (Uri uri : uris) {
                    owner.grantUriPermission(packageName, uri, Intent.FLAG_GRANT_WRITE_URI_PERMISSION | Intent.FLAG_GRANT_READ_URI_PERMISSION);
                }
            }
            startActivity(chooser);
        };

        activityBus.scanner().start(arg1 -> {
            devicesAdapter.update(arg1);
            updateStartBtn();
        });
        updateStartBtn();

    }

    @Override
    public void onResume() {
        super.onResume();
        owner.invalidateOptionsMenu();
    }

    @Override
    public void onPause() {
        super.onPause();
        Bundle savedInstanceState = new Bundle();
        onSaveInstanceState(savedInstanceState);
    }

    @Override
    public void onPrepareOptionsMenu(Menu menu) {
        super.onPrepareOptionsMenu(menu);
    }

    @Override
    Integer getMenuGroupResId() {
        return R.id.group_dev_info;
    }

    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState) {
        return inflater.inflate(R.layout.fragment_device_info, container, false);
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        RecyclerView devices = view.findViewById(R.id.known_devices);
        devices.setAdapter(devicesAdapter);
        devicesAdapter.notifyDataSetChanged();
        RecyclerView sessions = view.findViewById(R.id.sessions);
        sessions.setAdapter(sessionsAdapter);
        startBtn = view.findViewById(R.id.start);
        title = view.findViewById(R.id.title_devices);
    }
}
