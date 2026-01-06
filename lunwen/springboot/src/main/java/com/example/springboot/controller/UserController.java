package com.example.springboot.controller;

import com.example.springboot.entity.SysUser;
import com.example.springboot.entity.SysDorm;
import com.example.springboot.mapper.UserMapper;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 用户管理控制器
 * 负责处理用户列表查询、注册、新增、编辑、删除等操作。
 * 包含复杂的宿舍分配和满员校验逻辑。
 */
@RestController
@RequestMapping("/api/user")
public class UserController {

    @Autowired
    private UserMapper userMapper;

    // ============================================================
    // 1. 获取用户列表
    // ============================================================
    /**
     * 分页查询用户列表接口 (支持按角色筛选)
     * 管理员使用此接口进行人员管理。
     *
     * @param pageNum  当前页码 (默认1)
     * @param pageSize 每页条数 (默认10)
     * @param role     角色筛选条件 (0-管理员, 1-学生, 2-维修工, 不传则查所有)
     * @return 包含 total(总数) 和 list(用户列表) 的数据
     */
    @GetMapping("/list")
    public Map<String, Object> list(@RequestParam(defaultValue = "1") Integer pageNum,
                                    @RequestParam(defaultValue = "10") Integer pageSize,
                                    @RequestParam(required = false) Integer role) {
        // 1. 开启分页拦截器
        PageHelper.startPage(pageNum, pageSize);

        // 2. 调用 Mapper 查询数据库 (动态 SQL 支持 role 筛选)
        List<Map<String, Object>> list = userMapper.getAllUsers(role);

        // 3. 封装分页信息 (自动计算总条数)
        PageInfo<Map<String, Object>> pageInfo = new PageInfo<>(list);

        Map<String, Object> data = new HashMap<>();
        data.put("total", pageInfo.getTotal());
        data.put("list", pageInfo.getList());

        return success(data);
    }

    /**
     * 获取所有维修工列表
     * 用于"报修管理"页面管理员指派维修工时的下拉框选项。
     */
    @GetMapping("/repairmen")
    public Map<String, Object> getRepairmen() {
        List<SysUser> list = userMapper.getAllRepairmen();
        return success(list);
    }

    /**
     * 注册接口
     * 开放给未登录用户使用，逻辑直接复用 add 方法。
     */
    @PostMapping("/register")
    public Map<String, Object> register(@RequestBody Map<String, Object> params) {
        return add(params);
    }


    /**
     * 添加用户接口 (核心逻辑)
     * 包含：
     * 1. 基本信息提取
     * 2. 床位号类型安全转换
     * 3. 宿舍分配逻辑 (查询是否存在 -> 自动创建 -> 满员校验 -> 床位冲突校验)
     * 4. 插入数据库
     */
    @PostMapping("/add")
    public Map<String, Object> add(@RequestBody Map<String, Object> params) {
        try {
            // 1. 提取基本信息
            SysUser user = new SysUser();
            user.setUsername((String) params.get("username"));
            user.setRealName((String) params.get("realName"));
            user.setRole((Integer) params.get("role"));
            user.setPhone((String) params.get("phone"));
            user.setCollege((String) params.get("college"));
            user.setMajor((String) params.get("major"));
            user.setClassName((String) params.get("className"));

            // 2. bedNum 健壮性处理 (防止前端传空字符串导致 Integer 转换报错)
            Object bedNumObj = params.get("bedNum");
            if (bedNumObj != null && !bedNumObj.toString().trim().isEmpty()) {
                try {
                    user.setBedNum(Integer.parseInt(bedNumObj.toString().trim()));
                } catch (NumberFormatException e) {
                    user.setBedNum(null); // 如果不是数字，置为 null
                }
            } else {
                user.setBedNum(null);
            }

            // 3. 学生宿舍逻辑处理
            if (user.getRole() == 1) {
                String zoneName = (String) params.get("zoneName");
                String buildingName = (String) params.get("buildingName");
                String roomNumber = (String) params.get("roomNumber");

                // 只有当宿舍三要素都填写了，才进行分配逻辑
                if (zoneName != null && !zoneName.trim().isEmpty() &&
                        buildingName != null && !buildingName.trim().isEmpty() &&
                        roomNumber != null && !roomNumber.trim().isEmpty()) {

                    // A. 查询宿舍是否存在
                    Integer dormId = userMapper.findDormId(zoneName, buildingName, roomNumber);

                    if (dormId == null) {
                        // B. 宿舍不存在 -> 自动创建新宿舍
                        SysDorm newDorm = new SysDorm();
                        newDorm.setZoneName(zoneName);
                        newDorm.setBuildingName(buildingName);
                        newDorm.setRoomNumber(roomNumber);
                        // capacity 在 SQL 中默认为 4
                        userMapper.createDorm(newDorm);
                        dormId = newDorm.getId(); // 获取自增ID
                    } else {
                        // C. 宿舍存在 -> 进行满员校验
                        Integer capacity = userMapper.getDormCapacity(dormId);
                        int used = userMapper.countDormUsage(dormId);

                        // 校验1: 宿舍是否已满
                        if (capacity != null && used >= capacity) {
                            return error("注册失败：该宿舍 (" + roomNumber + ") 已满员 (" + used + "/" + capacity + ")");
                        }

                        // 校验2: 目标床位是否冲突
                        if (user.getBedNum() != null) {
                            int isBedTaken = userMapper.checkBedOccupied(dormId, user.getBedNum());
                            if (isBedTaken > 0) {
                                return error("注册失败：该宿舍的 " + user.getBedNum() + " 号床位已被占用");
                            }
                        }
                    }
                    user.setDormId(dormId);
                } else {
                    user.setDormId(null); // 信息不全不分配
                }
            }

            // 4. 插入用户数据
            userMapper.insert(user);
            return success("添加成功，默认密码 123456");

        } catch (DuplicateKeyException e) {
            e.printStackTrace();
            // 捕获唯一索引冲突 (username 重复)
            return error("添加失败：该账号已存在，请更换一个账号");
        } catch (Exception e) {
            e.printStackTrace();
            return error("添加失败: " + e.getMessage());
        }
    }


    /**
     * 更新用户信息接口
     * 逻辑与 add 类似，但调用 update SQL。
     * 也包含宿舍自动关联逻辑，但暂未加入严格的满员校验(假设管理员知道自己在做什么)。
     */
    @PostMapping("/update")
    public Map<String, Object> update(@RequestBody Map<String, Object> params) {
        try {
            SysUser user = new SysUser();
            user.setId((Integer) params.get("id"));
            user.setUsername((String) params.get("username"));
            user.setRealName((String) params.get("realName"));
            user.setRole((Integer) params.get("role"));
            user.setPhone((String) params.get("phone"));
            user.setCollege((String) params.get("college"));
            user.setMajor((String) params.get("major"));
            user.setClassName((String) params.get("className"));

            // 处理床位号
            Object bedNumObj = params.get("bedNum");
            if (bedNumObj != null && !bedNumObj.toString().trim().isEmpty()) {
                try {
                    user.setBedNum(Integer.parseInt(bedNumObj.toString().trim()));
                } catch (NumberFormatException e) {
                    user.setBedNum(null);
                }
            } else {
                user.setBedNum(null);
            }

            // 处理宿舍关联
            if (user.getRole() == 1) {
                String zoneName = (String) params.get("zoneName");
                String buildingName = (String) params.get("buildingName");
                String roomNumber = (String) params.get("roomNumber");

                if (zoneName != null && buildingName != null && roomNumber != null) {
                    Integer dormId = userMapper.findDormId(zoneName, buildingName, roomNumber);
                    if (dormId == null) {
                        SysDorm newDorm = new SysDorm();
                        newDorm.setZoneName(zoneName);
                        newDorm.setBuildingName(buildingName);
                        newDorm.setRoomNumber(roomNumber);
                        userMapper.createDorm(newDorm);
                        dormId = newDorm.getId();
                    }
                    user.setDormId(dormId);
                }
            } else {
                user.setDormId(null);
                user.setBedNum(null);
            }

            userMapper.update(user);
            return success("修改成功");
        } catch (Exception e) {
            e.printStackTrace();
            return error("修改失败: " + e.getMessage());
        }
    }

    /**
     * 删除用户接口
     */
    @PostMapping("/delete")
    public Map<String, Object> delete(@RequestBody Map<String, Integer> params) {
        userMapper.delete(params.get("id"));
        return success("删除成功");
    }

    // ================== 辅助方法 ==================

    private Map<String, Object> success(Object data) {
        Map<String, Object> map = new HashMap<>();
        map.put("code", 200);
        map.put("msg", "success");
        map.put("data", data);
        return map;
    }
    private Map<String, Object> error(String msg) {
        Map<String, Object> map = new HashMap<>();
        map.put("code", 500);
        map.put("msg", msg);
        return map;
    }
}