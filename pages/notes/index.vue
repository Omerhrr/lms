<script setup lang="ts">
import { NotebookPen, Bookmark, Trash2, ArrowRight } from 'lucide-vue-next'

useSeoMeta({ title: 'Notes & bookmarks - Infohive' })
definePageMeta({ middleware: 'auth', layout: 'dashboard' })

const api = useApi()
const { show } = useToast()
const tab = ref<'notes' | 'bookmarks'>('notes')
const notes = ref<any[]>([])
const bookmarks = ref<any[]>([])
const loading = ref(true)
const search = ref('')

const load = async () => {
  loading.value = true
  try {
    ;[notes.value, bookmarks.value] = await Promise.all([
      api.get<any[]>('/me/notes'), api.get<any[]>('/me/bookmarks'),
    ])
  } finally { loading.value = false }
}
onMounted(load)

const match = (x: any) => {
  const q = search.value.trim().toLowerCase()
  return !q || [x.body, x.lesson_title, x.course_title].some((v: string) => (v || '').toLowerCase().includes(q))
}
const filteredNotes = computed(() => notes.value.filter(match))
const filteredBookmarks = computed(() => bookmarks.value.filter(match))

const removeBookmark = async (b: any) => {
  await api.del(`/lessons/${b.lesson_id}/bookmark`)
  bookmarks.value = bookmarks.value.filter(x => x.id !== b.id)
  show('Bookmark removed', 'info')
}
const removeNote = async (n: any) => {
  if (!confirm('Delete this note?')) return
  await api.put(`/lessons/${n.lesson_id}/note`, { body: '' })
  notes.value = notes.value.filter(x => x.id !== n.id)
  show('Note deleted', 'info')
}
const when = (iso: string) => new Date(iso.endsWith('Z') ? iso : iso + 'Z').toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
</script>

<template>
  <div class="max-w-4xl">
    <h1 class="text-2xl font-extrabold text-slate-900">Notes & bookmarks</h1>
    <p class="text-slate-500 text-sm mt-0.5 mb-5">Everything you've written or saved while studying. Only you can see these.</p>

    <div class="flex flex-wrap items-center gap-3 mb-4">
      <div class="inline-flex rounded-xl bg-slate-100 p-1">
        <button v-for="t in (['notes', 'bookmarks'] as const)" :key="t" @click="tab = t"
          class="px-3.5 py-1.5 rounded-lg text-sm font-semibold capitalize transition flex items-center gap-1.5"
          :class="tab === t ? 'bg-white shadow text-slate-900' : 'text-slate-500'">
          <component :is="t === 'notes' ? NotebookPen : Bookmark" class="w-4 h-4" />
          {{ t }} <span class="text-xs text-slate-400">{{ t === 'notes' ? notes.length : bookmarks.length }}</span>
        </button>
      </div>
      <input v-model="search" class="input sm:!w-64 flex-1 sm:flex-none" placeholder="Search…" />
    </div>

    <div v-if="loading" class="space-y-3"><div v-for="i in 3" :key="i" class="card h-24 animate-pulse" /></div>

    <template v-else-if="tab === 'notes'">
      <div v-if="!filteredNotes.length" class="card p-10 text-center text-slate-500">
        <NotebookPen class="w-10 h-10 mx-auto mb-2 text-slate-300" />
        <p class="font-semibold text-slate-700">{{ search ? 'No matching notes' : 'No notes yet' }}</p>
        <p class="text-sm mt-1">Open any lesson and use the “My notes” panel. It saves as you type.</p>
      </div>
      <div v-else class="space-y-3">
        <div v-for="n in filteredNotes" :key="n.id" class="card p-4 sm:p-5">
          <div class="flex items-start gap-3">
            <div class="min-w-0 flex-1">
              <p class="text-xs text-slate-400 truncate">{{ n.course_title }}</p>
              <h3 class="font-semibold text-slate-800 truncate">{{ n.lesson_title }}</h3>
            </div>
            <button class="p-1.5 rounded-lg hover:bg-rose-50 text-rose-400 shrink-0" aria-label="Delete note" @click="removeNote(n)"><Trash2 class="w-4 h-4" /></button>
          </div>
          <p class="mt-2 text-sm text-slate-700 whitespace-pre-wrap break-words line-clamp-6">{{ n.body }}</p>
          <div class="mt-3 flex items-center justify-between gap-2">
            <span class="text-xs text-slate-400">Updated {{ when(n.updated_at) }}</span>
            <NuxtLink :to="`/learn/${n.course_slug}/${n.lesson_id}`" class="text-sm font-semibold text-brand-700 hover:underline inline-flex items-center gap-1">
              Open lesson <ArrowRight class="w-3.5 h-3.5" />
            </NuxtLink>
          </div>
        </div>
      </div>
    </template>

    <template v-else>
      <div v-if="!filteredBookmarks.length" class="card p-10 text-center text-slate-500">
        <Bookmark class="w-10 h-10 mx-auto mb-2 text-slate-300" />
        <p class="font-semibold text-slate-700">{{ search ? 'No matching bookmarks' : 'No bookmarks yet' }}</p>
        <p class="text-sm mt-1">Tap the bookmark icon on any lesson to come back to it later.</p>
      </div>
      <div v-else class="card divide-y divide-slate-100">
        <div v-for="b in filteredBookmarks" :key="b.id" class="flex items-center gap-3 p-3 sm:p-4">
          <Bookmark class="w-4.5 h-4.5 text-amber-500 fill-amber-400 shrink-0" />
          <NuxtLink :to="`/learn/${b.course_slug}/${b.lesson_id}`" class="min-w-0 flex-1 group">
            <p class="font-medium text-slate-800 truncate group-hover:text-brand-700">{{ b.lesson_title }}</p>
            <p class="text-xs text-slate-400 truncate">{{ b.course_title }} · saved {{ when(b.created_at) }}</p>
          </NuxtLink>
          <button class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 shrink-0" aria-label="Remove bookmark" @click="removeBookmark(b)"><Trash2 class="w-4 h-4" /></button>
        </div>
      </div>
    </template>
  </div>
</template>
