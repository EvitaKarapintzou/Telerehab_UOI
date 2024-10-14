package com.mbientlab.metawear.metabase;

public class Constants {
    // Bluetooth MAC addresses of the IMUs
    public static final String DEVICE_MAC_ADDRESS_01 = "EF:0F:A9:3D:48:AA";
    public static final String DEVICE_MAC_ADDRESS_02 = "EE:E2:E3:B4:9A:D7";
    public static final String DEVICE_MAC_ADDRESS_03 = "ED:B1:65:CE:EF:D4";
    public static final String DEVICE_MAC_ADDRESS_04 = "DA:C1:9F:1B:6E:40";

    // Timeout and retry values for connection attempts
    public static final int CONNECTION_TIMEOUT_MS = 5000;
    public static final int MAX_RETRY_ATTEMPTS = 5;
    public static final long RETRY_DELAY_MS = 5000;  // 5 seconds delay between retries

    // Recording duration
    public static final int RECORDING_DURATION_MS = 40000;  // 20 seconds

    // LED Configuration
    public static final short LED_RISE_TIME = 500;
    public static final short LED_PULSE_DURATION = 1000;
    public static final byte LED_REPEAT_COUNT = -1;  // Led.PATTERN_REPEAT_INDEFINITELY
    public static final short LED_HIGH_TIME = 500;
    public static final byte LED_HIGH_INTENSITY = 31;
    public static final byte LED_LOW_INTENSITY = 0;

    // Logging Tags
    public static final String LOG_TAG_SCANNER = "Scanner";
    public static final String LOG_TAG_IMU_MANAGER = "IMUManager";

    // Other constants
    public static final boolean STOP_LED_ON_DISCONNECT = true;
}
