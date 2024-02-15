/*
 * Copyright 2014-2018 MbientLab Inc. All rights reserved.
 *
 * IMPORTANT: Your use of this Software is limited to those specific rights
 * granted under the terms of a software license agreement between the user who
 * downloaded the software, his/her employer (which must be your employer) and
 * MbientLab Inc, (the "License").  You may not use this Software unless you
 * agree to abide by the terms of the License which can be found at
 * www.mbientlab.com/terms . The License limits your use, and you acknowledge,
 * that the  Software may not be modified, copied or distributed and can be used
 * solely and exclusively in conjunction with a MbientLab Inc, product.  Other
 * than for the foregoing purpose, you may not use, reproduce, copy, prepare
 * derivative works of, modify, distribute, perform, display or sell this
 * Software and/or its documentation for any purpose.
 *
 * YOU FURTHER ACKNOWLEDGE AND AGREE THAT THE SOFTWARE AND DOCUMENTATION ARE
 * PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESS OR IMPLIED,
 * INCLUDING WITHOUT LIMITATION, ANY WARRANTY OF MERCHANTABILITY, TITLE,
 * NON-INFRINGEMENT AND FITNESS FOR A PARTICULAR PURPOSE. IN NO EVENT SHALL
 * MBIENTLAB OR ITS LICENSORS BE LIABLE OR OBLIGATED UNDER CONTRACT, NEGLIGENCE,
 * STRICT LIABILITY, CONTRIBUTION, BREACH OF WARRANTY, OR OTHER LEGAL EQUITABLE
 * THEORY ANY DIRECT OR INDIRECT DAMAGES OR EXPENSES INCLUDING BUT NOT LIMITED
 * TO ANY INCIDENTAL, SPECIAL, INDIRECT, PUNITIVE OR CONSEQUENTIAL DAMAGES, LOST
 * PROFITS OR LOST DATA, COST OF PROCUREMENT OF SUBSTITUTE GOODS, TECHNOLOGY,
 * SERVICES, OR ANY CLAIMS BY THIRD PARTIES (INCLUDING BUT NOT LIMITED TO ANY
 * DEFENSE THEREOF), OR OTHER SIMILAR COSTS.
 *
 * Should you have any questions regarding your right to use this Software,
 * contact MbientLab Inc, at www.mbientlab.com.
 */

package com.mbientlab.metawear.metabase;

import static androidx.constraintlayout.helper.widget.MotionEffect.TAG;

import static com.mbientlab.metawear.metabase.database.addNewData;
import static com.mbientlab.metawear.metabase.database.clearData;
import static com.mbientlab.metawear.metabase.database.getData;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.content.pm.PackageManager;
import android.os.Build;
import android.util.Log;
import android.widget.TextView;

import androidx.core.app.ActivityCompat;
import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;

import com.google.gson.Gson;
import com.mbientlab.metawear.Data;

import org.eclipse.paho.android.service.MqttAndroidClient;
import org.eclipse.paho.client.mqttv3.IMqttActionListener;
import org.eclipse.paho.client.mqttv3.IMqttToken;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;

import java.io.FileOutputStream;
import java.io.IOException;
import java.security.InvalidParameterException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;
import java.util.TimeZone;


interface DataHandler {
    void init();
    void process(Data data);
    void stop();
    void setClient(Client newClient);

    String getMessage();

    void setName(String name);

    void setMac(String mac);

    class CsvDataHandler implements DataHandler {
        static final String TIMESTAMP_FORMAT = "%tY-%<tm-%<tdT%<tH.%<tM.%<tS.%<tL", TZ_OFFSET;
        private static final Map<String, String> CSV_HEADERS;
        private static Client newClient;
        private String message = "";
        private String name = "";
        private String mac = "";
        private Integer seq_packet = 0;
        static {
            CSV_HEADERS = new HashMap<>();
            CSV_HEADERS.put("acceleration", "x-axis (g),y-axis (g),z-axis (g)");
            CSV_HEADERS.put("angular-velocity", "x-axis (deg/s),y-axis (deg/s),z-axis (deg/s)");
            CSV_HEADERS.put("magnetic-field", "x-axis (T),y-axis (T),z-axis (T)");
            CSV_HEADERS.put("linear-acceleration", "x-axis (g),y-axis (g),z-axis (g)");
            CSV_HEADERS.put("gravity", "x-axis (g),y-axis (g),z-axis (g)");
            CSV_HEADERS.put("euler-angles", "pitch (deg),roll (deg),yaw (deg), heading (deg)");
            CSV_HEADERS.put("quaternion", "w (number),x (number),y (number), z (number)");
            CSV_HEADERS.put("illuminance", "illuminance (lx)");
            CSV_HEADERS.put("relative-humidity", "relative humidity (%)");
            CSV_HEADERS.put("pressure", "pressure (Pa)");
            CSV_HEADERS.put("temperature", "temperature (C)");

            SimpleDateFormat df= new SimpleDateFormat("HH:mm", Locale.US);
            TimeZone defaultTz= TimeZone.getDefault();
            int offset= defaultTz.useDaylightTime() ? defaultTz.getRawOffset() - defaultTz.getDSTSavings() : defaultTz.getRawOffset();
            TZ_OFFSET = offset < 0 ? "-" + df.format(offset) : df.format(offset);
        }

        static String formatTimestamp(Calendar datetime) {
            return String.format(Locale.US, "%tY-%<tm-%<tdT%<tH:%<tM:%<tS.%<tL", datetime);
        }

        final boolean isStreaming;
        final String identifier, prefix;
        final private FileOutputStream fos;
        final private Float period;

        Calendar first, last;
        private Long start, next, prev;

        CsvDataHandler(FileOutputStream fos, String identifier, Float frequency, boolean isStreaming) {
            this.identifier = identifier;
            this.prefix = identifier.split("[:|\\[]")[0];
            this.fos = fos;
            this.period = (1f / frequency) * 1000;
            this.isStreaming = isStreaming;

            start = null;
            prev = null;
        }

        void setFirst(long epoch) {
            start = epoch;

            first = Calendar.getInstance();
            first.setTimeInMillis(epoch);
        }

        @Override
        public void init() {
            try {
                String additional;
                if (CSV_HEADERS.containsKey(prefix)) {
                    additional = CSV_HEADERS.get(prefix);
                } else {
                    throw new InvalidParameterException("Unknown identifier: " + identifier);
                }
                fos.write(String.format(Locale.US, "epoch (ms),time (%s),elapsed (s),%s%n", TZ_OFFSET, additional).getBytes());
            } catch (IOException ignored) {
            }
        }

        private void calcRealTimestamp(Data data, long mask) {
            if (!isStreaming) {
                last = data.timestamp();
                if (start == null) {
                    first = last;
                    start = first.getTimeInMillis();
                }

                return;
            } else {
                if (start == null) {
                    first = Calendar.getInstance();
                    start = first.getTimeInMillis();
                }
            }

            long count = data.extra(Long.class);
            if (prev == null) {
                prev = count;
                next = start;
            } else if (prev == count) {
                next += period.longValue();
            }

            if (count < prev) {
                long diff = (count - prev) & mask;
                next += (long) (diff * period);
            } else {
                next += (long) ((count - prev) * period);
            }

            prev = count;
            last = Calendar.getInstance();
            last.setTimeInMillis(next);
        }

        @Override
        public void process(Data data) {
            try {
                switch (prefix) {
                    case "acceleration":
                    case "angular-velocity": {
                        calcRealTimestamp(data, 0xffffffffL);
                        float offset = (last.getTimeInMillis() - start) / 1000.f;

                        float[] vector = data.value(float[].class);
                        fos.write(String.format(Locale.US, "%d,%s,%.3f,%.3f,%.3f,%.3f%n",
                                last.getTimeInMillis(), formatTimestamp(last), offset,
                                vector[0], vector[1], vector[2]).getBytes());
                        break;
                    }
                    case "magnetic-field": {
                        calcRealTimestamp(data, 0xffffffffL);
                        float offset = (last.getTimeInMillis() - start) / 1000.f;

                        float[] vector = data.value(float[].class);
                        fos.write(String.format(Locale.US,"%d,%s,%.3f,%.9f,%.9f,%.9f%n",
                                last.getTimeInMillis(), formatTimestamp(last), offset,
                                vector[0], vector[1], vector[2]).getBytes());
                        break;
                    }
                    case "linear-acceleration":
                    case "gravity": {
                        calcRealTimestamp(data, 0xffL);
                        float offset = (last.getTimeInMillis() - start) / 1000.f;

                        float[] vector = data.value(float[].class);
                        fos.write(String.format(Locale.US, "%d,%s,%.3f,%.3f,%.3f,%.3f%n",
                                last.getTimeInMillis(), formatTimestamp(last), offset,
                                vector[0], vector[1], vector[2]).getBytes());
                        break;
                    }
                    case "euler-angles": {
                        calcRealTimestamp(data, 0xffL);
                        float offset = (last.getTimeInMillis() - start) / 1000.f;

                        float[] vector4 = data.value(float[].class);
                        fos.write(String.format(Locale.US, "%d,%s,%.3f,%.3f,%.3f,%.3f,%.3f%n",
                                last.getTimeInMillis(), formatTimestamp(last), offset,
                                vector4[1], vector4[2], vector4[3], vector4[0]).getBytes());
                        break;
                    }
                    case "quaternion": {
                        calcRealTimestamp(data, 0xffL);
                        float offset = (last.getTimeInMillis() - start) / 1000.f;

                        float[] vector4 = data.value(float[].class);
                        fos.write(String.format(Locale.US, "%d,%s,%.3f,%.3f,%.3f,%.3f,%.3f%n",
                                last.getTimeInMillis(), formatTimestamp(last), offset,
                                vector4[0], vector4[1], vector4[2], vector4[3]).getBytes());
                        /*Constants urlPort = new Constants();
                        String hostUrl = urlPort.getHostUrl();
                        Integer port = 0;
                        if(seq_packet == 0){
                            port = urlPort.getPort();
                            seq_packet = 1;
                        } else if (seq_packet == 1) {
                            port = 12346;
                            seq_packet = 2;
                        } else if (seq_packet == 2) {
                            port = 12347;
                            seq_packet = 3;
                        } else if (seq_packet == 3) {
                            port = 12348;
                            seq_packet = 4;
                        } else if (seq_packet == 4) {
                            port = 12349;
                            seq_packet = 5;
                        }
                        else if (seq_packet == 5) {
                            port = 12350;
                            seq_packet = 6;
                        }
                        else if (seq_packet == 6) {
                            port = 12351;
                            seq_packet = 7;
                        }
                        else if (seq_packet == 7) {
                            port = 12352;
                            seq_packet = 8;
                        }
                        else if (seq_packet == 8) {
                            port = 12353;
                            seq_packet = 9;
                        }
                        else if (seq_packet == 9) {
                            port = 12354;
                            seq_packet = 0;
                        }*/
                        message = name + " " + mac + " " + last.getTimeInMillis() + " " + formatTimestamp(last) + " " + offset + " " + vector4[0] + " " + vector4[1] + " " + vector4[2] + " " + vector4[3];
//                      Client newClient = new Client(hostUrl,port, message);
//                      newClient.execute();

                        addNewData(message);
                        ArrayList<String> retData = getData();

                        if(retData.size() >= 100){
                            Gson gson = new Gson();
                            String json = gson.toJson(retData);
                            //MqttPublisher publisher = new MqttPublisher("tcp://192.168.0.231:1883", "AndroidClient");
                            MqttPublisher publisher = new MqttPublisher("tcp://195.130.118.252:1883", "AndroidClient");
                            publisher.connect();
                            publisher.publish("location/123", json, 2);
                            publisher.disconnect();
                            clearData();
                        }
                        break;
                    }
                    case "pressure":
                    case "relative-humidity":
                    case "illuminance":
                    case "temperature": {
                        last = data.timestamp();
                        if (start == null) {
                            first = last;
                            start = first.getTimeInMillis();
                        }

                        float offset = (last.getTimeInMillis() - start) / 1000.f;

                        fos.write(String.format(Locale.US, "%d,%s,%.3f,%.3f%n",
                                last.getTimeInMillis(), formatTimestamp(last), offset,
                                data.value(Float.class)).getBytes());
                        break;
                    }
                }
            } catch (IOException ignored) {
            }
        }

        @Override
        public void stop() {
            try {
                fos.close();
            } catch (IOException ignored) {
            }
        }

        public void setClient(Client newClient){
            this.newClient = newClient;
        }
        public String getMessage(){
            return message;
        }

        public void setName(String name){
            this.name = name;
        }
        public void setMac(String mac){
            this.mac = mac;
        }
    }
    class SampleCountDataHandler implements DataHandler {
        int samples;
        TextView sampleCountView;


        @Override
        public void init() {
            samples = 0;
        }

        @Override
        public void process(Data data) {
            samples++;
        }

        @Override
        public void stop() {

        }

        @Override
        public void setClient(Client newClient) {

        }

        @Override
        public String getMessage() {
            return getMessage();
        }

        @Override
        public void setName(String name) {

        }

        @Override
        public void setMac(String mac) {

        }
    }
}
