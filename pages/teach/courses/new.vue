<script setup lang="ts">
import { ArrowLeft } from 'lucide-vue-next'

useSeoMeta({ title: 'New course - Infohive' })
definePageMeta({ middleware: 'staff', layout: 'dashboard' })

const api = useApi()
const router = useRouter()
const { show } = useToast()

const categories = ref<any[]>([])
const form = ref({ title: '', summary: '', description: '', category_id: null as number | null, price: 0, level: 'beginner', language: 'English', tags: '', outcomes: '' })
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
      outcomes: form.value.outcomes.split('\n').map(t => t.trim()).filter(Boolean),
    })
    show('Course created - build your curriculum next!')
    router.push(`/teach/courses/${res.id}/builder`)
  } catch {
    /* the api client already showed the error */
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
        <label class="label" for="teach-courses-new-form-title">Course title *</label>
        <input id="teach-courses-new-form-title" v-model="form.title" class="input" placeholder="e.g. Python Programming: Zero to Hero" />
      </div>
      <div>
        <label class="label" for="teach-courses-new-form-summary">One-line summary</label>
        <input id="teach-courses-new-form-summary" v-model="form.summary" class="input" placeholder="What will students achieve?" maxlength="500" />
      </div>
      <div>
        <label class="label" for="teach-courses-new-form-outcomes">What learners will learn <span class="font-normal text-slate-500">(optional, one per line)</span></label>
        <textarea id="teach-courses-new-form-outcomes" v-model="form.outcomes" rows="3" class="input" placeholder="Build a small web app&#10;Read and fix other people's code" />
      </div>
      <div class="grid sm:grid-cols-2 gap-4">
        <div>
          <label class="label" for="teach-courses-new-form-category_id">Category</label>
          <select id="teach-courses-new-form-category_id" v-model="form.category_id" class="input">
            <option :value="null">- None -</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </div>
        <div>
          <label class="label" for="teach-courses-new-form-level">Level</label>
          <select id="teach-courses-new-form-level" v-model="form.level" class="input">
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>
      </div>
      <div class="grid sm:grid-cols-2 gap-4">
        <div>
          <label class="label" for="teach-courses-new-form-price">Price ({{ usePlatform().config.value.currency }}, 0 = free)</label>
          <input id="teach-courses-new-form-price" v-model.number="form.price" type="number" min="0" step="0.01" class="input" />
        </div>
        <div>
          <label class="label" for="teach-courses-new-form-language">Language</label>
          <input id="teach-courses-new-form-language" v-model="form.language" class="input" />
        </div>
      </div>
      <div>
        <label class="label" for="teach-courses-new-form-tags">Tags (comma separated)</label>
        <input id="teach-courses-new-form-tags" v-model="form.tags" class="input" placeholder="python, beginner, programming" />
      </div>
      <div>
        <label class="label" for="teach-courses-new-form-description">Description (rich-ish text)</label>
        <textarea id="teach-courses-new-form-description" v-model="form.description" class="input min-h-[140px] font-mono text-xs"
          placeholder="Supports: ## headings, - bullet lists and plain paragraphs&#10;&#10;## What you'll learn&#10;- Topic one&#10;- Topic two" />
        <p class="text-xs text-slate-500 mt-1">Tip: use ## for section headings and - for bullets.</p>
      </div>
      <button type="submit" class="btn-primary w-full py-3" :disabled="saving">
        {{ saving ? 'Creating…' : 'Create course & build curriculum' }}
      </button>
    </form>
  </div>
</template>
