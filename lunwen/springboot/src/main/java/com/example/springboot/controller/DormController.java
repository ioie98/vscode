package com.example.springboot.controller;

import com.example.springboot.entity.SysDorm;
import com.example.springboot.mapper.UserMapper; // 复用 UserMapper 来查询宿舍
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/dorm")
public class DormController {

    @Autowired
    private UserMapper userMapper; // 可以复用 UserMapper

    @GetMapping("/list")
    public Map<String, Object> list() {
        List<SysDorm> dorms = userMapper.getAllDorms();
        return success(dorms);
    }

    private Map<String, Object> success(Object data) {
        Map<String, Object> map = new HashMap<>();
        map.put("code", 200);
        map.put("msg", "success");
        map.put("data", data);
        return map;
    }
}