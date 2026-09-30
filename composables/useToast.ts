export const useToast = () => {
  const toasts = useState<{ id: number; message: string; type: 'success' | 'error' | 'info' }[]>('toasts', () => [])
  let counter = 0

  const show = (message: string, type: 'success' | 'error' | 'info' = 'success') => {
    const id = ++counter + Date.now()
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, 3500)
  }
  return { toasts, show }
}
