package com.example.springboot.controller;

import com.example.springboot.entity.*;
import com.example.springboot.mapper.CommonMapper;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.ArrayList;

/**
 * 公共业务控制器
 * 处理离返校申请、卫生检查、节假日去向、留言板等通用业务逻辑。
 * 包含针对不同角色（管理员、学生、维修工）的权限过滤和数据展示逻辑。
 */
@RestController
@RequestMapping("/api/common")
public class CommonController {

    @Autowired
    private CommonMapper commonMapper;

    /**
     * 分页数据封装辅助方法
     * 将查询结果列表封装为前端需要的分页格式 {total: 总数, list: 当前页数据}
     *
     * @param list PageHelper 查询出的列表
     * @return 包含 total 和 list 的 Map
     */
    private Map<String, Object> getDataByPage(List<?> list) {
        PageInfo<?> pageInfo = new PageInfo<>(list);
        Map<String, Object> data = new HashMap<>();
        data.put("total", pageInfo.getTotal());
        data.put("list", pageInfo.getList());
        return data;
    }

    // =========================================================
    // 模块 1：离校/留校申请管理
    // =========================================================

    /**
     * 获取离校/留校申请列表
     * 根据用户角色返回不同的数据范围：
     * - 管理员(0): 查看全校申请
     * - 维修工(2): 查看维修工群体的申请
     * - 学生(1): 查看本宿舍的申请
     * - 其他: 查看个人申请
     */
    @GetMapping("/leave/list")
    public Map<String, Object> getLeaves(@RequestParam Integer userId,
                                         @RequestParam(required = false) Integer role,
                                         @RequestParam(required = false) Integer dormId,
                                         @RequestParam(defaultValue = "1") Integer pageNum,
                                         @RequestParam(defaultValue = "10") Integer pageSize) {
        // 1. 开启分页拦截
        PageHelper.startPage(pageNum, pageSize);

        // 2. 根据角色判断查询逻辑
        if (role != null) {
            // 管理员查看所有
            if (role == 0) return success(getDataByPage(commonMapper.getAllLeaves()));
            // 维修工只看维修工角色的记录
            if (role == 2) return success(getDataByPage(commonMapper.getLeavesByRole(2)));
            // 学生查看同宿舍记录（便于互相了解去向）
            if (role == 1 && dormId != null) return success(getDataByPage(commonMapper.getLeavesByDorm(dormId)));
        }
        // 默认情况（或无宿舍学生）：只看自己的记录
        return success(getDataByPage(commonMapper.getMyLeaves(userId)));
    }

    /**
     * 提交离校/留校申请
     */
    @PostMapping("/leave/add")
    public Map<String, Object> addLeave(@RequestBody SysLeave leave) {
        commonMapper.addLeave(leave);
        return success("申请提交成功");
    }

    /**
     * 审核申请 (管理员操作)
     * 修改申请的状态 (1-通过, 2-拒绝)
     */
    @PostMapping("/leave/audit")
    public Map<String, Object> auditLeave(@RequestBody Map<String, Integer> params) {
        commonMapper.updateLeaveStatus(params.get("id"), params.get("status"));
        return success("审核完成");
    }


    // =========================================================
    // 模块 2：卫生检查管理
    // =========================================================

    /**
     * 获取卫生检查记录
     * - 管理员/维修工: 查看全校记录
     * - 学生: 查看自己宿舍的记录
     */
    @GetMapping("/hygiene/list")
    public Map<String, Object> getHygieneList(@RequestParam(required = false) Integer dormId,
                                              @RequestParam(required = false) Integer role,
                                              @RequestParam(defaultValue = "1") Integer pageNum,
                                              @RequestParam(defaultValue = "10") Integer pageSize) {
        PageHelper.startPage(pageNum, pageSize);
        // 管理员和维修工查看所有
        if (role != null && (role == 0 || role == 2)) {
            return success(getDataByPage(commonMapper.getAllHygieneList()));
        }
        // 学生如果没有分配宿舍，看不到数据
        if (dormId == null) return success(getDataByPage(new ArrayList<>()));
        // 学生查看本宿舍记录
        return success(getDataByPage(commonMapper.getHygieneList(dormId)));
    }

    /**
     * 新增卫生检查记录 (管理员操作)
     */
    @PostMapping("/hygiene/add")
    public Map<String, Object> addHygiene(@RequestBody SysHygiene hygiene) {
        commonMapper.addHygieneRecord(hygiene);
        return success("添加成功");
    }


    // =========================================================
    // 模块 3：节假日去向统计
    // =========================================================

    /**
     * 获取节假日去向列表
     * - 维修工: 无此功能，返回空
     * - 学生: 查看本宿舍去向
     * - 管理员: 查看全校去向，支持按目的地筛选
     */
    @GetMapping("/holiday/list")
    public Map<String, Object> getHolidays(@RequestParam(required = false) String destination,
                                           @RequestParam(required = false) Integer role,
                                           @RequestParam(required = false) Integer dormId,
                                           @RequestParam(defaultValue = "1") Integer pageNum,
                                           @RequestParam(defaultValue = "10") Integer pageSize) {
        // 维修工(Role 2) 不需要此功能，直接返回空列表
        if (role != null && role == 2) return success(getDataByPage(new ArrayList<>()));

        // 处理筛选条件 "全部"
        if ("全部".equals(destination)) destination = null;

        Integer searchDormId = null;
        Integer targetRole = null;
        // 学生只能看本宿舍
        if (role != null) {
            if (role == 1) searchDormId = dormId;
        }

        PageHelper.startPage(pageNum, pageSize);
        return success(getDataByPage(commonMapper.getHolidays(destination, searchDormId, targetRole)));
    }

    /**
     * 登记节假日去向 (学生操作)
     */
    @PostMapping("/holiday/add")
    public Map<String, Object> addHoliday(@RequestBody SysHoliday holiday) {
        commonMapper.addHoliday(holiday);
        return success("登记成功");
    }


    // =========================================================
    // 模块 4：返校管理
    // =========================================================

    /**
     * 获取返校登记列表
     * 用于管理员查看学生返校情况统计
     */
    @GetMapping("/return/list")
    public Map<String, Object> getReturns(@RequestParam(defaultValue = "1") Integer pageNum,
                                          @RequestParam(defaultValue = "10") Integer pageSize) {
        PageHelper.startPage(pageNum, pageSize);
        return success(getDataByPage(commonMapper.getReturns()));
    }

    /**
     * 学生提交返校信息
     */
    @PostMapping("/return/add")
    public Map<String, Object> addReturn(@RequestBody SysReturn sysReturn) {
        commonMapper.addReturn(sysReturn);
        return success("登记成功");
    }


    // =========================================================
    // 模块 5：留言板功能
    // =========================================================

    /**
     * 获取留言列表 (按时间倒序)
     */
    @GetMapping("/message/list")
    public Map<String, Object> getMessages(@RequestParam(defaultValue = "1") Integer pageNum,
                                           @RequestParam(defaultValue = "10") Integer pageSize) {
        PageHelper.startPage(pageNum, pageSize);
        return success(getDataByPage(commonMapper.getMessages()));
    }

    /**
     * 发布新留言
     */
    @PostMapping("/message/add")
    public Map<String, Object> addMessage(@RequestBody SysMessage message) {
        commonMapper.addMessage(message);
        return success("发布成功");
    }


    // =========================================================
    // 模块 6：个人设置
    // =========================================================

    /**
     * 修改密码
     * 校验原密码是否正确，如果正确则更新新密码
     */
    @PostMapping("/update-password")
    public Map<String, Object> updatePassword(@RequestBody Map<String, Object> params) {
        int row = commonMapper.updatePassword((Integer)params.get("id"), (String)params.get("oldPwd"), (String)params.get("newPwd"));
        return row > 0 ? success("修改成功") : error("原密码错误");
    }

    // ================== 通用响应辅助方法 ==================

    /**
     * 返回成功响应结果
     * @param data 返回的数据对象
     */
    private Map<String, Object> success(Object data) {
        Map<String, Object> map = new HashMap<>();
        map.put("code", 200);
        map.put("msg", "success");
        map.put("data", data);
        return map;
    }

    /**
     * 返回失败/错误响应结果
     * @param msg 错误信息描述
     */
    private Map<String, Object> error(String msg) {
        Map<String, Object> map = new HashMap<>();
        map.put("code", 500);
        map.put("msg", msg);
        return map;
    }
}