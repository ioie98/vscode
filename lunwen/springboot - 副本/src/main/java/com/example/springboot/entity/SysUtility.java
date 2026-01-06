package com.example.springboot.entity;

import lombok.Data;
import java.util.Date;

@Data
public class SysUtility {
    private Integer id;
    private Integer dormId;
    private String month;
    private Double waterUsage;
    private Double electricUsage;
    private Double waterCost;
    private Double electricCost;
    private Double totalCost;
    private Integer status; // 0-未缴, 1-已缴
    private Date createTime;

    // 辅助字段：用于展示宿舍名
    private String buildingName;
    private String roomNumber;
    private String zoneName;
}