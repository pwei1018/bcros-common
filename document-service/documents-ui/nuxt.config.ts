// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-07-24',
  devtools: { enabled: true },
  components: true,
  app: {
    buildAssetsDir: '/src/',
    head: {
      title: 'BCROS Documents-ui',
      htmlAttrs: { dir: 'ltr' },
      link: [{ rel: 'icon', type: 'image/png', href: '/favicon.png' }]
    }
  },
  colorMode: {
    preference: 'light'
  },
  srcDir: 'src/',
  css: [
    '@mdi/font/css/materialdesignicons.css',
    '@/assets/styles/base.scss',
    '@/assets/styles/layout.scss'
  ],
  ui: {
    icons: ['mdi']
  },
  ssr: false,
  extends: [
    ['github:bcgov/business-dashboard-ui#v0.0.1', { install: true }]
  ],
  imports: {
    dirs: ['enums', 'interfaces', 'stores']
  },
  modules: [
    '@nuxt/ui',
    '@nuxtjs/i18n',
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss',
    "@nuxt/eslint"
  ],
  typescript: {
    tsConfig: {
      compilerOptions: {
        module: "esnext",
        dynamicImport: true,
        noImplicitAny: false,
        strictNullChecks: false,
        strict: true
      }
    },
    // NOTE: https://github.com/vuejs/language-tools/issues/3969
    typeCheck: false
  },
  i18n: {
    lazy: true,
    defaultLocale: 'en',
    langDir: './lang',
    locales: [
      { code: 'en', file: 'en.json' }
    ]
  },
  runtimeConfig: {
    public: {
      // Keys within public, will be also exposed to the client-side
      addressCompleteKey: process.env.VUE_APP_ADDRESS_COMPLETE_KEY,
      authApiURL: `${process.env.VUE_APP_AUTH_API_URL || ''}${process.env.VUE_APP_AUTH_API_VERSION || ''}`,
      authWebURL: process.env.VUE_APP_AUTH_WEB_URL || '',
      dashboardOldUrl: process.env.VUE_APP_DASHBOARD_URL || '',
      documentsApiURL: `${process.env.VUE_APP_DOC_API_URL || ''}${process.env.VUE_APP_DOC_API_VERSION || ''}`,
      documentsApiKey: `${process.env.VUE_APP_DOC_API_KEY || ''}`,
      kcURL: process.env.VUE_APP_KEYCLOAK_AUTH_URL || '',
      kcRealm: process.env.VUE_APP_KEYCLOAK_REALM || '',
      kcClient: process.env.VUE_APP_KEYCLOAK_CLIENTID || '',
      ldClientId: process.env.VUE_APP_LD_CLIENT_ID || '',
      legalApiURL: `${process.env.VUE_APP_LEGAL_API_URL || ''}${process.env.VUE_APP_LEGAL_API_VERSION_2 || ''}`,
      payApiURL: `${process.env.VUE_APP_PAY_API_URL || ''}${process.env.VUE_APP_PAY_API_VERSION || ''}`,
      editApiURL: `${process.env.VUE_APP_BUSINESS_EDIT_URL || ''}`,
      registryHomeURL: process.env.VUE_APP_REGISTRY_HOME_URL || '',
      appEnv: `${process.env.VUE_APP_POD_NAMESPACE || 'unknown'}`,
      requireLogin: true,
      version: process.env.npm_package_version || '',
      appName: process.env.npm_package_name || '',
      appNameDisplay: 'BCROS Documents-ui'
    }
  }
})