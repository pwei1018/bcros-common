// https://nuxt.com/docs/api/configuration/nuxt-config
import path from 'path'

export default defineNuxtConfig({
  devtools: { enabled: true },
  imports: {
    dirs: [
      'store',
      'composables',
      'components',
      'enums',
      'interfaces',
      'utils'
    ]
  },
  ssr: false,
  css: ['./assets/main.css'],
  modules: ['@nuxt/ui'],
  runtimeConfig: {
    public: {
      documentsApiURL: `${process.env.VUE_APP_DOC_API_URL || ''}${process.env.VUE_APP_DOC_API_VERSION || ''}`,
      documentsApiKey: `${process.env.VUE_APP_DOC_API_KEY || ''}`,
    }
  }
})
