package com.example.springboot.entity;

import lombok.Data;
import java.util.Date;

@Data
public class SysHoliday {
    private Integer id;
    private String studentId;
    private String name;
    private String major;
    private String className;
    private String phone;
    private String destination;
    private String location;
    private Date returnTime;
    private String dormName;
}