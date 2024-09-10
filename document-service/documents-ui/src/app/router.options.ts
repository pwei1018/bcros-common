import type { RouterConfig } from '@nuxt/schema'
import { RouteNameE } from '~/enums/route-name-e'
import { getDocumentManagementCrumb, getDocumentIndexingCrumb, getDocumentRecordsCrumb } from '~/utils/breadcrumbs'

export default <RouterConfig|Ro<unknown>> {
  // https://router.vuejs.org/api/interfaces/routeroptions.html#routes
  // alternatively, could put this inside the setup for each page
  routes: _routes => [
    {
      name: RouteNameE.DOCUMENT_MANAGEMENT,
      path: '/document-management',
      component: () => import('~/pages/DocumentManagement.vue').then(r => r.default || r),
      meta: {
        layout: 'default',
        title: 'Document Management',
        breadcrumbs: [getBcrosHomeCrumb, getDocumentManagementCrumb]
      }
    },
    {
      name: RouteNameE.DOCUMENT_INDEXING,
      path: '/document-indexing',
      component: () => import('~/pages/DocumentIndexing.vue').then(r => r.default || r),
      meta: {
        layout: 'default',
        title: 'Document Indexing',
        breadcrumbs: [getBcrosHomeCrumb, getDocumentManagementCrumb, getDocumentIndexingCrumb]
      }
    },
    {
      name: RouteNameE.DOCUMENT_RECORDS,
      path: '/document-records/:identifier',
      component: () => import('~/pages/DocumentRecords.vue').then(r => r.default || r),
      meta: {
        layout: 'tombstone-footer',
        title: 'Document Records',
        breadcrumbs: [getBcrosHomeCrumb, getDocumentManagementCrumb, getDocumentRecordsCrumb]
      }
    },
    {
      path: '/',
      redirect: '/document-management'
    }
  ]
}