package com.example.springboot.mapper;

import com.example.springboot.entity.SysRepair;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface RepairMapper {
    @Select("<script>" +
            "SELECT " +
            "  r.id, r.title, r.description, r.status, " +
            "  r.user_id AS userId, " +
            "  r.dorm_id AS dormId, " +
            "  r.repairman_id AS repairmanId, " +
            "  r.create_time AS createTime, " +
            "  r.finish_time AS finishTime, " +
            "  d.zone_name AS zoneName, " +
            "  d.building_name AS buildingName, " +
            "  d.room_number AS roomNumber, " +
            "  su.real_name AS repairmanName, " +
            "  suser.real_name AS studentName " +
            "FROM sys_repair r " +
            "LEFT JOIN sys_dorm d ON r.dorm_id = d.id " +
            "LEFT JOIN sys_user su ON r.repairman_id = su.id " + // 维修工表
            "LEFT JOIN sys_user suser ON r.user_id = suser.id " + // 报修人表
            "<where>" +
            // 如果是学生，并且有 dormId，就查该 dormId 下的所有报修
            "<if test='dormId != null'> AND r.dorm_id = #{dormId} </if>" +
            // 其他情况（管理员/维修工），dormId 为 null，不进行这个过滤
            "</where>" +
            "ORDER BY r.id DESC" +
            "</script>")
    List<SysRepair> getList(@Param("dormId") Integer dormId);

    // 2. 新增报修
    @Insert("INSERT INTO sys_repair(user_id, dorm_id, title, description, status, create_time) " +
            "VALUES(#{userId}, #{dormId}, #{title}, #{description}, 0, NOW())")
    int insert(SysRepair repair);

    // 3. 删除报修
    @Delete("DELETE FROM sys_repair WHERE id = #{id}")
    int delete(Integer id);

    // 4. 接单 (维修工用)
    @Update("UPDATE sys_repair SET status = 1, repairman_id = #{repairmanId} WHERE id = #{id}")
    int takeOrder(Integer id, Integer repairmanId);

    // 5. 完成 (维修工用)
    @Update("UPDATE sys_repair SET status = 2, finish_time = NOW() WHERE id = #{id}")
    int finishOrder(Integer id);

    // 6. 管理员指派
    @Update("UPDATE sys_repair SET status = 1, repairman_id = #{repairmanId} WHERE id = #{id}")
    int assign(Integer id, Integer repairmanId);

    // 7. 撤回指派
    @Update("UPDATE sys_repair SET status = 0, repairman_id = NULL WHERE id = #{id}")
    int revokeAssignment(Integer id);

}