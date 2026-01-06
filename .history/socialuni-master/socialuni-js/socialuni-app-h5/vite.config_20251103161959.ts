import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'node:url';
import socialuniPlatformAutoImportPlugin from '../vite-plugin-socialuni-platform-auto-import/src'; // ← 修改为 ../

export default defineConfig({
  define: {
    __DEV__: false,
    __FEATURE_PROD_DEVTOOLS__: false,
    __BROWSER__: true,
  },
  esbuild: {
    target: 'es2022'
  },
  plugins: [
    vue(),
    socialuniPlatformAutoImportPlugin()
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
});
