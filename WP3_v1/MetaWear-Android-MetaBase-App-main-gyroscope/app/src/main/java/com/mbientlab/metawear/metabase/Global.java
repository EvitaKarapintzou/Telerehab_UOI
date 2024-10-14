
package com.mbientlab.metawear.metabase;

/**
 * Created by eric on 10/26/16.
 */

class Global {
    static final String FIREBASE_PARAM_MODEL = "model",
            FIREBASE_PARAM_DEVICE_NAME = "device_name",
            FIREBASE_PARAM_FIRMWARE = "firmware",
            FIREBASE_PARAM_MAC = "mac",
            FIREBASE_PARAM_LOG_DURATION = "duration";
    static float connInterval = 11.25f;

    static final int nameMaxChar = 26, METABASE_SCAN_ID = 0x2, COMPANY_ID = 0x067e, OLD_COMPANY_Id = 0x626d;

    static String getRealModel(String original, String modelNumber) {
        if (original != null) return original;
        if (modelNumber == null) return "Unknown";
        switch(modelNumber) {
            case "10":
                return "Smilables";
            case "11":
                return "Beiersdorf";
            case "12":
                return "BlueWillow";
            case "13":
                return "Andres";
            case "14":
                return "Panasonic";
            case "15":
                return "MAS";
            case "16":
                return "Palarum";
        }
        return "Unknown";
    }
}
