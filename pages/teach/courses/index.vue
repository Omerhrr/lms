<script setup lang="ts">
import { Plus, Search } from 'lucide-vue-next'

useSeoMeta({ title: 'My courses - LearnHub' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const api = useApi()
const courses = ref<any[]>([])
const loading = ref(true)
const search = ref('')

onMounted(async () => {
  try { courses.value = await api.get<any[]>('/teach/courses') } finally { loading.value = false }
})

const filtered = computed(() =>
  courses.value.filter(c => c.title.toLowerCase().includes(search.value.toLowerCase())))
</script>

<template>
  <div>
    <div class="flex flex-wrap items-end justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">My courses</h1>
        <p class="text-slate-500 mt-1">Create, edit and monitor your courses</p>
      </div>
      <div class="flex gap-2">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input v-model="search" placeholder="Filter…" class="input pl-9 w-48" />
        </div>
        <NuxtLink to="/teach/courses/new" class="btn-primary"><Plus class="w-4 h-4" /> New course</NuxtLink>
      </div>
    </div>

    <div v-if="loading" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <div v-for="i in 3" :key="i" class="card h-80 animate-pulse" />
    </div>

    <EmptyState v-else-if="filtered.length === 0" empty>
      No courses match. <NuxtLink to="/teach/courses/new" class="text-brand-700 font-semibold">Create your first course →</NuxtLink>
    </EmptyState>

    <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
      <CourseCard v-for="c in filtered" :key="c.id" :course="c" show-status />
    </div>
  </div>
</template>
