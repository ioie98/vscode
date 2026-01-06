import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 1. 引入 Element Plus 和 样式
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 2. 引入所有图标
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)

// 3. 注册所有图标 (这样你就可以直接用 icon="Search" 了)
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(router)
app.use(ElementPlus) // 4. 使用 Element Plus
app.mount('#app')