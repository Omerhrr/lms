<script setup lang="ts">
const theme = useTheme()
const auth = useAuth()

onMounted(async () => {
  theme.init()
  // Restore the signed-in user on hard reloads of pages without route
  // middleware, so the header reflects the real session everywhere.
  if (auth.token.value && !auth.user.value) await auth.fetchMe()
})
</script>

<template>
  <div>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
    <ToastHost />
  </div>
</template>
