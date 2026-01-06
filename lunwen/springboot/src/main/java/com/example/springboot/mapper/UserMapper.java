package com.example.springboot.mapper;

import com.example.springboot.entity.SysUser;
import com.example.springboot.entity.SysDorm;
import org.apache.ibatis.annotations.*;
import java.util.List;
import java.util.Map;

@Mapper
public interface UserMapper {

    // ================== 1. 登录查询 ==================
    @Select("SELECT id, username, password, role, phone, create_time, " +
            "real_name AS realName, dorm_id AS dormId, bed_num AS bedNum, " +
            "college, major, class_name AS className " +
            "FROM sys_user WHERE username = #{username}")
    SysUser getByUsername(String username);

    // ================== 2. 我的宿舍查询 (学生看自己宿舍) ==================
    @Select("SELECT u.id, u.username, u.role, u.college, u.major, " +
            "u.real_name AS realName, u.bed_num AS bedNum, u.class_name AS className, " +
            "d.building_name AS buildingName, d.room_number AS roomNumber, d.zone_name AS zoneName " +
            "FROM sys_user u LEFT JOIN sys_dorm d ON u.dorm_id = d.id " +
            "WHERE u.dorm_id = #{dormId}")
    List<Map<String, Object>> getRoommates(Integer dormId);

    // ================== 3. 管理员查询所有学生的宿舍信息 (我的宿舍页面) ==================
    @Select("SELECT u.id, u.username, u.role, u.college, u.major, " +
            "u.real_name AS realName, u.bed_num AS bedNum, u.class_name AS className, " +
            "d.building_name AS buildingName, d.room_number AS roomNumber, d.zone_name AS zoneName " +
            "FROM sys_user u LEFT JOIN sys_dorm d ON u.dorm_id = d.id " +
            "WHERE u.role = 1 ORDER BY d.building_name, d.room_number, u.bed_num")
    List<Map<String, Object>> getAllStudentDorms();

    // ================== 4. 用户管理 - 列表查询 ==================
    @Select("<script>" +
            "SELECT " +
            "  u.id, " +
            "  u.username, " +
            "  u.real_name AS realName, " +
            "  u.role, " +
            "  u.phone, " +
            "  u.college, " +
            "  u.major, " +
            "  u.class_name AS className, " +
            "  d.building_name AS buildingName, " +
            "  d.room_number AS roomNumber, " +
            "  d.zone_name AS zoneName " +
            "FROM sys_user u " +
            "LEFT JOIN sys_dorm d ON u.dorm_id = d.id " +
            "<where>" +
            "<if test='role != null'> AND u.role = #{role} </if>" +
            "</where>" +
            "ORDER BY u.role ASC, u.id DESC" +
            "</script>")
    List<Map<String, Object>> getAllUsers(@Param("role") Integer role);

    // ================== 5. 指派维修工 ==================
    @Select("SELECT id, real_name AS realName, phone, username FROM sys_user WHERE role = 2")
    List<SysUser> getAllRepairmen();

    // ================== 6. 新增/删除/更新用户 ==================
    @Insert("INSERT INTO sys_user(username, password, real_name, role, phone, dorm_id, bed_num, college, major, class_name) " +
            "VALUES(#{username}, '123456', #{realName}, #{role}, #{phone}, #{dormId}, #{bedNum}, #{college}, #{major}, #{className})")
    int insert(SysUser user);

    @Delete("DELETE FROM sys_user WHERE id = #{id}")
    int delete(Integer id);

    @Update("UPDATE sys_user SET " +
            "real_name = #{realName}, " +
            "phone = #{phone}, " +
            "role = #{role}, " +
            "dorm_id = #{dormId}, " +
            "bed_num = #{bedNum}, " +
            "college = #{college}, " +
            "major = #{major}, " +
            "class_name = #{className} " +
            "WHERE id = #{id}")
    int update(SysUser user);

    //  7. 宿舍辅助查询

    @Select("SELECT id FROM sys_dorm WHERE zone_name = #{zoneName} AND building_name = #{buildingName} AND room_number = #{roomNumber} LIMIT 1")
    Integer findDormId(String zoneName, String buildingName, String roomNumber);

    @Insert("INSERT INTO sys_dorm(zone_name, building_name, room_number, capacity) VALUES(#{zoneName}, #{buildingName}, #{roomNumber}, 4)")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int createDorm(SysDorm dorm);

    // 获取所有宿舍列表 (给水电费发布、卫生检查下拉框用)
    @Select("SELECT id, zone_name AS zoneName, building_name AS buildingName, room_number AS roomNumber, capacity FROM sys_dorm ORDER BY zone_name, building_name, room_number")
    List<SysDorm> getAllDorms();

    //  8. 宿舍容量校验

    // 查询宿舍容量
    @Select("SELECT capacity FROM sys_dorm WHERE id = #{dormId}")
    Integer getDormCapacity(Integer dormId);

    // 统计宿舍当前人数
    @Select("SELECT count(*) FROM sys_user WHERE dorm_id = #{dormId}")
    int countDormUsage(Integer dormId);

    // 检查特定床位是否有人
    @Select("SELECT count(*) FROM sys_user WHERE dorm_id = #{dormId} AND bed_num = #{bedNum}")
    int checkBedOccupied(Integer dormId, Integer bedNum);
}