<script setup lang="ts">
import { Sun, Moon } from 'lucide-vue-next'

const { theme, toggle } = useTheme()
</script>

<template>
  <button
    @click="toggle"
    class="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-800 transition"
    :aria-label="theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'"
    :title="theme === 'dark' ? 'Light mode' : 'Dark mode'"
  >
    <Transition name="theme-icon" mode="out-in">
      <Sun v-if="theme === 'dark'" key="sun" class="w-5 h-5" />
      <Moon v-else key="moon" class="w-5 h-5" />
    </Transition>
  </button>
</template>
