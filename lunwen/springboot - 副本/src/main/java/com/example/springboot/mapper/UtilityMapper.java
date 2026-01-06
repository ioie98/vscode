package com.example.springboot.mapper;

import com.example.springboot.entity.SysUtility;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface UtilityMapper {

    // =========================================================
    // 1. 管理员查所有
    // =========================================================
    @Select("SELECT " +
            "  u.id, " +
            "  u.dorm_id AS dormId, " +
            "  u.month, " +
            "  u.water_usage AS waterUsage, " +
            "  u.electric_usage AS electricUsage, " +
            "  u.water_cost AS waterCost, " +
            "  u.electric_cost AS electricCost, " +
            "  u.total_cost AS totalCost, " +
            "  u.status, " +
            "  u.create_time AS createTime, " +
            "  d.building_name AS buildingName, " +
            "  d.room_number AS roomNumber, " +
            "  d.zone_name AS zoneName " +
            "FROM sys_utility u " +
            "LEFT JOIN sys_dorm d ON u.dorm_id = d.id " +
            "ORDER BY u.status ASC, u.month DESC")
    List<SysUtility> getAll();

    // =========================================================
    // 2. 学生查自己宿舍
    // =========================================================
    @Select("SELECT " +
            "  u.id, " +
            "  u.dorm_id AS dormId, " +
            "  u.month, " +
            "  u.water_usage AS waterUsage, " +
            "  u.electric_usage AS electricUsage, " +
            "  u.water_cost AS waterCost, " +
            "  u.electric_cost AS electricCost, " +
            "  u.total_cost AS totalCost, " +
            "  u.status, " +
            "  u.create_time AS createTime, " +
            "  d.building_name AS buildingName, " +
            "  d.room_number AS roomNumber, " +
            "  d.zone_name AS zoneName " +
            "FROM sys_utility u " +
            "LEFT JOIN sys_dorm d ON u.dorm_id = d.id " +
            "WHERE u.dorm_id = #{dormId} " +
            "ORDER BY u.month DESC")
    List<SysUtility> getByDormId(Integer dormId);

    // 3. 新增账单
    @Insert("INSERT INTO sys_utility(dorm_id, month, water_usage, electric_usage, water_cost, electric_cost, total_cost, status) " +
            "VALUES(#{dormId}, #{month}, #{waterUsage}, #{electricUsage}, #{waterCost}, #{electricCost}, #{totalCost}, 0)")
    int add(SysUtility utility);

    // 4. 缴费
    @Update("UPDATE sys_utility SET status = 1 WHERE id = #{id}")
    int pay(Integer id);

    // 5. 更新水电费记录
    @Update("UPDATE sys_utility SET " +
            "dorm_id = #{dormId}, " +
            "month = #{month}, " +
            "water_usage = #{waterUsage}, " +
            "electric_usage = #{electricUsage}, " +
            "water_cost = #{waterCost}, " +
            "electric_cost = #{electricCost}, " +
            "total_cost = #{totalCost} " +
            "WHERE id = #{id}")
    int update(SysUtility utility);

    // 6. 删除水电费记录
    @Delete("DELETE FROM sys_utility WHERE id = #{id}")
    int delete(Integer id);
}