package com.mbientlab.metawear.metabase;

import java.util.ArrayList;

public class database {

    public static ArrayList<String> data = new ArrayList<>();

    public static void addNewData(String newData){
        data.add(newData);
    }

    public static ArrayList<String> getData(){
        return data;
    }

    public static void clearData(){
        data.clear();
        data = new ArrayList<>();
    }
}
