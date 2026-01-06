package com.example.springboot.entity;

import lombok.Data;
import java.util.Date;

@Data
public class SysMessage {
    private Integer id;
    private String title;
    private String content;
    private String author;
    private String color;
    private Date createTime;
}