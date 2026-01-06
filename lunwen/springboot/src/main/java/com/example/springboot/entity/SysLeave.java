package com.example.springboot.entity;

import lombok.Data;
import java.util.Date;

@Data
public class SysLeave {
    private Integer id;
    private Integer userId;
    private Integer type; // 1-离校, 2-返校/留校
    private String reason;
    private Date leaveTime;
    private Date returnTime;
    private Integer status; // 0-审核中, 1-通过
    private String studentName;
    private String dormName;
}