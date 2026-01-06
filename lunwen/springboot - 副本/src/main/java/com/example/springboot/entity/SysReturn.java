package com.example.springboot.entity;

import lombok.Data;
import java.util.Date;

@Data
public class SysReturn {
    private Integer id;
    private String studentId;
    private String name;
    private String isDelayed; // 是否延迟
    private String reason;
    private Date returnTime;
    private String transport;
    private String transportNo;
    private String dormName;
}