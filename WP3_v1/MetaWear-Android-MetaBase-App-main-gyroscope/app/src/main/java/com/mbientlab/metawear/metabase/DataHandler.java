
package com.mbientlab.metawear.metabase;

import static com.mbientlab.metawear.metabase.database.addNewData;
import static com.mbientlab.metawear.metabase.database.clearData;
import static com.mbientlab.metawear.metabase.database.getData;
import android.widget.TextView;
import com.google.gson.Gson;
import com.mbientlab.metawear.Data;
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
//                        fos.write(String.format(Locale.US, "%d,%s,%.3f,%.3f,%.3f,%.3f%n",
//                                last.getTimeInMillis(), formatTimestamp(last), offset,
//                                vector[0], vector[1], vector[2]).getBytes());
                        message = name + " " + mac + " " + last.getTimeInMillis() + " " + formatTimestamp(last) + " " + offset + " " + vector[0] + " " + vector[1] + " " + vector[2];

                        addNewData(message);
                        ArrayList<String> retData = getData();

                        if(retData.size() >= 100){
                            Gson gson = new Gson();
                            String json = gson.toJson(retData);
                            //MqttPublisher publisher = new MqttPublisher("tcp://192.168.0.231:1883", "AndroidClient");  //nuc
                            MqttPublisher publisher = new MqttPublisher("tcp://195.251.196.168:1883", "AndroidClient");    //orthopedikh
                            //https://147.102.33.212/index.html

                            publisher.connect();
                            publisher.publish("location/123", json, 2);
                            publisher.disconnect();
                            clearData();
                        }
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
//                        fos.write(String.format(Locale.US, "%d,%s,%.3f,%.3f,%.3f,%.3f,%.3f%n",
//                                last.getTimeInMillis(), formatTimestamp(last), offset,
//                                vector4[0], vector4[1], vector4[2], vector4[3]).getBytes());

                        message = name + " " + mac + " " + last.getTimeInMillis() + " " + formatTimestamp(last) + " " + offset + " " + vector4[0] + " " + vector4[1] + " " + vector4[2] + " " + vector4[3];

                        addNewData(message);
                        ArrayList<String> retData = getData();

                        if(retData.size() >= 100){
                            Gson gson = new Gson();
                            String json = gson.toJson(retData);
                            //MqttPublisher publisher = new MqttPublisher("tcp://192.168.0.231:1883", "AndroidClient");  //nuc
                            MqttPublisher publisher = new MqttPublisher("tcp://195.251.196.168:1883", "AndroidClient");    //orthopedikh
                            //https://147.102.33.212/index.html

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
