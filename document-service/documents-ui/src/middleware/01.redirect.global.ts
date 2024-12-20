import { RouteNameE } from '@/enums/route-name-e'

export default defineNuxtRouteMiddleware((to) => {
  // Redirect to dashboard if route is not in the list of allowed routes or if user is not a staff
  const { currentAccount } = storeToRefs(useBcrosAccount())
  if (!Object.values(RouteNameE).includes(to.name as RouteNameE) || currentAccount.value?.accountType !== 'STAFF') {
      useBcrosNavigate().goToBcrosDashboard()
  }
})
