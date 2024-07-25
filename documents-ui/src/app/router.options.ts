import type { RouterConfig } from '@nuxt/schema'
// @ts-ignore
import DocumentsDashboard from '~/pages/DocumentsDashboard.vue'
import { RouteNameE } from '~/enums/route-name-e'

export default <RouterConfig> {
  // https://router.vuejs.org/api/interfaces/routeroptions.html#routes
  // alternatively, could put this inside the setup for each page
  routes: _routes => [
    {
      name: RouteNameE.DOCUMENTS_DASHBOARD,
      path: '/',
      component: DocumentsDashboard,
      meta: {
        layout: 'default',
        title: 'Documents UI',
        breadcrumbs: [getBcrosHomeCrumb, getDocumentsDashboardCrumb]
      }
    }
  ]
}