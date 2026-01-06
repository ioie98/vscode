<template>
  <!-- 使用 ConfigProvider 全局配置语言 -->
  <el-config-provider :locale="customLocale">
    <RouterView />
  </el-config-provider>
</template>

<script setup>
import { RouterView } from 'vue-router'
import { ElConfigProvider } from 'element-plus'
// 引入中文语言包
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

// 自定义语言配置
const customLocale = {
  ...zhCn, // 继承原有中文配置
  el: {
    ...zhCn.el,
    pagination: {
      ...zhCn.el.pagination,
      // 在这里修改你想要的文字
      total: '计数 {total}',  // 把 "共 {total} 条" 改为 "计数 {total}"
      pagesize: '页',         // 把 "条/页" 改为 "页"
      goto: '前往',
      pageClassifier: '页'    // 跳转页码后的单位
    }
  }
}
</script>

<style>
/* 全局 CSS 变量覆盖 (Element Plus 主题色) */
:root {
  --el-color-primary: #409EFF; 
  --el-color-primary-light-3: #79bbff;
  --el-color-primary-light-5: #a0cfff;
  --el-color-primary-light-7: #c6e2ff;
  --el-color-primary-light-8: #d9ecff;
  --el-color-primary-light-9: #ecf5ff;
  --el-color-primary-dark-2: #337ecc;

  /* 边框颜色 */
  --el-border-color-light: #e4e7ed;
  --el-border-color-lighter: #ebeef5;

  /* 字体 */
  --el-font-size-base: 14px;
  --el-font-size-small: 13px;
  --el-font-size-extra-small: 12px;
}

/* 全局 CSS 重置和美化 */
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%; 
  width: 100%;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: #333; 
  background-color: #f0f2f5; 
  overflow: hidden; 
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-thumb {
  background-color: #dcdfe6;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background-color: #c0c4cc;
}
::-webkit-scrollbar-track {
  background-color: #f5f5f5;
  border-radius: 4px;
}

/* Element Plus 表格头部背景色统一 */
.el-table th.el-table__cell {
    background-color: #f5f7fa !important;
    color: #606266;
    font-weight: bold;
}
</style>