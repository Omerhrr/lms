<script setup lang="ts">
import { ArrowLeft } from 'lucide-vue-next'

useSeoMeta({ title: 'New course - LearnHub' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const api = useApi()
const router = useRouter()
const { show } = useToast()

const categories = ref<any[]>([])
const form = ref({ title: '', summary: '', description: '', category_id: null as number | null, price: 0, level: 'beginner', language: 'English', tags: '' })
const saving = ref(false)

onMounted(async () => {
  try { categories.value = await api.get<any[]>('/categories') } catch {}
})

const submit = async () => {
  if (form.value.title.trim().length < 4) return show('Give the course a longer title (4+ chars)', 'error')
  saving.value = true
  try {
    const res = await api.post<{ id: number }>('/teach/courses', {
      ...form.value,
      tags: form.value.tags.split(',').map(t => t.trim()).filter(Boolean),
      price: Number(form.value.price),
    })
    show('Course created - build your curriculum next!')
    router.push(`/teach/courses/${res.id}/builder`)
  } catch (e: any) {
    show(e?.data?.detail || 'Could not create course', 'error')
  } finally { saving.value = false }
}
</script>

<template>
  <div class="max-w-2xl">
    <NuxtLink to="/teach/courses" class="text-sm text-slate-500 hover:text-slate-800 flex items-center gap-1 mb-4">
      <ArrowLeft class="w-4 h-4" /> All courses
    </NuxtLink>
    <h1 class="text-2xl font-extrabold text-slate-900 mb-6">Create a new course</h1>

    <form @submit.prevent="submit" class="card p-6 space-y-4">
      <div>
        <label class="label">Course title *</label>
        <input v-model="form.title" class="input" placeholder="e.g. Python Programming: Zero to Hero" />
      </div>
      <div>
        <label class="label">One-line summary</label>
        <input v-model="form.summary" class="input" placeholder="What will students achieve?" maxlength="500" />
      </div>
      <div class="grid sm:grid-cols-2 gap-4">
        <div>
          <label class="label">Category</label>
          <select v-model="form.category_id" class="input">
            <option :value="null">- None -</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div>
          <label class="label">Level</label>
          <select v-model="form.level" class="input">
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>
      </div>
      <div class="grid sm:grid-cols-2 gap-4">
        <div>
          <label class="label">Price (USD, 0 = free)</label>
          <input v-model.number="form.price" type="number" min="0" step="0.01" class="input" />
        </div>
        <div>
          <label class="label">Language</label>
          <input v-model="form.language" class="input" />
        </div>
      </div>
      <div>
        <label class="label">Tags (comma separated)</label>
        <input v-model="form.tags" class="input" placeholder="python, beginner, programming" />
      </div>
      <div>
        <label class="label">Description (rich-ish text)</label>
        <textarea v-model="form.description" class="input min-h-[140px] font-mono text-xs"
          placeholder="Supports: ## headings, - bullet lists and plain paragraphs&#10;&#10;## What you'll learn&#10;- Topic one&#10;- Topic two" />
        <p class="text-xs text-slate-400 mt-1">Tip: use ## for section headings and - for bullets.</p>
      </div>
      <button type="submit" class="btn-primary w-full py-3" :disabled="saving">
        {{ saving ? 'Creating…' : 'Create course & build curriculum' }}
      </button>
    </form>
  </div>
</template>
