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
        { name: 'description', content: 'LearnHub - a full-featured learning management platform for instructors, students and administrators.' },
        { name: 'theme-color', content: '#059669' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
        { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' },
        { rel: 'icon', type: 'image/png', sizes: '192x192', href: '/icon-192.png' },
        { rel: 'icon', type: 'image/png', sizes: '512x512', href: '/icon-512.png' },
        { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png' }
      ],
      script: [
        {
          // Apply the saved (or system) theme before first paint to avoid a flash of the wrong mode
          innerHTML:
            "(function(){try{var t=localStorage.getItem('lh-theme');if(t!=='dark'&&t!=='light'){t=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}if(t==='dark'){document.documentElement.classList.add('dark')}}catch(e){}})()"
        }
      ]
    }
  },
  tailwindcss: {
    cssPath: '~/assets/css/main.css'
  }
})
