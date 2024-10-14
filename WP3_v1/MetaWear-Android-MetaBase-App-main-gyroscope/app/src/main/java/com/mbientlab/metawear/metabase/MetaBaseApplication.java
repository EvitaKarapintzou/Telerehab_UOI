
package com.mbientlab.metawear.metabase;

import android.app.Application;
import android.os.Build;
import no.nordicsemi.android.dfu.DfuServiceInitiator;

/**
 * Created by eric on 10/26/16.
 */

public class MetaBaseApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        Global.connInterval = Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? 11.25f : 7.5f;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            DfuServiceInitiator.createDfuNotificationChannel(this);
        }
    }
}
