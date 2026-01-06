package com.example.springboot.entity;

import lombok.Data;
import java.util.Date;

@Data
public class SysHygiene {
    private Integer id;
    private Integer dormId;
    private Double score;
    private String remark;
    private Date checkDate;
    private Date createTime;
    private String buildingName; // 楼栋
    private String roomNumber;   // 房号
    private String zoneName;
}