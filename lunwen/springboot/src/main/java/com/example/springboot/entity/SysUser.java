package com.example.springboot.entity;

import lombok.Data;

@Data // Lombok 自动生成 Get/Set 方法
public class SysUser {
    private Integer id;
    private String username;
    private String password;
    private String realName;
    private Integer role; // 0-管理员, 1-学生, 2-维修工
    private String phone;
    private Integer dormId;
    private String College;
    private String Major;
    private String className;
    private Integer bedNum;
}