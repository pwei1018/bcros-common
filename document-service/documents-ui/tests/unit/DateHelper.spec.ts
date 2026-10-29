import { describe, it, expect } from 'vitest'
import { formatToReadableDate } from '~/utils/dateHelper'

describe('formatToReadableDate', () => {
  it.each([
    ['late evening Pacific time', '2026-12-04T06:30:00+00:00', 'December 3, 2026'],
    ['just after midnight Pacific time', '2027-01-04T07:30:00+00:00', 'January 4, 2027']
  ])('uses the Pacific calendar day (%s)', (_, timestamp, expected) => {
    expect(formatToReadableDate(timestamp, true)).toBe(expected)
  })

  it('formats the date and time in Pacific time', () => {
    expect(formatToReadableDate('2026-12-04T06:30:00+00:00'))
      .toMatch(/^December 3, 2026 at 11:30:00\sPM Pacific time$/)
  })
})
