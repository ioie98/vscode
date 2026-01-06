package com.example.springboot.controller;

import com.example.springboot.entity.SysUtility;
import com.example.springboot.mapper.UtilityMapper;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 水电费管理控制器
 * 负责处理水电费账单的查询、发布、修改、缴费及删除功能。
 * 包含核心的费用自动计算逻辑。
 */
@RestController
@RequestMapping("/api/utility")
public class UtilityController {

    @Autowired
    private UtilityMapper utilityMapper;

    // ================== 计费标准常量 ==================
    /** 水费单价：3元/吨 */
    private static final double PRICE_WATER = 3.0;
    /** 电费单价：0.5元/度 */
    private static final double PRICE_ELECTRIC = 0.5;

    // ================== 1. 列表查询接口 ==================

    /**
     * 获取水电费账单列表 (支持分页)
     * 根据用户角色返回不同的数据范围：
     * - 学生(1): 只能查看自己所在宿舍的账单。
     * - 管理员(0)/维修工(2): 可以查看全校所有账单。
     *
     * @param role     当前用户角色
     * @param dormId   当前用户宿舍ID (学生必传)
     * @param pageNum  页码 (默认1)
     * @param pageSize 每页条数 (默认15)
     * @return 包含 total 和 list 的分页数据
     */
    @GetMapping("/list")
    public Map<String, Object> list(@RequestParam(required = false) Integer role,
                                    @RequestParam(required = false) Integer dormId,
                                    @RequestParam(defaultValue = "1") Integer pageNum,
                                    @RequestParam(defaultValue = "15") Integer pageSize) {
        // 1. 开启分页拦截
        PageHelper.startPage(pageNum, pageSize);

        List<SysUtility> list;

        // 2. 权限判断
        if (role != null && role == 1) {
            // === 学生视图 ===
            if (dormId == null) {
                // 如果学生未分配宿舍，返回空列表
                return success(getDataByPage(java.util.Collections.emptyList()));
            }
            // 查询本宿舍记录
            list = utilityMapper.getByDormId(dormId);
        } else {
            // === 管理员/维修工视图 ===
            // 查询所有记录
            list = utilityMapper.getAll();
        }

        // 3. 封装并返回分页结果
        return success(getDataByPage(list));
    }

    // ================== 2. 业务操作接口 ==================

    /**
     * 发布新账单
     * 管理员输入用量，后端自动计算费用并保存。
     */
    @PostMapping("/add")
    public Map<String, Object> add(@RequestBody SysUtility utility) {
        // 调用计费逻辑，确保金额准确
        calculateCosts(utility);
        utilityMapper.add(utility);
        return success("账单发布成功");
    }

    /**
     * 修改账单信息
     * 管理员修改用量后，后端重新计算费用并更新。
     */
    @PostMapping("/update")
    public Map<String, Object> update(@RequestBody SysUtility utility) {
        // 调用计费逻辑，重新计算总价
        calculateCosts(utility);
        utilityMapper.update(utility);
        return success("修改成功");
    }

    /**
     * 缴纳水电费
     * 学生点击缴费，将状态更新为“已缴费”。
     */
    @PostMapping("/pay")
    public Map<String, Object> pay(@RequestBody Map<String, Integer> params) {
        utilityMapper.pay(params.get("id"));
        return success("缴费成功");
    }

    /**
     * 删除账单记录
     * 管理员操作，物理删除数据库记录。
     */
    @PostMapping("/delete")
    public Map<String, Object> delete(@RequestBody Map<String, Integer> params) {
        utilityMapper.delete(params.get("id"));
        return success("删除成功");
    }

    // ================== 核心逻辑与辅助方法 ==================

    /**
     * 核心计费逻辑
     * 根据用水量和用电量，结合单价常量，计算水费、电费和总费用。
     * 避免前端计算可能产生的精度丢失或篡改风险。
     *
     * @param u 账单实体对象
     */
    private void calculateCosts(SysUtility u) {
        // 防止空指针，默认为 0.0
        double wUsage = u.getWaterUsage() != null ? u.getWaterUsage() : 0.0;
        double eUsage = u.getElectricUsage() != null ? u.getElectricUsage() : 0.0;

        // 计算费用
        double wCost = wUsage * PRICE_WATER;
        double eCost = eUsage * PRICE_ELECTRIC;

        // 设置回实体对象
        u.setWaterCost(wCost);
        u.setElectricCost(eCost);
        u.setTotalCost(wCost + eCost);
    }

    /**
     * 分页数据封装工具
     * 将 List 转换为前端需要的 {total, list} 格式
     */
    private Map<String, Object> getDataByPage(List<?> list) {
        PageInfo<?> pageInfo = new PageInfo<>(list);
        Map<String, Object> data = new HashMap<>();
        data.put("total", pageInfo.getTotal());
        data.put("list", pageInfo.getList());
        return data;
    }

    /**
     * 构建成功响应
     */
    private Map<String, Object> success(Object data) {
        Map<String, Object> map = new HashMap<>();
        map.put("code", 200);
        map.put("msg", "success");
        map.put("data", data);
        return map;
    }
}