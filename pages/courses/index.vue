<script setup lang="ts">
import { Search, SlidersHorizontal, X } from 'lucide-vue-next'

useSeoMeta({ title: 'Browse courses — LearnHub' })

const route = useRoute()
const router = useRouter()
const api = useApi()

const courses = ref<any[]>([])
const total = ref(0)
const page = ref(Number(route.query.page) || 1)
const pages = ref(1)
const loading = ref(true)

const search = ref((route.query.search as string) || '')
const category_id = ref(route.query.category_id ? Number(route.query.category_id) : null)
const level = ref((route.query.level as string) || '')
const price = ref((route.query.price as string) || '')
const sort = ref((route.query.sort as string) || 'newest')
const categories = ref<any[]>([])

let debounce: ReturnType<typeof setTimeout> | undefined

const fetchCourses = async () => {
  loading.value = true
  try {
    const res = await api.get<any>('/courses', {
      search: search.value || undefined,
      category_id: category_id.value || undefined,
      level: level.value || undefined,
      price: price.value || undefined,
      sort: sort.value,
      page: page.value, size: 12,
    })
    courses.value = res.items
    total.value = res.total
    pages.value = res.pages
  } catch { /* keep UI */ } finally { loading.value = false }
}

watch([search, category_id, level, price, sort], () => {
  page.value = 1
  clearTimeout(debounce)
  debounce = setTimeout(() => { syncUrl(); fetchCourses() }, search.value ? 350 : 0)
})

watch(page, () => { syncUrl(); fetchCourses() })

const syncUrl = () => {
  router.replace({
    query: {
      ...(search.value ? { search: search.value } : {}),
      ...(category_id.value ? { category_id: String(category_id.value) } : {}),
      ...(level.value ? { level: level.value } : {}),
      ...(price.value ? { price: price.value } : {}),
      ...(sort.value !== 'newest' ? { sort: sort.value } : {}),
      ...(page.value > 1 ? { page: String(page.value) } : {}),
    },
  })
}

const clearFilters = () => {
  search.value = ''; category_id.value = null; level.value = ''; price.value = ''; sort.value = 'newest'
}
const hasFilters = computed(() => !!(search.value || category_id.value || level.value || price.value || sort.value !== 'newest'))

onMounted(async () => {
  try { categories.value = await api.get<any[]>('/categories', undefined, true) } catch {}
  fetchCourses()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10">
    <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 class="text-3xl font-extrabold text-slate-900">Browse courses</h1>
        <p class="text-slate-500 mt-1">{{ total }} course{{ total === 1 ? '' : 's' }} available</p>
      </div>
      <div class="relative w-full sm:w-80">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" />
        <input v-model="search" type="search" placeholder="Search courses…" class="input pl-10" />
      </div>
    </div>

    <!-- filter bar -->
    <div class="card p-4 mb-8 flex flex-wrap items-center gap-3">
      <SlidersHorizontal class="w-4.5 h-4.5 text-slate-400" />
      <select v-model="category_id" class="input w-auto min-w-[140px]">
        <option :value="null">All categories</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <select v-model="level" class="input w-auto min-w-[130px]">
        <option value="">Any level</option>
        <option value="beginner">Beginner</option>
        <option value="intermediate">Intermediate</option>
        <option value="advanced">Advanced</option>
      </select>
      <select v-model="price" class="input w-auto min-w-[120px]">
        <option value="">Any price</option>
        <option value="free">Free</option>
        <option value="paid">Paid</option>
      </select>
      <select v-model="sort" class="input w-auto min-w-[140px]">
        <option value="newest">Newest</option>
        <option value="popular">Most popular</option>
        <option value="rating">Highest rated</option>
        <option value="price_low">Price: low → high</option>
        <option value="price_high">Price: high → low</option>
      </select>
      <button v-if="hasFilters" @click="clearFilters" class="btn-ghost text-sm text-rose-600 ml-auto">
        <X class="w-4 h-4" /> Clear
      </button>
    </div>

    <div v-if="loading" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="i in 6" :key="i" class="card h-80 animate-pulse" />
    </div>

    <EmptyState v-else-if="courses.length === 0" empty>
      Try adjusting your search or filters.
    </EmptyState>

    <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <CourseCard v-for="c in courses" :key="c.id" :course="c" />
    </div>

    <!-- pagination -->
    <div v-if="pages > 1" class="mt-10 flex justify-center gap-1.5">
      <button v-for="p in pages" :key="p" @click="page = p"
        class="w-10 h-10 rounded-lg text-sm font-semibold transition"
        :class="p === page ? 'bg-brand-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'">
        {{ p }}
      </button>
    </div>
  </div>
</template>
