import type { RouterConfig } from '@nuxt/schema'
import { RouteNameE } from '~/enums/route-name-e'

export default <RouterConfig> {
  // https://router.vuejs.org/api/interfaces/routeroptions.html#routes
  // alternatively, could put this inside the setup for each page
  routes: _routes => [
    {
      name: RouteNameE.DOCUMENTS_DASHBOARD,
      path: '/',
      component: () => import('~/pages/DocumentsDashboard.vue').then(r => r.default || r),
      meta: {
        layout: 'default',
        title: 'Documents UI',
        breadcrumbs: [getBcrosHomeCrumb, getDocumentsDashboardCrumb]
      }
    }
  ]
}