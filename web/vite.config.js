import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from "@tailwindcss/vite";
const ip = "192.168.2.10"
// https://vite.dev/config/
export default defineConfig({
  base: process.env.NODE_ENV === 'production' ? '/ScensUI_3/' : '/',
  plugins: [
    vue(),
    vueDevTools({
            
    }),
    tailwindcss()
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
    server: {
    proxy: {
      '/upload': {
        target: `http://${ip}:8889/upload`, // 后端API地址
        changeOrigin: true, // 是否修改请求头中的Origin
        rewrite: (path) => path.replace(/^\/upload/, ''), // 重写路径
      }
    },
    host: '0.0.0.0',
    port: 13314,
  },
})
