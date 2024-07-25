import { RouteNameE } from '@/enums/route-name-e'

export default defineNuxtRouteMiddleware((to) => {
  const expectedRoutes = [RouteNameE.DOCUMENTS_DASHBOARD]
  if (!expectedRoutes.includes(to.name as RouteNameE)) {
      useBcrosNavigate().goToBcrosDashboard()
  }
})
