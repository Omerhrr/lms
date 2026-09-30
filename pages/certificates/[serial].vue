<script setup lang="ts">
import { Printer, ShieldCheck, BadgeCheck, XCircle } from 'lucide-vue-next'

useSeoMeta({ title: 'Certificate - LearnHub' })

const route = useRoute()
const api = useApi()
const cert = ref<any>(null)
const notFound = ref(false)

onMounted(async () => {
  try {
    cert.value = await api.get<any>(`/certificates/${route.params.serial}`, undefined, true)
  } catch { notFound.value = true }
})

const prettyDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
</script>

<template>
  <div class="min-h-[calc(100vh-10rem)] flex flex-col items-center justify-center px-4 py-12">
    <div v-if="notFound" class="card p-10 text-center max-w-md">
      <XCircle class="w-14 h-14 mx-auto text-rose-400 mb-3" />
      <h1 class="text-xl font-bold text-slate-900">Certificate not found</h1>
      <p class="text-sm text-slate-500 mt-1">The serial <b>{{ route.params.serial }}</b> doesn't match any issued certificate.</p>
    </div>

    <div v-else-if="!cert" class="text-slate-400 text-sm">Verifying certificate…</div>

    <template v-else>
      <!-- certificate -->
      <div class="w-full max-w-3xl bg-white border-8 border-double border-brand-700 rounded-2xl shadow-2xl p-8 sm:p-14 text-center relative overflow-hidden">
        <div class="absolute -top-16 -right-16 w-56 h-56 rounded-full bg-brand-50" />
        <div class="absolute -bottom-20 -left-16 w-64 h-64 rounded-full bg-amber-50" />

        <div class="relative">
          <div class="flex items-center justify-center gap-2.5 mb-8">
            <img src="/logo.svg" class="w-10 h-10" alt="LearnHub" />
            <span class="text-2xl font-extrabold text-slate-900">Learn<span class="text-brand-600">Hub</span></span>
          </div>

          <p class="text-xs font-bold tracking-[0.3em] uppercase text-slate-400">Certificate of Completion</p>
          <p class="text-sm text-slate-500 mt-6">This certifies that</p>
          <h1 class="text-3xl sm:text-4xl font-extrabold text-slate-900 mt-2">{{ cert.user_name }}</h1>
          <p class="text-sm text-slate-500 mt-4">has successfully completed the course</p>
          <h2 class="text-xl sm:text-2xl font-bold text-brand-700 mt-2">{{ cert.course_title }}</h2>

          <div class="mt-10 flex flex-col sm:flex-row items-center justify-center gap-8 sm:gap-16 text-sm">
            <div>
              <p class="font-cursive text-lg text-slate-700 font-semibold">{{ cert.instructor_name }}</p>
              <div class="border-t border-slate-300 mt-1 pt-1 text-xs text-slate-400">Instructor</div>
            </div>
            <div class="w-14 h-14 rounded-full bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-lg">
              <BadgeCheck class="w-7 h-7 text-white" />
            </div>
            <div>
              <p class="text-slate-700 font-semibold">{{ prettyDate(cert.issued_at) }}</p>
              <div class="border-t border-slate-300 mt-1 pt-1 text-xs text-slate-400">Date issued</div>
            </div>
          </div>

          <p class="mt-10 text-xs text-slate-400 font-mono">Serial: {{ cert.serial }}</p>
        </div>
      </div>

      <!-- verify banner -->
      <div class="mt-6 card p-4 flex items-center gap-3 max-w-3xl w-full no-print">
        <ShieldCheck class="w-8 h-8 text-brand-600 shrink-0" />
        <div class="text-sm flex-1">
          <b class="text-slate-800">Verified certificate.</b>
          <span class="text-slate-500"> This certificate was issued by LearnHub and is authentic.</span>
        </div>
        <button @click="print" class="btn-secondary shrink-0 text-sm"><Printer class="w-4 h-4" /> Print</button>
      </div>
    </template>
  </div>
</template>
