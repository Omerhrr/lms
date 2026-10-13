// Fetch public platform settings (currency, payments on/off) and website copy once per visit.
export default defineNuxtPlugin(async () => {
  await Promise.all([usePlatform().load(), useSiteContent().load()])
})
