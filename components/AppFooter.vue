<script setup lang="ts">
import { Facebook, Linkedin, Instagram, Twitter, Mail, Phone, MapPin } from 'lucide-vue-next'

const { config } = usePlatform()
const socials = computed(() => {
  const s = config.value.social || {}
  return [
    { key: 'facebook', label: 'Facebook', icon: Facebook, url: s.facebook },
    { key: 'linkedin', label: 'LinkedIn', icon: Linkedin, url: s.linkedin },
    { key: 'instagram', label: 'Instagram', icon: Instagram, url: s.instagram },
    { key: 'x', label: 'X', icon: Twitter, url: s.x },
  ].filter(x => x.url)
})
const contact = computed(() => config.value.contact || {})
</script>

<template>
  <footer class="mt-auto bg-slate-900 dark:bg-black/40 border-t border-slate-900 dark:border-slate-800 text-slate-400">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 py-12 grid gap-10 sm:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1.2fr]">
      <div>
        <BrandLogo dark tagline />
        <p class="mt-4 text-sm font-semibold text-brand-300">Technology. Learning. Innovation. Growth.</p>
        <p class="mt-2 text-sm leading-relaxed max-w-xs">
          Technology solutions and digital learning designed to empower people and organizations.
        </p>
        <div v-if="socials.length" class="mt-4 flex gap-2">
          <a v-for="s in socials" :key="s.key" :href="s.url" target="_blank" rel="noopener noreferrer" :aria-label="s.label"
            class="w-9 h-9 rounded-lg bg-slate-800 hover:bg-brand-600 hover:text-white flex items-center justify-center transition">
            <component :is="s.icon" class="w-4 h-4" />
          </a>
        </div>
      </div>
      <div>
        <div class="text-sm font-semibold text-white mb-3">Quick links</div>
        <ul class="space-y-2 text-sm">
          <li><NuxtLink to="/" class="hover:text-white transition">Home</NuxtLink></li>
          <li><NuxtLink to="/about" class="hover:text-white transition">About Us</NuxtLink></li>
          <li><NuxtLink to="/services" class="hover:text-white transition">Services</NuxtLink></li>
          <li><NuxtLink to="/lms" class="hover:text-white transition">LMS / Courses</NuxtLink></li>
          <li><NuxtLink to="/contact" class="hover:text-white transition">Contact Us</NuxtLink></li>
        </ul>
      </div>
      <div>
        <div class="text-sm font-semibold text-white mb-3">Learning</div>
        <ul class="space-y-2 text-sm">
          <li><NuxtLink to="/courses" class="hover:text-white transition">Explore Courses</NuxtLink></li>
          <li><NuxtLink to="/login" class="hover:text-white transition">Login to LMS</NuxtLink></li>
          <li><NuxtLink to="/dashboard" class="hover:text-white transition">My Learning</NuxtLink></li>
          <li><NuxtLink to="/certificates" class="hover:text-white transition">Certificates</NuxtLink></li>
          <li><NuxtLink to="/verify" class="hover:text-white transition">Verify a certificate</NuxtLink></li>
        </ul>
      </div>
      <div>
        <div class="text-sm font-semibold text-white mb-3">Get in touch</div>
        <ul class="space-y-2.5 text-sm">
          <li v-if="contact.email" class="flex gap-2"><Mail class="w-4 h-4 mt-0.5 shrink-0" /><a :href="`mailto:${contact.email}`" class="hover:text-white break-all">{{ contact.email }}</a></li>
          <li v-if="contact.phone" class="flex gap-2"><Phone class="w-4 h-4 mt-0.5 shrink-0" /><a :href="`tel:${contact.phone.replace(/\s/g, '')}`" class="hover:text-white">{{ contact.phone }}</a></li>
          <li v-if="contact.address" class="flex gap-2"><MapPin class="w-4 h-4 mt-0.5 shrink-0" /><span>{{ contact.address }}</span></li>
          <li><NuxtLink to="/contact" class="btn-primary !py-2 text-sm mt-1 inline-flex">Contact us</NuxtLink></li>
        </ul>
      </div>
    </div>
    <div class="border-t border-slate-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex flex-col sm:flex-row gap-2 items-center justify-between text-xs">
        <span>© {{ new Date().getFullYear() }} Infohive Technology Ltd. All Rights Reserved.</span>
        <span class="flex gap-4">
          <NuxtLink to="/privacy" class="hover:text-white">Privacy Policy</NuxtLink>
          <NuxtLink to="/terms" class="hover:text-white">Terms &amp; Conditions</NuxtLink>
        </span>
      </div>
    </div>
  </footer>
</template>
