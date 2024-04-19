package com.example.myapplication;

import java.util.ArrayList;
import org.apache.commons.math3.analysis.interpolation.LinearInterpolator;
import org.apache.commons.math3.analysis.polynomials.PolynomialSplineFunction;

public class Database {

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
