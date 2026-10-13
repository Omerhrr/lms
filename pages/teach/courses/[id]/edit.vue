<script setup lang="ts">
import { Save, Rocket, Undo2, Archive, Trash2, Upload, CheckCircle2, Circle, AlertCircle } from 'lucide-vue-next'

useSeoMeta({ title: 'Course settings - Infohive' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const route = useRoute()
const router = useRouter()
const api = useApi()
const { show } = useToast()
const courseId = Number(route.params.id)

const course = ref<any>(null)
const categories = ref<any[]>([])
const loading = ref(true)
const saving = ref(false)
const acting = ref(false)

const form = ref({
  title: '', summary: '', description: '',
  category_id: null as number | null,
  price: 0, level: 'beginner', language: 'English',
  tags: '' as string, thumbnail_url: '' as string, outcomes: '' as string,
})
const readiness = computed<any[]>(() => course.value?.readiness || [])
const blocking = computed(() => readiness.value.filter(i => i.required && !i.ok))
const readyCount = computed(() => readiness.value.filter(i => i.ok).length)

const load = async () => {
  loading.value = true
  try {
    const [c, cats] = await Promise.all([
      api.get<any>(`/teach/courses/${courseId}`),
      api.get<any[]>('/categories', undefined, true),
    ])
    course.value = c
    categories.value = cats
    form.value = {
      title: c.title,
      summary: c.summary || '',
      description: c.description || '',
      category_id: c.category?.id ?? null,
      price: c.price ?? 0,
      level: c.level || 'beginner',
      language: c.language || 'English',
      tags: Array.isArray(c.tags) ? c.tags.join(', ') : '',
      thumbnail_url: c.thumbnail_url || '',
      outcomes: Array.isArray(c.outcomes) ? c.outcomes.join('\n') : '',
    }
  } finally { loading.value = false }
}
onMounted(load)

const onThumbnail = async (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const res = await api.upload(file)
  form.value.thumbnail_url = res.url
  show('Thumbnail uploaded - remember to save!', 'info')
}

const save = async () => {
  const f = form.value
  if (!f.title.trim()) return show('Course title is required', 'error')
  saving.value = true
  try {
    await api.put(`/teach/courses/${courseId}`, {
      title: f.title.trim(),
      summary: f.summary,
      description: f.description,
      category_id: f.category_id,
      price: Number(f.price) || 0,
      level: f.level,
      language: f.language,
      thumbnail_url: f.thumbnail_url || null,
      outcomes: f.outcomes.split('\n').map((t: string) => t.trim()).filter(Boolean),
      tags: f.tags.split(',').map((t: string) => t.trim()).filter(Boolean),
    })
    show('Course settings saved')
    await load()
  } catch { /* the api client already showed the error */ } finally { saving.value = false }
}

const setStatus = async (action: 'publish' | 'unpublish' | 'archive') => {
  acting.value = true
  try {
    await api.post(`/teach/courses/${courseId}/${action}`)
    show(
      action === 'publish' ? 'Course published! Students can now enroll.'
        : action === 'unpublish' ? 'Course moved back to draft.'
          : 'Course archived.',
    )
    await load()
  } catch { /* the api client already showed the error */ } finally { acting.value = false }
}

const removeCourse = async () => {
  if (!confirm('Delete this course permanently? All sections, lessons, enrollments, grades and certificates go with it.')) return
  acting.value = true
  try {
    await api.del(`/teach/courses/${courseId}`)
    show('Course deleted', 'info')
    router.push('/teach/courses')
  } catch { /* the api client already showed the error */ } finally { acting.value = false }
}

// ---------- prerequisites ----------
const catalog = ref<any[]>([])
const prereqIds = ref<number[]>([])
const prereqSearch = ref('')
const savingPrereqs = ref(false)

const loadCatalog = async () => {
  try {
    const res = await api.get<any>('/courses', { size: 48 }, true)
    catalog.value = res.items.filter((c: any) => c.id !== courseId)
  } catch { catalog.value = [] }
}
watch(course, (c) => { if (c) prereqIds.value = [...(c.prerequisite_ids || [])] })
onMounted(loadCatalog)

const prereqOptions = computed(() => {
  const q = prereqSearch.value.trim().toLowerCase()
  return catalog.value.filter(c => !q || c.title.toLowerCase().includes(q))
})
const togglePrereq = (id: number) => {
  prereqIds.value = prereqIds.value.includes(id) ? prereqIds.value.filter(x => x !== id) : [...prereqIds.value, id]
}
const savePrereqs = async () => {
  savingPrereqs.value = true
  try {
    await api.put(`/teach/courses/${courseId}/prerequisites`, { course_ids: prereqIds.value })
    show('Prerequisites saved')
  } catch { /* toast shown */ } finally { savingPrereqs.value = false }
}

const statusStyle = computed(() => ({
  draft: 'bg-slate-100 text-slate-600',
  published: 'bg-emerald-50 text-emerald-700',
  archived: 'bg-amber-50 text-amber-700',
}[course.value?.status as string] || 'bg-slate-100 text-slate-600'))
</script>

<template>
  <div class="max-w-3xl">
    <div class="mb-6 flex items-center gap-3">
      <h1 class="text-2xl font-extrabold text-slate-900">Course settings</h1>
      <span v-if="course" class="badge capitalize" :class="statusStyle">{{ course.status }}</span>
    </div>

    <div v-if="loading" class="space-y-4"><div v-for="i in 3" :key="i" class="card h-24 animate-pulse" /></div>

    <template v-else-if="course">
      <!-- details -->
      <div class="card p-6 space-y-4">
        <h2 class="font-bold text-slate-800">Details</h2>
        <div>
          <label class="label" for="teach-courses-id-edi-form-title">Title</label>
          <input id="teach-courses-id-edi-form-title" v-model="form.title" class="input" placeholder="Course title" />
        </div>
        <div>
          <label class="label" for="teach-courses-id-edi-form-summary">Summary</label>
          <input id="teach-courses-id-edi-form-summary" v-model="form.summary" class="input" maxlength="500" placeholder="One-line pitch shown on cards (max 500 chars)" />
        </div>
        <div>
          <label class="label">Description</label>
          <ClientOnly>
            <RichEditor v-model="form.description" placeholder="What will students learn? Who is it for?" />
          </ClientOnly>
        </div>
        <div>
          <label class="label" for="teach-courses-id-edi-form-outcomes">What learners will learn <span class="font-normal text-slate-500">(one per line, 3-8 recommended)</span></label>
          <textarea id="teach-courses-id-edi-form-outcomes" v-model="form.outcomes" rows="5" class="input" placeholder="Write clean, readable Python&#10;Use loops, functions and data structures&#10;Build a small command-line project" />
        </div>
        <div class="grid sm:grid-cols-3 gap-3">
          <div>
            <label class="label" for="teach-courses-id-edi-form-category_id">Category</label>
            <select id="teach-courses-id-edi-form-category_id" v-model="form.category_id" class="input">
              <option :value="null">Uncategorized</option>
              <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </div>
          <div>
            <label class="label" for="teach-courses-id-edi-form-level">Level</label>
            <select id="teach-courses-id-edi-form-level" v-model="form.level" class="input">
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>
          <div>
            <label class="label" for="teach-courses-id-edi-form-price">Price ({{ usePlatform().config.value.currency }}, 0 = free)</label>
            <input id="teach-courses-id-edi-form-price" v-model.number="form.price" type="number" min="0" step="0.01" class="input" />
          </div>
        </div>
        <div class="grid sm:grid-cols-2 gap-3">
          <div>
            <label class="label" for="teach-courses-id-edi-form-language">Language</label>
            <input id="teach-courses-id-edi-form-language" v-model="form.language" class="input" />
          </div>
          <div>
            <label class="label" for="teach-courses-id-edi-form-tags">Tags (comma separated)</label>
            <input id="teach-courses-id-edi-form-tags" v-model="form.tags" class="input" placeholder="python, basics, coding" />
          </div>
        </div>
        <div>
          <label class="label">Thumbnail</label>
          <div class="flex items-center gap-4">
            <div class="w-28 h-16 rounded-lg bg-slate-100 border border-slate-200 overflow-hidden flex items-center justify-center shrink-0">
              <img v-if="form.thumbnail_url" :src="form.thumbnail_url" class="w-full h-full object-cover" alt="thumbnail" />
              <span v-else class="text-xs text-slate-500">No image</span>
            </div>
            <label class="btn-secondary cursor-pointer text-sm">
              <Upload class="w-4 h-4" /> Upload image
              <input type="file" class="hidden" accept="image/*" @change="onThumbnail" />
            </label>
          </div>
        </div>
        <button class="btn-primary" :disabled="saving" @click="save">
          <Save class="w-4 h-4" /> {{ saving ? 'Saving…' : 'Save changes' }}
        </button>
      </div>

      <!-- prerequisites -->
      <div class="card p-6 mt-6">
        <h2 class="font-bold text-slate-800 mb-1">Prerequisites</h2>
        <p class="text-sm text-slate-500 mb-4">Students must complete these courses before they can enroll in this one.</p>
        <input v-model="prereqSearch" class="input mb-3" placeholder="Search published courses…" />
        <div class="max-h-64 overflow-y-auto nice-scroll border border-slate-200 rounded-xl divide-y divide-slate-100">
          <label v-for="c in prereqOptions" :key="c.id" class="flex items-center gap-3 px-3 py-2.5 hover:bg-slate-50 cursor-pointer">
            <input type="checkbox" class="rounded accent-brand-600" :checked="prereqIds.includes(c.id)" @change="togglePrereq(c.id)" />
            <span class="flex-1 min-w-0">
              <span class="block text-sm font-medium text-slate-700 truncate">{{ c.title }}</span>
              <span class="block text-xs text-slate-500 truncate">{{ c.instructor?.full_name }} · {{ c.level }}</span>
            </span>
          </label>
          <p v-if="!prereqOptions.length" class="px-3 py-4 text-sm text-slate-500">No published courses match.</p>
        </div>
        <div class="mt-3 flex items-center justify-between gap-3 flex-wrap">
          <span class="text-xs text-slate-500">{{ prereqIds.length }} selected</span>
          <button class="btn-primary" :disabled="savingPrereqs" @click="savePrereqs">
            <Save class="w-4 h-4" /> {{ savingPrereqs ? 'Saving…' : 'Save prerequisites' }}
          </button>
        </div>
      </div>

      <!-- status -->
      <div class="card p-6 mt-6">
        <h2 class="font-bold text-slate-800 mb-1">Visibility</h2>
        <p class="text-sm text-slate-600 mb-4">Only published courses appear in the catalog.</p>
        <div v-if="readiness.length" class="rounded-xl border border-slate-200 p-4 mb-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-bold text-slate-800">Publish checklist</h3>
            <span class="text-xs text-slate-600">{{ readyCount }} / {{ readiness.length }} done</span>
          </div>
          <ul class="grid sm:grid-cols-2 gap-x-6 gap-y-2">
            <li v-for="i in readiness" :key="i.key" class="flex items-start gap-2 text-sm">
              <CheckCircle2 v-if="i.ok" class="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
              <AlertCircle v-else-if="i.required" class="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
              <Circle v-else class="w-4 h-4 text-slate-300 shrink-0 mt-0.5" />
              <span :class="i.ok ? 'text-slate-500' : 'text-slate-800'">{{ i.label }}<span v-if="i.required && !i.ok" class="text-rose-600 text-xs font-semibold"> · required</span></span>
            </li>
          </ul>
          <p class="text-xs text-slate-500 mt-3">Recommended items make the course page convert better. Save settings to refresh the list.</p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button v-if="course.status !== 'published'" class="btn-primary" :disabled="acting || blocking.length > 0" :title="blocking.length ? 'Finish the required items first' : ''" @click="setStatus('publish')">
            <Rocket class="w-4 h-4" /> Publish course
          </button>
          <button v-if="course.status === 'published'" class="btn-secondary" :disabled="acting" @click="setStatus('unpublish')">
            <Undo2 class="w-4 h-4" /> Unpublish (back to draft)
          </button>
          <button v-if="course.status !== 'archived'" class="btn-secondary" :disabled="acting" @click="setStatus('archive')">
            <Archive class="w-4 h-4" /> Archive
          </button>
          <NuxtLink v-if="course.slug" :to="`/courses/${course.slug}`" class="btn-ghost text-sm">Preview public page</NuxtLink>
        </div>
      </div>

      <!-- danger zone -->
      <div class="card p-6 mt-6 border-rose-200">
        <h2 class="font-bold text-rose-700 mb-1">Danger zone</h2>
        <p class="text-sm text-slate-500 mb-4">Deleting a course removes its lessons, quizzes, enrollments, grades and certificates. This cannot be undone.</p>
        <button class="btn bg-rose-600 text-white hover:bg-rose-700 inline-flex items-center gap-2" :disabled="acting" @click="removeCourse">
          <Trash2 class="w-4 h-4" /> Delete this course
        </button>
      </div>
    </template>
  </div>
</template>
