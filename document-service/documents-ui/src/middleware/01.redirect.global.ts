import { RouteNameE } from '@/enums/route-name-e'

export default defineNuxtRouteMiddleware((to) => {
  if (!Object.values(RouteNameE).includes(to.name as RouteNameE)) {
      useBcrosNavigate().goToBcrosDashboard()
  }
})
