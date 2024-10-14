package com.mbientlab.metawear.metabase;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

/**
 * MainActivity is the entry point of the app. It starts the BackgroundService.
 */
public class MainActivity extends AppCompatActivity {

    private static final int PERMISSION_REQUEST_CODE = 1;
    private MQTTManager mqttManager;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // Check Bluetooth permissions and handle accordingly
        checkBluetoothPermissions();
    }

    /**
     * Checks for necessary Bluetooth permissions and requests them if not granted.
     */
    private void checkBluetoothPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            if (checkSelfPermission(Manifest.permission.BLUETOOTH_SCAN) != PackageManager.PERMISSION_GRANTED ||
                    checkSelfPermission(Manifest.permission.BLUETOOTH_CONNECT) != PackageManager.PERMISSION_GRANTED ||
                    checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) {

                // Request the necessary Bluetooth permissions
                requestPermissions(new String[]{
                        Manifest.permission.BLUETOOTH_SCAN,
                        Manifest.permission.BLUETOOTH_CONNECT,
                        Manifest.permission.ACCESS_FINE_LOCATION
                }, PERMISSION_REQUEST_CODE);
            } else {
                // Permissions are granted, start services and MQTT connection
                initializeMQTTAndServices();
            }
        } else {
            // For devices with SDK < 31, directly start the service
            initializeMQTTAndServices();
        }
    }

    /**
     * Handles the result of the Bluetooth permission request.
     */
    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode == PERMISSION_REQUEST_CODE) {
            boolean allPermissionsGranted = true;
            for (int result : grantResults) {
                if (result != PackageManager.PERMISSION_GRANTED) {
                    allPermissionsGranted = false;
                    break;
                }
            }

            if (allPermissionsGranted) {
                // All permissions were granted, initialize services and MQTT connection
                initializeMQTTAndServices();
            } else {
                // Show a message if permissions were denied
                Toast.makeText(this, "Bluetooth permissions are required for this app to work.", Toast.LENGTH_LONG).show();
                finish(); // Close the app as it won't function properly without permissions
            }
        }
    }

    /**
     * Initializes the MQTTManager and starts the background service.
     */
    private void initializeMQTTAndServices() {
        // Initialize MQTT Manager with the broker URL (replace with your broker's URL)
        mqttManager = new MQTTManager(this, "tcp://192.168.1.96:1883");
        //mqttManager = new MQTTManager(this, "tcp://192.168.0.247:1883");
        mqttManager.connect();
        //mqttManager.subscribe("test", 1);

        // Start the BackgroundService
        //startBackgroundService();
        moveTaskToBack(true);
    }

    /**
     * Starts the BackgroundService.
     */
    public void startBackgroundService() {
        Intent serviceIntent = new Intent(this, BackgroundService.class);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            startForegroundService(serviceIntent);  // Required for Android O and above
        } else {
            startService(serviceIntent);  // For older versions
        }
        Log.i("MainActivity", "BackgroundService started.");

        // Close the activity as it's only needed to start the service
        finish();
    }
}
