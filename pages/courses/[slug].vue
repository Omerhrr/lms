<script setup lang="ts">
import {
  Clock, Users, Globe, BarChart3, PlayCircle, CheckCircle2, FileDown, Star,
  GraduationCap, MessageSquare, Megaphone, Lock, Check, Eye, FileText,
  ClipboardList, Upload, Send, Pin, PinOff, Unlock, Trash2, ArrowLeft, ChevronDown
} from 'lucide-vue-next'

const route = useRoute()
const api = useApi()
const auth = useAuth()
const { show } = useToast()

const course = ref<any>(null)
const reviews = ref<any[]>([])
const threads = ref<any[]>([])
const announcements = ref<any[]>([])
const assignments = ref<any[]>([])
const loading = ref(true)
const enrolling = ref(false)
const tab = ref<'overview' | 'curriculum' | 'live' | 'discussion' | 'assignments' | 'announcements' | 'reviews'>('overview')
const expanded = ref<Set<number>>(new Set())

const myReview = ref({ rating: 5, comment: '' })
const threadForm = ref({ title: '', body: '' })
const posting = ref(false)

// discussion thread viewer
const openThread = ref<any>(null)
const threadLoading = ref(false)
const replyText = ref('')
const replyPosting = ref(false)

// assignment submission forms, keyed by assignment id
const subForms = ref<Record<number, { text_response: string; file_url: string }>>({})
const submitting = ref<number | null>(null)

const load = async () => {
  loading.value = true
  try {
    course.value = await api.get<any>(`/courses/${route.params.slug}`, undefined, true)
    if (course.value?.sections?.length) expanded.value = new Set([course.value.sections[0].id])
    if (!course.value) { loading.value = false; return }
    if (auth.hasSession.value) await auth.fetchMe()
    if (course.value.is_enrolled) {
      reviews.value = await api.get<any[]>(`/courses/${route.params.slug}/reviews`, undefined, true).catch(() => [])
      threads.value = await api.get<any[]>(`/courses/${course.value.id}/discussions`, undefined, true).catch(() => [])
      announcements.value = await api.get<any[]>(`/courses/${course.value.id}/announcements`, undefined, true).catch(() => [])
      assignments.value = await api.get<any[]>(`/courses/${course.value.id}/assignments`, undefined, true).catch(() => [])
      // deep link from notifications: /courses/{slug}?tab=discussion&thread=ID
      const wanted = Number(route.query.thread)
      if (route.query.tab === 'discussion' && wanted) {
        tab.value = 'discussion'
        loadThread(wanted)
      } else if (route.query.tab === 'discussion') {
        tab.value = 'discussion'
      } else if (['live', 'assignments', 'announcements'].includes(String(route.query.tab))) {
        tab.value = route.query.tab as any
      }
    } else {
      reviews.value = await api.get<any[]>(`/courses/${route.params.slug}/reviews`, undefined, true).catch(() => [])
    }
  } catch (e) {
    course.value = null
  } finally { loading.value = false }
}

const { config: platform, money } = usePlatform()
const isPaid = computed(() => (course.value?.price || 0) > 0)
const canCheckout = computed(() => isPaid.value && platform.value.payments_enabled)
const needsRequest = computed(() => isPaid.value && !platform.value.payments_enabled)

const primaryLabel = computed(() => enrolling.value
  ? (canCheckout.value ? 'Opening secure checkout…' : 'Enrolling…')
  : !isPaid.value ? 'Enroll for free' : canCheckout.value ? 'Buy now' : 'Request access')
const primaryHint = computed(() => !isPaid.value ? 'Start right away - learn at your own pace'
  : canCheckout.value ? 'Secure payment by Paystack · card, bank transfer or USSD'
    : "We'll contact you with payment details")
const primaryAction = () => (needsRequest.value ? openRequest() : enroll())

const counts = computed(() => {
  const c: Record<string, number> = {}
  for (const s of course.value?.sections || []) for (const l of s.lessons) c[l.type] = (c[l.type] || 0) + 1
  return c
})

// ---------- request access (payments off) ----------
const requestOpen = ref(false)
const requestSent = ref(false)
const requestSending = ref(false)
const requestForm = ref({ name: '', email: '', phone: '', message: '' })
const openRequest = () => {
  requestSent.value = false
  requestForm.value = {
    name: auth.user.value?.full_name || '', email: auth.user.value?.email || '', phone: '',
    message: `I'd like to enroll in "${course.value.title}". Please send me the payment details.`,
  }
  requestOpen.value = true
}
const sendRequest = async () => {
  const f = requestForm.value
  if (f.name.trim().length < 2 || !/^\S+@\S+\.\S+$/.test(f.email)) return show('Please enter your name and a valid email', 'error')
  requestSending.value = true
  try {
    await api.post('/contact', { name: f.name, email: f.email, phone: f.phone || null, topic: 'LMS / Learning Enquiry',
      subject: `Enrollment request: ${course.value.title}`, message: f.message.length >= 10 ? f.message : `Enrollment request for ${course.value.title}`,
      course_id: course.value.id })
    requestSent.value = true
  } catch { /* toast shown */ } finally { requestSending.value = false }
}

const allOpen = computed(() => !!course.value?.sections.length && course.value.sections.every((s: any) => expanded.value.has(s.id)))
const toggleAll = () => {
  expanded.value = allOpen.value ? new Set() : new Set(course.value.sections.map((s: any) => s.id))
}

const enroll = async () => {
  if (!auth.isLoggedIn.value) return navigateTo({ path: '/login', query: { redirect: route.fullPath } })
  enrolling.value = true
  try {
    if (canCheckout.value) {
      // paid course: go to Paystack's secure checkout; they send the student back to /payments/callback
      const res = await api.post<{ authorization_url: string }>('/payments/checkout', { course_id: course.value.id })
      window.location.href = res.authorization_url
      return
    }
    await api.post(`/enrollments/${course.value.id}`)
    show(`You're enrolled in "${course.value.title}"! 🎉`)
    const firstLesson = firstPreviewableLesson()
    await load()
    if (firstLesson) navigateTo(`/learn/${course.value.slug}/${firstLesson.id}`)
  } catch { /* the api client already showed the error */ } finally { enrolling.value = false }
}

const firstPreviewableLesson = () => {
  for (const s of course.value?.sections || []) for (const l of s.lessons) return l
  return null
}

const canWatch = (l: any) => !l.unlocks_at && (l.is_preview || course.value?.is_enrolled || course.value?.can_manage)
const fmtUnlock = (iso: string) => new Date(iso + (iso.endsWith('Z') ? '' : 'Z')).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })

const toggle = (sid: number) => {
  const next = new Set(expanded.value)
  if (next.has(sid)) next.delete(sid)
  else next.add(sid)
  expanded.value = next
}

const lessonIcon = (t: string) => (t === 'video' ? PlayCircle : t === 'quiz' ? BarChart3 : t === 'file' ? FileDown : FileText)

const submitReview = async () => {
  try {
    await api.post(`/courses/${course.value.slug}/reviews`, myReview.value)
    show('Thanks for your review! ⭐')
    reviews.value = await api.get<any[]>(`/courses/${route.params.slug}/reviews`)
    course.value.has_reviewed = true
  } catch { /* the api client already showed the error */ }
}

const createThread = async () => {
  if (!threadForm.value.title.trim()) return show('Give your question a title', 'error')
  posting.value = true
  try {
    await api.post(`/courses/${course.value.id}/discussions`, threadForm.value)
    threadForm.value = { title: '', body: '' }
    threads.value = await api.get<any[]>(`/courses/${course.value.id}/discussions`)
    show('Question posted!')
  } catch { /* the api client already showed the error */ } finally { posting.value = false }
}

// ---------- thread detail ----------
const loadThread = async (id: number) => {
  threadLoading.value = true
  try {
    openThread.value = await api.get<any>(`/discussions/${id}`)
  } catch { /* the api client already showed the error */ } finally { threadLoading.value = false }
}

const closeThread = () => { openThread.value = null; replyText.value = '' }

const sendReply = async () => {
  const body = replyText.value.trim()
  if (!body || !openThread.value) return
  replyPosting.value = true
  try {
    await api.post(`/discussions/${openThread.value.id}/posts`, { body })
    replyText.value = ''
    await loadThread(openThread.value.id)
    threads.value = await api.get<any[]>(`/courses/${course.value.id}/discussions`)
  } catch { /* the api client already showed the error */ } finally { replyPosting.value = false }
}

const togglePin = async () => {
  await api.post(`/discussions/${openThread.value.id}/pin`)
  await loadThread(openThread.value.id)
  threads.value = await api.get<any[]>(`/courses/${course.value.id}/discussions`)
}

const toggleLock = async () => {
  await api.post(`/discussions/${openThread.value.id}/lock`)
  await loadThread(openThread.value.id)
  threads.value = await api.get<any[]>(`/courses/${course.value.id}/discussions`)
}

const deleteThread = async () => {
  if (!confirm('Delete this thread and all its replies?')) return
  await api.del(`/discussions/${openThread.value.id}`)
  closeThread()
  threads.value = await api.get<any[]>(`/courses/${course.value.id}/discussions`)
  show('Thread deleted', 'info')
}

// ---------- assignments ----------
const formFor = (a: any) => {
  if (!subForms.value[a.id]) subForms.value[a.id] = { text_response: a.my_submission?.text_response || '', file_url: a.my_submission?.file_url || '' }
  return subForms.value[a.id]
}

const onSubmissionFile = async (a: any, e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  const res = await api.upload(file)
  formFor(a).file_url = res.url
  show('File attached - submit when ready!', 'info')
}

const submitAssignment = async (a: any) => {
  const f = formFor(a)
  if (!f.text_response.trim() && !f.file_url) return show('Write a response or attach a file', 'error')
  submitting.value = a.id
  try {
    await api.post(`/assignments/${a.id}/submit`, { text_response: f.text_response, file_url: f.file_url || null })
    show('Assignment submitted!')
    assignments.value = await api.get<any[]>(`/courses/${course.value.id}/assignments`)
  } catch { /* the api client already showed the error */ } finally { submitting.value = null }
}

const formatDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })

onMounted(load)
watch(() => route.params.slug, load)
</script>

<template>
  <div v-if="loading" class="max-w-7xl mx-auto px-4 sm:px-6 py-10">
    <div class="h-8 w-96 bg-slate-200 rounded animate-pulse mb-6" />
    <div class="grid lg:grid-cols-3 gap-8"><div class="lg:col-span-2 h-96 bg-slate-200 rounded-xl animate-pulse" /><div class="h-96 bg-slate-200 rounded-xl animate-pulse" /></div>
  </div>

  <div v-else-if="!course" class="max-w-7xl mx-auto px-4 py-20 text-center">
    <h1 class="text-2xl font-bold text-slate-800">Course not found</h1>
    <NuxtLink to="/courses" class="btn-primary mt-4 inline-flex">Browse courses</NuxtLink>
  </div>

  <div v-else>
    <!-- hero -->
    <section class="bg-slate-900 text-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 pt-10 pb-10 lg:pb-14 grid lg:grid-cols-[1fr_22rem] gap-10">
        <div class="min-w-0 lg:min-h-[22rem]">
          <nav class="text-xs text-slate-400 mb-4 flex items-center gap-1.5" aria-label="Breadcrumb">
            <NuxtLink to="/courses" class="hover:text-white">Courses</NuxtLink>
            <template v-if="course.category"><span>/</span>
              <NuxtLink :to="{ path: '/courses', query: { category_id: course.category.id } }" class="hover:text-white">{{ course.category.name }}</NuxtLink></template>
          </nav>
          <h1 class="text-3xl lg:text-[2.5rem] font-extrabold leading-tight tracking-tight">{{ course.title }}</h1>
          <p class="mt-3 text-slate-300 text-lg leading-relaxed max-w-3xl">{{ course.summary }}</p>
          <div class="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-slate-300">
            <span v-if="course.review_count" class="flex items-center gap-1.5">
              <b class="text-amber-300">{{ course.rating.toFixed(1) }}</b>
              <RatingStars :rating="course.rating" size="w-4 h-4" />
              <button class="underline-offset-2 hover:underline" @click="tab = 'reviews'">({{ plural(course.review_count, 'review') }})</button>
            </span>
            <span v-else class="badge bg-sky-400/15 text-sky-200">New course</span>
            <span class="flex items-center gap-1.5"><Users class="w-4 h-4" /> {{ plural(course.enrollment_count, 'learner') }}</span>
            <span class="flex items-center gap-1.5"><Clock class="w-4 h-4" /> {{ fmtMinutes(course.total_minutes) }}</span>
            <span class="flex items-center gap-1.5 capitalize"><BarChart3 class="w-4 h-4" /> {{ course.level }}</span>
            <span class="flex items-center gap-1.5"><Globe class="w-4 h-4" /> {{ course.language }}</span>
          </div>
          <div class="mt-5 flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-brand-600 flex items-center justify-center font-bold uppercase">{{ course.instructor.full_name.slice(0, 1) }}</div>
            <div>
              <div class="font-semibold text-sm">{{ course.instructor.full_name }}</div>
              <div class="text-xs text-slate-400">{{ course.instructor.headline || 'Instructor' }}</div>
            </div>
            <span v-if="course.status !== 'published'" class="badge bg-amber-500/20 text-amber-300 ml-2 capitalize">{{ course.status }} - only you can see this</span>
          </div>

          <div v-if="course.outcomes?.length" class="mt-8 rounded-2xl border border-white/10 bg-white/[0.04] p-5 sm:p-6">
            <h2 class="font-bold text-white">What you'll learn</h2>
            <ul class="mt-3 grid sm:grid-cols-2 gap-x-6 gap-y-2.5 text-sm text-slate-200">
              <li v-for="o in course.outcomes" :key="o" class="flex gap-2.5"><Check class="w-4.5 h-4.5 text-brand-400 shrink-0 mt-0.5" /><span>{{ o }}</span></li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 grid lg:grid-cols-[1fr_22rem] gap-10 pb-24 lg:pb-10">
      <!-- main column -->
      <div class="min-w-0 order-2 lg:order-1">
        <!-- tabs -->
        <div class="bg-slate-50/95 dark:bg-slate-950/95 backdrop-blur border-b border-slate-200 sticky top-16 z-20 -mx-4 px-4 sm:mx-0 sm:px-0">
          <div class="flex gap-1 overflow-x-auto">
            <button v-for="t in [
              ['overview', 'Overview'],
              ...(course.is_enrolled || course.can_manage ? [['live', 'Live classes'], ['discussion', 'Q&A'], ['assignments', 'Assignments'], ['announcements', 'Announcements']] : []),
              ['reviews', course.review_count ? `Reviews (${course.review_count})` : 'Reviews'],
            ]" :key="t[0]" @click="tab = t[0] as any"
              class="px-4 py-3.5 text-sm font-semibold border-b-2 transition whitespace-nowrap"
              :class="tab === t[0] ? 'border-brand-600 text-brand-700' : 'border-transparent text-slate-500 hover:text-slate-800'">
              {{ t[1] }}
            </button>
          </div>
        </div>

        <div class="py-8 min-h-[300px]">
          <!-- overview: curriculum first (what buyers check), then description and instructor -->
          <div v-if="tab === 'overview' || tab === 'curriculum'" class="space-y-10">
            <section>
              <div class="flex flex-wrap items-end justify-between gap-2 mb-3">
                <h2 class="text-xl font-bold text-slate-900">Course content</h2>
                <p class="text-sm text-slate-500">{{ plural(course.sections.length, 'section') }} · {{ plural(course.lesson_count, 'lesson') }} · {{ fmtMinutes(course.total_minutes) }}
                  <button class="ml-2 font-semibold text-brand-700 hover:underline" @click="toggleAll">{{ allOpen ? 'Collapse all' : 'Expand all' }}</button></p>
              </div>
              <div class="card divide-y divide-slate-100 overflow-hidden">
                <div v-for="s in course.sections" :key="s.id">
                  <button class="w-full flex items-center justify-between gap-3 px-4 sm:px-5 py-3.5 bg-slate-50/70 hover:bg-slate-100/70 transition text-left" :aria-expanded="expanded.has(s.id)" @click="toggle(s.id)">
                    <span class="flex items-center gap-2 min-w-0">
                      <ChevronDown class="w-4 h-4 text-slate-500 shrink-0 transition" :class="expanded.has(s.id) ? '' : '-rotate-90'" />
                      <span class="font-semibold text-slate-800 truncate">{{ s.title }}</span>
                    </span>
                    <span class="text-xs text-slate-500 shrink-0">{{ plural(s.lessons.length, 'lesson') }} · {{ fmtMinutes(s.lessons.reduce((a: number, l: any) => a + (l.duration_minutes || 0), 0)) }}</span>
                  </button>
                  <div v-if="expanded.has(s.id)" class="divide-y divide-slate-50">
                    <div v-for="l in s.lessons" :key="l.id" class="flex flex-wrap sm:flex-nowrap items-center gap-x-3 gap-y-1 px-4 sm:px-5 py-3">
                      <component :is="lessonIcon(l.type)" class="w-4.5 h-4.5 shrink-0" :class="canWatch(l) ? 'text-brand-600' : 'text-slate-400'" />
                      <span class="text-sm flex-1 min-w-0" :class="canWatch(l) ? 'text-slate-800' : 'text-slate-600'">{{ l.title }}</span>
                      <span v-if="l.is_preview && !course.is_enrolled" class="badge bg-brand-50 text-brand-700">Free preview</span>
                      <span v-if="l.unlocks_at" class="badge bg-amber-50 text-amber-700">Opens {{ fmtUnlock(l.unlocks_at) }}</span>
                      <span v-else-if="l.drip_days && !course.is_enrolled" class="text-xs text-slate-500">Unlocks day {{ l.drip_days }}</span>
                      <span class="text-xs text-slate-500 w-14 text-right">{{ fmtMinutes(l.duration_minutes) }}</span>
                      <NuxtLink v-if="canWatch(l)" :to="`/learn/${course.slug}/${l.id}`" class="text-xs font-semibold text-brand-700 hover:underline w-12 text-right">{{ l.type === 'video' ? 'Watch' : 'Open' }}</NuxtLink>
                      <Lock v-else class="w-3.5 h-3.5 text-slate-400 w-12" aria-label="Locked" />
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <section v-if="course.description">
              <h2 class="text-xl font-bold text-slate-900 mb-3">About this course</h2>
              <div class="rich-text text-slate-700" v-html="course.description" />
            </section>

            <section v-if="course.prerequisites?.length">
              <h2 class="text-xl font-bold text-slate-900 mb-3">Before you start</h2>
              <ul class="space-y-2">
                <li v-for="p in course.prerequisites" :key="p.id" class="flex items-center gap-2 text-sm">
                  <component :is="p.completed ? CheckCircle2 : Lock" class="w-4 h-4 shrink-0" :class="p.completed ? 'text-brand-600' : 'text-amber-600'" />
                  Complete <NuxtLink :to="`/courses/${p.slug}`" class="font-semibold text-brand-700 hover:underline">{{ p.title }}</NuxtLink>
                </li>
              </ul>
            </section>

            <section>
              <h2 class="text-xl font-bold text-slate-900 mb-3">Your instructor</h2>
              <div class="card p-5 flex gap-4">
                <div class="w-14 h-14 rounded-full bg-brand-600 text-white text-xl flex items-center justify-center font-bold uppercase shrink-0">{{ course.instructor.full_name.slice(0, 1) }}</div>
                <div class="min-w-0">
                  <p class="font-bold text-slate-900">{{ course.instructor.full_name }}</p>
                  <p class="text-sm text-brand-700">{{ course.instructor.headline || 'Instructor' }}</p>
                  <p v-if="course.instructor.bio" class="mt-2 text-sm text-slate-600 leading-relaxed">{{ course.instructor.bio }}</p>
                </div>
              </div>
            </section>

            <section v-if="reviews.length">
              <div class="flex items-end justify-between gap-2 mb-3">
                <h2 class="text-xl font-bold text-slate-900">What learners say</h2>
                <button class="text-sm font-semibold text-brand-700 hover:underline" @click="tab = 'reviews'">All reviews</button>
              </div>
              <div class="grid sm:grid-cols-2 gap-3">
                <figure v-for="r in reviews.slice(0, 2)" :key="r.id" class="card p-5">
                  <RatingStars :rating="r.rating" size="w-3.5 h-3.5" />
                  <blockquote class="mt-2 text-sm text-slate-700 leading-relaxed">“{{ r.comment }}”</blockquote>
                  <figcaption class="mt-3 text-xs font-semibold text-slate-600">{{ r.user.full_name }}</figcaption>
                </figure>
              </div>
            </section>
          </div>

      <!-- discussion -->
      <div v-else-if="tab === 'discussion'" class="space-y-6">
        <div class="card p-5">
          <h3 class="font-bold text-slate-800 mb-3 flex items-center gap-2"><MessageSquare class="w-4.5 h-4.5 text-brand-600" /> Ask a question</h3>
          <input v-model="threadForm.title" class="input mb-2" placeholder="Question title…" />
          <textarea v-model="threadForm.body" class="input min-h-[80px]" placeholder="Describe your question…" />
          <button class="btn-primary mt-3" :disabled="posting" @click="createThread">{{ posting ? 'Posting…' : 'Post question' }}</button>
        </div>
        <EmptyState v-if="threads.length === 0" empty>No discussions yet - be the first to ask!</EmptyState>
        <div v-for="t in threads" :key="t.id" @click="loadThread(t.id)"
          class="card p-4 flex items-start gap-4 hover:border-brand-300 transition cursor-pointer">
          <div class="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center font-bold text-slate-500 uppercase text-sm shrink-0">
            {{ t.author.full_name.slice(0, 1) }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <h4 class="font-semibold text-slate-800 truncate">{{ t.title }}</h4>
              <span v-if="t.is_pinned" class="badge bg-amber-50 text-amber-700">📌 Pinned</span>
              <span v-if="t.is_locked" class="badge bg-slate-100 text-slate-500">🔒 Locked</span>
            </div>
            <p class="text-xs text-slate-400 mt-0.5">{{ t.author.full_name }} · {{ t.reply_count }} replies</p>
          </div>
        </div>
      </div>

      <!-- assignments -->
      <div v-else-if="tab === 'assignments'" class="space-y-5">
        <EmptyState v-if="assignments.length === 0" empty>No assignments in this course (yet).</EmptyState>
        <div v-for="a in assignments" :key="a.id" class="card p-5">
          <div class="flex items-start justify-between gap-3 flex-wrap">
            <div class="flex items-start gap-3 min-w-0">
              <div class="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center shrink-0">
                <ClipboardList class="w-5 h-5 text-amber-600" />
              </div>
              <div class="min-w-0">
                <h4 class="font-bold text-slate-800">{{ a.title }}</h4>
                <p class="text-xs text-slate-400 mt-0.5">
                  {{ a.max_points }} points
                  <span v-if="a.due_date"> · due {{ formatDate(a.due_date) }}</span>
                </p>
              </div>
            </div>
            <span v-if="a.my_submission" class="badge shrink-0"
              :class="a.my_submission.status === 'graded' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">
              {{ a.my_submission.status === 'graded' ? `Graded: ${a.my_submission.grade}/${Math.round(a.max_points)}` : 'Submitted - awaiting grade' }}
            </span>
            <span v-else class="badge bg-slate-100 text-slate-500 shrink-0">Not submitted</span>
          </div>

          <p v-if="a.instructions" class="text-sm text-slate-600 mt-3 whitespace-pre-wrap border-l-2 border-slate-100 pl-3">{{ a.instructions }}</p>

          <!-- graded feedback -->
          <div v-if="a.my_submission?.status === 'graded'" class="mt-4 rounded-lg bg-emerald-50 border border-emerald-100 p-4 text-sm">
            <p v-if="a.my_submission.feedback" class="text-emerald-800"><b>Instructor feedback:</b> {{ a.my_submission.feedback }}</p>
            <p v-else class="text-emerald-800">Graded {{ a.my_submission.grade }}/{{ Math.round(a.max_points) }}.</p>
          </div>

          <!-- submit / resubmit form -->
          <div v-else-if="course.is_enrolled" class="mt-4 space-y-3 border-t border-slate-100 pt-4">
            <p class="text-xs font-semibold uppercase tracking-wider text-slate-400">
              {{ a.my_submission ? 'Resubmit (allowed until it is graded)' : 'Your submission' }}
            </p>
            <textarea v-model="formFor(a).text_response" class="input min-h-[90px]"
              placeholder="Write your answer, paste a link, or attach a file…" />
            <div class="flex flex-wrap items-center gap-3">
              <label class="btn-secondary cursor-pointer text-sm">
                <Upload class="w-4 h-4" /> {{ formFor(a).file_url ? 'File attached ✓' : 'Attach file' }}
                <input type="file" class="hidden" @change="onSubmissionFile(a, $event)" />
              </label>
              <a v-if="safeUrl(formFor(a).file_url)" :href="safeUrl(formFor(a).file_url)" rel="noopener noreferrer" target="_blank" class="text-xs text-brand-700 hover:underline">View attached file</a>
              <button class="btn-primary text-sm ml-auto" :disabled="submitting === a.id" @click="submitAssignment(a)">
                <Send class="w-3.5 h-3.5" /> {{ submitting === a.id ? 'Submitting…' : 'Submit' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- announcements -->
      <div v-else-if="tab === 'live'">
        <div class="flex items-center justify-between gap-3 mb-4">
          <h3 class="font-bold text-slate-800">Live classes</h3>
          <NuxtLink v-if="course.can_manage" :to="`/teach/courses/${course.id}/live`" class="btn-secondary text-sm">Schedule a class</NuxtLink>
        </div>
        <LiveSessionList :course-id="course.id" />
      </div>

      <div v-else-if="tab === 'announcements'" class="space-y-4">
        <EmptyState v-if="announcements.length === 0" empty>No announcements yet.</EmptyState>
        <div v-for="a in announcements" :key="a.id" class="card p-5 flex gap-4">
          <div class="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center shrink-0">
            <Megaphone class="w-5 h-5 text-amber-500" />
          </div>
          <div>
            <h4 class="font-bold text-slate-800">{{ a.title }}</h4>
            <p class="text-sm text-slate-600 mt-1 whitespace-pre-wrap">{{ a.body }}</p>
            <p class="text-xs text-slate-400 mt-2">{{ formatDate(a.created_at) }}</p>
          </div>
        </div>
      </div>

      <!-- reviews -->
      <div v-else-if="tab === 'reviews'" class="space-y-6">
        <div v-if="course.is_enrolled && !course.has_reviewed" class="card p-5">
          <h3 class="font-bold text-slate-800 mb-3">Rate this course</h3>
          <div class="flex gap-1 mb-3">
            <button v-for="i in 5" :key="i" @click="myReview.rating = i" aria-label="rate">
              <Star class="w-7 h-7 transition" :class="i <= myReview.rating ? 'fill-amber-400 text-amber-400' : 'text-slate-300'" />
            </button>
          </div>
          <textarea v-model="myReview.comment" class="input min-h-[70px]" placeholder="Share your experience (optional)…" />
          <button class="btn-primary mt-3" @click="submitReview">Submit review</button>
        </div>

        <EmptyState v-if="reviews.length === 0" empty>No reviews yet.</EmptyState>
        <div v-for="r in reviews" :key="r.id" class="card p-5 flex gap-4">
          <div class="w-10 h-10 rounded-full bg-brand-50 text-brand-700 flex items-center justify-center font-bold uppercase shrink-0">
            {{ r.user.full_name.slice(0, 1) }}
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-2 flex-wrap">
              <b class="text-sm text-slate-800">{{ r.user.full_name }}</b>
              <RatingStars :rating="r.rating" size="w-3.5 h-3.5" />
            </div>
            <p class="text-sm text-slate-600 mt-1.5">{{ r.comment }}</p>
            <p class="text-xs text-slate-500 mt-2">{{ formatDate(r.created_at) }}</p>
          </div>
        </div>
      </div>
        </div>
      </div>

      <!-- price / action card: overlaps the hero and stays in view while scrolling (desktop) -->
      <aside class="order-1 lg:order-2 lg:-mt-[21rem] relative z-10">
        <div class="lg:sticky lg:top-24 card !bg-white overflow-hidden shadow-xl">
          <div class="aspect-video bg-slate-900">
            <VideoPlayer v-if="course.preview && !course.is_enrolled" :url="course.preview.video_url" class="!rounded-none" />
            <CourseCover v-else :title="course.title" :category="course.category?.name" :thumbnail-url="safeUrl(course.thumbnail_url)" icon-class="w-14 h-14" />
          </div>
          <div class="p-5">
            <p v-if="course.preview && !course.is_enrolled" class="text-xs text-slate-500 -mt-1 mb-3">▶ Free preview: {{ course.preview.title }}</p>
            <div v-if="!course.is_enrolled && !course.can_manage" class="flex items-baseline gap-2 mb-4">
              <span class="text-3xl font-extrabold text-slate-900">{{ money(course.price) }}</span>
              <span v-if="!isPaid" class="text-sm text-slate-500">No card needed</span>
            </div>

            <template v-if="course.is_enrolled">
              <p class="text-sm text-slate-600 mb-3">You're enrolled in this course.</p>
              <NuxtLink :to="`/learn/${course.slug}`" class="btn-primary w-full py-3"><PlayCircle class="w-5 h-5" /> Continue learning</NuxtLink>
            </template>
            <NuxtLink v-else-if="course.can_manage" :to="`/teach/courses/${course.id}/edit`" class="btn-secondary w-full py-3">Manage this course</NuxtLink>
            <div v-else-if="course.prerequisites?.length && !course.prerequisites_met" class="rounded-xl bg-amber-50 border border-amber-200 p-3 text-sm text-amber-900">
              <p class="font-semibold flex items-center gap-1.5"><Lock class="w-4 h-4" /> Complete these first</p>
              <ul class="mt-2 space-y-1">
                <li v-for="p in course.prerequisites" :key="p.id" class="flex items-center gap-2">
                  <component :is="p.completed ? CheckCircle2 : Lock" class="w-3.5 h-3.5 shrink-0" :class="p.completed ? 'text-brand-600' : 'text-amber-600'" />
                  <NuxtLink :to="`/courses/${p.slug}`" class="hover:underline">{{ p.title }}</NuxtLink>
                </li>
              </ul>
            </div>
            <button v-else class="btn-primary w-full py-3 text-base" :disabled="enrolling" @click="primaryAction">{{ primaryLabel }}</button>

            <p v-if="!course.is_enrolled && !course.can_manage" class="mt-2 text-xs text-slate-500 text-center">{{ primaryHint }}</p>

            <ul class="mt-5 pt-4 border-t border-slate-100 space-y-2.5 text-sm text-slate-700">
              <li class="flex gap-2.5"><Clock class="w-4 h-4 text-brand-600 shrink-0 mt-0.5" /> {{ fmtMinutes(course.total_minutes) }} of content · {{ plural(course.lesson_count, 'lesson') }}</li>
              <li v-if="counts.quiz" class="flex gap-2.5"><BarChart3 class="w-4 h-4 text-brand-600 shrink-0 mt-0.5" /> {{ plural(counts.quiz, 'quiz', 'quizzes') }} with instant feedback</li>
              <li v-if="counts.file" class="flex gap-2.5"><FileDown class="w-4 h-4 text-brand-600 shrink-0 mt-0.5" /> {{ plural(counts.file, 'downloadable resource') }}</li>
              <li class="flex gap-2.5"><GraduationCap class="w-4 h-4 text-brand-600 shrink-0 mt-0.5" /> Certificate of completion</li>
              <li class="flex gap-2.5"><MessageSquare class="w-4 h-4 text-brand-600 shrink-0 mt-0.5" /> Q&amp;A with the instructor</li>
            </ul>
          </div>
        </div>
      </aside>
    </div>

    <!-- phones: price + action always in reach -->
    <div v-if="!course.is_enrolled && !course.can_manage && !(course.prerequisites?.length && !course.prerequisites_met)"
      class="lg:hidden fixed inset-x-0 bottom-0 z-40 bg-white/95 dark:bg-slate-900/95 backdrop-blur border-t border-slate-200 px-4 py-3 flex items-center gap-3"
      style="padding-bottom: max(0.75rem, env(safe-area-inset-bottom))">
      <div class="min-w-0">
        <div class="font-extrabold text-slate-900 leading-tight">{{ money(course.price) }}</div>
        <div class="text-xs text-slate-500 truncate">{{ fmtMinutes(course.total_minutes) }} · {{ plural(course.lesson_count, 'lesson') }}</div>
      </div>
      <button class="btn-primary flex-1 py-3" :disabled="enrolling" @click="primaryAction">{{ primaryLabel }}</button>
    </div>

    <!-- request access (paid course while online payment is off) -->
    <Modal :open="requestOpen" title="Request access" @close="requestOpen = false">
      <div v-if="requestSent" class="py-6 text-center">
        <CheckCircle2 class="w-12 h-12 text-brand-500 mx-auto" />
        <p class="mt-3 font-bold text-slate-900">Request sent</p>
        <p class="mt-1 text-sm text-slate-600">We'll contact you with payment details, then enroll you in <b>{{ course.title }}</b>.</p>
      </div>
      <form v-else class="space-y-3" @submit.prevent="sendRequest">
        <p class="text-sm text-slate-600">Online payment isn't available for this course yet. Leave your details and our team will help you enroll.</p>
        <div><label class="label" for="ra-name">Name</label><input id="ra-name" v-model="requestForm.name" class="input" required /></div>
        <div class="grid sm:grid-cols-2 gap-3">
          <div><label class="label" for="ra-email">Email</label><input id="ra-email" v-model="requestForm.email" type="email" class="input" required /></div>
          <div><label class="label" for="ra-phone">Phone <span class="font-normal text-slate-400">(optional)</span></label><input id="ra-phone" v-model="requestForm.phone" type="tel" class="input" /></div>
        </div>
        <div><label class="label" for="ra-msg">Message</label><textarea id="ra-msg" v-model="requestForm.message" rows="3" class="input" /></div>
        <button class="btn-primary w-full" :disabled="requestSending">{{ requestSending ? 'Sending…' : 'Send request' }}</button>
      </form>
    </Modal>

    <!-- thread detail modal -->
    <Modal :open="!!openThread" :title="openThread?.title || 'Discussion'" wide @close="closeThread">
      <div v-if="threadLoading && !openThread" class="h-40 animate-pulse bg-slate-100 rounded-lg" />
      <div v-else-if="openThread" class="space-y-4">
        <div class="flex items-center justify-between flex-wrap gap-2">
          <div class="flex items-center gap-2 text-xs text-slate-400">
            <button class="btn-ghost text-xs !px-2" @click="closeThread"><ArrowLeft class="w-3.5 h-3.5" /> All threads</button>
            <span v-if="openThread.is_pinned" class="badge bg-amber-50 text-amber-700">📌 Pinned</span>
            <span v-if="openThread.is_locked" class="badge bg-slate-100 text-slate-500">🔒 Locked</span>
          </div>
          <div v-if="openThread.can_moderate" class="flex items-center gap-1">
            <button class="btn-ghost text-xs !px-2" @click="togglePin">
              <Pin v-if="!openThread.is_pinned" class="w-3.5 h-3.5" /><PinOff v-else class="w-3.5 h-3.5" />
              {{ openThread.is_pinned ? 'Unpin' : 'Pin' }}
            </button>
            <button class="btn-ghost text-xs !px-2" @click="toggleLock">
              <Lock v-if="!openThread.is_locked" class="w-3.5 h-3.5" /><Unlock v-else class="w-3.5 h-3.5" />
              {{ openThread.is_locked ? 'Unlock' : 'Lock' }}
            </button>
            <button class="btn-ghost text-xs !px-2 text-rose-600 hover:!bg-rose-50" @click="deleteThread">
              <Trash2 class="w-3.5 h-3.5" /> Delete
            </button>
          </div>
        </div>

        <!-- original question -->
        <div class="flex gap-3">
          <div class="w-9 h-9 rounded-full bg-brand-50 text-brand-700 flex items-center justify-center font-bold uppercase text-sm shrink-0">
            {{ openThread.author.full_name.slice(0, 1) }}
          </div>
          <div class="min-w-0">
            <div class="text-sm">
              <b class="text-slate-800">{{ openThread.author.full_name }}</b>
              <span v-if="openThread.author.role === 'instructor'" class="badge bg-brand-50 text-brand-700 ml-1.5">Instructor</span>
              <span class="text-slate-400 ml-2 text-xs">{{ formatDate(openThread.created_at) }}</span>
            </div>
            <p class="text-sm text-slate-600 mt-1 whitespace-pre-wrap">{{ openThread.body }}</p>
          </div>
        </div>

        <!-- replies -->
        <div v-if="openThread.posts?.length" class="space-y-3 border-l-2 border-slate-100 ml-4 pl-4">
          <div v-for="p in openThread.posts" :key="p.id" class="flex gap-3">
            <div class="w-8 h-8 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center font-bold uppercase text-xs shrink-0">
              {{ p.author.full_name.slice(0, 1) }}
            </div>
            <div class="min-w-0">
              <div class="text-sm">
                <b class="text-slate-700">{{ p.author.full_name }}</b>
                <span v-if="p.author.role === 'instructor'" class="badge bg-brand-50 text-brand-700 ml-1.5">Instructor</span>
                <span class="text-slate-400 ml-2 text-xs">{{ formatDate(p.created_at) }}</span>
              </div>
              <p class="text-sm text-slate-600 mt-0.5 whitespace-pre-wrap">{{ p.body }}</p>
            </div>
          </div>
        </div>
        <p v-else class="text-sm text-slate-400 ml-4">No replies yet.</p>

        <!-- reply box -->
        <div v-if="!openThread.is_locked || openThread.can_moderate" class="border-t border-slate-100 pt-4">
          <textarea v-model="replyText" class="input min-h-[70px]" placeholder="Write a reply…" />
          <button class="btn-primary mt-2 text-sm" :disabled="replyPosting || !replyText.trim()" @click="sendReply">
            <Send class="w-3.5 h-3.5" /> {{ replyPosting ? 'Posting…' : 'Post reply' }}
          </button>
        </div>
        <p v-else class="text-xs text-slate-400 border-t border-slate-100 pt-4">This thread is locked - new replies are disabled.</p>
      </div>
    </Modal>
  </div>
</template>
