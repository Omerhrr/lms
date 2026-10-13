<script setup lang="ts">
import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-vue-next'

// Paystack sends the student back here: /payments/callback?reference=...&trxref=...
useSeoMeta({ title: 'Confirming payment - Infohive' })
definePageMeta({ middleware: 'auth' })

const route = useRoute()
const api = useApi()
const reference = String(route.query.reference || route.query.trxref || '')
const payment = ref<any>(null)
const error = ref<string | null>(null)
const tries = ref(0)

const verify = async () => {
  if (!reference) { error.value = 'No payment reference in the link.'; return }
  try {
    payment.value = await api.get<any>(`/payments/verify/${encodeURIComponent(reference)}`, undefined, true)
    // bank transfers / USSD can take a moment to settle: poll a few times
    if (payment.value.status === 'pending' || payment.value.status === 'abandoned') {
      if (tries.value++ < 8) setTimeout(verify, 3000)
    }
  } catch (e: any) {
    error.value = e?.data?.detail || 'We could not confirm this payment.'
  }
}
onMounted(verify)
</script>

<template>
  <div class="min-h-[calc(100vh-10rem)] flex items-center justify-center px-4 py-12">
    <div class="card p-8 sm:p-10 max-w-md w-full text-center">
      <template v-if="error">
        <XCircle class="w-14 h-14 mx-auto text-rose-400 mb-3" />
        <h1 class="text-xl font-bold text-slate-900">Payment not confirmed</h1>
        <p class="text-sm text-slate-500 mt-2">{{ error }}</p>
        <p class="text-xs text-slate-400 mt-3">If you were charged, don't pay again - we'll match it automatically. Reference: <span class="font-mono">{{ reference }}</span></p>
        <NuxtLink to="/courses" class="btn-secondary mt-6 inline-flex">Back to courses</NuxtLink>
      </template>

      <template v-else-if="!payment || (payment.status !== 'success' && payment.status !== 'failed' && tries <= 8)">
        <Loader2 class="w-12 h-12 mx-auto text-brand-500 animate-spin mb-3" />
        <h1 class="text-xl font-bold text-slate-900">Confirming your payment…</h1>
        <p class="text-sm text-slate-500 mt-2">This usually takes a few seconds. Please don't close this page.</p>
      </template>

      <template v-else-if="payment.status === 'success'">
        <CheckCircle2 class="w-14 h-14 mx-auto text-brand-500 mb-3" />
        <h1 class="text-xl font-bold text-slate-900">Payment successful 🎉</h1>
        <p class="text-sm text-slate-500 mt-2">You're enrolled in <b class="text-slate-700">{{ payment.course_title }}</b>. A receipt is on its way to your email.</p>
        <p class="text-xs text-slate-400 mt-3">{{ payment.amount_display }} · <span class="font-mono">{{ payment.reference }}</span></p>
        <NuxtLink v-if="payment.course_slug" :to="`/learn/${payment.course_slug}`" class="btn-primary mt-6 inline-flex">Start learning</NuxtLink>
      </template>

      <template v-else-if="payment.status === 'failed'">
        <XCircle class="w-14 h-14 mx-auto text-rose-400 mb-3" />
        <h1 class="text-xl font-bold text-slate-900">Payment failed</h1>
        <p class="text-sm text-slate-500 mt-2">{{ payment.failure_reason || 'The payment was declined.' }} You haven't been enrolled.</p>
        <NuxtLink v-if="payment.course_slug" :to="`/courses/${payment.course_slug}`" class="btn-primary mt-6 inline-flex">Try again</NuxtLink>
      </template>

      <template v-else>
        <Clock class="w-14 h-14 mx-auto text-amber-400 mb-3" />
        <h1 class="text-xl font-bold text-slate-900">Payment still processing</h1>
        <p class="text-sm text-slate-500 mt-2">Some bank transfers take a few minutes. You'll be enrolled automatically and get an email when it clears.</p>
        <NuxtLink to="/payments" class="btn-secondary mt-6 inline-flex">View my payments</NuxtLink>
      </template>
    </div>
  </div>
</template>
