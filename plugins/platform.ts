// Fetch public platform settings (currency, payments on/off) once per visit.
export default defineNuxtPlugin(async () => {
  await usePlatform().load()
})
