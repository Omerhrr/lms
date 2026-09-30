<script setup lang="ts">
import { ShieldCheck, Search } from 'lucide-vue-next'

useSeoMeta({ title: 'Verify a certificate - LearnHub' })
definePageMeta({ layout: 'default' })

const api = useApi()
const serial = ref('')
const result = ref<any>(null)
const error = ref('')
const loading = ref(false)

const verify = async () => {
  if (!serial.value.trim()) return
  loading.value = true
  error.value = ''
  result.value = null
  try {
    result.value = await api.get<any>(`/certificates/${serial.value.trim().toUpperCase()}`)
  } catch {
    error.value = 'No certificate found with that serial number.'
  } finally { loading.value = false }
}
</script>

<template>
  <div class="max-w-xl mx-auto px-4 py-16">
    <div class="text-center mb-8">
      <div class="w-16 h-16 rounded-2xl bg-brand-50 flex items-center justify-center mx-auto mb-4">
        <ShieldCheck class="w-8 h-8 text-brand-600" />
      </div>
      <h1 class="text-2xl font-extrabold text-slate-900">Verify a certificate</h1>
      <p class="text-slate-500 text-sm mt-1">Enter the serial number printed on the certificate.</p>
    </div>

    <div class="card p-6">
      <div class="flex gap-2">
        <input v-model="serial" class="input font-mono" placeholder="LH-XXXXXXXXXXXX" @keyup.enter="verify" />
        <button class="btn-primary shrink-0" :disabled="loading" @click="verify">
          <Search class="w-4 h-4" /> {{ loading ? 'Checking…' : 'Verify' }}
        </button>
      </div>

      <div v-if="result" class="mt-5 rounded-xl border border-brand-200 bg-brand-50 p-4">
        <p class="font-bold text-brand-800 flex items-center gap-2"><ShieldCheck class="w-5 h-5" /> Authentic certificate</p>
        <ul class="mt-2 text-sm text-slate-700 space-y-1">
          <li><b>{{ result.user_name }}</b> completed <b>{{ result.course_title }}</b></li>
          <li class="text-slate-500">Issued {{ new Date(result.issued_at).toLocaleDateString() }} by {{ result.instructor_name }}</li>
        </ul>
        <NuxtLink :to="`/certificates/${result.serial}`" class="text-sm text-brand-700 font-semibold hover:underline mt-2 inline-block">View certificate →</NuxtLink>
      </div>

      <p v-if="error" class="mt-5 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 font-medium">{{ error }}</p>
    </div>
  </div>
</template>
