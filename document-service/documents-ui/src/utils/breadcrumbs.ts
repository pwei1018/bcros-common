import { RouteNameE } from '~/enums/route-name-e'

export function getBcrosHomeCrumb (): BreadcrumbI {
  const t = useNuxtApp().$i18n.t
  return {
    text: ref(t('breadcrumb.accountDashboard')),
    href: useRuntimeConfig().public.registryHomeURL + 'dashboard'
  }
}

export function getDocumentManagementCrumb (): BreadcrumbI {
  const t = useNuxtApp().$i18n.t
  return {
    text: ref(t('breadcrumb.documentManagement')),
    to: { name: RouteNameE.DOCUMENT_MANAGEMENT},
  }
}

export function getDocumentIndexingCrumb (): BreadcrumbI {
  const t = useNuxtApp().$i18n.t
  return {
    text: ref(t('breadcrumb.documentIndexing')),
    to: { name: RouteNameE.DOCUMENT_INDEXING},
  }
}

export function getDocumentRecordsCrumb (): BreadcrumbI {
  const t = useNuxtApp().$i18n.t
  return {
    text: ref(t('breadcrumb.documentRecords') + ' ' + useRoute()?.params?.identifier),
    to: { name: RouteNameE.DOCUMENT_RECORDS},
  }
}