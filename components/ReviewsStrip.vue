<script setup lang="ts">
import { Quote } from 'lucide-vue-next'
withDefaults(defineProps<{ title?: string }>(), { title: 'What our learners say' })
const api = useApi()
const reviews = ref<any[]>([])
onMounted(async () => {
  try { reviews.value = (await api.get<any[]>('/reviews/featured', undefined, true)).slice(0, 3) } catch { /* optional */ }
})
</script>

<template>
  <section v-if="reviews.length" class="max-w-7xl mx-auto px-4 sm:px-6 py-14">
    <h2 class="text-2xl sm:text-3xl font-extrabold text-slate-900 text-center">{{ title }}</h2>
    <div class="mt-8 grid md:grid-cols-3 gap-5">
      <figure v-for="(r, i) in reviews" :key="i" class="card p-6 flex flex-col">
        <Quote class="w-6 h-6 text-brand-300" />
        <RatingStars :rating="r.rating" class="mt-3" />
        <blockquote class="mt-3 text-sm text-slate-700 leading-relaxed line-clamp-5 flex-1">{{ r.comment }}</blockquote>
        <figcaption class="mt-4 pt-4 border-t border-slate-100 text-sm">
          <div class="font-semibold text-slate-900">{{ r.user.full_name }}</div>
          <NuxtLink :to="`/courses/${r.course.slug}`" class="text-xs text-brand-700 hover:underline">{{ r.course.title }}</NuxtLink>
        </figcaption>
      </figure>
    </div>
  </section>
</template>
