package com.example.springboot.entity;
import lombok.Data;

@Data
public class SysDorm {
    private Integer id;
    private String zoneName;
    private String buildingName;
    private String roomNumber;
    private Integer capacity;
}