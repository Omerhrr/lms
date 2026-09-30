<template>
  <footer class="mt-auto bg-slate-900 text-slate-400">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 py-10 grid gap-8 md:grid-cols-3">
      <div>
        <div class="flex items-center gap-2.5">
          <img src="/logo.svg" alt="LearnHub" class="w-8 h-8" />
          <span class="text-lg font-extrabold text-white">Learn<span class="text-brand-400">Hub</span></span>
        </div>
        <p class="mt-3 text-sm leading-relaxed max-w-xs">
          The complete learning management platform — create courses, enroll students, grade assessments and celebrate achievements.
        </p>
      </div>
      <div>
        <div class="text-sm font-semibold text-white mb-3">Platform</div>
        <ul class="space-y-2 text-sm">
          <li><NuxtLink to="/courses" class="hover:text-white transition">Browse courses</NuxtLink></li>
          <li><NuxtLink to="/register" class="hover:text-white transition">Become a student</NuxtLink></li>
          <li><NuxtLink to="/register?role=instructor" class="hover:text-white transition">Teach on LearnHub</NuxtLink></li>
          <li><NuxtLink to="/verify" class="hover:text-white transition">Verify a certificate</NuxtLink></li>
        </ul>
      </div>
      <div>
        <div class="text-sm font-semibold text-white mb-3">Demo accounts</div>
        <ul class="space-y-1.5 text-xs font-mono bg-slate-800/60 rounded-lg p-3">
          <li>admin@learnhub.io / Admin123!</li>
          <li>sarah@learnhub.io / Teach123!</li>
          <li>emma@example.com / Study123!</li>
        </ul>
      </div>
    </div>
    <div class="border-t border-slate-800 py-4 text-center text-xs">
      © {{ new Date().getFullYear() }} LearnHub LMS — built with Nuxt + FastAPI + SQLAlchemy
    </div>
  </footer>
</template>
