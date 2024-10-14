package com.mbientlab.metawear.metabase;
import com.google.gson.Gson;

class SensorData {
    private String deviceMacAddress;
    private long timestamp;
    private double w;
    private double x;
    private double y;
    private double z;

    // Constructor
    public SensorData(String deviceMacAddress, long timestamp, double w, double x, double y, double z) {
        this.deviceMacAddress = deviceMacAddress;
        this.timestamp = timestamp;
        this.w = w;
        this.x = x;
        this.y = y;
        this.z = z;
    }

    public SensorData() {

    }

    // Getters and setters
    public String getDeviceMacAddress() {
        return deviceMacAddress;
    }

    public void setDeviceMacAddress(String deviceMacAddress) {
        this.deviceMacAddress = deviceMacAddress;
    }

    public long getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }

    public double getW() {
        return w;
    }

    public void setW(double w) {
        this.w = w;
    }

    public double getX() {
        return x;
    }

    public void setX(double x) {
        this.x = x;
    }

    public double getY() {
        return y;
    }

    public void setY(double y) {
        this.y = y;
    }

    public double getZ() {
        return z;
    }

    public void setZ(double z) {
        this.z = z;
    }

    @Override
    public String toString() {
        return "{" + deviceMacAddress + ' ' +
                ", timestamp=" + timestamp +
                ", w=" + w +
                ", x=" + x +
                ", y=" + y +
                ", z=" + z +
                '}';
    }

    // Method to serialize SensorData to JSON
    public String toJson() {
        Gson gson = new Gson();
        return gson.toJson(this);
    }

    // Method to deserialize JSON to SensorData
    public static SensorData fromJson(String json) {
        Gson gson = new Gson();
        return gson.fromJson(json, SensorData.class);
    }
}
