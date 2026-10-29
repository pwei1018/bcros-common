import { describe, it, expect } from 'vitest'
import { formatToReadableDate } from '~/utils/dateHelper'

describe('formatToReadableDate', () => {
  it.each([
    ['late evening Pacific time', '2026-12-04T06:30:00+00:00', '11:30:00\\sPM'],
    ['just after midnight Pacific time', '2027-01-04T07:30:00+00:00', '12:30:00\\sAM']
  ])('formats the time in Pacific time (%s)', (_, timestamp, expectedTime) => {
    expect(formatToReadableDate(timestamp)).toMatch(new RegExp(` at ${expectedTime} Pacific time$`))
  })
})
