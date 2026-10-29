export default defineNuxtPlugin(async () => {
  let isTzOutdated = true
  try {
    const formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'America/Vancouver',
      timeZoneName: 'shortOffset'
    })

    const parts = formatter.formatToParts(new Date('2026-11-15T12:00:00Z'))
    const timeZoneName = parts.find(p => p.type === 'timeZoneName')?.value || ''
    // Only skip the polyfill when the offset is clearly UTC-7, so missing or unexpected values still load it
    isTzOutdated = !/^(GMT|UTC)[-\u2212]0?7(:00)?$/i.test(timeZoneName)
  } catch {
    // Old browsers throw on shortOffset, so assume their tz data is outdated too
  }

  if (isTzOutdated) {
    try {
      await import('@formatjs/intl-datetimeformat/polyfill-force.js')
      await import('@formatjs/intl-datetimeformat/locale-data/en.js')
      await import('@formatjs/intl-datetimeformat/add-all-tz.js')
    } catch (error) {
      // Log polyfill loading failures for investigation
      console.error('Failed to load the Intl.DateTimeFormat polyfill', error)
    }
  }
})
