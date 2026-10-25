import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' de web chay duoc o bat ky duong dan nao (GitHub Pages: /Thietbitheodoisuckhoe/).
export default defineConfig({
  plugins: [react()],
  base: './',
})
