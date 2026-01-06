package com.example.springboot.service;

import com.example.springboot.entity.SysUser;
import com.example.springboot.mapper.UserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    @Autowired
    private UserMapper userMapper;

    public SysUser login(String username, String password) {
        SysUser user = userMapper.getByUsername(username);

        // 1. 判断用户是否存在
        if (user == null) {
            return null;
        }

        // 2. 校验密码 (这里演示用明文，实际建议加密)
        if (!user.getPassword().equals(password)) {
            return null;
        }

        // 登录成功，把密码清空，防止泄露给前端
        user.setPassword(null);
        return user;
    }
}