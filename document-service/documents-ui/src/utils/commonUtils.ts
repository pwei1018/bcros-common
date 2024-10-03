import { isEqualWith } from 'lodash'

/** Scroll to the top of the page */
export const scrollToTop = () => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth' // Smooth scrolling animation
  })
}

/** Helper function to remove properties with undefined/null/empty values **/
const removeEmptyProperties = (obj: any) => {
  for (const key in obj) {
    if (obj[key] === undefined || obj[key] === null || obj[key] === '') {
      // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
      delete obj[key]
    } else if (typeof obj[key] === 'object') {
      removeEmptyProperties(obj[key])
    }
  }
}

/** Insensitive string comparison helper. */
export const insensitiveStrCompare = (v1, v2) => !v1?.localeCompare(v2, undefined, { sensitivity: 'accent' })

/**
 * Deeply compares two values, supporting objects, arrays, and case-insensitive string comparison.
 *
 * @param base - The first value to compare.
 * @param current - The second value to compare.
 * @param isCaseSensitive - Flag for case-sensitive string comparison. Defaults to false.
 * @param cleanEmptyProperties - Clean emppty/null/undefined properties from comparisons: true by default.
 * @returns {boolean} - Returns true if the values are different, false if they are equal.
 */
export const deepChangesComparison = (
  base: BaseDataUnionIF,
  current: BaseDataUnionIF,
  isCaseSensitive: boolean = false,
  cleanEmptyProperties: boolean = true
): boolean => {

  // Remove undefined properties before comparison
  if (cleanEmptyProperties) {
    removeEmptyProperties(base)
    removeEmptyProperties(current)
  }

  // Return booleans
  if(typeof current === 'boolean') {
    return base !== current
  }

  // Return deep comparison with case options when at least one property is defined
  return (!!base || !!current) && !isEqualWith(base, current,
    (v1, v2) => (typeof v1 === 'string' && !isCaseSensitive) ? insensitiveStrCompare(v1, v2) : undefined
  )
}