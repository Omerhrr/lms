/**
 * Recognise a pasted video link. Supports YouTube (any URL form), Vimeo, and direct
 * video files (.mp4/.webm/.ogg, including our own /api/media/files uploads).
 */
export type VideoSource =
  | { kind: 'youtube'; id: string }
  | { kind: 'vimeo'; id: string; hash?: string }
  | { kind: 'file'; url: string }
  | null

export const parseVideoUrl = (raw?: string | null): VideoSource => {
  if (!raw) return null
  const value = raw.trim()
  if (/\.(mp4|webm|ogg|ogv|m4v|mov)(\?.*)?$/i.test(value) &&
      (/^https?:\/\//i.test(value) || value.startsWith('/api/media/files/'))) {
    return { kind: 'file', url: value }
  }
  let u: URL
  try { u = new URL(value) } catch { return null }
  const host = u.hostname.replace(/^www\.|^m\./, '')
  const ytId = (s?: string | null) => (s && /^[\w-]{11}$/.test(s) ? s : null)

  if (host === 'youtu.be') {
    const id = ytId(u.pathname.slice(1).split('/')[0])
    return id ? { kind: 'youtube', id } : null
  }
  if (host === 'youtube.com' || host === 'youtube-nocookie.com' || host === 'music.youtube.com') {
    const fromQuery = ytId(u.searchParams.get('v'))
    if (fromQuery) return { kind: 'youtube', id: fromQuery }
    const m = u.pathname.match(/^\/(embed|shorts|live|v)\/([\w-]{11})/)
    return m ? { kind: 'youtube', id: m[2] } : null
  }
  if (host === 'vimeo.com' || host === 'player.vimeo.com') {
    const m = u.pathname.match(/(?:\/video)?\/(\d+)(?:\/([\da-f]+))?/)
    return m ? { kind: 'vimeo', id: m[1], hash: m[2] || u.searchParams.get('h') || undefined } : null
  }
  return null
}

export const videoKindLabel = (src: VideoSource) =>
  !src ? null : src.kind === 'youtube' ? 'YouTube' : src.kind === 'vimeo' ? 'Vimeo' : 'Video file'
