import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  // Expose components automatically
  components: [
    {
      path: '~/components',
      pathPrefix: false,
    },
  ],
  // Enable TypeScript strict mode
  typescript: {
    strict: true,
    shim: false,
  },
  css: [
    '@/assets/styles/base.scss',
    '@/assets/styles/layout.scss'
  ],
  // Add any shared modules or plugins here
  modules: ['@nuxt/ui'],
})
