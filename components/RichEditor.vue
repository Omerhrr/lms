<script setup lang="ts">
/** WYSIWYG lesson editor (Tiptap). Emits sanitizable HTML; the API cleans it again on save. */
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import {
  Bold, Italic, Strikethrough, Heading2, Heading3, List, ListOrdered, Quote, Code2,
  Link2, ImagePlus, Minus, Undo2, Redo2
} from 'lucide-vue-next'

const props = defineProps<{ modelValue: string; placeholder?: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()
const api = useApi()
const { show } = useToast()

/** Old lessons were plain text with "#"/"-" markup; convert them once so nothing is lost. */
const legacyToHtml = (text: string) => {
  if (!text || /<\w+[^>]*>/.test(text)) return text || ''
  const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  const out: string[] = []
  let list: string[] = []
  const flush = () => { if (list.length) out.push(`<ul>${list.map(i => `<li>${esc(i)}</li>`).join('')}</ul>`); list = [] }
  for (const raw of text.split('\n')) {
    const line = raw.trim()
    if (!line) { flush(); continue }
    if (line.startsWith('- ')) { list.push(line.slice(2)); continue }
    flush()
    if (line.startsWith('## ')) out.push(`<h3>${esc(line.slice(3))}</h3>`)
    else if (line.startsWith('# ')) out.push(`<h2>${esc(line.slice(2))}</h2>`)
    else out.push(`<p>${esc(line)}</p>`)
  }
  flush()
  return out.join('')
}

const editor = useEditor({
  content: legacyToHtml(props.modelValue),
  extensions: [
    StarterKit.configure({
      heading: { levels: [2, 3] },
      link: { openOnClick: false, autolink: true, protocols: ['http', 'https', 'mailto'],
              HTMLAttributes: { rel: 'noopener noreferrer nofollow', target: '_blank' } },
    }),
    Image.configure({ inline: false }),
    Placeholder.configure({ placeholder: props.placeholder || 'Write your lesson…' }),
  ],
  editorProps: { attributes: { class: 'rich-text prose-editor focus:outline-none min-h-[220px] px-4 py-3' } },
  onUpdate: ({ editor }) => emit('update:modelValue', editor.isEmpty ? '' : editor.getHTML()),
})

watch(() => props.modelValue, (v) => {
  const e = editor.value
  if (e && v !== e.getHTML() && !(v === '' && e.isEmpty)) e.commands.setContent(legacyToHtml(v), { emitUpdate: false })
})
onBeforeUnmount(() => editor.value?.destroy())

const setLink = () => {
  const e = editor.value
  if (!e) return
  const prev = e.getAttributes('link').href || 'https://'
  const url = window.prompt('Link address (leave empty to remove)', prev)
  if (url === null) return
  if (!url.trim()) return e.chain().focus().unsetLink().run()
  if (!/^(https?:\/\/|mailto:)/i.test(url.trim())) return show('Links must start with https:// or mailto:', 'error')
  e.chain().focus().extendMarkRange('link').setLink({ href: url.trim() }).run()
}

const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
const addImage = async (ev: Event) => {
  const file = (ev.target as HTMLInputElement).files?.[0]
  if (!file) return
  uploading.value = true
  try {
    const res = await api.upload(file)
    editor.value?.chain().focus().setImage({ src: res.url, alt: file.name }).run()
  } catch { /* toast already shown */ } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

const tools = computed(() => {
  const e = editor.value
  if (!e) return []
  return [
    { icon: Bold, label: 'Bold', run: () => e.chain().focus().toggleBold().run(), active: e.isActive('bold') },
    { icon: Italic, label: 'Italic', run: () => e.chain().focus().toggleItalic().run(), active: e.isActive('italic') },
    { icon: Strikethrough, label: 'Strikethrough', run: () => e.chain().focus().toggleStrike().run(), active: e.isActive('strike') },
    { sep: true },
    { icon: Heading2, label: 'Heading', run: () => e.chain().focus().toggleHeading({ level: 2 }).run(), active: e.isActive('heading', { level: 2 }) },
    { icon: Heading3, label: 'Subheading', run: () => e.chain().focus().toggleHeading({ level: 3 }).run(), active: e.isActive('heading', { level: 3 }) },
    { icon: List, label: 'Bullet list', run: () => e.chain().focus().toggleBulletList().run(), active: e.isActive('bulletList') },
    { icon: ListOrdered, label: 'Numbered list', run: () => e.chain().focus().toggleOrderedList().run(), active: e.isActive('orderedList') },
    { icon: Quote, label: 'Quote', run: () => e.chain().focus().toggleBlockquote().run(), active: e.isActive('blockquote') },
    { icon: Code2, label: 'Code block', run: () => e.chain().focus().toggleCodeBlock().run(), active: e.isActive('codeBlock') },
    { icon: Minus, label: 'Divider', run: () => e.chain().focus().setHorizontalRule().run(), active: false },
    { sep: true },
    { icon: Link2, label: 'Link', run: setLink, active: e.isActive('link') },
    { icon: ImagePlus, label: 'Image', run: () => fileInput.value?.click(), active: false },
    { sep: true },
    { icon: Undo2, label: 'Undo', run: () => e.chain().focus().undo().run(), active: false },
    { icon: Redo2, label: 'Redo', run: () => e.chain().focus().redo().run(), active: false },
  ]
})
</script>

<template>
  <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 overflow-hidden focus-within:ring-2 focus-within:ring-brand-500/40">
    <div class="flex flex-wrap items-center gap-0.5 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/60 px-1.5 py-1">
      <template v-for="(t, i) in tools" :key="i">
        <span v-if="t.sep" class="w-px h-5 bg-slate-200 dark:bg-slate-700 mx-1" />
        <button v-else type="button" :title="t.label" :aria-label="t.label" @click="t.run"
          class="p-1.5 rounded-md text-slate-600 dark:text-slate-300 hover:bg-white dark:hover:bg-slate-700 transition"
          :class="t.active ? '!bg-brand-100 !text-brand-700 dark:!bg-brand-900/50 dark:!text-brand-300' : ''">
          <component :is="t.icon" class="w-4 h-4" />
        </button>
      </template>
      <span v-if="uploading" class="ml-2 text-xs text-slate-400">Uploading image…</span>
      <input ref="fileInput" type="file" accept="image/png,image/jpeg,image/gif,image/webp" class="hidden" @change="addImage" />
    </div>
    <EditorContent :editor="editor" class="max-h-[50vh] overflow-y-auto nice-scroll text-slate-800 dark:text-slate-100" />
  </div>
</template>

<style>
.prose-editor p.is-editor-empty:first-child::before {
  content: attr(data-placeholder); float: left; height: 0; pointer-events: none; color: #94a3b8;
}
</style>
