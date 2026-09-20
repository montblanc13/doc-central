export default {
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/ui', '@nuxt/icon', '@nuxt/image'],
  css: ['~/assets/css/main.css'],
  icon: {
    serverBundle: {
      collections: ['lucide']
    }
  },
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api'
    }
  },
  typescript: {
    strict: true,
    typeCheck: true
  }
}
