import { RouteNameE } from '~/enums/route-name-e'

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