export function getBcrosHomeCrumb (): BreadcrumbI {
  const t = useNuxtApp().$i18n.t
  return {
    text: ref(t('breadcrumb.accountDashboard')),
    href: useRuntimeConfig().public.registryHomeURL + 'dashboard'
  }
}

export function getDocumentsDashboardCrumb (): BreadcrumbI {
  const t = useNuxtApp().$i18n.t
  return {
    text: ref(t('breadcrumb.documentsDashboard')),
    href: ``
  }
}