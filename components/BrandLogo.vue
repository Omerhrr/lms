<script setup lang="ts">
/** Infohive logo mark + wordmark. `dark` = on a dark background. */
withDefaults(defineProps<{ size?: 'sm' | 'md' | 'lg'; dark?: boolean; tagline?: boolean }>(), { size: 'md' })
</script>

<template>
  <span class="inline-flex items-center gap-2.5">
    <img src="/logo.svg" alt="" aria-hidden="true"
      :class="size === 'sm' ? 'w-8 h-8' : size === 'lg' ? 'w-11 h-11' : 'w-9 h-9'" />
    <span class="leading-none">
      <span class="block font-extrabold tracking-tight"
        :class="[size === 'sm' ? 'text-lg' : size === 'lg' ? 'text-2xl' : 'text-xl', dark ? 'text-white' : 'text-slate-900 dark:text-white']">
        Info<span :class="dark ? 'text-brand-400' : 'text-brand-600 dark:text-brand-400'">hive</span>
      </span>
      <span v-if="tagline" class="block text-xs uppercase tracking-[0.18em] mt-1"
        :class="dark ? 'text-slate-400' : 'text-slate-500'">Technology Ltd.</span>
    </span>
  </span>
</template>
