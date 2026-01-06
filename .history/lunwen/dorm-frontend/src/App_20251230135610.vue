<template>
  <RouterView />
</template>

<style>
/* 全局 CSS 变量覆盖 (Element Plus 主题色) */
:root {
  --el-color-primary: #409EFF; /* Element Plus 默认蓝色，可以改成你喜欢的 */
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
  height: 100%; /* 确保html, body, #app占据全屏高度 */
  width: 100%;
}

body {
  font-family: -apple-system, BlinkMacMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: #333; /* 默认字体颜色 */
  background-color: #f0f2f5; /* 页面背景色 */
  overflow: hidden; /* 防止出现双滚动条 */
}

/* 滚动条美化 (可选，兼容性IE不支持) */
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