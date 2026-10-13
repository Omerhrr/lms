<script setup lang="ts">
import { Search, X } from 'lucide-vue-next'

useSeoMeta({ title: 'Browse courses - Infohive' })

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
const levelNames: Record<string, string> = { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' }
// what the person has narrowed by, shown as removable chips
const activeChips = computed(() => [
  ...(search.value ? [{ key: 'search', label: `"${search.value}"`, clear: () => { search.value = '' } }] : []),
  ...(category_id.value ? [{ key: 'cat', label: categories.value.find(c => c.id === category_id.value)?.name || 'Category', clear: () => { category_id.value = null } }] : []),
  ...(level.value ? [{ key: 'level', label: levelNames[level.value], clear: () => { level.value = '' } }] : []),
  ...(price.value ? [{ key: 'price', label: price.value === 'free' ? 'Free' : 'Paid', clear: () => { price.value = '' } }] : []),
])
const hasFilters = computed(() => !!(search.value || category_id.value || level.value || price.value || sort.value !== 'newest'))

onMounted(async () => {
  try { categories.value = await api.get<any[]>('/categories', undefined, true) } catch {}
  fetchCourses()
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10">
    <div class="mb-6">
      <h1 class="text-3xl font-extrabold text-slate-900">Browse courses</h1>
      <p class="text-slate-600 mt-1" aria-live="polite">{{ loading ? 'Loading…' : `${total} course${total === 1 ? '' : 's'}${activeChips.length ? ' match' : ' available'}` }}</p>
    </div>

    <!-- search + filters in one bar -->
    <div class="card p-3 sm:p-4 mb-4 grid grid-cols-2 lg:grid-cols-[1fr_auto_auto_auto_auto] gap-2.5 sm:gap-3 items-center">
      <div class="relative col-span-2 lg:col-span-1">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-500" />
        <input v-model="search" type="search" aria-label="Search courses" placeholder="Search courses…" class="input pl-10" />
      </div>
      <select v-model="category_id" aria-label="Category" class="input lg:w-44">
        <option :value="null">All categories</option>
        <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <select v-model="level" aria-label="Level" class="input lg:w-36">
        <option value="">Any level</option>
        <option value="beginner">Beginner</option>
        <option value="intermediate">Intermediate</option>
        <option value="advanced">Advanced</option>
      </select>
      <select v-model="price" aria-label="Price" class="input lg:w-32">
        <option value="">Any price</option>
        <option value="free">Free</option>
        <option value="paid">Paid</option>
      </select>
      <select v-model="sort" aria-label="Sort by" class="input lg:w-44">
        <option value="newest">Sort: Newest</option>
        <option value="popular">Sort: Most popular</option>
        <option value="rating">Sort: Highest rated</option>
        <option value="price_low">Sort: Price, low → high</option>
        <option value="price_high">Sort: Price, high → low</option>
      </select>
    </div>

    <div class="min-h-[2rem] mb-6 flex flex-wrap items-center gap-2">
      <button v-for="c in activeChips" :key="c.key" type="button" @click="c.clear()"
        class="inline-flex items-center gap-1.5 rounded-full bg-brand-50 text-brand-800 border border-brand-200 pl-3 pr-2 py-1.5 text-sm font-medium hover:bg-brand-100"
        :aria-label="`Remove filter ${c.label}`">
        {{ c.label }} <X class="w-3.5 h-3.5" />
      </button>
      <button v-if="activeChips.length > 1" type="button" class="text-sm font-semibold text-slate-600 hover:text-slate-900 underline-offset-2 hover:underline" @click="clearFilters">Clear all</button>
    </div>

    <div v-if="loading" class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <div v-for="i in 6" :key="i" class="card h-80 animate-pulse" />
    </div>

    <EmptyState v-else-if="courses.length === 0" empty>
      No courses match these filters. <button v-if="hasFilters" class="text-brand-700 font-semibold hover:underline" @click="clearFilters">Clear filters</button>
    </EmptyState>

    <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <CourseCard v-for="c in courses" :key="c.id" :course="c" />
    </div>

    <!-- pagination -->
    <div v-if="pages > 1" class="mt-10 flex justify-center gap-1.5">
      <button v-for="p in pages" :key="p" @click="page = p" :aria-label="`Page ${p}`" :aria-current="p === page ? 'page' : undefined"
        class="w-10 h-10 rounded-lg text-sm font-semibold transition"
        :class="p === page ? 'bg-brand-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'">
        {{ p }}
      </button>
    </div>
  </div>
</template>
