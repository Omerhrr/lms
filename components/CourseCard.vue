<script setup lang="ts">
import { Users, Clock, FileText } from 'lucide-vue-next'

const { money } = usePlatform()

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
    <div class="relative h-40">
      <CourseCover :title="course.title" :category="course.category?.name" :thumbnail-url="safeUrl(course.thumbnail_url)" />
      <span v-if="course.category" class="absolute top-3 left-3 badge chip-light">{{ course.category.name }}</span>
      <span v-if="showStatus && course.status" class="absolute top-3 right-3 badge" :class="statusColors[course.status]">{{ course.status }}</span>
      <span v-if="course.price === 0" class="absolute bottom-3 left-3 badge bg-amber-400 text-amber-950 font-bold">FREE</span>
    </div>

    <div class="p-4 flex flex-col flex-1">
      <h3 class="font-bold text-slate-900 leading-snug line-clamp-2 group-hover:text-brand-700 transition">{{ course.title }}</h3>
      <p class="mt-1.5 text-sm text-slate-600 line-clamp-2">{{ course.summary }}</p>

      <div class="mt-3 flex items-center gap-1.5 text-xs text-slate-600">
        <template v-if="course.review_count">
          <span class="font-bold text-amber-700">{{ course.rating.toFixed(1) }}</span>
          <RatingStars :rating="course.rating" size="w-3.5 h-3.5" />
          <span>({{ course.review_count }})</span>
        </template>
        <span v-else class="badge bg-sky-50 text-sky-700">New</span>
      </div>

      <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-600">
        <span class="flex items-center gap-1" :title="`${course.enrollment_count} learners`"><Users class="w-3.5 h-3.5" /> {{ course.enrollment_count }}</span>
        <span class="flex items-center gap-1"><FileText class="w-3.5 h-3.5" /> {{ plural(course.lesson_count, 'lesson') }}</span>
        <span class="flex items-center gap-1"><Clock class="w-3.5 h-3.5" /> {{ fmtMinutes(course.total_minutes) }}</span>
        <span class="badge ml-auto capitalize" :class="levelColors[course.level]">{{ course.level }}</span>
      </div>

      <div class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between mt-auto">
        <span class="text-xs text-slate-600 truncate">by {{ course.instructor.full_name }}</span>
        <span class="font-extrabold text-slate-900">{{ money(course.price) }}</span>
      </div>
    </div>
  </NuxtLink>
</template>
