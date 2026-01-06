package com.example.springboot.controller;

import com.example.springboot.entity.SysRepair;
import com.example.springboot.mapper.RepairMapper;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 报修管理控制器
 * 处理与报修单相关的 HTTP 请求，包括查询、新增、删除、接单、派单等操作。
 */
@RestController
@RequestMapping("/api/repair")
public class RepairController {

    @Autowired
    private RepairMapper repairMapper;

    /**
     * 获取报修列表 (支持分页和权限过滤)
     *
     * @param role     当前登录用户的角色 (0-管理员, 1-学生, 2-维修工)
     * @param dormId   当前登录用户的宿舍ID (学生专用)
     * @param pageNum  当前页码 (默认1)
     * @param pageSize 每页显示数量 (默认10)
     * @return 包含总条数(total)和当前页数据列表(list)的 Map
     */
    @GetMapping("/list")
    public Map<String, Object> list(@RequestParam(required = false) Integer role,
                                    @RequestParam(required = false) Integer dormId,
                                    @RequestParam(defaultValue = "1") Integer pageNum,
                                    @RequestParam(defaultValue = "10") Integer pageSize) {
        // 1. 使用 PageHelper 开启分页拦截
        PageHelper.startPage(pageNum, pageSize);

        // 2. 根据角色判断查询范围
        Integer searchDormId = null;
        // 如果是学生 (Role=1)，只查询本宿舍的报修记录
        if (role != null && role == 1) {
            searchDormId = dormId;
        }
        // 如果是管理员(0)或维修工(2)，searchDormId 为 null，Mapper 中会查询所有记录

        // 3. 执行数据库查询
        List<SysRepair> list = repairMapper.getList(searchDormId);

        // 4. 封装分页信息 (自动计算总数等)
        PageInfo<SysRepair> pageInfo = new PageInfo<>(list);

        // 5. 构建返回结果
        Map<String, Object> data = new HashMap<>();
        data.put("total", pageInfo.getTotal());
        data.put("list", pageInfo.getList());
        return success(data);
    }

    /**
     * 提交新的报修申请
     *
     * @param repair 报修实体类 (包含标题、描述、用户ID等)
     * @return 操作结果
     */    public Map<String, Object> add(@RequestBody SysRepair repair) {
        // 校验：如果学生没有分配宿舍，不允许报修
        if (repair.getDormId() == null) {
            return error("您未分配宿舍，无法报修");
        }
        repairMapper.insert(repair);
        return success("报修成功");
    }

    /**
     * 删除报修记录
     * 通常由管理员操作，或学生撤销自己的待处理申请
     *
     * @param params 包含 id 的 JSON 对象
     * @return 操作结果
     */
    @PostMapping("/delete")
    public Map<String, Object> delete(@RequestBody Map<String, Integer> params) {
        repairMapper.delete(params.get("id"));
        return success("删除成功");
    }

    /**
     * 维修工接单
     * 将状态更新为 1 (维修中)，并绑定维修工ID
     *
     * @param params 包含 id (报修单ID) 和 repairmanId (维修工ID)
     * @return 操作结果
     */
    @PostMapping("/take")
    public Map<String, Object> take(@RequestBody Map<String, Integer> params) {
        repairMapper.takeOrder(params.get("id"), params.get("repairmanId"));
        return success("接单成功");
    }

    /**
     * 完成维修
     * 将状态更新为 2 (已完成)，并记录完成时间
     *
     * @param params 包含 id (报修单ID)
     * @return 操作结果
     */
    @PostMapping("/finish")
    public Map<String, Object> finish(@RequestBody Map<String, Integer> params) {
        repairMapper.finishOrder(params.get("id"));
        return success("维修完成");
    }

    /**
     * 管理员指派维修工
     * 本质上复用了接单的逻辑 (设置状态为维修中，并指定维修工)
     *
     * @param params 包含 id (报修单ID) 和 repairmanId (指派的维修工ID)
     * @return 操作结果
     */
    @PostMapping("/assign")
    public Map<String, Object> assign(@RequestBody Map<String, Integer> params) {
        repairMapper.takeOrder(params.get("id"), params.get("repairmanId"));
        return success("指派成功");
    }

    /**
     * 撤回指派
     * 将已指派或维修中的单子重置回“待处理”状态
     *
     * @param params 包含 id (报修单ID)
     * @return 操作结果
     */
    @PostMapping("/revoke")
    public Map<String, Object> revoke(@RequestBody Map<String, Integer> params) {
        repairMapper.revokeAssignment(params.get("id"));
        return success("已撤回，请重新指派");
    }

    // ================== 通用响应辅助方法 ==================

    /**
     * 返回成功响应
     */
    private Map<String, Object> success(Object data) {
        Map<String, Object> map = new HashMap<>();
        map.put("code", 200);
        map.put("msg", "success");
        map.put("data", data);
        return map;
    }

    /**
     * 返回失败响应
     */
    private Map<String, Object> error(String msg) {
        Map<String, Object> map = new HashMap<>();
        map.put("code", 500);
        map.put("msg", msg);
        return map;
    }
}