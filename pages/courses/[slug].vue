<script setup lang="ts">
import {
  Clock, Users, Globe, BarChart3, PlayCircle, CheckCircle2, FileDown, Star,
  GraduationCap, MessageSquare, Megaphone, Lock, Check, Eye
} from 'lucide-vue-next'

const route = useRoute()
const api = useApi()
const auth = useAuth()
const { show } = useToast()

const course = ref<any>(null)
const reviews = ref<any[]>([])
const threads = ref<any[]>([])
const announcements = ref<any[]>([])
const loading = ref(true)
const enrolling = ref(false)
const tab = ref<'overview' | 'curriculum' | 'discussion' | 'announcements' | 'reviews'>('overview')
const expanded = ref<Set<number>>(new Set())

const myReview = ref({ rating: 5, comment: '' })
const threadForm = ref({ title: '', body: '' })
const posting = ref(false)

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
    show(`You're enrolled in “${course.value.title}”! 🎉`)
    const firstLesson = firstPreviewableLesson()
    await load()
    if (firstLesson) navigateTo(`/learn/${course.value.slug}/${firstLesson.id}`)
  } catch (e: any) {
    show(e?.data?.detail || 'Could not enroll', 'error')
  } finally { enrolling.value = false }
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

const lessonIcon = (t: string) => (t === 'video' ? PlayCircle : t === 'quiz' ? BarChart3 : t === 'file' ? FileDown : FileText_)

import { FileText as FileText_ } from 'lucide-vue-next'

const submitReview = async () => {
  try {
    await api.post(`/courses/${course.value.slug}/reviews`, myReview.value)
    show('Thanks for your review! ⭐')
    reviews.value = await api.get<any[]>(`/courses/${route.params.slug}/reviews`)
    course.value.has_reviewed = true
  } catch (e: any) { show(e?.data?.detail || 'Could not submit review', 'error') }
}

const createThread = async () => {
  if (!threadForm.value.title.trim()) return show('Give your question a title', 'error')
  posting.value = true
  try {
    await api.post(`/courses/${course.value.id}/discussions`, threadForm.value)
    threadForm.value = { title: '', body: '' }
    threads.value = await api.get<any[]>(`/courses/${course.value.id}/discussions`)
    show('Question posted!')
  } catch (e: any) { show(e?.data?.detail || 'Could not post', 'error') } finally { posting.value = false }
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
          ...(course.is_enrolled || course.can_manage ? [['discussion', 'Q&A'], ['announcements', 'Announcements']] : []),
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
        <NuxtLink v-for="t in threads" :key="t.id" :to="`/courses/${course.slug}?tab=discussion`"
          @click.prevent="tab = 'discussion'"
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
        </NuxtLink>
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
  </div>
</template>
