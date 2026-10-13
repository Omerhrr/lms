<script setup lang="ts">
/**
 * Course artwork. Uses the uploaded thumbnail when there is one; otherwise a branded cover whose
 * colour and icon come from the category, so courses are recognisable at a glance.
 */
import { Code2, Palette, Megaphone, BarChart3, Briefcase, GraduationCap, Cpu, ShieldCheck, Camera, HeartPulse, Languages, Calculator } from 'lucide-vue-next'

const props = defineProps<{ title: string; category?: string | null; thumbnailUrl?: string | null; iconClass?: string }>()

const THEMES = [
  { from: '#059669', to: '#064e3b', accent: '#fbbf24' },   // brand green
  { from: '#2563eb', to: '#1e3a8a', accent: '#93c5fd' },   // blue
  { from: '#7c3aed', to: '#3b0764', accent: '#f0abfc' },   // violet
  { from: '#ea580c', to: '#7c2d12', accent: '#fde68a' },   // orange
  { from: '#0891b2', to: '#164e63', accent: '#a5f3fc' },   // cyan
  { from: '#db2777', to: '#831843', accent: '#fbcfe8' },   // pink
  { from: '#4f46e5', to: '#1e1b4b', accent: '#c7d2fe' },   // indigo
]
const ICONS: [RegExp, any][] = [
  [/develop|program|code|software|web/i, Code2], [/design|ui|ux|art/i, Palette], [/market|sales|brand/i, Megaphone],
  [/data|analytic|excel|stat/i, BarChart3], [/business|entrepreneur|manage|leader/i, Briefcase],
  [/ai|machine|tech|it\b|cloud|network/i, Cpu], [/secur|cyber/i, ShieldCheck], [/photo|video|media/i, Camera],
  [/health|wellness/i, HeartPulse], [/language|english|french/i, Languages], [/finance|account|math/i, Calculator],
]
const key = computed(() => props.category || props.title || '')
const theme = computed(() => {
  let h = 0
  for (const c of key.value) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return THEMES[h % THEMES.length]
})
const icon = computed(() => ICONS.find(([re]) => re.test(key.value))?.[1] || GraduationCap)
const pattern = computed(() =>
  `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='42' height='73'%3E%3Cpath d='M21 49.5 0 37.5v-24L21 1.5l21 12v24zm0 24L0 61.5V49.5l21 12 21-12v12z' fill='none' stroke='%23ffffff' stroke-opacity='.12'/%3E%3C/svg%3E")`)
</script>

<template>
  <div class="relative w-full h-full overflow-hidden" :style="!thumbnailUrl ? `background: linear-gradient(135deg, ${theme.from}, ${theme.to})` : ''">
    <img v-if="thumbnailUrl" :src="thumbnailUrl" :alt="title" class="w-full h-full object-cover" loading="lazy" />
    <template v-else>
      <div class="absolute inset-0" :style="`background-image:${pattern}`" />
      <div class="absolute inset-0 flex items-center justify-center">
        <component :is="icon" :class="iconClass || 'w-12 h-12'" class="text-white/85 drop-shadow transition-transform duration-300 group-hover:scale-110" />
      </div>
    </template>
  </div>
</template>
