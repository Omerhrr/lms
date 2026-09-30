export default defineNuxtRouteMiddleware(async (to) => {
  const auth = useAuth()
  if (!auth.user.value) await auth.fetchMe()
  if (!auth.user.value) {
    return navigateTo({ path: '/login', query: { redirect: to.fullPath } })
  }
})
