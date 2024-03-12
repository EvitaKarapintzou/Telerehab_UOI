
package com.mbientlab.metawear.metabase;

import java.util.ArrayList;
import java.util.List;

class SelectedGrouping {
    final List<MetaBaseDevice> devices;
    final List<AppState.Session> sessions;
    final String name;

    SelectedGrouping(List<AppState.Session> sessions, String name) {
        System.out.println("$$$$ " + sessions.size() + " " + name);
        devices = new ArrayList<>();
        this.sessions = sessions;
        this.name = name;
    }
}
