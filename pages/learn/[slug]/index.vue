<script setup lang="ts">
/** /learn/:slug → redirect into the course player (it picks first incomplete lesson). */
const route = useRoute()
onMounted(() => {
  navigateTo(`/learn/${route.params.slug}/0`, { replace: true })
})
</script>

<template>
  <div class="min-h-screen bg-slate-950 flex items-center justify-center text-slate-500 text-sm">
    Opening course player…
  </div>
</template>
