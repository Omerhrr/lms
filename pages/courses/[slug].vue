<script setup lang="ts">
import {
  Clock, Users, Globe, BarChart3, PlayCircle, CheckCircle2, FileDown, Star,
  GraduationCap, MessageSquare, Megaphone, Lock, Check, Eye, FileText,
  ClipboardList, Upload, Send, Pin, PinOff, Unlock, Trash2, ArrowLeft
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
const tab = ref<'overview' | 'curriculum' | 'discussion' | 'assignments' | 'announcements' | 'reviews'>('overview')
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
    if (!course.value) { loading.value = false; return }
    if (auth.token.value) {
      await auth.fetchMe()
    }
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
      }
    } else {
      reviews.value = await api.get<any[]>(`/courses/${route.params.slug}/reviews`, undefined, true).catch(() => [])
    }
  } catch (e) {
    course.value = null
  } finally { loading.value = false }
}

const enroll = async () => {
  if (!auth.isLoggedIn.value) return navigateTo({ path: '/login', query: { redirect: route.fullPath } })
  enrolling.value = true
  try {
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

const canWatch = (l: any) => l.is_preview || course.value?.is_enrolled || course.value?.can_manage

const toggle = (sid: number) => {
  if (expanded.value.has(sid)) expanded.value.delete(sid)
  else expanded.value.add(sid)
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
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-12 grid lg:grid-cols-3 gap-10">
        <div class="lg:col-span-2">
          <div class="flex flex-wrap items-center gap-2 text-xs mb-4">
            <span v-if="course.category" class="badge bg-brand-500/20 text-brand-300 border border-brand-400/30">{{ course.category.name }}</span>
            <span class="badge bg-white/10 text-slate-300">{{ course.level }}</span>
            <span v-if="course.status !== 'published'" class="badge bg-amber-500/20 text-amber-300">{{ course.status }} (preview)</span>
          </div>
          <h1 class="text-3xl lg:text-4xl font-extrabold leading-tight">{{ course.title }}</h1>
          <p class="mt-4 text-slate-300 text-lg leading-relaxed">{{ course.summary }}</p>
          <div class="mt-5 flex flex-wrap items-center gap-5 text-sm text-slate-300">
            <span class="flex items-center gap-1.5"><RatingStars :rating="course.rating" size="w-4 h-4" />
              <b class="text-white">{{ course.rating || 'New' }}</b>&nbsp;({{ course.review_count }} reviews)</span>
            <span class="flex items-center gap-1.5"><Users class="w-4 h-4" /> {{ course.enrollment_count }} students</span>
            <span class="flex items-center gap-1.5"><Clock class="w-4 h-4" /> {{ Math.round(course.total_minutes / 60 * 10) / 10 }}h content</span>
            <span class="flex items-center gap-1.5"><Globe class="w-4 h-4" /> {{ course.language }}</span>
          </div>
          <div class="mt-5 flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-brand-600 flex items-center justify-center font-bold uppercase">
              {{ course.instructor.full_name.slice(0, 1) }}
            </div>
            <div>
              <div class="font-semibold text-sm">{{ course.instructor.full_name }}</div>
              <div class="text-xs text-slate-400">{{ course.instructor.headline || 'Instructor' }}</div>
            </div>
          </div>
        </div>

        <!-- enroll card -->
        <div class="lg:justify-self-end w-full max-w-sm">
          <div class="card !bg-white text-slate-800 overflow-hidden">
            <div class="h-40 bg-gradient-to-br from-brand-500 to-slate-800 relative flex items-center justify-center">
              <img v-if="course.thumbnail_url" :src="course.thumbnail_url" class="w-full h-full object-cover" alt="" />
              <GraduationCap v-else class="w-12 h-12 text-white/40" />
            </div>
            <div class="p-5">
              <div class="flex items-baseline gap-2 mb-4">
                <span class="text-3xl font-extrabold">{{ course.price === 0 ? 'Free' : `$${course.price.toFixed(2)}` }}</span>
                <span v-if="course.price === 0" class="badge bg-amber-100 text-amber-800">No credit card needed</span>
              </div>

              <template v-if="course.is_enrolled">
                <NuxtLink v-if="course.sections.length && course.sections[0].lessons.length"
                  :to="`/learn/${course.slug}/${course.sections[0].lessons[0].id}`" class="btn-primary w-full py-3">
                  <PlayCircle class="w-5 h-5" /> Go to course
                </NuxtLink>
              </template>
              <template v-else-if="course.can_manage">
                <NuxtLink :to="`/teach/courses/${course.id}/edit`" class="btn-secondary w-full py-3">Manage this course</NuxtLink>
              </template>
              <button v-else class="btn-primary w-full py-3 text-base" :disabled="enrolling" @click="enroll">
                {{ enrolling ? 'Enrolling…' : (course.price === 0 ? 'Enroll for free' : `Enroll now · $${course.price.toFixed(2)}`) }}
              </button>

              <ul class="mt-4 space-y-2 text-sm text-slate-600">
                <li class="flex gap-2"><CheckCircle2 class="w-4 h-4 text-brand-600 shrink-0" /> {{ course.lesson_count }} lessons across {{ course.sections.length }} sections</li>
                <li class="flex gap-2"><CheckCircle2 class="w-4 h-4 text-brand-600 shrink-0" /> Quizzes with instant auto-grading</li>
                <li class="flex gap-2"><CheckCircle2 class="w-4 h-4 text-brand-600 shrink-0" /> Certificate of completion</li>
                <li class="flex gap-2"><CheckCircle2 class="w-4 h-4 text-brand-600 shrink-0" /> Q&A discussion board</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- tabs -->
    <div class="bg-white border-b border-slate-200 sticky top-16 z-30">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 flex gap-1 overflow-x-auto">
        <button v-for="t in [
          ['overview', 'Overview'], ['curriculum', 'Curriculum'],
          ...(course.is_enrolled || course.can_manage ? [['discussion', 'Q&A'], ['assignments', 'Assignments'], ['announcements', 'Announcements']] : []),
          ['reviews', 'Reviews'],
        ]" :key="t[0]" @click="tab = t[0] as any"
          class="px-4 py-3.5 text-sm font-semibold border-b-2 transition whitespace-nowrap"
          :class="tab === t[0] ? 'border-brand-600 text-brand-700' : 'border-transparent text-slate-500 hover:text-slate-800'">
          {{ t[1] }}
        </button>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10 min-h-[300px]">
      <!-- overview -->
      <div v-if="tab === 'overview'" class="grid lg:grid-cols-3 gap-10">
        <div class="lg:col-span-2 rich-text text-slate-700" v-html="course.description || `<p>No description yet.</p>`" />
        <div class="card p-5 h-fit">
          <h3 class="font-bold text-slate-800 mb-3">Course details</h3>
          <ul class="space-y-3 text-sm text-slate-600">
            <li class="flex justify-between"><span class="text-slate-400">Level</span><b class="capitalize">{{ course.level }}</b></li>
            <li class="flex justify-between"><span class="text-slate-400">Language</span><b>{{ course.language }}</b></li>
            <li class="flex justify-between"><span class="text-slate-400">Lessons</span><b>{{ course.lesson_count }}</b></li>
            <li class="flex justify-between"><span class="text-slate-400">Duration</span><b>{{ Math.round(course.total_minutes / 60 * 10) / 10 }} hours</b></li>
            <li class="flex justify-between"><span class="text-slate-400">Category</span><b>{{ course.category?.name || '-' }}</b></li>
          </ul>
          <div v-if="course.tags?.length" class="mt-4 flex flex-wrap gap-1.5">
            <span v-for="t in course.tags" :key="t" class="badge bg-slate-100 text-slate-600">#{{ t }}</span>
          </div>
        </div>
      </div>

      <!-- curriculum -->
      <div v-else-if="tab === 'curriculum'" class="max-w-3xl mx-auto">
        <div class="space-y-3">
          <div v-for="s in course.sections" :key="s.id" class="card overflow-hidden">
            <button class="w-full flex items-center justify-between px-5 py-4 hover:bg-slate-50 transition" @click="toggle(s.id)">
              <span class="font-bold text-slate-800 text-left">{{ s.title }}
                <span class="ml-2 text-xs font-normal text-slate-400">{{ s.lessons.length }} lessons</span>
              </span>
              <component :is="expanded.has(s.id) ? Check : Eye" class="w-4 h-4 text-slate-400" />
            </button>
            <div v-if="expanded.has(s.id)" class="border-t border-slate-100 divide-y divide-slate-50">
              <div v-for="l in s.lessons" :key="l.id" class="flex items-center gap-3 px-5 py-3">
                <component :is="lessonIcon(l.type)" class="w-4.5 h-4.5 shrink-0" :class="canWatch(l) ? 'text-brand-600' : 'text-slate-300'" />
                <span class="text-sm flex-1" :class="canWatch(l) ? 'text-slate-700' : 'text-slate-400'">{{ l.title }}</span>
                <span v-if="l.is_preview" class="badge bg-brand-50 text-brand-700">Preview</span>
                <span class="text-xs text-slate-400">{{ l.duration_minutes }} min</span>
                <NuxtLink v-if="canWatch(l)" :to="`/learn/${course.slug}/${l.id}`"
                  class="text-xs font-semibold text-brand-700 hover:underline">Watch</NuxtLink>
                <Lock v-else class="w-3.5 h-3.5 text-slate-300" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- discussion -->
      <div v-else-if="tab === 'discussion'" class="max-w-3xl mx-auto space-y-6">
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
      <div v-else-if="tab === 'assignments'" class="max-w-3xl mx-auto space-y-5">
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
              <a v-if="formFor(a).file_url" :href="formFor(a).file_url" target="_blank" class="text-xs text-brand-700 hover:underline">View attached file</a>
              <button class="btn-primary text-sm ml-auto" :disabled="submitting === a.id" @click="submitAssignment(a)">
                <Send class="w-3.5 h-3.5" /> {{ submitting === a.id ? 'Submitting…' : 'Submit' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- announcements -->
      <div v-else-if="tab === 'announcements'" class="max-w-3xl mx-auto space-y-4">
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
      <div v-else-if="tab === 'reviews'" class="max-w-3xl mx-auto space-y-6">
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
            <p class="text-xs text-slate-400 mt-2">{{ formatDate(r.created_at) }}</p>
          </div>
        </div>
      </div>
    </div>

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
