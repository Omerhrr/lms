<script setup lang="ts">
/** Lightweight renderer for lesson text: supports #/## headings, - bullets and paragraphs. Color-neutral (inherits). */
const props = defineProps<{ content: string }>()

interface Block { type: 'h1' | 'h2' | 'ul' | 'p'; text?: string; items?: string[] }

const blocks = computed<Block[]>(() => {
  const out: Block[] = []
  let list: string[] | null = null
  const flushList = () => {
    if (list && list.length) out.push({ type: 'ul', items: list })
    list = null
  }
  for (const raw of (props.content || '').split('\n')) {
    const line = raw.trim()
    if (!line) { flushList(); continue }
    if (line.startsWith('- ')) {
      if (!list) list = []
      list.push(line.slice(2))
      continue
    }
    flushList()
    if (line.startsWith('## ')) out.push({ type: 'h2', text: line.slice(3) })
    else if (line.startsWith('# ')) out.push({ type: 'h1', text: line.slice(2) })
    else out.push({ type: 'p', text: line })
  }
  flushList()
  return out
})
</script>

<template>
  <div class="rich-text inherit-color">
    <template v-for="(b, i) in blocks" :key="i">
      <h2 v-if="b.type === 'h2'">{{ b.text }}</h2>
      <h1 v-else-if="b.type === 'h1'">{{ b.text }}</h1>
      <ul v-else-if="b.type === 'ul'">
        <li v-for="(it, j) in b.items" :key="j">{{ it }}</li>
      </ul>
      <p v-else>{{ b.text }}</p>
    </template>
  </div>
</template>

<style scoped>
.inherit-color { color: inherit; }
.inherit-color :deep(h1), .inherit-color :deep(h2) { color: inherit; }
.inherit-color :deep(p), .inherit-color :deep(li) { color: inherit; }
</style>
