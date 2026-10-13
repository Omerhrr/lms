<script setup lang="ts">
import { Mail, Phone, MapPin, Clock, Send, CheckCircle2 } from 'lucide-vue-next'

useSeoMeta({ title: 'Contact Us - Infohive Technology Ltd.', description: "Have a project, training need, partnership opportunity, or question? Let's talk." })

const route = useRoute()
const api = useApi()
const { show } = useToast()
const { config } = usePlatform()
const { content: site } = useSiteContent()

const topics = computed(() => config.value.enquiry_topics?.length ? config.value.enquiry_topics : [
  'Technology / Software Project', 'Web Development', 'IT Consulting', 'Digital Transformation',
  'Corporate Training', 'LMS / Learning Enquiry', 'Partnership', 'General Enquiry'])
const initialTopic = String(route.query.topic || '')
const form = ref({ name: '', email: '', phone: '', topic: topics.value.includes(initialTopic) ? initialTopic : 'General Enquiry', subject: '', message: '', website: '' })
const sending = ref(false)
const sent = ref(false)

const submit = async () => {
  const f = form.value
  if (f.name.trim().length < 2) return show('Please tell us your name', 'error')
  if (!/^\S+@\S+\.\S+$/.test(f.email)) return show('Please enter a valid email address', 'error')
  if (f.message.trim().length < 10) return show('Please add a little more detail to your message', 'error')
  sending.value = true
  try {
    await api.post('/contact', { ...f, phone: f.phone || null })
    sent.value = true
  } catch { /* toast shown */ } finally { sending.value = false }
}
const contact = computed(() => config.value.contact || {})
const hasDetails = computed(() => Object.values(contact.value).some(Boolean))
</script>

<template>
  <div>
    <PageHero eyebrow="Contact Us" :title="site?.contact.hero_title || 'Let\'s Talk'" :lead="site?.contact.hero_lead" />

    <section class="mx-auto px-4 sm:px-6 py-10 lg:py-14 grid gap-8" :class="hasDetails ? 'max-w-7xl lg:grid-cols-[1.6fr_1fr]' : 'max-w-3xl'">
      <div class="card p-6 sm:p-8">
        <div v-if="sent" class="py-12 text-center">
          <CheckCircle2 class="w-14 h-14 text-brand-500 mx-auto" />
          <h2 class="mt-3 text-xl font-extrabold text-slate-900">Message sent - thank you!</h2>
          <p class="mt-2 text-slate-600">We've emailed you a confirmation and our team will get back to you shortly.</p>
          <div class="mt-6 flex flex-wrap justify-center gap-3">
            <NuxtLink to="/lms" class="btn-primary">Start Learning</NuxtLink>
            <NuxtLink to="/services" class="btn-secondary">Our Services</NuxtLink>
          </div>
        </div>
        <form v-else class="space-y-4" novalidate @submit.prevent="submit">
          <h2 class="text-lg font-extrabold text-slate-900">Send us a message</h2>
          <fieldset>
            <legend class="label">What can we help with?</legend>
            <div class="flex flex-wrap gap-2" role="radiogroup">
              <button v-for="t in topics" :key="t" type="button" role="radio" :aria-checked="form.topic === t" @click="form.topic = t"
                class="px-3 py-2 rounded-full border text-sm font-medium transition"
                :class="form.topic === t ? 'bg-brand-600 border-brand-600 text-white' : 'border-slate-300 text-slate-700 hover:border-brand-500'">{{ t }}</button>
            </div>
          </fieldset>
          <div class="grid sm:grid-cols-2 gap-4">
            <div><label class="label" for="c-name">Name</label><input id="c-name" v-model="form.name" class="input" autocomplete="name" required /></div>
            <div><label class="label" for="c-email">Email Address</label><input id="c-email" v-model="form.email" type="email" class="input" autocomplete="email" required /></div>
            <div><label class="label" for="c-phone">Phone Number <span class="text-slate-500 font-normal">(optional)</span></label><input id="c-phone" v-model="form.phone" type="tel" class="input" autocomplete="tel" /></div>
          </div>
          <div><label class="label" for="c-subject">Subject</label><input id="c-subject" v-model="form.subject" class="input" maxlength="255" /></div>
          <div><label class="label" for="c-msg">Message</label><textarea id="c-msg" v-model="form.message" rows="6" class="input" maxlength="5000" required /></div>
          <!-- honeypot for bots: hidden from people and screen readers -->
          <div class="hidden" aria-hidden="true"><label>Website<input v-model="form.website" tabindex="-1" autocomplete="off" /></label></div>
          <button class="btn-primary px-6 py-3" :disabled="sending"><Send class="w-4 h-4" /> {{ sending ? 'Sending…' : 'Send Message' }}</button>
        </form>
      </div>

      <!-- contact details only when there are some to show -->
      <aside v-if="hasDetails" class="card p-6 h-fit">
        <h2 class="text-lg font-extrabold text-slate-900">Other ways to reach us</h2>
        <ul class="mt-4 space-y-3 text-sm text-slate-700">
          <li v-if="contact.email" class="flex gap-3"><Mail class="w-4.5 h-4.5 text-brand-600 shrink-0 mt-0.5" /><a :href="`mailto:${contact.email}`" class="hover:text-brand-700 break-all">{{ contact.email }}</a></li>
          <li v-if="contact.phone" class="flex gap-3"><Phone class="w-4.5 h-4.5 text-brand-600 shrink-0 mt-0.5" /><a :href="`tel:${contact.phone.replace(/\s/g, '')}`" class="hover:text-brand-700">{{ contact.phone }}</a></li>
          <li v-if="contact.address" class="flex gap-3"><MapPin class="w-4.5 h-4.5 text-brand-600 shrink-0 mt-0.5" /><span>{{ contact.address }}</span></li>
          <li v-if="contact.hours" class="flex gap-3"><Clock class="w-4.5 h-4.5 text-brand-600 shrink-0 mt-0.5" /><span>{{ contact.hours }}</span></li>
        </ul>
      </aside>
    </section>

    <section class="max-w-7xl mx-auto px-4 sm:px-6 pb-16">
      <div class="rounded-3xl bg-gradient-to-br from-brand-600 to-brand-800 text-white p-8 sm:p-12">
        <h2 class="text-2xl sm:text-3xl font-extrabold tracking-tight max-w-3xl">Let's use technology and knowledge to create something better.</h2>
        <p class="mt-3 text-brand-50 max-w-3xl leading-relaxed">Whether you are looking to build a digital solution, transform your organization, train your team, or develop your own skills, Infohive Technology Ltd. is ready to work with you.</p>
        <div class="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3">
          <NuxtLink to="/lms" class="btn btn-light px-5 py-2.5 font-bold">Start Learning</NuxtLink>
          <NuxtLink to="/services" class="font-semibold text-white hover:underline">See our services →</NuxtLink>
        </div>
      </div>
    </section>
  </div>
</template>
