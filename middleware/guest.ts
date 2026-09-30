export default defineNuxtRouteMiddleware(async () => {
  const auth = useAuth()
  if (!auth.user.value) await auth.fetchMe()
  if (auth.user.value) {
    return navigateTo(auth.homeFor(auth.user.value))
  }
})
