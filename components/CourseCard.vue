<script setup lang="ts">
import { Star, Users, Clock, BarChart3, PlayCircle, FileText, HelpCircle, FileDown } from 'lucide-vue-next'

defineProps<{
  course: {
    id: number; title: string; slug: string; summary: string; thumbnail_url: string | null
    price: number; level: string; rating: number; review_count: number; enrollment_count: number
    total_minutes: number; lesson_count: number; status?: string
    instructor: { full_name: string }
    category?: { name: string } | null
  }
  showStatus?: boolean
}>()

const levelColors: Record<string, string> = {
  beginner: 'bg-emerald-50 text-emerald-700',
  intermediate: 'bg-amber-50 text-amber-700',
  advanced: 'bg-rose-50 text-rose-700',
}
const statusColors: Record<string, string> = {
  draft: 'bg-slate-100 text-slate-600',
  published: 'bg-brand-50 text-brand-700',
  archived: 'bg-rose-50 text-rose-600',
}
</script>

<template>
  <NuxtLink :to="`/courses/${course.slug}`"
    class="card group overflow-hidden hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 flex flex-col">
    <div class="relative h-40 bg-gradient-to-br from-brand-500 via-brand-600 to-slate-800 flex items-center justify-center overflow-hidden">
      <img v-if="course.thumbnail_url" :src="course.thumbnail_url" :alt="course.title" class="w-full h-full object-cover" />
      <BookOpen v-else class="w-14 h-14 text-white/40 group-hover:scale-110 transition-transform" />
      <span v-if="course.category" class="absolute top-3 left-3 badge bg-white/90 text-slate-700">{{ course.category.name }}</span>
      <span v-if="showStatus && course.status" class="absolute top-3 right-3 badge" :class="statusColors[course.status]">{{ course.status }}</span>
      <span v-if="course.price === 0" class="absolute bottom-3 left-3 badge bg-amber-400 text-amber-950 font-bold">FREE</span>
    </div>

    <div class="p-4 flex flex-col flex-1">
      <h3 class="font-bold text-slate-900 leading-snug line-clamp-2 group-hover:text-brand-700 transition">{{ course.title }}</h3>
      <p class="mt-1.5 text-sm text-slate-500 line-clamp-2">{{ course.summary }}</p>

      <div class="mt-3 flex items-center gap-1.5 text-xs text-slate-500">
        <RatingStars :rating="course.rating" size="w-3.5 h-3.5" />
        <span class="font-semibold text-slate-700">{{ course.rating || 'New' }}</span>
        <span v-if="course.review_count">({{ course.review_count }})</span>
      </div>

      <div class="mt-2 flex items-center gap-3 text-xs text-slate-500">
        <span class="flex items-center gap-1"><Users class="w-3.5 h-3.5" /> {{ course.enrollment_count }}</span>
        <span class="flex items-center gap-1"><FileText class="w-3.5 h-3.5" /> {{ course.lesson_count }} lessons</span>
        <span class="flex items-center gap-1"><Clock class="w-3.5 h-3.5" /> {{ Math.round(course.total_minutes / 60 * 10) / 10 || 0.1 }}h</span>
        <span class="badge ml-auto" :class="levelColors[course.level]">{{ course.level }}</span>
      </div>

      <div class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between mt-auto">
        <span class="text-xs text-slate-500 truncate">by {{ course.instructor.full_name }}</span>
        <span class="font-extrabold text-slate-900">{{ course.price === 0 ? 'Free' : `$${course.price.toFixed(2)}` }}</span>
      </div>
    </div>
  </NuxtLink>
</template>
