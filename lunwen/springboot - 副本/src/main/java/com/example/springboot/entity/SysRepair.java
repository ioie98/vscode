package com.example.springboot.entity;

import lombok.Data;
import java.util.Date;

@Data
public class SysRepair {
    private Integer id;
    private Integer userId;       // 报修人ID
    private Integer dormId;       // 宿舍ID
    private Integer repairmanId;  // 维修工ID

    // 用于展示的字段
    private String repairmanName; // 维修工姓名
    private String studentName;   // 报修人姓名

    private String title;
    private String description;
    private Integer status;       // 0-待处理, 1-维修中, 2-已完成

    private Date createTime;
    private Date finishTime;

    // 辅助字段：用于前端展示楼栋和房号
    private String buildingName;
    private String roomNumber;
    private String zoneName;    // 园区名
}