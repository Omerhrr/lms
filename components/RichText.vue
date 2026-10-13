<script setup lang="ts">
/**
 * Renders lesson text. New lessons are HTML from the rich editor (sanitized by the API with an
 * allow-list, so v-html is safe here). Older lessons are plain text with "#"/"-" markup.
 */
const props = defineProps<{ content: string }>()

const isHtml = computed(() => /<\w+[^>]*>/.test(props.content || ''))

interface Block { type: 'h1' | 'h2' | 'ul' | 'p'; text?: string; items?: string[] }

const blocks = computed<Block[]>(() => {
  if (isHtml.value) return []
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
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div v-if="isHtml" class="rich-text inherit-color" v-html="content" />
  <div v-else class="rich-text inherit-color">
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
.inherit-color { color: inherit; overflow-wrap: anywhere; }
.inherit-color :deep(h1), .inherit-color :deep(h2), .inherit-color :deep(h3) { color: inherit; }
.inherit-color :deep(p), .inherit-color :deep(li) { color: inherit; }
.inherit-color :deep(img) { max-width: 100%; height: auto; border-radius: 0.75rem; margin: 1rem 0; }
.inherit-color :deep(pre) { overflow-x: auto; }
.inherit-color :deep(a) { text-decoration: underline; }
</style>
