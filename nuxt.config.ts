export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: false },
  // The app manifest (used for ISR/route-rule prefetching) isn't needed here, and in dev on WSL it
  // can race with file generation and throw 'Failed to resolve import "#app-manifest"'.
  experimental: { appManifest: false },
  modules: ['@nuxtjs/tailwindcss'],
  css: ['~/assets/css/main.css'],
  devServer: { host: '0.0.0.0', port: 3000 },
  // Allow preview/proxy hostnames (Vite blocks unknown Host headers by default)
  vite: {
    server: {
      allowedHosts: true
    }
  },
  // /api/** is forwarded to the FastAPI backend by server/api/[...path].ts (same-origin, so the
  // API's HttpOnly session cookies are first-party). Override at runtime with env vars:
  //   NUXT_API_ORIGIN   e.g. https://learnhub-api.vercel.app
  //   NUXT_PROXY_SECRET same value as the API's PROXY_SHARED_SECRET
  runtimeConfig: {
    apiOrigin: 'http://127.0.0.1:8000',
    proxySecret: '',
  },
  routeRules: {
    '/**': {
      headers: {
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        // camera/mic are delegated only to iframes that ask for them (the live-class video room)
        'Permissions-Policy': 'camera=*, microphone=*, display-capture=*, geolocation=()'
      }
    }
  },
  app: {
    head: {
      title: 'Infohive Technology Ltd. - Technology. Learning. Innovation. Growth.',
      htmlAttrs: { lang: 'en' },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Infohive Technology Ltd. provides technology solutions and digital learning - web and software development, IT consulting, digital transformation, corporate training and online courses.' },
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
