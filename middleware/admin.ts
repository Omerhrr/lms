/** Allows only admins. */
export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuth()
  if (!auth.user.value) await auth.fetchMe()
  // on the server, an expired access cookie can't be refreshed (the new cookies would be lost),
  // so leave the decision to the browser, which refreshes and then re-checks
  if (!auth.user.value && import.meta.server && auth.hasSession.value) return
  if (!auth.user.value) {
    return navigateTo({ path: '/login', query: { redirect: to.fullPath } })
  }
  if (!auth.isAdmin.value) {
    return navigateTo(auth.homeFor(auth.user.value))
  }
})
