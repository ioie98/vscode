// vite.config.js
const { defineConfig } = require('vite')
const vue = require('@vitejs/plugin-vue')
const path = require('path')
// const socialuniPlatformAutoImportPlugin = require('vite-plugin-socialuni-platform-auto-import')
// const transformIoc = require('./viteplugin/index')

module.exports = defineConfig({
  define: {
    __DEV__: false,
    __FEATURE_PROD_DEVTOOLS__: false,
    __BROWSER__: true,
  },
  esbuild: {
    target: 'es2022'
  },
  plugins: [
    // transformIoc(),
    // socialuniPlatformAutoImportPlugin(),
    vue()
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
