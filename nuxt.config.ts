export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: false },
  modules: ['@nuxtjs/tailwindcss'],
  css: ['~/assets/css/main.css'],
  devServer: { host: '0.0.0.0', port: 3000 },
  // Allow preview/proxy hostnames (Vite blocks unknown Host headers by default)
  vite: {
    server: {
      allowedHosts: true
    }
  },
  // Proxy all /api/* calls to the FastAPI modular-monolith backend (port 8000)
  routeRules: {
    '/api/**': { proxy: 'http://127.0.0.1:8000/api/**' }
  },
  app: {
    head: {
      title: 'LearnHub - Learning Management System',
      htmlAttrs: { lang: 'en' },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'LearnHub - a full-featured learning management platform for instructors, students and administrators.' }
      ],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }]
    }
  },
  tailwindcss: {
    cssPath: '~/assets/css/main.css'
  }
})
