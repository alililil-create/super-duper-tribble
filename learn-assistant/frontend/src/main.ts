import {createApp} from 'vue'
import {createPinia} from 'pinia'
import {createRouter,createWebHistory} from 'vue-router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import Workspace from './Workspace.vue'
import './style.css'
const router=createRouter({history:createWebHistory(),routes:[{path:'/:pathMatch(.*)*',component:Workspace}]})
createApp(App).use(createPinia()).use(router).use(ElementPlus).mount('#app')
