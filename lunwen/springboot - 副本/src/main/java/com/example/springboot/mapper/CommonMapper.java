package com.example.springboot.mapper;

import com.example.springboot.entity.*;
import org.apache.ibatis.annotations.*;
import java.util.List;

@Mapper
public interface CommonMapper {

    // =========================================================
    // 模块 1：离校/留校申请 (修复：手动指定别名，解决时间不显示问题)
    // =========================================================

    // 1.1 学生查自己的
    @Select("SELECT " +
            "  l.id, " +
            "  l.user_id AS userId, " +
            "  l.type, " +
            "  l.reason, " +
            "  l.leave_time AS leaveTime, " +     // 修复点
            "  l.return_time AS returnTime, " +   // 修复点
            "  l.status, " +
            "  u.real_name AS studentName, " +
            "  CONCAT(d.zone_name, ' ', d.building_name, ' ', d.room_number) AS dormName " +
            "FROM sys_leave l " +
            "LEFT JOIN sys_user u ON l.user_id = u.id " +
            "LEFT JOIN sys_dorm d ON u.dorm_id = d.id " +
            "WHERE l.user_id = #{userId} " +
            "ORDER BY l.id DESC")
    List<SysLeave> getMyLeaves(Integer userId);

    // 1.2 管理员查所有的
    @Select("SELECT " +
            "  l.id, " +
            "  l.user_id AS userId, " +
            "  l.type, " +
            "  l.reason, " +
            "  l.leave_time AS leaveTime, " +     // 修复点
            "  l.return_time AS returnTime, " +   // 修复点
            "  l.status, " +
            "  u.real_name AS studentName, " +
            "  CONCAT(d.zone_name, ' ', d.building_name, ' ', d.room_number) AS dormName " +
            "FROM sys_leave l " +
            "LEFT JOIN sys_user u ON l.user_id = u.id " +
            "LEFT JOIN sys_dorm d ON u.dorm_id = d.id " +
            "ORDER BY l.id DESC")
    List<SysLeave> getAllLeaves();

    // 1.3 维修工查特定角色的
    @Select("SELECT " +
            "  l.id, " +
            "  l.user_id AS userId, " +
            "  l.type, " +
            "  l.reason, " +
            "  l.leave_time AS leaveTime, " +     // 修复点
            "  l.return_time AS returnTime, " +   // 修复点
            "  l.status, " +
            "  l.status, " +
            "  u.real_name AS studentName, " +
            "  CONCAT(d.zone_name, ' ', d.building_name, ' ', d.room_number) AS dormName " +
            "FROM sys_leave l " +
            "LEFT JOIN sys_user u ON l.user_id = u.id " +
            "LEFT JOIN sys_dorm d ON u.dorm_id = d.id " +
            "WHERE u.role = #{targetRole} " +
            "ORDER BY l.id DESC")
    List<SysLeave> getLeavesByRole(Integer targetRole);

    // 1.4 学生查同宿舍的
    @Select("SELECT " +
            "  l.id, " +
            "  l.user_id AS userId, " +
            "  l.type, " +
            "  l.reason, " +
            "  l.leave_time AS leaveTime, " +     // 修复点
            "  l.return_time AS returnTime, " +   // 修复点
            "  l.status, " +
            "  u.real_name AS studentName, " +
            "  CONCAT(d.zone_name, ' ', d.building_name, ' ', d.room_number) AS dormName " +
            "FROM sys_leave l " +
            "LEFT JOIN sys_user u ON l.user_id = u.id " +
            "LEFT JOIN sys_dorm d ON u.dorm_id = d.id " +
            "WHERE u.dorm_id = #{dormId} " +
            "ORDER BY l.id DESC")
    List<SysLeave> getLeavesByDorm(Integer dormId);

    @Insert("INSERT INTO sys_leave(user_id, type, reason, leave_time, return_time, status) " +
            "VALUES(#{userId}, #{type}, #{reason}, #{leaveTime}, #{returnTime}, 0)")
    int addLeave(SysLeave leave);

    @Update("UPDATE sys_leave SET status = #{status} WHERE id = #{id}")
    int updateLeaveStatus(@Param("id") Integer id, @Param("status") Integer status);


    // =========================================================
    // 模块 2：卫生检查
    // =========================================================
    @Select("SELECT id, dorm_id AS dormId, score, remark, check_date AS checkDate, create_time AS createTime FROM sys_hygiene WHERE dorm_id = #{dormId} ORDER BY check_date DESC")
    List<SysHygiene> getHygieneList(Integer dormId);

    @Select("SELECT h.id, h.score, h.remark, h.check_date AS checkDate, h.create_time AS createTime, d.building_name AS buildingName, d.room_number AS roomNumber, d.zone_name AS zoneName FROM sys_hygiene h LEFT JOIN sys_dorm d ON h.dorm_id = d.id ORDER BY h.check_date DESC")
    List<SysHygiene> getAllHygieneList();

    @Insert("INSERT INTO sys_hygiene(dorm_id, score, remark, check_date) VALUES(#{dormId}, #{score}, #{remark}, #{checkDate})")
    int addHygieneRecord(SysHygiene hygiene);


    // =========================================================
    // 模块 3：节假日去向
    // =========================================================
    @Select("<script>" +
            "SELECT " +
            "  h.id, " +
            "  h.student_id AS studentId, " +
            "  h.name, " +
            "  h.major, " +
            "  h.class_name AS className, " +
            "  h.phone, " +
            "  h.destination, " +
            "  h.location, " +
            "  h.return_time AS returnTime, " + // 修复点
            "  CONCAT(d.zone_name, ' ', d.building_name, ' ', d.room_number) AS dormName " +
            "FROM sys_holiday h " +
            "LEFT JOIN sys_user u ON h.student_id = u.username " +
            "LEFT JOIN sys_dorm d ON u.dorm_id = d.id " +
            "<where>" +
            "<if test='destination != null and destination != \"\"'> AND h.destination = #{destination} </if>" +
            "<if test='dormId != null'> AND u.dorm_id = #{dormId} </if>" +
            "<if test='targetRole != null'> AND u.role = #{targetRole} </if>" +
            "</where>" +
            "</script>")
    List<SysHoliday> getHolidays(@Param("destination") String destination,
                                 @Param("dormId") Integer dormId,
                                 @Param("targetRole") Integer targetRole);

    @Insert("INSERT INTO sys_holiday(student_id, name, major, class_name, phone, destination, location, return_time) " +
            "VALUES(#{studentId}, #{name}, #{major}, #{className}, #{phone}, #{destination}, #{location}, #{returnTime})")
    int addHoliday(SysHoliday holiday);



// ================== 4. 返校管理 ==================
    @Select("SELECT " +
            "  r.id, " +
            "  r.student_id AS studentId, " +
            "  r.name, " +
            "  r.is_delayed AS isDelayed, " +
            "  r.reason, " +
            "  r.return_time AS returnTime, " +
            "  r.transport, " +
            "  r.transport_no AS transportNo, " +
            "  CONCAT(IFNULL(d.zone_name, ''), ' ', IFNULL(d.building_name, ''), ' ', IFNULL(d.room_number, '')) AS dormName " + // 宿舍名
            "FROM sys_return r " +
            "LEFT JOIN sys_user u ON r.student_id = u.username " + // 关联用户表
            "LEFT JOIN sys_dorm d ON u.dorm_id = d.id")            // 关联宿舍表
    List<SysReturn> getReturns();

    @Insert("INSERT INTO sys_return(student_id, name, is_delayed, reason, return_time, transport, transport_no) VALUES(#{studentId}, #{name}, #{isDelayed}, #{reason}, #{returnTime}, #{transport}, #{transportNo})")
    int addReturn(SysReturn sysReturn);

    @Select("SELECT * FROM sys_message ORDER BY create_time DESC")
    List<SysMessage> getMessages();

    @Insert("INSERT INTO sys_message(title, content, author, color) VALUES(#{title}, #{content}, #{author}, #{color})")
    int addMessage(SysMessage message);

    @Update("UPDATE sys_user SET password = #{newPwd} WHERE id = #{id} AND password = #{oldPwd}")
    int updatePassword(@Param("id") Integer id, @Param("oldPwd") String oldPwd, @Param("newPwd") String newPwd);
}