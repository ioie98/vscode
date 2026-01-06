package com.example.springboot.controller;

import com.example.springboot.entity.SysUser;
import com.example.springboot.mapper.UserMapper;
import com.example.springboot.service.UserService;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 登录与基础查询控制器
 * 处理用户认证（登录）以及首页核心的宿舍列表查询功能。
 */
@RestController
@RequestMapping("/api")
public class LoginController {

    @Autowired
    private UserService userService;

    @Autowired
    private UserMapper userMapper;

    // ================== 1. 登录模块 ==================

    /**
     * 用户登录接口
     * 接收前端传入的账号、密码和角色，进行身份验证。
     *
     * @param loginForm 包含 username, password, role 的登录表单对象
     * @return 登录成功返回用户信息和 Token（此处简化为用户信息），失败返回错误提示
     */
    @PostMapping("/login")
    public Map<String, Object> login(@RequestBody SysUser loginForm) {
        try {
            // 1. 调用 Service 层进行账号密码验证
            SysUser user = userService.login(loginForm.getUsername(), loginForm.getPassword());

            if (user != null) {
                // 2. 校验角色一致性
                // 防止用户在前端选择"管理员"角色，却使用"学生"账号登录的情况
                if (loginForm.getRole() != null && !loginForm.getRole().equals(user.getRole())) {
                    Map<String, Object> map = new HashMap<>();
                    map.put("code", 400);
                    map.put("msg", "角色选择错误，请确认您的身份");
                    return map;
                }

                // 3. 登录成功，返回用户信息
                return success(user);
            } else {
                // 4. 账号或密码错误
                Map<String, Object> map = new HashMap<>();
                map.put("code", 400);
                map.put("msg", "用户名或密码错误");
                return map;
            }
        } catch (Exception e) {
            e.printStackTrace();
            return error("系统错误: " + e.getMessage());
        }
    }

    // ================== 2. 宿舍列表查询模块 ==================

    /**
     * 获取宿舍/床位列表接口 (支持分页)
     * 根据当前登录用户的角色，返回不同的数据视图：
     * - 管理员：查看全校所有住宿学生的分布列表。
     * - 学生：查看自己所在宿舍的室友列表。
     *
     * @param dormId   宿舍ID (学生查询时必须)
     * @param role     当前用户角色 (0-管理员, 1-学生)
     * @param pageNum  当前页码 (默认1)
     * @param pageSize 每页条数 (默认10)
     * @return 包含 total(总数) 和 list(数据列表) 的 Map 对象
     */
    @GetMapping("/my-dorm/list")
    public Map<String, Object> getMyDormList(@RequestParam(required = false) Integer dormId,
                                             @RequestParam(required = false) Integer role,
                                             @RequestParam(defaultValue = "1") Integer pageNum,  // 分页参数
                                             @RequestParam(defaultValue = "10") Integer pageSize // 分页参数
    ) {
        try {
            // 1. 开启分页拦截器
            // PageHelper 会自动拦截紧随其后的 SQL 查询，并注入 Limit 语句
            PageHelper.startPage(pageNum, pageSize);

            List<Map<String, Object>> list;

            // 2. 根据角色判断查询逻辑
            if (role != null && role == 0) {
                // === 管理员视图 ===
                // 查询全校所有已分配宿舍的学生列表
                list = userMapper.getAllStudentDorms();
            } else {
                // === 学生视图 ===
                if (dormId == null) {
                    // 如果学生尚未分配宿舍，直接返回空列表，避免执行无效 SQL
                    Map<String, Object> emptyData = new HashMap<>();
                    emptyData.put("total", 0);
                    emptyData.put("list", Collections.emptyList());
                    return success(emptyData);
                }
                // 查询该宿舍内的所有成员信息（室友）
                list = userMapper.getRoommates(dormId);
            }

            // 3. 封装分页结果
            // PageInfo 对象包含了总记录数(total)、总页数等元数据
            PageInfo<Map<String, Object>> pageInfo = new PageInfo<>(list);

            // 4. 构造前端约定的响应格式 { "total": 100, "list": [...] }
            Map<String, Object> data = new HashMap<>();
            data.put("total", pageInfo.getTotal());
            data.put("list", pageInfo.getList());

            return success(data);

        } catch (Exception e) {
            e.printStackTrace();
            return error("查询出错: " + e.getMessage());
        }
    }

    // ================== 3. 通用响应方法 ==================

    /**
     * 构造成功响应
     * @param data 返回的数据主体
     */
    private Map<String, Object> success(Object data) {
        Map<String, Object> map = new HashMap<>();
        map.put("code", 200);       // 状态码 200 表示成功
        map.put("msg", "success");  // 提示信息
        map.put("data", data);      // 数据载荷
        return map;
    }

    /**
     * 构造失败响应
     * @param msg 错误提示信息
     */
    private Map<String, Object> error(String msg) {
        Map<String, Object> map = new HashMap<>();
        map.put("code", 500);       // 状态码 500 表示服务器错误/业务异常
        map.put("msg", msg);
        return map;
    }
}