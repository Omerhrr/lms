<script setup lang="ts">
/**
 * Renders lesson text. New lessons are HTML from the rich editor (sanitized by the API with an
 * allow-list, so v-html is safe here). Older lessons are plain text with light markup:
 * "# " / "## " headings, "- " bullets, ``` fenced code blocks and `inline code`.
 */
const props = defineProps<{ content: string }>()

const isHtml = computed(() => /<\w+[^>]*>/.test(props.content || ''))
// editors leave empty paragraphs (<p></p>, <p><br></p>) that show up as blank lines
const cleanHtml = computed(() => (props.content || '').replace(/<p>(\s|&nbsp;|<br\s*\/?>)*<\/p>/gi, '').trim())

interface Inline { code: boolean; text: string }
interface Block { type: 'h1' | 'h2' | 'ul' | 'p' | 'pre'; text?: string; items?: string[] }

/** split `code` spans so they can be rendered as <code> without v-html */
const inline = (text = ''): Inline[] =>
  text.split(/(`[^`]+`)/g).filter(Boolean).map(t => (t.startsWith('`') && t.endsWith('`') && t.length > 2
    ? { code: true, text: t.slice(1, -1) } : { code: false, text: t }))

const blocks = computed<Block[]>(() => {
  if (isHtml.value) return []
  const out: Block[] = []
  let list: string[] | null = null
  let code: string[] | null = null
  const flushList = () => { if (list?.length) out.push({ type: 'ul', items: list }); list = null }
  for (const raw of (props.content || '').replace(/\r\n/g, '\n').split('\n')) {
    if (raw.trim().startsWith('```')) {
      if (code) { out.push({ type: 'pre', text: code.join('\n') }); code = null }
      else { flushList(); code = [] }
      continue
    }
    if (code) { code.push(raw); continue }          // keep indentation inside code
    const line = raw.trim()
    if (!line) { flushList(); continue }
    if (line.startsWith('- ')) { (list ||= []).push(line.slice(2)); continue }
    flushList()
    if (line.startsWith('## ')) out.push({ type: 'h2', text: line.slice(3) })
    else if (line.startsWith('# ')) out.push({ type: 'h1', text: line.slice(2) })
    else out.push({ type: 'p', text: line })
  }
  if (code) out.push({ type: 'pre', text: code.join('\n') })
  flushList()
  return out
})
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div v-if="isHtml" class="rich-text inherit-color" v-html="cleanHtml" />
  <div v-else class="rich-text inherit-color">
    <template v-for="(b, i) in blocks" :key="i">
      <h2 v-if="b.type === 'h2'">{{ b.text }}</h2>
      <h1 v-else-if="b.type === 'h1'">{{ b.text }}</h1>
      <pre v-else-if="b.type === 'pre'"><code>{{ b.text }}</code></pre>
      <ul v-else-if="b.type === 'ul'">
        <li v-for="(it, j) in b.items" :key="j"><template v-for="(s, k) in inline(it)" :key="k"><code v-if="s.code">{{ s.text }}</code><template v-else>{{ s.text }}</template></template></li>
      </ul>
      <p v-else><template v-for="(s, k) in inline(b.text)" :key="k"><code v-if="s.code">{{ s.text }}</code><template v-else>{{ s.text }}</template></template></p>
    </template>
  </div>
</template>

<style scoped>
.inherit-color { color: inherit; overflow-wrap: anywhere; }
.inherit-color > :first-child { margin-top: 0; }
.inherit-color > :last-child { margin-bottom: 0; }
.inherit-color :deep(h1), .inherit-color :deep(h2), .inherit-color :deep(h3) { color: inherit; }
.inherit-color :deep(p), .inherit-color :deep(li) { color: inherit; }
.inherit-color :deep(img) { max-width: 100%; height: auto; border-radius: 0.75rem; margin: 1rem 0; }
.inherit-color :deep(pre) { overflow-x: auto; overflow-wrap: normal; white-space: pre; }
.inherit-color :deep(pre code) { background: transparent; padding: 0; color: inherit; }
.inherit-color :deep(a) { text-decoration: underline; }
</style>
