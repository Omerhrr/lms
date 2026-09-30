<script setup lang="ts">
import { CheckCircle2, XCircle, RotateCcw, Send, Award, AlertCircle } from 'lucide-vue-next'

interface QuizQuestion {
  id: number; type: string; text: string; options: string[]; points: number
}
interface QuizPayload {
  id: number; title: string; description: string | null; passing_score: number
  max_attempts: number; questions: QuizQuestion[]; attempt_count: number
  best_score: number | null; passed: boolean; can_take: boolean
}
interface AttemptResult {
  score: number; passed: boolean; passing_score: number
  detail: Record<string, { correct: boolean; correct_answers: any[]; explanation: string | null }>
}

const props = defineProps<{ lessonId: number }>()
const emit = defineEmits<{ (e: 'passed'): void }>()
const api = useApi()
const { show } = useToast()

const quiz = ref<QuizPayload | null>(null)
const answers = ref<Record<string, any>>({})
const result = ref<AttemptResult | null>(null)
const submitting = ref(false)
const loading = ref(true)
const confirmSubmit = ref(false)

const load = async () => {
  loading.value = true
  try {
    quiz.value = await api.get<QuizPayload>(`/lessons/${props.lessonId}/quiz`)
  } catch {
    quiz.value = null
  } finally {
    loading.value = false
  }
}

const submit = async () => {
  submitting.value = true
  try {
    result.value = await api.post<AttemptResult>(`/quizzes/${quiz.value?.id}/attempts`, { answers: answers.value })
    confirmSubmit.value = false
    if (result.value.passed) emit('passed')
  } catch (e: any) {
    show(e?.data?.detail || 'Could not submit quiz', 'error')
  } finally {
    submitting.value = false
  }
}

const answeredCount = computed(() =>
  Object.keys(answers.value).filter(k => {
    const v = answers.value[k]
    return Array.isArray(v) ? v.length > 0 : (v !== undefined && v !== null && String(v).trim() !== '')
  }).length
)

const retry = () => {
  result.value = null
  answers.value = {}
}

const isAnswered = (q: QuizQuestion) => {
  const v = answers.value[q.id]
  if (Array.isArray(v)) return v.length > 0
  return v !== undefined && v !== null && String(v).trim() !== ''
}

onMounted(load)
</script>

<template>
  <div v-if="loading" class="py-12 text-center text-slate-400 text-sm">Loading quiz…</div>

  <div v-else-if="quiz" class="max-w-3xl mx-auto">
    <!-- header -->
    <div class="card p-5 mb-5">
      <h1 class="text-xl font-bold text-slate-900">{{ quiz.title }}</h1>
      <p v-if="quiz.description" class="text-sm text-slate-500 mt-1">{{ quiz.description }}</p>
      <div class="mt-3 flex flex-wrap gap-2 text-xs">
        <span class="badge bg-slate-100 text-slate-600">{{ quiz.questions.length }} questions</span>
        <span class="badge bg-slate-100 text-slate-600">Pass ≥ {{ quiz.passing_score }}%</span>
        <span v-if="quiz.max_attempts" class="badge bg-slate-100 text-slate-600">{{ quiz.max_attempts }} attempts allowed</span>
        <span class="badge bg-slate-100 text-slate-600">Used {{ quiz.attempt_count }}{{ quiz.max_attempts ? `/${quiz.max_attempts}` : '' }}</span>
        <span v-if="quiz.best_score !== null" class="badge bg-brand-50 text-brand-700">Best: {{ quiz.best_score }}%</span>
      </div>
    </div>

    <!-- blocked state -->
    <div v-if="!quiz.can_take" class="card p-8 text-center">
      <Award class="w-12 h-12 mx-auto text-brand-500 mb-3" />
      <h2 v-if="quiz.passed" class="font-bold text-lg text-slate-900">You already passed this quiz 🎉</h2>
      <h2 v-else class="font-bold text-lg text-slate-900">No attempts remaining</h2>
      <p class="text-sm text-slate-500 mt-1">Your best score: {{ quiz.best_score }}%</p>
    </div>

    <!-- result view -->
    <template v-else-if="result">
      <div class="card p-8 text-center mb-5" :class="result.passed ? 'border-brand-300' : 'border-rose-200'">
        <component :is="result.passed ? Award : AlertCircle"
          class="w-14 h-14 mx-auto mb-3" :class="result.passed ? 'text-brand-500' : 'text-rose-400'" />
        <div class="text-5xl font-extrabold" :class="result.passed ? 'text-brand-600' : 'text-rose-600'">{{ result.score }}%</div>
        <p class="mt-2 font-semibold" :class="result.passed ? 'text-brand-700' : 'text-rose-700'">
          {{ result.passed ? 'Passed - great job!' : `You need ${result.passing_score}% to pass` }}
        </p>
        <div v-if="!result.passed" class="mt-4">
          <button @click="retry" class="btn-secondary inline-flex"><RotateCcw class="w-4 h-4" /> Try again</button>
        </div>
      </div>

      <div class="space-y-4">
        <div v-for="(q, qi) in quiz.questions" :key="q.id" class="card p-5">
          <div class="flex items-start gap-3">
            <component :is="result.detail[q.id]?.correct ? CheckCircle2 : XCircle"
              class="w-5 h-5 shrink-0 mt-0.5" :class="result.detail[q.id]?.correct ? 'text-brand-500' : 'text-rose-500'" />
            <div class="flex-1">
              <p class="font-semibold text-slate-800 text-sm">{{ qi + 1 }}. {{ q.text }}</p>
              <p v-if="result.detail[q.id]?.explanation" class="text-xs text-slate-500 mt-2 bg-slate-50 rounded-lg p-3">
                💡 {{ result.detail[q.id].explanation }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- take quiz -->
    <template v-else>
      <div class="space-y-4">
        <div v-for="(q, qi) in quiz.questions" :key="q.id" class="card p-5">
          <p class="font-semibold text-slate-800 text-sm mb-3">
            {{ qi + 1 }}. {{ q.text }}
            <span class="text-xs font-normal text-slate-400">({{ q.points }} pt{{ q.points !== 1 ? 's' : '' }})</span>
          </p>

          <div v-if="q.type === 'single_choice' || q.type === 'true_false'" class="space-y-2">
            <label v-for="(opt, oi) in q.options" :key="oi"
              class="flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition text-sm"
              :class="answers[q.id] === oi ? 'border-brand-500 bg-brand-50 text-brand-800' : 'border-slate-200 hover:bg-slate-50'">
              <input type="radio" :name="`q${q.id}`" :value="oi" v-model="answers[q.id]" class="accent-brand-600" />
              {{ opt }}
            </label>
          </div>

          <div v-else-if="q.type === 'multi_choice'" class="space-y-2">
            <label v-for="(opt, oi) in q.options" :key="oi"
              class="flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition text-sm"
              :class="(answers[q.id] || []).includes(oi) ? 'border-brand-500 bg-brand-50 text-brand-800' : 'border-slate-200 hover:bg-slate-50'">
              <input type="checkbox" :value="oi" v-model="answers[q.id]" class="accent-brand-600 rounded" />
              {{ opt }}
            </label>
          </div>

          <input v-else type="text" v-model="answers[q.id]" placeholder="Type your answer…"
            class="input" />
        </div>
      </div>

      <div class="sticky bottom-4 mt-5 flex items-center justify-between bg-white border border-slate-200 rounded-xl shadow-lg p-4">
        <span class="text-sm text-slate-500">{{ answeredCount }}/{{ quiz.questions.length }} answered</span>
        <button class="btn-primary" :disabled="submitting" @click="confirmSubmit = true">
          <Send class="w-4 h-4" /> {{ submitting ? 'Submitting…' : 'Submit quiz' }}
        </button>
      </div>

      <Modal :open="confirmSubmit" title="Submit quiz?" @close="confirmSubmit = false">
        <p class="text-sm text-slate-600">
          You answered <b>{{ answeredCount }} of {{ quiz.questions.length }}</b> questions.
          {{ answeredCount < quiz.questions.length ? 'Unanswered questions will be marked incorrect.' : 'Everything is answered.' }}
        </p>
        <div class="mt-5 flex justify-end gap-2">
          <button class="btn-secondary" @click="confirmSubmit = false">Keep editing</button>
          <button class="btn-primary" :disabled="submitting" @click="submit">{{ submitting ? 'Submitting…' : 'Confirm submit' }}</button>
        </div>
      </Modal>
    </template>
  </div>
</template>
