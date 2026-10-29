import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

const importSpy = vi.fn()

function mockTimeZoneName(tzValue: string) {
  vi.spyOn(Intl, 'DateTimeFormat').mockImplementation(function () {
    return {
      formatToParts: () => [{ type: 'timeZoneName', value: tzValue }]
    } as unknown as Intl.DateTimeFormat
  })
}

async function runPlugin() {
  const { default: plugin } = await import('~/plugins/polyfill-date-time-format')
  await (plugin as any)({})
}

describe('Timezone Polyfill Plugin', () => {
  beforeEach(() => {
    vi.resetModules()
    importSpy.mockClear()
    vi.doMock('@formatjs/intl-datetimeformat/polyfill-force.js', () => {
      importSpy()
      return {}
    })
    vi.doMock('@formatjs/intl-datetimeformat/locale-data/en.js', () => ({}))
    vi.doMock('@formatjs/intl-datetimeformat/add-all-tz.js', () => ({}))
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it.each(['GMT-8', 'GMT-08:00', 'GMT−8', 'PST', ''])('loads the polyfill when the offset is "%s"', async (tzValue) => {
    mockTimeZoneName(tzValue)
    await runPlugin()
    expect(importSpy).toHaveBeenCalled()
  })

  it('loads the polyfill when shortOffset is not supported', async () => {
    vi.spyOn(Intl, 'DateTimeFormat').mockImplementation(function () {
      throw new RangeError('Invalid timeZoneName')
    })
    await runPlugin()
    expect(importSpy).toHaveBeenCalled()
  })

  it.each(['GMT-7', 'GMT-07:00', 'GMT−7'])('does not load the polyfill when the offset is "%s"', async (tzValue) => {
    mockTimeZoneName(tzValue)
    await runPlugin()
    expect(importSpy).not.toHaveBeenCalled()
  })
})
