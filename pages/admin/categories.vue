<script setup lang="ts">
import { FolderTree, Plus, Pencil, Trash2 } from 'lucide-vue-next'

useSeoMeta({ title: 'Categories — LearnHub' })
definePageMeta({ middleware: 'admin', layout: 'dashboard' })

const api = useApi()
const { show } = useToast()

const categories = ref<any[]>([])
const loading = ref(true)
const modal = ref<{ open: boolean; editing?: any; name: string; description: string }>({ open: false, name: '', description: '' })

const load = async () => {
  loading.value = true
  try { categories.value = await api.get<any[]>('/categories') } finally { loading.value = false }
}
onMounted(load)

const save = async () => {
  if (modal.value.name.trim().length < 2) return show('Name is too short', 'error')
  try {
    if (modal.value.editing) {
      await api.put(`/categories/${modal.value.editing.id}`, { name: modal.value.name, description: modal.value.description || null })
      show('Category updated')
    } else {
      await api.post('/categories', { name: modal.value.name, description: modal.value.description || null })
      show('Category created')
    }
    modal.value = { open: false, name: '', description: '' }
    await load()
  } catch (e: any) { show(e?.data?.detail || 'Failed', 'error') }
}

const remove = async (c: any) => {
  if (!confirm(`Delete category "${c.name}"?`)) return
  try {
    await api.del(`/categories/${c.id}`)
    show('Category deleted', 'info')
    await load()
  } catch (e: any) { show(e?.data?.detail || 'Delete failed', 'error') }
}
</script>

<template>
  <div class="max-w-2xl">
    <div class="flex items-end justify-between mb-6">
      <div>
        <h1 class="text-2xl font-extrabold text-slate-900">Course categories</h1>
        <p class="text-slate-500 mt-1">Organize the catalog</p>
      </div>
      <button class="btn-primary" @click="modal = { open: true, name: '', description: '' }">
        <Plus class="w-4 h-4" /> New category
      </button>
    </div>

    <div v-if="loading" class="card h-64 animate-pulse" />
    <EmptyState v-else-if="categories.length === 0" empty>No categories yet.</EmptyState>

    <div v-else class="space-y-2.5">
      <div v-for="c in categories" :key="c.id" class="card p-4 flex items-center gap-4">
        <div class="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center shrink-0">
          <FolderTree class="w-5 h-5 text-brand-600" />
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-bold text-slate-800">{{ c.name }}</h3>
          <p class="text-xs text-slate-400 truncate">{{ c.description || c.slug }}</p>
        </div>
        <button class="p-2 rounded-lg hover:bg-slate-100 text-slate-400" @click="modal = { open: true, editing: c, name: c.name, description: c.description || '' }">
          <Pencil class="w-4 h-4" />
        </button>
        <button class="p-2 rounded-lg hover:bg-rose-50 text-rose-400" @click="remove(c)">
          <Trash2 class="w-4 h-4" />
        </button>
      </div>
    </div>

    <Modal :open="modal.open" :title="modal.editing ? 'Edit category' : 'New category'" @close="modal = { open: false, name: '', description: '' }">
      <div class="space-y-3">
        <div>
          <label class="label">Name</label>
          <input v-model="modal.name" class="input" placeholder="e.g. Photography" @keyup.enter="save" />
        </div>
        <div>
          <label class="label">Description</label>
          <input v-model="modal.description" class="input" placeholder="Optional" />
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-2">
          <button class="btn-secondary" @click="modal = { open: false, name: '', description: '' }">Cancel</button>
          <button class="btn-primary" @click="save">Save</button>
        </div>
      </template>
    </Modal>
  </div>
</template>
